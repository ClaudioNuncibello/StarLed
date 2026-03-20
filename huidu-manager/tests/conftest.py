"""Fixture condivise per la suite di test.

Fornisce:
- mock delle variabili d'ambiente Huidu
- una Presentation di esempio (aggiornata quando TASK-02 è completato)
"""

from __future__ import annotations

import os
import pytest


# ---------------------------------------------------------------------------
# Fixture: variabili d'ambiente mock
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=False)
def env_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Imposta variabili d'ambiente di test per tutti i moduli che usano .env."""
    monkeypatch.setenv("HUIDU_SDK_KEY", "test_sdk_key_0000000000")
    monkeypatch.setenv("HUIDU_SDK_SECRET", "test_sdk_secret_000000")
    monkeypatch.setenv("HUIDU_GATEWAY_HOST", "127.0.0.1")
    monkeypatch.setenv("HUIDU_GATEWAY_PORT", "30080")
    monkeypatch.setenv("LICENSE_SERVER_URL", "http://localhost:9999/api/verify")
    monkeypatch.setenv("LICENSE_SERVER_TIMEOUT", "5")
    monkeypatch.setenv("APP_NAME", "Huidu Manager Test")
    monkeypatch.setenv("APP_VERSION", "0.0.1-test")
    monkeypatch.setenv("DEBUG", "true")


# ---------------------------------------------------------------------------
# Fixture: presentation di esempio (dizionario grezzo)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_presentation_dict() -> dict:
    """Restituisce un dizionario che rappresenta una presentazione minimale.

    Struttura compatibile con docs/PRESENTATION_FORMAT.md.
    Aggiornare quando TASK-02 (presentation_model.py) è completato.
    """
    return {
        "uuid": "test-uuid-1234",
        "name": "Presentazione di test",
        "areas": [
            {
                "uuid": "area-uuid-0001",
                "x": 0,
                "y": 0,
                "width": 128,
                "height": 32,
                "items": [
                    {
                        "type": "text",
                        "uuid": "item-uuid-0001",
                        "text": "Hello LED",
                        "font_size": 16,
                        "color": "#ffffff",
                        "effect": "scroll_left",
                        "speed": 30,
                    }
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Fixture: gateway URL di test
# ---------------------------------------------------------------------------

@pytest.fixture
def gateway_base_url() -> str:
    """URL base del gateway Huidu in ambiente di test."""
    return "http://127.0.0.1:30080"
