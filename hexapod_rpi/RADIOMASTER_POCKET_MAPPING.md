# RadioMaster Pocket + ELRS Channel Mapping Guide

## Overview

Your RadioMaster Pocket transmitter outputs **SBUS protocol** through the ELRS receiver, which is correctly parsed by the code. This document explains the channel mapping.

---

## ✅ SBUS Protocol - CORRECT

**ELRS receivers in SBUS mode output standard SBUS frames:**
- 25 bytes per frame
- 16 channels × 11-bit resolution (0-2047)
- 100,000 baud, 8E2 (8 data bits, even parity, 2 stop bits)
- Inverted signal (handled by serial adapter)

**The code correctly parses SBUS frames** as per the standard protocol. ✅

---

## 🎮 RadioMaster Pocket Stick Layout

```
┌─────────────────────────────────────┐
│                                     │
│  RadioMaster Pocket                 │
│                                     │
│   RIGHT STICK        LEFT STICK     │
│   ┌─────────┐       ┌─────────┐    │
│   │    ↑    │       │    ↑    │    │
│   │ ←  +  → │       │ ←  +  → │    │
│   │    ↓    │       │    ↓    │    │
│   └─────────┘       └─────────┘    │
│   Ail  Ele          Thr  Rud       │
│   Ch1  Ch2          Ch3  Ch4       │
│                                     │
└─────────────────────────────────────┘
```

---

## 📊 Standard AETR Channel Order

| Channel | Name | Stick | Direction | RC Code Channel |
|---------|------|-------|-----------|-----------------|
| Ch 1 | Aileron (Roll) | Right X | Left/Right | 0 |
| Ch 2 | Elevator (Pitch) | Right Y | Up/Down | 1 |
| Ch 3 | Throttle | Left Y | Up/Down | 2 |
| Ch 4 | Rudder (Yaw) | Left X | Left/Right | 3 |
| Ch 5 | Aux 1 | Switch/Pot | - | 4 |
| Ch 6 | Aux 2 | Switch/Pot | - | 5 |
| Ch 7 | Aux 3 | Switch | - | 6 |
| Ch 8 | Aux 4 | Switch | - | 7 |

**Note:** Channel numbers in code are 0-indexed (0-7), but on your radio they're 1-indexed (1-8).

---

## 🦿 Hexapod Control Mapping

### Movement Controls

| Function | Stick | Channel | Code Variable | Description |
|----------|-------|---------|---------------|-------------|
| **Forward/Back** | Left Y | Ch 3 | `joy1_y` | Move forward/backward |
| **Rotation** | Left X | Ch 4 | `joy1_x` | Rotate in place (yaw) |
| **Strafe Left/Right** | Right X | Ch 1 | `joy2_x` | Move sideways |
| **Height Adjust** | Right Y | Ch 2 | `joy2_y` | Raise/lower body |

### Additional Controls

| Function | Input | Channel | Code Variable | Description |
|----------|-------|---------|---------------|-------------|
| **Speed** | Pot/Slider | Ch 5 | `slider1` | Movement speed |
| **Gait Select** | Pot/Slider | Ch 6 | `slider2` | Choose gait (0-5) |
| **Calibration** | Switch | Ch 7 | `button1` | Enter calibration mode |
| **Sleep** | Switch | Ch 8 | `button2` | Enter sleep mode |

---

## 🔧 Configuration in config.py

```python
# RadioMaster Pocket AETR mapping
RC_CHANNEL_JOY1_X = 3      # Left stick X (Ch4 Rudder/Yaw) - rotation
RC_CHANNEL_JOY1_Y = 2      # Left stick Y (Ch3 Throttle) - forward/back
RC_CHANNEL_JOY2_X = 0      # Right stick X (Ch1 Aileron/Roll) - strafe
RC_CHANNEL_JOY2_Y = 1      # Right stick Y (Ch2 Elevator/Pitch) - height
RC_CHANNEL_SLIDER1 = 4     # Ch5 - Speed control
RC_CHANNEL_SLIDER2 = 5     # Ch6 - Gait selector
RC_CHANNEL_BUTTON1 = 6     # Ch7 - Calibration mode
RC_CHANNEL_BUTTON2 = 7     # Ch8 - Sleep mode
```

