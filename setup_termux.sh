#!/bin/bash
# ==========================================
# Gmail Creator - Termux Setup Script
# Run this on your Android device with Termux
# ==========================================

set -e

echo "╔═══════════════════════════════════════╗"
echo "║  📧 Gmail Creator - Termux Setup 📧  ║"
echo "╚═══════════════════════════════════════╝"

# Step 1: Update Termux
echo ""
echo "📦 [1/5] Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Step 2: Install dependencies
echo ""
echo "📦 [2/5] Installing packages..."
pkg install -y python git wget curl unzip

# Step 3: Install Chromium
echo ""
echo "🌐 [3/5] Installing Chromium..."
pkg install -y x11-repo 2>/dev/null || true
pkg install -y chromium 2>/dev/null || {
    pkg install -y tur-repo 2>/dev/null || true
    pkg install -y chromium 2>/dev/null || true
}

# Verify chromium
CHROMIUM_PATH=$(which chromium 2>/dev/null || echo "")
if [ -n "$CHROMIUM_PATH" ]; then
    echo "✅ Chromium installed: $CHROMIUM_PATH"
else
    echo "❌ Chromium NOT found!"
    echo "   Try manually: pkg install x11-repo && pkg install chromium"
    exit 1
fi

# Step 4: Install chromedriver
echo ""
echo "🔧 [4/5] Installing chromedriver..."
pkg install -y chromium-driver 2>/dev/null || true

CHROMEDRIVER_PATH=$(which chromedriver 2>/dev/null || echo "")
if [ -z "$CHROMEDRIVER_PATH" ]; then
    echo "chromedriver not in repo, trying to extract from chromium package..."
    # Some Termux setups bundle chromedriver with chromium
    find /data/data/com.termux -name "chromedriver" -type f 2>/dev/null | head -1
fi

# Step 5: Install Python packages
echo ""
echo "📦 [5/5] Installing Python packages..."
pip install selenium webdriver-manager faker rich requests

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║       ✅ Setup Complete!              ║"
echo "╠═══════════════════════════════════════╣"
echo "║                                       ║"
echo "║  Run:                                 ║"
echo "║    python main.py                     ║"
echo "║                                       ║"
echo "║  Quick test:                          ║"
echo "║    python main.py --test              ║"
echo "║                                       ║"
echo "╚═══════════════════════════════════════╝"
