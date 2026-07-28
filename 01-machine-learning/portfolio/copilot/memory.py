from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

MAX_TURNS = 6


@dataclass
class MemoryTurn:
    role: str
    text: str
    intent: Optional[str] = None
    resolved_entity: Optional[str] = None


class ConversationMemory:
    def __init__(self) -> None:
        self._turns: list[MemoryTurn] = []

    def add(self, role: str, text: str, intent: str | None = None, resolved_entity: str | None = None) -> None:
        self._turns.append(MemoryTurn(role=role, text=text, intent=intent, resolved_entity=resolved_entity))
        if len(self._turns) > MAX_TURNS * 2:
            self._turns = self._turns[-MAX_TURNS * 2:]

    def last_n_turns(self, n: int = MAX_TURNS) -> list[MemoryTurn]:
        return self._turns[-n:]

    def resolved_entities(self) -> list[str]:
        entities: list[str] = []
        for turn in self._turns:
            if turn.resolved_entity and turn.resolved_entity not in entities:
                entities.append(turn.resolved_entity)
        return entities

    def last_intent(self) -> str | None:
        for turn in reversed(self._turns):
            if turn.intent:
                return turn.intent
        return None

    def clear(self) -> None:
        self._turns = []

    def is_empty(self) -> bool:
        return len(self._turns) == 0

    def to_context_string(self) -> str:
        parts: list[str] = []
        for turn in self.last_n_turns():
            parts.append(f"[{turn.role}]: {turn.text}")
        return "\n".join(parts)