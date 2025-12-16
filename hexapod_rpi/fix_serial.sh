#!/bin/bash
#
# Fix stuck serial port - use this if you get "Invalid argument" error
# when trying to open the ELRS receiver serial port
#

echo "================================================================"
echo "  Serial Port Cleanup Utility"
echo "================================================================"
echo ""

SERIAL_PORT="/dev/serial0"
ALT_PORT="/dev/ttyAMA0"

echo "Checking for processes using serial ports..."
echo ""

# Check if any Python processes are using the serial port
PYTHON_PROCS=$(ps aux | grep python | grep -v grep | awk '{print $2}')

if [ ! -z "$PYTHON_PROCS" ]; then
    echo "Found Python processes:"
    ps aux | grep python | grep -v grep
    echo ""
    read -p "Kill these Python processes? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing Python processes..."
        killall python3 2>/dev/null
        killall python 2>/dev/null
        sleep 1
        echo "✓ Done"
    fi
else
    echo "No Python processes found"
fi

echo ""
echo "Checking specific serial port usage..."

# Check lsof if available
if command -v lsof &> /dev/null; then
    echo ""
    echo "Processes using $SERIAL_PORT:"
    sudo lsof $SERIAL_PORT 2>/dev/null || echo "  None"
    
    echo ""
    echo "Processes using $ALT_PORT:"
    sudo lsof $ALT_PORT 2>/dev/null || echo "  None"
else
    echo "  (lsof not installed - install with: sudo apt install lsof)"
fi

echo ""
echo "Checking serial port status..."
if [ -e "$SERIAL_PORT" ]; then
    ls -l $SERIAL_PORT
    echo "  Port exists ✓"
else
    echo "  ❌ $SERIAL_PORT does not exist!"
    echo "  Check UART is enabled in raspi-config"
fi

echo ""
echo "Checking user permissions..."
CURRENT_USER=$(whoami)
if groups $CURRENT_USER | grep -q dialout; then
    echo "  ✓ User '$CURRENT_USER' is in dialout group"
else
    echo "  ❌ User '$CURRENT_USER' is NOT in dialout group"
    echo "  Fix with: sudo usermod -a -G dialout $CURRENT_USER"
    echo "  (then logout and login again)"
fi

echo ""
echo "================================================================"
echo "  Quick Actions"
echo "================================================================"
echo ""
echo "If serial port is still stuck, try:"
echo ""
echo "  1. Force kill all Python:"
echo "     killall -9 python3"
echo ""
echo "  2. Reboot Raspberry Pi:"
echo "     sudo reboot"
echo ""
echo "  3. Check UART configuration:"
echo "     sudo raspi-config"
echo "     → Interface Options → Serial Port"
echo "     → Disable login shell"
echo "     → Enable serial hardware"
echo ""
echo "  4. Check kernel messages:"
echo "     dmesg | grep tty"
echo ""
echo "================================================================"
