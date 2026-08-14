"""
SmartBall — BLE Pressure Logger (Bleak)

Connects to the XIAO nRF52840 SmartBall over BLE, subscribes to the pressure
notify characteristic, and streams every 120 Hz sample to a timestamped CSV for
post-processing against TrackMan.

Matches firmware/pressure_logger/pressure_logger.ino:
  Local name   : "SmartBall"
  Service UUID : 00001234-0000-1000-8000-00805f9b34fb
  Char UUID    : 00001235-0000-1000-8000-00805f9b34fb  (Read | Notify)
  Packet (12 B): <I H H H H  = uint32 t_ms + 4x uint16 ADC (sensors S1,S2,S3,S4)
                 little-endian

Raw ADC is the source of truth (calibration is applied/refined in analysis).
The *N force columns are a convenience readout using the same conductance model
as the firmware — do not treat them as final.

Sensors sit at FIXED positions on the ball. Which finger lands on which pad
depends on how the hand rotates for the grip, so each pitch type has its own
map and the script asks for the pitch at startup, tagging every row.

Channels are fixed hardware (wire colour -> pin -> sensor -> calFactor):
  S1 = A0 black   = BK (119 N)     S3 = A2 green   = KA (148 N)
  S2 = A1 white   = RM (129 N)     S4 = A3 purple  = CG (157 N)

Finger per grip (3 fingers measured; ring is not instrumented in v2):
  fastball  : S1=pointer  S2=middle   S3=thumb    (S4 unused)
  curveball : S3=pointer  S4=middle   S1=thumb    (S2 unused)
  slider    : same as curveball

ANALYSIS CAVEAT: because the grip rotates, "pointer" is BK on a fastball but KA
on a curveball — different sensors with different calFactors and different
calibrated ranges. Comparing absolute per-finger force ACROSS pitch types
therefore compares instruments, not just grips. Force ratios within a single
pitch type are the more defensible measure.

Field workflow (July 11-12):
  1. Power the ball on the LiPo (not USB) so it advertises as "SmartBall".
  2. Run:  python ble_logger.py --out session_2026-07-11.csv
     → answer the pitch-type prompt (1=fastball, 2=curveball, 3=slider).
  3. Press ENTER between pitches to drop a marker row (for TrackMan alignment).
     Type ff / cb / sl + ENTER to SWITCH pitch type mid-session (also marks).
  4. Ctrl+C to stop — the file is flushed and a summary is printed.

USAGE:
    python ble_logger.py [--out FILE] [--name SmartBall] [--duration SECONDS]
                         [--no-force] [--quiet]

Requires: pip install bleak  (see requirements.txt)
"""

import argparse
import asyncio
import csv
import struct
import sys
import threading
from datetime import datetime, timezone

from bleak import BleakClient, BleakScanner

# ── BLE identifiers (must match firmware) ──
DEVICE_NAME = "SmartBall"
CHAR_UUID = "00001235-0000-1000-8000-00805f9b34fb"
BATT_UUID = "00001236-0000-1000-8000-00805f9b34fb"  # uint16 mV, ~every 2 s

# Packet: uint32 t_ms of the FIRST sample, then N x {4x uint16 ADC}, LE.
#   12 B -> 1 sample/packet   (pressure_logger.ino,     120 Hz)
#   20 B -> 2 samples/packet  (pressure_logger_480.ino, 240 Hz)
#   36 B -> 4 samples/packet  (pressure_logger_480.ino, 480 Hz)
# Detected from the packet length, so one logger serves either firmware.
CHANNELS = ("s1", "s2", "s3", "s4")
_STRUCTS = {}


def packer_for(nbytes):
    """(struct, samples_per_packet) for a packet length, or None if malformed."""
    if nbytes < 12 or (nbytes - 4) % 8:
        return None
    n = (nbytes - 4) // 8
    if n not in _STRUCTS:
        _STRUCTS[n] = struct.Struct("<I" + "H" * (4 * n))
    return _STRUCTS[n], n

