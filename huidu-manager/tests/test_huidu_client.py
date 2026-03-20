"""Test unitari per app/api/huidu_client.py — TASK-P1 / TASK-01.

Tutti i test usano unittest.mock per simulare requests HTTP,
senza mai aprire connessioni di rete reali.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.api.huidu_client import HuiduApiError, HuiduClient


# ---------------------------------------------------------------------------
# Costanti e fixture
# ---------------------------------------------------------------------------

HOST = "127.0.0.1"
PORT = 30080
SDK_KEY = "testSdkKey12345"
SDK_SECRET = "testSdkSecret999"


@pytest.fixture
def client() -> HuiduClient:
    """Restituisce un HuiduClient di test (non apre connessioni reali)."""
    return HuiduClient(host=HOST, port=PORT, sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)


def _mock_response(
    json_data: dict,
    status_code: int = 200,
    ok: bool = True,
) -> MagicMock:
    """Costruisce un MagicMock che simula una requests.Response."""
    mock = MagicMock()
    mock.ok = ok
    mock.status_code = status_code
    mock.url = f"http://{HOST}:{PORT}/test"
    mock.content = json.dumps(json_data).encode()
    mock.json.return_value = json_data
    mock.text = json.dumps(json_data)
    return mock


# ---------------------------------------------------------------------------
# Test HuiduApiError
# ---------------------------------------------------------------------------


class TestHuiduApiError:
    """Verifica il comportamento dell'eccezione custom."""

    def test_eredita_da_exception(self) -> None:
        """HuiduApiError deve essere una Exception."""
        err = HuiduApiError("errore", 500)
        assert isinstance(err, Exception)

    def test_attributi(self) -> None:
        """message e status_code devono essere accessibili."""
        err = HuiduApiError("gateway irraggiungibile", 0)
        assert err.message == "gateway irraggiungibile"
        assert err.status_code == 0

    def test_status_code_default(self) -> None:
        """status_code default deve essere 0 (errore di rete)."""
        err = HuiduApiError("timeout")
        assert err.status_code == 0

    def test_str_leggibile(self) -> None:
        """str(err) deve restituire il messaggio."""
        err = HuiduApiError("messaggio di errore", 404)
        assert "messaggio di errore" in str(err)


# ---------------------------------------------------------------------------
# Test HuiduClient.__init__
# ---------------------------------------------------------------------------


class TestHuiduClientInit:
    """Verifica la costruzione del client."""

    def test_costruzione_valida(self) -> None:
        """Non deve sollevare eccezioni con parametri validi."""
        c = HuiduClient(host=HOST, port=PORT, sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)
        assert c is not None

    def test_host_vuoto_solleva(self) -> None:
        """Host vuoto deve sollevare ValueError."""
        with pytest.raises(ValueError, match="host"):
            HuiduClient(host="", port=PORT, sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)

    def test_base_url_costruito(self) -> None:
        """L'URL base deve essere composto da host e porta."""
        c = HuiduClient(host="192.168.1.10", port=30080, sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)
        assert c._base_url == "http://192.168.1.10:30080"


# ---------------------------------------------------------------------------
# Test HuiduClient.get
# ---------------------------------------------------------------------------


