from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

RESEARCH_USE_DISCLAIMER = (
    "This tool is intended for authorized security research and red-teaming purposes only. "
    "Use of this tool to generate attacks against systems without explicit authorization "
    "is strictly prohibited. Users are responsible for ensuring compliance with all applicable "
    "laws, regulations, and organizational policies. By using this tool, you acknowledge "
    "that you have proper authorization and accept full responsibility for your actions."
)

_API_KEY_PATTERN = re.compile(
    r"(sk-[a-zA-Z0-9]{10,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"ghp_[a-zA-Z0-9]{36}|"
    r"xox[bporas]-[a-zA-Z0-9\-]+)",
    re.IGNORECASE,
)

_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

_PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
)


class RedactionLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"


def redact_content(text: str, level: RedactionLevel = RedactionLevel.BASIC) -> str:
    """Apply redaction based on the configured level.

    - NONE: no redaction.
    - BASIC: redact API keys and obvious credentials.
    - STRICT: also redact emails, phone numbers, and other PII patterns.
    """
    if level == RedactionLevel.NONE:
        return text

    result = _API_KEY_PATTERN.sub("[REDACTED_KEY]", text)

    if level == RedactionLevel.STRICT:
        result = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", result)
        result = _PHONE_PATTERN.sub("[REDACTED_PHONE]", result)

    return result


def validate_research_acknowledgment(acknowledged: bool) -> None:
    """Raise if the user has not acknowledged the research-use disclaimer."""
    if not acknowledged:
        raise PermissionError(
            "You must acknowledge the research-use disclaimer before running attacks. "
            "This tool is for authorized security research only."
        )


def sanitize_api_key_for_logging(key: Optional[str]) -> str:
    """Return a masked version of an API key safe for log output."""
    if not key or len(key) < 8:
        return "***"
    return key[:4] + "..." + key[-4:]
