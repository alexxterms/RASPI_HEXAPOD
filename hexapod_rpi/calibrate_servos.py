#!/usr/bin/env python3
"""
Servo Calibration Helper
Moves all servos to calibration position for physical alignment
"""

import sys
import time
from utils.vectors import Vector3
from utils.helpers import Timer
from servo_controller import HexapodServoController
from kinematics import HexapodKinematics
from storage import HexapodStorage
from states.calibration import CalibrationState
import config


def main():
    """Run calibration mode for servo alignment"""
    print("=" * 70)
    print("HEXAPOD SERVO CALIBRATION - Physical Alignment Mode")
    print("=" * 70)
    print()
    print("This tool will move all servos to a known calibration position")
    print("where you can physically attach servo horns in proper alignment.")
    print()
    print("CALIBRATION POSITION:")
    print(f"  X: {config.COXA_LENGTH + 43}mm")
    print(f"  Y: 0mm")
    print(f"  Z: {config.FEMUR_LENGTH + 185}mm")
    print()
    print("At this position, all legs should be:")
    print("  - Coxas pointing straight out from body")
    print("  - Femurs at same angle (~45° up)")
    print("  - Tibias at same angle (~45° down)")
    print()
    
    response = input("Ready to move servos to calibration position? (y/n): ")
    if response.lower() != 'y':
        print("Calibration cancelled.")
        return
    
    try:
        # Initialize timer
        Timer.init()
        
        # Initialize storage
        print("\nInitializing storage...")
        storage = HexapodStorage()
        
        # Initialize servo controller
        print("Initializing servo controller...")
        servo_controller = HexapodServoController()
        
        # Initialize kinematics
        print("Initializing kinematics...")
        kinematics = HexapodKinematics(servo_controller)
        
        # Load any existing offsets
        offsets = storage.load_offsets()
        kinematics.set_raw_offsets(offsets)
        print(f"Loaded offsets: {offsets}")
        
        # Attach servos
        print("\nAttaching servos...")
        servo_controller.attach_servos()
        time.sleep(0.5)
        
        # Get current positions (will be at default)
        current_points = kinematics.get_all_positions()
        
        # Create calibration state
        print("\nInitializing calibration state...")
        cal_state = CalibrationState(kinematics, current_points, storage)
        
        # Display instructions
        print("\n" + "=" * 70)
        print(cal_state.get_calibration_instructions())
        print("=" * 70)
        
        # Move to calibration position
        print("\nMoving to calibration position...")
        print("This will take a few seconds...")
        
        # Run calibration updates until complete
        max_iterations = 200  # Safety limit
        iterations = 0
        
        while iterations < max_iterations:
            complete = cal_state.update()
            if complete:
                print("\n✅ Calibration position reached!")
                break
            
            iterations += 1
            time.sleep(0.02)  # 50Hz update rate
        
        if iterations >= max_iterations:
            print("\n⚠️  Timeout reaching calibration position")
            print("Servos may still be moving...")
        
        print("\n" + "=" * 70)
        print("SERVO ALIGNMENT INSTRUCTIONS:")
        print("=" * 70)
        print()
        print("The hexapod is now in calibration position.")
        print()
        print("FOR EACH LEG:")
        print("  1. Check if servo horn is aligned correctly")
        print("  2. If misaligned:")
        print("     a. POWER OFF the servos (or detach)")
        print("     b. Remove servo horn")
        print("     c. Rotate to correct position")
        print("     d. Reattach servo horn")
        print("     e. POWER ON and verify alignment")
        print()
        print("  3. If servo horn position is correct but leg angle is off:")
        print("     - Note the leg number (0-5)")
        print("     - Note the joint (coxa/femur/tibia)")
        print("     - You'll adjust offsets later in software")
        print()
        print("Expected alignment at calibration position:")
        print("  - ALL coxas should point straight out")
        print("  - ALL femurs should be at same upward angle")
        print("  - ALL tibias should be at same downward angle")
        print()
        
        input("Press Enter when you're done aligning servo horns...")
        
        print("\n" + "=" * 70)
        print("OPTIONS:")
        print("=" * 70)
        print("1. Keep servos powered (stay in position)")
        print("2. Detach servos (safe to handle)")
        print("3. Return to home position")
        print()
        
        choice = input("Choose option (1/2/3): ")
        
        if choice == '2':
            print("\nDetaching servos...")
            servo_controller.detach_servos()
            print("✅ Servos detached - safe to handle")
        
        elif choice == '3':
            print("\nReturning to home position...")
            home_pos = Vector3(
                config.DISTANCE_FROM_CENTER,
                0,
                config.DISTANCE_FROM_GROUND_BASE
            )
            for leg in range(6):
                kinematics.move_to_pos(leg, home_pos)
                time.sleep(0.1)
            print("✅ Returned to home position")
            
            detach = input("Detach servos? (y/n): ")
            if detach.lower() == 'y':
                servo_controller.detach_servos()
                print("✅ Servos detached")
        
        else:
            print("\nServos staying powered in calibration position")
            print("Press Ctrl+C when done")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nShutting down...")
        
        # Cleanup
        print("\nCleaning up...")
        servo_controller.cleanup()
        print("✅ Cleanup complete")
        
    except KeyboardInterrupt:
        print("\n\nCalibration interrupted by user")
        if 'servo_controller' in locals():
            servo_controller.cleanup()
    
    except Exception as e:
        print(f"\n❌ Error during calibration: {e}")
        import traceback
        traceback.print_exc()
        if 'servo_controller' in locals():
            servo_controller.cleanup()
        return 1
    
    print("\n" + "=" * 70)
    print("Calibration session complete!")
    print("=" * 70)
    print()
    print("NEXT STEPS:")
    print("1. Verify all servo horns are properly aligned")
    print("2. If you need fine-tuning, run the main program and use")
    print("   calibration mode to adjust offsets")
    print("3. Save any offset adjustments for permanent calibration")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
