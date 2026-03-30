from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

from pydantic import BaseModel

from src.backend.providers.openai_provider import OpenAIProvider

DEFAULT_TOGETHER_BASE_URL = "https://api.together.xyz/v1"
logger = logging.getLogger(__name__)


class TogetherAIProvider(OpenAIProvider):
    """Provider for Together AI's OpenAI-compatible chat completions API."""

    def __init__(
        self,
        model: str = "meta-llama/Meta-Llama-3-8B-Instruct-Lite",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> None:
        resolved_base_url = base_url or DEFAULT_TOGETHER_BASE_URL
        resolved_api_key = api_key or os.environ.get("TOGETHER_API_KEY", "")
        super().__init__(
            model=model,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            temperature=temperature,
            max_retries=max_retries,
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        client = self._get_client()
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"{prompt}\n\n"
                    "Respond with ONLY a valid JSON object matching the requested schema. "
                    "No markdown, no code fences, no explanation."
                ),
            }
        )

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                )
                raw = response.choices[0].message.content or "{}"
                text = raw.strip()
                if text.startswith("```"):
                    lines = text.splitlines()
                    text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
                data = json.loads(text)
                return schema(**data)
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.warning(
                        "Together structured generation attempt %d failed, retrying in %ds: %s",
                        attempt + 1,
                        sleep_time,
                        exc,
                    )
                    await asyncio.sleep(sleep_time)

        raise RuntimeError(
            f"Together structured generation failed after {self.max_retries} attempts: {last_error}"
        )
