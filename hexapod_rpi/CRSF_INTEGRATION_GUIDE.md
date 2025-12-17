# CRSF Receiver Integration Guide

## Quick Start

The new CRSF receiver (`receiver/crsf_receiver.py`) uses the same `crsf_parser` library that works in your `test_crsf_servo_control.py`.

## Testing the Receiver

### 1. Test Receiver Standalone
```bash
cd /home/ali/Documents/Aecerts_Hexapod_V1/hexapod_rpi
python3 test_crsf_receiver.py
```

**Expected Output:**
- All 16 channels displayed in real-time
- Processed values (joysticks, speed, height, gait, modes)
- Connection status and frame rate
- Statistics (valid frames, CRC errors, etc.)

**What to Check:**
1. Move **right stick UP/DOWN** → Ch15 should change (Forward/Back)
2. Move **right stick LEFT/RIGHT** → Ch16 should change (Strafe)
3. Move **left stick LEFT/RIGHT** → Ch13 should change (Rotation)
4. Move **left stick UP/DOWN** → Ch14 should change (Speed)
5. Toggle switches → Ch7, Ch9, Ch10, Ch11, Ch12 should change

## Integration with Main Code

### Replace Old Receiver

The old `receiver/elrs_receiver.py` used SBUS protocol (wrong for ELRS). Replace it with the new CRSF receiver:

```python
# OLD (doesn't work):
from receiver.elrs_receiver import ELRSReceiver
receiver = ELRSReceiver()

# NEW (working):
from receiver.crsf_receiver import CRSFReceiver
receiver = CRSFReceiver()
```

### Basic Usage Example

```python
from receiver.crsf_receiver import CRSFReceiver
import time

# Initialize
receiver = CRSFReceiver()
if not receiver.connect():
    print("Failed to connect")
    exit(1)

# Main loop
while True:
    # Update receiver (reads serial data and parses CRSF)
    receiver.update()
    
    if receiver.is_connected():
        # Get control values
        rotation, speed_mult = receiver.get_joystick1()
        strafe, forward = receiver.get_joystick2()
        height = receiver.get_height_control()
        gait = receiver.get_gait()
        
        # Check modes
        if receiver.is_calibration_mode():
            print("Calibration mode active")
        
        if receiver.is_sleep_mode():
            print("Sleep mode active")
        
        # Use values for movement
        print(f"Forward: {forward:+.2f}, Strafe: {strafe:+.2f}, Rotation: {rotation:+.2f}")
        print(f"Speed: {speed_mult:.2f}x, Gait: {gait}")
    else:
        print("No signal")
    
    time.sleep(0.02)  # 50Hz update rate

# Cleanup
receiver.disconnect()
```

## API Reference

### Connection Methods

```python
receiver.connect()           # Connect to ELRS receiver
                            # Returns: bool (True if successful)

receiver.disconnect()        # Disconnect from receiver

receiver.update()            # Read and parse CRSF data (call in main loop)
                            # Returns: bool (True if connected and receiving)

receiver.is_connected()      # Check connection status
                            # Returns: bool
```

### Control Value Methods

```python
receiver.get_joystick1()     # Get left stick values
                            # Returns: (rotation, speed_multiplier)
                            # rotation: -1.0 to 1.0 (left/right)
                            # speed_multiplier: 0.0 to 2.0

receiver.get_joystick2()     # Get right stick values
                            # Returns: (strafe, forward)
                            # strafe: -1.0 to 1.0 (left/right)
                            # forward: -1.0 to 1.0 (back/forward)

receiver.get_speed_multiplier() # Get speed control
                               # Returns: float (0.0 to 2.0)

receiver.get_height_control()   # Get height adjustment
                               # Returns: float (-1.0 to 1.0)

receiver.get_gait()            # Get current gait selection
                              # Returns: int (0-5)
                              # 0=TRI, 1=RIPPLE, 2=WAVE, 3=QUAD, 4=BI, 5=HOP

receiver.is_calibration_mode() # Check calibration mode
                              # Returns: bool

receiver.is_sleep_mode()       # Check sleep mode
                              # Returns: bool
```

### Statistics Methods

```python
receiver.get_stats()         # Get statistics
                            # Returns: dict with keys:
                            #   'connected': bool
                            #   'frames_received': int
                            #   'errors': int
                            #   'parser_valid': int
                            #   'parser_crc_errors': int
                            #   'parser_invalid': int

receiver.print_status()      # Print detailed status to console
```

### Direct Channel Access

```python
receiver.channels[index]     # Access raw channel values (0-15)
                            # Returns: int (172 to 1811)
                            # Example: receiver.channels[15] = Ch16 (Roll)
```

## Channel Index Reference

```python
# Control channels (use methods above instead of direct access)
CH_YAW = 12          # Ch13 - Left stick X → Rotation
CH_SPEED = 13        # Ch14 - Left stick Y → Speed
CH_PITCH = 14        # Ch15 - Right stick Y → Forward/Back
CH_ROLL = 15         # Ch16 - Right stick X → Strafe
CH_HEIGHT = 6        # Ch7 - Height control
CH_CALIBRATION = 8   # Ch9 - Calibration mode
CH_GAIT_1 = 9        # Ch10 - Gait 0-2
CH_GAIT_2 = 10       # Ch11 - Gait 3-5
CH_SLEEP = 11        # Ch12 - Sleep mode
```

