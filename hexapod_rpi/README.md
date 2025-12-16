# Hexapod Robot - Raspberry Pi Zero Port

This is a Python port of the Teensy-based hexapod robot controller, adapted for **Raspberry Pi Zero** with **dual PCA9685 servo controllers** and **ELRS receiver**.

## 🎯 Overview

This project converts the original Arduino/Teensy hexapod code to run on a Raspberry Pi Zero, replacing:
- **Arduino Servo library** → PCA9685 I2C servo controllers
- **EEPROM storage** → JSON file-based configuration
- **RF24 radio** → ELRS (ExpressLRS) receiver
- **Arduino .ino files** → Structured Python project

## 📁 Project Structure

```
hexapod_rpi/
├── main.py                 # Main control loop and state machine
├── config.py              # Hardware configuration and constants
├── servo_controller.py    # PCA9685 servo control interface
├── kinematics.py          # Inverse kinematics calculations
├── storage.py             # JSON-based configuration storage
├── receiver/
│   ├── __init__.py
│   └── elrs_receiver.py   # ELRS receiver interface (SBUS/PWM)
├── utils/
│   ├── __init__.py
│   ├── vectors.py         # Vector2/Vector3 classes
│   └── helpers.py         # Helper functions and Bezier curves
├── states/                # State machine modules (to be expanded)
│   └── __init__.py
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🔧 Hardware Requirements

### Required Components
1. **Raspberry Pi Zero W** (or Zero 2 W for better performance)
2. **2× PCA9685 16-Channel PWM Servo Driver Boards**
   - Addresses: 0x40 and 0x41
   - Connected via I2C
3. **18× Servo Motors** (3 per leg × 6 legs)
4. **ELRS Receiver**
   - SBUS output (recommended) or PWM outputs
5. **Power Supply**
   - 5-6V for servos (separate from Pi)
   - 5V for Raspberry Pi
6. **Voltage Regulator** (if needed for Pi)

### Wiring

#### I2C Connections (Both PCA9685 Boards)
```
Raspberry Pi          PCA9685 Board 1 (0x40)
GPIO 2 (SDA)    -->   SDA
GPIO 3 (SCL)    -->   SCL
5V              -->   VCC
GND             -->   GND

PCA9685 Board 2 (0x41)
Same as above, with address jumper set to 0x41
```

#### Servo Connections
```
PCA9685 Board 1 (0x40):
  Channels 0-2:   Leg 1 (Coxa, Femur, Tibia)
  Channels 3-5:   Leg 2 (Coxa, Femur, Tibia)
  Channels 6-8:   Leg 3 (Coxa, Femur, Tibia)
  Channels 9-11:  Leg 4 (Coxa, Femur, Tibia)
  Channels 12-14: Leg 5 (Coxa, Femur, Tibia)

PCA9685 Board 2 (0x41):
  Channels 0-2:   Leg 6 (Coxa, Femur, Tibia)
```

#### ELRS Receiver (SBUS Mode - Recommended)
```
ELRS Receiver         Raspberry Pi
SBUS Pin        -->   GPIO 14 (UART TXD / Serial RX)
GND             -->   GND
5V              -->   5V
```

## 📦 Installation

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python 3 and pip (if not already installed)
sudo apt install python3 python3-pip -y

# Install system dependencies
sudo apt install python3-dev python3-smbus i2c-tools git -y

# Enable I2C and Serial
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
# Navigate to: Interface Options → Serial → Disable login shell, Enable hardware
```

### 2. Clone/Copy Project Files

```bash
# Navigate to your home directory
cd ~

# Copy the hexapod_rpi folder to your Pi
# (Use scp, git clone, or USB transfer)

cd hexapod_rpi
```

### 3. Install Python Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt

# Or install system-wide (with sudo)
sudo pip3 install -r requirements.txt
```

### 4. Test I2C Connection

```bash
# Scan for I2C devices
sudo i2cdetect -y 1

# You should see devices at 0x40 and 0x41
```

### 5. Configure Settings

Edit `config.py` to match your hardware setup:

```python
# Adjust I2C addresses if different
PCA9685_ADDRESS_1 = 0x40
PCA9685_ADDRESS_2 = 0x41

# Configure ELRS mode (SBUS or PWM)
ELRS_MODE = 'SBUS'

# Adjust servo pulse width ranges if needed
SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500

# Set leg dimensions to match your hexapod
COXA_LENGTH = 46.0
FEMUR_LENGTH = 108.0
TIBIA_LENGTH = 200.0
```

## 🚀 Running the Code

### Basic Test (Servo Test)

```bash
# Test servo controller
python3 servo_controller.py

# This will move leg 0 servos through a test sequence
```

### Test Individual Components

```bash
# Test vector math
python3 utils/vectors.py

# Test helper functions
python3 utils/helpers.py

# Test kinematics (without hardware)
python3 kinematics.py

# Test storage
python3 storage.py

# Test ELRS receiver (requires hardware)
python3 receiver/elrs_receiver.py
```

### Run Main Program

```bash
# Run with normal priority
python3 main.py

