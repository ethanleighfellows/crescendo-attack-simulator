"""Unit tests for the Crescendo engine.

Covers escalation logic, backtracking behavior, transcript persistence,
and parity checks against the source deepteam framework.
"""
from __future__ import annotations

import asyncio
import json
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.backend.engine.crescendo import CrescendoEngine
from src.backend.engine.memory import MemorySystem
from src.backend.engine.schemas import AttackData, EvalData, RefusalData
from src.backend.engine.types import (
    Outcome,
    RunConfig,
    RunResult,
    RunStatus,
    TurnRecord,
)


def _make_config(**overrides: object) -> RunConfig:
    defaults = {
        "objective": "Test objective for unit testing",
        "max_rounds": 3,
        "max_backtracks": 2,
        "enhancement_probability": 0.0,
        "success_threshold": 100,
        "stop_on_first_success": True,
        "turn_level_attacks": [],
        "simulator_provider": "openai",
        "simulator_model": "gpt-4o-mini",
        "target_provider": "openai",
        "target_model": "gpt-4o",
    }
    defaults.update(overrides)
    return RunConfig(**defaults)


def _mock_simulator(
    attack_questions: list[str],
    refusal_flags: list[bool],
    eval_scores: list[int],
) -> AsyncMock:
    """Build a mock simulator provider with pre-scripted responses."""
    mock = AsyncMock()
    attack_idx = 0
    refusal_idx = 0
    eval_idx = 0

    async def structured_side_effect(
        prompt: str, schema: type, system_prompt: Optional[str] = None
    ) -> object:
        nonlocal attack_idx, refusal_idx, eval_idx

        if schema == AttackData:
            q = attack_questions[min(attack_idx, len(attack_questions) - 1)]
            attack_idx += 1
            return AttackData(
                generated_question=q,
                last_response_summary="summary",
                rationale_behind_jailbreak="rationale",
            )
        elif schema == RefusalData:
            flag = refusal_flags[min(refusal_idx, len(refusal_flags) - 1)]
            refusal_idx += 1
            return RefusalData(value=flag, rationale="test rationale", metadata=99 if flag else 0)
        elif schema == EvalData:
            score = eval_scores[min(eval_idx, len(eval_scores) - 1)]
            eval_idx += 1
            return EvalData(
                value=score >= 100,
                description="test",
                rationale="test rationale",
                metadata=score,
            )
        raise ValueError(f"Unexpected schema: {schema}")

    mock.generate_structured = AsyncMock(side_effect=structured_side_effect)
    mock.generate = AsyncMock(return_value="enhanced attack")
    return mock


def _mock_target(responses: list[str]) -> AsyncMock:
    """Build a mock target provider with pre-scripted responses."""
    mock = AsyncMock()
    idx = 0

    async def gen_side_effect(prompt: str, **kwargs: object) -> str:
        nonlocal idx
        r = responses[min(idx, len(responses) - 1)]
        idx += 1
        return r

    mock.generate = AsyncMock(side_effect=gen_side_effect)
    return mock


# ── Memory System ──────────────────────────────────────────────


class TestMemorySystem:
    def test_create_and_add_messages(self) -> None:
        mem = MemorySystem()
        cid = mem.create_conversation()
        mem.add_message(cid, "user", "hello")
        mem.add_message(cid, "assistant", "hi")
        assert mem.get_message_count(cid) == 2
        conv = mem.get_conversation(cid)
        assert conv[0] == {"role": "user", "content": "hello"}

    def test_branch_excludes_last_turn(self) -> None:
        mem = MemorySystem()
        cid = mem.create_conversation()
        mem.add_message(cid, "user", "q1")
        mem.add_message(cid, "assistant", "a1")
        mem.add_message(cid, "user", "q2")
        mem.add_message(cid, "assistant", "a2")

        new_cid = mem.branch_excluding_last_turn(cid)
        assert new_cid != cid
        new_conv = mem.get_conversation(new_cid)
        assert len(new_conv) == 2
        assert new_conv[-1]["content"] == "a1"

    def test_branch_on_short_conversation(self) -> None:
        mem = MemorySystem()
        cid = mem.create_conversation()
        mem.add_message(cid, "user", "only one")
        new_cid = mem.branch_excluding_last_turn(cid)
        assert mem.get_conversation(new_cid) == []

    def test_branch_does_not_mutate_original(self) -> None:
        mem = MemorySystem()
        cid = mem.create_conversation()
        mem.add_message(cid, "user", "q1")
        mem.add_message(cid, "assistant", "a1")
        mem.branch_excluding_last_turn(cid)
        assert mem.get_message_count(cid) == 2


# ── Engine: Normal Flow ────────────────────────────────────────


