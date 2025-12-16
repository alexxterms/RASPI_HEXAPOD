#!/bin/bash
# Hexapod Robot - Raspberry Pi Zero Setup Script
# Run this script on a fresh Raspberry Pi OS installation

set -e  # Exit on error

echo "=========================================="
echo "Hexapod Robot - Raspberry Pi Zero Setup"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-smbus \
    i2c-tools \
    git \
    libgpiod2

echo ""
echo "Step 3: Enabling I2C..."
sudo raspi-config nonint do_i2c 0

echo ""
echo "Step 4: Configuring serial for SBUS..."
# Disable serial console, enable serial port
sudo raspi-config nonint do_serial 1  # Disable console
sudo raspi-config nonint do_serial_hw 0  # Enable hardware

echo ""
echo "Step 5: Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo ""
echo "Step 6: Adding user to I2C and GPIO groups..."
sudo usermod -a -G gpio,i2c $USER

echo ""
echo "Step 7: Testing I2C connection..."
echo "Scanning for I2C devices (should see 0x40 and 0x41 if PCA9685 connected)..."
sudo i2cdetect -y 1

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. After reboot, verify I2C: sudo i2cdetect -y 1"
echo "3. Configure your settings in config.py"
echo "4. Test servos: python3 servo_controller.py"
echo "5. Run main program: python3 main.py"
echo ""
echo "Optional:"
echo "- Set up auto-start: See README.md"
echo "- Enable high priority: Run with 'sudo nice -n -20 python3 main.py'"
echo ""
echo "IMPORTANT: You must REBOOT for group changes to take effect!"
read -p "Reboot now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