# Or run with higher priority (recommended)
sudo nice -n -20 python3 main.py
```

### Run at Startup (Optional)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/hexapod.service
```

Add this content:

```ini
[Unit]
Description=Hexapod Robot Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/hexapod_rpi
ExecStart=/usr/bin/python3 /home/pi/hexapod_rpi/main.py
Restart=on-failure
Nice=-20

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable hexapod.service
sudo systemctl start hexapod.service
sudo systemctl status hexapod.service
```

## 🎮 ELRS Receiver Configuration

### SBUS Mode (Recommended)

1. Configure your ELRS receiver to output SBUS
2. Connect SBUS pin to GPIO 14 on Raspberry Pi
3. Ensure serial is enabled in `raspi-config`
4. Set `ELRS_MODE = 'SBUS'` in `config.py`

### PWM Mode (Alternative)

1. Connect individual channel outputs to GPIO pins
2. Configure pins in `config.py` under `ELRS_PWM_PINS`
3. Set `ELRS_MODE = 'PWM'` in `config.py`
4. Install `pigpio` for better PWM timing:
   ```bash
   sudo apt install pigpio python3-pigpio
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod
   ```

### Channel Mapping

Default channel assignments (adjust in `config.py`):
- **Channel 1** (Joy1 X): Yaw/Rotation
- **Channel 2** (Joy1 Y): Forward/Backward
- **Channel 3** (Joy2 X): Strafe Left/Right
- **Channel 4** (Joy2 Y): Height Up/Down
- **Channel 5** (Slider1): Speed Control
- **Channel 6** (Slider2): Gait Selection
- **Channel 7** (Button1): Mode Switch
- **Channel 8** (Button2): Special Function

## 🔍 Calibration

### Servo Offset Calibration

Servo offsets are stored in `/home/pi/hexapod_config.json`

To calibrate:
1. Enter calibration mode (implementation needed in full version)
2. Adjust individual servo offsets
3. Save to persistent storage

The system automatically loads offsets on startup.

## ⚙️ Configuration Files

### config.py
- Hardware pin mappings
- Servo channel assignments
- Hexapod dimensions
- Movement parameters
- Debug settings

### hexapod_config.json
- Servo calibration offsets
- Saved settings
- Calibration data

## 🐛 Troubleshooting

### I2C Issues
```bash
# Check I2C devices
sudo i2cdetect -y 1

# If devices not found:
# - Check wiring
# - Verify I2C is enabled
# - Check PCA9685 power
```

### Serial/SBUS Issues
```bash
# Check serial port
ls -l /dev/serial*

# Test serial communication
sudo cat /dev/serial0  # Should show data when receiver active

# If no data:
# - Check wiring
# - Verify serial enabled in raspi-config
# - Check ELRS receiver configuration
```

### Servo Issues
- Verify separate 5-6V power supply for servos
- Check PCA9685 power LED
- Ensure servo pulse width ranges match your servos
- Test individual servos with `servo_controller.py`

### Permission Issues
```bash
# Add user to GPIO and I2C groups
sudo usermod -a -G gpio,i2c pi

# Reboot for changes to take effect
sudo reboot
```

## 📝 Next Steps / TODO

This is a foundational port. To complete the full hexapod functionality, you need to:

1. **Implement Full State Machines**
   - Walking states (Car, Crab)
   - Gait patterns (Tripod, Ripple, Wave, etc.)
   - Attack animations
   - Sleep/wake sequences

2. **Add Bezier Curve Gait Control**
   - Port `Rotate_TriGait.ino`
   - Implement dynamic stride length
   - Add rotation support

3. **Implement Calibration Mode**
   - Interactive servo calibration
   - Save/load calibration data

4. **Add Advanced Features**
   - Body rotation (pitch, roll, yaw)
   - Terrain adaptation
   - Obstacle avoidance

5. **Performance Optimization**
   - Multi-threading for RC input
   - Optimize loop timing
   - Profile and optimize hotspots

## 🔄 Differences from Original Teensy Code

| Feature | Teensy | Raspberry Pi Zero |
|---------|--------|-------------------|
| Servo Control | Direct PWM pins | I2C PCA9685 |
| Storage | EEPROM | JSON file |
| Radio | RF24 (SPI) | ELRS SBUS/PWM |
| Language | C++ (.ino) | Python |
| Timing | Hardware timers | Software (time module) |
| Performance | ~600MHz, real-time | ~1GHz, OS overhead |

## 📚 Resources

- [PCA9685 Datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf)
- [Adafruit PCA9685 Guide](https://learn.adafruit.com/16-channel-pwm-servo-driver)
- [SBUS Protocol](https://github.com/bolderflight/sbus)
- [Raspberry Pi GPIO](https://www.raspberrypi.com/documentation/computers/os.html#gpio)

## 📄 License

Same as original project.

## 🤝 Contributing

Contributions welcome! Please test thoroughly on hardware before submitting PRs.

---

**Note**: This is a conversion/port of the original Teensy code. Some features may need additional implementation or optimization for Raspberry Pi.
