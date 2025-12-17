"""
Main control loop for Hexapod Robot
Raspberry Pi Zero with dual PCA9685 servo controllers and ELRS receiver
"""

import time
import sys
import signal
from utils.vectors import Vector2, Vector3
from utils.helpers import Timer, lerp, get_point_on_bezier_curve
from servo_controller import HexapodServoController
from kinematics import HexapodKinematics
from receiver.crsf_receiver import CRSFReceiver
from storage import HexapodStorage
from states.walking import WalkingState
from states.standing import StandingState
from states.calibration import CalibrationState
from states.sleep import SleepState
from states.attacks import AttacksState
import config


class HexapodController:
    """Main hexapod controller class"""
    
    def __init__(self):
        """Initialize all subsystems"""
        print("=" * 50)
        print("Hexapod Robot Controller - Raspberry Pi Zero")
        print("=" * 50)
        
        # Initialize timer
        Timer.init()
        
        # Initialize storage
        print("\nInitializing storage...")
        self.storage = HexapodStorage()
        
        # Initialize servo controller
        print("\nInitializing servo controller...")
        self.servo_controller = HexapodServoController()
        
        # Initialize kinematics
        print("\nInitializing kinematics...")
        self.kinematics = HexapodKinematics(self.servo_controller)
        
        # Load offsets from storage
        offsets = self.storage.load_offsets()
        self.kinematics.set_raw_offsets(offsets)
        print(f"Loaded servo offsets: {offsets}")
        
        # Initialize ELRS receiver
        print("\nInitializing ELRS receiver...")
        try:
            self.receiver = CRSFReceiver()
        except Exception as e:
            print(f"Warning: Could not initialize receiver: {e}")
            self.receiver = None
        
        # State variables
        self.current_state = config.State.INITIALIZE
        self.current_gait = config.Gait.TRI
        self.connected = False
        
        # Initialize state objects
        self.walking_state = None
        self.standing_state = None
        self.calibration_state = None
        self.sleep_state = None
        self.attacks_state = None
        
        # Movement parameters
        self.distance_from_ground = config.DISTANCE_FROM_GROUND_BASE
        self.target_distance_from_ground = config.DISTANCE_FROM_GROUND_BASE
        self.distance_from_center = config.DISTANCE_FROM_CENTER
        
        # Control inputs
        self.joy1_current = Vector2(0, 0)
        self.joy1_target = Vector2(0, 0)
        self.joy2_current = Vector2(0, 0)
        self.joy2_target = Vector2(0, 0)
        
        # Timing
        self.last_loop_time = Timer.millis()
        self.loop_count = 0
        
        print("\n" + "=" * 50)
        print("Initialization complete!")
        print("=" * 50)
    
    def setup(self):
        """Initial setup - attach servos and move to initial position"""
        print("\nAttaching servos...")
        self.servo_controller.attach_servos()
        
        print("Moving to initial position...")
        # Move all legs to a safe starting position
        initial_pos = Vector3(
            config.DISTANCE_FROM_CENTER,
            0,
            config.DISTANCE_FROM_GROUND_BASE
        )
        
        for leg in range(6):
            self.kinematics.move_to_pos(leg, initial_pos)
        
        time.sleep(2)  # Give servos time to reach position
        
        # Initialize state objects with current positions
        current_points = self.kinematics.get_all_positions()
        
        print("Initializing state objects...")
        self.standing_state = StandingState(
            self.kinematics,
            current_points
        )
        
        self.walking_state = WalkingState(
            self.kinematics,
            current_points
        )
        # Set initial gait
        self.walking_state.set_gait(self.current_gait)
        
        self.calibration_state = CalibrationState(
            self.kinematics,
            current_points,
            self.storage
        )
        
        self.sleep_state = SleepState(
            self.servo_controller,
            self.kinematics,
            current_points
        )
        
        self.attacks_state = AttacksState(
            self.kinematics,
            current_points
        )
        
        print("Setup complete - entering standing state")
        self.current_state = config.State.STAND
    
    def update_receiver(self):
        """Update receiver data and process inputs"""
        if self.receiver is None:
            return
        
        # Read receiver data
        if self.receiver.update():
            data = self.receiver.get_control_data()
            
            # Update connection status
            self.connected = data['connected']
            
            if self.connected:
                # Update target joystick values
                self.joy1_target.x = data['joy1_x']
                self.joy1_target.y = data['joy1_y']
                self.joy2_target.x = data['joy2_x']
                self.joy2_target.y = data['joy2_y']
                
                # Update gait
                self.current_gait = data['gait']
                if self.walking_state:
                    self.walking_state.set_gait(self.current_gait)
                
                # Handle buttons for state changes
                if data['button1']:
                    # Button 1: Calibration mode
                    if self.current_state != config.State.CALIBRATE:
                        if config.PRINT_STATE_CHANGES:
                            print("Button 1: Entering calibration mode")
                        self.current_state = config.State.CALIBRATE
                        if self.calibration_state:
                            self.calibration_state.reset()
                
                if data['button2']:
                    # Button 2: Sleep mode
                    if self.current_state != config.State.SLEEP:
                        if config.PRINT_STATE_CHANGES:
                            print("Button 2: Entering sleep mode")
                        self.current_state = config.State.SLEEP
                        if self.sleep_state:
                            self.sleep_state.reset()
        else:
            # No connection - set to safe defaults
            self.connected = False
            self.joy1_target = Vector2(0, 0)
            self.joy2_target = Vector2(0, 0)
    
    def update_control_smoothing(self):
        """Smooth control inputs"""
        # Lerp joystick values for smooth control
        smoothing_factor = 0.1
        
        self.joy1_current = lerp(self.joy1_current, self.joy1_target, smoothing_factor)
        self.joy2_current = lerp(self.joy2_current, self.joy2_target, smoothing_factor)
        
        # Smooth height changes
        self.distance_from_ground = lerp(
            self.distance_from_ground,
            self.target_distance_from_ground,
            0.05
        )
    
    def update_state(self):
        """Execute current state logic"""
        if self.current_state == config.State.INITIALIZE:
            self._state_initialize()
        
        elif self.current_state == config.State.STAND:
            self._state_stand()
        
        elif self.current_state == config.State.CAR:
            self._state_car()
        
        elif self.current_state == config.State.CALIBRATE:
            self._state_calibrate()
        
        elif self.current_state == config.State.SLEEP:
            self._state_sleep()
        
        elif self.current_state == config.State.SLAM_ATTACK:
            self._state_slam_attack()
    
    def _state_initialize(self):
        """Initialize state - just transition to stand"""
        self.current_state = config.State.STAND
    
    def _state_stand(self):
        """Standing state - using complete StandingState class"""
        if self.standing_state is None:
            return
        
        # Adjust height based on joy2_y
        if self.receiver and self.connected:
            height_adjustment = self.joy2_current.y * 30  # ±30mm
            self.target_distance_from_ground = config.DISTANCE_FROM_GROUND_BASE + height_adjustment
            self.standing_state.set_target_height(self.target_distance_from_ground)
        
        # Update standing state
        self.standing_state.update()
        
        # Transition to walking if joystick moved significantly
        if abs(self.joy1_current.x) > 0.1 or abs(self.joy1_current.y) > 0.1:
            if config.PRINT_STATE_CHANGES:
                print(f"Transitioning to CAR state (gait: {self.current_gait})")
            self.current_state = config.State.CAR
            # Reset walking state
            if self.walking_state:
                self.walking_state.reset()
    
    def _state_car(self):
        """Walking state - using complete WalkingState class"""
        if self.walking_state is None:
            return
        
        # If joystick centered, return to standing
        if abs(self.joy1_current.x) < 0.05 and abs(self.joy1_current.y) < 0.05:
            if config.PRINT_STATE_CHANGES:
                print("Transitioning to STAND state")
            self.current_state = config.State.STAND
            # Reset standing state
            if self.standing_state:
                self.standing_state.reset()
            return
        
        # Update movement direction and rotation from joysticks
        # RadioMaster Pocket mapping:
        # LEFT stick:  Y (Ch3/Throttle) = forward/back
        #              X (Ch4/Yaw) = rotation
        # RIGHT stick: X (Ch1/Aileron) = strafe left/right
        #              Y (Ch2/Elevator) = height adjustment
        translation = Vector2(self.joy2_current.x, self.joy1_current.y)  # strafe, forward/back
        rotation = self.joy1_current.x  # yaw rotation
        
        # Update walking state
        self.walking_state.update(translation, rotation)
    
    def _state_calibrate(self):
        """Calibration state - using complete CalibrationState class"""
        if self.calibration_state is None:
            return
        
        # Get RC offsets if available
        rc_offsets = None
        if self.receiver and self.connected:
            # Could get offset values from RC channels if implemented
            pass
        
        # Update calibration state
        complete = self.calibration_state.update(rc_offsets)
        
        if complete:
            # Print current offsets
            if self.loop_count % 50 == 0:  # Print every 50 loops
                self.calibration_state.print_current_offsets()
            
            # Could save offsets on button press
            # For now, auto-save when exiting calibration state
    
    def _state_sleep(self):
        """Sleep state - using complete SleepState class"""
        if self.sleep_state is None:
            return
        
        # Update sleep state
        sleeping = self.sleep_state.update()
        
        if sleeping:
            # Stay in sleep mode until joystick input or button press
            if self.receiver and self.connected:
                # Wake up if any significant input
                if (abs(self.joy1_current.x) > 0.2 or 
                    abs(self.joy1_current.y) > 0.2):
                    if config.PRINT_STATE_CHANGES:
                        print("Waking up from sleep...")
                    self.sleep_state.wake_up()
                    self.current_state = config.State.STAND
                    if self.standing_state:
                        self.standing_state.reset()
    
    def _state_slam_attack(self):
        """Slam attack - using complete AttacksState class"""
        if self.attacks_state is None:
            return
        
        # Execute slam attack
        self.attacks_state.slam_attack(attack_speed=25)
        
        # Return to standing after attack
        if config.PRINT_STATE_CHANGES:
            print("Attack complete - returning to STAND")
        self.current_state = config.State.STAND
        if self.standing_state:
            self.standing_state.reset()
    
    def loop(self):
        """Main control loop"""
        try:
            loop_interval = 1000 / config.MAIN_LOOP_FREQUENCY  # ms
            
            while True:
                loop_start = Timer.millis()
                
                # Update receiver inputs
                self.update_receiver()
                
                # Smooth control inputs
                self.update_control_smoothing()
                
                # Execute state machine
                self.update_state()
                
                # Statistics
                self.loop_count += 1
                if self.loop_count % 100 == 0:
                    loop_time = Timer.millis() - loop_start
                    if config.DEBUG_MODE:
                        print(f"Loop #{self.loop_count}: {loop_time}ms, "
                              f"State: {self.current_state}, "
                              f"Connected: {self.connected}")
                
                # Sleep to maintain loop frequency
                elapsed = Timer.millis() - loop_start
                sleep_time = max(0, loop_interval - elapsed) / 1000.0
                time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
            self.shutdown()
        
        except Exception as e:
            print(f"\nError in main loop: {e}")
            import traceback
            traceback.print_exc()
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all systems"""
        print("\n" + "=" * 50)
        print("Shutting down hexapod controller...")
        print("=" * 50)
        
        # Save any modified settings
        print("Saving configuration...")
        self.storage.save()
        
        # Cleanup servo controller
        print("Cleaning up servo controller...")
        self.servo_controller.cleanup()
        
        # Cleanup receiver
        if self.receiver:
            print("Cleaning up receiver...")
            self.receiver.cleanup()
        
        print("Shutdown complete")
        sys.exit(0)


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C)"""
    print("\nSignal received, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create controller
    controller = HexapodController()
    
    # Run setup
    controller.setup()
    
    # Run main loop
    print("\nStarting main control loop...")
    print("Press Ctrl+C to exit\n")
    controller.loop()


if __name__ == "__main__":
    main()
