"""
Hexapod Configuration File
Hardware and constant definitions for Raspberry Pi Zero with dual PCA9685 controllers
"""

# ============================================================================
# PCA9685 Configuration
# ============================================================================
PCA9685_ADDRESS_1 = 0x40  # First PCA9685 board (Legs 1-5)
PCA9685_ADDRESS_2 = 0x41  # Second PCA9685 board (Leg 6)
PCA9685_FREQUENCY = 50    # 50Hz for analog servos

# ============================================================================
# Servo Channel Mapping (PCA9685 board and channel)
# Format: (board_address, channel)
# ============================================================================
SERVO_CHANNELS = {
    # Leg 1 (Front Right)
    'coxa1':  (PCA9685_ADDRESS_1, 0),
    'femur1': (PCA9685_ADDRESS_1, 1),
    'tibia1': (PCA9685_ADDRESS_1, 2),
    
    # Leg 2 (Middle Right)
    'coxa2':  (PCA9685_ADDRESS_1, 3),
    'femur2': (PCA9685_ADDRESS_1, 4),
    'tibia2': (PCA9685_ADDRESS_1, 5),
    
    # Leg 3 (Rear Right)
    'coxa3':  (PCA9685_ADDRESS_1, 6),
    'femur3': (PCA9685_ADDRESS_1, 7),
    'tibia3': (PCA9685_ADDRESS_1, 8),
    
    # Leg 4 (Rear Left)
    'coxa4':  (PCA9685_ADDRESS_1, 9),
    'femur4': (PCA9685_ADDRESS_1, 10),
    'tibia4': (PCA9685_ADDRESS_1, 11),
    
    # Leg 5 (Middle Left)
    'coxa5':  (PCA9685_ADDRESS_1, 12),
    'femur5': (PCA9685_ADDRESS_1, 13),
    'tibia5': (PCA9685_ADDRESS_1, 14),
    
    # Leg 6 (Front Left)
    'coxa6':  (PCA9685_ADDRESS_2, 0),
    'femur6': (PCA9685_ADDRESS_2, 1),
    'tibia6': (PCA9685_ADDRESS_2, 2),
}

# Servo index mapping for easier access
# Index order: coxa, femur, tibia for each leg
SERVO_INDEX_MAP = [
    'coxa1', 'femur1', 'tibia1',   # Leg 0
    'coxa2', 'femur2', 'tibia2',   # Leg 1
    'coxa3', 'femur3', 'tibia3',   # Leg 2
    'coxa4', 'femur4', 'tibia4',   # Leg 3
    'coxa5', 'femur5', 'tibia5',   # Leg 4
    'coxa6', 'femur6', 'tibia6',   # Leg 5
]

# ============================================================================
# Servo Pulse Width Configuration (microseconds)
# ============================================================================
SERVO_MIN_PULSE = 500   # Minimum pulse width in microseconds
SERVO_MAX_PULSE = 2500  # Maximum pulse width in microseconds

# ============================================================================
# Hexapod Leg Dimensions (from original code)
# ============================================================================
COXA_LENGTH = 46.0   # a1 - Coxa length in mm
FEMUR_LENGTH = 108.0 # a2 - Femur length in mm
TIBIA_LENGTH = 200.0 # a3 - Tibia length in mm
LEG_LENGTH = COXA_LENGTH + FEMUR_LENGTH + TIBIA_LENGTH  # Total leg length

# ============================================================================
# Hexapod Geometry
# ============================================================================
BASE_OFFSET = {'x': 90, 'y': 50, 'z': -10}  # Base servo offset angles
DISTANCE_FROM_CENTER = 173.0  # Default distance of feet from center
DISTANCE_FROM_GROUND_BASE = -60.0  # Base height offset

# Gait parameters
LIFT_HEIGHT = 130.0
LAND_HEIGHT = 70.0
STRIDE_OVERSHOOT = 10.0
LANDING_BUFFER = 15.0

# ============================================================================
# Movement Parameters
# ============================================================================
POINTS = 1000  # Number of points in movement cycles
STRIDE_MULTIPLIER = [1, 1, 1, -1, -1, -1]  # Per-leg stride multipliers
ROTATION_MULTIPLIER = [-1, 0, 1, -1, 0, 1]  # Per-leg rotation multipliers

