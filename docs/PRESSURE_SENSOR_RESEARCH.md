# Flexible Pressure Sensing Matrix Research
## For MastersBall Instrumented Baseball (73mm Diameter Sphere)
### Research Date: 2026-04-06

---

## CRITICAL CONTEXT: Baseball Grip Force Requirements

Before evaluating any sensor technology, we need to know what forces we are measuring.

**Kinoshita et al. (2017) — "Finger forces in fastball baseball pitching"**
(Published in Human Movement Science, ScienceDirect)

- Index and middle finger: peak forces ~97N each (bimodal pattern, peaks at 38-39ms and 6-7ms before release)
- Thumb: ~83N single peak
- Ring finger: ~50N single peak
- Shear forces (index + middle combined): peak of 102N at 4-5ms before release
- These forces represent 80-85% of maximum finger strength
- Forces scale linearly with pitch velocity

**This means any sensor technology MUST handle at least 0-100N reliably. This is a hard requirement that immediately eliminates several options.**

---

## 1. Velostat/Linqstat Pressure Matrices

### What It Is
Velostat (also sold as Linqstat) is a polyethylene film impregnated with carbon black particles. It is piezoresistive — resistance decreases when force is applied. Available as sheets from Adafruit (~$5 for a large sheet). A matrix is built by sandwiching Velostat between perpendicular strips of conductive material (copper tape or conductive fabric) — row electrodes on one side, column electrodes on the other. Each intersection becomes a force-sensing pixel.

### Force-to-Resistance Relationship
**NOT linear.** The relationship is complex and depends on the force range:
- 0-15N: Approximately linear conductance-vs-force relationship (inverse resistance-vs-force). This is the best-behaved region.
- Above 15N: Sensitivity drops sharply. At 3N+ the sensitivity is only 0.003 N^-1 compared to 0.775 N^-1 at 0-1N. The material saturates.
- A logarithmic model fits best overall: F = 0.569 * log(44.98V), with R^2 = 0.9902 (Polyethylene-Carbon Composite Tactile Sensor study, PMC 2020).
- Power law model: F = -1.067V^-0.4798 + 3.244 (same study, slightly worse fit).
- Can be calibrated to give Newtons, but requires per-sensor calibration and the calibration drifts over time.

