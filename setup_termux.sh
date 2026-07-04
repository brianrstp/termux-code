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
echo "📦 [1/6] Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Step 2: Install dependencies
echo ""
echo "📦 [2/5] Installing packages..."
pkg install -y python git wget curl

# Step 3: Install Chromium
echo ""
echo "🌐 [3/5] Installing Chromium..."
pkg install -y x11-repo 2>/dev/null || true
pkg install -y chromium 2>/dev/null || {
    echo "⚠️  chromium not in repo. Installing from alternative..."
    pkg install -y tur-repo 2>/dev/null || true
    pkg install -y chromium 2>/dev/null || echo "⚠️  Will try to download chromedriver manually"
}

# Step 4: Install Python packages
echo ""
echo "📦 [4/5] Installing Python packages..."
# Do NOT run 'pip install --upgrade pip' on Termux — it breaks the package
pip install selenium webdriver-manager faker rich requests

# Step 5: Setup chromedriver
echo ""
echo "🔧 [5/5] Setting up chromedriver..."
# Try Termux package first
pkg install -y chromium-driver 2>/dev/null || true

# Find chromedriver
CHROMEDRIVER_PATH=$(which chromedriver 2>/dev/null || echo "")
if [ -z "$CHROMEDRIVER_PATH" ]; then
    echo "⚠️  chromedriver not found via pkg. Downloading for ARM..."
    ARCH=$(uname -m)
    if [ "$ARCH" = "aarch64" ]; then
        CHROME_VER=$(chromium --version 2>/dev/null | grep -oP '\d+' | head -1 || echo "120")
        echo "   Chromium version: $CHROME_VER"
        echo "   Downloading chromedriver for aarch64..."
        wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VER}.0.6099.0/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip 2>/dev/null || \
        wget -q "https://chromedriver.storage.googleapis.com/${CHROME_VER}.0.6099.0/chromedriver_linux64.zip" -O /tmp/chromedriver.zip 2>/dev/null || true
        if [ -f /tmp/chromedriver.zip ]; then
            unzip -o /tmp/chromedriver.zip -d /tmp/ 2>/dev/null
            cp /tmp/chromedriver-linux64/chromedriver /data/data/com.termux/files/usr/bin/ 2>/dev/null || true
            chmod +x /data/data/com.termux/files/usr/bin/chromedriver 2>/dev/null || true
            rm -f /tmp/chromedriver.zip
            rm -rf /tmp/chromedriver-linux64
            echo "✅ chromedriver installed"
        else
            echo "⚠️  Auto-download failed. Install chromedriver manually."
        fi
    fi
fi

# Verify
CHROMEDRIVER_PATH=$(which chromedriver 2>/dev/null || echo "not found")
echo "🔧 chromedriver: $CHROMEDRIVER_PATH"

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
