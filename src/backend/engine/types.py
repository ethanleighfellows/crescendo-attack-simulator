from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Outcome(str, Enum):
    SUCCESS = "success"
    MAX_ROUNDS = "max_rounds"
    MAX_BACKTRACKS = "max_backtracks"
    CANCELLED = "cancelled"
    FAILED = "failed"


class JudgeDecision(BaseModel):
    value: bool
    rationale: str
    metadata: int
    description: Optional[str] = None


class TurnRecord(BaseModel):
    round_number: int
    backtrack_count: int
    user_prompt: str
    assistant_response: str
    turn_level_attack: Optional[str] = None
    enhancement_applied: bool = False
    refusal_decision: Optional[JudgeDecision] = None
    eval_decision: Optional[JudgeDecision] = None
    is_backtrack: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RunConfig(BaseModel):
    objective: str
    vulnerability: str = ""
    vulnerability_type: str = ""
    initial_prompt: Optional[str] = None
    system_prompt_override: Optional[str] = None

    max_rounds: int = 10
    max_backtracks: int = 10
    enhancement_probability: float = 0.5
    success_threshold: int = 100
    stop_on_first_success: bool = True
    turn_level_attacks: list[str] = Field(default_factory=list)

    simulator_provider: str = "together"
    simulator_model: str = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
    simulator_api_key: Optional[str] = None
    simulator_base_url: Optional[str] = None

    target_provider: str = "together"
    target_model: str = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
    target_api_key: Optional[str] = None
    target_base_url: Optional[str] = None

    temperature: float = 0.7
    max_retries: int = 3


class RunResult(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    config: RunConfig
    status: RunStatus = RunStatus.PENDING
    outcome: Optional[Outcome] = None
    turns: list[TurnRecord] = Field(default_factory=list)
    total_rounds: int = 0
    total_backtracks: int = 0
    final_eval_score: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class TurnEvent(BaseModel):
    """Real-time event emitted during a run for WebSocket streaming."""
    event_type: str
    run_id: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
