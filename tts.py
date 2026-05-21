"""
services/tts.py — Text-to-Speech using pyttsx3
Runs synthesis in a subprocess to avoid pyttsx3 COM/threading issues on Windows.
"""

import base64
import io
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path


class TTSService:
    """
    Synthesises speech to a WAV byte-string using pyttsx3.
    Each synthesis runs in its own subprocess so pyttsx3's COM
    initialisation never conflicts with FastAPI's event loop.
    """

    def __init__(self):
        self.available = self._check_available()
        self._lock = threading.Lock()
        if self.available:
            print("✅ TTS ready (pyttsx3)")
        else:
            print("⚠️  pyttsx3 not found — TTS disabled")

    # ------------------------------------------------------------------
    def _check_available(self) -> bool:
        try:
            import pyttsx3  # noqa: F401
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    def synthesize_b64(self, text: str) -> str | None:
        """Return base64-encoded WAV audio, or None on failure."""
        if not self.available or not text:
            return None
        try:
            with self._lock:
                return self._synth_subprocess(text)
        except Exception as e:
            print(f"TTS error: {e}")
            return None

    # ------------------------------------------------------------------
    def _synth_subprocess(self, text: str) -> str | None:
        """
        Spawn a fresh Python process that runs pyttsx3 and writes a WAV
        to a temp file, then read and base64-encode it.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name

        script = f"""
import pyttsx3, sys
engine = pyttsx3.init()
engine.setProperty('rate', 165)
engine.setProperty('volume', 1.0)
# Try to pick a female voice if available
voices = engine.getProperty('voices')
for v in voices:
    if 'female' in v.name.lower() or 'zira' in v.name.lower() or 'hazel' in v.name.lower():
        engine.setProperty('voice', v.id)
        break
engine.save_to_file({repr(text)}, {repr(tmp_path)})
engine.runAndWait()
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            timeout=15,
        )

        if result.returncode != 0:
            print(f"TTS subprocess error: {result.stderr.decode()}")
            return None

        try:
            data = Path(tmp_path).read_bytes()
            if not data:
                return None
            return base64.b64encode(data).decode()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass