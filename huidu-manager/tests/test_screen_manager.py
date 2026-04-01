"""Test unitari per app/core/screen_manager.py — TASK-06.

Tutti i test usano unittest.mock — nessuna connessione di rete reale.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.api.device_api import DeviceApi
from app.core.screen_manager import Screen, ScreenManager


DEVICE_ID_1 = "C16-D00-A000F"
DEVICE_ID_2 = "A3L-D24-A05C1"


# ---------------------------------------------------------------------------
# Fixture comuni
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_device_api() -> MagicMock:
    return MagicMock(spec=DeviceApi)


@pytest.fixture
def manager(mock_device_api: MagicMock) -> ScreenManager:
    return ScreenManager(mock_device_api)


PROPERTY_DATA = {
    "name": "LED-01",
    "screen.width": "128",
    "screen.height": "64",
    "eth.ip": "192.168.1.50",
    "version.app": "1.2.3",
    "screen.openStatus": "true",
    "volume": "80",
    "luminance": "70",
}


# ---------------------------------------------------------------------------
# Test Screen.from_property_data
# ---------------------------------------------------------------------------


class TestScreen:
    def test_from_property_data(self) -> None:
        s = Screen.from_property_data(DEVICE_ID_1, PROPERTY_DATA)
        assert s.id == DEVICE_ID_1
        assert s.name == "LED-01"
        assert s.width == 128
        assert s.height == 64
        assert s.ip == "192.168.1.50"
        assert s.version == "1.2.3"
        assert s.open_status is True
        assert s.volume == 80
        assert s.luminance == 70

    def test_from_property_data_valori_default(self) -> None:
        s = Screen.from_property_data(DEVICE_ID_1, {})
        assert s.name == ""
        assert s.width == 0
        assert s.height == 0
        assert s.open_status is False

    def test_from_property_data_schermo_spento(self) -> None:
        data = dict(PROPERTY_DATA)
        data["screen.openStatus"] = "false"
        s = Screen.from_property_data(DEVICE_ID_1, data)
        assert s.open_status is False


# ---------------------------------------------------------------------------
# Test ScreenManager.refresh
# ---------------------------------------------------------------------------


class TestScreenManagerRefresh:
    def test_zero_dispositivi(
        self, manager: ScreenManager, mock_device_api: MagicMock
    ) -> None:
        mock_device_api.get_device_list.return_value = []
        screens = manager.refresh()
        assert screens == []
        assert manager.screens == []

    def test_un_dispositivo(
        self, manager: ScreenManager, mock_device_api: MagicMock
    ) -> None:
        mock_device_api.get_device_list.return_value = [DEVICE_ID_1]
        mock_device_api.get_device_property.return_value = PROPERTY_DATA
        screens = manager.refresh()
        assert len(screens) == 1
        assert screens[0].id == DEVICE_ID_1
        assert screens[0].width == 128

    def test_due_dispositivi(
        self, manager: ScreenManager, mock_device_api: MagicMock
    ) -> None:
        mock_device_api.get_device_list.return_value = [DEVICE_ID_1, DEVICE_ID_2]
        mock_device_api.get_device_property.return_value = PROPERTY_DATA
        screens = manager.refresh()
        assert len(screens) == 2

    def test_skip_dispositivo_con_errore(
        self, manager: ScreenManager, mock_device_api: MagicMock
    ) -> None:
        mock_device_api.get_device_list.return_value = [DEVICE_ID_1, DEVICE_ID_2]
        mock_device_api.get_device_property.side_effect = [
            PROPERTY_DATA,
            Exception("Dispositivo non raggiungibile"),
        ]
        screens = manager.refresh()
        assert len(screens) == 1
        assert screens[0].id == DEVICE_ID_1


# ---------------------------------------------------------------------------
# Test ScreenManager.get_screen
# ---------------------------------------------------------------------------


class TestScreenManagerGetScreen:
    def test_trovato(
        self, manager: ScreenManager, mock_device_api: MagicMock
    ) -> None:
        mock_device_api.get_device_list.return_value = [DEVICE_ID_1]
        mock_device_api.get_device_property.return_value = PROPERTY_DATA
        manager.refresh()
        screen = manager.get_screen(DEVICE_ID_1)
        assert screen is not None
        assert screen.id == DEVICE_ID_1

    def test_non_trovato(self, manager: ScreenManager) -> None:
        screen = manager.get_screen("INESISTENTE")
        assert screen is None