# ============================================================================
# ELRS Receiver Configuration
# ============================================================================
# GPIO pins for ELRS receiver (adjust based on your wiring)
# If using SBUS: single pin for serial data
# If using PWM: multiple pins for each channel
ELRS_MODE = 'SBUS'  # 'SBUS' or 'PWM'

# For SBUS mode (serial communication)
ELRS_SBUS_PIN = 14  # GPIO14 (UART TX)
ELRS_SBUS_SERIAL = '/dev/serial0'  # Raspberry Pi serial port

# For PWM mode (individual channel pins)
ELRS_PWM_PINS = {
    'channel_1': 17,  # Roll
    'channel_2': 18,  # Pitch
    'channel_3': 27,  # Throttle
    'channel_4': 22,  # Yaw
    'channel_5': 23,  # Aux1
    'channel_6': 24,  # Aux2
    'channel_7': 25,  # Aux3
    'channel_8': 5,   # Aux4
}

# Channel mapping for RadioMaster Pocket (Standard AETR mode)
# Note: Channels are 0-indexed in code but 1-indexed in radio world
# RadioMaster Pocket has:
#   - Right stick: Aileron (Ch1/roll) and Elevator (Ch2/pitch)
#   - Left stick: Throttle (Ch3) and Rudder (Ch4/yaw)
#
# Standard AETR channel order:
# Ch 0 (Ch1): Aileron (Roll) - Right stick LEFT/RIGHT
# Ch 1 (Ch2): Elevator (Pitch) - Right stick UP/DOWN
# Ch 2 (Ch3): Throttle - Left stick UP/DOWN
# Ch 3 (Ch4): Rudder (Yaw) - Left stick LEFT/RIGHT

RC_CHANNEL_JOY1_X = 3      # Left stick X (Rudder/Yaw) - rotation
RC_CHANNEL_JOY1_Y = 2      # Left stick Y (Throttle) - forward/back
RC_CHANNEL_JOY2_X = 0      # Right stick X (Aileron/Roll) - strafe left/right
RC_CHANNEL_JOY2_Y = 1      # Right stick Y (Elevator/Pitch) - height adjustment
RC_CHANNEL_SLIDER1 = 4     # Ch5 - Speed control
RC_CHANNEL_SLIDER2 = 5     # Ch6 - Gait selector
RC_CHANNEL_BUTTON1 = 6     # Ch7 - Mode switch (calibration)
RC_CHANNEL_BUTTON2 = 7     # Ch8 - Additional function (sleep)

# Channel value ranges (standard PWM)
RC_MIN = 1000
RC_MID = 1500
RC_MAX = 2000
RC_DEADZONE = 50

# Timeout
RC_TIMEOUT_MS = 1000  # Consider disconnected after 1 second

# ============================================================================
# State Machine
# ============================================================================
class State:
    INITIALIZE = 'Initialize'
    STAND = 'Stand'
    CAR = 'Car'
    CRAB = 'Crab'
    CALIBRATE = 'Calibrate'
    SLAM_ATTACK = 'SlamAttack'
    SLEEP = 'Sleep'
    ATTACH = 'Attach'

class LegState:
    PROPELLING = 'Propelling'
    LIFTING = 'Lifting'
    STANDING = 'Standing'
    RESET = 'Reset'

class Gait:
    TRI = 0     # Tripod gait
    RIPPLE = 1  # Ripple gait
    WAVE = 2    # Wave gait
    QUAD = 3    # Quadruped gait
    BI = 4      # Bipod gait
    HOP = 5     # Hop gait

TOTAL_GAITS = 6
GAITS_LIST = [Gait.TRI, Gait.RIPPLE, Gait.WAVE, Gait.QUAD, Gait.BI, Gait.HOP]

# ============================================================================
# File Paths
# ============================================================================
CONFIG_FILE_PATH = '/home/pi/hexapod_config.json'  # Storage for offsets and calibration
LOG_FILE_PATH = '/home/pi/hexapod.log'  # Log file

# ============================================================================
# Performance Settings
# ============================================================================
MAIN_LOOP_FREQUENCY = 100  # Hz - main control loop frequency
SERVO_UPDATE_FREQUENCY = 50  # Hz - servo update frequency
RC_UPDATE_FREQUENCY = 50  # Hz - RC input read frequency

# ============================================================================
# Debug Settings
# ============================================================================
DEBUG_MODE = True
PRINT_SERVO_VALUES = False
PRINT_RC_VALUES = False
PRINT_STATE_CHANGES = True