# ── Grip maps: which finger sits on which sensor, per pitch type. None = no
#    finger on that sensor for this grip (still logged — raw is raw).
#    Ring is not instrumented in v2: three fingers per grip. ──
PITCH_MAPS = {
    "fastball":  {"s1": "pointer", "s2": "middle", "s3": "thumb",   "s4": None},
    "curveball": {"s1": "thumb",   "s2": None,     "s3": "pointer", "s4": "middle"},
    "slider":    {"s1": "thumb",   "s2": None,     "s3": "pointer", "s4": "middle"},
}
PITCH_ALIASES = {
    "1": "fastball",  "ff": "fastball",  "fb": "fastball",  "fastball": "fastball",
    "2": "curveball", "cb": "curveball", "curveball": "curveball",
    "3": "slider",    "sl": "slider",    "slider": "slider",
}

# ── Calibration (N per unit conductance), PER SENSOR (fixed, grip-independent).
#    v3 fits, calfactors_v3.csv (2026-07-31, 20 staircases per sensor).
#    Channel = physical pin, so these follow the v2 harness assignment:
#      s1 = A0 black = BK (119, to 28.4 N)   s3 = A2 green  = KA (148, to 19.6 N)
#      s2 = A1 white = RM (129, to 28.4 N)   s4 = A3 purple = CG (157, to 19.6 N)
#    NOTE: fit only to ~19-28 N; pitches reach 40-100+ N, so these extrapolate.
#    Used ONLY for the live force readout — raw ADC is logged for real analysis. ──
CAL_FACTOR = {"s1": 119.0, "s2": 129.0, "s3": 148.0, "s4": 157.0}
ADC_MAX = 4095


def adc_to_force(adc, ch):
    """Firmware-matching conductance model: G = adc/(4095-adc); F = G * calFactor."""
    if adc <= 0 or adc >= ADC_MAX:
        return 0.0
    conductance = adc / (ADC_MAX - adc)
    return conductance * CAL_FACTOR[ch]


