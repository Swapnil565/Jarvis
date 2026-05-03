#!/bin/bash

# Deploy script for Railway Reservation System
# Run this on each EC2 instance

echo "Installing dependencies..."
sudo apt update
sudo apt install python3-pip -y
pip3 install flask requests

echo "Setup complete!"
echo ""
echo "Now run:"
echo "For Server 1: python3 app.py 1"
echo "For Server 2: python3 app.py 2"
echo "For Server 3: python3 app.py 3" 
