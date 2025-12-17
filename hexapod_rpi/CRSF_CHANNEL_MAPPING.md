# RadioMaster Pocket CRSF Channel Mapping for Hexapod

## Overview
This document describes the channel mapping for the RadioMaster Pocket transmitter with ELRS receiver using CRSF protocol.

## Protocol Details
- **Protocol**: CRSF (Crossfire)
- **Baud Rate**: 420000 (NOT 100000 like SBUS)
- **Serial Port**: `/dev/serial0` (Raspberry Pi UART)
- **Channel Range**: 172 to 1811 (11-bit CRSF values)
- **Center Value**: 992

## Channel Mapping

### Movement Controls

| Channel | Index | Control | Function | Range |
|---------|-------|---------|----------|-------|
| **Ch16** | 15 | Right Stick X (Roll) | **Strafe Left/Right** | -1.0 to 1.0 |
| **Ch15** | 14 | Right Stick Y (Pitch) | **Forward/Backward** | -1.0 to 1.0 |
| **Ch14** | 13 | Left Stick Y | **Speed Control** | 0.0 to 2.0 |
| **Ch13** | 12 | Left Stick X (Yaw) | **Rotation** | -1.0 to 1.0 |
| **Ch7** | 6 | Aux Switch/Slider | **Height Control** | -1.0 to 1.0 |

### Mode Controls

| Channel | Index | Control | Function | Values |
|---------|-------|---------|----------|--------|
| **Ch9** | 8 | Switch | **Calibration Mode** | ON/OFF |
| **Ch12** | 11 | Switch | **Sleep Mode** | ON/OFF |

### Gait Selection (3-Position Switches)

| Channel | Index | Control | Gaits | Position Values |
|---------|-------|---------|-------|-----------------|
| **Ch10** | 9 | 3-Pos Switch | Gaits 0-2 | 191 / 997 / 1792 |
| **Ch11** | 10 | 3-Pos Switch | Gaits 3-5 | 191 / 997 / 1792 |

**Gait Mapping:**
- **Channel 10**:
  - Position 1 (191): Gait 0 - TRI (Tripod)
  - Position 2 (997): Gait 1 - RIPPLE
  - Position 3 (1792): Gait 2 - WAVE
  
- **Channel 11**:
  - Position 1 (191): Gait 3 - QUAD (Quadruped)
  - Position 2 (997): Gait 4 - BI (Bipod)
  - Position 3 (1792): Gait 5 - HOP

## Control Scheme

```
┌─────────────────────────────────────────────────────────────┐
│              RadioMaster Pocket Controller                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LEFT STICK (Ch13/14)          RIGHT STICK (Ch15/16)       │
│  ┌─────────────┐                ┌─────────────┐           │
│  │      ↑      │                │      ↑      │           │
│  │   SPEED+    │                │   FORWARD   │           │
│  │  (Ch14)     │                │   (Ch15)    │           │
│  │             │                │             │           │
│  │ ←  [·]  → │                │ ←  [·]  → │           │
│  │  ROTATE     │                │   STRAFE    │           │
│  │  (Ch13)     │                │   (Ch16)    │           │
│  │             │                │             │           │
│  │      ↓      │                │      ↓      │           │
│  │   SPEED-    │                │  BACKWARD   │           │
│  └─────────────┘                └─────────────┘           │
│                                                             │
│  Ch7:  Height Control (Slider/Switch)                      │
│  Ch9:  Calibration Mode (Switch)                           │
│  Ch10: Gait Selector 1 - TRI/RIPPLE/WAVE (3-pos)          │
│  Ch11: Gait Selector 2 - QUAD/BI/HOP (3-pos)              │
│  Ch12: Sleep Mode (Switch)                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Movement Examples

### Basic Walking
1. **Forward**: Right stick UP (Ch15)
2. **Backward**: Right stick DOWN (Ch15)
3. **Strafe Left**: Right stick LEFT (Ch16)
4. **Strafe Right**: Right stick RIGHT (Ch16)
5. **Rotate Left**: Left stick LEFT (Ch13)
6. **Rotate Right**: Left stick RIGHT (Ch13)

### Speed Control
- **Slow Motion**: Left stick DOWN (Ch14) → Speed multiplier < 1.0
- **Normal Speed**: Left stick CENTER (Ch14) → Speed multiplier = 1.0
- **Fast Motion**: Left stick UP (Ch14) → Speed multiplier > 1.0
- **Range**: 0.0 (stopped) to 2.0 (double speed)

### Height Adjustment
- **Lower Body**: Ch7 down → Height control = -1.0
- **Raise Body**: Ch7 up → Height control = +1.0

### Modes
- **Calibration Mode**: Ch9 HIGH → Enter calibration for servo alignment
- **Sleep Mode**: Ch12 HIGH → Power-saving sleep mode

## Value Ranges

### CRSF Protocol
```
Channel Value Range: 172 to 1811 (11-bit)
Center: 992
```

### Normalized Values (after processing)
```
Joystick inputs: -1.0 to +1.0
Speed multiplier: 0.0 to 2.0
Height control: -1.0 to +1.0
Gait index: 0 to 5 (integer)
Mode switches: True/False
```

## Gait Threshold Detection

The receiver uses the following logic to detect gait switch positions:

```python
if channel_value < 400:
    position = 1  # Low position (value ~191)
elif channel_value < 1400:
    position = 2  # Middle position (value ~997)
else:
    position = 3  # High position (value ~1792)
```

## Testing

### 1. Test CRSF Receiver Connection
```bash
cd /home/ali/Documents/Aecerts_Hexapod_V1/hexapod_rpi/receiver
python3 crsf_receiver.py
```

This will display:
- All 16 channel values in real-time
- Processed control values (joysticks, speed, height)
- Current gait selection
- Mode switches (calibration, sleep)
- Connection statistics

### 2. Test with Servo Control
```bash
cd /home/ali/Documents/Aecerts_Hexapod_V1/hexapod_rpi
python3 test_crsf_servo_control.py
```

This demonstrates servo control using CRSF channel 16 (roll/strafe).

## Troubleshooting

### No Signal Received
1. Verify UART is enabled:
   ```bash
   sudo raspi-config → Interface Options → Serial Port
   # Enable hardware, disable console
   ```

2. Check `/boot/config.txt`:
   ```
   enable_uart=1
   ```

3. Verify receiver is powered and bound to transmitter

4. Check baud rate is 420000 (CRSF), not 100000 (SBUS)

### Incorrect Channel Values
1. Verify channel mapping on your transmitter
2. Check channel order in receiver output
3. Confirm 3-position switches output 191/997/1792 values

### CRC Errors
- Signal interference - check wiring
- Loose connections - secure TX/RX pins
- Power issues - ensure stable 5V supply

## Library Used

**crsf_parser**: Python library for parsing CRSF protocol frames
- Location: `/home/ali/Documents/Aecerts_Hexapod_V1/hexapod_rpi/crsf_parser/`
- Handles frame synchronization, CRC validation, channel extraction
- Provides callback interface for frame processing

## Summary

This mapping provides intuitive control:
- **Right stick**: Direct movement (forward/back, strafe)
- **Left stick X**: Rotation
- **Left stick Y**: Speed control
- **Ch7**: Height adjustment
- **Ch10/11**: Gait selection (6 gaits total)
- **Ch9**: Calibration mode
- **Ch12**: Sleep mode

The CRSF receiver (`crsf_receiver.py`) abstracts all protocol details and provides simple methods like `get_joystick1()`, `get_joystick2()`, `get_gait()`, etc.