class Logger:
    def __init__(self, out_path, pitch_type="fastball", add_force=True,
                 quiet=False, sample_hz=None):
        self.add_force = add_force
        self.quiet = quiet
        self.pitch_type = pitch_type
        # Filled in from the first packet's length (see packer_for)
        self.samples_per_packet = None
        self.sample_hz = sample_hz
        self.step_ms = None
        self._prev_raw = None     # last raw timestamp, for wrap detection
        self._wraps = 0           # micros() rollovers seen
        self._last_t = None       # last emitted ball_t_ms, for monotonicity
        self.nudged = 0           # timestamps pushed forward to stay monotonic
        self._file = open(out_path, "w", newline="")
        self._writer = csv.writer(self._file)

        cols = ["wall_iso", "wall_unix_ms", "ball_t_ms", *CHANNELS]
        if add_force:
            cols += [f"{c}_N" for c in CHANNELS]
        cols += ["pitch_type", "battery_mV", "marker"]
        self._writer.writerow(cols)
        self.battery_mv = None  # last-known battery voltage from the ball

        self.count = 0
        self.dropped = 0          # gaps inferred from ball_t_ms jumps
        self.first_ball_t = None
        self.last_ball_t = None
        self.first_wall = None
        self.last_wall = None
        self._pending_marker = ""
        self._lock = threading.Lock()

    def mark(self, text="mark"):
        """Queue a marker to attach to the next sample (thread-safe)."""
        with self._lock:
            self._pending_marker = text

    def set_pitch_type(self, pitch_type):
        """Switch the active grip map mid-session (thread-safe enough: str swap)."""
        self.pitch_type = pitch_type

    def on_battery(self, data):
        if len(data) == 2:
            self.battery_mv = struct.unpack("<H", data)[0]

    def on_packet(self, data):
        got = packer_for(len(data))
        if got is None:
            return  # malformed / partial write
        st, nsamp = got

        vals = st.unpack(data)
        t_raw, adcs = vals[0], vals[1:]

        # Timebase differs by firmware, keyed off the packet size:
        #   1 sample/packet  -> pressure_logger.ino sends millis()
        #   >1 sample/packet -> pressure_logger_480.ino sends micros(), which
        #      avoids the 1 ms quantisation that made reconstructed sample times
        #      overlap across batch boundaries. micros() wraps every ~71.6 min,
        #      so accumulate the wraps here.
        if self._prev_raw is not None and t_raw < self._prev_raw - (1 << 31):
            self._wraps += 1
        self._prev_raw = t_raw
        t_base = t_raw + self._wraps * (1 << 32)
        t_ms = t_base / 1000.0 if len(data) > 12 else float(t_base)

        # First packet tells us the firmware's batching, hence the sample rate.
        if self.samples_per_packet is None:
            self.samples_per_packet = nsamp
            if self.sample_hz is None:
                self.sample_hz = 120.0 if nsamp == 1 else 120.0 * nsamp
            self.step_ms = 1000.0 / self.sample_hz
            if not self.quiet:
                sys.stdout.write(
                    f"  packet {len(data)} B = {nsamp} sample(s) -> "
                    f"{self.sample_hz:.0f} Hz\n")
                sys.stdout.flush()

        now = datetime.now(timezone.utc)
        wall_ms = int(now.timestamp() * 1000)

        with self._lock:
            marker, self._pending_marker = self._pending_marker, ""

        # Batch samples share an arrival instant; ball_t_ms is the precise
        # timebase and is reconstructed from the known fixed sample interval.
        # wall_* is offset the same way purely to stay monotonic.
        for k in range(nsamp):
            adc = adcs[4 * k:4 * (k + 1)]
            off = k * self.step_ms
            t_s = round(t_ms + off, 3)
            # Never emit a non-monotonic timestamp: a stalled loop can make the
            # next batch start before the previous batch's assumed span ends.
            if self._last_t is not None and t_s <= self._last_t:
                t_s = round(self._last_t + 0.001, 3)
                self.nudged += 1
            self._last_t = t_s
            row = [now.isoformat(), wall_ms + round(off), t_s, *adc]
            if self.add_force:
                row += [round(adc_to_force(a, c), 2)
                        for a, c in zip(adc, CHANNELS)]
            row += [self.pitch_type,
                    self.battery_mv if self.battery_mv is not None else "",
                    marker if k == 0 else ""]   # marker rides the first sample
            self._writer.writerow(row)
            self.count += 1

        # Dropped-packet estimate, measured between batches
        batch_ms = self.step_ms * nsamp
        if self.first_ball_t is None:
            self.first_ball_t = t_ms
            self.first_wall = now
        elif self.last_ball_t is not None:
            gap = t_ms - self.last_ball_t
            if gap > 1.5 * batch_ms:
                self.dropped += (round(gap / batch_ms) - 1) * nsamp
        self.last_ball_t = t_ms
        self.last_wall = now

        if not self.quiet and self.count % 100 < nsamp:
            adc = adcs[4 * (nsamp - 1):]      # newest sample in the batch
            amap = PITCH_MAPS[self.pitch_type]
            forces = "  ".join(
                f"{amap[c]}(S{c[1]}):{adc_to_force(a, c):5.1f}N"
                for a, c in zip(adc, CHANNELS) if amap[c]
            )
            batt = (f" | {self.battery_mv / 1000:.2f}V"
                    if self.battery_mv is not None else "")
            sys.stdout.write(
                f"\r  {self.count:>7} samples | {self.pitch_type:<9} | "
                f"{forces}{batt}   "
            )
            sys.stdout.flush()

    def close(self):
        self._file.flush()
        self._file.close()

    def summary(self):
        if self.count == 0:
            return "No samples received."
        span_ball = (self.last_ball_t - self.first_ball_t) / 1000.0
        span_wall = (self.last_wall - self.first_wall).total_seconds()
        rate = self.count / span_wall if span_wall > 0 else 0.0
        batt = (f"  Battery (last) : {self.battery_mv / 1000:.2f} V\n"
                if self.battery_mv is not None else "")
        target = self.sample_hz or 120.0
        return (
            f"\n--- Summary ----------------------------\n"
            f"  Samples logged : {self.count}\n"
            f"  Est. dropped   : {self.dropped}\n"
            f"  Samples/packet : {self.samples_per_packet}\n"
            f"  Time nudges    : {self.nudged}"
            f"{'  <-- loop stalls, check' if self.nudged > self.count * 0.02 else ''}\n"
            f"  Ball time span : {span_ball:.1f} s\n"
            f"  Wall time span : {span_wall:.1f} s\n"
            f"  Effective rate : {rate:.1f} Hz (target {target:.0f})\n"
            f"{batt}"
            f"----------------------------------------"
        )


def ask_pitch_type():
    """Interactive startup prompt → 'fastball' | 'curveball' | 'slider'."""
    print("Pitch type for this block?")
    print("  [1] fastball   (S1 blk=pointer  S2 wht=middle  S3 grn=thumb,  S4 unused)")
    print("  [2] curveball  (S3 grn=pointer  S4 pur=middle  S1 blk=thumb,  S2 unused)")
    print("  [3] slider     (same sensor map as curveball)")
    while True:
        ans = input("Enter 1/2/3 (or ff/cb/sl): ").strip().lower()
        if ans in PITCH_ALIASES:
            pt = PITCH_ALIASES[ans]
            print(f"-> {pt}\n")
            return pt
        print("   Didn't catch that — type 1, 2, 3, ff, cb, or sl.")


