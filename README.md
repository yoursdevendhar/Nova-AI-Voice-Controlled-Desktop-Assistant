# ✦ Nova AI — Voice-Controlled Desktop Assistant

> An intelligent AI-powered desktop assistant for Windows, built with Python, FastAPI, and Grok AI.
> Control your PC, automate tasks, write code, and chat naturally — all through voice or text.

---

## 📸 Preview

```
┌─────────────────────────────────────────────────────┐
│  NOVA                          Voice & Text Interface│
├──────────┬──────────────────────────────────────────┤
│Assistant │                                          │
│History   │         ◉  (animated orb)               │
│Settings  │      Listening...                        │
│          │  ┌──────────────────────────────────┐   │
│          │  │ Open Chrome           [user]      │   │
│          │  │ Opening Chrome...     [nova ✦]    │   │
│          │  │ Write a sort function [user]      │   │
│          │  │ Here's your code ↓    [nova ✦]    │   │
│          │  └──────────────────────────────────┘   │
│          │  🎙  ___________________________ [➤]    │
└──────────┴──────────────────────────────────────────┘
```

---

## ✨ Features

| Category | Capabilities |
|---|---|
| 🎙️ Voice | Browser mic recording → speech-to-text → Grok response |
| 🤖 AI | Grok 3 Fast — intent detection, code generation, Q&A |
| 🖥️ Automation | Open/close apps, screenshots, volume, lock, shutdown, file search |
| 💬 Memory | Per-session conversation history (rolling 20 turns) |
| 🔊 TTS | pyttsx3 — Nova speaks her replies aloud |
| 🎨 UI | Futuristic glassmorphism design with animated orb and visualizer |
| ⚡ Real-time | WebSocket for instant streaming responses |

---

## 🗂️ Project Structure

```
nova-ai/
├── backend/
│   ├── main.py                  # FastAPI server — REST + WebSocket
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   ├── core/
│   │   ├── nlu.py               # Grok NLU engine (intent + action parsing)
│   │   └── conversation.py      # Per-session memory manager
│   ├── services/
│   │   └── tts.py               # Text-to-speech via pyttsx3
│   └── automation/
│       └── desktop.py           # Windows desktop actions
└── frontend/
    └── index.html               # Complete UI (single file, no build step)
```

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yoursdevendhar/Nova-AI-Voice-Controlled-Desktop-Assistant.git
cd Nova-AI-Voice-Controlled-Desktop-Assistant
```

### 2. Set up Python environment
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your GROQ API key
```bash
copy .env.example .env
```
Edit .env:
```
GROQ_API_KEY=your_key_here

### 4. Start the backend
```bash
# Must be run from inside the backend/ folder
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Open the UI
Visit → **http://127.0.0.1:8000**

---

## 🗣️ Example Commands

```
"Open Chrome"
"Take a screenshot"
"Volume up"
"Lock the screen"
"Search for budget.xlsx"
"Create a folder called Projects"
"Open youtube.com"
"Write a Python function to reverse a string"
"Explain what a binary search tree is"
"Shutdown the PC"
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, Uvicorn |
| AI | Grok 3 Fast via xAI API (`openai` SDK, OpenAI-compatible) |
| STT | SpeechRecognition (Google Web Speech API) |
| TTS | pyttsx3 (Windows SAPI) |
| Automation | subprocess, pyautogui, pyperclip |
| Frontend | Vanilla HTML / CSS / JS, WebSocket |

---

## 🧩 Supported Desktop Actions

| Command | What Nova Does |
|---|---|
| "Open [app]" | Launches the application |
| "Close [app]" | Kills the process |
| "Open [website]" | Opens in default browser |
| "Take a screenshot" | Saves PNG to Desktop with timestamp |
| "Volume up / down / mute" | Controls system volume via PowerShell |
| "Lock the screen" | Locks Windows session |
| "Shutdown / Restart" | Power control with 15-second cancel window |
| "Search for [filename]" | Searches Documents, Desktop, Downloads |
| "Create folder [name]" | Creates folder on Desktop |
| "What's in my clipboard" | Reads clipboard contents aloud |

---

## 🐛 Troubleshooting

**`No module named 'core'`**
→ You're running uvicorn from the wrong folder. Always `cd backend` first.

**`XAI_API_KEY not set`**
→ Create `backend/.env` from `.env.example` and paste your key.

**Mic not working**
→ Allow microphone permissions in your browser when prompted. No PyAudio needed — recording happens in the browser.

**TTS not speaking**
→ pyttsx3 uses Windows SAPI — works out of the box on Windows 10/11. No extra install needed.

**App won't open**
→ Add the executable name to `APP_MAP` in `automation/desktop.py`.

---




<p align="center">Built with ✦ by Nova AI &nbsp;|&nbsp; Powered by Grok (xAI)</p>
