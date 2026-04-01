"""Upload file media verso gateway Huidu con callback progresso — TASK-05.

Wrappa ``FileApi`` con logica a più alto livello:
- Callback di progresso ``Callable[[int, int], None]``
- Calcolo MD5 pre-upload

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.api.file_api import FileApi, FileUploadResult, compute_md5

logger = logging.getLogger(__name__)


class FileUploader:
    """Uploader di file media con callback di progresso.

    Example:
        >>> uploader = FileUploader(file_api)
        >>> def on_progress(sent, total):
        ...     print(f"{sent}/{total} byte")
        >>> result = uploader.upload("C16-D00-A000F", "image.png", progress=on_progress)
    """

    def __init__(self, file_api: FileApi) -> None:
        """Inizializza l'uploader con l'API file.

        Args:
            file_api: Istanza ``FileApi`` configurata.
        """
        self._file_api = file_api

    def upload(
        self,
        device_id: str,
        file_path: str | Path,
        *,
        progress: Callable[[int, int], None] | None = None,
    ) -> FileUploadResult:
        """Carica un file media con notifica di progresso.

        Args:
            device_id: ID del dispositivo destinatario.
            file_path: Percorso locale del file da caricare.
            progress: Callback opzionale ``(bytes_sent, total_bytes)``.
                Viene chiamata prima e dopo l'upload.

        Returns:
            ``FileUploadResult`` con informazioni del file caricato.

        Raises:
            HuiduApiError: Se l'upload fallisce.
            FileNotFoundError: Se il file non esiste.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")

        total_size = path.stat().st_size

        # Notifica inizio
        if progress:
            progress(0, total_size)

        # Upload effettivo
        result = self._file_api.upload_file(device_id, path)

        # Notifica completamento
        if progress:
            progress(total_size, total_size)

        logger.info(
            "FileUploader: %s caricato (%d byte) → %s",
            result.name, result.size, device_id,
        )
        return result
