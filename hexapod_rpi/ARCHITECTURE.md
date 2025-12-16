# System Architecture Diagram

## Hardware Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Raspberry Pi Zero W/2W                      │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   main.py    │──────│ kinematics.py│──────│servo_ctrl.py │ │
│  │  (Control)   │      │     (IK)     │      │  (PCA9685)   │ │
│  └──────────────┘      └──────────────┘      └──────┬───────┘ │
│         │                                            │         │
│         │ ┌────────────────────┐                    │         │
│         └─│ receiver/elrs.py   │                    │         │
│           │  (ELRS SBUS/PWM)   │                    │         │
│           └─────────┬──────────┘                    │         │
└─────────────────────┼───────────────────────────────┼─────────┘
                      │                               │
                GPIO 14                          I2C (GPIO 2,3)
                 (UART)                          (SDA, SCL)
                      │                               │
                      │                               ▼
              ┌───────▼──────┐           ┌────────────────────┐
              │ELRS Receiver │           │  PCA9685 Board #1  │
              │              │           │   Address: 0x40    │
              │  8 Channels  │           │                    │
              │  SBUS Output │           │  16 PWM Channels   │
              └──────────────┘           │  Ch 0-14: Legs 1-5 │
                                        └──────┬─────────────┘
                                               │
                                               │  I2C Bus
                                               │
                                        ┌──────▼─────────────┐
                                        │  PCA9685 Board #2  │
                                        │   Address: 0x41    │
                                        │                    │
                                        │  16 PWM Channels   │
                                        │  Ch 0-2: Leg 6     │
                                        └──────┬─────────────┘
                                               │
                    ┌──────────────────────────┴───────────────────────┐
                    │                                                  │
            ┌───────▼────────┐                              ┌─────────▼────────┐
            │  18 Servos     │                              │  Power Supply    │
            │  (6 legs × 3)  │◄─────────────────────────────│  5-6V, High Amp  │
            │                │                              │                  │
            │ Coxa, Femur,   │                              │  Separate from   │
            │ Tibia per leg  │                              │  Raspberry Pi    │
            └────────────────┘                              └──────────────────┘
```

## Software Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         main.py                                │
│                    (Main Control Loop)                         │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ State Machine│  │ RC Input     │  │ Control      │       │
│  │ • Initialize │  │ Processing   │  │ Smoothing    │       │
│  │ • Stand      │  │              │  │              │       │
│  │ • Walk       │  └──────┬───────┘  └──────────────┘       │
│  │ • Calibrate  │         │                                  │
│  │ • Sleep      │         │                                  │
│  └──────┬───────┘         │                                  │
└─────────┼─────────────────┼──────────────────────────────────┘
          │                 │
          │                 │
   ┌──────▼─────────────────▼────────┐
   │      HexapodKinematics          │
   │                                 │
   │  • move_to_pos(leg, Vector3)   │
   │  • Inverse kinematics          │
   │  • Servo offset calibration    │
   └──────────────┬──────────────────┘
                  │
   ┌──────────────▼──────────────────┐
   │   HexapodServoController        │
   │                                 │
   │  • PCA9685 I2C communication   │
   │  • Microsecond → PWM duty      │
   │  • 18 servo channel management │
   └──────────────┬──────────────────┘
                  │
       ┌──────────▼──────────┐
       │   PCA9685 Hardware  │
       │   (I2C Addresses)   │
       │   0x40 and 0x41     │
       └─────────────────────┘


┌────────────────────────────────────────┐
│         ELRSReceiver                   │
│                                        │
│  ┌──────────────┐  ┌──────────────┐  │
│  │ SBUS Mode    │  │  PWM Mode    │  │
│  │              │  │              │  │
│  │ • Serial RX  │  │ • GPIO pins  │  │
│  │ • Parse      │  │ • Pulse read │  │
│  │   frames     │  │              │  │
│  └──────────────┘  └──────────────┘  │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Processed Output:               │ │
│  │  • joy1_x, joy1_y (movement)    │ │
│  │  • joy2_x, joy2_y (height/side) │ │
│  │  • gait selection               │ │
│  │  • buttons                      │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘


┌────────────────────────────────────────┐
│         HexapodStorage                 │
│                                        │
│  JSON File: /home/pi/hexapod_config.json│
│                                        │
│  {                                     │
│    "offsets": [18 values],            │
│    "calibration": {...},              │
│    "settings": {...}                  │
│  }                                     │
└────────────────────────────────────────┘


┌────────────────────────────────────────┐
│         Utils Package                  │
│                                        │
│  ┌──────────────┐  ┌──────────────┐  │
│  │ vectors.py   │  │ helpers.py   │  │
│  │              │  │              │  │
│  │ • Vector2    │  │ • lerp()     │  │
│  │ • Vector3    │  │ • Bezier     │  │
│  │ • Math ops   │  │ • Timer      │  │
│  └──────────────┘  └──────────────┘  │
└────────────────────────────────────────┘
```

