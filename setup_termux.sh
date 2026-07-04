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

# Step 2: Install build deps (REQUIRED for playwright on ARM)
echo ""
echo "📦 [2/7] Installing build dependencies..."
pkg install -y python python-pip git wget curl
# Note: Termux uses different package names than Debian/Ubuntu
# No -dev suffix needed, headers come with the main package
pkg install -y libffi openssl clang binutils make cmake

# Step 3: Install Chromium
echo ""
echo "🌐 [3/7] Installing Chromium browser..."
pkg install -y chromium

# Step 4: Install Python packages
echo ""
echo "📦 [4/7] Installing Python packages..."
pip install --upgrade pip setuptools wheel cffi

echo "🔧 Building playwright from source (10-20 min, be patient)..."
pip install --no-binary :all: playwright || {
    echo "⚠️  Full build failed. Trying minimal build..."
    pip install --no-binary playwright playwright || {
        echo "❌ Could not install playwright."
        echo "    Falling back to requests-only mode."
        echo "    Browser features will be limited."
    }
}

pip install faker rich requests

# Step 5: Configure Chromium path for Playwright
echo ""
echo "🌐 [5/7] Configuring Chromium..."
CHROMIUM_PATH=$(which chromium 2>/dev/null || echo "")
if [ -n "$CHROMIUM_PATH" ]; then
    echo "✅ System chromium: $CHROMIUM_PATH"
    echo "export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=$CHROMIUM_PATH" >> ~/.bashrc
    export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH="$CHROMIUM_PATH"
else
    echo "⚠️  Chromium not found at system path, trying playwright install..."
    python -m playwright install chromium 2>/dev/null || true
fi

# Step 6: Create data directory
echo ""
echo "📁 [6/7] Creating data directory..."
mkdir -p ~/.gmail_creator
mkdir -p ~/.gmail_creator/profiles

# Step 7: Verify installation
echo ""
echo "✅ [7/7] Verifying installation..."
python -c "from playwright.async_api import async_playwright; print('✅ Playwright OK')" 2>/dev/null || echo "⚠️  Playwright not available (browser mode disabled)"
python -c "from faker import Faker; print('✅ Faker OK')"
python -c "from rich.console import Console; print('✅ Rich OK')"
python -c "import requests; print('✅ Requests OK')"

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
