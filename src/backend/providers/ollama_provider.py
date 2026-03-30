from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from pydantic import BaseModel

from src.backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    """Provider for locally-hosted Ollama models."""

    def __init__(
        self,
        model: str = "llama3.1",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> None:
        super().__init__(
            model, api_key, base_url or DEFAULT_OLLAMA_URL, temperature, max_retries
        )

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        import httpx

        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                result = await self._post(
                    "/api/chat",
                    {
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": self.temperature},
                    },
                )
                return result.get("message", {}).get("content", "")
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.warning(
                        "Ollama generation attempt %d failed, retrying in %ds: %s",
                        attempt + 1,
                        sleep_time,
                        exc,
                    )
                    await asyncio.sleep(sleep_time)

        raise RuntimeError(
            f"Ollama generation failed after {self.max_retries} attempts: {last_error}"
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        json_instruction = (
            "\n\nRespond with ONLY a valid JSON object. "
            "No markdown, no explanation, just the JSON."
        )
        full_prompt = prompt + json_instruction
        raw = await self.generate(full_prompt, system_prompt=system_prompt)

        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        data = json.loads(text)
        return schema(**data)

    async def health_check(self) -> bool:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
