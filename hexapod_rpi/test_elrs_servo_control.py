#!/usr/bin/env python3
"""
ELRS Receiver to Servo Control
Reads Channel 1 (Roll/Aileron) from RadioMaster ELRS receiver
and controls a servo motor position via PCA9685
"""

import time
import serial
import sys
import os
from adafruit_servokit import ServoKit

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
SERIAL_PORT = '/dev/serial0'  # Raspberry Pi UART serial port
BAUD_RATE = 100000            # SBUS uses 100000 baud
TIMEOUT = 0.01                # 10ms timeout

# PCA9685 Configuration
PCA_ADDRESS = 0x41            # Second board address (change to 0x40 for first board)
SERVO_CHANNEL = 0             # Which servo channel to control (0-15)

# SBUS to Servo mapping
SBUS_MIN = 172                # SBUS minimum value
SBUS_MID = 992                # SBUS middle value
SBUS_MAX = 1811               # SBUS maximum value
SERVO_MIN = 0                 # Servo minimum angle (degrees)
SERVO_MAX = 180               # Servo maximum angle (degrees)

# Channel to read (0-indexed)
ROLL_CHANNEL = 0              # Channel 1 (Roll/Aileron) = index 0

# Smoothing
SMOOTH_FACTOR = 0.3           # Lower = smoother but more lag (0.0-1.0)


