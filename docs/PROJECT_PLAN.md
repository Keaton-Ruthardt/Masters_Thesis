# Instrumented Baseball Project Plan
## Master's Project: Pressure-Sensing Baseball for Pitch Analysis

**Project Goal**: Design and build a research-grade instrumented baseball that measures grip force and pressure distribution during a pitch to analyze how grip variations affect spin and pitch movement.

**Key Innovation**: First 4-finger grip pressure map combined with on-board spin rate measurement (magnetometer DFT) — no external cameras or radar needed.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Research Background & Prior Art](#research-background--prior-art)
3. [System Architecture](#system-architecture)
4. [Component List](#component-list)
5. [Build Phases](#build-phases)
6. [How This Advances Beyond Prior Art](#how-this-advances-beyond-prior-art)
7. [Technical Challenges](#technical-challenges)
8. [Budget Estimate](#budget-estimate)
9. [References](#references)

---

## Project Overview

### Objective
Create a baseball with embedded sensors that can:
- Measure pressure distribution at 4 finger contact points (index, middle, thumb, ring)
- Estimate release velocity via accelerometer integration (H3LIS331DL, ±400g)
- Measure spin rate at any RPM via magnetometer DFT (LIS3MDL — no saturation limit)
- Detect impact forces up to ±400g (H3LIS331DL)
- Transmit data wirelessly in real-time via BLE 5
- Charge wirelessly (no exposed ports)
- Maintain regulation weight and balance (142–149g)

### What Makes This Novel
Existing products like PitchLogic measure ball flight metrics (spin, velocity) but do NOT measure grip pressure distribution. Existing research (Yeh et al. 2024) measured only 2 fingers on a single pitch type. This project fills that gap by capturing:
- **4-finger pressure** — index, middle, thumb, and ring finger (thumb and ring data completely absent from literature)
- **Multiple pitch types** — 4-seam, 2-seam, changeup, curveball
- **Self-contained spin measurement** — DFT of magnetometer signal (Diamond Kinetics' patented approach), no external camera/radar
- **Open hardware design** — fully documented for reproducibility, unlike commercial products

---

## Research Background & Prior Art

### Key Prior Art

#### McGinnis 2012 — Miniaturized Wireless IMU for Baseballs
- Embedded a ~30×25mm rigid PCB inside a regulation baseball
- Proved ±0.1g mass accuracy by machining pockets in the core
- Used nRF51-series MCU with BLE
- **Key insight**: Rigid PCB works; circular/flex unnecessary
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC3478818/

#### Diamond Kinetics — Patented Spin Rate Method
- Uses DFT (Discrete Fourier Transform) of magnetometer signal to measure spin rate
- **Key advantage**: No gyro saturation — works at any RPM (gyros saturate at ±4000°/s = 66.7 rev/s = 4000 RPM, but elite fastballs reach 2500+ RPM and some spin axes exceed this)
- Commercial product (not open source)

#### PitchLogic — Industry Standard Smart Baseball
- Uses nRF52840 MCU with BLE 5
- Runs 3 hours on a 40mAh battery (BLE is key — Wi-Fi would drain in <1 hour)
- Measures velocity, spin rate, spin axis, spin efficiency, release point
- No grip pressure measurement
- Source: https://pitchlogic.com/howitworks

#### Kookaburra SmartBall (Cricket)
- Also uses nRF52840 + BLE
- Confirms industry convergence on this MCU for ball-embedded electronics

#### Yeh et al. 2024 — Sensor-Embedded Baseball (MDPI)
- 2× FlexiForce A301 sensors (index + middle finger only)
- 4-seam fastball only, seated 3m throw (not full pitching motion)
- Epoxy-coated central electronics survived 100 km/h wall impact
- FlexiForce sensors under leather cover — leather transmits force, preserves grip feel
- Re-wound yarn around electronics for mass compensation
- Sealed with styrene-acrylic polymer adhesive
- Ball survived real pitching by 21 college pitchers at 70–86 mph
- Source: https://www.mdpi.com/1424-8220/24/11/3523

### Why nRF52840 Over ESP32
| Factor | ESP32 | nRF52840 |
|--------|-------|----------|
| Wireless | Wi-Fi + BLE 4.2 | BLE 5 only (2 Mbps) |
| Power (active BLE) | ~130mA (Wi-Fi wastes power) | ~8mA |
| Sleep current | ~10µA | <1µA (system OFF) |
| Battery life (100mAh) | <1 hr (Wi-Fi), ~3 hr (BLE only) | 8–10 hr active BLE |
| Industry adoption | Hobbyist IoT | PitchLogic, Kookaburra, commercial sports |
| Analog pins | 4 usable (ADC2 conflicts with Wi-Fi) | 6 (A0–A5 on XIAO) |
| Package size (QFN) | 18×25.5mm (module) | 7×7mm (bare chip) |
| Dev board | Beetle ESP32 (35×34mm, $12) | Seeed XIAO nRF52840 (21×17mm, $10) |
| FPU | No hardware FPU | ARM Cortex-M4F (hardware FPU for DFT) |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  INSTRUMENTED BASEBALL                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ FlexiForce   │  │  H3LIS331DL  │  │  LIS3MDL     │  │
│  │ A201 (×4)    │  │  ±400g Accel │  │ Magnetometer │  │
│  │ Grip pressure│  │  Velocity +  │  │ Spin rate    │  │
│  └──────┬───────┘  │  Impact det. │  │ via DFT      │  │
│         │ Analog   └──────┬───────┘  └──────┬───────┘  │
│         │                 │ I2C              │ I2C      │
│  ┌──────▼─────────────────▼──────────────────▼───────┐  │
│  │           Seeed XIAO nRF52840                     │  │
│  │  - 64MHz ARM Cortex-M4F (hardware FPU)            │  │
│  │  - 6 analog pins (A0-A5)                          │  │
│  │  - BLE 5 (2 Mbps, low power)                      │  │
│  │  - 256KB RAM / 1MB Flash                          │  │
│  │  - Ultra-low-power sleep (<5µA)                   │  │
│  └──────────────┬────────────────────────────────────┘  │
│                 │                                       │
│  ┌──────────────▼────────────────────────────────────┐  │
│  │           Power Management                        │  │
│  │  - 100-150mAh LiPo (centered)                     │  │
│  │  - MCP73831T charge controller                    │  │
│  │  - Qi wireless charging coil                      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │ BLE 5
                         ▼
              ┌──────────────────────┐
              │   Phone App          │
              │   - nRF Connect      │
              │   - Custom app later │
              │   - Data logging     │
              └──────────────────────┘
```

### I2C Bus Map (Final PCB)
```
nRF52840 ── SDA ── SCL
  ├── H3LIS331DL  @ 0x18  (3-axis accel, ±400g — velocity + impact)
  └── LIS3MDL     @ 0x1C  (3-axis magnetometer — spin rate via DFT)

Pull-ups: 2× 4.7kΩ on SDA/SCL

Note: ISM330DHCX (gyroscope) was removed from the design.
The gyroscope saturates at ±4000°/s (~666 RPM per axis), which is
below every real pitch. Spin rate is measured via magnetometer DFT
instead (Diamond Kinetics' patented approach). Velocity is estimated
by integrating H3LIS331DL acceleration data during the throw.
Release detection uses FlexiForce pressure dropout (more precise
than accelerometer-based detection).
```

### ADC Pin Assignments (XIAO nRF52840)
```
Sensor 1 (Index)  → A0
Sensor 2 (Middle) → A1
Sensor 3 (Thumb)  → A2
Sensor 4 (Ring)   → A3
(A4, A5 available for future expansion)
```

### Data Flow
1. Pressure sensors detect finger force at 4 contact points
2. H3LIS331DL captures 3-axis acceleration (velocity estimation via integration + impact detection)
3. LIS3MDL captures 3-axis magnetic field → DFT → spin rate (RPM)
4. FlexiForce pressure dropout = release point (more precise than accelerometer-based detection)
5. nRF52840 reads all sensors at 100 Hz (upgradeable to 1 kHz)
6. Data transmitted via BLE 5 to phone/laptop
7. Receiving device logs, visualizes, and analyzes data

---

## Component List

### Components Already Purchased

| Component | Specifications | Status |
|-----------|---------------|--------|
| **DFRobot Beetle ESP32** | 35×34mm, BLE+WiFi, 4 analog pins | Phase 1 prototype (retired) |
| **Adafruit MPU-6050** | 3-axis accel (±16g) + 3-axis gyro (±2000 dps) | Phase 1-2 dev IMU |
| **FlexiForce A201** (×4) | 0–25 lb, 9.5mm sensing area, 0.2mm thick | Purchased |
| **ISM330DHCX breakout** | 6-axis gyro+accel, ±4000°/s, I2C 0x6A | Purchased (used for Phase 2 testing; NOT on final PCB — gyro saturates on every real pitch) |
| **H3LIS331DL breakout** | 3-axis ±400g accel, I2C 0x18 | Purchased |
| **MCP73831T** | LiPo charge controller, SOT-23-5 | Purchased |
| **100mAh LiPo battery** | 3.7V, ~2g | Purchased |
| **Qi receiver module** | 20mm coil | Purchased |
| **Breadboard + Jumper Wires** | Half-size breadboard, assorted wires | In use |
| **Soldering Iron Kit** | 60W adjustable temperature | Purchased |
| **Resistor Kit** | Assorted values including 10kΩ | Purchased |
| **Practice baseballs** (×3) | For testing sensor placement | Purchased |
| **Regulation baseballs** (×2) | Final integration | Purchased |
| **30 AWG wire** (50ft) | Thin sensor leads | Purchased |
| **2-part epoxy** | Shock protection for electronics | Purchased |
| **Conformal coating spray** | Waterproof electronics | Purchased |

### Still Need to Purchase

| Component | Specifications | Source | Cost |
|-----------|---------------|--------|------|
| **Seeed XIAO nRF52840** | 21×17mm, BLE 5, 6 analog pins, ARM Cortex-M4F | [Seeed Studio](https://www.seeedstudio.com/Seeed-XIAO-BLE-nRF52840-p-5201.html) | $10 |
| **LIS3MDL breakout** | 3-axis magnetometer, I2C 0x1C, 3×3mm | [Adafruit](https://www.adafruit.com/product/4479) | $5 |
| **Custom rigid PCB** (5 pcs) | ~30×25mm, 2-layer rigid | [JLCPCB](https://jlcpcb.com) | $15–30 |
| **Remaining total** | | | **$30–45** |

---

## Build Phases

### Phase 1: Proof of Concept — COMPLETE
**Goal**: Validate sensor selection and basic data pipeline

- [x] Order initial components (ESP32, FlexiForce ×2, MPU-6050)
- [x] Set up Arduino IDE with ESP32 board support
- [x] Build breadboard prototype
- [x] Test MPU-6050 IMU communication (I2C, accel + gyro reading)
- [x] Test FlexiForce pressure sensor with voltage divider circuit
- [x] Combine IMU and pressure data in single firmware
- [x] Implement BLE data transmission ("SmartBaseball" device)
- [x] Verify BLE data received on phone (nRF Connect app)
- [x] Build 3D baseball visualization in Processing

**Deliverable**: Working breadboard prototype with wireless data transmission and 3D visualization

**Key Findings from Phase 1**:
- FlexiForce A201 requires 10kΩ voltage divider per sensor
- Beetle ESP32 analog pins: A0=GPIO36, A1=GPIO39, A2=GPIO34, A3=GPIO35
- BLE library adds significant compile time (~3–5 min first build)
- FlexiForce middle pin (Pin 2) is inactive — only outer pins used
- MPU-6050 connects via I2C on SDA/SCL pins

### Phase 2: nRF52840 Migration + 4-Sensor Array (Weeks 5–10)
**Goal**: Switch to nRF52840 platform and expand to 4 pressure sensors

**Phase 2A — Hardware Setup**
- [ ] Order Seeed XIAO nRF52840 ($10) and 2 more FlexiForce A201 ($50)
- [ ] Install Seeed nRF52840 board support in Arduino IDE
- [ ] Wire MPU-6050 to XIAO via I2C (SDA/SCL)
- [ ] Wire 4× FlexiForce sensors to analog pins A0–A3 with 10kΩ voltage dividers

**Phase 2B — Firmware Rewrite**
- [ ] Port BLE transmission from ESP32 BLE library → ArduinoBLE (nRF52840)
- [ ] BLE service: "SmartBaseball" with characteristics for pressure[4] + IMU[6] + mag[3]
- [ ] Implement IMU reading via Wire library (same I2C code, should mostly port)
- [ ] Implement 4-channel ADC reading for pressure sensors
- [ ] Target 100 Hz sampling rate (XIAO ADC is 12-bit, 200 ksps)
- [ ] Implement sleep/wake via IMU motion interrupt (save power)

**Phase 2C — Finger Mapping & Grip Testing**
- [ ] Use ink/chalk method to identify finger contact points on baseball
- [ ] Document grip patterns for 4-seam, 2-seam, changeup, curveball
- [ ] Place sensors, test different grips, record pressure patterns
- [ ] Calibrate sensors (known weights → ADC values → Newtons)

**Deliverable**: Working 4-sensor + IMU prototype on XIAO nRF52840 with BLE streaming

### Phase 3: Miniaturization + Custom PCB (Weeks 11–16)
**Goal**: Custom rigid PCB with all sensors and power management

**Phase 3A — Breadboard Integration on XIAO**
- [ ] Add LIS3MDL magnetometer breakout to I2C bus (order from Adafruit, $5)
- [ ] Wire H3LIS331DL (already owned) to XIAO I2C bus
- [ ] Implement DFT-based spin rate algorithm (mag signal → FFT → peak freq = RPM)
- [ ] Implement velocity estimation (integrate H3LIS331DL accel during throw)
- [ ] Validate spin rate: hand-spin ball at known rates, compare DFT output
- [ ] Test all sensors working simultaneously on XIAO breadboard

**Phase 3B — PCB Design in KiCad**
- [ ] Target: ~30×25mm 2-layer rigid PCB (proven by McGinnis 2012)
- [ ] nRF52840 QFN-48 (bare chip, 7×7mm) with external 32 MHz crystal + antenna
- [ ] H3LIS331DL (LGA-16, 3×3mm) — I2C 0x18 (velocity + impact)
- [ ] LIS3MDL (LGA-12, 3×3mm) — I2C 0x1C (spin rate DFT)
- [ ] MCP73831T (SOT-23-5) — LiPo charge controller
- [ ] 4× 10kΩ 0603 resistors (voltage dividers)
- [ ] 2× 4.7kΩ 0603 resistors (I2C pull-ups)
- [ ] 4× 100nF + 1× 10µF 0603 caps (decoupling)
- [ ] Qi coil solder pads, LiPo JST pads, 4× sensor wire pads
- [ ] BLE antenna: chip antenna or PCB trace antenna
- [ ] Run DRC for JLCPCB capabilities
- [ ] Generate Gerbers, order from JLCPCB ($15–30 for rigid, 5 pcs)

**Phase 3C — Assembly & Test**
- [ ] Hand-solder or JLCPCB assembly service
- [ ] Verify both I2C devices respond (0x18, 0x1C)
- [ ] Flash firmware, verify BLE + all sensors
- [ ] Measure total mass (target: <7g board + <4g battery = <11g total)

**Deliverable**: Custom PCB with all sensors, BLE, and power management working

### Phase 4: Baseball Integration (Weeks 17–19)
**Goal**: Embed electronics into regulation baseball

Hybrid construction method (McGinnis 2012 + Yeh et al. 2024):
1. Unstitch half the leather cover (McGinnis method — preserves clean re-stitch)
2. Cut cork/rubber core in half (Yeh method — both halves accessible)
3. Partially remove compressed cork, yarn, and cotton to create cavity (~32×27×8mm)
4. Coat PCB + battery assembly in **epoxy** for shock protection (Yeh method — survived 100 km/h wall impact)
5. Place epoxy-coated electronics at ball's center of mass
6. Carve pocket below electronics for Qi coil
7. Attach 4× FlexiForce sensors **under the leather cover** (Yeh method — leather transmits force, preserves grip feel, protects sensors)
8. Route 4× sensor wires (30 AWG) through channels cut in yarn layers to central PCB
9. **Re-wind additional yarn** around electronics to compensate removed mass (Yeh method — target 142–149g)
10. Seal halves with **styrene-acrylic polymer** adhesive (Yeh method — flexible enough for impacts)
11. Re-stitch leather cover
12. Weigh — verify within regulation 142–149g (5.0–5.25 oz)
13. Spin test for balance — visual wobble check

**Why this hybrid approach:**
- McGinnis achieved ±0.1g mass accuracy by machining pockets in the core
- Yeh et al. proved FlexiForce sensors work under leather with epoxy-coated central electronics
- Yeh's yarn re-winding is simpler than CNC machining for mass compensation
- Yeh's ball survived real pitching by 21 college pitchers at 70–86 mph

**Deliverable**: Functional instrumented baseball

### Phase 5: Software & Analysis (Weeks 20–26)
**Goal**: Build data pipeline and analysis tools

- [ ] Develop Python data analysis pipeline
- [ ] Implement pitch detection algorithm (pressure spike → release event)
- [ ] Implement DFT spin rate computation (validate on-board vs post-processed)
- [ ] Correlation analysis: grip pressure patterns vs spin rate/velocity/movement
- [ ] Test with multiple pitchers
- [ ] Build data export functionality (CSV)
- [ ] Write thesis content
- [ ] Document findings

**Deliverable**: Complete system with analysis and thesis documentation

---

## How This Advances Beyond Prior Art

| Aspect | Yeh et al. 2024 (MDPI) | MastersBall (This Project) |
|--------|------------------------|---------------------------|
| Sensors | 2× FlexiForce A301 (index + middle only) | **4× FlexiForce A201** (index, middle, thumb, ring) |
| Pitch types | 4-seam fastball only | **Multiple pitch types** (4-seam, 2-seam, changeup, curve) |
| Force measurement | Seated, 3m throw | **Full pitching motion** |
| Spin/velocity source | External Rapsodo camera system | **On-board IMU + magnetometer** (self-contained) |
| Spin rate method | External measurement only | **DFT of magnetometer signal** (Diamond Kinetics approach) — no saturation limit |
| Sampling rate | 433 Hz | **1 kHz target** (nRF52840 ADC capable of 200 ksps) |
| Data transmission | Bluetooth (unspecified version) | **BLE 5** (2 Mbps, ultra-low power) |
| Impact detection | Not measured | **H3LIS331DL ±400g** accelerometer |
| Velocity | External Rapsodo | **H3LIS331DL acceleration integration** — self-contained |
| MCU | Not disclosed | **nRF52840** (same as PitchLogic — industry-proven) |
| Design openness | Chip models undisclosed | **Fully documented, reproducible** |
| Real-time feedback | No | **BLE streaming to phone app** |

**Key novel contributions:**
1. **First 4-finger grip pressure map** — thumb and ring finger data is completely absent from literature
2. **Multi-pitch-type grip analysis** — no existing study maps grip pressure across different pitch types
3. **Self-contained ball** — no external camera/radar needed for spin rate (magnetometer DFT approach)
4. **Open hardware design** — documented for reproducibility, unlike commercial products

---

## Technical Challenges & Solutions

| Challenge | Impact | Solution |
|-----------|--------|----------|
| **Spin measurement** | Gyroscopes saturate on every real pitch | LIS3MDL magnetometer DFT — no RPM limit; gyro removed from design |
| **Velocity estimation** | Need release speed without external radar | H3LIS331DL acceleration integration over throw (~0.5-1s); 4-6% accuracy (McGinnis 2012) |
| **Sensor durability** | Repeated impacts may damage sensors | Epoxy coating (Yeh method — survived 100 km/h) |
| **Sampling rate** | Need fast reads for pitch capture (~150ms window) | nRF52840 ADC at 200 ksps; target 1 kHz sampling |
| **BLE bandwidth** | BLE 5 can handle ~2 Mbps | Buffer locally, transmit between pitches if needed |
| **Weight/balance** | Must maintain regulation 142–149g | Center electronics, yarn re-winding for mass compensation |
| **Seam interference** | Sensors may affect grip feel | FlexiForce is 0.2mm thin under leather (Yeh method) |
| **Battery life** | Small battery, high sampling rate | BLE 5 ultra-low power; sleep/wake on motion interrupt; 8–10 hr target |
| **Environmental** | Sweat, dirt, impact | Epoxy-coated electronics, sealed leather shell |
| **Analog pin count** | Need 4 sensor channels | XIAO has 6 analog pins — direct wiring, no MUX needed |

---

## Budget Estimate

### Actual Spending (Phase 1)

| Item | Cost | Status |
|------|------|--------|
| DFRobot Beetle ESP32 | $12 | Purchased (Phase 1 only) |
| FlexiForce A201 ×2 | $50 | Purchased |
| Adafruit MPU-6050 | $7 | Purchased |
| Breadboard + Wire Bundle | $6 | Purchased |
| Soldering Iron Kit | $20 | Purchased |
| Resistor Kit | $9 | Ordered |
| **Phase 1 Total** | **$104** | |

### Already Spent

| Item | Cost | Status |
|------|------|--------|
| DFRobot Beetle ESP32 | $12 | Phase 1 prototype |
| FlexiForce A201 ×4 | $100 | Purchased |
| Adafruit MPU-6050 | $7 | Purchased |
| Breadboard + Wire Bundle | $6 | Purchased |
| Soldering Iron Kit | $20 | Purchased |
| Resistor Kit | $9 | Purchased |
| ISM330DHCX breakout | $12 | Purchased (Phase 2 testing) |
| H3LIS331DL breakout | $10 | Purchased |
| MCP73831T | $2 | Purchased |
| 100mAh LiPo | $6 | Purchased |
| Qi receiver module | $10 | Purchased |
| Practice baseballs ×3 | $15 | Purchased |
| Regulation baseballs ×2 | $15 | Purchased |
| 30 AWG wire, epoxy, conformal coat | $35 | Purchased |
| **Total Spent** | **$259** | |

### Remaining to Purchase

| Component | Cost | Phase |
|-----------|------|-------|
| Seeed XIAO nRF52840 | $10 | 2 |
| LIS3MDL breakout (Adafruit) | $5 | 3 |
| Custom rigid PCB (JLCPCB, 5 pcs) | $15–30 | 3 |
| **Remaining Total** | **$30–45** | |
| **Grand Total** | **$289–304** | |

---

## References

### Research Papers
1. **Sensor-Embedded Baseball for Finger Characteristics (Yeh et al. 2024)**
   - https://www.mdpi.com/1424-8220/24/11/3523
   - Key findings on finger force correlation with spin rate
   - Proved FlexiForce under leather + epoxy coating approach

2. **Highly Miniaturized Wireless IMU for Baseballs (McGinnis 2012)**
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC3478818/
   - IMU embedding approach and validation
   - ~30×25mm rigid PCB, ±0.1g mass accuracy

3. **Finger Forces in Fastball Pitching**
   - https://www.sciencedirect.com/science/article/abs/pii/S0167945716303037
   - Foundational biomechanics data

### Commercial Products
- PitchLogic: https://pitchlogic.com/howitworks (nRF52840 + BLE 5)
- Diamond Kinetics: Magnetometer DFT for spin rate (patented approach)
- Kookaburra SmartBall: nRF52840-based cricket ball

### Component Vendors
- Seeed Studio: https://www.seeedstudio.com (XIAO nRF52840)
- Tekscan FlexiForce: https://www.tekscan.com/force-sensors
- Adafruit: https://www.adafruit.com (sensor breakouts, batteries)
- DigiKey: https://www.digikey.com
- Mouser: https://www.mouser.com
- JLCPCB (PCB fab): https://jlcpcb.com

### Technical Resources
- Seeed XIAO nRF52840 Wiki: https://wiki.seeedstudio.com/XIAO_BLE/
- ArduinoBLE Library: https://www.arduino.cc/reference/en/libraries/arduinoble/
- FlexiForce Datasheet: https://www.tekscan.com/resources/datasheets-guides/flexiforce-a201-datasheet

---

## Progress Log

| Date | Phase | Activity | Status |
|------|-------|----------|--------|
| 2026-01-27 | Planning | Initial research and project plan created | Complete |
| 2026-02-16 | Phase 1 | Set up Arduino IDE + ESP32 board support | Complete |
| 2026-02-16 | Phase 1 | MPU-6050 IMU tested — accel + gyro working | Complete |
| 2026-02-16 | Phase 1 | FlexiForce pressure sensor tested — voltage divider working | Complete |
| 2026-02-16 | Phase 1 | Combined pressure + IMU data in single firmware | Complete |
| 2026-02-16 | Phase 1 | BLE transmission working — "SmartBaseball" visible on phone | Complete |
| 2026-02-16 | Phase 1 | 3D baseball visualization built in Processing | Complete |
| 2026-02-16 | Phase 1 | **PHASE 1 COMPLETE** | Complete |
| 2026-03-04 | Planning | Architecture revision: ESP32 → nRF52840, flex → rigid PCB, added magnetometer | Complete |

---

## Notes

- FlexiForce A201 middle pin (Pin 2) is not connected — only outer pins are active
- XIAO nRF52840 analog pins: A0–A5 (6 available, need 4 for sensors)
- BLE device broadcasts as "SmartBaseball" — visible in nRF Connect
- 10kΩ resistor needed per sensor for voltage divider circuit
- USB-C on XIAO (not Micro USB like Beetle ESP32)
- nRF52840 uses ArduinoBLE library (not ESP32 BLE library)
- Hardware FPU on Cortex-M4F enables efficient DFT computation for spin rate
