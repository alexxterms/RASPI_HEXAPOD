# Teensy to Raspberry Pi Zero Conversion Guide

## Overview

This document provides detailed information about converting your Teensy-based hexapod to Raspberry Pi Zero with PCA9685 servo controllers.

## Hardware Changes

### Microcontroller
**Before (Teensy):**
- Direct PWM control on pins 22-39
- Hardware timers for precise timing
- 600MHz ARM Cortex-M7
- Built-in EEPROM

**After (Raspberry Pi Zero):**
- I2C communication with PCA9685
- Software timing (less precise but adequate)
- 1GHz ARM11 (Zero W) or 4-core Cortex-A53 (Zero 2 W)
- No EEPROM (use file system)

### Servo Control
**Before:** 
```cpp
Servo coxa1;
coxa1.attach(22, 500, 2500);
coxa1.writeMicroseconds(1500);
```

**After:**
```python
controller = HexapodServoController()
controller.attach_servos()
controller.write_microseconds(0, 1500)  # Servo index 0 = coxa1
```

### Remote Control
**Before (RF24):**
```cpp
RF24 radio(49, 48); // CE, CSN
radio.begin();
radio.read(&data, sizeof(data));
```

**After (ELRS SBUS):**
```python
receiver = ELRSReceiver(mode='SBUS')
receiver.update()
data = receiver.get_control_data()
```

## Software Architecture Changes

### File Structure Conversion

| Arduino | Python | Notes |
|---------|--------|-------|
| `Hexapod_Code.ino` | `main.py` | Main loop and setup |
| `Initializations.h` | `config.py` | Constants and pin mappings |
| `Helpers.h` | `utils/helpers.py` | Utility functions |
| `vectors.h` | `utils/vectors.py` | Vector classes |
| `RC.h` | `receiver/elrs_receiver.py` | RC input handling |
| `Bezier.ino` | `utils/helpers.py` | Bezier curves |
| `Standing_State.ino` | `states/standing.py` | State logic |
| EEPROM calls | `storage.py` | Persistent storage |

### Key Code Conversions

#### 1. Timing

**Arduino:**
```cpp
unsigned long currentTime = millis();
delay(100);

#define every(interval) \
  static uint32_t __every__##interval = millis(); \
  if(millis() - __every__##interval >= interval && (__every__##interval = millis()))
```

**Python:**
```python
from utils.helpers import Timer, EveryTimer

Timer.init()
current_time = Timer.millis()
time.sleep(0.1)

timer = EveryTimer(interval_ms=100)
if timer.check():
    # Do something every 100ms
    pass
```

#### 2. Servo Control

**Arduino:**
```cpp
// moveToPos() function
coxa1.writeMicroseconds(coxaMicroseconds);
femur1.writeMicroseconds(femurMicroseconds);
tibia1.writeMicroseconds(tibiaMicroseconds);
```

**Python:**
```python
# In kinematics.py
self.servo_controller.write_leg_servos(
    leg=0,
    coxa_us=coxa_microseconds,
    femur_us=femur_microseconds,
    tibia_us=tibia_microseconds
)
```

#### 3. Vector Math

**Arduino:**
```cpp
Vector3 pos(100, 0, -50);
float distance = pos.distanceTo(Vector3(0, 0, 0));
Vector3 lerped = lerp(start, end, 0.5);
```

**Python:**
```python
from utils.vectors import Vector3
from utils.helpers import lerp

pos = Vector3(100, 0, -50)
distance = pos.distance_to(Vector3(0, 0, 0))
lerped = lerp(start, end, 0.5)
```

#### 4. Storage (EEPROM → JSON)

**Arduino:**
```cpp
void saveOffsets() {
    for (int i = 0; i < 18; i++) {
        EEPROM.put(i * sizeof(int8_t), rawOffsets[i]);
    }
}

void loadOffsets() {
    for (int i = 0; i < 18; i++) {
        EEPROM.get(i * sizeof(int8_t), rawOffsets[i]);
    }
}
```

**Python:**
```python
from storage import HexapodStorage

storage = HexapodStorage()

# Save
storage.save_offsets(raw_offsets)

# Load
raw_offsets = storage.load_offsets()
```

#### 5. State Machine

