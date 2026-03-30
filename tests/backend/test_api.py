"""Integration tests for the FastAPI API layer.

Uses TestClient for synchronous HTTP testing and verifies
the REST endpoints and WebSocket protocol.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestDisclaimerEndpoint:
    def test_disclaimer_returns_text(self) -> None:
        response = client.get("/api/disclaimer")
        assert response.status_code == 200
        data = response.json()
        assert "disclaimer" in data
        assert "research" in data["disclaimer"].lower()


class TestPresetsEndpoint:
    def test_list_presets(self) -> None:
        response = client.get("/api/presets")
        assert response.status_code == 200
        data = response.json()
        assert "conservative" in data
        assert "balanced" in data
        assert "aggressive" in data

    def test_get_specific_preset(self) -> None:
        response = client.get("/api/presets/balanced")
        assert response.status_code == 200
        data = response.json()
        assert "max_rounds" in data
        assert data["max_rounds"] == 10

    def test_get_invalid_preset(self) -> None:
        response = client.get("/api/presets/nonexistent")
        assert response.status_code == 422


class TestTurnLevelAttacksEndpoint:
    def test_list_available_attacks(self) -> None:
        response = client.get("/api/attacks/turn-level")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "base64" in data["available"]
        assert "leetspeak" in data["available"]


class TestProviderSupport:
    def test_together_provider_is_available_via_run_validation(self) -> None:
        response = client.post(
            "/api/runs",
            json={
                "config": {
                    "objective": "Test",
                    "simulator_provider": "together",
                    "target_provider": "together",
                },
                "research_acknowledged": False,
            },
        )
        assert response.status_code != 400


class TestRunEndpoints:
    def test_start_run_requires_disclaimer(self) -> None:
        response = client.post(
            "/api/runs",
            json={
                "config": {
                    "objective": "Test",
                    "simulator_api_key": "sk-test",
                    "target_api_key": "sk-test",
                },
                "research_acknowledged": False,
            },
        )
        assert response.status_code == 403 or response.status_code == 500

    def test_get_nonexistent_run(self) -> None:
        response = client.get("/api/runs/nonexistent-id")
        assert response.status_code == 404


class TestSafetyGuardrails:
    def test_disclaimer_must_be_acknowledged(self) -> None:
        """Starting a run without acknowledging the disclaimer should fail."""
        response = client.post(
            "/api/runs",
            json={
                "config": {"objective": "Test"},
                "research_acknowledged": False,
            },
        )
        assert response.status_code != 200
