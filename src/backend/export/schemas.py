from __future__ import annotations

from pydantic import BaseModel


class ExportConfig(BaseModel):
    """Controls what gets included in the export."""
    include_api_keys: bool = False
    redact_sensitive_content: bool = False
    include_judge_rationale: bool = True
    filename: str = "crescendo_report"


SUMMARY_COLUMNS = [
    "Run ID",
    "Objective",
    "Vulnerability",
    "Vulnerability Type",
    "Outcome",
    "Total Rounds",
    "Total Backtracks",
    "Final Eval Score",
    "Started At",
    "Completed At",
    "Duration (s)",
]

CONFIG_COLUMNS = [
    "Parameter",
    "Value",
]

TRANSCRIPT_COLUMNS = [
    "Round",
    "Backtrack Count",
    "User Prompt",
    "Assistant Response",
    "Turn-Level Attack",
    "Enhancement Applied",
    "Is Backtrack",
    "Timestamp",
]

OUTCOMES_COLUMNS = [
    "Round",
    "Backtrack Count",
    "Refusal (Yes/No)",
    "Refusal Rationale",
    "Refusal Score",
    "Eval Success (Yes/No)",
    "Eval Score",
    "Eval Rationale",
    "Turn-Level Attack",
]
