# KAHNA — Local AI Computer Agent

KAHNA is an intelligent, cross-platform local AI companion featuring an interactive 3D Voice Orb GUI, native speech engine, and remote Telegram control.

---

## Features

- **3D Glowing Orb GUI**: Built with React, Three.js, Tailwind CSS, and Tauri v2. Dynamically reflects agent state (Idle, Listening, Thinking, Speaking).
- **Voice Agent with Barge-In**: Real-time voice interaction with native speech output (macOS `say` / Windows SAPI). Loud-voice speech interruption cuts off TTS output immediately when you speak.
- **Remote Telegram Bot**: Control your machine remotely via Telegram with screenshot capture, application management, file browsing, and multi-user access control.
- **Cross-Platform OS Automation**: Native operating system adapters for macOS and Windows.
- **Unified Single-Command Launcher**: Launch both backend agent services and the desktop GUI with a single command.

---

## Prerequisites

1. **Python 3.10+**
2. **Node.js 18+** and `npm`
3. **Rust and Cargo** (Required for Tauri desktop app: https://www.rust-lang.org/tools/install)
4. An **OpenRouter API Key** (Free tier available at https://openrouter.ai/keys)

---

## Quickstart Guide

### 1. Clone and Set Up Backend

```bash
# Clone the repository
git clone https://github.com/Satishhhh989/Kanha.git
cd Kanha

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
# Message @userinfobot on Telegram to retrieve your numeric ID
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

## Running the Application

### Option A: All-in-One Mode (Recommended)
Launches the agent backend, starts voice listener and Telegram bot, and opens the 3D Orb Desktop window:

```bash
python -m apps.cli.main desktop
```

### Option B: Standalone Services
Individual components can also be run independently:

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
- **API and WebSocket Server:**
  ```bash
  python -m apps.cli.main serve
  ```
- **Desktop GUI Only (Connects to running backend):**
  ```bash
  cd desktop
  npm run tauri dev
  ```

---

## Telegram Multi-User Setup

To grant access to multiple Telegram accounts:
1. Have each user send any message to `@userinfobot` on Telegram to get their numeric User ID.
2. Add their IDs to `.env` separated by commas:
   ```env
   TELEGRAM_ALLOWED_USER_ID=your_id,second_user_id,third_user_id
   ```
3. Restart KAHNA. The bot will authenticate all listed user IDs.

---

## Project Structure

```
kanha/
├── apps/
│   ├── api/          # FastAPI and WebSocket server
│   └── cli/          # Command-line interface and runner
├── core/
│   ├── agent/        # Agent runtime, prompt loop, context
│   ├── ai/           # OpenRouter LLM provider and fallback handler
│   ├── computer/     # Desktop control tools (screenshots, apps, bash)
│   ├── session/      # SQLite session database
│   └── voice/        # Voice session, audio stream, barge-in logic
├── desktop/          # Tauri v2 + React 3D Glowing Orb GUI
├── infrastructure/   # Audio capture and native TTS engines
├── remote/           # Telegram bot adapter and multi-user auth
└── sysplatform/      # Platform-specific OS adapters (macOS and Windows)
```

---

## Security Note

Never commit your `.env` file to version control. Keep your `OPENROUTER_API_KEY` and `TELEGRAM_BOT_TOKEN` private.
