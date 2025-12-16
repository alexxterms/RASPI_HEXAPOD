# Raspberry Pi UART Setup for ELRS SBUS

## ⚠️ Important: This Test Requires Actual Hardware

The ELRS receiver test (`receiver/elrs_receiver.py`) requires:
- A Raspberry Pi (not a development PC)
- UART serial port enabled
- ELRS receiver physically connected
- Receiver powered and bound to transmitter

---

## 🔧 Raspberry Pi UART Configuration

### Step 1: Enable UART Hardware

Run the configuration tool:
```bash
sudo raspi-config
```

Navigate to:
1. **Interface Options**
2. **Serial Port**
3. **Disable** "Would you like a login shell accessible over serial?"
4. **Enable** "Would you like the serial port hardware enabled?"
5. Select **Finish** and **reboot**

### Step 2: Verify UART is Enabled

After reboot, check that `/dev/serial0` exists:
```bash
ls -l /dev/serial0
```

You should see something like:
```
lrwxrwxrwx 1 root root 5 Dec 17 10:00 /dev/serial0 -> ttyS0
```

### Step 3: Add User to dialout Group

To access serial ports without sudo:
```bash
sudo usermod -a -G dialout $USER
```

**Important**: Logout and login again (or reboot) for this to take effect!

### Step 4: Verify Permissions

Check you're in the dialout group:
```bash
groups
```

You should see `dialout` in the list.

---

## 🔌 Hardware Connections

### ELRS Receiver Wiring

Connect your ELRS receiver to the Raspberry Pi:

```
ELRS Receiver          Raspberry Pi Zero
─────────────          ─────────────────
5V     ────────────>   Pin 2 or 4 (5V)
GND    ────────────>   Pin 6 or 9 (GND)
SBUS   ────────────>   Pin 8 (GPIO 14 / UART TX)
```

**Pin Layout (Raspberry Pi Zero):**
```
     3.3V [ 1] [ 2] 5V  ←── Power for receiver
      SDA [ 3] [ 4] 5V
      SCL [ 5] [ 6] GND ←── Ground for receiver
  GPIO  4 [ 7] [ 8] GPIO 14 (UART TX) ←── SBUS signal
      GND [ 9] [10] GPIO 15 (UART RX)
```

### Important Notes:

