#!/bin/bash
set -euo pipefail

###############################################################################
# Oracle Cloud Always Free Tier - ERPNext + Inventory System Setup
#
# Prerequisites:
#   - Oracle Cloud account with Always Free VM provisioned
#   - Ubuntu 22.04/24.04 ARM64 (Ampere A1) instance
#   - Recommended: 4 OCPU, 24GB RAM, 100GB boot volume
#   - SSH access to the instance
#
# Usage:
#   scp setup-oracle-cloud.sh ubuntu@<your-vm-ip>:~/
#   ssh ubuntu@<your-vm-ip>
#   chmod +x setup-oracle-cloud.sh
#   ./setup-oracle-cloud.sh
###############################################################################

echo "========================================="
echo " Oracle Cloud ERPNext Setup"
echo "========================================="

# --- Step 1: System Updates ---
echo "[1/6] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# --- Step 2: Install Docker ---
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in for group changes."
else
    echo "Docker already installed."
fi

# Ensure docker compose plugin
sudo apt-get install -y docker-compose-plugin 2>/dev/null || true

# --- Step 3: Open Firewall Ports ---
echo "[3/6] Configuring firewall (iptables)..."
# Oracle Cloud uses iptables, not ufw by default
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT  # ERPNext
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT  # Inventory API
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 3000 -j ACCEPT  # Inventory Frontend
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT    # HTTP
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT   # HTTPS
sudo netfilter-persistent save 2>/dev/null || sudo sh -c "iptables-save > /etc/iptables/rules.v4"

echo ""
echo "IMPORTANT: Also open these ports in Oracle Cloud Console:"
echo "  Networking > Virtual Cloud Networks > Your VCN > Security Lists > Default"
echo "  Add Ingress Rules for TCP ports: 80, 443, 3000, 8000, 8080"

# --- Step 4: Create Project Directory ---
echo "[4/6] Setting up project directories..."
mkdir -p ~/inventory-system/{erpnext,app}

# --- Step 5: Deploy ERPNext ---
echo "[5/6] Setting up ERPNext..."
if [ ! -f ~/inventory-system/erpnext/docker-compose.yml ]; then
    echo "Please copy deployment/erpnext/docker-compose.yml and .env to ~/inventory-system/erpnext/"
    echo "Then run: cd ~/inventory-system/erpnext && docker compose up -d"
else
    cd ~/inventory-system/erpnext
    echo "Starting ERPNext (this takes 3-5 minutes on first run)..."
    docker compose up -d
    echo "Waiting for ERPNext site creation..."
    sleep 30
    echo "ERPNext should be available at http://<your-vm-ip>:8080"
    echo "Default login: Administrator / (your ADMIN_PASSWORD from .env)"
fi

# --- Step 6: Generate ERPNext API Keys ---
echo "[6/6] Post-setup instructions..."
cat << 'INSTRUCTIONS'

=========================================
 SETUP COMPLETE - Next Steps
=========================================

1. ACCESS ERPNEXT:
   Open http://<your-vm-ip>:8080
   Login: Administrator / <your admin password>

2. GENERATE API KEYS (required for inventory system):
   - Go to: Settings > User > Administrator
   - Scroll to "API Access" section
   - Click "Generate Keys"
   - Copy the API Key and API Secret
   - Save these in your inventory system .env file

3. CONFIGURE ERPNEXT FOR INVENTORY:
   a) Create a Warehouse:
      Stock > Warehouse > Add: "Stores - <Company>"

   b) Add Items with Barcodes:
      Stock > Item > New Item
      - Set item name, group, unit
      - Under "Barcodes" section, add EAN-13/UPC-A barcode
      - Set standard selling rate and reorder level

   c) Create a Supplier:
      Buying > Supplier > New

4. DEPLOY INVENTORY SYSTEM:
   cd ~/inventory-system/app
   # Copy the inventory-system backend/ and frontend/ here
   # Copy docker-compose.yml and .env
   # Update .env with:
   #   ERPNEXT_URL=http://<your-vm-ip>:8080
   #   ERPNEXT_API_KEY=<from step 2>
   #   ERPNEXT_API_SECRET=<from step 2>
   docker compose up -d

5. ORACLE CLOUD SECURITY RULES (if not done):
   - Go to Oracle Cloud Console
   - Networking > Virtual Cloud Networks
   - Click your VCN > Subnets > Public Subnet
   - Click Security List > Add Ingress Rules:
     Source: 0.0.0.0/0, Protocol: TCP
     Ports: 80, 443, 3000, 8000, 8080

INSTRUCTIONS

echo ""
echo "Setup script finished!"
