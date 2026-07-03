#!/bin/bash
# install.sh
# One-click installer for the Arduino Compilation Server on Ubuntu VPS.
# Run as root: curl -fsSL https://raw.githubusercontent.com/yourrepo/arduino-server/main/install.sh | sudo bash

set -e

# Define defaults
REPO_URL="https://github.com/yourrepo/arduino-server.git"
INSTALL_DIR="/opt/arduino-server"

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this script as root (using sudo)."
  exit 1
fi

echo "=================================================="
echo " Installing Arduino Compilation Server..."
echo "=================================================="

# 1. Install system dependencies
echo "Installing system dependencies (python3, pip, venv, curl, git)..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl git netfilter-persistent

# 2. Install Arduino CLI
echo "Installing Arduino CLI..."
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh
arduino-cli version

# 3. Clone repository
if [ -d "$INSTALL_DIR" ]; then
  echo "Directory $INSTALL_DIR already exists. Backing it up to ${INSTALL_DIR}_backup..."
  mv "$INSTALL_DIR" "${INSTALL_DIR}_backup_$(date +%s)"
fi

echo "Cloning server repository..."
git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 4. Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 5. Ensure relative config maps
cat > arduino-cli.yaml << EOF
directories:
  user: ./arduino_user
EOF

# 6. Pre-install Arduino core and libraries
echo "Installing Arduino core and libraries..."
./venv/bin/python -c "
import subprocess
cmd_prefix = ['arduino-cli', '--config-file', 'arduino-cli.yaml']
subprocess.run(cmd_prefix + ['core', 'update-index'], check=True)
subprocess.run(cmd_prefix + ['core', 'install', 'arduino:avr'], check=True)
subprocess.run(cmd_prefix + ['lib', 'update-index'], check=True)

libs = ['Servo', 'DHT sensor library', 'Adafruit NeoPixel', 'Adafruit SSD1306', 'Adafruit GFX Library', 'NewPing', 'RTClib', 'AccelStepper']
for lib in libs:
    print(f'Installing {lib}...')
    subprocess.run(cmd_prefix + ['lib', 'install', lib], check=True)
"

# 7. Configure permissions and users safely
RUN_USER="ubuntu"
if ! id -u "$RUN_USER" >/dev/null 2>&1; then
  # Fallback to the user who ran sudo, or root
  RUN_USER="${SUDO_USER:-root}"
fi
echo "Configuring owner permissions for user: $RUN_USER"
chown -R "$RUN_USER":"$RUN_USER" "$INSTALL_DIR"

# 8. Start with systemd (auto-restart on reboot)
echo "Registering systemd background daemon..."
cat > /etc/systemd/system/arduino-server.service << EOF
[Unit]
Description=Arduino Compilation Server
After=network.target

[Service]
User=$RUN_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python prod_server.py
Restart=always
RestartSec=3
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 9. Configure Firewalls (UFW / iptables)
echo "Configuring OS firewalls..."
# Allow in UFW if UFW is active
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  echo "UFW is active, allowing port 5000..."
  ufw allow 5000/tcp
fi

# Allow in iptables (necessary for Oracle Cloud VPS images)
if iptables -L INPUT -n --line-numbers | grep -q "reject-with icmp-host-prohibited"; then
  if ! iptables -L INPUT -n | grep -q "dpt:5000"; then
    echo "Adding port 5000 entry to iptables..."
    iptables -I INPUT 5 -p tcp --dport 5000 -m state --state NEW,ESTABLISHED -j ACCEPT
    if command -v netfilter-persistent >/dev/null; then
      netfilter-persistent save
    fi
  fi
fi

# 10. Enable and Start service
echo "Starting daemon service..."
systemctl daemon-reload
systemctl enable arduino-server.service
systemctl restart arduino-server.service

# Get Public IP
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "<your-vps-ip>")

echo ""
echo "=================================================="
echo "✓ Arduino Compilation Server is successfully running!"
echo "=================================================="
echo "Your Server URL: http://${PUBLIC_IP}:5000"
echo "Paste this URL in your IDE COMPILER SERVER panel."
echo "Check logs: sudo journalctl -u arduino-server.service -f"
echo "=================================================="
