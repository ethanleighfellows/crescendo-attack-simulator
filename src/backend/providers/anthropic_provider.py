from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Optional

from pydantic import BaseModel

from src.backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude models."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> None:
        super().__init__(model, api_key, base_url, temperature, max_retries)
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def _get_client(self) -> Any:
        from anthropic import AsyncAnthropic

        kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return AsyncAnthropic(**kwargs)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        client = self._get_client()
        messages: list[dict[str, str]] = []

        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": self.temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await client.messages.create(**kwargs)
                return response.content[0].text
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.warning(
                        "Anthropic generation attempt %d failed, retrying in %ds: %s",
                        attempt + 1,
                        sleep_time,
                        exc,
                    )
                    await asyncio.sleep(sleep_time)

        raise RuntimeError(
            f"Anthropic generation failed after {self.max_retries} attempts: {last_error}"
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        json_instruction = (
            "\n\nYou MUST respond with ONLY a valid JSON object. "
            "No markdown, no explanation, just the JSON."
        )
        full_prompt = prompt + json_instruction

        raw_response = await self.generate(
            full_prompt, system_prompt=system_prompt
        )

        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        data = json.loads(text)
        return schema(**data)

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            await client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
