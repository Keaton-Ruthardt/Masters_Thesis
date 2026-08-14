# Flashing the Custom PCB Using a XIAO nRF52840 as Programmer

This turns your spare XIAO nRF52840 into a CMSIS-DAP SWD programmer so you can
flash firmware onto the bare nRF52840 on your custom board (which has no USB port).

## One-Time Setup: Convert the XIAO into a Programmer

1. Download the free-dap / CMSIS-DAP UF2 firmware built for the XIAO nRF52840
   (search "free-dap XIAO nRF52840 uf2" or "DapperMime nRF52840").
2. Plug the XIAO into USB. Double-tap its reset button.
3. The XIAO mounts as a USB drive named "XIAO-BOOT".
4. Drag the CMSIS-DAP .uf2 file onto that drive.
5. The XIAO reboots as a CMSIS-DAP debug probe. It is now a programmer.

(To turn it back into a normal XIAO later, flash the standard Seeed XIAO
nRF52840 bootloader UF2 the same way.)

## Wiring: XIAO Programmer to Custom Board SWD Pads

Connect five wires. The exact XIAO pins for SWCLK and SWDIO are defined by the
free-dap firmware build you used — check its README. A common mapping is:

| XIAO (programmer) | Custom board pad |
|-------------------|------------------|
| SWCLK pin         | SWD_CLK          |
| SWDIO pin         | SWD_DIO          |
| RST               | SWD_RST          |
| 3V3               | SWD_VCC          |
| GND               | SWD_GND          |

Your custom board's SWD pads are round 1.5 mm / 2.0 mm test pads. Either solder
thin 30 AWG wires to them temporarily, or hold pogo pins against them while flashing.

## Power

Power the custom board during flashing either from:
- The XIAO's 3V3 pin into SWD_VCC, OR
- The board's own LiPo battery connected to BATT+ / BATT-

## Flashing Firmware in Arduino IDE

1. Open Arduino IDE with your smartball_full.ino sketch.
2. Tools -> Board -> Seeed XIAO nRF52840 (the target chip is the same family).
3. Tools -> Programmer -> CMSIS-DAP.
4. First time only: Tools -> Burn Bootloader (writes the SoftDevice/bootloader
   region to the bare chip via SWD). This prepares the blank nRF52840.
5. Then: Sketch -> Upload Using Programmer (NOT the normal Upload button).
6. The XIAO programs your custom board's nRF52840 over SWD.

## Verifying It Worked

After upload:
- Open the Serial Monitor only if the custom board has a USB/serial path
  (it does not, so use BLE instead).
- Power the custom board and scan with the nRF Connect app on your phone.
- The board should advertise as "SmartBall" and stream the sensor characteristics,
  exactly like the breadboard prototype did.

## If It Fails

- Double-check SWD wiring (SWDIO/SWCLK not swapped, solid GND).
- Confirm the custom board is powered (measure 3.3 V on SWD_VCC).
- Make sure "Upload Using Programmer" was used, not normal Upload.
- If "Burn Bootloader" fails, the SWD connection is not solid — re-check pads.

## Fallback

If the XIAO-as-programmer route gives trouble, a $4 Raspberry Pi Pico
(debugprobe firmware) or a ~$12 generic CMSIS-DAP/DAPLink does the same job
with the same Arduino IDE steps (Programmer -> CMSIS-DAP).
