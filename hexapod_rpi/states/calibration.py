"""
Calibration State - Complete implementation
Allows fine-tuning of individual servo offsets
Port from Calibration_State.ino
"""

from utils.vectors import Vector3
from utils.helpers import lerp
import config


class CalibrationState:
    """
    Calibration state - positions legs for servo offset adjustment
    Moves all legs to a known position to visually check alignment
    """
    
    def __init__(self, kinematics, current_points, storage):
        """
        Initialize calibration state
        
        Args:
            kinematics: HexapodKinematics instance
            current_points: List of current leg positions
            storage: HexapodStorage instance for saving offsets
        """
        self.kinematics = kinematics
        self.current_points = current_points
        self.storage = storage
        
        # Calibration target position
        # Position where all leg joints are at known angles for visual inspection
        a1 = config.COXA_LENGTH
        a2 = config.FEMUR_LENGTH
        a3 = config.TIBIA_LENGTH
        
        # Standard calibration pose: legs extended at specific angles
        self.target_calibration = Vector3(a1 + 43, 0, a2 + 185)
        # Alternative: self.target_calibration = Vector3(a1 + a3, 0, a2)
        
        # Intermediate height for safety (lift legs before moving to calibration)
        self.in_between_z = -20
        
        # Track previous offsets to detect changes
        self.previous_offsets = [0] * 18
        
        # State tracking
        self.initialized = False
        self.legs_lifted = False
        
        print(f"Calibration target: {self.target_calibration}")
    
    def update(self, rc_offsets=None):
        """
        Update calibration state
        
        Args:
            rc_offsets: List of 18 offset values from RC controller (optional)
                       If None, uses stored offsets
        
        Returns:
            True if in calibration position, False if still moving
        """
        if not self.initialized:
            self.initialized = True
            self.legs_lifted = False
            print("Entering calibration state...")
            print("Lift legs to safe height, then move to calibration position")
        
        # Phase 1: Lift legs to safe intermediate height
        if not self.legs_lifted:
            all_legs_up = True
            
            for i in range(6):
                if self.current_points[i].z < self.in_between_z:
                    all_legs_up = False
                    # Smoothly lift leg to intermediate height
                    next_z = lerp(
                        self.current_points[i].z,
                        self.in_between_z + 2,
                        0.03
                    )
                    new_pos = Vector3(
                        self.current_points[i].x,
                        self.current_points[i].y,
                        next_z
                    )
                    self.kinematics.move_to_pos(i, new_pos)
            
            if all_legs_up:
                self.legs_lifted = True
                print("Legs lifted - moving to calibration position")
            
            return False
        
        # Phase 2: Move to calibration position and apply offsets
        if self.legs_lifted:
            # Apply offsets from controller if provided
            if rc_offsets is not None and len(rc_offsets) == 18:
                # Check if offsets have changed
                if rc_offsets != self.previous_offsets:
                    self.previous_offsets = rc_offsets.copy()
                    self.kinematics.set_raw_offsets(rc_offsets)
                    print(f"Applied new offsets: {rc_offsets}")
            
            # Move all legs toward calibration position
            all_at_target = True
            
            for i in range(6):
                current = self.current_points[i]
                target = self.target_calibration
                
                # Move incrementally toward target (5mm steps)
                next_x = min(current.x + 5, target.x) if current.x < target.x else max(current.x - 5, target.x)
                next_y = min(current.y + 5, target.y) if current.y < target.y else max(current.y - 5, target.y)
                next_z = min(current.z + 5, target.z) if current.z < target.z else max(current.z - 5, target.z)
                
                new_pos = Vector3(next_x, next_y, next_z)
                self.kinematics.move_to_pos(i, new_pos)
                
                # Check if this leg reached target
                distance = current.distance_to(target)
                if distance > 5:
                    all_at_target = False
            
            if all_at_target:
                return True  # Calibration position reached
        
        return False
    
    def adjust_offset(self, leg, joint, delta):
        """
        Adjust offset for a specific servo
        
        Args:
            leg: Leg index (0-5)
            joint: Joint index (0=coxa, 1=femur, 2=tibia)
            delta: Amount to change offset (+/- degrees)
        """
        if leg < 0 or leg > 5:
            print(f"Invalid leg index: {leg}")
            return
        
        if joint < 0 or joint > 2:
            print(f"Invalid joint index: {joint}")
            return
        
        # Get current offsets
        offsets = self.kinematics.get_raw_offsets()
        
        # Calculate offset index
        offset_index = leg * 3 + joint
        
        # Apply delta
        offsets[offset_index] += delta
        
        # Constrain to reasonable range (-30 to +30 degrees)
        offsets[offset_index] = max(-30, min(30, offsets[offset_index]))
        
        # Apply updated offsets
        self.kinematics.set_raw_offsets(offsets)
        
        joint_names = ['coxa', 'femur', 'tibia']
        print(f"Adjusted Leg {leg} {joint_names[joint]}: "
              f"offset = {offsets[offset_index]}")
    
    def save_offsets(self):
        """
        Save current offsets to persistent storage
        
        Returns:
            True if successful, False otherwise
        """
        offsets = self.kinematics.get_raw_offsets()
        success = self.storage.save_offsets(offsets)
        
        if success:
            print("Calibration offsets saved successfully!")
            print(f"Offsets: {offsets}")
        else:
            print("Failed to save offsets")
        
        return success
    
    def load_offsets(self):
        """
        Load offsets from persistent storage
        
        Returns:
            List of 18 offset values
        """
        offsets = self.storage.load_offsets()
        self.kinematics.set_raw_offsets(offsets)
        print(f"Loaded offsets: {offsets}")
        return offsets
    
    def reset_offsets(self):
        """Reset all offsets to zero"""
        zero_offsets = [0] * 18
        self.kinematics.set_raw_offsets(zero_offsets)
        print("All offsets reset to zero")
    
    def print_current_offsets(self):
        """Print current offset values in a readable format"""
        offsets = self.kinematics.get_raw_offsets()
        
        print("\nCurrent Servo Offsets:")
        print("=" * 50)
        joint_names = ['Coxa', 'Femur', 'Tibia']
        
        for leg in range(6):
            print(f"Leg {leg}:")
            for joint in range(3):
                offset_index = leg * 3 + joint
                print(f"  {joint_names[joint]:6s}: {offsets[offset_index]:+3d}°")
        
        print("=" * 50)
    
    def get_calibration_instructions(self):
        """
        Get human-readable calibration instructions
        
        Returns:
            String with instructions
        """
        return """
CALIBRATION INSTRUCTIONS:
========================

1. The hexapod will lift all legs to a safe height
2. Then move to calibration position where all joints are at known angles
3. Visually inspect each leg:
   - All coxas should point straight out from body
   - All femurs should be at same angle
   - All tibias should be at same angle
   
4. If a servo is misaligned:
   - Note which leg (0-5) and joint (coxa/femur/tibia)
   - Adjust offset in small increments (±1° to ±5°)
   - Positive offset = rotate clockwise
   - Negative offset = rotate counter-clockwise

5. Save offsets when satisfied

CALIBRATION POSITION:
- X: {:.1f}mm
- Y: {:.1f}mm  
- Z: {:.1f}mm

This position makes it easy to see if servos are properly aligned.
        """.format(
            self.target_calibration.x,
            self.target_calibration.y,
            self.target_calibration.z
        )
    
    def reset(self):
        """Reset state for next calibration session"""
        self.initialized = False
        self.legs_lifted = False


