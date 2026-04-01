"""Test unitari per app/api/file_api.py e app/core/file_uploader.py — TASK-05.

Tutti i test usano unittest.mock — nessuna connessione di rete reale.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from app.api.file_api import FileApi, FileUploadResult, compute_md5
from app.api.huidu_client import HuiduApiError, HuiduClient
from app.core.file_uploader import FileUploader


DEVICE_ID = "C16-D00-A000F"


# ---------------------------------------------------------------------------
# Test compute_md5
# ---------------------------------------------------------------------------


class TestComputeMd5:
    def test_md5_deterministico(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("ciao mondo")
        md5_1, size_1 = compute_md5(f)
        md5_2, size_2 = compute_md5(f)
        assert md5_1 == md5_2
        assert size_1 == size_2 == len("ciao mondo".encode())

    def test_md5_valore_noto(self, tmp_path: Path) -> None:
        """MD5 di stringa vuota = d41d8cd98f00b204e9800998ecf8427e"""
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        md5, size = compute_md5(f)
        assert md5 == "d41d8cd98f00b204e9800998ecf8427e"
        assert size == 0

    def test_file_non_trovato(self) -> None:
        with pytest.raises(FileNotFoundError):
            compute_md5("/path/inesistente.txt")


# ---------------------------------------------------------------------------
# Test FileApi.upload_file
# ---------------------------------------------------------------------------


class TestFileApi:
    @pytest.fixture
    def mock_client(self) -> MagicMock:
        return MagicMock(spec=HuiduClient)

    @pytest.fixture
    def file_api(self, mock_client: MagicMock) -> FileApi:
        return FileApi(mock_client)

    @pytest.fixture
    def sample_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "test_image.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        return f

    def test_upload_successo(
        self, file_api: FileApi, mock_client: MagicMock, sample_file: Path
    ) -> None:
        mock_client.post_file.return_value = {
            "data": [
                {
                    "message": "ok",
                    "name": "test_image.png",
                    "md5": "abc123",
                    "size": "108",
                    "data": "http://192.168.1.100/files/test_image.png",
                }
            ]
        }
        result = file_api.upload_file(DEVICE_ID, sample_file)
        assert isinstance(result, FileUploadResult)
        assert result.name == "test_image.png"
        assert result.md5 == "abc123"
        assert result.size == 108
        assert "test_image.png" in result.url

    def test_upload_file_non_trovato(self, file_api: FileApi) -> None:
        with pytest.raises(FileNotFoundError):
            file_api.upload_file(DEVICE_ID, "/path/inesistente.png")

    def test_upload_errore_gateway(
        self, file_api: FileApi, mock_client: MagicMock, sample_file: Path
    ) -> None:
        mock_client.post_file.return_value = {
            "data": [{"message": "kFileTooBig"}]
        }
        with pytest.raises(HuiduApiError, match="kFileTooBig"):
            file_api.upload_file(DEVICE_ID, sample_file)

    def test_upload_risposta_vuota(
        self, file_api: FileApi, mock_client: MagicMock, sample_file: Path
    ) -> None:
        mock_client.post_file.return_value = {"data": []}
        with pytest.raises(HuiduApiError, match="vuota"):
            file_api.upload_file(DEVICE_ID, sample_file)

    def test_endpoint_corretto(
        self, file_api: FileApi, mock_client: MagicMock, sample_file: Path
    ) -> None:
        mock_client.post_file.return_value = {
            "data": [{"message": "ok", "name": "f.png", "md5": "x", "size": "1", "data": ""}]
        }
        file_api.upload_file(DEVICE_ID, sample_file)
        mock_client.post_file.assert_called_once_with(
            f"/api/file/{DEVICE_ID}", str(sample_file)
        )


# ---------------------------------------------------------------------------
# Test FileUploader
# ---------------------------------------------------------------------------


class TestFileUploader:
    @pytest.fixture
    def mock_file_api(self) -> MagicMock:
        return MagicMock(spec=FileApi)

    @pytest.fixture
    def uploader(self, mock_file_api: MagicMock) -> FileUploader:
        return FileUploader(mock_file_api)

    @pytest.fixture
    def sample_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "video.mp4"
        f.write_bytes(b"\x00" * 5000)
        return f

    def test_upload_con_callback(
        self, uploader: FileUploader, mock_file_api: MagicMock, sample_file: Path
    ) -> None:
        mock_file_api.upload_file.return_value = FileUploadResult(
            name="video.mp4", md5="xyz", size=5000, url="http://test/video.mp4"
        )
        progress_calls: list[tuple[int, int]] = []
        result = uploader.upload(
            DEVICE_ID, sample_file, progress=lambda s, t: progress_calls.append((s, t))
        )
        assert result.name == "video.mp4"
        assert len(progress_calls) == 2
        assert progress_calls[0] == (0, 5000)
        assert progress_calls[1] == (5000, 5000)

    def test_upload_senza_callback(
        self, uploader: FileUploader, mock_file_api: MagicMock, sample_file: Path
    ) -> None:
        mock_file_api.upload_file.return_value = FileUploadResult(
            name="video.mp4", md5="xyz", size=5000, url=""
        )
        result = uploader.upload(DEVICE_ID, sample_file)
        assert result.name == "video.mp4"

    def test_file_non_trovato(self, uploader: FileUploader) -> None:
        with pytest.raises(FileNotFoundError):
            uploader.upload(DEVICE_ID, "/path/inesistente.mp4")
