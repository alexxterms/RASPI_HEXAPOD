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
# ELRS Receiver Configuration (CRSF Protocol)
# ============================================================================
# ELRS uses CRSF protocol at 420000 baud (not SBUS at 100000)
ELRS_MODE = 'CRSF'  # Using CRSF protocol with crsf_parser library

# Serial port for CRSF
ELRS_SERIAL_PORT = '/dev/serial0'  # Raspberry Pi UART
ELRS_BAUD_RATE = 420000            # CRSF standard baud rate

# Channel mapping for RadioMaster Pocket with ELRS
# Your actual channel mapping (verified from test_crsf_servo_control.py):
# Channel 16 (index 15): Roll → Strafe left/right
# Channel 15 (index 14): Pitch → Forward/backward  
# Channel 14 (index 13): Left stick up/down → Speed control
# Channel 13 (index 12): Yaw → Rotation
# Channel 7 (index 6): Height control
# Channel 9 (index 8): Calibration mode
# Channel 10 (index 9): Gait selector 1 (191=Gait0, 997=Gait1, 1792=Gait2)
# Channel 11 (index 10): Gait selector 2 (191=Gait3, 997=Gait4, 1792=Gait5)
# Channel 12 (index 11): Sleep mode

RC_CHANNEL_YAW = 12        # Channel 13 - Left stick left/right → Rotation
RC_CHANNEL_SPEED = 13      # Channel 14 - Left stick up/down → Speed control  
RC_CHANNEL_PITCH = 14      # Channel 15 - Right stick up/down → Forward/backward
RC_CHANNEL_ROLL = 15       # Channel 16 - Right stick left/right → Strafe
RC_CHANNEL_HEIGHT = 6      # Channel 7 - Height control
RC_CHANNEL_SLEEP = 7       # Channel 8 - Sleep mode toggle
RC_CHANNEL_GAIT = 9        # Channel 10 - Single gait selector (all 6 gaits)
RC_CHANNEL_CALIBRATION = 11 # Channel 12 - Calibration mode toggle

# CRSF channel value ranges (11-bit)
CRSF_MIN = 172
CRSF_MID = 992
CRSF_MAX = 1811

# Gait selector thresholds for single 6-position channel
# Channel 10 values: 443, 657, 871, 1086, 1300, 1514
GAIT_THRESHOLDS = [
    (443 - 100, 443 + 100, 0),  # Gait 1: value ~443 → index 0
    (871 - 100, 871 + 100, 1),  # Gait 2: value ~871 → index 1
    (1300 - 100, 1300 + 100, 2), # Gait 3: value ~1300 → index 2
    (1514 - 100, 1514 + 100, 3), # Gait 4: value ~1514 → index 3
    (1086 - 100, 1086 + 100, 4), # Gait 5: value ~1086 → index 4
    (657 - 100, 657 + 100, 5),   # Gait 6: value ~657 → index 5
]

# Channel value ranges (for backwards compatibility)
RC_MIN = 172   # CRSF minimum
RC_MID = 992   # CRSF middle
RC_MAX = 1811  # CRSF maximum
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
CONFIG_FILE_PATH = '/home/alexxterms/hexapod_config.json'  # Storage for offsets and calibration
LOG_FILE_PATH = '/home/alexxterms/hexapod.log'  # Log file

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
