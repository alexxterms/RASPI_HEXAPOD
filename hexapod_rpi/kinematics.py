"""
Inverse Kinematics for hexapod leg control
Port from moveToPos() function in the original Arduino code
"""

import math
from utils.vectors import Vector3
from utils.helpers import constrain, angle_to_microseconds, microseconds_to_angle
import config


class HexapodKinematics:
    """
    Handles inverse kinematics calculations for hexapod legs
    Converts 3D position to joint angles
    """
    
    def __init__(self, servo_controller):
        """
        Initialize kinematics system
        
        Args:
            servo_controller: Instance of HexapodServoController
        """
        self.servo_controller = servo_controller
        
        # Leg dimensions
        self.a1 = config.COXA_LENGTH   # Coxa length
        self.a2 = config.FEMUR_LENGTH  # Femur length
        self.a3 = config.TIBIA_LENGTH  # Tibia length
        self.leg_length = config.LEG_LENGTH
        
        # Current foot positions for each leg
        self.current_points = [Vector3(0, 0, 0) for _ in range(6)]
        
        # Servo offsets for calibration (18 values: 3 per leg)
        self.raw_offsets = [0] * 18
        self.offsets = [Vector3(
            config.BASE_OFFSET['x'],
            config.BASE_OFFSET['y'],
            config.BASE_OFFSET['z']
        ) for _ in range(6)]
        
        # Base offset
        self.base_offset = Vector3(
            config.BASE_OFFSET['x'],
            config.BASE_OFFSET['y'],
            config.BASE_OFFSET['z']
        )
        
        # Sensor data (for debugging/monitoring)
        self.foot_positions = [{'x': 0, 'y': 0} for _ in range(6)]
        
        print("Kinematics system initialized")
    
    def move_to_pos(self, leg, pos):
        """
        Move a leg to a 3D position using inverse kinematics
        
        Args:
            leg: Leg index (0-5)
            pos: Target position as Vector3 (x, y, z)
        
        Returns:
            True if position is reachable, False otherwise
        """
        # Update foot position tracking
        self.foot_positions[leg]['x'] = int(pos.x)
        self.foot_positions[leg]['y'] = int(pos.y)
        
        # Store current position
        self.current_points[leg] = pos.copy()
        
        # Check if position is reachable
        distance = Vector3(0, 0, 0).distance_to(pos)
        if distance > self.leg_length:
            if config.DEBUG_MODE:
                print(f"Leg {leg}: Point impossible to reach - Distance: {distance:.2f}")
            return False
        
        # Extract position components
        x = pos.x
        y = pos.y
        z = pos.z
        
        # Get calibration offsets for this leg
        o1 = self.offsets[leg].x
        o2 = self.offsets[leg].y
        o3 = self.offsets[leg].z
        
        # ====================================================================
        # Inverse Kinematics Calculations
        # ====================================================================
        
        # 1. Calculate coxa angle (theta1) - rotation around vertical axis
        theta1 = math.atan2(y, x) * (180 / math.pi) + o1
        
        # 2. Calculate the horizontal extension (l) and remaining extension (l1)
        l = math.sqrt(x * x + y * y)  # Total horizontal distance
        l1 = l - self.a1               # Distance after coxa
        
        # 3. Calculate the hypotenuse in the vertical plane
        h = math.sqrt(l1 * l1 + z * z)
        
        # 4. Calculate femur angle (theta2) using law of cosines
        # Angle between femur and horizontal plane
        phi1 = math.acos(constrain(
            (h * h + self.a2 * self.a2 - self.a3 * self.a3) / (2 * h * self.a2),
            -1, 1
        ))
        phi2 = math.atan2(z, l1)
        theta2 = (phi1 + phi2) * 180 / math.pi + o2
        
        # 5. Calculate tibia angle (theta3) using law of cosines
        phi3 = math.acos(constrain(
            (self.a2 * self.a2 + self.a3 * self.a3 - h * h) / (2 * self.a2 * self.a3),
            -1, 1
        ))
        theta3 = 180 - (phi3 * 180 / math.pi) + o3
        
        # ====================================================================
        # Convert angles to microseconds and write to servos
        # ====================================================================
        
        coxa_microseconds = angle_to_microseconds(theta1)
        femur_microseconds = angle_to_microseconds(theta2)
        tibia_microseconds = angle_to_microseconds(theta3)
        
        # Convert microseconds to degrees (500-2500μs maps to 0-180°)
        coxa_angle = microseconds_to_angle(coxa_microseconds)
        femur_angle = microseconds_to_angle(femur_microseconds)
        tibia_angle = microseconds_to_angle(tibia_microseconds)
        
        # Write to servos (new API expects list of angles)
        self.servo_controller.write_leg_servos(leg, [coxa_angle, femur_angle, tibia_angle])
        
        if config.DEBUG_MODE and config.PRINT_SERVO_VALUES:
            print(f"Leg {leg}: pos={pos}, angles=({theta1:.1f}°, {theta2:.1f}°, {theta3:.1f}°)")
        
        return True
    
    def update_offset_variables(self):
        """
        Update offset vectors from raw offset array
        Called after loading offsets from storage or receiving calibration data
        """
        for i in range(6):
            self.offsets[i] = Vector3(
                self.raw_offsets[i * 3] + self.base_offset.x,
                self.raw_offsets[i * 3 + 1] + self.base_offset.y,
                self.raw_offsets[i * 3 + 2] + self.base_offset.z
            )
        
        if config.DEBUG_MODE:
            print("Offsets updated:")
            for i, offset in enumerate(self.offsets):
                print(f"  Leg {i}: {offset}")
    
    def set_raw_offsets(self, offsets):
        """
        Set raw offset values (18 values: 3 per leg)
        
        Args:
            offsets: List of 18 offset values
        """
        if len(offsets) != 18:
            print(f"Error: Expected 18 offsets, got {len(offsets)}")
            return
        
        self.raw_offsets = offsets.copy()
        self.update_offset_variables()
    
    def get_raw_offsets(self):
        """
        Get current raw offset values
        
        Returns:
            List of 18 offset values
        """
        return self.raw_offsets.copy()
    
    def get_current_position(self, leg):
        """
        Get current position of a leg
        
        Args:
            leg: Leg index (0-5)
        
        Returns:
            Current position as Vector3
        """
        if 0 <= leg < 6:
            return self.current_points[leg].copy()
        return Vector3(0, 0, 0)
    
    def get_all_positions(self):
        """
        Get current positions of all legs
        
        Returns:
            List of 6 Vector3 positions
        """
        return [pos.copy() for pos in self.current_points]
    
    def set_current_position(self, leg, pos):
        """
        Set current position of a leg (for initialization)
        
        Args:
            leg: Leg index (0-5)
            pos: Position as Vector3
        """
        if 0 <= leg < 6:
            self.current_points[leg] = pos.copy()


