from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class BaseProvider(ABC):
    """Unified interface for LLM providers.

    Both the target model and the simulator/judge model use this interface.
    Providers handle authentication, request formatting, and response parsing.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_retries = max_retries

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Generate a text completion.

        Args:
            prompt: The user message to send.
            system_prompt: Optional system message prepended to the conversation.
            history: Optional prior conversation messages as {"role": ..., "content": ...} dicts.

        Returns:
            The model's text response.
        """
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        """Generate a structured response conforming to a Pydantic schema.

        Args:
            prompt: The user message containing the full context.
            schema: A Pydantic model class defining the expected output shape.
            system_prompt: Optional system message.

        Returns:
            An instance of the given schema populated from the model's response.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify the provider connection is working."""
        ...
