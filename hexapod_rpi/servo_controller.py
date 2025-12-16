"""
Servo Controller for Hexapod using dual PCA9685 boards
Handles communication with PCA9685 PWM controllers via I2C
"""

import time
import math
from adafruit_pca9685 import PCA9685
import board
import busio

import config


class HexapodServoController:
    """
    Controls 18 servos (6 legs × 3 joints) using two PCA9685 boards.
    Provides interface similar to Arduino Servo library.
    """
    
    def __init__(self):
        """Initialize I2C connection and both PCA9685 boards"""
        self.servos_attached = False
        self.pca9685_boards = {}
        
        try:
            # Initialize I2C bus
            self.i2c = busio.I2C(board.SCL, board.SDA)
            
            # Initialize PCA9685 boards
            self.pca9685_boards[config.PCA9685_ADDRESS_1] = PCA9685(
                self.i2c, address=config.PCA9685_ADDRESS_1
            )
            self.pca9685_boards[config.PCA9685_ADDRESS_2] = PCA9685(
                self.i2c, address=config.PCA9685_ADDRESS_2
            )
            
            # Set PWM frequency for servos (50Hz)
            for board_addr in self.pca9685_boards:
                self.pca9685_boards[board_addr].frequency = config.PCA9685_FREQUENCY
            
            print("PCA9685 boards initialized successfully")
            
        except Exception as e:
            print(f"Error initializing PCA9685 boards: {e}")
            raise
    
    def attach_servos(self):
        """
        Enable all servos (equivalent to Arduino's attach())
        Sets initial state for all servo channels
        """
        if self.servos_attached:
            print("Servos already attached")
            return
        
        try:
            # Initialize all servo channels to neutral position (1500μs)
            for servo_name in config.SERVO_INDEX_MAP:
                self.write_microseconds_by_name(servo_name, 1500)
            
            self.servos_attached = True
            print("Servos attached successfully")
            
        except Exception as e:
            print(f"Error attaching servos: {e}")
            raise
    
    def detach_servos(self):
        """
        Disable all servos (equivalent to Arduino's detach())
        Stops sending PWM signals to conserve power
        """
        if not self.servos_attached:
            print("Servos already detached")
            return
        
        try:
            # Set all channels to 0 (off)
            for board_addr in self.pca9685_boards:
                for channel in range(16):
                    self.pca9685_boards[board_addr].channels[channel].duty_cycle = 0
            
            self.servos_attached = False
            print("Servos detached")
            
        except Exception as e:
            print(f"Error detaching servos: {e}")
    
    def write_microseconds(self, servo_index, microseconds):
        """
        Write PWM value in microseconds to a servo by index (0-17)
        
        Args:
            servo_index: Servo index (0-17)
            microseconds: Pulse width in microseconds (500-2500)
        """
        if servo_index < 0 or servo_index >= len(config.SERVO_INDEX_MAP):
            print(f"Invalid servo index: {servo_index}")
            return
        
        servo_name = config.SERVO_INDEX_MAP[servo_index]
        self.write_microseconds_by_name(servo_name, microseconds)
    
    def write_microseconds_by_name(self, servo_name, microseconds):
        """
        Write PWM value in microseconds to a servo by name
        
        Args:
            servo_name: Servo name (e.g., 'coxa1', 'femur2')
            microseconds: Pulse width in microseconds (500-2500)
        """
        if servo_name not in config.SERVO_CHANNELS:
            print(f"Invalid servo name: {servo_name}")
            return
        
        # Clamp microseconds to valid range
        microseconds = max(config.SERVO_MIN_PULSE, 
                          min(config.SERVO_MAX_PULSE, microseconds))
        
        # Get board address and channel
        board_addr, channel = config.SERVO_CHANNELS[servo_name]
        
        # Convert microseconds to duty cycle
        # PCA9685 is 12-bit (0-4095)
        # At 50Hz, period is 20ms (20000μs)
        # duty_cycle = (microseconds / 20000) * 4095
        duty_cycle = int((microseconds / 20000.0) * 4095)
        
        if config.DEBUG_MODE and config.PRINT_SERVO_VALUES:
            print(f"{servo_name}: {microseconds}μs -> duty_cycle {duty_cycle}")
        
        try:
            # Write to PCA9685
            self.pca9685_boards[board_addr].channels[channel].duty_cycle = duty_cycle
        except Exception as e:
            print(f"Error writing to {servo_name}: {e}")
    
    def write_angle(self, servo_index, angle):
        """
        Write angle (0-180) to a servo
        Converts angle to microseconds and calls write_microseconds
        
        Args:
            servo_index: Servo index (0-17)
            angle: Angle in degrees (0-180)
        """
        # Convert angle to microseconds (linear mapping)
        microseconds = self.angle_to_microseconds(angle)
        self.write_microseconds(servo_index, microseconds)
    
    def angle_to_microseconds(self, angle):
        """
        Convert angle (0-180) to microseconds (500-2500)
        
        Args:
            angle: Angle in degrees (0-180)
        
        Returns:
            Pulse width in microseconds
        """
        # Clamp angle to 0-180
        angle = max(0, min(180, angle))
        
        # Linear mapping: 0° -> 500μs, 180° -> 2500μs
        microseconds = config.SERVO_MIN_PULSE + (
            (angle / 180.0) * (config.SERVO_MAX_PULSE - config.SERVO_MIN_PULSE)
        )
        
        return int(microseconds)
    
    def write_leg_servos(self, leg_index, coxa_us, femur_us, tibia_us):
        """
        Write microsecond values to all three servos of a leg
        
        Args:
            leg_index: Leg number (0-5)
            coxa_us: Coxa servo pulse width in microseconds
            femur_us: Femur servo pulse width in microseconds
            tibia_us: Tibia servo pulse width in microseconds
        """
        if leg_index < 0 or leg_index > 5:
            print(f"Invalid leg index: {leg_index}")
            return
        
        # Calculate servo indices for this leg
        base_index = leg_index * 3
        
        self.write_microseconds(base_index + 0, coxa_us)   # Coxa
        self.write_microseconds(base_index + 1, femur_us)  # Femur
        self.write_microseconds(base_index + 2, tibia_us)  # Tibia
    
    def cleanup(self):
        """Clean up resources and detach servos"""
        self.detach_servos()
        
        # Deinitialize PCA9685 boards
        for board_addr in self.pca9685_boards:
            self.pca9685_boards[board_addr].deinit()
        
        print("Servo controller cleaned up")


# Standalone test function
if __name__ == "__main__":
    """Test the servo controller"""
    print("Testing Hexapod Servo Controller...")
    
    controller = HexapodServoController()
    controller.attach_servos()
    
    try:
        print("\nTesting leg 0 servos...")
        print("Moving to center position (1500μs)")
        controller.write_leg_servos(0, 1500, 1500, 1500)
        time.sleep(2)
        
        print("Moving to min position (1000μs)")
        controller.write_leg_servos(0, 1000, 1000, 1000)
        time.sleep(2)
        
        print("Moving to max position (2000μs)")
        controller.write_leg_servos(0, 2000, 2000, 2000)
        time.sleep(2)
        
        print("Returning to center")
        controller.write_leg_servos(0, 1500, 1500, 1500)
        time.sleep(1)
        
        print("\nTest complete!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    finally:
        controller.cleanup()