---

## 🎯 Walking State Translation

In the walking state, `translation` is a Vector2:
- **translation.x** = Strafe (right stick X / Ch1)
- **translation.y** = Forward/back (left stick Y / Ch3)
- **rotation** = Yaw rotation (left stick X / Ch4)

This allows:
```python
# From main.py
translation = Vector2(self.joy2_current.x, self.joy1_current.y)  # strafe, forward
rotation = self.joy1_current.x  # rotation
```

---

## 🎮 How to Use

### Walking
1. **Left stick UP/DOWN** = Move forward/backward
2. **Left stick LEFT/RIGHT** = Rotate in place
3. **Right stick LEFT/RIGHT** = Strafe sideways
4. **Right stick UP/DOWN** = Adjust body height

### Gait Selection
- Adjust Ch6 slider/pot to select gait:
  - Position 0 = TRI (tripod) - fast, stable
  - Position 1 = WAVE - slow, maximum stability
  - Position 2 = RIPPLE - medium speed
  - Position 3 = BI (bipod) - very fast
  - Position 4 = QUAD - medium, 4-leg
  - Position 5 = HOP - synchronized

### Mode Switches
- **Ch7 switch HIGH** = Enter calibration mode
- **Ch8 switch HIGH** = Enter sleep mode

---

## 🔍 Verification

### Test SBUS Reception

Run the receiver test:
```bash
python3 receiver/elrs_receiver.py
```

You should see:
```
SBUS initialized on /dev/serial0
Reading receiver data for 10 seconds...
Connected: True, Joy1: (0.52, -0.31), Gait: 2
```

### Check Channel Values

Enable debug mode in config.py:
```python
DEBUG_MODE = True
PRINT_RC_VALUES = True
```

Run main program:
```bash
python3 main.py
```

You'll see:
```
RC: J1(0.00,0.50) J2(-0.30,0.00) S1:0.50 Gait:2 Btn:False,False
```

This shows:
- J1 = Left stick (rotation X, forward/back Y)
- J2 = Right stick (strafe X, height Y)
- S1 = Speed slider
- Gait = Current gait (0-5)
- Btn = Calibration, Sleep buttons

---

## 🛠️ Troubleshooting

### No SBUS Signal
1. Check ELRS receiver is in SBUS mode (not PWM)
2. Verify GPIO 14 (UART TX) connection
3. Check serial port: `ls /dev/serial*`
4. Enable UART: `sudo raspi-config` → Interface Options → Serial

### Wrong Channel Mapping
1. Check your radio's channel order (AETR vs TAER)
2. Verify in OpenTX/EdgeTX: Mixer screen shows channel assignments
3. Adjust config.py channel numbers if needed

### Inverted Controls
If a stick direction is backwards:
1. Check radio mixer settings
2. Or invert in code by negating values

### Deadzone Issues
Adjust in config.py:
```python
RC_DEADZONE = 50  # Increase if sticks drift, decrease if not responsive
```

---

## 📝 Summary

✅ **SBUS protocol parsing is correct** - Standard 25-byte frames  
✅ **Channel mapping is correct** - Matches RadioMaster Pocket AETR  
✅ **Stick assignment is correct** - Left=movement/rotation, Right=strafe/height  
✅ **Ready to use** - Just wire up and test!

### Final Stick Assignments

**LEFT STICK (Primary Movement):**
- UP/DOWN = Walk forward/backward
- LEFT/RIGHT = Rotate in place

**RIGHT STICK (Secondary Movement):**  
- LEFT/RIGHT = Strafe sideways
- UP/DOWN = Adjust body height

**SWITCHES:**
- Ch5 = Speed
- Ch6 = Gait selection
- Ch7 = Calibration mode
- Ch8 = Sleep mode

**This matches intuitive FPV-style control!** 🎮
