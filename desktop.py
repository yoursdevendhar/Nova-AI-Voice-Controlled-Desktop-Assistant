"""
desktop.py — Windows Desktop Automation
Handles: open_app, close_app, open_url, screenshot, volume,
         brightness, lock_screen, shutdown, restart,
         search_file, create_folder, clipboard_get, clipboard_set
"""

import asyncio
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ── Detect if running on a server (not Windows) ───────────────────────────────
IS_SERVER = platform.system() != "Windows"
SERVER_MSG = "🖥️ This action only works when Nova runs locally on your Windows PC. AI chat, voice, and PDF features are fully available here!"


# ── App name → executable / path map ─────────────────────────────────────────
APP_MAP: dict[str, list[str]] = {
    # Browsers
    "chrome":           ["chrome", "google chrome", "googlechrome"],
    "firefox":          ["firefox", "mozilla firefox"],
    "edge":             ["msedge", "microsoft edge"],
    "brave":            ["brave"],
    "opera":            ["opera"],

    # Communication
    "whatsapp":         ["whatsapp", "whatsapp web"],
    "telegram":         ["telegram"],
    "discord":          ["discord"],
    "slack":            ["slack"],
    "teams":            ["teams", "microsoft teams"],
    "zoom":             ["zoom"],
    "skype":            ["skype"],

    # Microsoft Office
    "word":             ["winword", "microsoft word"],
    "excel":            ["excel", "microsoft excel"],
    "powerpoint":       ["powerpnt", "powerpoint", "microsoft powerpoint"],
    "outlook":          ["outlook", "microsoft outlook"],
    "onenote":          ["onenote"],
    "access":           ["msaccess"],

    # Dev tools
    "vscode":           ["code", "visual studio code", "vscode"],
    "notepad":          ["notepad"],
    "notepad++":        ["notepad++", "notepadplusplus"],
    "pycharm":          ["pycharm"],
    "android studio":   ["studio64"],
    "github desktop":   ["githubdesktop"],
    "postman":          ["postman"],
    "cmd":              ["cmd", "command prompt"],
    "powershell":       ["powershell"],
    "terminal":         ["wt", "windows terminal"],
    "git bash":         ["git-bash"],

    # Media
    "vlc":              ["vlc", "vlc media player"],
    "spotify":          ["spotify"],
    "windows media":    ["wmplayer"],
    "photos":           ["microsoft.photos"],

    # System
    "calculator":       ["calc", "calculator"],
    "paint":            ["mspaint", "paint"],
    "wordpad":          ["wordpad"],
    "file explorer":    ["explorer", "file explorer", "explorer.exe"],
    "task manager":     ["taskmgr", "task manager"],
    "settings":         ["ms-settings:", "windows settings"],
    "control panel":    ["control"],
    "registry":         ["regedit"],
    "snipping tool":    ["snippingtool", "snip"],
    "clock":            ["ms-clock:"],
    "maps":             ["bingmaps:"],
    "store":            ["ms-windows-store:"],

    # Other
    "steam":            ["steam"],
    "epic games":       ["epicgameslauncher"],
    "obs":              ["obs64", "obs"],
}

WHATSAPP_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "WhatsApp" / "WhatsApp.exe",
    Path(os.environ.get("PROGRAMFILES", "")) / "WindowsApps" / "WhatsApp",
    Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Local" / "WhatsApp" / "WhatsApp.exe",
]

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
]