async def stdin_marker_loop(logger, stop_event):
    """Read console lines off the event loop.

    ENTER            → drop a plain markN marker (one per pitch).
    ff / cb / sl     → switch the active pitch type AND drop a marker row.
    anything else    → drop it as a custom marker (e.g. P1_FF_03).
    """
    loop = asyncio.get_running_loop()
    n = 0
    while not stop_event.is_set():
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if line == "":  # EOF (e.g. piped input)
            return
        text = line.strip()
        if text.lower() in PITCH_ALIASES:
            pt = PITCH_ALIASES[text.lower()]
            logger.set_pitch_type(pt)
            logger.mark(f"pitch_type={pt}")
            if not logger.quiet:
                sys.stdout.write(f"\r  * pitch type -> {pt}\n")
                sys.stdout.flush()
            continue
        n += 1
        text = text or f"mark{n}"
        logger.mark(text)
        if not logger.quiet:
            sys.stdout.write(f"\r  * marker '{text}' set\n")
            sys.stdout.flush()


async def run(args):
    pitch_type = args.pitch or ask_pitch_type()

    print(f"Scanning for '{args.name}' …  (Ctrl+C to stop)")
    device = await BleakScanner.find_device_by_name(args.name, timeout=args.scan_timeout)
    if device is None:
        print(f"ERROR: '{args.name}' not found. Is the ball powered on the LiPo "
              f"and advertising? Try moving closer.")
        return 1

    print(f"Found {device.name}  [{device.address}].  Connecting …")
    logger = Logger(args.out, pitch_type=pitch_type,
                    add_force=not args.no_force, quiet=args.quiet,
                    sample_hz=args.sample_hz)
    stop_event = asyncio.Event()

    def handle_notify(_sender, data):
        logger.on_packet(bytes(data))

    try:
        async with BleakClient(device) as client:
            await client.start_notify(CHAR_UUID, handle_notify)
            try:
                await client.start_notify(
                    BATT_UUID, lambda _s, d: logger.on_battery(bytes(d)))
            except Exception:
                print("(no battery characteristic — older firmware; "
                      "voltage readout disabled)")
            print(f"Connected. Logging to {args.out}  (pitch type: {pitch_type})")
            print("ENTER = pitch marker  |  ff/cb/sl + ENTER = switch pitch type\n")

            marker_task = asyncio.create_task(stdin_marker_loop(logger, stop_event))

            if args.duration:
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=args.duration)
                except asyncio.TimeoutError:
                    pass
            else:
                # Run until disconnect or Ctrl+C
                while client.is_connected and not stop_event.is_set():
                    await asyncio.sleep(0.25)
                if not client.is_connected:
                    print("\nDevice disconnected.")

            stop_event.set()
            marker_task.cancel()
            try:
                await client.stop_notify(CHAR_UUID)
            except Exception:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        logger.close()
        print(logger.summary())
        print(f"Saved: {args.out}")
    return 0


def parse_args():
    p = argparse.ArgumentParser(description="SmartBall BLE pressure logger")
    default_out = f"smartball_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    p.add_argument("--out", default=default_out, help="output CSV path")
    p.add_argument("--name", default=DEVICE_NAME, help="BLE local name to connect to")
    p.add_argument("--duration", type=float, default=None,
                   help="auto-stop after N seconds (default: run until Ctrl+C)")
    p.add_argument("--scan-timeout", type=float, default=20.0,
                   help="seconds to scan before giving up")
    p.add_argument("--no-force", action="store_true",
                   help="log raw ADC only (skip the convenience force columns)")
    p.add_argument("--pitch", choices=sorted(PITCH_MAPS),
                   help="pitch type for this block (skips the startup prompt)")
    p.add_argument("--quiet", action="store_true", help="suppress live readout")
    p.add_argument("--sample-hz", type=float, default=None,
                   help="override the sample rate used to reconstruct "
                        "intra-batch timestamps (default: inferred from the "
                        "packet size — 1 sample=120 Hz, 2=240, 4=480)")
    return p.parse_args()


def main():
    args = parse_args()
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
