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
pip install --upgrade pip
pip install selenium webdriver-manager faker rich requests

# Step 5: Verify installation
echo ""
echo "✅ [5/5] Verifying..."
python -c "from selenium import webdriver; print('✅ Selenium OK')"
python -c "from faker import Faker; print('✅ Faker OK')"
python -c "from rich.console import Console; print('✅ Rich OK')"
CHROMIUM_PATH=$(which chromium 2>/dev/null || echo "not found")
echo "🌐 Chromium: $CHROMIUM_PATH"

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
