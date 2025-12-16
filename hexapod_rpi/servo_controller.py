"""
Servo Controller for Hexapod
Controls 18 servos via 2 PCA9685 PWM controllers over I2C
Uses adafruit-servokit for reliable servo control
"""

import time
from adafruit_servokit import ServoKit
import config


class HexapodServoController:
    """
    Controls all 18 servos for the hexapod
    Uses 2 PCA9685 boards via I2C with ServoKit library
    """
    
    def __init__(self):
        """Initialize PCA9685 controllers using ServoKit"""
        print("Initializing PCA9685 servo controllers...")
        
        try:
            # Initialize both PCA9685 boards using ServoKit
            # ServoKit handles all the low-level PWM/frequency setup automatically
            self.kit1 = ServoKit(channels=16, address=config.PCA9685_ADDRESS_1)
            self.kit2 = ServoKit(channels=16, address=config.PCA9685_ADDRESS_2)
            
            # Track servo attachment state
            self.servos_attached = False
            
            # Cache for last written angles (to avoid unnecessary writes)
            self.last_angles = [None] * 18
            
            print(f"PCA9685 #1 at {hex(config.PCA9685_ADDRESS_1)}")
            print(f"PCA9685 #2 at {hex(config.PCA9685_ADDRESS_2)}")
            print("ServoKit initialized successfully")
            
        except Exception as e:
            print(f"Error initializing ServoKit: {e}")
            print("Make sure:")
            print("  1. I2C is enabled (sudo raspi-config)")
            print("  2. PCA9685 boards are connected")
            print("  3. I2C addresses are correct (0x40, 0x41)")
            raise
    
    def attach_servos(self):
        """
        Enable all servos
        Sets initial state for all servo channels
        """
        if self.servos_attached:
            print("Servos already attached")
            return
        
        try:
            # Move all servos to neutral position (90 degrees)
            print("Attaching servos and moving to neutral position...")
            for i in range(18):
                self.write_angle(i, 90)
                time.sleep(0.01)  # Small delay between servo commands
            
            self.servos_attached = True
            print("All servos attached successfully")
            
        except Exception as e:
            print(f"Error attaching servos: {e}")
            raise
    
    def detach_servos(self):
        """
        Disable all servos
        Note: ServoKit doesn't have a direct detach, but we can stop sending commands
        """
        if not self.servos_attached:
            print("Servos already detached")
            return
        
        try:
            # ServoKit maintains the last position when we stop commanding
            # To truly "detach", we'd need to set PWM to 0, but ServoKit doesn't expose this
            # Just mark as detached
            self.servos_attached = False
            print("Servos detached")
            
        except Exception as e:
            print(f"Error detaching servos: {e}")
            raise
    
    def write_angle(self, servo_index, angle):
        """
        Write angle to a servo (0-180 degrees)
        
        Args:
            servo_index: Servo index (0-17)
            angle: Angle in degrees (0-180)
        """
        # Constrain angle to valid range
        angle = max(0, min(180, angle))
        
        # Check if angle has changed (avoid unnecessary writes)
        if self.last_angles[servo_index] == angle:
            return
        
        # Determine which board and channel
        board_num, channel = self._get_board_and_channel(servo_index)
        
        # Write angle
        if board_num == 1:
            self.kit1.servo[channel].angle = angle
        else:
            self.kit2.servo[channel].angle = angle
        
        # Cache the angle
        self.last_angles[servo_index] = angle
    
    def write_microseconds(self, servo_index, microseconds):
        """
        Write PWM pulse width in microseconds
        Converts microseconds to angle for ServoKit
        
        Args:
            servo_index: Servo index (0-17)
            microseconds: Pulse width (500-2500μs, typical servo range)
        """
        # Convert microseconds to angle (500μs = 0°, 2500μs = 180°)
        # Standard servo: 1000μs = 0°, 2000μs = 180°
        # We'll use 500-2500 range for full 0-180°
        angle = ((microseconds - 500) / 2000.0) * 180.0
        
        # Constrain to valid range
        angle = max(0, min(180, angle))
        
        self.write_angle(servo_index, angle)
    
    def write_leg_servos(self, leg, angles):
        """
        Write angles to all servos of a specific leg
        
        Args:
            leg: Leg index (0-5)
            angles: List of 3 angles [coxa, femur, tibia] in degrees
        """
        # Get servo indices for this leg
        servo_indices = self._get_leg_servo_indices(leg)
        
        # Write each angle
        for i, angle in enumerate(angles):
            self.write_angle(servo_indices[i], angle)
    
    def _get_board_and_channel(self, servo_index):
        """
        Get PCA9685 board number and channel for a servo index
        
        Args:
            servo_index: Global servo index (0-17)
        
        Returns:
            (board_num, channel) tuple
            board_num: 1 or 2
            channel: 0-15
        """
        # Servos 0-14 are on board 1 (legs 0-4)
        # Servos 15-17 are on board 2 (leg 5)
        if servo_index < 15:
            return (1, servo_index)
        else:
            return (2, servo_index - 15)
    
    def _get_leg_servo_indices(self, leg):
        """
        Get the three servo indices for a leg
        
        Args:
            leg: Leg index (0-5)
        
        Returns:
            List of [coxa_index, femur_index, tibia_index]
        """
        # Each leg has 3 servos (coxa, femur, tibia)
        base_index = leg * 3
        return [base_index, base_index + 1, base_index + 2]
    
    def get_servo_index(self, leg, joint):
        """
        Get global servo index from leg and joint
        
        Args:
            leg: Leg index (0-5)
            joint: Joint index (0=coxa, 1=femur, 2=tibia)
        
        Returns:
            Global servo index (0-17)
        """
        return leg * 3 + joint
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.servos_attached:
                self.detach_servos()
            print("Servo controller cleanup complete")
        except Exception as e:
            print(f"Error during cleanup: {e}")


# Test code
if __name__ == "__main__":
    """Test servo controller"""
    print("Testing Hexapod Servo Controller with ServoKit")
    print("=" * 60)
    
    try:
        # Create controller
        controller = HexapodServoController()
        
        # Attach servos
        print("\nAttaching servos...")
        controller.attach_servos()
        time.sleep(1)
        
        # Test individual servo movement
        print("\nTesting individual servos...")
        print("Moving servo 0 (Leg 0, Coxa) through full range")
        
        # Sweep servo 0
        for angle in range(0, 181, 10):
            print(f"  Angle: {angle}°", end='\r')
            controller.write_angle(0, angle)
            time.sleep(0.05)
        
        print("\n  Sweep complete!")
        
        # Return to neutral
        print("\nReturning to neutral position (90°)...")
        for i in range(18):
            controller.write_angle(i, 90)
            time.sleep(0.01)
        
        print("\nTest complete!")
        print("All servos should be at 90° (neutral position)")
        
        # Option to detach
        response = input("\nDetach servos? (y/n): ")
        if response.lower() == 'y':
            controller.detach_servos()
        
        # Cleanup
        controller.cleanup()
        
        print("\nServo controller test successful!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        if 'controller' in locals():
            controller.cleanup()
    
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
        if 'controller' in locals():
            controller.cleanup()
