# Ball Integration Guide — XIAO Pressure Prototype

**Goal:** embed the XIAO nRF52840 + LiPo + 4 FlexiForce sensors into a real leather
baseball so it can be gripped, thrown, and tracked by TrackMan (July 11–12).

**Design principle for this prototype: make it RE-OPENABLE, not permanently sealed.**
You will need to recharge (USB-C), reflash, and fix wiring between sessions. A ball you
epoxy shut is a ball you can't debug. Use a leather flap held by tape/lacing, not glue.

---

## Materials
- Real leather baseball (for TrackMan realism) — plus 1–2 spares to practice on
- Assembled electronics: XIAO nRF52840, LiPo, 4× FlexiForce A201, 4× 10 kΩ resistors
- Thin stranded wire (30 AWG) + solder, heat-shrink
- Seam ripper or X-acto knife, curved needle + waxed thread (or strong lacing)
- Foam / thin closed-cell padding for shock protection (NOT epoxy for this prototype)
- Small tape (electrical/gaffer), a little hot glue for tacking
- Kitchen scale (target ~5.0–5.25 oz / 142–149 g), fine-tip marker

---

## STEP 0 — Bench-test the FULL assembly first (do not skip)
Before anything goes inside the ball, confirm the complete circuit works exactly as it
will inside:
- Solder the 4 sensors + 4 resistors + XIAO + LiPo into their final wired form.
- Flash `pressure_logger.ino`, run on the LiPo (not USB), confirm BLE logs all 4 channels
  and each sensor responds to a press.
- Once it's sealed in a ball, you can't rewire — so everything must work here first.

## STEP 1 — Map the grip points
Hold a four-seam grip and mark the ball surface where each finger sits:
- **Index** and **Middle** on top (across/near the seams)
- **Thumb** underneath
- **Ring** on the side
Mark each spot with the marker and label which sensor (S1–S4) goes there.

## STEP 2 — Open the ball (re-openable flap)
- With the seam ripper, cut the stitching along **one figure-8 seam** to free a leather
  flap — enough to reach inside. Do NOT remove the whole cover; you want to close it back up.
- Peel the flap back. Under the leather is tightly wound yarn around the cork/rubber pill.

## STEP 3 — Carve the central cavity
- Dig out yarn (and shave a little of the pill if needed) to make a pocket at the ball's
  **center** sized for the XIAO + LiPo. Keep it centered — off-center mass makes it fly wrong.
- Save the removed yarn; you'll pack some back for weight.

## STEP 4 — Protect and seat the electronics
- Wrap the XIAO + LiPo in a thin layer of **closed-cell foam** (shock protection you can
  still open later). Keep the **USB-C port oriented toward the flap** so you can reach it.
- Seat the wrapped pack in the central cavity.

## STEP 5 — Route wires to the grip points
- Run each sensor's 30 AWG tail from the central electronics out through the yarn to its
  mapped grip point. Leave a little slack (strain relief) so a throw can't yank a joint.
- Tack wires down with tiny dabs of hot glue so nothing shifts.

## STEP 6 — Place sensors under the leather
- Lay each FlexiForce sensing pad **flat against the inside of the leather** at its grip
  point (index/middle/thumb/ring). The 0.2 mm sensor + leather preserves natural grip feel.
- Lightly tape or tack each in place so it can't slide.

## STEP 7 — Repack for weight & balance
- Pack yarn back around the electronics to rebuild the ball's shape and mass.
- Weigh as you go; target **~5.0–5.25 oz**. Add small packing/weight opposite any heavy
  side to keep the center of mass centered.

## STEP 8 — Close it up (re-openably)
- Fold the leather flap back down. **Re-stitch with waxed thread OR lace it snug with a
  removable stitch / strong tape** so you can reopen to charge and reflash.
- Do NOT glue it shut for this prototype.

## STEP 9 — Validate before throwing
1. Power on (battery), confirm BLE still logs (yarn/leather don't block short-range BLE).
2. Press each grip point → confirm the correct sensor channel responds.
3. Check weight and that it feels balanced in the hand.
4. Gentle **drop test** from waist height a few times → re-check it still logs.
5. A few easy test throws → confirm data survives a real throw before the pitchers arrive.

---

## Prototype tips
- **Charging/reflashing:** keep the USB-C port reachable through the flap; recharge between
  sessions and top off before each pitcher.
- **Strain relief is the #1 failure point** — the thin sensor tails tear at the solder joint.
  Slack + glue tacks + heat-shrink at joints.
- **Keep a spare ball built** if time allows — throwing tests are hard on prototypes.
- **Balance matters for TrackMan** (the ball must fly true to read), but note: grip-pressure
  data is captured *before release*, so a slightly imperfect ball still yields valid pressure
  data even if flight isn't perfect.
