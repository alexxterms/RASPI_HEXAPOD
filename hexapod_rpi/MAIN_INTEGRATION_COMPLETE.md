# Main.py Integration with CRSF Receiver - COMPLETE

## Changes Made

### 1. Updated Receiver Import
**File**: `main.py`

**Old**:
```python
from receiver.elrs_receiver import ELRSReceiver
```

**New**:
```python
from receiver.crsf_receiver import CRSFReceiver
```

### 2. Updated Receiver Instantiation
**Old**:
```python
self.receiver = ELRSReceiver()
```

**New**:
```python
self.receiver = CRSFReceiver()
```

### 3. Fixed StandingState Constructor
**File**: `main.py` line ~113

**Old** (3 arguments - ERROR):
```python
self.standing_state = StandingState(
    self.kinematics,
    current_points,
    self.distance_from_ground  # ❌ This parameter doesn't exist!
)
```

**New** (2 arguments - CORRECT):
```python
self.standing_state = StandingState(
    self.kinematics,
    current_points
)
```

### 4. Added get_control_data() to CRSF Receiver
**File**: `receiver/crsf_receiver.py`

Added new method to maintain compatibility with `main.py`:

```python
def get_control_data(self):
    """
    Get all control data in a single dictionary
    Compatible with main.py expected format
    
    Returns:
        dict: All control values
    """
    return {
        'connected': self.connected,
        'joy1_x': self.joystick1_x,      # Rotation (left stick X)
        'joy1_y': self.speed_multiplier, # Speed (left stick Y converted to 0-2 range)
        'joy2_x': self.joystick2_x,      # Strafe (right stick X)
        'joy2_y': self.joystick1_y,      # Forward/back (right stick Y)
        'gait': self.gait_index,         # Current gait (0-5)
        'button1': self.calibration_mode, # Calibration mode switch
        'button2': self.sleep_mode,       # Sleep mode switch
        'height': self.height_control,    # Height control
    }
```

## API Compatibility

The CRSF receiver now provides the **exact same interface** as the old ELRS receiver:

### Methods Used by main.py:
1. ✅ `receiver.update()` - Read new data
2. ✅ `receiver.get_control_data()` - Get all control values

### Data Format:
```python
data = {
    'connected': bool,      # Connection status
    'joy1_x': float,        # -1.0 to 1.0 (rotation)
    'joy1_y': float,        # 0.0 to 2.0 (speed multiplier)
    'joy2_x': float,        # -1.0 to 1.0 (strafe)
    'joy2_y': float,        # -1.0 to 1.0 (forward/back)
    'gait': int,            # 0-5 (gait index)
    'button1': bool,        # Calibration mode
    'button2': bool,        # Sleep mode
    'height': float,        # -1.0 to 1.0 (height control)
}
```

## Testing

The integration is now complete. Run the main program:

```bash
cd /home/ali/Documents/Aecerts_Hexapod_V1/hexapod_rpi
python3 main.py
```

### Expected Initialization:
```
==================================================
Hexapod Robot Controller - Raspberry Pi Zero
==================================================

Initializing storage...
Initializing servo controller...
✓ PCA9685 initialized

Initializing kinematics...
✓ Kinematics initialized

Initializing ELRS receiver...
✓ CRSF Receiver connected to /dev/serial0 @ 420000 baud

==================================================
Initialization complete!
==================================================

Attaching servos...
✓ All servos attached

Moving to initial position...
Initializing state objects...
✓ States initialized

Setup complete - entering standing state
```

## State Machine Flow

With the CRSF receiver integrated, the hexapod will:

1. **Start in STANDING state** - All legs in neutral position
2. **Monitor receiver** for control inputs:
   - **Left stick** → Rotation + Speed control
   - **Right stick** → Forward/back + Strafe
   - **Channel 7** → Height adjustment
   - **Channel 9** → Calibration mode
   - **Channel 10/11** → Gait selection (0-5)
   - **Channel 12** → Sleep mode

3. **Transition states** based on inputs:
   - Move sticks → Enter WALKING state
   - Ch9 switch → Enter CALIBRATION state
   - Ch12 switch → Enter SLEEP state
   - Stop input → Return to STANDING state

## Channel Mapping Summary

| Channel | Index | Control | Usage |
|---------|-------|---------|-------|
| 16 | 15 | Right Stick X | Strafe left/right |
| 15 | 14 | Right Stick Y | Forward/backward |
| 14 | 13 | Left Stick Y | Speed (0.0-2.0) |
| 13 | 12 | Left Stick X | Rotation/yaw |
| 7 | 6 | Aux Switch | Height control |
| 9 | 8 | Switch | Calibration mode |
| 10 | 9 | 3-Pos Switch | Gaits 0-2 |
| 11 | 10 | 3-Pos Switch | Gaits 3-5 |
| 12 | 11 | Switch | Sleep mode |

## All Issues Resolved

✅ **CRSF receiver integrated** - Uses working crsf_parser library
✅ **StandingState fixed** - Correct number of arguments
✅ **API compatibility** - get_control_data() method added
✅ **No syntax errors** - main.py passes validation
✅ **Channel mapping** - Matches your verified test configuration

The hexapod is now ready to run!
