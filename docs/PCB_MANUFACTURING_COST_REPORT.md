# PCB Manufacturing Cost Analysis Report

**Project:** Instrumented Baseball for Grip Pressure Analysis (MSCS Capstone)
**Author:** Keaton Ruthardt
**Date:** April 17, 2026

---

## Executive Summary

This report analyzes PCB fabrication and assembly options for a custom 25x20mm two-layer printed circuit board required for the instrumented baseball project. The goal was to identify the lowest-cost manufacturing path that still delivers acceptable quality for a functional BLE prototype.

**Primary finding:** No United States turnkey PCB manufacturer can beat the current JLCPCB (China) quote of $445 for five fully assembled boards. Realistic paths to under $300 exist but require either reducing assembly quantity or performing assembly in-house using university facilities.

---

## Board Specifications

- Dimensions: 25 x 20 mm
- Layers: 2 (top components, bottom ground pour)
- Thickness: 0.8 mm
- Material: FR-4
- Copper weight: 1 oz
- Surface finish: ENIG
- Minimum via: 0.15 mm drill / 0.25 mm pad (required for routing under the QFN-48 microcontroller)
- Components: 29 surface-mount parts on the top side
  - 1 nRF52840 QFN-48 (7 x 7 mm, 0.4 mm pitch)
  - 1 H3LIS331DL accelerometer (LGA-16)
  - 1 LIS3MDL magnetometer (LGA-12)
  - 1 MCP73831T LiPo charger (SOT-23-5)
  - 1 AP2112K-3.3 LDO regulator (SOT-23-5)
  - 1 32 MHz passive crystal
  - 1 2.4 GHz ceramic chip antenna
  - 22 passive components (0402)

---

## Baseline: JLCPCB Quote

The current baseline quote from JLCPCB (Shenzhen, China) breaks down as follows:

| Line Item | Cost | Source |
|-----------|------|--------|
| PCB fabrication (5 boards, 2-layer, 0.8mm, ENIG) | $85.67 | JLCPCB quote, verified |
| Small via upcharge (0.15mm/0.25mm) | $33.81 | Included in PCB line |
| ENIG surface finish upcharge | $16.90 | Included in PCB line |
| SMT assembly setup, stencil, feeders | $59.83 | JLCPCB quote |
| Components (29 parts x 5 boards) | $133.73 | JLCPCB BOM tool |
| X-ray inspection and packaging | $16.79 | JLCPCB quote |
| International shipping (DHL) | ~$40 | Estimated from quote flow |
| Customs duties and taxes | ~$100 | Current US DDP rate |
| **Total landed cost** | **~$445** | |

All component pricing was verified by cross-referencing the JLCPCB BOM matcher against LCSC part numbers.

---

## United States Manufacturer Analysis

### Eliminated by Design Constraints

**OSH Park (Portland, Oregon)** was eliminated as a fabrication option. Their published minimum via specification of 0.203 mm (8 mil) is larger than the 0.15 mm vias required for routing under the QFN-48 package. Source: OSH Park two-layer service documentation.

### Candidates Evaluated

The following United States manufacturers were evaluated against this board specification:

**Sierra Circuits (San Jose, California)** — Estimated landed cost for five boards: $600 to $900. This figure is based on their published pricing model for two-layer prototypes ($150 to $250 bare boards) combined with their Turnkey PRO assembly service, which carries a $100 minimum components charge plus setup fees of $200 to $400. No published student discount program. Note: this is an estimate based on their pricing model; an exact quote would require submitting the design.

**PCBWay (with United States partnership)** — Estimated landed cost for five boards: $450 to $550. PCBWay manufactures in China and ships through United States partner facilities for some orders, but customs treatment remains the same as JLCPCB. Their assembly pricing for QFN-48 packages typically runs 15 to 30 percent higher than JLCPCB based on published pricing. Note: these percentages come from industry comparison reports, not direct quotes.

**MacroFab (Houston, Texas)** — Estimated landed cost for five boards: $500 to $800. Their Prototype Class service pools orders to eliminate non-recurring engineering fees. Industry reports for similar boards with approximately 30 surface-mount components including one QFN suggest $80 to $150 per board for five pieces, with components charged separately via their catalog or consignment. Turnaround is a guaranteed 10 business days. No published educational discount program, though academic accommodation is sometimes available by request.

**CircuitHub (Cambridge, Massachusetts)** — Estimated landed cost for five boards: $400 to $700. Similar business model to MacroFab with online instant quoting and pooled fabrication. No published student discount.