class DesktopAutomation:

    def __init__(self):
        if IS_SERVER:
            print("⚠️  Desktop automation disabled (server/Linux mode — AI features still work)")
        else:
            print("✅ Desktop automation ready")

    # ── Main dispatcher ───────────────────────────────────────────────────────
    async def execute(self, action: str, params: dict) -> dict:
        if IS_SERVER:
            return {"success": False, "message": SERVER_MSG}

        loop = asyncio.get_event_loop()
        try:
            fn = getattr(self, f"_act_{action}", None)
            if fn is None:
                return {"success": False, "message": f"Unknown action: {action}"}
            return await loop.run_in_executor(None, fn, params)
        except Exception as e:
            print(f"Desktop action error [{action}]: {e}")
            return {"success": False, "message": f"Action failed: {e}"}

    # ── open_app ─────────────────────────────────────────────────────────────
    def _act_open_app(self, params: dict) -> dict:
        app = params.get("app", "").lower().strip()

        if "whatsapp" in app:
            return self._open_whatsapp()

        if app in ("chrome", "google chrome"):
            return self._open_chrome()

        try:
            subprocess.Popen(["cmd", "/c", "start", "", app],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return {"success": True, "message": f"Opening {app}…"}
        except Exception:
            pass

        exe = self._resolve_app(app)
        if exe:
            try:
                subprocess.Popen(exe, creationflags=subprocess.CREATE_NO_WINDOW,
                                 shell=isinstance(exe, str))
                return {"success": True, "message": f"Opening {app}…"}
            except Exception as e:
                return {"success": False, "message": f"Could not open {app}: {e}"}

        return {"success": False, "message": f"App '{app}' not found. Make sure it's installed."}

    def _open_whatsapp(self) -> dict:
        for p in WHATSAPP_PATHS:
            if Path(p).exists():
                subprocess.Popen(str(p), creationflags=subprocess.CREATE_NO_WINDOW)
                return {"success": True, "message": "Opening WhatsApp…"}
        try:
            subprocess.Popen(
                ["explorer.exe", "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return {"success": True, "message": "Opening WhatsApp…"}
        except Exception:
            pass
        try:
            subprocess.Popen(["cmd", "/c", "start", "whatsapp:"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return {"success": True, "message": "Opening WhatsApp…"}
        except Exception:
            pass
        import webbrowser
        webbrowser.open("https://web.whatsapp.com")
        return {"success": True, "message": "Opening WhatsApp Web in your browser (desktop app not found)."}

    def _open_chrome(self) -> dict:
        for p in CHROME_PATHS:
            if Path(str(p)).exists():
                subprocess.Popen(str(p), creationflags=subprocess.CREATE_NO_WINDOW)
                return {"success": True, "message": "Opening Chrome…"}
        try:
            subprocess.Popen(["cmd", "/c", "start", "chrome"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return {"success": True, "message": "Opening Chrome…"}
        except Exception as e:
            return {"success": False, "message": f"Chrome not found: {e}"}

    def _resolve_app(self, app: str) -> str | list | None:
        for exe, aliases in APP_MAP.items():
            if app == exe or app in aliases:
                return exe
        return None

    # ── close_app ─────────────────────────────────────────────────────────────
    def _act_close_app(self, params: dict) -> dict:
        app = params.get("app", "").lower().strip()
        process_map = {
            "chrome": "chrome.exe", "firefox": "firefox.exe",
            "edge": "msedge.exe", "whatsapp": "WhatsApp.exe",
            "telegram": "Telegram.exe", "discord": "Discord.exe",
            "spotify": "Spotify.exe", "vlc": "vlc.exe",
            "notepad": "notepad.exe", "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE", "powerpoint": "POWERPNT.EXE",
            "teams": "Teams.exe", "zoom": "Zoom.exe",
            "slack": "slack.exe", "obs": "obs64.exe", "vscode": "Code.exe",
        }
        proc = process_map.get(app, app + ".exe")
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", proc],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return {"success": True, "message": f"Closed {app}."}
            return {"success": False, "message": f"Could not close {app} — is it running?"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── open_url ──────────────────────────────────────────────────────────────
    def _act_open_url(self, params: dict) -> dict:
        url = params.get("url", "").strip()
        if not url:
            return {"success": False, "message": "No URL provided."}
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        import webbrowser
        webbrowser.open(url)
        return {"success": True, "message": f"Opening {url} in your browser…"}

    # ── screenshot ────────────────────────────────────────────────────────────
    def _act_screenshot(self, params: dict) -> dict:
        try:
            import pyautogui
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            desktop = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
            desktop.mkdir(parents=True, exist_ok=True)
            path = desktop / f"nova_screenshot_{ts}.png"
            img = pyautogui.screenshot()
            img.save(str(path))
            return {"success": True, "message": f"Screenshot saved to Desktop as nova_screenshot_{ts}.png"}
        except ImportError:
            import pyautogui
            pyautogui.hotkey("win", "shift", "s")
            return {"success": True, "message": "Snipping tool opened — select an area to capture."}
        except Exception as e:
            return {"success": False, "message": f"Screenshot failed: {e}"}

    # ── volume ────────────────────────────────────────────────────────────────
    def _act_volume(self, params: dict) -> dict:
        direction = params.get("direction", "up")
        amount    = int(params.get("amount", 10))
        try:
            import pyautogui
            if direction == "mute":
                pyautogui.press("volumemute")
                return {"success": True, "message": "Volume muted/unmuted."}
            elif direction == "up":
                for _ in range(max(1, amount // 2)):
                    pyautogui.press("volumeup")
                return {"success": True, "message": "Volume increased."}
            elif direction == "down":
                for _ in range(max(1, amount // 2)):
                    pyautogui.press("volumedown")
                return {"success": True, "message": "Volume decreased."}
        except ImportError:
            pass
        try:
            if direction == "mute":
                subprocess.run(
                    ["powershell", "-c",
                     "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"],
                    creationflags=subprocess.CREATE_NO_WINDOW, check=True
                )
            else:
                key = 175 if direction == "up" else 174
                for _ in range(max(1, amount // 2)):
                    subprocess.run(
                        ["powershell", "-c",
                         f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]{key})"],
                        creationflags=subprocess.CREATE_NO_WINDOW, check=True
                    )
            return {"success": True, "message": f"Volume {direction}."}
        except Exception as e:
            return {"success": False, "message": f"Volume control failed: {e}"}

    # ── brightness ────────────────────────────────────────────────────────────
    def _act_brightness(self, params: dict) -> dict:
        try:
            import screen_brightness_control as sbc
            if "level" in params:
                level = max(0, min(100, int(params["level"])))
                sbc.set_brightness(level)
                return {"success": True, "message": f"Brightness set to {level}%."}
            else:
                direction = params.get("direction", "up")
                amount    = int(params.get("amount", 10))
                current   = sbc.get_brightness()
                current   = current[0] if isinstance(current, list) else current
                new_val   = max(0, min(100, current + (amount if direction == "up" else -amount)))
                sbc.set_brightness(new_val)
                return {"success": True, "message": f"Brightness {'increased' if direction=='up' else 'decreased'} to {new_val}%."}
        except ImportError:
            try:
                direction = params.get("direction", "up")
                amount    = int(params.get("amount", 10))
                ps = (
                    "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                    f".WmiSetBrightness(1, [Math]::Min(100, [Math]::Max(0, "
                    f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness "
                    f"{'+ ' + str(amount) if direction == 'up' else '- ' + str(amount)})))"
                )
                subprocess.run(
                    ["powershell", "-c", ps],
                    creationflags=subprocess.CREATE_NO_WINDOW, check=True
                )
                return {"success": True, "message": "Brightness adjusted."}
            except Exception as e:
                return {"success": False, "message": f"Brightness control failed: {e}"}
        except Exception as e:
            return {"success": False, "message": f"Brightness error: {e}"}

    # ── lock_screen ───────────────────────────────────────────────────────────
    def _act_lock_screen(self, params: dict) -> dict:
        try:
            subprocess.Popen(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return {"success": True, "message": "Locking screen now."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── shutdown ──────────────────────────────────────────────────────────────
    def _act_shutdown(self, params: dict) -> dict:
        try:
            subprocess.Popen(["shutdown", "/s", "/t", "10"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return {"success": True, "message": "Shutting down in 10 seconds. Run 'shutdown /a' to cancel."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── restart ───────────────────────────────────────────────────────────────
    def _act_restart(self, params: dict) -> dict:
        try:
            subprocess.Popen(["shutdown", "/r", "/t", "10"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return {"success": True, "message": "Restarting in 10 seconds. Run 'shutdown /a' to cancel."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── search_file ───────────────────────────────────────────────────────────
    def _act_search_file(self, params: dict) -> dict:
        query = params.get("query", "").strip()
        if not query:
            return {"success": False, "message": "No search query provided."}
        search_dirs = [
            Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop",
            Path(os.environ.get("USERPROFILE", Path.home())) / "Documents",
            Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads",
        ]
        found = []
        for d in search_dirs:
            if d.exists():
                for p in d.rglob(f"*{query}*"):
                    found.append(str(p))
                    if len(found) >= 5:
                        break
            if len(found) >= 5:
                break
        if found:
            files = "\n".join(found[:5])
            return {"success": True, "message": f"Found {len(found)} file(s) matching '{query}':\n{files}"}
        return {"success": False, "message": f"No files matching '{query}' found in Desktop, Documents, or Downloads."}

    # ── create_folder ─────────────────────────────────────────────────────────
    def _act_create_folder(self, params: dict) -> dict:
        name = params.get("name", "New Folder").strip()
        base = params.get("path", "").strip()
        if not base:
            base = str(Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop")
        target = Path(base) / name
        try:
            target.mkdir(parents=True, exist_ok=True)
            return {"success": True, "message": f"Folder '{name}' created at {target}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to create folder: {e}"}

    # ── clipboard ─────────────────────────────────────────────────────────────
    def _act_clipboard_get(self, params: dict) -> dict:
        try:
            import pyperclip
            text = pyperclip.paste()
            if text:
                return {"success": True, "message": f"Clipboard contains: {text[:300]}"}
            return {"success": True, "message": "Clipboard is empty."}
        except Exception as e:
            return {"success": False, "message": f"Clipboard read failed: {e}"}

    def _act_clipboard_set(self, params: dict) -> dict:
        text = params.get("text", "")
        try:
            import pyperclip
            pyperclip.copy(text)
            return {"success": True, "message": f"Copied to clipboard: {text[:80]}"}
        except Exception as e:
            return {"success": False, "message": f"Clipboard write failed: {e}"}
