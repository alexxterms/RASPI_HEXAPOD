# Servo Controller API Fix

## Issue
When the servo controller was upgraded to use ServoKit, the API for `write_leg_servos()` changed but `kinematics.py` wasn't updated to match.

## Error
```
TypeError: HexapodServoController.write_leg_servos() takes 3 positional arguments but 5 were given
```

## Root Cause

### Old servo_controller.py API (with PCA9685):
```python
def write_leg_servos(self, leg, coxa_us, femur_us, tibia_us):
    # Expected 4 separate arguments in microseconds
```

### New servo_controller.py API (with ServoKit):
```python
def write_leg_servos(self, leg, angles):
    # Expects leg index and LIST of 3 angles in degrees
```

### Old kinematics.py call:
```python
# Called with 4 arguments (microseconds)
self.servo_controller.write_leg_servos(
    leg,
    coxa_microseconds,
    femur_microseconds,
    tibia_microseconds
)
```

## Solution

Updated `kinematics.py` to:
1. Convert microseconds to degrees using `microseconds_to_angle()`
2. Pass angles as a list instead of separate arguments

### New kinematics.py call:
```python
# Convert microseconds to degrees (500-2500μs maps to 0-180°)
coxa_angle = microseconds_to_angle(coxa_microseconds)
femur_angle = microseconds_to_angle(femur_microseconds)
tibia_angle = microseconds_to_angle(tibia_microseconds)

# Write to servos (new API expects list of angles)
self.servo_controller.write_leg_servos(leg, [coxa_angle, femur_angle, tibia_angle])
```

## Files Changed
- **kinematics.py**
  - Added import: `microseconds_to_angle`
  - Updated `move_to_pos()` to convert microseconds → angles
  - Changed API call to match new `write_leg_servos()` signature

## Testing
Now run:
```bash
python3 calibrate_servos.py
```

The servos should move to calibration position (89, 0, 293) without errors!