## Data Flow

```
RC Controller
      │
      ▼
ELRS Receiver ──SBUS──► Raspberry Pi GPIO 14
                              │
                              ▼
                      ELRSReceiver.update()
                              │
                              ▼
                      Parse channels, apply deadzone
                              │
                              ▼
                      joy1_x, joy1_y, gait, etc.
                              │
                              ▼
                      main.py: update_receiver()
                              │
                              ▼
                      Control smoothing (lerp)
                              │
                              ▼
                      State machine logic
                              │
                              ▼
              Calculate desired foot positions
                      (Vector3 per leg)
                              │
                              ▼
              kinematics.move_to_pos(leg, pos)
                              │
                              ▼
              Inverse kinematics calculation
              θ1 (coxa), θ2 (femur), θ3 (tibia)
                              │
                              ▼
              Convert angles → microseconds
                              │
                              ▼
              servo_controller.write_leg_servos()
                              │
                              ▼
              PCA9685 I2C commands
                              │
                              ▼
              PWM signals → Servos
                              │
                              ▼
                    Physical movement!
```

## State Machine Flow

```
    ┌──────────────┐
    │ INITIALIZE   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    STAND     │◄────────┐
    └──────┬───────┘         │
           │                 │
      joy1 moved?            │
           │                 │
           ▼                 │
    ┌──────────────┐         │
    │     CAR      │─────────┘
    │  (Walking)   │ joy1 centered
    └──────┬───────┘
           │
      button press?
           │
           ▼
    ┌──────────────┐
    │  CALIBRATE   │
    │   / SLEEP    │
    │  / ATTACK    │
    └──────────────┘
```

## File Dependencies

```
main.py
├── config.py
├── servo_controller.py
│   ├── config
│   └── adafruit_pca9685
├── kinematics.py
│   ├── config
│   ├── servo_controller
│   └── utils/
│       ├── vectors
│       └── helpers
├── receiver/elrs_receiver.py
│   ├── config
│   └── utils/helpers
├── storage.py
│   └── config
└── utils/
    ├── vectors.py
    └── helpers.py
        └── vectors
```

## Leg Numbering

```
        Front
         ┌─┐
    L1 ──┤ ├── L6
         │ │
    L2 ──┤ ├── L5
         │ │
    L3 ──┤ ├── L4
         └─┘
        Rear

Legs 1-3: Right side
Legs 4-6: Left side

Each leg: 3 servos
- Coxa (hip)
- Femur (thigh)
- Tibia (shin)
```

## Coordinate System

```
         +Z (up)
          │
          │
          └──────── +X (forward)
         ╱
        ╱
    +Y (left)

Origin: Center of hexapod body
Leg position: Vector3(x, y, z)
- x: Distance forward/back
- y: Distance left/right
- z: Height (negative = down)
```

---

This architecture provides a clear separation of concerns:
- **Hardware layer**: servo_controller.py, receiver/
- **Logic layer**: kinematics.py, main.py
- **Data layer**: storage.py
- **Utility layer**: utils/