1. **SBUS is inverted** - The code handles this automatically
2. **Use GPIO 14**, not GPIO 15 (we're receiving data, not sending)
3. **5V power** - Most ELRS receivers need 5V (check your receiver specs)
4. **Binding** - Ensure receiver is bound to your RadioMaster Pocket first

---

## 🧪 Testing Procedure

### Test 1: Check Serial Port

Before running Python code, test the serial port exists:
```bash
ls -l /dev/serial0
cat /dev/serial0
```

If the receiver is working, you should see binary data (garbage characters). Press Ctrl+C to stop.

### Test 2: Run Receiver Test

From the hexapod_rpi directory:
```bash
cd /path/to/hexapod_rpi
python3 receiver/elrs_receiver.py
```

Or using module syntax:
```bash
cd /path/to/hexapod_rpi
python3 -m receiver.elrs_receiver
```

### Expected Output:

```
======================================================================
ELRS RECEIVER TEST
======================================================================
Mode: SBUS
Serial Port: /dev/serial0

⚠️  HARDWARE REQUIREMENTS:
  - Raspberry Pi with UART enabled
  - ELRS receiver connected to GPIO 14 (UART TX)
  - Receiver powered and bound to transmitter

Initializing receiver...
✓ Receiver initialized successfully!

Reading receiver data for 10 seconds...
(Move sticks on your RadioMaster Pocket)
(Press Ctrl+C to stop)

----------------------------------------------------------------------
Connected: True  | Joy1: (+0.00, +0.00) | Joy2: (+0.00, +0.00) | Gait: 0 | Btn: False,False
Connected: True  | Joy1: (+0.15, +0.80) | Joy2: (-0.20, +0.00) | Gait: 2 | Btn: False,False
Connected: True  | Joy1: (+0.00, +1.00) | Joy2: (+0.00, +0.00) | Gait: 0 | Btn: False,False
...
----------------------------------------------------------------------

✓ Test complete! Received 500 updates
```

### What to Look For:

✅ **Connected: True** - Receiver is receiving signal  
✅ **Joy values change** when you move sticks  
✅ **Gait changes** when you move Ch6 slider  
✅ **Buttons change** when you flip switches  

---

## ❌ Common Errors & Solutions

### Error: "No such file or directory: '/dev/serial0'"

**Problem**: UART not enabled

**Solution**:
```bash
sudo raspi-config
# Enable UART hardware (see Step 1 above)
sudo reboot
```

### Error: "Permission denied: '/dev/serial0'"

**Problem**: User not in dialout group

**Solution**:
```bash
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Error: "Invalid argument"

**Problem**: Serial port configuration issue

**Solution**:
1. Check UART is enabled: `ls -l /dev/serial0`
2. Check for conflicts: `sudo systemctl status serial-getty@ttyS0.service`
3. Disable serial console if active:
   ```bash
   sudo systemctl stop serial-getty@ttyS0.service
   sudo systemctl disable serial-getty@ttyS0.service
   ```

### Error: "Connected: False" (always)

**Problem**: No SBUS signal from receiver

**Solutions**:
1. **Check receiver power** - LED should be on
2. **Check binding** - Receiver must be bound to your transmitter
3. **Check wiring** - SBUS to GPIO 14 (Pin 8)
4. **Check receiver mode** - Must be in SBUS mode, not PWM
5. **Try different ELRS rate** - Some receivers need specific packet rates

### Error: "ModuleNotFoundError: No module named 'config'"

**Problem**: Running from wrong directory

**Solution**:
```bash
# Don't run from inside receiver/ directory
cd /path/to/hexapod_rpi
python3 receiver/elrs_receiver.py
```

---

## 🔍 Debugging SBUS Signal

### Check Raw SBUS Data

To see if ANY data is coming from the receiver:
```bash
# This will show binary data if SBUS is working
sudo cat /dev/serial0 | hexdump -C
```

Press Ctrl+C to stop. You should see:
- Constant stream of data (even with sticks centered)
- Frames starting with `0F` byte
- About 25 bytes per frame
- Updates at ~100Hz (10ms intervals)

If you see nothing, the problem is hardware/wiring.

### Check Receiver LED

Different ELRS receivers have different LED patterns:

| LED Pattern | Meaning |
|-------------|---------|
| Solid green | Connected to transmitter |
| Slow blink | Waiting for connection |
| Fast blink | Binding mode |
| Off | No power |

---

## 📊 SBUS Protocol Details

For reference (code handles this automatically):

- **Baud rate**: 100000
- **Format**: 8E2 (8 data bits, even parity, 2 stop bits)
- **Inverted**: SBUS signal is inverted (0V = high, 3.3V = low)
- **Frame**: 25 bytes total
  - Byte 0: 0x0F (start)
  - Bytes 1-22: Channel data (16 channels × 11 bits)
  - Byte 23: Flags
  - Byte 24: 0x00 (end)
- **Update rate**: ~100Hz (every 10ms)
- **Channel range**: 172-1811 (mapped to 1000-2000μs)

---

## ✅ Verification Checklist

Before testing:
- [ ] Raspberry Pi UART enabled (via raspi-config)
- [ ] User in dialout group
- [ ] ELRS receiver connected to GPIO 14
- [ ] Receiver powered (5V)
- [ ] Receiver bound to RadioMaster Pocket
- [ ] Transmitter powered on and in range
- [ ] `/dev/serial0` exists
- [ ] Can read from `/dev/serial0` without permission error

---

## 🚀 Next Steps After Successful Test

Once the receiver test works:

1. **Test main program**:
   ```bash
   python3 main.py
   ```

2. **Verify stick control**:
   - LEFT stick UP → hexapod walks forward
   - LEFT stick LEFT → hexapod rotates left
   - RIGHT stick RIGHT → hexapod strafes right

3. **Test state changes**:
   - Ch7 high → enters calibration mode
   - Ch8 high → enters sleep mode

4. **Test gait switching**:
   - Move Ch6 slider through positions
   - Verify gait changes (TRI→RIPPLE→WAVE→BI→QUAD→HOP)

---

## 📚 Additional Resources

- **ELRS Documentation**: https://www.expresslrs.org/
- **Raspberry Pi UART**: https://www.raspberrypi.com/documentation/computers/configuration.html#uart
- **SBUS Protocol**: Standard Futaba SBUS (widely documented online)

---

## 💡 Pro Tips

1. **Test on bench first** - Don't power servos until receiver works
2. **Check range** - Test receiver signal before assembling hexapod
3. **Set failsafe** - Configure failsafe in your transmitter (centered sticks)
4. **Monitor signal quality** - ELRS has built-in telemetry
5. **Update firmware** - Keep ELRS transmitter/receiver firmware updated

---

**Once you see "Connected: True" and joystick values changing, your ELRS setup is working perfectly!** 🎉
