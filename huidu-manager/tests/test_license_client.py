"""Test unitari per app/auth/ — TASK-03.

Copre LicenseClient, mac_helper e LicenseCache.
Tutti i test usano unittest.mock — nessuna connessione di rete reale.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.auth.license_cache import LicenseCache
from app.auth.license_client import LicenseClient, LicenseResult, LicenseStatus
from app.auth.mac_helper import get_mac_address


# ---------------------------------------------------------------------------
# Test mac_helper
# ---------------------------------------------------------------------------


class TestMacHelper:
    def test_formato_mac_address(self) -> None:
        mac = get_mac_address()
        assert len(mac) == 17
        assert mac.count(":") == 5

    def test_mac_uppercase(self) -> None:
        mac = get_mac_address()
        assert mac == mac.upper()

    def test_mac_deterministica(self) -> None:
        """Lo stesso MAC viene restituito ad ogni invocazione."""
        assert get_mac_address() == get_mac_address()


# ---------------------------------------------------------------------------
# Test LicenseCache
# ---------------------------------------------------------------------------


class TestLicenseCache:
    @pytest.fixture
    def cache_file(self, tmp_path: Path) -> Path:
        return tmp_path / "test_cache.json"

    @pytest.fixture
    def cache(self, cache_file: Path) -> LicenseCache:
        return LicenseCache(cache_file=cache_file, ttl_hours=24)

    @pytest.fixture
    def valid_result(self) -> LicenseResult:
        return LicenseResult(
            status=LicenseStatus.VALID,
            customer_name="Test User",
            expiry_date="2027-12-31",
            max_screens=5,
        )

    def test_save_e_get(self, cache: LicenseCache, valid_result: LicenseResult) -> None:
        cache.save(valid_result)
        loaded = cache.get()
        assert loaded is not None
        assert loaded.status == LicenseStatus.VALID
        assert loaded.customer_name == "Test User"
        assert loaded.max_screens == 5

    def test_get_senza_file(self, cache: LicenseCache) -> None:
        result = cache.get()
        assert result is None

    def test_cache_scaduta(
        self, cache: LicenseCache, valid_result: LicenseResult, cache_file: Path
    ) -> None:
        cache.save(valid_result)
        # Modifica cached_at per farla scadere
        data = json.loads(cache_file.read_text())
        data["cached_at"] = (datetime.now() - timedelta(hours=25)).isoformat()
        cache_file.write_text(json.dumps(data))
        result = cache.get()
        assert result is None

    def test_cache_corrotta(
        self, cache: LicenseCache, cache_file: Path
    ) -> None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("{non-json-valido")
        result = cache.get()
        assert result is None

    def test_clear(
        self, cache: LicenseCache, valid_result: LicenseResult, cache_file: Path
    ) -> None:
        cache.save(valid_result)
        assert cache_file.exists()
        cache.clear()
        assert not cache_file.exists()

    def test_clear_file_inesistente(self, cache: LicenseCache) -> None:
        # Non deve sollevare eccezione
        cache.clear()


# ---------------------------------------------------------------------------
# Test LicenseClient
# ---------------------------------------------------------------------------


class TestLicenseClient:
    @pytest.fixture
    def cache_file(self, tmp_path: Path) -> Path:
        return tmp_path / "lc_cache.json"

    @pytest.fixture
    def client(self, cache_file: Path) -> LicenseClient:
        client = LicenseClient(server_url="http://license.test/verify", timeout=5)
        client._cache = LicenseCache(cache_file=cache_file, ttl_hours=24)
        return client

    @patch("app.auth.license_client.requests.post")
    def test_verifica_valida(self, mock_post: MagicMock, client: LicenseClient) -> None:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "customer_name": "Azienda ABC",
                "expiry_date": "2027-06-30",
                "max_screens": 10,
            },
        )
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert result.status == LicenseStatus.VALID
        assert result.customer_name == "Azienda ABC"
        assert result.max_screens == 10

    @patch("app.auth.license_client.requests.post")
    def test_verifica_not_found(self, mock_post: MagicMock, client: LicenseClient) -> None:
        mock_post.return_value = MagicMock(status_code=404)
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert result.status == LicenseStatus.NOT_FOUND

    @patch("app.auth.license_client.requests.post")
    def test_verifica_expired(self, mock_post: MagicMock, client: LicenseClient) -> None:
        mock_post.return_value = MagicMock(status_code=403)
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert result.status == LicenseStatus.EXPIRED

    @patch("app.auth.license_client.requests.post")
    def test_verifica_server_error(self, mock_post: MagicMock, client: LicenseClient) -> None:
        mock_post.return_value = MagicMock(status_code=500)
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert result.status == LicenseStatus.INVALID

    @patch("app.auth.license_client.requests.post")
    def test_network_error_timeout(self, mock_post: MagicMock, client: LicenseClient) -> None:
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert result.status == LicenseStatus.NETWORK_ERROR

    @patch("app.auth.license_client.requests.post")
    def test_network_error_connection(self, mock_post: MagicMock, client: LicenseClient) -> None:
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert result.status == LicenseStatus.NETWORK_ERROR

    @patch("app.auth.license_client.requests.post")
    def test_cache_hit(self, mock_post: MagicMock, client: LicenseClient) -> None:
        """Se la cache è valida, non chiama il server."""
        # Prima chiamata → salva in cache
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"customer_name": "Cached", "expiry_date": "", "max_screens": 1},
        )
        client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert mock_post.call_count == 1

        # Seconda chiamata → usa cache
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert mock_post.call_count == 1  # Non ha fatto una seconda request
        assert result.status == LicenseStatus.VALID
        assert result.customer_name == "Cached"

    def test_server_url_non_configurato(self, tmp_path: Path) -> None:
        client = LicenseClient(server_url="", timeout=5)
        client._cache = LicenseCache(cache_file=tmp_path / "empty.json")
        result = client.verify("AA:BB:CC:DD:EE:FF", "user@test.com")
        assert result.status == LicenseStatus.SERVER_ERROR
