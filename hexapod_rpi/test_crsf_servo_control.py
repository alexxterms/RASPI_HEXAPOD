#!/usr/bin/env python3
"""
CRSF (ELRS) Receiver to Servo Control
Reads Channel 1 (Roll/Aileron) from RadioMaster ELRS receiver using CRSF protocol
and controls a servo motor position via PCA9685
"""

import sys
import os
import time
from typing import Container

# Add crsf_parser to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crsf_parser'))

from crsf_parser import CRSFParser, PacketValidationStatus
from crsf_parser.payloads import PacketsTypes
from serial import Serial
from adafruit_servokit import ServoKit


# ============================================================================
# Configuration
# ============================================================================
SERIAL_PORT = '/dev/serial0'  # Raspberry Pi UART serial port
BAUD_RATE = 420000            # CRSF uses 420000 baud (not 100000 like SBUS)

# PCA9685 Configuration
PCA_ADDRESS = 0x41            # Second board address (change to 0x40 for first)
SERVO_CHANNEL = 0             # Which servo channel to control (0-15)

# CRSF Channel Configuration
ROLL_CHANNEL = 0              # Channel 1 (Roll/Aileron) = index 0

# CRSF to Servo mapping
CRSF_MIN = 172                # CRSF minimum value (11-bit)
CRSF_MID = 992                # CRSF middle value
CRSF_MAX = 1811               # CRSF maximum value
SERVO_MIN = 0                 # Servo minimum angle (degrees)
SERVO_MAX = 180               # Servo maximum angle (degrees)

# Smoothing
SMOOTH_FACTOR = 0.3           # Lower = smoother but more lag (0.0-1.0)


