"""
CRSF (ELRS) Receiver for Hexapod Control
Uses the crsf_parser library to decode RadioMaster ELRS receiver signals
"""

import sys
import os
import time
from typing import Container

# Add crsf_parser to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'crsf_parser'))

from crsf_parser import CRSFParser, PacketValidationStatus
from crsf_parser.payloads import PacketsTypes
from serial import Serial


class CRSFReceiver:
    """
    CRSF protocol receiver for ELRS
    Parses CRSF frames and provides RC channel values
    """
    
    # CRSF Configuration
    SERIAL_PORT = '/dev/serial0'
    BAUD_RATE = 420000  # CRSF uses 420000 baud
    
    # CRSF value ranges (11-bit)
    CRSF_MIN = 172
    CRSF_MID = 992
    CRSF_MAX = 1811
    
    # Channel indices (0-based, your mapping)
    CH_YAW = 12          # Channel 13 - Left stick left/right → Rotation
    CH_SPEED = 13        # Channel 14 - Left stick up/down → Speed control
    CH_PITCH = 14        # Channel 15 - Right stick up/down → Forward/backward
    CH_ROLL = 15         # Channel 16 - Right stick left/right → Strafe
    CH_HEIGHT = 6        # Channel 7 - Height control
    CH_SLEEP = 7         # Channel 8 - Sleep mode toggle
    CH_GAIT = 9          # Channel 10 - Single gait selector (all 6 gaits)
    CH_CALIBRATION = 11  # Channel 12 - Calibration mode toggle
    
    # Gait selector thresholds (single channel with 6 positions)
    # Channel 10 values: 443, 657, 871, 1086, 1300, 1514
    GAIT_THRESHOLDS = [
        (343, 543, 0),    # Gait 1: value ~443 → index 0
        (771, 971, 1),    # Gait 2: value ~871 → index 1
        (1200, 1400, 2),  # Gait 3: value ~1300 → index 2
        (1414, 1614, 3),  # Gait 4: value ~1514 → index 3
        (986, 1186, 4),   # Gait 5: value ~1086 → index 4
        (557, 757, 5),    # Gait 6: value ~657 → index 5
    ]
    
    def __init__(self):
        """Initialize CRSF receiver"""
        self.serial = None
        self.parser = None
        self.input_buffer = bytearray()
        
        # Current channel values (CRSF range: 172-1811)
        self.channels = [self.CRSF_MID] * 16  # 16 channels
        
        # Processed control values
        self.joystick1_x = 0.0      # Left stick X (yaw/rotation) [-1.0 to 1.0]
        self.joystick1_y = 0.0      # Left stick Y (speed) [-1.0 to 1.0]
        self.joystick2_x = 0.0      # Right stick X (strafe) [-1.0 to 1.0]
        self.joystick2_y = 0.0      # Right stick Y (forward/back) [-1.0 to 1.0]
        self.height_control = 0.0   # Height [-1.0 to 1.0]
        self.speed_multiplier = 1.0 # Speed control [0.0 to 2.0]
        self.gait_index = 0         # Current gait (0-5)
        self.calibration_mode = False
        self.sleep_mode = False
        
        # Connection status
        self.connected = False
        self.last_frame_time = 0
        self.timeout_seconds = 1.0
        
        # Statistics
        self.frame_count = 0
        self.error_count = 0
        
    def connect(self):
        """
        Connect to ELRS receiver via serial port
        
        Returns:
            bool: True if connected successfully
        """
        try:
            # Open serial port
            self.serial = Serial(
                self.SERIAL_PORT,
                self.BAUD_RATE,
                timeout=0.01
            )
            
            # Create CRSF parser with callback
            self.parser = CRSFParser(self._frame_callback)
            
            self.connected = True
            self.last_frame_time = time.time()
            
            print(f"✓ CRSF Receiver connected to {self.SERIAL_PORT} @ {self.BAUD_RATE} baud")
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect to CRSF receiver: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from receiver"""
        if self.serial:
            try:
                self.serial.close()
            except:
                pass
            self.serial = None
        
        self.connected = False
        print("CRSF Receiver disconnected")
    
    def cleanup(self):
        """Cleanup receiver (alias for disconnect for compatibility with main.py)"""
        self.disconnect()
    
    def update(self):
        """
        Read and parse incoming CRSF data
        Call this regularly in your main loop
        
        Returns:
            bool: True if receiver is connected and receiving data
        """
        if not self.connected or not self.serial:
            return False
        
        try:
            # Read available data
            if self.serial.in_waiting > 0:
                data = self.serial.read(self.serial.in_waiting)
                self.input_buffer.extend(data)
                
                # Parse CRSF stream
                self.parser.parse_stream(self.input_buffer)
            
            # Check for timeout
            if time.time() - self.last_frame_time > self.timeout_seconds:
                if self.connected:
                    print("⚠ CRSF signal lost (timeout)")
                    self.connected = False
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Error reading CRSF data: {e}")
            self.error_count += 1
            return False
    
    def _frame_callback(self, frame: Container, status: PacketValidationStatus):
        """
        Callback function for CRSF parser
        Called whenever a frame is received
        """
        # Handle errors
        if status == PacketValidationStatus.CRC:
            self.error_count += 1
            return
        elif status == PacketValidationStatus.INVALID:
            self.error_count += 1
            return
        
        # Process valid RC channel packets
        if status == PacketValidationStatus.VALID:
            if frame.header.type == PacketsTypes.RC_CHANNELS_PACKED:
                self._process_channels(frame)
    
    def _process_channels(self, frame):
        """Process RC channels from CRSF frame"""
        try:
            # Extract channels
            self.channels = list(frame.payload.channels)
            self.frame_count += 1
            self.last_frame_time = time.time()
            
            if not self.connected:
                print("✓ CRSF signal acquired")
                self.connected = True
            
            # Convert channels to normalized values
            self._update_control_values()
            
        except Exception as e:
            print(f"✗ Error processing channels: {e}")
            self.error_count += 1
    
    def _update_control_values(self):
        """Convert raw channel values to control values"""
        # Joystick values (normalized to -1.0 to 1.0)
        self.joystick1_x = self._normalize_channel(self.channels[self.CH_YAW])      # Rotation
        self.joystick1_y = self._normalize_channel(self.channels[self.CH_PITCH])    # Forward/back
        self.joystick2_x = self._normalize_channel(self.channels[self.CH_ROLL])     # Strafe
        self.joystick2_y = self._normalize_channel(self.channels[self.CH_PITCH])   # Forward/backward
        
        # Speed control from left stick up/down (0.0 to 2.0, default 1.0)
        speed_normalized = self._normalize_channel(self.channels[self.CH_SPEED])
        self.speed_multiplier = (speed_normalized + 1.0)  # Map -1..1 to 0..2
        
        # Height control (normalized -1.0 to 1.0)
        self.height_control = self._normalize_channel(self.channels[self.CH_HEIGHT])
        
        # Gait selection (single channel with 6 positions on channel 10)
        # Values: 443, 657, 871, 1086, 1300, 1514 → Gaits 0-5
        gait_value = self.channels[self.CH_GAIT]
        self.gait_index = self._get_gait_from_value(gait_value)
        
        # Mode switches (treat as boolean: high = True)
        self.calibration_mode = self.channels[self.CH_CALIBRATION] > self.CRSF_MID
        self.sleep_mode = self.channels[self.CH_SLEEP] > self.CRSF_MID
    
    def _normalize_channel(self, value):
        """
        Normalize CRSF channel value to -1.0 to 1.0 range
        
        Args:
            value: CRSF channel value (172-1811)
        
        Returns:
            float: Normalized value (-1.0 to 1.0)
        """
        # Map CRSF range to -1.0 to 1.0
        normalized = (value - self.CRSF_MID) / (self.CRSF_MAX - self.CRSF_MID)
        
        # Constrain to valid range
        return max(-1.0, min(1.0, normalized))
    
    def _get_gait_from_value(self, value):
        """
        Convert single 6-position channel to gait index (0-5)
        
        Channel 10 values:
          - 443 → Gait 0
          - 871 → Gait 1
          - 1300 → Gait 2
          - 1514 → Gait 3
          - 1086 → Gait 4
          - 657 → Gait 5
        
        Args:
            value: CRSF channel value
        
        Returns:
            int: Gait index (0-5)
        """
        # Check each threshold range
        for min_val, max_val, gait_idx in self.GAIT_THRESHOLDS:
            if min_val <= value <= max_val:
                return gait_idx
        
        # Default to gait 0 if no match
        return 0
    
    def get_joystick1(self):
        """
        Get left stick values
        
        Returns:
            tuple: (x, y) where x is yaw/rotation, y is speed control
        """
        return (self.joystick1_x, self.speed_multiplier)
    
    def get_joystick2(self):
        """
        Get right stick values
        
        Returns:
            tuple: (x, y) where x is strafe, y is forward/back
        """
        return (self.joystick2_x, self.joystick1_y)  # Note: forward/back from left stick Y
    
    def get_speed_multiplier(self):
        """Get current speed multiplier (0.0 to 2.0)"""
        return self.speed_multiplier
    
    def get_height_control(self):
        """Get height control value (-1.0 to 1.0)"""
        return self.height_control
    
    def get_gait(self):
        """Get current gait index (0-5)"""
        return self.gait_index
    
    def is_calibration_mode(self):
        """Check if calibration mode is enabled"""
        return self.calibration_mode
    
    def is_sleep_mode(self):
        """Check if sleep mode is enabled"""
        return self.sleep_mode
    
    def is_connected(self):
        """Check if receiver is connected and receiving data"""
        return self.connected
    
    def get_stats(self):
        """
        Get receiver statistics
        
        Returns:
            dict: Statistics including frame count, errors, etc.
        """
        parser_stats = self.parser.get_stats() if self.parser else None
        
        return {
            'connected': self.connected,
            'frames_received': self.frame_count,
            'errors': self.error_count,
            'parser_valid': parser_stats.valid_frames if parser_stats else 0,
            'parser_crc_errors': parser_stats.crc_errors if parser_stats else 0,
            'parser_invalid': parser_stats.invalid_frames if parser_stats else 0,
        }
    
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
            'joy2_y': self.joystick1_y,      # Forward/back (right stick Y, but from Ch15/pitch)
            'gait': self.gait_index,         # Current gait (0-5)
            'button1': self.calibration_mode, # Calibration mode switch
            'button2': self.sleep_mode,       # Sleep mode switch
            'height': self.height_control,    # Height control
        }
    
    def print_status(self):
        """Print current receiver status and channel values"""
        if not self.connected:
            print("⚠ CRSF Receiver: DISCONNECTED")
            return
        
        print("\n" + "=" * 80)
        print("CRSF Receiver Status")
        print("=" * 80)
        
        # Control values
        print(f"Left Stick:   X={self.joystick1_x:+.2f} (Rotation)  Y={self.speed_multiplier:.2f} (Speed)")
        print(f"Right Stick:  X={self.joystick2_x:+.2f} (Strafe)    Y={self.joystick1_y:+.2f} (Fwd/Back)")
        print(f"Height:       {self.height_control:+.2f}")
        print(f"Gait:         {self.gait_index} ({['TRI', 'RIPPLE', 'WAVE', 'QUAD', 'BI', 'HOP'][self.gait_index]})")
        print(f"Calibration:  {'ON' if self.calibration_mode else 'OFF'}")
        print(f"Sleep:        {'ON' if self.sleep_mode else 'OFF'}")
        
        # Raw channel values (first 16 channels)
        print("\nRaw Channels:")
        for i in range(16):
            ch_num = i + 1
            value = self.channels[i]
            
            # Highlight special channels
            label = ""
            if i == self.CH_YAW:
                label = " (Yaw/Rotation)"
            elif i == self.CH_SPEED:
                label = " (Speed)"
            elif i == self.CH_PITCH:
                label = " (Forward/Back)"
            elif i == self.CH_ROLL:
                label = " (Strafe)"
            elif i == self.CH_HEIGHT:
                label = " (Height)"
            elif i == self.CH_CALIBRATION:
                label = " (Calibration)"
            elif i == self.CH_GAIT_1:
                label = " (Gait 0-2)"
            elif i == self.CH_GAIT_2:
                label = " (Gait 3-5)"
            elif i == self.CH_SLEEP:
                label = " (Sleep)"
            
            print(f"  Ch{ch_num:2d}: {value:4d}{label}")
        
        # Statistics
        stats = self.get_stats()
        print(f"\nStatistics:")
        print(f"  Frames:      {stats['frames_received']}")
        print(f"  Valid:       {stats['parser_valid']}")
        print(f"  CRC Errors:  {stats['parser_crc_errors']}")
        print(f"  Invalid:     {stats['parser_invalid']}")
        print("=" * 80)


# Test function
if __name__ == '__main__':
    print("CRSF Receiver Test")
    print("=" * 80)
    print("This will display RC channel values from your ELRS receiver")
    print("Press Ctrl+C to stop")
    print("=" * 80)
    
    receiver = CRSFReceiver()
    
    if not receiver.connect():
        print("Failed to connect to receiver")
        sys.exit(1)
    
    try:
        last_print = 0
        while True:
            receiver.update()
            
            # Print status every second
            if time.time() - last_print > 1.0:
                receiver.print_status()
                last_print = time.time()
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        receiver.disconnect()
        print("Done")