# Test code
if __name__ == "__main__":
    """Test kinematics calculations (without actual hardware)"""
    print("Testing Hexapod Kinematics...")
    print("Note: This test runs without hardware - servo commands will fail gracefully")
    
    # Mock servo controller for testing
    class MockServoController:
        def write_leg_servos(self, leg, coxa, femur, tibia):
            print(f"  Servo commands: Leg {leg} -> Coxa: {coxa}μs, Femur: {femur}μs, Tibia: {tibia}μs")
        
        def attach_servos(self):
            print("  Mock servos attached")
    
    # Create kinematics system with mock controller
    mock_controller = MockServoController()
    ik = HexapodKinematics(mock_controller)
    
    print("\nTest 1: Move leg 0 to a reachable position")
    pos1 = Vector3(200, 0, -50)
    result = ik.move_to_pos(0, pos1)
    print(f"  Result: {'Success' if result else 'Failed'}")
    
    print("\nTest 2: Try to move leg 0 to unreachable position")
    pos2 = Vector3(500, 0, 0)  # Too far
    result = ik.move_to_pos(0, pos2)
    print(f"  Result: {'Success' if result else 'Failed (expected)'}")
    
    print("\nTest 3: Test offset system")
    test_offsets = [1, -2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ik.set_raw_offsets(test_offsets)
    
    print("\nTest 4: Get current positions")
    positions = ik.get_all_positions()
    for i, pos in enumerate(positions):
        print(f"  Leg {i}: {pos}")