## Value Ranges

### Raw CRSF Values
```python
CRSF_MIN = 172      # Minimum channel value
CRSF_MID = 992      # Center/neutral position
CRSF_MAX = 1811     # Maximum channel value
```

### Processed Values
```python
# Joystick axes (normalized)
joystick_x: -1.0 (left)  to +1.0 (right)
joystick_y: -1.0 (down)  to +1.0 (up)

# Speed multiplier
speed: 0.0 (stopped) to 2.0 (double speed)
       1.0 = normal speed (stick centered)

# Height control
height: -1.0 (lower) to +1.0 (raise)

# Gait index
gait: 0 to 5 (integer)
      0=TRI, 1=RIPPLE, 2=WAVE, 3=QUAD, 4=BI, 5=HOP

# Mode switches
calibration_mode: True/False
sleep_mode: True/False
```

## Gait Selection Logic

The receiver automatically handles gait selection from two 3-position switches:

```python
# Channel 10 (3-position switch)
Position 1 (value ~191):  Gait 0 (TRI)
Position 2 (value ~997):  Gait 1 (RIPPLE)
Position 3 (value ~1792): Gait 2 (WAVE)

# Channel 11 (3-position switch)
Position 1 (value ~191):  Gait 3 (QUAD)
Position 2 (value ~997):  Gait 4 (BI)
Position 3 (value ~1792): Gait 5 (HOP)

# The receiver uses whichever switch is moved furthest from center
gait = receiver.get_gait()  # Returns 0-5
```

## Error Handling

### Connection Errors
```python
if not receiver.connect():
    # Handle connection failure
    print("Check:")
    print("- UART enabled in raspi-config")
    print("- Baud rate is 420000 (CRSF)")
    print("- Receiver is powered and bound")
    print("- TX pin connected to GPIO15")
```

### Signal Loss
```python
if not receiver.is_connected():
    # Signal lost - handle gracefully
    # Stop movement, enter safe mode, etc.
    print("Signal lost - stopping movement")
```

### CRC Errors
```python
stats = receiver.get_stats()
if stats['parser_crc_errors'] > 100:
    # High error rate - check wiring/interference
    print("High CRC error rate - check connections")
```

## Troubleshooting

### No Signal Received

1. **Check UART Configuration**
   ```bash
   sudo raspi-config
   # Interface Options → Serial Port
   # Enable hardware, disable console
   ```

2. **Verify /boot/config.txt**
   ```bash
   grep enable_uart /boot/config.txt
   # Should show: enable_uart=1
   ```

3. **Check /boot/cmdline.txt**
   ```bash
   cat /boot/cmdline.txt
   # Should NOT contain: console=serial0
   ```

4. **Verify Wiring**
   - Receiver TX → Raspberry Pi GPIO15 (Pin 10)
   - Receiver GND → Raspberry Pi GND
   - Receiver powered (5V)

5. **Check Receiver Binding**
   - Transmitter powered on
   - Receiver bound to transmitter
   - Green LED on receiver should be solid (not blinking)

6. **Verify Baud Rate**
   - CRSF uses 420000 baud (NOT 100000!)
   - Check `CRSFReceiver.BAUD_RATE` is 420000

### Wrong Channel Values

1. **Verify Channel Order**
   ```python
   # Run test and move sticks one at a time
   python3 test_crsf_receiver.py
   ```

2. **Check Transmitter Settings**
   - Verify channel order in transmitter
   - Check for channel mixing/reversing

3. **Test 3-Position Switches**
   - Should output: 191, 997, 1792
   - Adjust `GAIT_THRESHOLD_LOW/MID` if needed

### High CRC Errors

1. **Check Wiring Quality**
   - Secure connections
   - Short wires (< 30cm)
   - Twisted pair if long

2. **Power Supply**
   - Clean 5V supply
   - Avoid power from noisy sources

3. **Interference**
   - Keep away from WiFi/servos
   - Add ferrite bead if needed

## Performance Tips

### Update Rate
```python
# Call update() at 50-100 Hz for smooth control
while True:
    receiver.update()
    time.sleep(0.01)  # 100Hz
```

### Minimize Latency
```python
# Process immediately after update
receiver.update()
if receiver.is_connected():
    # Process control values NOW
    forward, strafe, rotation = ...
```

### Dead Zone
```python
# Apply dead zone to joystick inputs if needed
def apply_deadzone(value, deadzone=0.1):
    if abs(value) < deadzone:
        return 0.0
    return value

rotation, speed = receiver.get_joystick1()
rotation = apply_deadzone(rotation, 0.05)
```

## Summary

The CRSF receiver provides:
- ✅ Correct CRSF protocol (420000 baud)
- ✅ All 16 channels accessible
- ✅ Normalized control values (-1.0 to 1.0)
- ✅ 6 gaits via 3-position switches
- ✅ Speed control (0.0 to 2.0x)
- ✅ Calibration and sleep modes
- ✅ Automatic connection management
- ✅ Error handling and statistics

Use `test_crsf_receiver.py` to verify everything works before integrating with main code!
