#!/usr/bin/env python3
"""
Debug test for servo_controller.py
Tests if the HexapodServoController can actually move servos
"""

import sys
import time
from servo_controller import HexapodServoController
import config

print("=" * 70)
print("SERVO CONTROLLER DEBUG TEST")
print("=" * 70)

try:
    # Initialize controller
    print("\n1. Initializing servo controller...")
    controller = HexapodServoController()
    print("   ✓ Controller initialized")
    
    # Attach servos
    print("\n2. Attaching servos...")
    controller.attach_servos()
    print("   ✓ Servos attached")
    
    # Test writing to first servo (coxa1)
    print("\n3. Testing servo movement...")
    print("   Testing servo 'coxa1' (index 0)")
    
    # Move to different positions
    positions = [1000, 1500, 2000, 1500]  # microseconds
    angles = [0, 90, 180, 90]  # degrees
    
    print("\n   Using microseconds control:")
    for i, us in enumerate(positions):
        print(f"   → Writing {us}μs...", end='')
        controller.write_microseconds(0, us)
        time.sleep(1)
        print(" done")
    
    print("\n   Using angle control:")
    for i, angle in enumerate(angles):
        print(f"   → Writing {angle}°...", end='')
        controller.write_angle(0, angle)
        time.sleep(1)
        print(" done")
    
    # Test all servos briefly
    print("\n4. Testing all servos (quick sweep)...")
    print("   Each servo will move to center (1500μs)")
    
    for servo_idx in range(18):
        servo_name = config.SERVO_INDEX_MAP[servo_idx]
        print(f"   → {servo_name} (index {servo_idx})...", end='')
        controller.write_microseconds(servo_idx, 1500)
        time.sleep(0.2)
        print(" done")
    
    print("\n5. Keeping servos at center position for 3 seconds...")
    time.sleep(3)
    
    # Cleanup
    print("\n6. Detaching servos...")
    controller.detach_servos()
    print("   ✓ Servos detached")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nIf servos didn't move, check:")
    print("  1. Servo power supply is connected and ON")
    print("  2. Servos are connected to correct PCA9685 channels")
    print("  3. PCA9685 boards have correct I2C addresses (0x40, 0x41)")
    print("  4. Ground is common between Pi and servo power supply")
    
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
    if 'controller' in locals():
        controller.detach_servos()

except Exception as e:
    print(f"\n\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\nDEBUG INFO:")
    print(f"  config.PCA9685_ADDRESS_1 = {hex(config.PCA9685_ADDRESS_1)}")
    print(f"  config.PCA9685_ADDRESS_2 = {hex(config.PCA9685_ADDRESS_2)}")
    print(f"  config.PCA9685_FREQUENCY = {config.PCA9685_FREQUENCY}")
    print(f"  config.SERVO_MIN_PULSE = {config.SERVO_MIN_PULSE}")
    print(f"  config.SERVO_MAX_PULSE = {config.SERVO_MAX_PULSE}")
    
    if 'controller' in locals():
        controller.cleanup()