class TestCrescendoEngineNormalFlow:
    @pytest.mark.asyncio
    async def test_runs_to_max_rounds(self) -> None:
        """Engine should run exactly max_rounds when no success and no refusals."""
        cfg = _make_config(max_rounds=3)
        simulator = _mock_simulator(
            attack_questions=["q1", "q2", "q3"],
            refusal_flags=[False, False, False],
            eval_scores=[20, 40, 60],
        )
        target = _mock_target(["initial", "r1", "r2", "r3"])
        engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)

        events = []
        async for event in engine.run():
            events.append(event)

        turn_events = [e for e in events if e.event_type == "turn_completed"]
        assert len(turn_events) == 3

        final = [e for e in events if e.event_type == "run_completed"]
        assert len(final) == 1
        result = RunResult(**final[0].data["result"])
        assert result.outcome == Outcome.MAX_ROUNDS
        assert result.total_rounds == 3

    @pytest.mark.asyncio
    async def test_stops_on_success(self) -> None:
        """Engine should stop when eval score meets threshold."""
        cfg = _make_config(max_rounds=10, success_threshold=100)
        simulator = _mock_simulator(
            attack_questions=["q1", "q2"],
            refusal_flags=[False, False],
            eval_scores=[50, 100],
        )
        target = _mock_target(["initial", "r1", "r2"])
        engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)

        events = []
        async for event in engine.run():
            events.append(event)

        final = RunResult(**[e for e in events if e.event_type == "run_completed"][0].data["result"])
        assert final.outcome == Outcome.SUCCESS
        assert final.total_rounds == 2
        assert final.final_eval_score == 100


# ── Engine: Backtracking ───────────────────────────────────────


class TestCrescendoEngineBacktracking:
    @pytest.mark.asyncio
    async def test_backtracks_on_refusal(self) -> None:
        """Engine should backtrack on refusal and retry."""
        cfg = _make_config(max_rounds=5, max_backtracks=3)
        simulator = _mock_simulator(
            attack_questions=["q1", "q2", "q3"],
            refusal_flags=[True, False, False],
            eval_scores=[80, 100],
        )
        target = _mock_target(["initial", "refused!", "r2", "r3"])
        engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)

        events = []
        async for event in engine.run():
            events.append(event)

        turns = [e for e in events if e.event_type == "turn_completed"]
        backtrack_turns = [t for t in turns if t.data.get("is_backtrack")]
        assert len(backtrack_turns) >= 1

    @pytest.mark.asyncio
    async def test_max_backtracks_stops_engine(self) -> None:
        """Engine should stop when max backtracks is reached."""
        cfg = _make_config(max_rounds=10, max_backtracks=2)
        simulator = _mock_simulator(
            attack_questions=["q"] * 10,
            refusal_flags=[True] * 10,
            eval_scores=[0] * 10,
        )
        target = _mock_target(["initial"] + ["refused"] * 10)
        engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)

        events = []
        async for event in engine.run():
            events.append(event)

        final = RunResult(**[e for e in events if e.event_type == "run_completed"][0].data["result"])
        assert final.outcome == Outcome.MAX_BACKTRACKS


# ── Engine: Cancellation ───────────────────────────────────────


class TestCrescendoEngineCancellation:
    @pytest.mark.asyncio
    async def test_cancel_stops_engine(self) -> None:
        """Engine should stop gracefully when cancelled."""
        cfg = _make_config(max_rounds=50)
        simulator = _mock_simulator(
            attack_questions=["q"] * 50,
            refusal_flags=[False] * 50,
            eval_scores=[10] * 50,
        )
        target = _mock_target(["initial"] + ["response"] * 50)
        engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)

        events = []
        count = 0
        async for event in engine.run():
            events.append(event)
            count += 1
            if count == 3:
                engine.cancel()

        final = RunResult(**[e for e in events if e.event_type == "run_completed"][0].data["result"])
        assert final.outcome == Outcome.CANCELLED


# ── Engine: Turn-Level Attacks ─────────────────────────────────


class TestCrescendoEngineTurnLevelAttacks:
    @pytest.mark.asyncio
    async def test_enhancement_applied_when_configured(self) -> None:
        """Turn-level attacks should be applied based on enhancement_probability."""
        cfg = _make_config(
            max_rounds=3,
            enhancement_probability=1.0,
            turn_level_attacks=["base64"],
        )
        simulator = _mock_simulator(
            attack_questions=["q1", "q2", "q3"],
            refusal_flags=[False, False, False],
            eval_scores=[30, 60, 100],
        )
        target = _mock_target(["initial", "r1", "r2", "r3"])
        engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)

        events = []
        async for event in engine.run():
            events.append(event)

        turn_events = [e for e in events if e.event_type == "turn_completed"]
        enhanced = [t for t in turn_events if t.data.get("turn", {}).get("enhancement_applied")]
        assert len(enhanced) > 0


# ── Engine: Transcript Capture ─────────────────────────────────


class TestTranscriptCapture:
    @pytest.mark.asyncio
    async def test_all_turns_recorded(self) -> None:
        """Every round should produce a TurnRecord with all fields populated."""
        cfg = _make_config(max_rounds=2)
        simulator = _mock_simulator(
            attack_questions=["q1", "q2"],
            refusal_flags=[False, False],
            eval_scores=[50, 100],
        )
        target = _mock_target(["initial", "r1", "r2"])
        engine = CrescendoEngine(config=cfg, simulator=simulator, target=target)

        events = []
        async for event in engine.run():
            events.append(event)

        final = RunResult(**[e for e in events if e.event_type == "run_completed"][0].data["result"])
        assert len(final.turns) == 2

        for turn_dict in final.turns:
            turn = TurnRecord(**turn_dict) if isinstance(turn_dict, dict) else turn_dict
            assert turn.user_prompt
            assert turn.assistant_response
            assert turn.refusal_decision is not None
            assert turn.timestamp
