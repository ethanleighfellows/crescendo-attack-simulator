from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.backend.config.presets import PRESETS, PresetName, get_preset
from src.backend.config.settings import Settings
from src.backend.engine.crescendo import CrescendoEngine
from src.backend.engine.types import RunConfig, RunResult, RunStatus
from src.backend.export.schemas import ExportConfig
from src.backend.export.xlsx import export_to_xlsx
from src.backend.providers.base import BaseProvider
from src.backend.safety.guardrails import (
    RESEARCH_USE_DISCLAIMER,
    validate_research_acknowledgment,
)

router = APIRouter()

_active_runs: dict[str, CrescendoEngine] = {}
_run_results: dict[str, RunResult] = {}
_run_tasks: dict[str, asyncio.Task[None]] = {}
_settings = Settings()


class StartRunRequest(BaseModel):
    config: RunConfig
    research_acknowledged: bool = False


class StartRunResponse(BaseModel):
    run_id: str
    status: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    outcome: Optional[str] = None
    total_rounds: int = 0
    total_backtracks: int = 0
    final_eval_score: Optional[int] = None
    error: Optional[str] = None


@router.get("/disclaimer")
async def get_disclaimer() -> dict[str, str]:
    return {"disclaimer": RESEARCH_USE_DISCLAIMER}


@router.get("/presets")
async def list_presets() -> dict[str, Any]:
    return {name.value: preset for name, preset in PRESETS.items()}


@router.get("/presets/{name}")
async def get_preset_config(name: PresetName) -> dict[str, Any]:
    try:
        return get_preset(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/attacks/turn-level")
async def list_turn_level_attacks() -> dict[str, list[str]]:
    from src.backend.engine.crescendo import TURN_LEVEL_ATTACK_MAP

    return {"available": list(TURN_LEVEL_ATTACK_MAP.keys())}


@router.post("/runs", response_model=StartRunResponse)
async def start_run(request: StartRunRequest) -> StartRunResponse:
    validate_research_acknowledgment(request.research_acknowledged)

    cfg = request.config
    simulator = _build_provider(
        cfg.simulator_provider,
        cfg.simulator_model,
        cfg.simulator_api_key,
        cfg.simulator_base_url,
        cfg.temperature,
        cfg.max_retries,
    )
    target = _build_provider(
        cfg.target_provider,
        cfg.target_model,
        cfg.target_api_key,
        cfg.target_base_url,
        cfg.temperature,
        cfg.max_retries,
    )

    engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)
    run_id = engine.run_id
    _active_runs[run_id] = engine

    async def _execute() -> None:
        result: Optional[RunResult] = None
        async for event in engine.run():
            if event.event_type == "run_completed":
                result = RunResult(**event.data["result"])
        if result:
            _run_results[run_id] = result
        if run_id in _active_runs:
            del _active_runs[run_id]

    task = asyncio.create_task(_execute())
    _run_tasks[run_id] = task

    return StartRunResponse(run_id=run_id, status=RunStatus.RUNNING.value)


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run_status(run_id: str) -> RunStatusResponse:
    if run_id in _run_results:
        r = _run_results[run_id]
        return RunStatusResponse(
            run_id=run_id,
            status=r.status.value,
            outcome=r.outcome.value if r.outcome else None,
            total_rounds=r.total_rounds,
            total_backtracks=r.total_backtracks,
            final_eval_score=r.final_eval_score,
            error=r.error,
        )
    if run_id in _active_runs:
        return RunStatusResponse(run_id=run_id, status=RunStatus.RUNNING.value)
    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


@router.get("/runs/{run_id}/result")
async def get_run_result(run_id: str) -> dict[str, Any]:
    if run_id not in _run_results:
        raise HTTPException(status_code=404, detail=f"No result for run {run_id}")
    return _run_results[run_id].model_dump(mode="json")


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str) -> dict[str, str]:
    if run_id not in _active_runs:
        raise HTTPException(status_code=404, detail=f"No active run {run_id}")
    _active_runs[run_id].cancel()
    return {"status": "cancelling"}


@router.post("/runs/{run_id}/pause")
async def pause_run(run_id: str) -> dict[str, str]:
    if run_id not in _active_runs:
        raise HTTPException(status_code=404, detail=f"No active run {run_id}")
    _active_runs[run_id].pause()
    return {"status": "pausing"}


@router.post("/runs/{run_id}/resume")
async def resume_run(run_id: str) -> dict[str, str]:
    if run_id not in _active_runs:
        raise HTTPException(status_code=404, detail=f"No active run {run_id}")
    _active_runs[run_id].resume()
    return {"status": "resuming"}


@router.post("/runs/{run_id}/export")
async def export_run(run_id: str, export_config: ExportConfig) -> dict[str, str]:
    if run_id not in _run_results:
        raise HTTPException(status_code=404, detail=f"No result for run {run_id}")

    import base64

    result = _run_results[run_id]
    xlsx_bytes = export_to_xlsx(result, export_config)
    encoded = base64.b64encode(xlsx_bytes).decode("utf-8")
    return {
        "filename": f"{export_config.filename}.xlsx",
        "data": encoded,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }


def _build_provider(
    provider_name: str,
    model: str,
    api_key: Optional[str],
    base_url: Optional[str],
    temperature: float,
    max_retries: int,
) -> BaseProvider:
    from src.backend.providers.anthropic_provider import AnthropicProvider
    from src.backend.providers.ollama_provider import OllamaProvider
    from src.backend.providers.openai_provider import OpenAIProvider
    from src.backend.providers.together_provider import TogetherAIProvider

    providers = {
        "openai": OpenAIProvider,
        "azure": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "together": TogetherAIProvider,
    }

    cls = providers.get(provider_name.lower())
    if cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {provider_name}. Available: {list(providers.keys())}",
        )

    resolved_api_key = api_key or _resolve_default_api_key(provider_name.lower())

    return cls(
        model=model,
        api_key=resolved_api_key,
        base_url=base_url,
        temperature=temperature,
        max_retries=max_retries,
    )


def _resolve_default_api_key(provider_name: str) -> Optional[str]:
    if provider_name in {"openai", "azure"}:
        return _settings.openai_api_key
    if provider_name == "anthropic":
        return _settings.anthropic_api_key
    if provider_name == "together":
        return _settings.together_api_key
    return None
