from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.backend.api.routes import _active_runs, _build_provider, _run_results
from src.backend.engine.crescendo import CrescendoEngine
from src.backend.engine.types import RunConfig, RunResult, RunStatus
from src.backend.safety.guardrails import validate_research_acknowledgment

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/run")
async def websocket_run(websocket: WebSocket) -> None:
    """WebSocket endpoint for running a Crescendo attack with real-time streaming.

    Client sends a JSON message with the run config, then receives
    turn-by-turn events as the attack progresses.

    Protocol:
      → Client sends: {"config": {...}, "research_acknowledged": true}
      ← Server sends: {"event_type": "run_started", ...}
      ← Server sends: {"event_type": "turn_completed", ...}  (repeated)
      ← Server sends: {"event_type": "run_completed", ...}
    """
    await websocket.accept()

    try:
        init_data = await websocket.receive_json()

        if not init_data.get("research_acknowledged", False):
            await websocket.send_json({
                "event_type": "error",
                "data": {"message": "Research use disclaimer not acknowledged"},
            })
            await websocket.close(code=4001)
            return

        cfg = RunConfig(**init_data["config"])

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
        _active_runs[engine.run_id] = engine

        async def _listen_for_commands() -> None:
            """Listen for pause/resume/cancel commands while the run is active."""
            try:
                while True:
                    msg = await websocket.receive_json()
                    command = msg.get("command")
                    if command == "cancel":
                        engine.cancel()
                    elif command == "pause":
                        engine.pause()
                    elif command == "resume":
                        engine.resume()
            except WebSocketDisconnect:
                engine.cancel()
            except Exception:
                pass

        listener_task = asyncio.create_task(_listen_for_commands())

        try:
            async for event in engine.run():
                await websocket.send_json(event.model_dump(mode="json"))

                if event.event_type == "run_completed":
                    result_data = event.data.get("result")
                    if result_data:
                        _run_results[engine.run_id] = RunResult(**result_data)
        finally:
            listener_task.cancel()
            if engine.run_id in _active_runs:
                del _active_runs[engine.run_id]

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.exception("WebSocket error")
        try:
            await websocket.send_json({
                "event_type": "error",
                "data": {"message": str(exc)},
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
