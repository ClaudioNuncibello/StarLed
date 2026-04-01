"""Test unitari per app/api/device_api.py e app/api/program_api.py — TASK-P3.

Tutti i test usano unittest.mock — nessuna connessione di rete reale.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.api.device_api import DeviceApi
from app.api.huidu_client import HuiduApiError, HuiduClient
from app.api.program_api import ProgramApi
from app.core.presentation_model import Area, Presentation, TextItem


# ---------------------------------------------------------------------------
# Fixture comuni
# ---------------------------------------------------------------------------

DEVICE_ID = "C16-D00-A000F"


@pytest.fixture
def mock_client() -> MagicMock:
    """Mock di HuiduClient — non fa chiamate HTTP reali."""
    return MagicMock(spec=HuiduClient)


@pytest.fixture
def device_api(mock_client: MagicMock) -> DeviceApi:
    return DeviceApi(mock_client)


@pytest.fixture
def program_api(mock_client: MagicMock) -> ProgramApi:
    return ProgramApi(mock_client)


@pytest.fixture
def simple_presentation() -> Presentation:
    return Presentation.simple_text("Test CLI", "Hello LED")


# ---------------------------------------------------------------------------
# Test DeviceApi.get_device_list
# ---------------------------------------------------------------------------


class TestGetDeviceList:
    def test_lista_dispositivi(self, device_api: DeviceApi, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "message": "ok",
            "data": [DEVICE_ID],
            "total": "1",
        }
        result = device_api.get_device_list()
        assert result == [DEVICE_ID]

    def test_lista_vuota(self, device_api: DeviceApi, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"message": "ok", "data": [], "total": "0"}
        result = device_api.get_device_list()
        assert result == []

    def test_chiama_endpoint_corretto(self, device_api: DeviceApi, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"message": "ok", "data": []}
        device_api.get_device_list()
        mock_client.get.assert_called_once_with("/api/device/list/")

    def test_data_non_lista_restituisce_vuota(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"message": "ok", "data": None}
        result = device_api.get_device_list()
        assert result == []


# ---------------------------------------------------------------------------
# Test DeviceApi.get_device_status
# ---------------------------------------------------------------------------


class TestGetDeviceStatus:
    def _risposta_ok(self, data_fields: dict) -> dict:
        return {
            "message": "ok",
            "data": [{"id": DEVICE_ID, "message": "ok", "data": data_fields}],
        }

    def test_stato_acceso(self, device_api: DeviceApi, mock_client: MagicMock) -> None:
        mock_client.post.return_value = self._risposta_ok(
            {"screen.openStatus": "true", "eth.ip": "192.168.1.100"}
        )
        status = device_api.get_device_status(DEVICE_ID)
        assert status["screen.openStatus"] == "true"
        assert status["eth.ip"] == "192.168.1.100"

    def test_chiama_endpoint_e_metodo_corretti(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = self._risposta_ok({})
        device_api.get_device_status(DEVICE_ID)
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert f"/api/device/{DEVICE_ID}" in call_args[0][0]
        assert call_args[0][1]["method"] == "getDeviceStatus"

    def test_errore_dispositivo_solleva(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "message": "ok",
            "data": [{"id": DEVICE_ID, "message": "device offline"}],
        }
        with pytest.raises(HuiduApiError):
            device_api.get_device_status(DEVICE_ID)


# ---------------------------------------------------------------------------
# Test DeviceApi.open_screen / close_screen
# ---------------------------------------------------------------------------


class TestOpenCloseScreen:
    def _risposta_ok(self) -> dict:
        return {
            "message": "ok",
            "data": [{"id": DEVICE_ID, "message": "ok", "data": {}}],
        }

    def test_open_screen_restituisce_true(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        assert device_api.open_screen(DEVICE_ID) is True

    def test_close_screen_restituisce_true(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        assert device_api.close_screen(DEVICE_ID) is True

    def test_open_screen_metodo_corretto(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        device_api.open_screen(DEVICE_ID)
        body = mock_client.post.call_args[0][1]
        assert body["method"] == "openDeviceScreen"

    def test_close_screen_metodo_corretto(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        device_api.close_screen(DEVICE_ID)
        body = mock_client.post.call_args[0][1]
        assert body["method"] == "closeDeviceScreen"


# ---------------------------------------------------------------------------
# Test ProgramApi.send_presentation
# ---------------------------------------------------------------------------


class TestSendPresentation:
    def _risposta_ok(self) -> dict:
        return {
            "message": "ok",
            "data": [{"id": DEVICE_ID, "message": "ok"}],
        }

    def test_send_restituisce_true(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
        simple_presentation: Presentation,
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        result = program_api.send_presentation(DEVICE_ID, simple_presentation)
        assert result is True

    def test_send_chiama_endpoint_corretto(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
        simple_presentation: Presentation,
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        program_api.send_presentation(DEVICE_ID, simple_presentation)
        call_path = mock_client.post.call_args[0][0]
        assert call_path == "/api/program/"

    def test_send_metodo_replace_default(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
        simple_presentation: Presentation,
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        program_api.send_presentation(DEVICE_ID, simple_presentation)
        body = mock_client.post.call_args[0][1]
        assert body["method"] == "replace"

    def test_send_metodo_append(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
        simple_presentation: Presentation,
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        program_api.send_presentation(DEVICE_ID, simple_presentation, method="append")
        body = mock_client.post.call_args[0][1]
        assert body["method"] == "append"

    def test_send_device_id_nel_payload(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
        simple_presentation: Presentation,
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        program_api.send_presentation(DEVICE_ID, simple_presentation)
        body = mock_client.post.call_args[0][1]
        assert body["id"] == DEVICE_ID

    def test_send_data_contiene_presentazione(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
        simple_presentation: Presentation,
    ) -> None:
        mock_client.post.return_value = self._risposta_ok()
        program_api.send_presentation(DEVICE_ID, simple_presentation)
        body = mock_client.post.call_args[0][1]
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == simple_presentation.name

    def test_send_presentation_senza_aree_solleva(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
    ) -> None:
        """Presentazione senza aree deve sollevare ValueError prima del POST."""
        pres_vuota = Presentation(name="Vuota")
        with pytest.raises(ValueError):
            program_api.send_presentation(DEVICE_ID, pres_vuota)
        mock_client.post.assert_not_called()

    def test_send_errore_dispositivo_solleva(
        self,
        program_api: ProgramApi,
        mock_client: MagicMock,
        simple_presentation: Presentation,
    ) -> None:
        mock_client.post.return_value = {
            "message": "ok",
            "data": [{"id": DEVICE_ID, "message": "program error"}],
        }
        with pytest.raises(HuiduApiError):
            program_api.send_presentation(DEVICE_ID, simple_presentation)


# ---------------------------------------------------------------------------
# Test DeviceApi.get_device_property — TASK-04
# ---------------------------------------------------------------------------


class TestGetDeviceProperty:
    def test_estrae_dimensioni_e_ip(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": [
                {
                    "id": DEVICE_ID,
                    "message": "ok",
                    "data": {
                        "name": "LED-01",
                        "screen.width": "128",
                        "screen.height": "64",
                        "eth.ip": "192.168.1.50",
                        "version.app": "1.2.3",
                        "volume": "80",
                        "luminance": "70",
                    },
                }
            ]
        }
        result = device_api.get_device_property(DEVICE_ID)
        assert result["screen.width"] == "128"
        assert result["screen.height"] == "64"
        assert result["eth.ip"] == "192.168.1.50"
        assert result["name"] == "LED-01"

    def test_endpoint_e_method_corretti(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"data": [{"message": "ok", "data": {}}]}
        device_api.get_device_property(DEVICE_ID)
        mock_client.post.assert_called_once_with(
            f"/api/device/{DEVICE_ID}",
            {"method": "getDeviceProperty", "data": []},
        )


# ---------------------------------------------------------------------------
# Test DeviceApi.set_device_property — TASK-04
# ---------------------------------------------------------------------------


class TestSetDeviceProperty:
    def test_imposta_volume_luminosita(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"data": [{"message": "ok", "data": {}}]}
        result = device_api.set_device_property(
            DEVICE_ID, volume="80", luminance="70"
        )
        assert result is True
        call_args = mock_client.post.call_args
        payload = call_args[0][1]
        assert payload["method"] == "setDeviceProperty"
        assert payload["data"]["volume"] == "80"
        assert payload["data"]["luminance"] == "70"

    def test_nessuna_proprieta_solleva(self, device_api: DeviceApi) -> None:
        with pytest.raises(ValueError, match="proprietà"):
            device_api.set_device_property(DEVICE_ID)


# ---------------------------------------------------------------------------
# Test DeviceApi.reboot_device — TASK-04
# ---------------------------------------------------------------------------


class TestRebootDevice:
    def test_delay_nel_payload(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"data": [{"message": "ok", "data": {}}]}
        device_api.reboot_device(DEVICE_ID, delay=10)
        payload = mock_client.post.call_args[0][1]
        assert payload["method"] == "rebootDevice"
        assert payload["data"]["delay"] == 10

    def test_delay_default(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"data": [{"message": "ok", "data": {}}]}
        device_api.reboot_device(DEVICE_ID)
        payload = mock_client.post.call_args[0][1]
        assert payload["data"]["delay"] == 5


# ---------------------------------------------------------------------------
# Test DeviceApi.get_scheduled_task — TASK-04
# ---------------------------------------------------------------------------


class TestGetScheduledTask:
    def test_categorie_default(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": [{"message": "ok", "data": {"screen": [], "volume": [], "luminance": []}}]
        }
        device_api.get_scheduled_task(DEVICE_ID)
        payload = mock_client.post.call_args[0][1]
        assert payload["data"] == ["screen", "volume", "luminance"]

    def test_categorie_custom(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": [{"message": "ok", "data": {"screen": []}}]
        }
        device_api.get_scheduled_task(DEVICE_ID, categories=["screen"])
        payload = mock_client.post.call_args[0][1]
        assert payload["data"] == ["screen"]


# ---------------------------------------------------------------------------
# Test DeviceApi.set_scheduled_task — TASK-04
# ---------------------------------------------------------------------------


class TestSetScheduledTask:
    def test_struttura_payload(
        self, device_api: DeviceApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"data": [{"message": "ok", "data": {}}]}
        tasks = {
            "screen": [{"timeRange": "00:00:00~06:00:00", "data": "false"}],
        }
        result = device_api.set_scheduled_task(DEVICE_ID, tasks)
        assert result is True
        payload = mock_client.post.call_args[0][1]
        assert payload["method"] == "setScheduledTask"
        assert payload["data"] == tasks


# ---------------------------------------------------------------------------
# Test ProgramApi.get_programs — TASK-04
# ---------------------------------------------------------------------------


class TestGetPrograms:
    def test_lista_programmi(
        self, program_api: ProgramApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": [
                {
                    "id": DEVICE_ID,
                    "message": "ok",
                    "data": {
                        "item": [
                            {"uuid": "ABC-123", "name": "Promo Estate"},
                            {"uuid": "DEF-456", "name": "Orario"},
                        ]
                    },
                }
            ]
        }
        result = program_api.get_programs(DEVICE_ID)
        assert len(result) == 2
        assert result[0]["uuid"] == "ABC-123"

    def test_nessun_programma(
        self, program_api: ProgramApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": [{"id": DEVICE_ID, "message": "ok", "data": {"item": []}}]
        }
        result = program_api.get_programs(DEVICE_ID)
        assert result == []

    def test_verifica_method_getAll(
        self, program_api: ProgramApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": [{"id": DEVICE_ID, "message": "ok", "data": {"item": []}}]
        }
        program_api.get_programs(DEVICE_ID)
        payload = mock_client.post.call_args[0][1]
        assert payload["method"] == "getAll"


# ---------------------------------------------------------------------------
# Test ProgramApi.append_presentation — TASK-04
# ---------------------------------------------------------------------------


class TestAppendPresentation:
    def test_method_append(
        self, program_api: ProgramApi, mock_client: MagicMock, simple_presentation: Presentation
    ) -> None:
        mock_client.post.return_value = {
            "data": [{"id": DEVICE_ID, "message": "ok"}]
        }
        result = program_api.append_presentation(DEVICE_ID, simple_presentation)
        assert result is True
        payload = mock_client.post.call_args[0][1]
        assert payload["method"] == "append"


# ---------------------------------------------------------------------------
# Test ProgramApi.remove_presentation — TASK-04
# ---------------------------------------------------------------------------


class TestRemovePresentation:
    def test_rimozione_uuid(
        self, program_api: ProgramApi, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": [{"id": DEVICE_ID, "message": "ok"}]
        }
        uuids = ["ABC-123", "DEF-456"]
        result = program_api.remove_presentation(DEVICE_ID, uuids)
        assert result is True
        payload = mock_client.post.call_args[0][1]
        assert payload["method"] == "remove"
        assert len(payload["data"]) == 2
        assert payload["data"][0]["uuid"] == "ABC-123"

    def test_lista_vuota_solleva(self, program_api: ProgramApi) -> None:
        with pytest.raises(ValueError, match="UUID"):
            program_api.remove_presentation(DEVICE_ID, [])

