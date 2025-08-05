#!/bin/bash
# GenHook Server Installation Script for Ubuntu 22.04
set -e

echo "🚀 Installing GenHook on AWS EC2..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies
sudo apt install -y git curl nginx supervisor htop

# Create genhook user
sudo useradd -m -s /bin/bash genhook || true
sudo usermod -aG sudo genhook

# Create application directory
sudo mkdir -p /opt/genhook
sudo chown genhook:genhook /opt/genhook

# Switch to genhook user for application setup
sudo -u genhook bash << 'EOF'
cd /opt/genhook

# Clone repository (replace YOUR_USERNAME with your actual GitHub username)
git clone https://github.com/YOUR_USERNAME/GenHook.git . || git pull origin main

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Copy configuration files
cd backend
cp config/app-config.ini config/app-config.prod.ini
cp config/webhook-config.ini config/webhook-config.prod.ini

echo "✅ Application installed successfully"
EOF

echo "✅ GenHook installation complete!"
echo "Next: Configure /opt/genhook/backend/config/app-config.prod.ini"