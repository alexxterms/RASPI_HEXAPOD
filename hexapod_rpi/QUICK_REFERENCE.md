# Quick Reference Guide

## Project Files Overview

```
hexapod_rpi/
├── main.py              ⭐ Main entry point - run this!
├── config.py            🔧 Configuration - edit hardware settings here
├── servo_controller.py  🎛️  PCA9685 servo interface
├── kinematics.py        🦿 Inverse kinematics calculations
├── storage.py           💾 Configuration file storage
├── receiver/            📡 ELRS receiver interface
├── utils/               🛠️  Helper functions, vectors, math
├── states/              🔄 State machine modules
├── requirements.txt     📦 Python dependencies
├── setup.sh            🚀 Installation script
└── README.md           📖 Full documentation
```

## Quick Start (TL;DR)

```bash
# 1. On Raspberry Pi, run setup
chmod +x setup.sh
./setup.sh

# 2. Reboot
sudo reboot

# 3. Test I2C (should see 0x40, 0x41)
sudo i2cdetect -y 1

# 4. Edit config.py for your hardware

# 5. Test servos
python3 servo_controller.py

# 6. Run hexapod
python3 main.py
```

## Hardware Connections

### PCA9685 to Raspberry Pi
```
Pi Pin          PCA9685 (Both)
GPIO 2 (SDA) -> SDA
GPIO 3 (SCL) -> SCL
5V           -> VCC
GND          -> GND
```

### ELRS to Raspberry Pi (SBUS)
```
ELRS Pin        Pi Pin
SBUS        ->  GPIO 14 (TXD)
GND         ->  GND
5V          ->  5V
```

### Servo Channels
```
Board 1 (0x40):
0-2:   Leg 1 (Coxa, Femur, Tibia)
3-5:   Leg 2
6-8:   Leg 3
9-11:  Leg 4
12-14: Leg 5

Board 2 (0x41):
0-2:   Leg 6
```

## Common Commands

### Testing
```bash
# Test individual components
python3 servo_controller.py    # Servo test
python3 kinematics.py          # IK test
python3 receiver/elrs_receiver.py  # RC test
python3 storage.py             # Storage test

# Check I2C
sudo i2cdetect -y 1

# Check serial
sudo cat /dev/serial0
```

### Running
```bash
# Normal run
python3 main.py

# High priority (recommended)
sudo nice -n -20 python3 main.py

# As systemd service
sudo systemctl start hexapod
sudo systemctl status hexapod
sudo systemctl logs -f hexapod
```

### Debugging
```bash
# Enable debug mode in config.py
DEBUG_MODE = True
PRINT_SERVO_VALUES = True
PRINT_RC_VALUES = True

# View logs
tail -f /home/pi/hexapod.log

# Monitor system resources
htop
```

## Configuration Quick Edits

### Change Servo Ranges
```python
# In config.py
SERVO_MIN_PULSE = 500   # Minimum μs
SERVO_MAX_PULSE = 2500  # Maximum μs
```

### Change Hexapod Dimensions
```python
# In config.py
COXA_LENGTH = 46.0   # mm
FEMUR_LENGTH = 108.0 # mm
TIBIA_LENGTH = 200.0 # mm
```

### Change ELRS Mode
```python
# In config.py
ELRS_MODE = 'SBUS'  # or 'PWM'
```

### Change I2C Addresses
```python
# In config.py
PCA9685_ADDRESS_1 = 0x40
PCA9685_ADDRESS_2 = 0x41
```

## RC Channel Mapping

Default mapping (edit in `config.py`):
```python
RC_CHANNEL_JOY1_X = 0  # Yaw/rotation
RC_CHANNEL_JOY1_Y = 1  # Forward/back
RC_CHANNEL_JOY2_X = 2  # Strafe
RC_CHANNEL_JOY2_Y = 3  # Height
RC_CHANNEL_SLIDER1 = 4 # Speed
RC_CHANNEL_SLIDER2 = 5 # Gait select
RC_CHANNEL_BUTTON1 = 6 # Mode
RC_CHANNEL_BUTTON2 = 7 # Function
```

## Calibration

### Servo Offsets
Stored in `/home/pi/hexapod_config.json`

Format: 18 values (3 per leg)
```json
{
  "offsets": [
    coxa1, femur1, tibia1,  // Leg 0
    coxa2, femur2, tibia2,  // Leg 1
    // ... etc
  ]
}
```

### Reset Configuration
```python
from storage import HexapodStorage
storage = HexapodStorage()
storage.reset_to_defaults()
```

## Troubleshooting Quick Fixes

### No I2C Devices
```bash
# Enable I2C
sudo raspi-config
# Interface Options -> I2C -> Enable

# Check connections
sudo i2cdetect -y 1
```

### Servos Not Moving
1. Check servo power supply (separate from Pi)
2. Verify I2C connection: `sudo i2cdetect -y 1`
3. Test with: `python3 servo_controller.py`
4. Check PCA9685 power LED

### No SBUS Data
1. Check wiring (SBUS -> GPIO 14)
2. Enable serial: `sudo raspi-config` -> Interface -> Serial
3. Disable console: Select "No" for login shell
4. Enable hardware: Select "Yes" for serial port
5. Test: `sudo cat /dev/serial0`

### Python Import Errors
```bash
# Reinstall dependencies
pip3 install --upgrade -r requirements.txt

# Or system-wide
sudo pip3 install -r requirements.txt
```

### Permission Denied
```bash
# Add to groups
sudo usermod -a -G gpio,i2c $USER

# Reboot
sudo reboot
```

## Performance Tuning

### Increase Priority
```bash
# Run with higher priority
sudo nice -n -20 python3 main.py
```

### Adjust Loop Frequency
```python
# In config.py
MAIN_LOOP_FREQUENCY = 100  # Hz (50-200 recommended)
```

### Reduce Debug Output
```python
# In config.py
DEBUG_MODE = False
PRINT_SERVO_VALUES = False
PRINT_RC_VALUES = False
```

## File Locations

- **Config file**: `/home/pi/hexapod_config.json`
- **Log file**: `/home/pi/hexapod.log`
- **Service file**: `/etc/systemd/system/hexapod.service`
- **Project**: `~/hexapod_rpi/`

## Getting Help

1. Check `README.md` for full documentation
2. Check `CONVERSION_GUIDE.md` for Arduino → Python mappings
3. Review error messages carefully
4. Test components individually
5. Check wiring and power supply
6. Verify configuration in `config.py`

## Emergency Stop

If hexapod is misbehaving:
1. **Kill Python**: Press `Ctrl+C`
2. **Cut servo power**: Disconnect servo power supply
3. **Emergency shutdown**: `sudo shutdown now`

## Next Steps After Basic Setup

1. ✅ Get servos moving
2. ✅ Test RC input
3. ✅ Calibrate servo offsets
4. ⬜ Implement standing state fully
5. ⬜ Implement walking gaits
6. ⬜ Add advanced features
7. ⬜ Optimize performance
8. ⬜ Set up auto-start

---

**Remember**: Always have a way to quickly cut power to servos!