def map_value(value, in_min, in_max, out_min, out_max):
    """Map a value from one range to another"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def constrain(value, min_val, max_val):
    """Constrain a value between min and max"""
    return max(min_val, min(max_val, value))


class SBUSParser:
    """Parse SBUS protocol data from ELRS receiver"""
    
    def __init__(self, serial_port, baudrate=100000):
        """Initialize SBUS serial connection"""
        try:
            # SBUS: 100000 baud, 8E2 (8 data bits, even parity, 2 stop bits)
            self.serial = serial.Serial(
                port=serial_port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_TWO,
                timeout=TIMEOUT
            )
            print(f"✓ SBUS initialized on {serial_port}")
            self.connected = False
        except Exception as e:
            print(f"✗ Error opening serial port: {e}")
            raise
    
    def read_frame(self):
        """
        Read and parse one SBUS frame
        
        Returns:
            List of 16 channel values (0-2047) or None if invalid frame
        """
        try:
            # SBUS frame is 25 bytes
            if self.serial.in_waiting >= 25:
                data = self.serial.read(25)
                
                # Validate SBUS frame (start byte 0x0F, end byte 0x00)
                if len(data) == 25 and data[0] == 0x0F and data[24] == 0x00:
                    channels = self._parse_channels(data)
                    self.connected = True
                    return channels
                else:
                    # Invalid frame, flush buffer
                    self.serial.reset_input_buffer()
            
        except Exception as e:
            print(f"Read error: {e}")
            self.connected = False
        
        return None
    
    def _parse_channels(self, data):
        """
        Parse 16 channels from SBUS frame
        SBUS packs 16 11-bit channels into bytes 1-22
        
        Args:
            data: 25-byte SBUS frame
        
        Returns:
            List of 16 channel values (11-bit, 0-2047)
        """
        channels = []
        
        # Extract 16 11-bit channels from the data
        channels.append((data[1] | data[2] << 8) & 0x07FF)
        channels.append((data[2] >> 3 | data[3] << 5) & 0x07FF)
        channels.append((data[3] >> 6 | data[4] << 2 | data[5] << 10) & 0x07FF)
        channels.append((data[5] >> 1 | data[6] << 7) & 0x07FF)
        channels.append((data[6] >> 4 | data[7] << 4) & 0x07FF)
        channels.append((data[7] >> 7 | data[8] << 1 | data[9] << 9) & 0x07FF)
        channels.append((data[9] >> 2 | data[10] << 6) & 0x07FF)
        channels.append((data[10] >> 5 | data[11] << 3) & 0x07FF)
        channels.append((data[12] | data[13] << 8) & 0x07FF)
        channels.append((data[13] >> 3 | data[14] << 5) & 0x07FF)
        channels.append((data[14] >> 6 | data[15] << 2 | data[16] << 10) & 0x07FF)
        channels.append((data[16] >> 1 | data[17] << 7) & 0x07FF)
        channels.append((data[17] >> 4 | data[18] << 4) & 0x07FF)
        channels.append((data[18] >> 7 | data[19] << 1 | data[20] << 9) & 0x07FF)
        channels.append((data[20] >> 2 | data[21] << 6) & 0x07FF)
        channels.append((data[21] >> 5 | data[22] << 3) & 0x07FF)
        
        return channels
    
    def close(self):
        """Close serial connection"""
        if self.serial:
            self.serial.close()


def main():
    """Main control loop"""
    print("=" * 60)
    print("ELRS Receiver to Servo Control")
    print("=" * 60)
    print(f"Serial Port: {SERIAL_PORT}")
    print(f"PCA9685 Address: {hex(PCA_ADDRESS)}")
    print(f"Servo Channel: {SERVO_CHANNEL}")
    print(f"Reading Channel: {ROLL_CHANNEL + 1} (Roll/Aileron)")
    print("=" * 60)
    print("\nStarting... (Press Ctrl+C to stop)")
    print()
    
    # Initialize PCA9685
    try:
        kit = ServoKit(channels=16, address=PCA_ADDRESS)
        print("✓ PCA9685 servo driver initialized")
    except Exception as e:
        print(f"✗ Error initializing PCA9685: {e}")
        print("\nMake sure:")
        print("  1. I2C is enabled (sudo raspi-config)")
        print("  2. PCA9685 board is connected to I2C (SDA/SCL)")
        print("  3. Correct I2C address is set")
        return
    
    # Initialize SBUS parser
    try:
        sbus = SBUSParser(SERIAL_PORT, BAUD_RATE)
    except Exception as e:
        print(f"\n✗ Failed to initialize SBUS")
        print("\nMake sure:")
        print("  1. UART is enabled (sudo raspi-config)")
        print("  2. Serial console is disabled")
        print("  3. ELRS receiver is connected to GPIO14/15")
        print("  4. ELRS receiver is powered and bound to transmitter")
        return
    
    # Control variables
    current_angle = 90.0  # Start at center
    last_update_time = time.time()
    frame_count = 0
    
    try:
        while True:
            # Read SBUS frame
            channels = sbus.read_frame()
            
            if channels:
                frame_count += 1
                
                # Get roll channel value (SBUS range: 172-1811)
                roll_value = channels[ROLL_CHANNEL]
                
                # Map SBUS value to servo angle (0-180 degrees)
                target_angle = map_value(
                    roll_value,
                    SBUS_MIN, SBUS_MAX,
                    SERVO_MIN, SERVO_MAX
                )
                
                # Constrain to valid servo range
                target_angle = constrain(target_angle, SERVO_MIN, SERVO_MAX)
                
                # Smooth the movement
                current_angle = current_angle * (1 - SMOOTH_FACTOR) + target_angle * SMOOTH_FACTOR
                
                # Set servo position
                kit.servo[SERVO_CHANNEL].angle = current_angle
                
                # Print status every 20 frames (~0.4 seconds at 50Hz)
                if frame_count % 20 == 0:
                    # Calculate frame rate
                    current_time = time.time()
                    elapsed = current_time - last_update_time
                    fps = 20 / elapsed if elapsed > 0 else 0
                    last_update_time = current_time
                    
                    # Print formatted status
                    print(f"Ch{ROLL_CHANNEL + 1}: {roll_value:4d} → Servo: {current_angle:6.1f}° | "
                          f"FPS: {fps:4.1f} | {'✓ Connected' if sbus.connected else '✗ No signal'}")
            
            # Small delay to prevent CPU overload
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Stopping...")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        # Clean up
        print("\nCentering servo...")
        kit.servo[SERVO_CHANNEL].angle = 90
        sbus.close()
        print("✓ Done")


if __name__ == '__main__':
    main()
