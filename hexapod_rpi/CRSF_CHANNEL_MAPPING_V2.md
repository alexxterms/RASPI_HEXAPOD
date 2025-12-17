# CRSF Channel Mapping v2 - Single Gait Channel

## Updated Channel Assignments

### Movement Controls
| Channel | Name | Function | Range |
|---------|------|----------|-------|
| Ch16 (idx 15) | Right Stick X | **STRAFE** left/right | -1.0 to 1.0 |
| Ch15 (idx 14) | Right Stick Y | **FORWARD/BACKWARD** | -1.0 to 1.0 |
| Ch14 (idx 13) | Left Stick Y | **SPEED** control | 0.0 to 2.0 |
| Ch13 (idx 12) | Left Stick X | **ROTATION** | -1.0 to 1.0 |
| Ch7 (idx 6) | Aux Switch | **HEIGHT** control | -1.0 to 1.0 |

### Mode Controls
| Channel | Name | Function | Values |
|---------|------|----------|--------|
| Ch12 (idx 11) | Switch | **CALIBRATION** mode | OFF/ON |
| Ch8 (idx 7) | Switch | **SLEEP** mode | OFF/ON |

### Gait Selection - SINGLE 6-Position Channel
| Channel | Name | Function | Values → Gaits |
|---------|------|----------|----------------|
| Ch10 (idx 9) | 6-Pos Switch | **ALL GAITS** | See table below |

## Gait Channel Values (Channel 10)

| Position | Value | Range (±100) | Gait # | Gait Name |
|----------|-------|--------------|--------|-----------|
| 1 | **443** | 343-543 | 0 | Tripod |
| 2 | **871** | 771-971 | 1 | Ripple |
| 3 | **1300** | 1200-1400 | 2 | Wave |
| 4 | **1514** | 1414-1614 | 3 | Quad |
| 5 | **1086** | 986-1186 | 4 | Bi-pedal |
| 6 | **657** | 557-757 | 5 | Hop |

**Note:** The order is based on your physical switch positions. The code uses ranges (±100 from center value) to reliably detect each position.

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│                   RADIOMASTER POCKET                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LEFT STICK (Ch13/14):     RIGHT STICK (Ch15/16):          │
│  ┌───────────┐             ┌───────────┐                   │
│  │     ↑     │             │     ↑     │                   │
│  │   SPEED+  │             │  FORWARD  │                   │
│  │  (Ch14)   │             │  (Ch15)   │                   │
│  │           │             │           │                   │
│  │ ← YAW →  │             │ ← STRAFE →│                   │
│  │  (Ch13)   │             │  (Ch16)   │                   │
│  │     ↓     │             │     ↓     │                   │
│  │   SPEED-  │             │  BACKWARD │                   │
│  └───────────┘             └───────────┘                   │
│                                                             │
│  SWITCHES:                                                  │
│  ┌──────────────────────────────────────────────┐          │
│  │ Ch7:  Height Control (3-pos or knob)        │          │
│  │ Ch8:  Sleep Mode (2-pos switch)             │          │
│  │ Ch10: GAIT SELECTOR (6-pos switch!)         │          │
│  │       443=Gait0, 871=Gait1, 1300=Gait2      │          │
│  │       1514=Gait3, 1086=Gait4, 657=Gait5     │          │
│  │ Ch12: Calibration Mode (2-pos switch)       │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Control Scheme Details

### Movement
- **Right Stick Y (Ch15)** = Forward/Backward movement
- **Right Stick X (Ch16)** = Strafe left/right
- **Left Stick X (Ch13)** = Rotate in place
- **Left Stick Y (Ch14)** = Speed multiplier (center=1.0x, up=2.0x, down=0.0x)

### Height Control
- **Channel 7** = Body height adjustment
  - Up = Raise body
  - Down = Lower body
  - Center = Default height

### Gait Selection (Channel 10)
All 6 gaits on one channel with specific values:

```
Position 1 (443)  → Gait 0: TRIPOD    (fastest, most stable)
Position 2 (871)  → Gait 1: RIPPLE    (smooth, wave-like)
Position 3 (1300) → Gait 2: WAVE      (slow wave)
Position 4 (1514) → Gait 3: QUAD      (4-leg groups)
Position 5 (1086) → Gait 4: BI-PEDAL  (two legs)
Position 6 (657)  → Gait 5: HOP       (all legs together)
```

### Mode Switches
- **Channel 12 (Calibration)**: 
  - OFF (< 992) = Normal operation
  - ON (> 992) = Enter calibration mode for servo alignment

- **Channel 8 (Sleep)**:
  - OFF (< 992) = Active
  - ON (> 992) = Sleep mode (legs folded)

## Testing the New Mapping

### 1. Test Gait Channel
```bash
python3 test_crsf_receiver.py
```

Move the gait switch (Ch10) through all 6 positions and verify the output shows:
- Position 1: "Gait: 0 (TRIPOD)" when value ≈ 443
- Position 2: "Gait: 1 (RIPPLE)" when value ≈ 871
- Position 3: "Gait: 2 (WAVE)" when value ≈ 1300
- Position 4: "Gait: 3 (QUAD)" when value ≈ 1514
- Position 5: "Gait: 4 (BI)" when value ≈ 1086
- Position 6: "Gait: 5 (HOP)" when value ≈ 657

### 2. Verify Mode Switches
- Toggle Ch12 → Should see "Calibration: ON/OFF"
- Toggle Ch8 → Should see "Sleep: ON/OFF"

### 3. Test Movement
- Move right stick → Should see Forward/Strafe values change
- Move left stick X → Should see Rotation change
- Move left stick Y → Should see Speed multiplier change (0.0-2.0)

## CRSF Protocol Details

- **Baud Rate**: 420000 (CRSF standard)
- **Value Range**: 172 to 1811 (11-bit resolution)
- **Center Value**: 992
- **Update Rate**: ~150Hz typical
- **Serial Port**: `/dev/serial0`

## Implementation Notes

### Code Changes
1. **config.py**:
   - `RC_CHANNEL_GAIT = 9` (single gait channel on Ch10)
   - `RC_CHANNEL_CALIBRATION = 11` (moved to Ch12)
   - `RC_CHANNEL_SLEEP = 7` (moved to Ch8)
   - `GAIT_THRESHOLDS` array with 6 value ranges

2. **crsf_receiver.py**:
   - Single `_get_gait_from_value()` method
   - Checks channel value against 6 threshold ranges
   - Returns gait index 0-5 based on exact value matching

### Advantages
✅ All 6 gaits accessible from one switch
✅ No ambiguity - each position has unique value
✅ Calibration on dedicated channel (Ch12)
✅ Sleep mode on dedicated channel (Ch8)
✅ Simpler logic - no dual-channel coordination needed

### Calibration
If your gait switch values differ slightly from the expected values (443, 657, 871, 1086, 1300, 1514), you can adjust the ranges in `config.py`:

```python
GAIT_THRESHOLDS = [
    (your_value1 - 100, your_value1 + 100, 0),
    (your_value2 - 100, your_value2 + 100, 1),
    # ... etc
]
```

The ±100 range provides tolerance for minor variations.