# ============================================================================
# Helper Functions
# ============================================================================
def map_value(value, in_min, in_max, out_min, out_max):
    """Map a value from one range to another"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def constrain(value, min_val, max_val):
    """Constrain a value between min and max"""
    return max(min_val, min(max_val, value))


# ============================================================================
# Servo Controller Class
# ============================================================================
class ServoController:
    """Controls servo based on CRSF RC channels"""
    
    def __init__(self, kit, servo_channel, roll_channel):
        self.kit = kit
        self.servo_channel = servo_channel
        self.roll_channel = roll_channel
        self.current_angle = 90.0  # Start at center
        self.frame_count = 0
        self.last_update_time = time.time()
        self.last_channels = None
        
    def process_frame(self, frame: Container, status: PacketValidationStatus) -> None:
        """
        Callback function for CRSF parser
        Called whenever a valid frame is received
        """
        # Only process valid RC channel packets
        if status == PacketValidationStatus.VALID:
            if frame.header.type == PacketsTypes.RC_CHANNELS_PACKED:
                self._update_servo(frame)
        
        # Print errors for debugging
        elif status == PacketValidationStatus.CRC:
            if self.frame_count % 50 == 0:  # Don't spam console
                print("⚠ CRC Error detected")
        elif status == PacketValidationStatus.INVALID:
            if self.frame_count % 50 == 0:
                print("⚠ Invalid frame")
    
    def _update_servo(self, frame):
        """Update servo position based on RC channels"""
        try:
            # Extract channels from the frame
            channels = frame.payload.channels
            self.last_channels = channels
            self.frame_count += 1
            
            # Get roll channel value (11-bit CRSF range: 172-1811)
            roll_value = channels[self.roll_channel]
            
            # Map CRSF value to servo angle (0-180 degrees)
            target_angle = map_value(
                roll_value,
                CRSF_MIN, CRSF_MAX,
                SERVO_MIN, SERVO_MAX
            )
            
            # Constrain to valid servo range
            target_angle = constrain(target_angle, SERVO_MIN, SERVO_MAX)
            
            # Smooth the movement
            self.current_angle = (
                self.current_angle * (1 - SMOOTH_FACTOR) + 
                target_angle * SMOOTH_FACTOR
            )
            
            # Set servo position
            self.kit.servo[self.servo_channel].angle = self.current_angle
            
            # Print status every 25 frames (~0.5 seconds at 50Hz)
            if self.frame_count % 25 == 0:
                self._print_status(roll_value)
        
        except Exception as e:
            print(f"✗ Error updating servo: {e}")
    
    def _print_status(self, roll_value):
        """Print formatted status information"""
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        fps = 25 / elapsed if elapsed > 0 else 0
        self.last_update_time = current_time
        
        # Create channel display
        if self.last_channels and len(self.last_channels) >= 4:
            ch_display = (f"Ch1:{self.last_channels[0]:4d} Ch2:{self.last_channels[1]:4d} "
                         f"Ch3:{self.last_channels[2]:4d} Ch4:{self.last_channels[3]:4d}")
        else:
            ch_display = "No channel data"
        
        print(f"Roll: {roll_value:4d} → Servo: {self.current_angle:6.1f}° | "
              f"FPS: {fps:4.1f} | {ch_display}")


# ============================================================================
# Main Function
# ============================================================================
def main():
    """Main control loop"""
    print("=" * 70)
    print("CRSF (ELRS) Receiver to Servo Control")
    print("=" * 70)
    print(f"Serial Port:    {SERIAL_PORT} @ {BAUD_RATE} baud")
    print(f"PCA9685:        Address {hex(PCA_ADDRESS)}, Channel {SERVO_CHANNEL}")
    print(f"RC Channel:     {ROLL_CHANNEL + 1} (Roll/Aileron)")
    print(f"Smooth Factor:  {SMOOTH_FACTOR}")
    print("=" * 70)
    print()
    
    # Initialize PCA9685
    print("Initializing PCA9685 servo driver...")
    try:
        kit = ServoKit(channels=16, address=PCA_ADDRESS)
        # Center servo at startup
        kit.servo[SERVO_CHANNEL].angle = 90
        print("✓ PCA9685 initialized and servo centered")
    except Exception as e:
        print(f"✗ Error initializing PCA9685: {e}")
        print("\nTroubleshooting:")
        print("  1. Enable I2C: sudo raspi-config → Interface Options → I2C")
        print("  2. Check I2C connection: sudo i2cdetect -y 1")
        print(f"  3. Verify address {hex(PCA_ADDRESS)} appears in i2cdetect output")
        print("  4. Check wiring: SDA, SCL, VCC, GND")
        print("  5. Ensure external power supply is connected to PCA9685")
        return 1
    
    # Initialize servo controller
    servo_controller = ServoController(kit, SERVO_CHANNEL, ROLL_CHANNEL)
    
    # Initialize CRSF parser with servo controller callback
    crsf_parser = CRSFParser(servo_controller.process_frame)
    
    # Open serial port
    print(f"Opening serial port {SERIAL_PORT}...")
    try:
        ser = Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print("✓ Serial port opened")
    except Exception as e:
        print(f"✗ Error opening serial port: {e}")
        print("\nTroubleshooting:")
        print("  1. Enable UART: sudo raspi-config → Interface Options → Serial Port")
        print("  2. Disable serial console, enable hardware")
        print("  3. Check /boot/config.txt has: enable_uart=1")
        print("  4. Check /boot/cmdline.txt does NOT have console=serial0")
        print("  5. Verify ELRS receiver is connected to GPIO14/15")
        print("  6. Ensure receiver is powered and bound to transmitter")
        return 1
    
    print("\n" + "=" * 70)
    print("✓ Ready! Move the right stick LEFT/RIGHT to control the servo")
    print("  Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    # Main loop
    input_buffer = bytearray()
    try:
        while True:
            # Read available data from serial
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                input_buffer.extend(data)
                
                # Parse CRSF stream
                crsf_parser.parse_stream(input_buffer)
            
            # Small delay to prevent CPU overload
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("Stopping...")
        print("=" * 70)
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("\nCentering servo...")
        try:
            kit.servo[SERVO_CHANNEL].angle = 90
            time.sleep(0.5)
        except:
            pass
        
        print("Closing serial port...")
        ser.close()
        
        # Print statistics
        stats = crsf_parser.get_stats()
        print("\nSession Statistics:")
        print(f"  Valid frames:    {stats.valid_frames}")
        print(f"  Invalid frames:  {stats.invalid_frames}")
        print(f"  CRC errors:      {stats.crc_errors}")
        print(f"  Framing errors:  {stats.framing_errors}")
        print("\n✓ Done")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