# Standalone calibration utility functions

def interactive_calibration(kinematics, storage):
    """
    Interactive calibration session (for testing/manual calibration)
    
    Args:
        kinematics: HexapodKinematics instance
        storage: HexapodStorage instance
    """
    print("\n" + "=" * 60)
    print("HEXAPOD SERVO CALIBRATION UTILITY")
    print("=" * 60)
    
    cal_state = CalibrationState(kinematics, kinematics.get_all_positions(), storage)
    
    print(cal_state.get_calibration_instructions())
    
    print("\nCommands:")
    print("  adjust <leg> <joint> <delta>  - Adjust servo offset")
    print("  print                         - Print current offsets")
    print("  save                          - Save offsets to file")
    print("  load                          - Load offsets from file")
    print("  reset                         - Reset all offsets to zero")
    print("  quit                          - Exit calibration")
    print("\nExample: adjust 0 1 -5")
    print("         (adjusts leg 0, femur, by -5 degrees)")
    
    return cal_state


# Test code
if __name__ == "__main__":
    """Test calibration state"""
    print("Testing Calibration State...")
    
    # Mock classes for testing
    class MockKinematics:
        def __init__(self):
            self.positions = [Vector3(150, 0, -50) for _ in range(6)]
            self.offsets = [0] * 18
        
        def move_to_pos(self, leg, pos):
            self.positions[leg] = pos
            print(f"  Leg {leg} -> {pos}")
        
        def get_all_positions(self):
            return self.positions
        
        def get_raw_offsets(self):
            return self.offsets
        
        def set_raw_offsets(self, offsets):
            self.offsets = offsets.copy()
            print(f"  Offsets updated: {offsets}")
    
    class MockStorage:
        def __init__(self):
            self.saved_offsets = [0] * 18
        
        def save_offsets(self, offsets):
            self.saved_offsets = offsets.copy()
            print(f"  Saved to storage: {offsets}")
            return True
        
        def load_offsets(self):
            return self.saved_offsets
    
    # Create mock instances
    mock_ik = MockKinematics()
    mock_storage = MockStorage()
    
    # Create calibration state
    cal = CalibrationState(mock_ik, mock_ik.positions, mock_storage)
    
    print("\n1. Initial update (lifting phase):")
    cal.update()
    
    print("\n2. Simulate legs lifted:")
    for i in range(6):
        mock_ik.positions[i].z = -15
    
    print("\n3. Update (moving to calibration):")
    cal.update()
    
    print("\n4. Test offset adjustment:")
    cal.adjust_offset(0, 1, -5)  # Leg 0, femur, -5 degrees
    cal.adjust_offset(2, 0, 3)   # Leg 2, coxa, +3 degrees
    
    print("\n5. Print offsets:")
    cal.print_current_offsets()
    
    print("\n6. Save offsets:")
    cal.save_offsets()
    
    print("\n7. Reset offsets:")
    cal.reset_offsets()
    
    print("\n8. Load offsets:")
    cal.load_offsets()
    
    print("\n9. Print instructions:")
    print(cal.get_calibration_instructions())
    
    print("\nCalibration state test complete!")
