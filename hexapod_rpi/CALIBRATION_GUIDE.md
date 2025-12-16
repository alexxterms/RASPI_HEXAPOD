# Servo Calibration Quick Guide

## 🎯 Physical Servo Alignment

### Why Calibration is Important
When you attach servo horns to servos, they need to be in the correct position. The calibration position puts all servos at known angles so you can visually align them.

---

## 🚀 Quick Start - Physical Alignment

### Step 1: Run Calibration Script
```bash
cd /path/to/hexapod_rpi
python3 calibrate_servos.py
```

This will:
1. Move all servos to a known calibration position
2. Hold them there while you align servo horns
3. Let you safely power off when done

---

## 📐 Calibration Position

At calibration position, **all legs should look identical**:

```
        Calibration Position
        (All legs same angles)
        
             Body
        ┌─────────────┐
        │             │
    ┌───┴───┐     ┌───┴───┐
    │ Coxa  │     │ Coxa  │  ← All pointing straight out
    └───┬───┘     └───┬───┘
        │ Femur       │ Femur  ← All at ~45° up
        ├───────      ├───────
        │ Tibia       │ Tibia  ← All at ~45° down
        └──○          └──○
        
  X: COXA + 43mm
  Y: 0mm
  Z: FEMUR + 185mm
```

**Expected appearance:**
- ✅ All coxa servos point straight out from body
- ✅ All femur servos at same upward angle (~45°)
- ✅ All tibia servos at same downward angle (~45°)

---

## 🔧 Alignment Procedure

### For Each Leg (0-5):

#### 1. Check Visual Alignment
Look at the leg - does it match the expected angles?

#### 2. If Servo Horn is Misaligned:
```
POWER OFF → Remove Horn → Rotate → Reattach → POWER ON
```

Detailed steps:
1. **IMPORTANT**: Detach/power off servos first!
2. Remove the servo horn screw
3. Lift off the servo horn
4. Rotate horn to correct position
5. Press horn back on
6. Secure with screw
7. Power on and verify

#### 3. If Angle is Slightly Off (but horn correct):
- Note: leg number (0-5)
- Note: joint (coxa/femur/tibia)  
- Note: how many degrees off
- **Don't adjust hardware** - you'll fix this with software offsets later

---

## 📋 Calibration Checklist

### Before Running:
- [ ] Raspberry Pi connected and powered
- [ ] PCA9685 boards connected via I2C
- [ ] All 18 servos connected to correct channels
- [ ] Servo power supply connected (6V)
- [ ] Servo horns **NOT** attached yet (or loose)

### During Calibration:
- [ ] Run `python3 calibrate_servos.py`
- [ ] Wait for servos to reach calibration position
- [ ] Check each leg visually
- [ ] Adjust servo horns as needed
- [ ] Verify all legs look identical

### After Physical Alignment:
- [ ] All servo horns properly attached
- [ ] All legs at same angles
- [ ] Note any legs that need software offset tweaks

---

## 🎮 Using the Calibration Script

### Interactive Menu:

```
Ready to move servos to calibration position? (y/n):
  → Type 'y' and press Enter

[Servos move to position...]

Press Enter when you're done aligning servo horns...
  → Align all servos, then press Enter

OPTIONS:
1. Keep servos powered (stay in position)
2. Detach servos (safe to handle)
3. Return to home position

Choose option (1/2/3):
  → 1: Keeps servos powered while you work
  → 2: Powers off servos (safe to manually move)
  → 3: Returns to home, then asks to power off
```

---

## 🔍 Troubleshooting

### Servo doesn't move
- Check servo is connected to correct channel
- Check servo power supply is on
- Check PCA9685 I2C connection

### Servo moves but wrong angle
- First align servo horn mechanically
- Then use software offset adjustment later

### Can't remove servo horn
- Make sure servos are powered OFF
- Use proper servo horn puller tool
- Don't force - gentle wiggling works

### All servos move to random positions
- Check COXA_LENGTH, FEMUR_LENGTH, TIBIA_LENGTH in config.py
- Verify these match your actual leg dimensions

---

## 📊 Leg & Joint Reference

```
Leg Layout (top view):
         Front
    0           1
         ┌─┐
   5    │ │    2
         └─┘
    4           3
         Back

Each leg has 3 joints:
  - Coxa (hip):   Rotates leg left/right
  - Femur (thigh): Lifts leg up/down  
  - Tibia (shin):  Extends/retracts foot
```

### Servo Channel Mapping:

| Leg | Coxa | Femur | Tibia | PCA9685 Board |
|-----|------|-------|-------|---------------|
| 0   | Ch0  | Ch1   | Ch2   | #1 (0x40)     |
| 1   | Ch3  | Ch4   | Ch5   | #1 (0x40)     |
| 2   | Ch6  | Ch7   | Ch8   | #1 (0x40)     |
| 3   | Ch9  | Ch10  | Ch11  | #1 (0x40)     |
| 4   | Ch12 | Ch13  | Ch14  | #1 (0x40)     |
| 5   | Ch0  | Ch1   | Ch2   | #2 (0x41)     |

---

## ⚡ Quick Commands

```bash
# Run calibration for physical alignment
python3 calibrate_servos.py

# Test individual state (after alignment)
python3 -m states.calibration

# Run main program with all features
python3 main.py
```

---

## 🎯 After Physical Alignment

Once servo horns are mechanically aligned:

### Fine-Tuning with Software Offsets

If a servo is 5° off after physical alignment:

1. Run main program: `python3 main.py`
2. Enter calibration mode (RC button or manually)
3. Adjust offset for that specific servo
4. Save offsets to storage

**Example offset adjustment:**
```python
# In calibration mode
cal_state.adjust_offset(leg=0, joint=1, delta=-5)  # Femur on leg 0, -5°
cal_state.save_offsets()  # Save permanently
```

---

## ✅ Success Criteria

You're done when:
- [ ] All 18 servos have horns attached
- [ ] In calibration position, all legs look identical
- [ ] No servo is visibly misaligned by more than 10°
- [ ] Servos move smoothly without binding
- [ ] You've noted any legs needing software offset tweaks

---

## 🎊 Ready to Walk!

After calibration:
1. ✅ Physical alignment complete
2. ⏭️ Fine-tune offsets if needed (software)
3. ⏭️ Test standing mode
4. ⏭️ Test walking with different gaits
5. ⏭️ Enjoy your hexapod! 🦿🦿🦿🦿🦿🦿
