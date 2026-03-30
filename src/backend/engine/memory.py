from __future__ import annotations

from uuid import uuid4


class MemorySystem:
    """Manages separate conversation threads with branching support for backtracking."""

    def __init__(self) -> None:
        self._conversations: dict[str, list[dict[str, str]]] = {}

    def create_conversation(self) -> str:
        conversation_id = str(uuid4())
        self._conversations[conversation_id] = []
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append(
            {"role": role, "content": content}
        )

    def get_conversation(self, conversation_id: str) -> list[dict[str, str]]:
        return list(self._conversations.get(conversation_id, []))

    def branch_excluding_last_turn(self, conversation_id: str) -> str:
        """Fork the conversation, removing the last user+assistant exchange.

        Used during backtracking to give the target model a clean slate
        without the refused exchange.
        """
        original = self.get_conversation(conversation_id)
        new_id = str(uuid4())
        self._conversations[new_id] = original[:-2] if len(original) >= 2 else []
        return new_id

    def get_message_count(self, conversation_id: str) -> int:
        return len(self._conversations.get(conversation_id, []))
