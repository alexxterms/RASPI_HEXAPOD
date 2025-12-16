# Servo Not Moving - Troubleshooting Guide

## Problem: calibrate_servos.py doesn't move servos, but test_servo_sweep.py works

---

## 🔍 Root Cause Analysis

Your `test_servo_sweep.py` works because it uses **ServoKit** which auto-detects one PCA9685 board.

The hexapod code expects **TWO** PCA9685 boards at addresses 0x40 and 0x41.

---

## ✅ Quick Fixes (Choose One)

### Option 1: If you have ONLY ONE PCA9685 board

Modify `config.py` to use only one board for all 18 servos:

**Problem**: ServoKit/PCA9685 only supports 16 channels per board, you have 18 servos!

**Solutions**:
1. Use 2 PCA9685 boards (recommended)
2. Use only 15 servos (5 legs) temporarily for testing
3. Chain two boards on same I2C bus

---

### Option 2: If you have TWO PCA9685 boards

#### Step 1: Verify I2C Addresses

Run this command to see what I2C devices are detected:
```bash
sudo i2cdetect -y 1
```

You should see:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: 40 41 -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- 70 -- -- -- 
70: 70 -- -- -- -- -- -- --
```

Look for **40** and **41** (hexadecimal). If you see both, boards are detected!

#### Step 2: Check Board Addressing

Each PCA9685 has solder jumpers (A0-A5) to set the I2C address:
- **Board 1**: All jumpers open → Address 0x40 (default)
- **Board 2**: Close A0 jumper → Address 0x41

#### Step 3: Check Power

PCA9685 boards need:
- **V+**: 5-6V for servos (external power supply)
- **VCC**: 3.3V or 5V from Pi (logic power)
- **GND**: Common ground with Pi

**Critical**: Servo power (V+) MUST be connected! The boards won't drive servos without it.

---

## 🧪 Testing Steps

### Test 1: Check if PCA9685 boards are detected
```bash
sudo i2cdetect -y 1
```

Expected: See `40` and `41`

If missing:
- Check I2C wiring (SDA → GPIO2, SCL → GPIO3)
- Check solder jumpers for address 0x41
- Enable I2C: `sudo raspi-config` → Interface Options → I2C → Enable

---

### Test 2: Run debug script
```bash
cd /path/to/hexapod_rpi
python3 debug_servo_controller.py
```

This will:
1. Initialize both PCA9685 boards
2. Try to move servo 0 through different positions
3. Show detailed error messages

Watch for:
- ✓ "PCA9685 boards initialized successfully"
- ✓ "Servos attached successfully"
- ❌ Any error messages about board addresses

---

### Test 3: Compare with working test
```bash
# Your working test (uses ServoKit)
python3 test_servo_sweep.py

# vs. our debug test (uses PCA9685)
python3 debug_servo_controller.py
```

If debug test fails but sweep test works → board addressing issue

---

## 🔧 Common Issues & Fixes

### Issue 1: Only Board 1 (0x40) detected

**Cause**: Second board not addressed correctly or not connected

**Fix**:
1. Check A0 solder jumper on second board (should be closed)
2. Check I2C wiring to second board
3. Check power to second board
4. Run `sudo i2cdetect -y 1` to verify

---

### Issue 2: Both boards detected but servos don't move

**Cause**: Servo power (V+) not connected

**Fix**:
1. Check external 5-6V power supply is connected to V+ terminals
2. Check power supply is ON and has sufficient current (18 servos × 1A each!)
3. Check GND is common between Pi and servo power supply
4. Use multimeter to verify V+ has voltage

---

### Issue 3: Some servos move, others don't

**Cause**: Wrong channel mapping

**Fix**:
Check `config.py` servo channel mappings:
```python
SERVO_CHANNELS = {
    # Leg 0 (Board 1, Channels 0-2)
    'coxa1': (0x40, 0),
    'femur1': (0x40, 1),
    'tibia1': (0x40, 2),
    
    # Leg 5 (Board 2, Channels 0-2)
    'coxa6': (0x41, 0),
    'femur6': (0x41, 1),
    'tibia6': (0x41, 2),
}
```

Verify servos are physically connected to these channels!

---

### Issue 4: Servos jitter or move erratically

**Cause**: Insufficient power supply

**Fix**:
1. Use 5-6V power supply rated for at least 10A (18 servos)
2. Check power supply voltage under load
3. Add bulk capacitors (1000μF) near PCA9685 boards

---

## 📋 Hardware Checklist

Before running calibration:

**I2C Connection:**
- [ ] SDA connected (GPIO2 on Pi → SDA on both PCA9685)
- [ ] SCL connected (GPIO3 on Pi → SCL on both PCA9685)
- [ ] GND connected (Pi → Both PCA9685)

**Power:**
- [ ] VCC connected (3.3V or 5V from Pi → VCC on both boards)
- [ ] V+ connected (5-6V external → V+ on both boards)
- [ ] GND common (Pi GND = Servo PSU GND)
- [ ] Power supply rated for 10A+ @ 5-6V

**Addressing:**
- [ ] Board 1: All jumpers open (Address 0x40)
- [ ] Board 2: A0 closed (Address 0x41)
- [ ] `sudo i2cdetect -y 1` shows both 40 and 41

**Servos:**
- [ ] 18 servos connected to correct channels
- [ ] Servo signal pins match channel numbers
- [ ] Servos are appropriate voltage (4.8-6V)

---

## 🎯 Quick Diagnostic Commands

```bash
# Check I2C devices
sudo i2cdetect -y 1

# Check I2C enabled
ls /dev/i2c-*

# Enable I2C if needed
sudo raspi-config
# → Interface Options → I2C → Enable

# Test working servo code
python3 test_servo_sweep.py

# Test hexapod servo controller
python3 debug_servo_controller.py

# Test calibration
python3 calibrate_servos.py
```

---

## 🚨 Most Likely Issues

Based on your symptoms (test works, calibration doesn't):

1. **Most Likely**: Second PCA9685 not detected
   - Run `sudo i2cdetect -y 1`
   - Check address jumpers

2. **Second Most Likely**: Servo power not connected
   - Check V+ terminals have 5-6V
   - Check power supply current capacity

3. **Third**: Wrong board in test vs calibration
   - test_servo_sweep.py might be on board 1 (0x40)
   - calibration might be trying board 2 (0x41)
   - Try changing SERVO_CHANNEL in test to different values

---

## ✅ Next Steps

1. Run `sudo i2cdetect -y 1` and report what you see
2. Run `python3 debug_servo_controller.py` and share output
3. Check which PCA9685 board your test servo is connected to
4. Verify servo power supply voltage and current

Let me know what you find!
