"""Unit tests for configuration presets."""
from __future__ import annotations

import pytest

from src.backend.config.presets import PRESETS, PresetName, get_preset
from src.backend.engine.types import RunConfig


class TestPresets:
    def test_all_presets_exist(self) -> None:
        for name in PresetName:
            assert name in PRESETS

    def test_conservative_preset_values(self) -> None:
        preset = get_preset(PresetName.CONSERVATIVE)
        assert preset["max_rounds"] == 5
        assert preset["max_backtracks"] == 3
        assert preset["enhancement_probability"] == 0.0
        assert preset["turn_level_attacks"] == []

    def test_balanced_preset_values(self) -> None:
        preset = get_preset(PresetName.BALANCED)
        assert preset["max_rounds"] == 10
        assert preset["max_backtracks"] == 10
        assert preset["enhancement_probability"] == 0.5

    def test_aggressive_preset_values(self) -> None:
        preset = get_preset(PresetName.AGGRESSIVE)
        assert preset["max_rounds"] == 30
        assert preset["max_backtracks"] == 20
        assert preset["enhancement_probability"] == 0.8
        assert preset["success_threshold"] == 80
        assert len(preset["turn_level_attacks"]) > 0

    def test_presets_produce_valid_run_config(self) -> None:
        """Every preset should be mergeable into a valid RunConfig."""
        for name in PresetName:
            preset = get_preset(name)
            config = RunConfig(
                objective="Test objective",
                **preset,
            )
            assert config.max_rounds > 0
            assert config.max_backtracks >= 0

    def test_get_preset_returns_copy(self) -> None:
        """Mutating the returned preset should not affect the original."""
        preset1 = get_preset(PresetName.BALANCED)
        preset1["max_rounds"] = 999
        preset2 = get_preset(PresetName.BALANCED)
        assert preset2["max_rounds"] == 10