class TestHuiduClientGet:
    """Verifica il metodo GET."""

    @patch("app.api.huidu_client.requests.get")
    def test_get_successo(self, mock_get: MagicMock, client: HuiduClient) -> None:
        """GET con risposta ok deve restituire il dizionario JSON."""
        payload = {"message": "ok", "data": ["C16-D00-A000F"], "total": "1"}
        mock_get.return_value = _mock_response(payload)

        result = client.get("/api/device/list/")

        assert result == payload
        mock_get.assert_called_once()

    @patch("app.api.huidu_client.requests.get")
    def test_get_invia_header_coretti(self, mock_get: MagicMock, client: HuiduClient) -> None:
        """GET deve inviare sdkKey, date, sign, requestId negli header."""
        mock_get.return_value = _mock_response({"message": "ok", "data": []})

        client.get("/api/device/list/")

        _, kwargs = mock_get.call_args
        headers = kwargs["headers"]
        for chiave in ("sdkKey", "date", "sign", "requestId"):
            assert chiave in headers, f"Header mancante: {chiave}"

    @patch("app.api.huidu_client.requests.get")
    def test_get_errore_http(self, mock_get: MagicMock, client: HuiduClient) -> None:
        """GET con HTTP 500 deve sollevare HuiduApiError."""
        mock_get.return_value = _mock_response({"message": "error"}, status_code=500, ok=False)

        with pytest.raises(HuiduApiError) as exc_info:
            client.get("/api/device/list/")
        assert exc_info.value.status_code == 500

    @patch("app.api.huidu_client.requests.get")
    def test_get_message_non_ok(self, mock_get: MagicMock, client: HuiduClient) -> None:
        """GET con message != 'ok' deve sollevare HuiduApiError."""
        mock_get.return_value = _mock_response({"message": "device not found"})

        with pytest.raises(HuiduApiError, match="device not found"):
            client.get("/api/device/list/")

    @patch("app.api.huidu_client.requests.get")
    def test_get_errore_connessione(self, mock_get: MagicMock, client: HuiduClient) -> None:
        """Errore di connessione deve sollevare HuiduApiError con status_code=0."""
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.ConnectionError("refused")

        with pytest.raises(HuiduApiError) as exc_info:
            client.get("/api/device/list/")
        assert exc_info.value.status_code == 0

    @patch("app.api.huidu_client.requests.get")
    def test_get_timeout(self, mock_get: MagicMock, client: HuiduClient) -> None:
        """Timeout deve sollevare HuiduApiError con status_code=0."""
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout("timeout")

        with pytest.raises(HuiduApiError) as exc_info:
            client.get("/api/device/list/")
        assert exc_info.value.status_code == 0

    @patch("app.api.huidu_client.requests.get")
    def test_get_risposta_non_json(self, mock_get: MagicMock, client: HuiduClient) -> None:
        """Risposta non JSON deve sollevare HuiduApiError."""
        mock = MagicMock()
        mock.ok = True
        mock.status_code = 200
        mock.url = "http://test"
        mock.content = b"not json"
        mock.text = "not json"
        mock.json.side_effect = ValueError("not json")
        mock_get.return_value = mock

        with pytest.raises(HuiduApiError):
            client.get("/api/device/list/")


# ---------------------------------------------------------------------------
# Test HuiduClient.post
# ---------------------------------------------------------------------------


class TestHuiduClientPost:
    """Verifica il metodo POST."""

    @patch("app.api.huidu_client.requests.post")
    def test_post_successo(self, mock_post: MagicMock, client: HuiduClient) -> None:
        """POST con risposta ok deve restituire il dizionario JSON."""
        payload = {"message": "ok", "data": [{"id": "C16-D00-A000F", "message": "ok"}]}
        mock_post.return_value = _mock_response(payload)

        result = client.post("/api/device/C16-D00-A000F", {"method": "getDeviceStatus", "data": []})

        assert result == payload

    @patch("app.api.huidu_client.requests.post")
    def test_post_serializza_body(self, mock_post: MagicMock, client: HuiduClient) -> None:
        """POST deve trasmettere il body come JSON serializzato."""
        mock_post.return_value = _mock_response({"message": "ok"})
        body = {"method": "getAll", "data": []}

        client.post("/api/program/", body)

        _, kwargs = mock_post.call_args
        inviato = json.loads(kwargs["data"])
        assert inviato == body

    @patch("app.api.huidu_client.requests.post")
    def test_post_header_nuovo_ogni_chiamata(
        self, mock_post: MagicMock, client: HuiduClient
    ) -> None:
        """Ogni POST deve usare un dizionario header distinto (thread-safety)."""
        mock_post.return_value = _mock_response({"message": "ok"})

        client.post("/api/device/D1", {"method": "getAll"})
        client.post("/api/device/D2", {"method": "getAll"})

        call1_headers = mock_post.call_args_list[0][1]["headers"]
        call2_headers = mock_post.call_args_list[1][1]["headers"]
        # Devono essere dizionari distinti (non lo stesso oggetto)
        assert call1_headers is not call2_headers

    @patch("app.api.huidu_client.requests.post")
    def test_post_errore_connessione(self, mock_post: MagicMock, client: HuiduClient) -> None:
        """Errore di connessione POST deve sollevare HuiduApiError."""
        import requests as req_lib
        mock_post.side_effect = req_lib.exceptions.ConnectionError("refused")

        with pytest.raises(HuiduApiError) as exc_info:
            client.post("/api/device/D1", {})
        assert exc_info.value.status_code == 0

    @patch("app.api.huidu_client.requests.post")
    def test_post_errore_http_404(self, mock_post: MagicMock, client: HuiduClient) -> None:
        """POST HTTP 404 deve sollevare HuiduApiError con status_code=404."""
        mock_post.return_value = _mock_response({"message": "not found"}, status_code=404, ok=False)

        with pytest.raises(HuiduApiError) as exc_info:
            client.post("/api/device/inesistente", {})
        assert exc_info.value.status_code == 404
