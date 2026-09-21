# ⚡ KAHNA — Local AI Computer Agent

KAHNA is an intelligent, cross-platform local AI companion with a futuristic 3D Voice Orb GUI, native speech engine, and remote Telegram control.

---

## ✨ Features

- **Futuristic 3D Glowing Orb GUI**: React + Three.js + Tailwind + Tauri v2 interface with animated glow states (Idle, Listening, Thinking, Speaking).
- **Voice Agent with Barge-In**: Real-time voice interaction with native speech output (macOS `say` / Windows SAPI). Loud-voice speech interruption cuts off TTS instantly when you talk back.
- **Remote Telegram Bot**: Control your machine remotely via Telegram with screenshot capture, app launching, file browsing, and multi-user access control.
- **Cross-Platform OS Control**: Native automation adapters for macOS and Windows.
- **Unified Single-Command Launcher**: Launch both the backend agent services and the desktop GUI with a single command.

---

## 📋 Prerequisites

1. **Python 3.10+**
2. **Node.js 18+** & `npm`
3. **Rust & Cargo** (Required for Tauri desktop app: https://www.rust-lang.org/tools/install)
4. An **OpenRouter API Key** (Free tier available at https://openrouter.ai/keys)

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Backend

```bash
# Clone the repository
git clone <your-repo-url>
cd kanha

# Create and activate a Python virtual environment
# On macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install backend dependencies in editable mode:
```bash
pip install -e .
```

---

### 2. Configure Environment Variables

Copy the example configuration file:
```bash
cp .env.example .env
```

Open `.env` and configure your credentials:
```env
# Your OpenRouter API key
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=nex-agi/nex-n2.5-pro:free

# Telegram Bot (Optional, for remote control)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Comma-separated Telegram user IDs allowed to control the bot
# Message @userinfobot on Telegram to get your numeric ID
TELEGRAM_ALLOWED_USER_ID=123456789,987654321
```

---

### 3. Install Desktop GUI Dependencies

```bash
cd desktop
npm install
cd ..
```

---

## 🎮 How to Run

### Option A: All-in-One Mode (Recommended)
Launches the agent backend, starts voice listener & Telegram bot, and opens the 3D Orb Desktop window:

```bash
python -m apps.cli.main desktop
```

### Option B: Standalone Services
You can also run individual components separately:

- **Interactive CLI Chat:**
  ```bash
  python -m apps.cli.main chat
  ```
- **Voice Agent Only:**
  ```bash
  python -m apps.cli.main voice
  ```
- **Telegram Bot Only:**
  ```bash
  python -m apps.cli.main telegram
  ```
- **API / WebSocket Server:**
  ```bash
  python -m apps.cli.main serve
  ```
- **Desktop GUI Only (Connects to running backend):**
  ```bash
  cd desktop
  npm run tauri dev
  ```

---

## 🔒 Telegram Multi-User Setup

To let others access the same Telegram bot from their accounts:
1. Ask them to send any message to `@userinfobot` on Telegram to get their numeric User ID.
2. Add their ID to `.env` separated by a comma:
   ```env
   TELEGRAM_ALLOWED_USER_ID=your_id,friend1_id,friend2_id
   ```
3. Restart KAHNA. They can now interact with the bot!

---

## 📁 Project Structure

```
kanha/
├── apps/
│   ├── api/          # FastAPI & WebSocket server
│   └── cli/          # Command-line interface & runner
├── core/
│   ├── agent/        # Agent runtime, prompt loop, context
│   ├── ai/           # OpenRouter LLM provider & failover
│   ├── computer/     # Desktop control tools (screenshots, apps, bash)
│   ├── session/      # SQLite session database
│   └── voice/        # Voice session, audio stream, barge-in logic
├── desktop/          # Tauri v2 + React 3D Glowing Orb GUI
├── infrastructure/   # Audio capture & native TTS engines
├── remote/           # Telegram bot adapter & multi-user auth
└── sysplatform/      # Platform-specific OS adapters (macOS / Windows)
```

---

## 🛡️ Privacy & Security Note

Never commit your `.env` file to version control. Keep your `OPENROUTER_API_KEY` and `TELEGRAM_BOT_TOKEN` private.
