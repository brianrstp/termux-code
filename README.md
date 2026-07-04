# 📧 Gmail Creator — Termux Edition

Gmail account creator optimized for **Termux on Android**. Uses Playwright + Chromium with stealth mode instead of Chromax browser.

## ⚠️ Disclaimer

This tool is for **educational purposes only**. Automated account creation may violate Google's Terms of Service. Use at your own risk.

## 📱 Requirements

- Android device with **Termux** installed
- Minimum 2GB RAM
- Stable internet connection

## 🚀 Setup

### 1. Install Termux
Download from [F-Droid](https://f-droid.org/en/packages/com.termux/) (recommended) or GitHub Releases.

### 2. Clone & Setup
```bash
# Clone or copy project files
cd ~/gmail-creator

# Run setup script
chmod +x setup_termux.sh
./setup_termux.sh
```

### 3. Or Manual Setup
```bash
pkg update && pkg upgrade
pkg install python python-pip nodejs git
pip install -r requirements.txt
python -m playwright install chromium
```

## 📖 Usage

### Interactive Mode
```bash
python main.py
```

### CLI Mode
```bash
# Create 1 account (test mode)
python main.py --test

# Create 5 accounts
python main.py -n 5

# List saved accounts
python main.py --list

# With proxy
python main.py --test --proxy socks5://user:pass@host:port

# With specific SMS provider
python main.py --test --sms manual
python main.py --test --sms sms_activate
python main.py --test --sms five_sim
```

### Environment Variables
```bash
# SMS Providers
export SMS_ACTIVATE_API_KEY="your-key"
export FIVE_SIM_API_KEY="your-key"

# Proxy
export PROXY="socks5://user:pass@host:port"
```

## 📁 Project Structure

```
├── config.py          # Configuration & settings
├── browser.py         # Playwright stealth browser
├── gmail_create.py    # Gmail creation logic
├── sms_verify.py      # SMS verification providers
├── main.py            # CLI interface
├── requirements.txt   # Python dependencies
├── setup_termux.sh    # Termux setup script
└── README.md          # This file
```

## 🔧 How It Works

1. **Browser Warmup** — Visits Google to build fingerprint
2. **Signup Flow** — Navigates to Gmail signup
3. **Fills Information** — Name, birthday, gender (randomized)
4. **Email Selection** — Creates custom username
5. **Password** — Generates strong password
6. **Phone Verification** — Via API or manual input
7. **Terms Acceptance** — Accepts Google ToS

### Anti-Detection Features
- 🕵️ JavaScript stealth (hides webdriver, plugins, etc.)
- 🎭 Random user agents (mobile & desktop profiles)
- ⌨️ Human-like typing with typos and backspace
- 🖱️ Natural mouse movement and clicks
- ⏱️ Variable delays between actions
- 🌐 Request interception (blocks trackers)
- 📱 Mobile device emulation

## 📱 SMS Providers

| Provider | Setup | Notes |
|----------|-------|-------|
| `manual` | None (default) | Enter code yourself |
| `sms_activate` | Set `SMS_ACTIVATE_API_KEY` | Paid service |
| `five_sim` | Set `FIVE_SIM_API_KEY` | Paid service |

## 💾 Accounts Storage

Created accounts are saved to `~/.gmail_creator/accounts.json`:
```json
[
  {
    "email": "example@gmail.com",
    "password": "StrongP@ss123",
    "profile": "Pixel7",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

## ⚡ Performance Tips

- Use **headless mode** (default) for faster creation
- Use a **proxy** to avoid IP-based detection
- Wait between accounts to avoid rate limiting
- Use a **dedicated phone number** for each account

## 🐛 Troubleshooting

### Playwright won't install
```bash
pkg install build-essential
pip install playwright
python -m playwright install chromium
```

### Out of memory
```bash
# Increase swap
fallocate -l 2G ~/swapfile
chmod 600 ~/swapfile
mkswap ~/swapfile
swapon ~/swapfile
```

### Connection errors
```bash
# Try with proxy
export PROXY="socks5://127.0.0.1:1080"
python main.py --test
```