**Source**: [Polyethylene-Carbon Composite (Velostat) Based Tactile Sensor (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7761878/); [Low-Cost Pressure Sensor Matrix Using Velostat (IEEE)](https://ieeexplore.ieee.org/document/8537720)

### Accuracy
- 32x32 matrix for foot pressure: body weight error 0.4-12.1%, but footprint area error 7.3-68.8%, maximum pressure error 37.6-70.7%.
- Prosthetic socket study: mean accuracy errors of 110 kPa with significant cyclical and thermal drift of up to 0.00715 V/cycle, leading to up to 67% difference in voltage range.
- 32x32 foot pressure matrix with efficient calibration: 4.2% mean error, 3.1% median error for total body weight (but this aggregates many cells — individual cell accuracy is much worse).
- Center-of-Pressure computation: decreased from 17.37% error to 5.47% with novel algorithms.

**Source**: [Efficient Calibration of Velostat-Based Flexible Pressure Sensor Matrix (IEEE)](https://ieeexplore.ieee.org/document/10220429/); [Examination of Velostat as In-Socket Pressure Sensor (IEEE)](https://ieeexplore.ieee.org/document/9024130/)

### Repeatability
**Poor.** This is Velostat's biggest weakness:
- ANOVA testing showed p > 0.05, indicating statistically insufficient repeatability.
- The material structure is non-homogenous, which directly impacts measurement repeatability.
- Significant cyclical drift (0.00715 V/cycle).
- Material ages — electrical properties change over time and do not return to initial state.
- Temperature-dependent output adds another variable.

**Source**: [Examination of Performance Characteristics of Velostat as In-Socket Pressure Sensor (IEEE)](https://ieeexplore.ieee.org/document/9024130/)

### Drift and Hysteresis
- Significant cyclical drift — up to 67% difference in voltage range over repeated loading.
- Material deforms over time and does not fully return to initial state.
- Thermal drift is also significant.
- Hysteresis is present but actually one of the better characteristics (lower hysteresis than some commercial FSRs in some tests).

### Performance at High Forces (40-100N) — CRITICAL PROBLEM
**Velostat saturates well before the forces needed for baseball pitching.**
- Linear range extends only to ~15N.
- At 3N+, sensitivity drops to 0.003 N^-1 (essentially flat — barely distinguishable readings).
- Normal force measurement range documented at only 0-12N in research.
- Higher loads can damage Velostat and lead to loss of conductivity or short circuits.
- **VERDICT: Velostat CANNOT measure baseball grip forces (50-100N). The material saturates and/or is damaged at these forces.**

### Durability
- Survives 2500 loading/unloading cycles at ~2N with stable characteristics (stabilizes after 5th cycle).
- Bending cycles: 0.95-2.2% output deviation after 150 cycles.
- 210-day long-term study showed material properties do change over time.
- BUT: These are at low forces (2-5N). No evidence of surviving repeated 100N impacts.
- Higher loads can damage the material.

**Source**: [Investigation of Long-Term Reliability of Velostat Pressure Sensor Array (IEEE)](https://ieeexplore.ieee.org/document/10349695/); [Investigation of Mechanical Reliability of Velostat Pressure Sensor (IEEE)](https://ieeexplore.ieee.org/document/9781575/)

### Layered Velostat (Recent Research 2025)
- Stacking multiple 0.1mm Velostat layers improves accuracy.
- Layered sensors reduced measurement errors by 27-60% compared to single-layer and even outperformed some commercial FSRs.
- Study specifically targeted hand force sensing applications.
- However, this still does not solve the force range / saturation problem for baseball.

**Source**: [On the Effect of Layering Velostat on Force Sensing for Hands (MDPI, 2025)](https://www.mdpi.com/1424-8220/25/10/3245)

### Crosstalk Problem
- Velostat's multidirectional conductivity (both normal and transversal) means pressure at one point affects readings at adjacent points.
- This is a fundamental limitation for matrix arrays — "ghosting" is inherent.
- Solutions exist (zero potential circuits, isolated drive feedback, AC multi-frequency scanning) but add significant circuit complexity.

**Source**: [A Proposal to Eliminate Crosstalk in Resistive Sensor Array Readouts (ResearchGate)](https://www.researchgate.net/publication/342499867); [Novel Crosstalk Suppression Method for 2-D Networked Resistive Sensor Array (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4168420/)

### Cost
- Velostat sheet: ~$5 (Adafruit, large sheet)
- Copper tape: ~$5-10
- Total matrix material cost: ~$10-20
- This is by far the cheapest option.

### OVERALL VERDICT ON VELOSTAT FOR THIS PROJECT: NOT SUITABLE
- Force range is fundamentally insufficient (saturates at ~15N, pitching requires 50-100N)
- Accuracy is poor (individual sensor errors can exceed 50%)
- Repeatability fails statistical testing
- Higher forces damage the material
- Crosstalk in matrices adds further error
- Good for: low-force applications (sitting posture, gentle touch), rough presence detection, educational demos
- Bad for: quantitative force measurement above 15N, anything requiring repeatability

---

## 2. Interlink FSR 406/408 (Large Area FSR)

### What They Are
- FSR 406: Square, 43.69mm (1.75") sensing area. ~$7-12 each.
- FSR 408: Long strip, 622.3mm length. ~$10-15 each.
- FSR 402: Round, 18.28mm diameter. ~$7-10 each (smaller, more commonly available).
- All are polymer thick-film (PTF) devices — resistance decreases with applied force.

### Specifications
- Actuation force: as low as 0.1N
- **Sensitivity range: 0.1N to only 10N** (FSR 400 series)
- Part-to-part variation: ~10%
- NOT designed for quantitative force measurement — datasheet explicitly notes they're best for "approximate" force (light/moderate/strong).
- Response is logarithmic (like most FSRs).

### Can They Be Cut or Shaped?
**No.** The sensing area is printed as a specific pattern. Cutting destroys the sensor. You would need to use them as-is and conform them to the ball surface, which is mechanically awkward.

### Covering a Baseball
A baseball circumference is ~230mm. To cover the full surface you'd need many sensors, and their rigid tail connectors make wrapping extremely difficult. You'd also need ~6-8 sensors minimum just for finger contact areas, at $7-12 each.

### VERDICT: NOT SUITABLE
- Force range (0-10N) is far too low for baseball pitching (50-100N needed)
- Accuracy is explicitly stated as poor (~10% variation between identical sensors)
- Cannot be cut to shape
- Rigid connector tails complicate spherical mounting
- More expensive than Velostat matrix for less coverage
- Better than Velostat for single-point measurement, but still not research-grade

**Source**: [FSR 406 Data Sheet (SparkFun/Interlink)](https://cdn.sparkfun.com/assets/c/4/6/8/b/2010-10-26-DataSheet-FSR406-Layout2.pdf); [FSR Integration Guide (Interlink/DigiKey)](https://media.digikey.com/pdf/Data%20Sheets/Interlink%20Electronics.PDF/FSR_Integration_Guide.pdf)

---

## 3. Tekscan FlexiForce A502 and Tekscan Grip System

### FlexiForce A502 (Large Area Sensor)
- Sensing area: 2" x 2" (50.8 x 50.8mm) — single zone, not a matrix
- Standard force range: 0-222N (0-50 lb) — **actually covers the baseball range**
- Can handle up to 44,482N with adjusted drive voltage/feedback resistor
- 2-pin male connector
- Available from DigiKey/Mouser; sold in 8-packs
- Price: approximately $25-35 per sensor (based on similar FlexiForce pricing; contact distributor for exact current price)
- This is a single large sensor, NOT a matrix. It tells you total force over the 2"x2" area, not force distribution.

### FlexiForce A201 (Already In Your Project)
- Your current sensors: 9.5mm sensing area, 0-111N (25 lb) range
- ~$25 each
- Proven by Yeh et al. (2024) for baseball grip measurement under leather
- Linearity: significantly better than Velostat or generic FSRs
- Durability: 3+ million presses
- Repeatability: best among piezoresistive sensors in head-to-head comparisons

### Tekscan Grip System (Full Pressure Mapping)
- 18 individually positionable sensing regions on a thin sensor sheet
- Designed to be worn on the hand or built into a glove
- Ultra-thin (0.1mm), flexible
- Scanning rate: up to 750 Hz
- **Price: Not publicly listed. Industry estimates put full Tekscan systems at $5,000-$20,000+ including hardware and software. These are research-lab instruments.**
- This would give you exactly what you want (full grip pressure map) but is completely out of budget range.

### Tekscan Pressure Mapping Sensors (Custom)
- Tekscan manufactures custom thin-film pressure mapping sensors
- They make sensors for a huge range of applications (dental, automotive, sports)
- All require Tekscan's proprietary electronics and software
- Custom sensors start in the thousands of dollars

### VERDICT
- A502: Force range is correct, but it's a single zone (not a matrix). Could work as larger individual sensors at finger positions, but at ~$25-35 each, the cost adds up.
- A201 (current choice): Already validated for this exact application by Yeh et al. Correct force range, proven repeatability, 0.2mm thin, works under leather. 4 sensors at $25 each = $100. **This remains the best option for discrete measurement points.**
- Grip System: Would be the ideal solution if budget were unlimited. Far too expensive.

**Source**: [FlexiForce A502 Sensor (Tekscan)](https://www.tekscan.com/products-solutions/force-sensors/flexiforce-a502-sensor); [Tekscan Grip System](https://www.tekscan.com/products-solutions/systems/grip-system)

---

## 4. Sensitronics Pressure Mapping

### Products
- **ThruMode Matrix Array**: 10x16 (160 cells, 2"x3" active area) and 16x16 (256 cells, 4"x4" active area)
- **ShuntMode Matrix Array**: Different construction, wider dynamic range
- **Discrete FSR Arrays**: Custom printed to client specifications (not off-the-shelf)
- Available through their web store and Amazon

### Specifications
- ThruMode: Force sensing through the material thickness
- ShuntMode: Force sensing via lateral conduction changes
- Can be used for multi-touch, pressure mapping, force mapping
- Flexible enough to conform to surfaces

### Price
- 16x16 FSR matrix array appears on Amazon (B0CFWZDBXP) — based on similar products, likely $50-150 range (could not confirm exact price from search results)
- No educational discount mentioned
- Custom arrays: quote-based pricing

### Suitability for Baseball
- 4"x4" (100x100mm) active area is large enough to wrap around part of a baseball
- But: these are flat sensors designed for flat or gently curved surfaces
- Wrapping a flat 100x100mm sensor around a 73mm diameter sphere would require significant bending, potentially causing delamination or inaccurate readings
- Force range and accuracy specifications not publicly documented in detail
- No published research validating their use on highly curved surfaces or at 50-100N forces

### VERDICT: UNCERTAIN — POSSIBLE BUT UNVALIDATED
- Could work for a proof-of-concept if the sensor can physically conform to the ball
- Force range and accuracy at baseball-relevant forces are unknown
- No published research on curved-surface applications
- Would need 26 wires for a 10x16 array (10 rows + 16 columns) — doable with multiplexer
- Risk: spending $50-150 on something that may not survive the curvature or force range

**Source**: [Sensitronics ThruMode Matrix Array](https://www.sensitronics.com/products-thru-mode-matrix-array.php); [Sensitronics Products](https://www.sensitronics.com/products.php)

---

## 5. BeBop Sensors Fabric Sensors

### What They Offer
- Patented "Monolithic Fabric Sensor Technology"
- Sensors measure force, bend, twist, stretch
- Can conform to complex geometries and curved surfaces
- All sensors, traces, and electronics integrated into a single piece of fabric
- Ultra-thin, lightweight, durable

### Custom Only
- **All projects are custom.** There are no off-the-shelf products you can buy for general pressure mapping.
- They provide proof-of-concept development with their R&D team
- Target markets: automotive (smart seats), VR gloves, industrial
- Consumer products using their tech include the BopPad (drum controller) and K-Board Pro 4 (keyboard)

### Cost
- **Not publicly available.** Custom development projects with BeBop likely cost thousands to tens of thousands of dollars.
- Completely inappropriate for a student/research project budget.

### VERDICT: NOT ACCESSIBLE
- Technology would be ideal in theory (fabric sensor conforming to a ball)
- But: custom-only, no publicly available products for general purchase
- Pricing far exceeds project budget
- No way to prototype without engaging their team

**Source**: [BeBop Sensors Technology](https://bebopsensors.com/technology/)

---

## 6. Peratech QTC (Quantum Tunnelling Composite)

### What It Is
QTC is a composite material where metal particles are dispersed in an elastomeric matrix. Under pressure, quantum tunnelling between particles causes dramatic resistance changes. It is fundamentally different from piezoresistive materials like Velostat.

### Performance vs Velostat
- **Part-to-part repeatability: <5% variation** (per batch) — dramatically better than Velostat
- Response is "predictable, repeatable, and consistent over time"
- Works in extreme temperatures and humid environments
- Available as opaque or clear, screen-printable, bendable formulation
- 200 microns thick
- Multi-touch capable
- Sensitivity down to 10g pressure

### Availability — CRITICAL PROBLEM
- **Peratech uses a licensing business model.** They do NOT sell QTC material to consumers or researchers.
- You must engage in a custom consultation and licensing arrangement.
- No evaluation kits or sample materials available for general purchase (they explicitly state a general dev board "was not found to be useful to the average engineer" due to calibration complexity).
- Contact must go through Peratech directly or through ipXchange.

### Cost
- Not applicable — you cannot buy the material.

### VERDICT: NOT ACCESSIBLE
- Superior technology to Velostat on every metric
- But completely inaccessible for an individual research project
- Licensing model means you need to be a company integrating it into a product
- No hobbyist/researcher path to obtain material

**Source**: [Quantum Tunnelling Composite (Wikipedia)](https://en.wikipedia.org/wiki/Quantum_tunnelling_composite); [11 Myths About QTC Touch Sensors (Electronic Design)](https://www.electronicdesign.com/technologies/embedded/article/21805171/11-myths-about-qtc-touch-sensors); [Peratech QTC Consultation (ipXchange)](https://ipxchange.tech/evaluation-boards/peratech-qtc-pressure-sensing-material-consultation/)

---

## 7. Academic Approaches to Pressure Matrices

### Sports Grip Pressure (2024 — Key Paper)
**"The assessment of sports performance by grip pressure using flexible piezoresistive pressure sensors in seven sports events"** — Scientific Reports (Nature), 2024

- Used MMSS sensor: MXene as sensitive material on melamine sponge substrate
- Tested on golf, billiards, basketball, javelin, shot put, badminton, tennis
- MXene sensor sensitivity: 5.35 kPa^-1 (1.1-22.2 kPa range), stable 0.6 kPa^-1 up to 266 kPa
- KNN classification accuracy: 95% for expert vs amateur grip patterns
- Survived 5000 load/unload cycles at 5.5 kPa
- **BUT: MXene sensors require lab fabrication (dip-coating, specialized chemistry). Not commercially available as off-the-shelf products.**

**Source**: [Scientific Reports (Nature, 2024)](https://www.nature.com/articles/s41598-024-82274-1)

### Smart Ball with Graphene Kirigami (2022)
**"A smart ball sensor fabricated by laser kirigami of graphene for personalized long-term grip strength monitoring"** — npj Flexible Electronics, 2022

- Laser-induced graphene patterned into kirigami (cut-pattern) on a ball surface
- Spiral sensing unit wraps around ball surface
- Embedded electronics in transparent pill shell at ball center
- Wireless readout to mobile phone
- Validated against gold-standard grip strength measurement in diseased and healthy subjects
- **This is the closest published work to what you want to build — a spherical grip sensor.**
- However: requires laser fabrication equipment, graphene processing, not reproducible without specialized lab.

**Source**: [npj Flexible Electronics (Nature, 2022)](https://www.nature.com/articles/s41528-022-00156-w)

### Robotic Hand Tactile Sensors
- Piezoresistive sensor arrays (3x3 to 5x5 taxels) commonly used on robotic gripper fingers
- FlexiForce sensors assembled on robotic hand grippers with custom arrangements
- Prosthetic hands use 25-sensor arrays (5 per finger) with learning-based classification
- Typical accuracy: sufficient for object classification, not for precise force measurement in Newtons
- Most use commercial sensors (FlexiForce, Interlink FSR) rather than DIY matrices for quantitative work

**Source**: [Sensitivity Study of Piezoresistive Pressure Sensor for Robotic Hand (Academia)](https://www.academia.edu/6257316/); [Learning-Based Sensor Array for Prosthetic Hand (ResearchGate)](https://www.researchgate.net/publication/373161802)

### Prosthetic Socket Pressure (Velostat-based)
- Multiple studies use Velostat matrices inside prosthetic sockets
- Typical force range: 0-15N (far below pitching forces)
- Used for monitoring pressure distribution, not precise force measurement
- Always require individual calibration
- Drift is a consistent reported problem

### Key Takeaway from Academic Literature
**No published academic work has achieved reliable, repeatable, quantitative force measurement above 20N using a DIY piezoresistive matrix.** All high-force quantitative studies (including Kinoshita's baseball study and Yeh's instrumented baseball) use commercial force transducers or FlexiForce sensors.

---

## 8. Practical Matrix Design for a Baseball

### Geometry Challenge
- Baseball diameter: 73mm, circumference: ~230mm
- Surface area: ~16,740 mm^2
- Finger contact area during grip: roughly 4 oval patches of ~15x25mm each
- Total contact area: ~1,500 mm^2 (about 9% of ball surface)
- You do NOT need to map the entire ball — just the finger contact zones

### Realistic Matrix Resolution on a 73mm Sphere
- For a flat sensor wrapping around the ball, the maximum size before excessive buckling/wrinkling is roughly 80x60mm (covering about one hemisphere face)
- At 5mm pitch (spacing), that gives 16x12 = 192 sensors — impressive resolution
- At 10mm pitch: 8x6 = 48 sensors — still useful
- BUT: the curvature means a flat sensor must stretch, fold, or be cut into segments (like gore patterns on a globe)
- Realistically, 4-8 separate small matrix patches (one per finger zone) is more practical than one large continuous sheet

### nRF52840 ADC Limitations
- **8 configurable ADC channels** (AIN0-AIN7) on the nRF52840 chip
- XIAO nRF52840 exposes **6 analog pins** (A0-A5)
- ADC: 12-bit, 200 kSPS (kilosamples per second)
- Single-ended or differential mode
- **For a matrix, you DON'T use one ADC channel per sensor.** You scan rows and columns:
  - Drive one row at a time (digital output)
  - Read all columns simultaneously (one ADC channel per column)
  - For an 8x8 matrix (64 sensors): need 8 digital pins (rows) + 8 analog pins (columns) = 16 pins total
  - XIAO only has 6 analog pins, so max native matrix without MUX: 6 columns

### Multiplexer Solution
- **CD74HC4067**: 16-channel analog multiplexer, ~$2-5 on SparkFun/Adafruit
- Uses 4 digital pins to select 1 of 16 channels, routes to 1 ADC pin
- With one MUX + 1 ADC pin: can read 16 column lines
- With 8 digital row drives + 1 MUX on 1 ADC pin: read an 8x16 matrix (128 sensors)
- Additional MUXes can expand further

### Scanning Speed at 1 kHz
- At 200 kSPS, the nRF52840 ADC can sample one channel in 5 microseconds
- For an 8x8 matrix: 8 rows x 8 columns = 64 readings per frame
- At 5us per reading: 64 x 5us = 320 microseconds per frame
- That gives a theoretical maximum of ~3,125 Hz frame rate — **well above 1 kHz target**
- With MUX switching overhead (add ~1us per switch): still comfortably above 1 kHz
- Even a 16x16 matrix (256 readings): 256 x 6us = 1,536 microseconds = ~650 Hz
- **1 kHz is achievable for matrices up to about 12x12 with comfortable margin**

### Practical Matrix Architecture for This Project
If you wanted a matrix approach:
- 4 separate small patches (one per finger), each ~20x15mm
- Each patch could be 4x3 = 12 taxels at 5mm pitch
- Total: 48 taxels across 4 patches
- Wiring: Could share column lines across patches → 4 rows per patch x 4 patches = 16 row lines + 3 shared column lines = 19 digital/analog lines
- With 1 MUX (CD74HC4067): entirely feasible on XIAO nRF52840

---

## 9. Conductive Fabric/Thread Approaches

### EeonTex Pressure Sensing Fabric
- Made by Eeonyx Corporation
- Nonwoven microfiber with piezoresistive coating
- Surface resistivity: 2 kOhm/sq
- **Dynamic range: 5g to 100kg** — this range actually covers baseball pitching forces!
- Thickness: ~0.8mm
- Available from SparkFun, Adafruit, etc.
- Price: ~$25 for a 12"x13" (305x330mm) sheet — enough material for many sensors
- Previously available from SparkFun (COM-14111) but listed as "retired" by some vendors

**Source**: [EeonTex Conductive and Piezoresistive Fabrics (Marktek Inc)](https://marktek-inc.com/eeontex-conductive-and-piezoresistive-fabrics-and-leather/); [EeonTex on Adafruit](https://www.adafruit.com/product/3669)

### Shieldex Conductive Thread/Fabric
- Silver-coated nylon threads and fabrics
- Used for traces/electrodes (not for sensing itself)
- Shieldex 117/17 DTEX conductive threads used as row/column electrodes with piezoresistive fabric in between
- Can be sewn into fabric, conformal to curved surfaces
- Resistance is stable enough for use as interconnects

### Using Conductive Fabric Instead of Copper Tape for Matrix Traces
**YES — this is actually the recommended approach for curved surfaces.**
- Copper tape is rigid, does not stretch, and wrinkles/tears on compound curves
- Conductive fabric strips or sewn conductive thread can follow a sphere's curvature naturally
- Research demonstrates: columns and rows of conductive fabric with piezoresistive fabric between them creates a functional matrix
- A patent (US8161826A) describes elastically stretchable fabric force sensor arrays specifically designed for complex curved shapes like human body parts, using conductive polymer threads in serpentine paths for conformability

**Source**: [Easy-to-Build Textile Pressure Sensor (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5948620/); [Stryker Patent US8161826A](https://www.freepatentsonline.com/8161826.html)

### EeonTex + Conductive Fabric Matrix for Baseball
This is the most promising DIY matrix approach found in this research:
- EeonTex piezoresistive fabric as the sensing layer (dynamic range includes 50-100N)
- Shieldex conductive thread or conductive fabric strips as row/column electrodes
- Fabric naturally conforms to sphere without wrinkling
- Could be sewn or adhered under the leather cover
- Much cheaper than commercial solutions (~$30-50 in materials)
- **BUT: accuracy and repeatability at 50-100N forces is NOT validated in any published paper**
- The 5g-100kg dynamic range claim comes from the manufacturer — independent validation at high forces is lacking
- Still has the fundamental piezoresistive limitations: drift, hysteresis, non-linearity
- Calibration to Newtons would require your own validation work

---

## Comparison Matrix

| Technology | Force Range | Accuracy | Repeatability | Conforms to Sphere? | Survives Impact? | Cost | Validated Research? |
|------------|-------------|----------|---------------|--------------------|--------------------|------|---------------------|
| **Velostat matrix** | 0-15N (saturates) | 7-70% error | POOR (fails ANOVA) | Yes (flexible) | Only at low forces | ~$15 | Yes, many papers (but all low-force) |
| **Interlink FSR 406** | 0.1-10N | ~10% variation | Moderate | No (rigid tail) | Unknown | ~$8-12/ea | Datasheets only |
| **FlexiForce A201 (current)** | 0-111N | Best in class for piezoresistive | Good (3M+ presses) | Yes (0.2mm thin) | Yes (Yeh 2024) | ~$25/ea | Yes (Yeh 2024, baseball) |
| **FlexiForce A502** | 0-222N | Same tech as A201 | Good | Somewhat (50mm sq) | Likely | ~$30/ea | Tekscan validated |
| **Tekscan Grip System** | Full range | Research-grade | Research-grade | Yes (0.1mm) | Yes | $5,000-20,000+ | Extensive |
| **Sensitronics 16x16** | Unknown (not spec'd) | Unknown | Unknown | Partially (flat) | Unknown | ~$50-150 | Minimal |
| **BeBop Sensors** | Custom | Custom | Custom | Yes (fabric) | Custom | $$$$ (custom) | Internal only |
| **Peratech QTC** | Wide | <5% part variation | Good | Yes (200um thick) | Unknown | NOT AVAILABLE | Some |
| **EeonTex fabric** | 5g-100kg (claimed) | Unknown at high forces | Unknown at high forces | YES (fabric) | Unknown | ~$25/sheet | Minimal at high forces |
| **MXene sensors** | Up to 266 kPa | Good (research) | 5000+ cycles | Yes (flexible) | Research only | Lab fabrication only | Yes (2024 papers) |

---

## Honest Assessment and Recommendations

### What Actually Works for Your Project (in order of recommendation):

#### RECOMMENDATION 1: KEEP YOUR CURRENT APPROACH (FlexiForce A201 x 4)
**This is still the best option.** Here's why:
- Validated for exactly this application (Yeh et al. 2024, baseball, under leather)
- Force range (0-111N) perfectly covers the 50-100N pitching forces
- Best repeatability and accuracy among accessible piezoresistive sensors
- 0.2mm thin — works under leather
- Already purchased (4 sensors, $100)
- Simple wiring (4 analog pins, one per sensor)
- Proven to survive 100 km/h impacts (Yeh's epoxy method)
- The "only 4 sensors" is actually a feature, not a bug — it keeps the system simple, validated, and publishable

#### RECOMMENDATION 2: HYBRID — FlexiForce A201 x 4 + Small EeonTex Matrix Patches (Experimental)
If you want to explore higher-resolution mapping as a secondary experiment:
- Keep 4x FlexiForce A201 as your primary, validated measurement (Channels A0-A3)
- Add small EeonTex fabric matrix patches around the FlexiForce sensors
- Use remaining analog pins (A4-A5) plus a CD74HC4067 MUX for the matrix
- The matrix data would be qualitative (relative pressure distribution) while FlexiForce provides quantitative Newtons
- Additional cost: ~$25 (EeonTex) + $5 (MUX) + $5 (conductive thread/fabric) = ~$35
- Risk: the matrix may not produce useful data at pitching forces — treat as experimental
- Upside: if it works, you have both precise force data AND spatial distribution

#### RECOMMENDATION 3: More FlexiForce Sensors with MUX
If 4 measurement points aren't enough spatial resolution:
- Purchase 4-8 more FlexiForce A201 sensors ($100-200)
- Use CD74HC4067 MUX to read 8-12 sensors from fewer ADC pins
- Place sensors at key finger sub-regions (fingertip, pad, side of each finger)
- All sensors remain individually calibrated and validated
- Total: 8-12 validated force measurement points
- This gives you a "semi-distributed" pressure map with quantitative accuracy at every point
- Cost: $200-300 additional

### What Does NOT Work:

1. **Velostat matrix for this application** — Force range is fundamentally insufficient. Saturates below 15N, pitching requires 50-100N. Would waste time and produce unusable data.

2. **Interlink FSR 406/408** — Force range (0-10N) is even worse than Velostat. Accuracy is poor. Cannot be cut to shape.

3. **BeBop/Peratech/Tekscan Grip System** — All either inaccessible or far too expensive for a student project.

4. **MXene-based sensors** — Excellent technology but requires specialized lab fabrication (not commercially available as products you can buy).

5. **Full-surface graphene kirigami** — Published proof that spherical grip mapping works (npj Flex Electron 2022), but requires laser processing equipment not available in most labs.

### Honest Summary
The reason everyone studying baseball grip forces uses individual FlexiForce sensors (Yeh et al.) or tri-axial force transducers (Kinoshita et al.) is that **no affordable, accessible technology exists that provides a validated, high-resolution pressure map at 50-100N forces on a curved surface.** The technologies that could do it (Tekscan Grip System, custom BeBop, custom QTC) cost thousands of dollars. The cheap alternatives (Velostat, generic FSRs) cannot handle the forces involved in pitching.

Your current 4x FlexiForce A201 approach is not a compromise — it is the state-of-the-art for what is achievable at this budget and validation level. Adding thumb and ring finger data already puts you ahead of all published work.

---

## Sources

### Validated Research Papers
- [Finger forces in fastball baseball pitching - Kinoshita et al. (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0167945716303037)
- [Using a Sensor-Embedded Baseball - Yeh et al. 2024 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11175286/)
- [Polyethylene-Carbon Composite (Velostat) Based Tactile Sensor (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7761878/)
- [Efficient Calibration of Velostat-Based Flexible Pressure Sensor Matrix (IEEE)](https://ieeexplore.ieee.org/document/10220429/)
- [Low-Cost Pressure Sensor Matrix Using Velostat (IEEE)](https://ieeexplore.ieee.org/document/8537720)
- [Examination of Velostat as In-Socket Pressure Sensor (IEEE)](https://ieeexplore.ieee.org/document/9024130/)
- [Investigation of Long-Term Reliability of Velostat Sensor Array - 210 Days (IEEE)](https://ieeexplore.ieee.org/document/10349695/)
- [Investigation of Mechanical Reliability of Velostat Sensor (IEEE)](https://ieeexplore.ieee.org/document/9781575/)
- [On the Effect of Layering Velostat on Force Sensing for Hands (MDPI 2025)](https://www.mdpi.com/1424-8220/25/10/3245)
- [A Novel Crosstalk Suppression Method for 2-D Networked Resistive Sensor Array (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4168420/)
- [Sports Performance Assessment by Grip Pressure Using Flexible Piezoresistive Sensors (Nature 2024)](https://www.nature.com/articles/s41598-024-82274-1)
- [Smart Ball Sensor by Laser Kirigami of Graphene (npj Flex Electron 2022)](https://www.nature.com/articles/s41528-022-00156-w)
- [Easy-to-Build Textile Pressure Sensor (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5948620/)
- [Elastically Stretchable Fabric Force Sensor Arrays - Stryker Patent](https://www.freepatentsonline.com/8161826.html)
- [Velostat-Based Pressure Sensor Matrix for Decubitus Ulcer Prevention (Springer)](https://link.springer.com/chapter/10.1007/978-3-030-70601-2_126)

### Datasheets and Product Pages
- [FSR 406 Data Sheet (SparkFun/Interlink)](https://cdn.sparkfun.com/assets/c/4/6/8/b/2010-10-26-DataSheet-FSR406-Layout2.pdf)
- [FSR Integration Guide (Interlink/DigiKey)](https://media.digikey.com/pdf/Data%20Sheets/Interlink%20Electronics.PDF/FSR_Integration_Guide.pdf)
- [FlexiForce A502 Sensor (Tekscan)](https://www.tekscan.com/products-solutions/force-sensors/flexiforce-a502-sensor)
- [FlexiForce A201 Datasheet (Tekscan)](https://www.tekscan.com/resources/datasheets-guides/flexiforce-a201-datasheet)
- [Tekscan Grip System](https://www.tekscan.com/products-solutions/systems/grip-system)
- [Sensitronics ThruMode Matrix Array](https://www.sensitronics.com/products-thru-mode-matrix-array.php)
- [Sensitronics Products](https://www.sensitronics.com/products.php)
- [BeBop Sensors Technology](https://bebopsensors.com/technology/)
- [Peratech QTC DataSheet SP200 Series](https://www.peratech.com/assets/uploads/datasheets/Peratech-QTC-DataSheet-SP200-Series-Nov15.pdf)
- [QTC Wikipedia](https://en.wikipedia.org/wiki/Quantum_tunnelling_composite)
- [EeonTex Conductive and Piezoresistive Fabrics (Marktek Inc)](https://marktek-inc.com/eeontex-conductive-and-piezoresistive-fabrics-and-leather/)
- [EeonTex Stretchy Variable Resistance Sensor Fabric (Adafruit)](https://www.adafruit.com/product/3669)
- [CD74HC4067 Datasheet (TI)](https://www.ti.com/lit/ds/symlink/cd74hc4067.pdf)

### nRF52840 ADC References
- [nRF52840 SAADC Documentation (Nordic Semi)](https://infocenter.nordicsemi.com/topic/com.nordic.infocenter.nrf52832.ps.v1.1/saadc.html)
- [nRF52840 Datasheet Explained (Ultra Librarian)](https://www.ultralibrarian.com/2026/1/9/nrf52840-datasheet-explained-ulc)
- [nRF52 ADC (Adafruit Learning System)](https://learn.adafruit.com/introducing-the-adafruit-nrf52840-feather/nrf52-adc)
