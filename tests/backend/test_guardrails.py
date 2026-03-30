"""Unit tests for safety and governance guardrails."""
from __future__ import annotations

import pytest

from src.backend.safety.guardrails import (
    RedactionLevel,
    redact_content,
    sanitize_api_key_for_logging,
    validate_research_acknowledgment,
)


class TestRedaction:
    def test_no_redaction(self) -> None:
        text = "sk-abcdef1234567890abcdef"
        assert redact_content(text, RedactionLevel.NONE) == text

    def test_basic_redacts_api_keys(self) -> None:
        text = "Use key sk-abcdef1234567890abcdef1234567890"
        result = redact_content(text, RedactionLevel.BASIC)
        assert "sk-" not in result
        assert "[REDACTED_KEY]" in result

    def test_basic_does_not_redact_emails(self) -> None:
        text = "Contact user@example.com for help"
        result = redact_content(text, RedactionLevel.BASIC)
        assert "user@example.com" in result

    def test_strict_redacts_emails(self) -> None:
        text = "Contact user@example.com for help"
        result = redact_content(text, RedactionLevel.STRICT)
        assert "user@example.com" not in result
        assert "[REDACTED_EMAIL]" in result

    def test_strict_redacts_phone_numbers(self) -> None:
        text = "Call 555-123-4567 now"
        result = redact_content(text, RedactionLevel.STRICT)
        assert "555-123-4567" not in result
        assert "[REDACTED_PHONE]" in result


class TestResearchAcknowledgment:
    def test_raises_when_not_acknowledged(self) -> None:
        with pytest.raises(PermissionError, match="research-use disclaimer"):
            validate_research_acknowledgment(False)

    def test_passes_when_acknowledged(self) -> None:
        validate_research_acknowledgment(True)


class TestApiKeyMasking:
    def test_short_key(self) -> None:
        assert sanitize_api_key_for_logging("abc") == "***"

    def test_normal_key(self) -> None:
        result = sanitize_api_key_for_logging("sk-abcdef1234567890abcdef")
        assert result.startswith("sk-a")
        assert result.endswith("cdef")
        assert "..." in result

    def test_none_key(self) -> None:
        assert sanitize_api_key_for_logging(None) == "***"
