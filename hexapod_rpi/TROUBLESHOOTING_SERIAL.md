# 🔧 Troubleshooting Guide - Serial Port Issues

## Common Error: "Invalid argument" (errno 22)

This error occurs when the serial port is locked or misconfigured.

---

## 🚨 Quick Fixes

### 1. **Kill Stuck Python Processes**
```bash
# Kill all Python processes
killall python3
killall python

# Or force kill
killall -9 python3
```

### 2. **Use the Fix Script**
```bash
cd hexapod_rpi
./fix_serial.sh
```

### 3. **Check What's Using the Serial Port**
```bash
# Install lsof if needed
sudo apt install lsof

# Check what's using the port
sudo lsof /dev/serial0
sudo lsof /dev/ttyAMA0

# Kill specific process by PID
kill <PID>
```

---

## 🔍 Root Causes & Solutions

### Issue 1: Serial Port Already Open

**Symptom**: `OSError: [Errno 22] Invalid argument`

**Cause**: Previous Python script didn't close the serial port properly

**Solution**:
```bash
# Quick fix
killall python3

# Or reboot
sudo reboot
```

**Prevention**: The code now has proper cleanup with try/finally blocks!

---

### Issue 2: UART Not Enabled

**Symptom**: `/dev/serial0` doesn't exist

**Solution**:
```bash
# Enable UART
sudo raspi-config

# Navigate to:
#   3. Interface Options
#   → I6. Serial Port
#   → "Would you like a login shell accessible over serial?" → No
#   → "Would you like the serial port hardware to be enabled?" → Yes
#   → Finish → Reboot

sudo reboot
```

**Verify**:
```bash
ls -l /dev/serial0
# Should show: lrwxrwxrwx ... /dev/serial0 -> ttyAMA0
```

---

### Issue 3: Permission Denied

**Symptom**: `Permission denied` when accessing serial port

**Solution**:
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# IMPORTANT: Logout and login again for changes to take effect
# Or reboot
sudo reboot
```

**Verify**:
```bash
groups
# Should include: dialout
```

---

### Issue 4: Wrong Serial Port

**Symptom**: Port exists but no data received

**Solution**: Try different serial ports in `config.py`:

```python
# Try these options:
ELRS_SBUS_SERIAL = '/dev/serial0'  # Default (symbolic link)
# Or
ELRS_SBUS_SERIAL = '/dev/ttyAMA0'  # Direct UART
# Or
ELRS_SBUS_SERIAL = '/dev/ttyS0'    # On some Pi models
```

**Check available ports**:
```bash
ls -l /dev/tty* | grep -E "AMA|USB|ACM"
```

---

### Issue 5: Bluetooth Interfering

On some Raspberry Pi models, Bluetooth uses the same UART.

**Solution**: Disable Bluetooth
```bash
# Edit config
sudo nano /boot/config.txt

# Add this line:
dtoverlay=disable-bt

# Save and reboot
sudo reboot
```

---

## 🧪 Testing Procedure

### Step 1: Basic Serial Port Test
```bash
# Check if port exists
ls -l /dev/serial0

# Expected output:
# lrwxrwxrwx 1 root root 7 Dec 17 10:00 /dev/serial0 -> ttyAMA0
```

### Step 2: Check Permissions
```bash
# Should show your user
groups | grep dialout

# Check port ownership
ls -l /dev/serial0
# Should be: crw-rw---- 1 root dialout ...
```

### Step 3: Test with Minicom (Optional)
```bash
# Install minicom
sudo apt install minicom

# Test serial port
minicom -b 100000 -D /dev/serial0

# Press Ctrl+A then X to exit
```

### Step 4: Run Receiver Test
```bash
cd hexapod_rpi

# Run test
python3 -m receiver.elrs_receiver

# Should see:
# ✓ Receiver initialized successfully!
# (If ELRS receiver is connected and powered)
```

---

## 🛠️ Complete Raspberry Pi Setup

If you're setting up from scratch:

```bash
# 1. Update system
sudo apt update
sudo apt upgrade

# 2. Enable UART
sudo raspi-config
# Interface Options → Serial Port
# Disable login shell, Enable hardware

# 3. Add user to dialout group
sudo usermod -a -G dialout $USER

# 4. Install dependencies
cd hexapod_rpi
sudo ./setup.sh

# 5. Reboot
sudo reboot

# 6. Test
cd hexapod_rpi
python3 -m receiver.elrs_receiver
```

---

## 🔌 Hardware Connection

Verify ELRS receiver wiring:

```
ELRS Receiver          Raspberry Pi
═══════════════        ══════════════
    GND        ───→    Pin 6  (GND)
    5V         ───→    Pin 2  (5V)
    SBUS       ───→    Pin 8  (GPIO 14 / UART TX)
```

**Note**: SBUS signal is **inverted** - the Pi's UART expects this.

---

## 📊 Error Code Reference

| Error | Code | Meaning | Fix |
|-------|------|---------|-----|
| Invalid argument | 22 | Port locked/busy | Kill Python processes |
| Permission denied | 13 | No permission | Add to dialout group |
| No such file | 2 | UART disabled | Enable in raspi-config |
| Device busy | 16 | Port already open | Reboot or kill process |

---

## 🆘 Still Having Issues?

### Debug Checklist:
- [ ] UART enabled in raspi-config
- [ ] User in dialout group (run `groups`)
- [ ] Serial port exists (`ls -l /dev/serial0`)
- [ ] No Python processes running (`ps aux | grep python`)
- [ ] ELRS receiver powered on
- [ ] ELRS receiver bound to transmitter (LED solid/blinking)
- [ ] Correct wiring (SBUS → GPIO 14)

### Get System Info:
```bash
# Raspberry Pi model
cat /proc/cpuinfo | grep Model

# Kernel messages about UART
dmesg | grep -i uart

# Kernel messages about serial
dmesg | grep -i tty

# Check enabled overlays
vcgencmd get_config int | grep serial
```

---

## 💡 Testing Without Hardware

If you're developing on a PC (not Raspberry Pi), you can test individual state machines without the receiver:

```bash
# These have built-in mock tests:
python3 -m states.walking
python3 -m states.standing
python3 -m states.calibration
python3 -m states.sleep
python3 -m states.attacks
python3 servo_controller.py
python3 kinematics.py
```

---

## ✅ When Everything Works

You should see:
```
Testing ELRS Receiver...
Mode: SBUS
SBUS initialized on /dev/serial0
✓ Receiver initialized successfully!

Reading receiver data for 10 seconds...
Connected: True  | Joy1: (-0.05, +0.02) | Joy2: (+0.00, -0.01) | Gait: 0 | Btn: False,False
```

If you see this, your serial port is working correctly! 🎉
