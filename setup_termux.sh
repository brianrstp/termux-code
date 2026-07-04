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
echo "📦 [1/7] Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Step 2: Install required packages
echo ""
echo "📦 [2/7] Installing system dependencies..."
pkg install -y python python-pip git wget curl

# Step 3: Install Node.js (needed for Playwright)
echo ""
echo "📦 [3/7] Installing Node.js (required by Playwright)..."
pkg install -y nodejs

# Step 4: Install Python dependencies
echo ""
echo "📦 [4/7] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Install Playwright browsers
echo ""
echo "🌐 [5/7] Installing Playwright Chromium..."
echo "This may take a few minutes..."
python -m playwright install chromium
python -m playwright install-deps chromium 2>/dev/null || true

# Step 6: Create data directory
echo ""
echo "📁 [6/7] Creating data directory..."
mkdir -p ~/.gmail_creator
mkdir -p ~/.gmail_creator/profiles

# Step 7: Verify installation
echo ""
echo "✅ [7/7] Verifying installation..."
python -c "from playwright.async_api import async_playwright; print('✅ Playwright OK')"
python -c "from faker import Faker; print('✅ Faker OK')"
python -c "from rich.console import Console; print('✅ Rich OK')"

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║       ✅ Setup Complete!              ║"
echo "╠═══════════════════════════════════════╣"
echo "║                                       ║"
echo "║  Run the creator:                     ║"
echo "║    python main.py                     ║"
echo "║                                       ║"
echo "║  Quick test:                          ║"
echo "║    python main.py --test              ║"
echo "║                                       ║"
echo "║  CLI options:                         ║"
echo "║    python main.py -n 5  (5 accounts) ║"
echo "║    python main.py --list             ║"
echo "║                                       ║"
echo "║  SMS providers (env vars):            ║"
echo "║    export SMS_ACTIVATE_API_KEY=...    ║"
echo "║    export FIVE_SIM_API_KEY=...        ║"
echo "║    export PROXY=socks5://...          ║"
echo "║                                       ║"
echo "╚═══════════════════════════════════════╝"