**Arduino:**
```cpp
enum State { Initialize, Stand, Car, Calibrate, Sleep };
State currentState = Initialize;

void loop() {
    switch(currentState) {
        case Stand:
            standingState();
            break;
        case Car:
            carState();
            break;
        // ...
    }
}
```

**Python:**
```python
from config import State

current_state = State.INITIALIZE

def loop():
    if current_state == State.STAND:
        state_stand()
    elif current_state == State.CAR:
        state_car()
    # ...
```

## Performance Considerations

### Timing Precision
- **Teensy**: Hardware timers, μs precision
- **Raspberry Pi**: Software timing, ~ms precision
- **Impact**: Slightly less precise servo control
- **Mitigation**: Use higher priority (`nice -n -20`)

### Loop Frequency
- **Teensy**: Can run at 1000+ Hz
- **Raspberry Pi**: Recommend 50-100 Hz
- **Impact**: Slower response time
- **Mitigation**: Optimize Python code, use compiled libraries

### I2C Communication
- **PCA9685 Update Rate**: ~50 Hz (adequate for servos)
- **I2C Speed**: Standard (100 kHz) or Fast (400 kHz)
- **Latency**: ~1-2ms per servo command
- **Impact**: Slight delay vs. direct PWM
- **Mitigation**: Use ServoKit for optimized control

## Advantages of Raspberry Pi

1. **More Processing Power**: Can run computer vision, AI, etc.
2. **Built-in WiFi**: Easy remote control, telemetry, OTA updates
3. **Linux OS**: More development tools, easier debugging
4. **Python**: Faster development, easier to maintain
5. **Expandability**: USB devices, camera, sensors

## Disadvantages vs. Teensy

1. **Less Real-time**: OS overhead affects timing precision
2. **More Complex**: OS management, dependencies
3. **Power Consumption**: Higher power draw
4. **Boot Time**: Slower startup
5. **I2C Overhead**: Additional latency vs. direct PWM

## Migration Checklist

- [ ] Wire PCA9685 boards and test with `i2cdetect`
- [ ] Connect ELRS receiver and verify SBUS data
- [ ] Configure servo channel mapping in `config.py`
- [ ] Test servo controller with simple movements
- [ ] Calibrate servo offsets and save to storage
- [ ] Test inverse kinematics with test positions
- [ ] Implement basic standing state
- [ ] Test RC input processing
- [ ] Implement walking gait
- [ ] Add remaining states (calibration, sleep, attacks)
- [ ] Performance testing and optimization
- [ ] Set up auto-start service
- [ ] Test fail-safes and emergency stop

## Tips for Success

1. **Start Simple**: Get servos moving before implementing complex gaits
2. **Test Incrementally**: Test each component separately before integration
3. **Use Debug Mode**: Enable detailed logging during development
4. **Monitor Performance**: Check loop timing and optimize if needed
5. **Power Management**: Ensure adequate power supply for all servos
6. **Backup Configs**: Save working configurations before making changes
7. **Use Version Control**: Git track your changes and configurations

## Common Issues and Solutions

### Servos Jittering
- **Cause**: Power supply insufficient or I2C communication issues
- **Solution**: Check power supply, add capacitors, reduce I2C speed

### Slow Response
- **Cause**: Loop running too slow or too much processing
- **Solution**: Profile code, optimize hotspots, reduce debug output

### RC Connection Lost
- **Cause**: SBUS wiring, serial configuration, receiver settings
- **Solution**: Check wiring, verify baud rate (100000), test with scope

### Servos Not Moving
- **Cause**: PCA9685 not initialized, wrong I2C address, no power
- **Solution**: Run `i2cdetect`, check addresses, verify servo power

### Config Not Saving
- **Cause**: File permissions, disk full, wrong path
- **Solution**: Check permissions, verify disk space, use absolute paths

## Advanced Optimizations

1. **Multi-threading**: Separate threads for RC input and servo control
2. **Compiled Extensions**: Use Cython for performance-critical code
3. **Direct Memory Access**: Use `/dev/mem` for lower-level GPIO control
4. **Real-time Kernel**: Install PREEMPT_RT patch for better timing
5. **Overclock**: Carefully overclock Pi Zero 2 for better performance

## References

- Original Teensy code: `../Hexapod_Code/`
- Python port: This directory
- Hardware docs: See README.md

---

Last updated: December 2025
