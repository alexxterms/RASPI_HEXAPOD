#!/usr/bin/env python3
"""
CRSF Channel Monitor - Diagnostic Tool
Displays all 16 RC channels in real-time to help debug receiver issues
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


# Configuration
SERIAL_PORT = '/dev/serial0'
BAUD_RATE = 420000


class ChannelMonitor:
    """Monitor and display all RC channels"""
    
    def __init__(self):
        self.frame_count = 0
        self.last_update_time = time.time()
        self.last_channels = [0] * 16
        
    def process_frame(self, frame: Container, status: PacketValidationStatus) -> None:
        """Callback for CRSF parser"""
        if status == PacketValidationStatus.VALID:
            if frame.header.type == PacketsTypes.RC_CHANNELS_PACKED:
                self.frame_count += 1
                self.last_channels = list(frame.payload.channels)
                
                # Print every 10 frames
                if self.frame_count % 10 == 0:
                    self._print_channels()
        
        elif status == PacketValidationStatus.CRC:
            print("⚠ CRC Error")
    
    def _print_channels(self):
        """Print all channels in a readable format"""
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        fps = 10 / elapsed if elapsed > 0 else 0
        self.last_update_time = current_time
        
        # Print in rows of 4 channels
        print(f"\n{'='*70}")
        print(f"Frame #{self.frame_count} | FPS: {fps:5.1f}")
        print(f"{'-'*70}")
        
        for i in range(0, 16, 4):
            ch_str = ""
            for j in range(4):
                ch_num = i + j + 1
                ch_val = self.last_channels[i + j]
                # Show percentage too
                pct = ((ch_val - 172) / (1811 - 172)) * 100 if ch_val > 0 else 0
                ch_str += f"Ch{ch_num:2d}: {ch_val:4d} ({pct:5.1f}%)  "
            print(ch_str)
        
        # Show min/mid/max reference
        print(f"{'-'*70}")
        print(f"Reference: MIN=172 (0%), MID=992 (50%), MAX=1811 (100%)")
        print(f"{'='*70}")


def main():
    print("=" * 70)
    print("CRSF Channel Monitor - Diagnostic Tool")
    print("=" * 70)
    print(f"Serial: {SERIAL_PORT} @ {BAUD_RATE} baud")
    print("=" * 70)
    print("\nThis will show ALL 16 channels from your receiver")
    print("Move your sticks and switches to verify receiver is working\n")
    print("Expected behavior:")
    print("  - All channels should be around 992 (50%) at center")
    print("  - Channels should change when you move sticks")
    print("  - Values should range from 172 (0%) to 1811 (100%)")
    print("\nPress Ctrl+C to stop\n")
    
    # Initialize monitor
    monitor = ChannelMonitor()
    parser = CRSFParser(monitor.process_frame)
    
    # Open serial
    try:
        ser = Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"✓ Serial port opened\n")
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    # Main loop
    input_buffer = bytearray()
    try:
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                input_buffer.extend(data)
                parser.parse_stream(input_buffer)
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        ser.close()
        stats = parser.get_stats()
        print("\nStatistics:")
        print(f"  Valid frames:    {stats.valid_frames}")
        print(f"  CRC errors:      {stats.crc_errors}")
        print(f"  Invalid frames:  {stats.invalid_frames}")
        print("\n✓ Done")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