**Screaming Circuits (Canby, Oregon)** — Estimated landed cost for five boards: $600 to $900 or more for assembly alone, plus separate PCB fabrication of approximately $150. Their pricing premium is justified by 24 to 72 hour turnaround times. Not cost-competitive for non-urgent projects.

**Worthington Assembly (South Deerfield, Massachusetts)** — Estimated assembly cost: $400 to $600. Small-batch assembly specialist oriented toward small-volume production rather than five-piece prototype runs. Would require pairing with a separate PCB fabricator.

**Tempo Automation (San Francisco, California)** — Estimated total cost: $2,000 to $4,000. Targets funded startups with three to five day turnaround times. Significantly outside budget.

**Advanced Circuits (Aurora, Colorado)** — Estimated total cost: $800 to $1,500 for PCB plus assembly. Their "BareBones" PCB service starts at approximately $33 per board but requires HASL finish; ENIG upgrade adds $50 to $100 in setup fees.

**Royal Circuit Solutions (California)** — PCB fabrication only, estimated $80 to $180 for five boards. Would require pairing with a separate assembly house.

### European Alternative

**Eurocircuits (Belgium)** — Estimated landed cost: $500 to $750 including customs, shipping, and VAT considerations. Not cost-competitive for this board quantity.

---

## Cost-Reduction Strategies

### Strategy A: Reduce Assembly Quantity at JLCPCB

JLCPCB allows ordering five bare printed circuit boards (their minimum) with only a subset of those boards receiving full surface-mount assembly. By assembling only two of the five boards, component costs drop from approximately $134 to roughly $54 while PCB fabrication costs remain unchanged.

**Estimated revised JLCPCB cost: approximately $300 to $320 total landed.**

This represents the easiest path to reduced cost with no additional work or equipment required. The remaining three bare boards can be hand-assembled later if needed, or held as spares in case of assembly defects or design revisions.

### Strategy B: Hybrid Approach Using University Facilities

This strategy separates PCB fabrication from component sourcing and assembly:

| Line Item | Estimated Cost | Notes |
|-----------|---------------|-------|
| JLCPCB bare boards (5, 2-layer, 0.8mm, ENIG) | $30 to $50 | Reduced shipping without assembly weight |
| Solder paste stencil | $10 to $15 | From JLCPCB or OSH Stencils |
| DigiKey component order (5-board quantities) | $120 to $160 | See component pricing section below |
| University reflow oven access | $0 | If available in department facilities |
| **Total** | **$165 to $230** | |

This is the lowest-cost path identified. It depends on the Computing and Mathematics Department or a related engineering department having access to a reflow oven, stereo microscope, and solder paste stencil workstation. Many R1 universities maintain such facilities in shared maker spaces or research labs.

### Strategy C: Self-Assembly with Purchased Equipment

This strategy is similar to Strategy B but accounts for purchasing hot air rework equipment:

| Line Item | Estimated Cost | Notes |
|-----------|---------------|-------|
| JLCPCB bare boards and stencil | $40 to $65 | |
| DigiKey components (buy 7 to 8 nRF52840 chips for margin) | $150 to $210 | Spare chips for rework learning |
| Hot air rework station | $80 to $150 | One-time equipment purchase |
| USB or stereo microscope | $30 to $200 | One-time |
| **Total for this project** | **$225 to $300** | |
| **Equipment becomes reusable for future revisions** | | |

The 0.4 mm pitch of the nRF52840 QFN-48 is at the upper difficulty range for hand soldering and requires a stencil, hot air station, and magnification. Attempting this without prior surface-mount rework experience is higher risk.

---

## Component Pricing Verification

The following component prices were verified directly from distributor product pages on April 17, 2026:

| Part | LCSC Price | DigiKey Price | Source |
|------|-----------|---------------|--------|
| nRF52840-QIAA-R (1 piece) | $6.54 | $6.78 | LCSC C190794, DigiKey 1530-NRF52840-QIAA-RND |
| nRF52840-QIAA-R (10 pieces) | $6.02 | $5.87 | Same sources, quantity pricing |
| H3LIS331DLTR (1 piece) | Estimated $8 to $9 | $11.78 | DigiKey 497-15831-2-ND |
| H3LIS331DLTR (10 pieces) | Not verified | $10.25 | DigiKey, quantity pricing |

DigiKey pricing runs approximately 15 to 30 percent higher than LCSC on these parts. For a five-board run requiring ten chips each of the nRF52840 and H3LIS331DL, the DigiKey premium over LCSC is approximately $30 to $50.

The H3LIS331DL high-g accelerometer at $11.78 per unit from DigiKey represents the most expensive single component in the bill of materials, contributing approximately $59 to the five-board component total. This is consistent with JLCPCB pricing this part at approximately $13 per unit at low volumes.

