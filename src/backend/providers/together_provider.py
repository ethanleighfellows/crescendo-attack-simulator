from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any, Optional

from pydantic import BaseModel

from src.backend.providers.openai_provider import OpenAIProvider

DEFAULT_TOGETHER_BASE_URL = "https://api.together.xyz/v1"
MIN_USEFUL_TOKENS = 128
logger = logging.getLogger(__name__)


def _parse_context_length_error(exc: Exception) -> tuple[int, int, int] | None:
    """Extract (limit, input_tokens, max_new_tokens) from a Together token-limit error.

    Returns None if the exception is not a context-length error.
    """
    msg = str(exc)
    match = re.search(
        r"`inputs` tokens \+ `max_new_tokens` must be <= (\d+)\. "
        r"Given: (\d+) `inputs` tokens and (\d+) `max_new_tokens`",
        msg,
    )
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    if re.search(r"context.length|token.limit|max.tokens|too.many.tokens", msg, re.IGNORECASE):
        return None
    return None


def _is_non_retryable(exc: Exception) -> bool:
    """Return True for errors that will always fail with the same request."""
    msg = str(exc)
    if _parse_context_length_error(exc) is not None:
        return True
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status in (400, 401, 403, 422):
        return True
    if re.search(r"authentication|unauthorized|forbidden|invalid.api.key", msg, re.IGNORECASE):
        return True
    return False


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

    @staticmethod
    def _capped_max_tokens(exc: Exception) -> int | None:
        """If *exc* is a Together context-length error, return a reduced max_tokens that fits."""
        parsed = _parse_context_length_error(exc)
        if parsed is None:
            return None
        limit, input_tokens, _ = parsed
        available = limit - input_tokens
        if available < MIN_USEFUL_TOKENS:
            return None
        return available

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

        extra_kwargs: dict[str, Any] = {}
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    **extra_kwargs,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                last_error = exc
                capped = self._capped_max_tokens(exc)
                if capped is not None:
                    logger.warning(
                        "Together context-length exceeded; retrying with max_tokens=%d",
                        capped,
                    )
                    extra_kwargs["max_tokens"] = capped
                    continue
                if _is_non_retryable(exc):
                    logger.error("Together generation hit non-retryable error: %s", exc)
                    break
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.warning(
                        "Together generation attempt %d failed, retrying in %ds: %s",
                        attempt + 1,
                        sleep_time,
                        exc,
                    )
                    await asyncio.sleep(sleep_time)

        raise RuntimeError(
            f"Together generation failed after {self.max_retries} attempts: {last_error}"
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

        extra_kwargs: dict[str, Any] = {}
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    **extra_kwargs,
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
                capped = self._capped_max_tokens(exc)
                if capped is not None:
                    logger.warning(
                        "Together context-length exceeded; retrying with max_tokens=%d",
                        capped,
                    )
                    extra_kwargs["max_tokens"] = capped
                    continue
                if _is_non_retryable(exc):
                    logger.error(
                        "Together structured generation hit non-retryable error: %s", exc
                    )
                    break
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
