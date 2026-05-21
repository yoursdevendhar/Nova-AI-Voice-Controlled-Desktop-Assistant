"""
core/nlu.py — Natural Language Understanding via Groq
"""

import asyncio
import json
import re
from typing import Any

from groq import Groq


SYSTEM_PROMPT = """You are Nova, an intelligent AI desktop assistant for Windows.

When the user gives a command, respond ONLY with a valid JSON object.
No markdown, no text outside the JSON.

JSON schema:
{
  "intent": "<intent_name>",
  "action": "<action_key or null>",
  "params": {},
  "reply": "<short friendly spoken reply>"
}

Available intents and actions:
  open_app        → action: "open_app",      params: {"app": "<name>"}
  close_app       → action: "close_app",     params: {"app": "<name>"}
  open_website    → action: "open_url",      params: {"url": "<url>"}
  screenshot      → action: "screenshot",    params: {}
  volume_up       → action: "volume",        params: {"direction": "up",   "amount": 10}
  volume_down     → action: "volume",        params: {"direction": "down", "amount": 10}
  volume_mute     → action: "volume",        params: {"direction": "mute"}
  lock_screen     → action: "lock_screen",   params: {}
  shutdown        → action: "shutdown",      params: {}
  restart         → action: "restart",       params: {}
  search_file     → action: "search_file",   params: {"query": "<name>"}
  create_folder   → action: "create_folder", params: {"name": "<name>", "path": "<optional>"}
  clipboard_get   → action: "clipboard_get", params: {}
  clipboard_set   → action: "clipboard_set", params: {"text": "<text>"}
  brightness_up   → action: "brightness",    params: {"direction": "up",    "amount": 10}
  brightness_down → action: "brightness",    params: {"direction": "down",  "amount": 10}
  brightness_set  → action: "brightness",    params: {"level": <0-100>}
  general_qa      → action: null
  write_code      → action: null,            params: {"language": "<lang>", "task": "<task>"}
  explain_code    → action: null,            params: {"code": "<snippet>"}
  chitchat        → action: null

Rules:
- reply must be concise and conversational (1-2 sentences max).
- For shutdown/restart, warn the user in the reply.
- For general_qa, write_code, explain_code: put the full answer in "reply".
- Never wrap output in markdown code fences.
"""


class NLUEngine:
    def __init__(self, api_key: str):
        self._client = Groq(api_key=api_key)

    def _call_groq(self, messages: list) -> str:
        response = self._client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    async def process(self, user_text: str, history: list[dict]) -> dict[str, Any]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for turn in history[-6:]:
            messages.append({"role": "user",      "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})

        messages.append({"role": "user", "content": user_text})

        try:
            # Run sync Groq client in a thread so it doesn't block the event loop
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, self._call_groq, messages)
            return self._parse(raw)
        except Exception as e:
            print(f"Groq error: {e}")
            return {
                "intent": "error",
                "action": None,
                "params": {},
                "reply": "I couldn't reach my AI engine. Please check your GROQ_API_KEY in the .env file.",
            }

    def _parse(self, raw: str) -> dict[str, Any]:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                data.setdefault("intent", "general_qa")
                data.setdefault("action", None)
                data.setdefault("params", {})
                data.setdefault("reply", "Done.")
                return data
            except json.JSONDecodeError:
                pass
        return {"intent": "general_qa", "action": None, "params": {}, "reply": raw}