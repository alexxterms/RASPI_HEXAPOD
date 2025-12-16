"""
Sleep State - Complete implementation
Smoothly lowers hexapod to ground and detaches servos
Port from Sleep_State.ino
"""

from utils.vectors import Vector3
from utils.helpers import lerp
import config


class SleepState:
    """
    Sleep state - lowers hexapod to ground and powers down servos
    Saves power and allows safe handling when not in use
    """
    
    def __init__(self, servo_controller, kinematics, current_points):
        """
        Initialize sleep state
        
        Args:
            servo_controller: HexapodServoController instance
            kinematics: HexapodKinematics instance
            current_points: List of current leg positions
        """
        self.servo_controller = servo_controller
        self.kinematics = kinematics
        self.current_points = current_points
        
        # Target sleep position - legs folded close to body
        self.target_sleep_position = Vector3(130, 0, -46)
        
        # State tracking
        self.sleep_state = 1
        self.initialized = False
        self.servos_detached = False
        
        print(f"Sleep target position: {self.target_sleep_position}")
    
    def update(self):
        """
        Update sleep state
        
        Returns:
            True if sleeping (servos detached), False if still moving
        """
        if not self.initialized:
            self.initialized = True
            self.sleep_state = 1
            self.servos_detached = False
            print("Entering sleep state...")
            print("Lowering to ground and detaching servos")
        
        # Check if servos are already detached
        if not self.servo_controller.servos_attached:
            return True
        
        # Optional Phase 0: Lift legs slightly (commented out in original)
        # This would lift legs to z=1 before lowering to sleep position
        # Skipping this phase as it's commented in original code
        
        # Phase 1: Move to sleep position
        if self.sleep_state == 1:
            target_reached = True
            
            for i in range(6):
                # Smoothly lerp toward target position
                next_pos = lerp(
                    self.current_points[i],
                    self.target_sleep_position,
                    0.03
                )
                
                # Snap to target if very close (within 1mm)
                if abs(self.current_points[i].x - self.target_sleep_position.x) < 1:
                    next_pos.x = self.target_sleep_position.x
                if abs(self.current_points[i].y - self.target_sleep_position.y) < 1:
                    next_pos.y = self.target_sleep_position.y
                if abs(self.current_points[i].z - self.target_sleep_position.z) < 1:
                    next_pos.z = self.target_sleep_position.z
                
                self.kinematics.move_to_pos(i, next_pos)
                
                # Check if this leg reached target
                if self.current_points[i] != self.target_sleep_position:
                    target_reached = False
            
            if target_reached:
                print("Sleep position reached - detaching servos")
                self.sleep_state = 2
            
            return False
        
        # Phase 2: Detach servos to save power
        if self.sleep_state == 2:
            self.servo_controller.detach_servos()
            self.servos_detached = True
            self.sleep_state = 3
            print("Servos detached - hexapod sleeping")
            return True
        
        # Phase 3: Sleep complete
        if self.sleep_state == 3:
            return True
        
        return False
    
    def wake_up(self):
        """
        Wake up from sleep - reattach servos and prepare for operation
        
        Returns:
            True if wake-up complete
        """
        if self.servos_detached:
            print("Waking up - reattaching servos")
            self.servo_controller.attach_servos()
            self.servos_detached = False
            print("Servos reattached - ready for operation")
            return True
        return False
    
    def is_sleeping(self):
        """Check if currently in sleep mode (servos detached)"""
        return self.sleep_state == 3 and self.servos_detached
    
    def reset(self):
        """Reset state for next sleep cycle"""
        self.initialized = False
        self.sleep_state = 1
        # Note: servos_detached state persists until wake_up() is called


# Utility functions for sleep management

def enter_sleep_mode(servo_controller, kinematics, current_points, smooth=True):
    """
    Convenience function to enter sleep mode
    
    Args:
        servo_controller: HexapodServoController instance
        kinematics: HexapodKinematics instance
        current_points: List of current leg positions
        smooth: If True, animate to sleep position; if False, detach immediately
    
    Returns:
        SleepState instance
    """
    sleep_state = SleepState(servo_controller, kinematics, current_points)
    
    if not smooth:
        # Immediate sleep without animation
        servo_controller.detach_servos()
        sleep_state.sleep_state = 3
        sleep_state.servos_detached = True
        print("Immediate sleep - servos detached")
    
    return sleep_state


def emergency_sleep(servo_controller):
    """
    Emergency sleep - immediately detach servos without movement
    Use when battery low or immediate shutdown needed
    
    Args:
        servo_controller: HexapodServoController instance
    """
    print("EMERGENCY SLEEP - Immediate servo detachment")
    servo_controller.detach_servos()


# Test code
if __name__ == "__main__":
    """Test sleep state"""
    print("Testing Sleep State...")
    
    # Mock classes for testing
    class MockServoController:
        def __init__(self):
            self.servos_attached = True
        
        def detach_servos(self):
            self.servos_attached = False
            print("  Servos detached")
        
        def attach_servos(self):
            self.servos_attached = True
            print("  Servos attached")
    
    class MockKinematics:
        def __init__(self):
            self.positions = [Vector3(200, 0, -100) for _ in range(6)]
        
        def move_to_pos(self, leg, pos):
            self.positions[leg] = pos
            print(f"  Leg {leg} -> {pos}")
    
    # Create mock instances
    mock_servo = MockServoController()
    mock_ik = MockKinematics()
    
    # Create sleep state
    sleep_state = SleepState(mock_servo, mock_ik, mock_ik.positions)
    
    print("\n1. Start sleep sequence:")
    sleep_state.update()
    
    print("\n2. Simulate gradual movement to sleep position:")
    # Move legs closer to target
    for i in range(6):
        mock_ik.positions[i] = lerp(
            mock_ik.positions[i],
            sleep_state.target_sleep_position,
            0.5
        )
    
    print("\n3. Continue sleep sequence:")
    result = sleep_state.update()
    print(f"   Sleep complete: {result}")
    
    print("\n4. Snap to final position:")
    for i in range(6):
        mock_ik.positions[i] = sleep_state.target_sleep_position
    
    print("\n5. Final update (should detach servos):")
    result = sleep_state.update()
    print(f"   Sleeping: {result}")
    print(f"   Servos attached: {mock_servo.servos_attached}")
    
    print("\n6. Check sleep status:")
    print(f"   Is sleeping: {sleep_state.is_sleeping()}")
    
    print("\n7. Wake up:")
    sleep_state.wake_up()
    print(f"   Servos attached: {mock_servo.servos_attached}")
    
    print("\n8. Test emergency sleep:")
    mock_servo.servos_attached = True
    emergency_sleep(mock_servo)
    print(f"   Servos attached: {mock_servo.servos_attached}")
    
    print("\nSleep state test complete!")
