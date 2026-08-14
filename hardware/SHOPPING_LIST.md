# Component Shopping List
## Instrumented Baseball Project

---

## Already Purchased

### Phase 1 Components (ESP32 Prototype)

| Qty | Component | Source | Cost | Status |
|-----|-----------|--------|------|--------|
| 1 | DFRobot Beetle ESP32 | DFRobot | $12 | Phase 1 only (retired) |
| 1 | MPU-6050 breakout | Adafruit | $7 | Phase 1-2 dev IMU |
| 2 | FlexiForce A201 (25 lb) | DigiKey | $50 | Purchased |
| 1 | Breadboard + Wire Bundle | Adafruit | $6 | In use |
| 1 | Soldering Iron Kit | Amazon | $20 | Purchased |
| 1 | Resistor Kit (assorted) | Amazon | $9 | Purchased |

### Phase 2 Components (Sensor Array + IMUs)

| Qty | Component | Source | Cost | Status |
|-----|-----------|--------|------|--------|
| 2 | FlexiForce A201 (25 lb) — total now 4 | DigiKey | $50 | Purchased |
| 1 | ISM330DHCX breakout | Adafruit | $12 | Purchased (Phase 2 testing; NOT on final PCB — gyro saturates) |
| 1 | H3LIS331DL breakout | Adafruit | $10 | Purchased |
| 3 | Practice baseballs | Amazon | $15 | Purchased |

### Phase 3-4 Components (Power + Integration)

| Qty | Component | Source | Cost | Status |
|-----|-----------|--------|------|--------|
| 1 | MCP73831T LiPo charger | DigiKey | $2 | Purchased |
| 1 | 100mAh LiPo battery | Adafruit | $6 | Purchased |
| 1 | Qi receiver module (20mm) | Adafruit | $10 | Purchased |
| 2 | Regulation baseballs | Amazon | $15 | Purchased |
| 1 | 30 AWG wire (50ft) | Amazon | $10 | Purchased |
| 1 | 2-part epoxy | Hardware store | $10 | Purchased |
| 1 | Conformal coating spray | Amazon | $15 | Purchased |

### nRF52840 Migration Components

| Qty | Component | Source | Cost | Status |
|-----|-----------|--------|------|--------|
| 1 | Seeed XIAO nRF52840 | Seeed Studio | $10 | Purchased |
| 1 | LIS3MDL magnetometer breakout | Adafruit | $5 | Purchased |

**Total Spent: ~$274**

---

## Order Later — When PCB Design Is Ready

| Qty | Component | Why | Source | Link | Cost |
|-----|-----------|-----|--------|------|------|
| 5 | **Custom Rigid PCB** | ~30x25mm 2-layer rigid board (proven by McGinnis 2012) | JLCPCB | https://jlcpcb.com | $15-30 |

> **Note:** Rigid PCB, not flex. McGinnis (2012) proved a ~30x25mm rigid board fits inside a baseball. Rigid is cheaper and easier to solder.

**PCB Subtotal: $15-30**

---

## Final PCB Bill of Materials (on-board components)

| Component | Package | Qty | I2C Addr | Notes |
|-----------|---------|-----|----------|-------|
| nRF52840 | QFN-48 (7x7mm) | 1 | — | Bare chip MCU, BLE 5 |
| H3LIS331DL | LGA-16 (3x3mm) | 1 | 0x18 | ±400g accel — velocity + impact |
| LIS3MDL | LGA-12 (3x3mm) | 1 | 0x1C | Magnetometer — spin rate via DFT |
| MCP73831T | SOT-23-5 | 1 | — | LiPo charge controller |
| 10kΩ Resistor | 0603 | 4 | — | Voltage dividers for FSR sensors |
| 4.7kΩ Resistor | 0603 | 2 | — | I2C pull-ups (SDA/SCL) |
| 100nF Capacitor | 0603 | 4 | — | Decoupling (near each IC) |
| 10µF Capacitor | 0603 | 1 | — | Bulk decoupling |
| 32 MHz Crystal | 3.2x2.5mm | 1 | — | nRF52840 clock |
| Chip Antenna | SMD | 1 | — | BLE 5 antenna |

> **ISM330DHCX removed from final PCB.** Its gyroscope saturates at ±4000°/s (~666 RPM per axis), which is below every real pitch. Spin rate is measured via LIS3MDL magnetometer DFT instead. Velocity is estimated by integrating H3LIS331DL acceleration data. Release detection uses FlexiForce pressure dropout.

---

## Budget Summary

| Category | Cost | Status |
|----------|------|--------|
| Already spent | $274 | DONE |
| Custom PCB (JLCPCB) | $15-30 | Later |
| **Grand Total** | **$289-304** | |

---

## Decision Log

| Decision | Reasoning |
|----------|-----------|
| Switch from ESP32 to nRF52840 | 10x lower power, BLE 5, industry standard (PitchLogic, SmartBall), hardware FPU |
| Use Seeed XIAO as dev board | $10, 21x17mm, 6 analog pins, Arduino-compatible, USB-C |
| Drop ISM330DHCX from final PCB | Gyro saturates on every real pitch (±4000°/s < every pitch's spin rate). H3LIS331DL covers acceleration. LIS3MDL covers spin rate. FlexiForce covers release detection. |
| Add LIS3MDL magnetometer | DFT of mag signal measures spin rate at any RPM (Diamond Kinetics' patented approach) |
| Use H3LIS331DL for velocity | Integrate acceleration over throw duration (~0.5-1s). McGinnis showed 4-6% accuracy. |
| Rigid PCB instead of flex | McGinnis 2012 proved ~30x25mm rigid works; cheaper ($15-30 vs $50-80) |
| 4 sensors, not 6-8 | XIAO has 6 pins; 4 covers critical fingers; first study with thumb + ring data |
| FlexiForce over FSR | Calibrated, repeatable readings needed for research-grade data |
| Qi wireless charging | No exposed ports; ball can be fully sealed; charge through leather |
| Epoxy coating (not 3D frame) | Yeh et al. proved it survives 100 km/h impacts; simpler than 3D-printed frame |
