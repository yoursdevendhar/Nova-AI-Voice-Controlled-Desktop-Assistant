"""
core/conversation.py — per-session rolling conversation history
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import List


@dataclass
class Turn:
    user: str
    assistant: str


class ConversationManager:
    MAX_TURNS = 20

    def __init__(self):
        self._sessions: dict[str, List[Turn]] = defaultdict(list)

    def add(self, session_id: str, user: str, assistant: str):
        turns = self._sessions[session_id]
        turns.append(Turn(user, assistant))
        if len(turns) > self.MAX_TURNS:
            self._sessions[session_id] = turns[-self.MAX_TURNS:]

    def get_history(self, session_id: str) -> list[dict]:
        return [{"user": t.user, "assistant": t.assistant}
                for t in self._sessions[session_id]]

    def clear(self, session_id: str):
        self._sessions[session_id] = []