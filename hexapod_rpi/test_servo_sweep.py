#!/usr/bin/env python3
"""
Simple servo sweep test for PCA9685 on Raspberry Pi
Sweeps a single servo through its full range of motion
"""

import time
from adafruit_servokit import ServoKit

# Initialize PCA9685 with 16 channels
kit = ServoKit(channels=16)

# Configuration
SERVO_CHANNEL = 0  # Change this to test different servo channels (0-15)
MIN_ANGLE = 0      # Minimum servo angle
MAX_ANGLE = 180    # Maximum servo angle
STEP = 5           # Degrees to move per step
DELAY = 0.05       # Delay between steps (seconds)

print(f"Starting servo sweep test on channel {SERVO_CHANNEL}")
print(f"Sweeping from {MIN_ANGLE}° to {MAX_ANGLE}° and back")
print("Press Ctrl+C to stop")

try:
    while True:
        # Sweep forward (0 to 180 degrees)
        print(f"Sweeping forward: {MIN_ANGLE}° -> {MAX_ANGLE}°")
        for angle in range(MIN_ANGLE, MAX_ANGLE + 1, STEP):
            kit.servo[SERVO_CHANNEL].angle = angle
            print(f"  Angle: {angle}°", end='\r')
            time.sleep(DELAY)
        
        print()  # New line after sweep
        time.sleep(0.5)  # Pause at max position
        
        # Sweep backward (180 to 0 degrees)
        print(f"Sweeping backward: {MAX_ANGLE}° -> {MIN_ANGLE}°")
        for angle in range(MAX_ANGLE, MIN_ANGLE - 1, -STEP):
            kit.servo[SERVO_CHANNEL].angle = angle
            print(f"  Angle: {angle}°", end='\r')
            time.sleep(DELAY)
        
        print()  # New line after sweep
        time.sleep(0.5)  # Pause at min position

except KeyboardInterrupt:
    print("\n\nStopping servo sweep test")
    # Center the servo before exiting
    kit.servo[SERVO_CHANNEL].angle = 90
    print(f"Servo centered at 90°")

except Exception as e:
    print(f"\nError: {e}")
    print("Make sure:")
    print("  1. PCA9685 is properly connected to I2C (SDA/SCL)")
    print("  2. Servo is connected to the correct channel")
    print("  3. External power supply is connected to PCA9685")
    print("  4. I2C is enabled on Raspberry Pi (sudo raspi-config)")
