"""
Storage system for hexapod configuration
Replaces EEPROM with JSON file-based persistence
"""

import json
import os
import config


class HexapodStorage:
    """
    Handles persistent storage of hexapod configuration
    Replaces Arduino EEPROM with JSON file storage
    """
    
    def __init__(self, filepath=None):
        """
        Initialize storage system
        
        Args:
            filepath: Path to config file (defaults to config.CONFIG_FILE_PATH)
        """
        self.filepath = filepath or config.CONFIG_FILE_PATH
        self.data = self._load_or_create()
    
    def _load_or_create(self):
        """
        Load existing config or create default
        
        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                print(f"Configuration loaded from {self.filepath}")
                return data
            except Exception as e:
                print(f"Error loading config: {e}")
                print("Creating default configuration")
        
        # Create default configuration
        return self._create_default_config()
    
    def _create_default_config(self):
        """
        Create default configuration dictionary
        
        Returns:
            Default configuration
        """
        return {
            'version': '1.0',
            'offsets': [0] * 18,  # 18 servo offsets (3 per leg)
            'calibration': {
                'distance_from_center': config.DISTANCE_FROM_CENTER,
                'distance_from_ground': config.DISTANCE_FROM_GROUND_BASE,
                'lift_height': config.LIFT_HEIGHT,
                'land_height': config.LAND_HEIGHT
            },
            'settings': {
                'dynamic_stride_length': True,
                'default_gait': 0
            }
        }
    
    def save(self):
        """
        Save current configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(self.filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write to file with pretty formatting
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=2)
            
            print(f"Configuration saved to {self.filepath}")
            return True
        
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def save_offsets(self, offsets):
        """
        Save servo offset calibration values
        
        Args:
            offsets: List of 18 offset values (3 per leg)
        
        Returns:
            True if successful, False otherwise
        """
        if len(offsets) != 18:
            print(f"Error: Expected 18 offsets, got {len(offsets)}")
            return False
        
        self.data['offsets'] = offsets
        return self.save()
    
    def load_offsets(self):
        """
        Load servo offset calibration values
        
        Returns:
            List of 18 offset values
        """
        offsets = self.data.get('offsets', [0] * 18)
        
        # Ensure we have exactly 18 values
        if len(offsets) < 18:
            offsets.extend([0] * (18 - len(offsets)))
        elif len(offsets) > 18:
            offsets = offsets[:18]
        
        return offsets
    
    def save_calibration(self, calibration_data):
        """
        Save calibration parameters
        
        Args:
            calibration_data: Dictionary with calibration values
        
        Returns:
            True if successful, False otherwise
        """
        self.data['calibration'].update(calibration_data)
        return self.save()
    
    def load_calibration(self):
        """
        Load calibration parameters
        
        Returns:
            Dictionary with calibration values
        """
        return self.data.get('calibration', {})
    
    def save_settings(self, settings_data):
        """
        Save general settings
        
        Args:
            settings_data: Dictionary with setting values
        
        Returns:
            True if successful, False otherwise
        """
        self.data['settings'].update(settings_data)
        return self.save()
    
    def load_settings(self):
        """
        Load general settings
        
        Returns:
            Dictionary with setting values
        """
        return self.data.get('settings', {})
    
    def get_setting(self, key, default=None):
        """
        Get a specific setting value
        
        Args:
            key: Setting key
            default: Default value if key not found
        
        Returns:
            Setting value or default
        """
        return self.data.get('settings', {}).get(key, default)
    
    def set_setting(self, key, value):
        """
        Set a specific setting value and save
        
        Args:
            key: Setting key
            value: Setting value
        
        Returns:
            True if successful, False otherwise
        """
        if 'settings' not in self.data:
            self.data['settings'] = {}
        
        self.data['settings'][key] = value
        return self.save()
    
    def reset_to_defaults(self):
        """
        Reset all configuration to defaults
        
        Returns:
            True if successful, False otherwise
        """
        self.data = self._create_default_config()
        return self.save()
    
    def print_config(self):
        """Print current configuration"""
        print("\n=== Hexapod Configuration ===")
        print(f"Version: {self.data.get('version', 'unknown')}")
        
        print("\nServo Offsets:")
        offsets = self.data.get('offsets', [])
        for i in range(6):
            leg_offsets = offsets[i*3:(i+1)*3]
            print(f"  Leg {i}: {leg_offsets}")
        
        print("\nCalibration:")
        for key, value in self.data.get('calibration', {}).items():
            print(f"  {key}: {value}")
        
        print("\nSettings:")
        for key, value in self.data.get('settings', {}).items():
            print(f"  {key}: {value}")
        
        print("=" * 30)


# Test code
if __name__ == "__main__":
    """Test storage system"""
    print("Testing Hexapod Storage...")
    
    # Use a test file
    test_file = '/tmp/hexapod_test_config.json'
    
    # Create storage instance
    storage = HexapodStorage(test_file)
    
    print("\nTest 1: Load or create default config")
    storage.print_config()
    
    print("\nTest 2: Save custom offsets")
    test_offsets = [1, -2, 3, 0, 0, 0, 5, -5, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    storage.save_offsets(test_offsets)
    
    print("\nTest 3: Load offsets")
    loaded_offsets = storage.load_offsets()
    print(f"Loaded offsets: {loaded_offsets}")
    assert loaded_offsets == test_offsets, "Offsets don't match!"
    
    print("\nTest 4: Save calibration data")
    calibration = {
        'distance_from_center': 180.0,
        'lift_height': 140.0
    }
    storage.save_calibration(calibration)
    
    print("\nTest 5: Load calibration data")
    loaded_calibration = storage.load_calibration()
    print(f"Loaded calibration: {loaded_calibration}")
    
    print("\nTest 6: Save and load settings")
    storage.set_setting('dynamic_stride_length', False)
    storage.set_setting('default_gait', 2)
    print(f"Dynamic stride: {storage.get_setting('dynamic_stride_length')}")
    print(f"Default gait: {storage.get_setting('default_gait')}")
    
    print("\nTest 7: Print final config")
    storage.print_config()
    
    print("\nTest 8: Reset to defaults")
    storage.reset_to_defaults()
    storage.print_config()
    
    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\nTest file {test_file} removed")
    
    print("\nAll tests passed!")
