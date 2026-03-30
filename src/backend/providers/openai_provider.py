from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Optional

from pydantic import BaseModel

from src.backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)


def _is_non_retryable_openai(exc: Exception) -> bool:
    """Return True for OpenAI errors that will fail identically on every retry."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status in (400, 401, 403):
        return True
    msg = str(exc)
    if re.search(
        r"context.length|maximum.context.length|token.limit|"
        r"authentication|unauthorized|forbidden|invalid.api.key",
        msg,
        re.IGNORECASE,
    ):
        return True
    return False


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI and Azure OpenAI compatible APIs."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> None:
        super().__init__(model, api_key, base_url, temperature, max_retries)
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def _get_client(self) -> Any:
        from openai import AsyncOpenAI

        kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return AsyncOpenAI(**kwargs)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        client = self._get_client()
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                last_error = exc
                if _is_non_retryable_openai(exc):
                    logger.error("OpenAI generation hit non-retryable error: %s", exc)
                    break
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.warning(
                        "OpenAI generation attempt %d failed, retrying in %ds: %s",
                        attempt + 1,
                        sleep_time,
                        exc,
                    )
                    await asyncio.sleep(sleep_time)

        raise RuntimeError(
            f"OpenAI generation failed after {self.max_retries} attempts: {last_error}"
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
        messages.append({"role": "user", "content": prompt})

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or "{}"
                data = json.loads(raw)
                return schema(**data)
            except Exception as exc:
                last_error = exc
                if _is_non_retryable_openai(exc):
                    logger.error("OpenAI structured generation hit non-retryable error: %s", exc)
                    break
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.warning(
                        "OpenAI structured generation attempt %d failed, retrying in %ds: %s",
                        attempt + 1,
                        sleep_time,
                        exc,
                    )
                    await asyncio.sleep(sleep_time)

        raise RuntimeError(
            f"OpenAI structured generation failed after {self.max_retries} attempts: {last_error}"
        )

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception:
            return False
