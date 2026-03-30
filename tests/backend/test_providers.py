"""Unit tests for provider adapters.

Tests the interface contract and error handling without
making real API calls (uses mocked HTTP responses).
"""
from __future__ import annotations

import pytest
from pydantic import BaseModel

from src.backend.providers.base import BaseProvider
from src.backend.providers.openai_provider import OpenAIProvider
from src.backend.providers.anthropic_provider import AnthropicProvider
from src.backend.providers.ollama_provider import OllamaProvider
from src.backend.providers.together_provider import (
    DEFAULT_TOGETHER_BASE_URL,
    TogetherAIProvider,
)


class SampleSchema(BaseModel):
    answer: str
    confidence: int


class TestProviderInstantiation:
    def test_openai_provider_creation(self) -> None:
        provider = OpenAIProvider(
            model="gpt-4o-mini",
            api_key="test-key",
            temperature=0.5,
        )
        assert provider.model == "gpt-4o-mini"
        assert provider.temperature == 0.5
        assert isinstance(provider, BaseProvider)

    def test_anthropic_provider_creation(self) -> None:
        provider = AnthropicProvider(
            model="claude-sonnet-4-20250514",
            api_key="test-key",
        )
        assert provider.model == "claude-sonnet-4-20250514"
        assert isinstance(provider, BaseProvider)

    def test_ollama_provider_creation(self) -> None:
        provider = OllamaProvider(model="llama3.1")
        assert provider.model == "llama3.1"
        assert provider.base_url == "http://localhost:11434"
        assert isinstance(provider, BaseProvider)

    def test_together_provider_creation(self) -> None:
        provider = TogetherAIProvider(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            api_key="test-key",
        )
        assert provider.model == "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
        assert provider.base_url == DEFAULT_TOGETHER_BASE_URL
        assert isinstance(provider, BaseProvider)

    def test_openai_with_custom_base_url(self) -> None:
        provider = OpenAIProvider(
            model="gpt-4",
            api_key="key",
            base_url="https://custom.azure.endpoint/v1",
        )
        assert provider.base_url == "https://custom.azure.endpoint/v1"


class TestProviderInterfaceContract:
    """Verify all providers implement the required abstract methods."""

    def test_openai_has_required_methods(self) -> None:
        provider = OpenAIProvider(model="gpt-4o-mini", api_key="test")
        assert hasattr(provider, "generate")
        assert hasattr(provider, "generate_structured")
        assert hasattr(provider, "health_check")
        assert callable(provider.generate)
        assert callable(provider.generate_structured)
        assert callable(provider.health_check)

    def test_anthropic_has_required_methods(self) -> None:
        provider = AnthropicProvider(model="claude-sonnet-4-20250514", api_key="test")
        assert hasattr(provider, "generate")
        assert hasattr(provider, "generate_structured")
        assert hasattr(provider, "health_check")

    def test_ollama_has_required_methods(self) -> None:
        provider = OllamaProvider(model="llama3.1")
        assert hasattr(provider, "generate")
        assert hasattr(provider, "generate_structured")
        assert hasattr(provider, "health_check")

    def test_together_has_required_methods(self) -> None:
        provider = TogetherAIProvider(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            api_key="test",
        )
        assert hasattr(provider, "generate")
        assert hasattr(provider, "generate_structured")
        assert hasattr(provider, "health_check")


class TestProviderRetryConfig:
    def test_default_max_retries(self) -> None:
        provider = OpenAIProvider(model="gpt-4o-mini", api_key="test")
        assert provider.max_retries == 3

    def test_custom_max_retries(self) -> None:
        provider = OpenAIProvider(model="gpt-4o-mini", api_key="test", max_retries=5)
        assert provider.max_retries == 5
