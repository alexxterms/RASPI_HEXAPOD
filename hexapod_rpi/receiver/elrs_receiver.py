"""
ELRS (ExpressLRS) Receiver Interface
Supports both SBUS and PWM input modes
"""

import time
import serial
import sys
import os

# Add parent directory to path for imports when running standalone
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.helpers import Timer, map_float, constrain

# Try to import GPIO library (only available on Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available - PWM mode disabled")


class ELRSReceiver:
    """
    Interface for ELRS receiver
    Supports SBUS (serial) and PWM (individual channels) modes
    """
    
    def __init__(self, mode=None):
        """
        Initialize ELRS receiver
        
        Args:
            mode: 'SBUS' or 'PWM' (defaults to config.ELRS_MODE)
        """
        self.mode = mode or config.ELRS_MODE
        self.connected = False
        self.last_received_time = 0
        
        # Channel values (microseconds)
        self.channel_values = [config.RC_MID] * 8
        
        # Processed control data
        self.joy1_x = 0.0  # -1.0 to 1.0
        self.joy1_y = 0.0  # -1.0 to 1.0
        self.joy2_x = 0.0  # -1.0 to 1.0
        self.joy2_y = 0.0  # -1.0 to 1.0
        self.slider1 = 0.0  # 0.0 to 1.0
        self.slider2 = 0.0  # 0.0 to 1.0
        self.button1 = False
        self.button2 = False
        
        # Gait selection
        self.gait = 0
        
        # Initialize based on mode
        if self.mode == 'SBUS':
            self._init_sbus()
        elif self.mode == 'PWM':
            self._init_pwm()
        else:
            raise ValueError(f"Invalid ELRS mode: {self.mode}. Use 'SBUS' or 'PWM'")
    
    def _init_sbus(self):
        """Initialize SBUS serial communication"""
        try:
            # SBUS: 100000 baud, 8E2 (8 data bits, even parity, 2 stop bits), inverted
            self.serial_port = serial.Serial(
                port=config.ELRS_SBUS_SERIAL,
                baudrate=100000,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_TWO,
                timeout=0.01
            )
            print(f"SBUS initialized on {config.ELRS_SBUS_SERIAL}")
        except Exception as e:
            print(f"Error initializing SBUS: {e}")
            raise
    
    def _init_pwm(self):
        """Initialize PWM pin reading"""
        if not GPIO_AVAILABLE:
            print("Error: GPIO not available for PWM mode")
            return
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Setup pins for input
        for channel_name, pin in config.ELRS_PWM_PINS.items():
            GPIO.setup(pin, GPIO.IN)
        
        print(f"PWM mode initialized with {len(config.ELRS_PWM_PINS)} channels")
    
    def update(self):
        """
        Update receiver data
        Call this regularly in the main loop
        
        Returns:
            True if new data received, False otherwise
        """
        if self.mode == 'SBUS':
            return self._update_sbus()
        elif self.mode == 'PWM':
            return self._update_pwm()
        return False
    
    def _update_sbus(self):
        """Read and parse SBUS data"""
        try:
            # SBUS frame is 25 bytes
            if self.serial_port.in_waiting >= 25:
                data = self.serial_port.read(25)
                
                # Validate SBUS frame
                if data[0] == 0x0F and data[24] == 0x00:
                    # Parse 16 channels from SBUS data
                    channels = self._parse_sbus_frame(data)
                    
                    # Update channel values (convert from SBUS range to PWM microseconds)
                    for i in range(min(8, len(channels))):
                        # SBUS range: 172-1811 -> PWM range: 1000-2000μs
                        self.channel_values[i] = int(map_float(
                            channels[i], 172, 1811, 1000, 2000
                        ))
                    
                    self.last_received_time = Timer.millis()
                    self.connected = True
                    self._process_channels()
                    return True
        
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"SBUS read error: {e}")
        
        # Check for timeout
        if Timer.millis() - self.last_received_time > config.RC_TIMEOUT_MS:
            self.connected = False
        
        return False
    
    def _parse_sbus_frame(self, data):
        """
        Parse SBUS frame to extract channel data
        
        Args:
            data: 25-byte SBUS frame
        
        Returns:
            List of 16 channel values (11-bit, 0-2047)
        """
        channels = []
        
        # SBUS packs 16 11-bit channels into bytes 1-22
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
    
    def _update_pwm(self):
        """Read PWM values from GPIO pins (placeholder - requires hardware PWM library)"""
        # Note: Reading PWM on Raspberry Pi requires additional libraries
        # like pigpio or rpi_hardware_pwm for accurate timing
        # This is a placeholder implementation
        
        if not GPIO_AVAILABLE:
            return False
        
        # TODO: Implement PWM reading using pigpio or similar library
        # For now, this is a stub
        print("Warning: PWM reading not fully implemented")
        return False
    
    def _process_channels(self):
        """Process raw channel values into usable control data"""
        # Apply deadzone and normalize joystick values
        def apply_deadzone(value, center=config.RC_MID, deadzone=config.RC_DEADZONE):
            """Apply deadzone around center and normalize to -1.0 to 1.0"""
            if abs(value - center) < deadzone:
                return 0.0
            
            if value > center:
                return map_float(value, center + deadzone, config.RC_MAX, 0.0, 1.0)
            else:
                return map_float(value, config.RC_MIN, center - deadzone, -1.0, 0.0)
        
        # Process joysticks
        self.joy1_x = apply_deadzone(self.channel_values[config.RC_CHANNEL_JOY1_X])
        self.joy1_y = apply_deadzone(self.channel_values[config.RC_CHANNEL_JOY1_Y])
        self.joy2_x = apply_deadzone(self.channel_values[config.RC_CHANNEL_JOY2_X])
        self.joy2_y = apply_deadzone(self.channel_values[config.RC_CHANNEL_JOY2_Y])
        
        # Process sliders (0.0 to 1.0)
        self.slider1 = map_float(
            self.channel_values[config.RC_CHANNEL_SLIDER1],
            config.RC_MIN, config.RC_MAX, 0.0, 1.0
        )
        self.slider2 = map_float(
            self.channel_values[config.RC_CHANNEL_SLIDER2],
            config.RC_MIN, config.RC_MAX, 0.0, 1.0
        )
        
        # Process buttons (consider high position as pressed)
        self.button1 = self.channel_values[config.RC_CHANNEL_BUTTON1] > config.RC_MID
        self.button2 = self.channel_values[config.RC_CHANNEL_BUTTON2] > config.RC_MID
        
        # Map slider2 to gait selection (0-5)
        self.gait = int(constrain(self.slider2 * config.TOTAL_GAITS, 0, config.TOTAL_GAITS - 1))
        
        if config.DEBUG_MODE and config.PRINT_RC_VALUES:
            print(f"RC: J1({self.joy1_x:.2f},{self.joy1_y:.2f}) "
                  f"J2({self.joy2_x:.2f},{self.joy2_y:.2f}) "
                  f"S1:{self.slider1:.2f} Gait:{self.gait} "
                  f"Btn:{self.button1},{self.button2}")
    
    def is_connected(self):
        """
        Check if receiver is connected
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected
    
    def get_control_data(self):
        """
        Get processed control data as a dictionary
        
        Returns:
            Dictionary with all control values
        """
        return {
            'joy1_x': self.joy1_x,
            'joy1_y': self.joy1_y,
            'joy2_x': self.joy2_x,
            'joy2_y': self.joy2_y,
            'slider1': self.slider1,
            'slider2': self.slider2,
            'gait': self.gait,
            'button1': self.button1,
            'button2': self.button2,
            'connected': self.connected
        }
    
    def cleanup(self):
        """Clean up resources"""
        if self.mode == 'SBUS' and hasattr(self, 'serial_port'):
            self.serial_port.close()
            print("SBUS port closed")
        
        if self.mode == 'PWM' and GPIO_AVAILABLE:
            GPIO.cleanup()
            print("GPIO cleaned up")


# Test code
if __name__ == "__main__":
    """Test ELRS receiver (requires hardware)"""
    print("\n" + "="*70)
    print("ELRS RECEIVER TEST")
    print("="*70)
    print(f"Mode: {config.ELRS_MODE}")
    print(f"Serial Port: {config.ELRS_SBUS_SERIAL}")
    print()
    
    print("⚠️  HARDWARE REQUIREMENTS:")
    print("  - Raspberry Pi with UART enabled")
    print("  - ELRS receiver connected to GPIO 14 (UART TX)")
    print("  - Receiver powered and bound to transmitter")
    print()
    
    try:
        print("Initializing receiver...")
        receiver = ELRSReceiver()
        Timer.init()
        
        print("✓ Receiver initialized successfully!")
        print("\nReading receiver data for 10 seconds...")
        print("(Move sticks on your RadioMaster Pocket)")
        print("(Press Ctrl+C to stop)\n")
        print("-"*70)
        
        start_time = Timer.millis()
        update_count = 0
        
        while Timer.millis() - start_time < 10000:
            if receiver.update():
                update_count += 1
                data = receiver.get_control_data()
                
                # Print every 10th update to avoid spam
                if update_count % 10 == 0:
                    print(f"Connected: {data['connected']:5} | "
                          f"Joy1: ({data['joy1_x']:+.2f}, {data['joy1_y']:+.2f}) | "
                          f"Joy2: ({data['joy2_x']:+.2f}, {data['joy2_y']:+.2f}) | "
                          f"Gait: {data['gait']} | "
                          f"Btn: {data['button1']},{data['button2']}")
            
            time.sleep(0.02)  # 50Hz update rate
        
        print("-"*70)
        print(f"\n✓ Test complete! Received {update_count} updates")
        receiver.cleanup()
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        if 'receiver' in locals():
            receiver.cleanup()
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("  1. Are you running on a Raspberry Pi?")
        print("     (This test requires actual hardware)")
        print()
        print("  2. Is UART enabled on your Raspberry Pi?")
        print("     Run: sudo raspi-config")
        print("     → Interface Options → Serial Port")
        print("     → Disable login shell, Enable serial port hardware")
        print()
        print("  3. Is the ELRS receiver connected?")
        print(f"     GPIO 14 (UART TX) → {config.ELRS_SBUS_SERIAL}")
        print()
        print("  4. Is the receiver powered and bound?")
        print("     Check LED on receiver (should be solid or blinking)")
        print()
        print("  5. Check serial port permissions:")
        print("     sudo usermod -a -G dialout $USER")
        print("     (then logout and login again)")
        print()
        print("📚 For mock testing without hardware, see:")
        print("   - states/walking.py (has mock test)")
        print("   - states/standing.py (has mock test)")
        print("   - servo_controller.py (has mock test)")
        print()
        
        if 'receiver' in locals():
            try:
                receiver.cleanup()
            except:
                pass
