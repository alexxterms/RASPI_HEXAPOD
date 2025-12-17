#!/usr/bin/env python3
"""
Test CRSF Receiver - Display all channels and processed values
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from receiver.crsf_receiver import CRSFReceiver


def main():
    print("=" * 80)
    print("CRSF Receiver Test for Hexapod")
    print("=" * 80)
    print()
    print("This test will display:")
    print("  - All 16 CRSF channel values")
    print("  - Processed control values (joysticks, speed, gait, modes)")
    print("  - Connection status and statistics")
    print()
    print("Move your sticks and switches to verify correct channel mapping!")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)
    
    # Create receiver
    receiver = CRSFReceiver()
    
    # Connect to ELRS
    if not receiver.connect():
        print("\n✗ Failed to connect to CRSF receiver")
        print("\nTroubleshooting:")
        print("  1. Enable UART: sudo raspi-config → Interface Options → Serial Port")
        print("  2. Disable serial console, enable hardware")
        print("  3. Add to /boot/config.txt: enable_uart=1")
        print("  4. Remove console=serial0 from /boot/cmdline.txt")
        print("  5. Verify ELRS receiver TX → GPIO15 (Pin 10)")
        print("  6. Ensure receiver is powered and bound")
        print("  7. Check baud rate is 420000 (CRSF), not 100000 (SBUS)")
        return 1
    
    print("\n✓ Connected! Waiting for signal...")
    print()
    
    try:
        last_print = 0
        frames_at_last_print = 0
        
        while True:
            # Update receiver (read and parse data)
            receiver.update()
            
            # Print status every 0.5 seconds
            if time.time() - last_print >= 0.5:
                # Calculate frame rate
                frames = receiver.frame_count
                fps = (frames - frames_at_last_print) / 0.5
                frames_at_last_print = frames
                
                # Clear screen (for cleaner display)
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("=" * 80)
                print("CRSF Receiver - Hexapod Channel Mapping Test")
                print("=" * 80)
                
                if not receiver.is_connected():
                    print("\n⚠ NO SIGNAL - Waiting for receiver...")
                    print("   Check transmitter is on and bound to receiver")
                else:
                    print(f"\n✓ Connected - Receiving at {fps:.1f} FPS")
                    
                    # Get control values
                    joy1_x, speed = receiver.get_joystick1()
                    joy2_x, joy1_y = receiver.get_joystick2()
                    height = receiver.get_height_control()
                    gait = receiver.get_gait()
                    cal_mode = receiver.is_calibration_mode()
                    sleep_mode = receiver.is_sleep_mode()
                    
                    print("\n" + "-" * 80)
                    print("CONTROL VALUES (Processed)")
                    print("-" * 80)
                    print(f"Left Stick X (Yaw):       {joy1_x:+.2f}  (Rotation)")
                    print(f"Left Stick Y (Speed):     {speed:.2f}   (Speed multiplier 0.0-2.0)")
                    print(f"Right Stick X (Roll):     {joy2_x:+.2f}  (Strafe left/right)")
                    print(f"Right Stick Y (Pitch):    {joy1_y:+.2f}  (Forward/backward)")
                    print(f"Height Control (Ch7):     {height:+.2f}")
                    
                    gait_names = ['TRI', 'RIPPLE', 'WAVE', 'QUAD', 'BI', 'HOP']
                    print(f"Gait (Ch10/11):           {gait} - {gait_names[gait]}")
                    print(f"Calibration Mode (Ch9):   {'ON' if cal_mode else 'OFF'}")
                    print(f"Sleep Mode (Ch12):        {'ON' if sleep_mode else 'OFF'}")
                    
                    print("\n" + "-" * 80)
                    print("RAW CHANNEL VALUES (CRSF 172-1811, center=992)")
                    print("-" * 80)
                    
                    # Display channels in 4 columns
                    for row in range(4):
                        line = ""
                        for col in range(4):
                            ch_idx = row * 4 + col
                            if ch_idx < 16:
                                ch_num = ch_idx + 1
                                value = receiver.channels[ch_idx]
                                
                                # Highlight special channels
                                if ch_idx == 12:
                                    marker = "←YAW"
                                elif ch_idx == 13:
                                    marker = "←SPEED"
                                elif ch_idx == 14:
                                    marker = "←PITCH"
                                elif ch_idx == 15:
                                    marker = "←ROLL"
                                elif ch_idx == 6:
                                    marker = "←HEIGHT"
                                elif ch_idx == 8:
                                    marker = "←CAL"
                                elif ch_idx == 9:
                                    marker = "←GAIT1"
                                elif ch_idx == 10:
                                    marker = "←GAIT2"
                                elif ch_idx == 11:
                                    marker = "←SLEEP"
                                else:
                                    marker = ""
                                
                                line += f"Ch{ch_num:2d}:{value:4d} {marker:8s}  "
                        print(line)
                    
                    # Statistics
                    stats = receiver.get_stats()
                    print("\n" + "-" * 80)
                    print("STATISTICS")
                    print("-" * 80)
                    print(f"Valid Frames:   {stats['parser_valid']:6d}")
                    print(f"CRC Errors:     {stats['parser_crc_errors']:6d}")
                    print(f"Invalid Frames: {stats['parser_invalid']:6d}")
                    
                    print("\n" + "=" * 80)
                    print("Press Ctrl+C to stop")
                    print("=" * 80)
                
                last_print = time.time()
            
            # Small delay
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Stopping...")
        print("=" * 80)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        receiver.disconnect()
        
        # Print final statistics
        stats = receiver.get_stats()
        print("\nFinal Statistics:")
        print(f"  Total frames received: {stats['frames_received']}")
        print(f"  Valid frames:          {stats['parser_valid']}")
        print(f"  CRC errors:            {stats['parser_crc_errors']}")
        print(f"  Invalid frames:        {stats['parser_invalid']}")
        print("\n✓ Test complete")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