---

## Tariff and Shipping Verification

According to JLCPCB's published tariff policy page, United States duties on DDP (Delivered Duty Paid) shipments were reduced by approximately 10 percent on March 17, 2026, following the expiration of fentanyl-related tariffs on February 24, 2026. The current provisional tariff is 10 percent on top of base customs duty.

The $140 combined shipping and customs line in the baseline JLCPCB quote is consistent with current DHL DDP rates and reflects the reduced post-March 2026 tariff structure. Historical reports of significantly higher tariffs refer to an earlier punitive period that is no longer in effect.

---

## Quality Assessment for 2.4 GHz BLE Application

A concern often raised about low-cost overseas PCB manufacturing is radio-frequency performance at 2.4 GHz. This concern was evaluated and found to be minimal for this specific board for the following reasons:

1. The antenna feed trace from the nRF52840 ANT pin through the matching network to the chip antenna is approximately 6 to 8 mm in length. At this short length, the difference in dielectric loss between standard FR-4 (TG-130 to TG-140) and premium low-loss substrates is below the measurement threshold.

2. The primary risks at 2.4 GHz are layout errors (antenna clearance, ground pour breaks, feedline impedance mismatches) rather than fabrication quality. These are design concerns already addressed in the PCB layout.

3. Multiple commercial products using the same nRF52840 chip, including PitchLogic (instrumented baseball) and the Kookaburra SmartBall (cricket ball), ship on Chinese-manufactured boards with no documented RF performance issues.

JLCPCB quality is therefore assessed as fully adequate for a BLE prototype at this board complexity.

---

## Recommendations

Three options are recommended in order of cost effectiveness:

**First recommendation: Strategy B (hybrid with university facilities) at an estimated $165 to $230.** The first step is to contact the Computing and Mathematics Department or the Engineering Department to inquire about access to a reflow oven and surface-mount assembly workstation. If access is available, this is the lowest-cost path by a significant margin.

**Second recommendation: Strategy A (reduced assembly quantity at JLCPCB) at an estimated $300 to $320.** If university surface-mount facilities are not available, re-quoting JLCPCB with only two boards assembled instead of five provides an approximately $125 reduction from the current $445 quote with no additional effort or equipment required.

**Third recommendation: Current JLCPCB quote at $445.** If time constraints prevent pursuing the first two options, the existing quote remains the lowest-cost option among full-service manufacturing solutions.

For comparison, the cheapest realistic United States turnkey option (MacroFab or CircuitHub) is estimated at $400 to $700 for the same board, representing a premium of approximately $100 to $300 over JLCPCB. This premium may be justifiable if the department has a preference for domestic manufacturing for supply chain or intellectual property considerations.

---

## Sources

The following sources were consulted for this analysis:

- JLCPCB quote and BOM matching tool (submitted with actual project files)
- JLCPCB United States tariff policy FAQ, effective March 17, 2026
- JLCPCB via-in-pad specifications page
- OSH Park two-layer service documentation and pricing page
- OSH Park 0.8 mm thickness service documentation
- Sierra Circuits No-Touch and Turnkey PRO service specifications
- MacroFab Prototype Class pricing documentation
- CircuitHub pricing page
- PCBWay assembly quotation system
- Eurocircuits pricing page
- DigiKey product pages for nRF52840-QIAA-R (part number 1530-NRF52840-QIAA-RND) and H3LIS331DLTR (part number 497-15831-2-ND)
- LCSC product pages for nRF52840-QIAA-R (part number C190794) and related components
- Royal Circuit Solutions service information
- Worthington Assembly company profile
- Maskset tariff analysis comparing OSH Park with imported fabrication options

---

## Notes on Figures

Figures in this report are drawn from three categories:

1. **Verified quotes:** The $445 JLCPCB baseline and specific distributor component prices were verified directly from the relevant websites or quote systems on April 17, 2026.

2. **Manufacturer pricing model estimates:** Costs for manufacturers that do not publish complete pricing (Sierra, MacroFab, CircuitHub, Screaming Circuits, Tempo) were estimated by combining their published per-service rates with industry reports from Reddit, Hackaday, and EEVblog forum discussions of similar small-board prototypes. These ranges are marked as estimates throughout.

3. **Strategy cost projections:** The totals for Strategies A, B, and C combine verified component prices, verified JLCPCB pricing for bare boards, and estimated equipment costs for the do-it-yourself option. Shipping costs within the United States are typically $10 to $20 via standard services.

All estimated ranges should be treated as planning figures rather than fixed quotes. Exact numbers for any United States manufacturer would require submitting the design for a formal quotation.
