"""Upload file media verso gateway Huidu con callback progresso — TASK-05.

Wrappa ``FileApi`` con logica a più alto livello:
- Callback di progresso ``Callable[[int, int], None]``
- Calcolo MD5 pre-upload

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.api.file_api import FileApi, FileUploadResult, compute_md5

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

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
        target_size: tuple[int, int] | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> FileUploadResult:
        """Carica un file media con notifica di progresso e eventuale ridimensionamento.

        Args:
            device_id: ID del dispositivo destinatario.
            file_path: Percorso locale del file da caricare.
            target_size: Dimensione opzionale ``(width, height)`` a cui
                ridimensionare l'immagine prima dell'upload. Funziona solo
                se Pillow è installato e il file è un'immagine.
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

        # Se richiesto e se è un'immagine, la processiamo con Pillow in una cartella temp
        temp_dir: tempfile.TemporaryDirectory[str] | None = None
        actual_path = path

        if target_size and _HAS_PIL:
            ext = path.suffix.lower()
            if ext in (".png", ".jpg", ".jpeg", ".bmp"):
                logger.info("Ridimensionamento immagine %s a %s...", path.name, target_size)
                try:
                    with Image.open(path) as img:
                        # Rimuove canale alpha e converte in RGB
                        if img.mode in ("RGBA", "P", "LA"):
                            img = img.convert("RGB")
                        
                        # Ridimensionamento
                        resampled = img.resize(target_size, Image.Resampling.LANCZOS)
                        
                        # Salvataggio temporaneo
                        temp_dir = tempfile.TemporaryDirectory()
                        # Usiamo .jpg per massima compatibilità con i controller
                        new_name = path.stem + ".jpg"
                        temp_path = Path(temp_dir.name) / new_name
                        resampled.save(temp_path, format="JPEG", quality=90)
                        
                        actual_path = temp_path
                        logger.debug("Immagine salvata temporaneamente in %s", temp_path)
                except Exception as exc:
                    logger.warning("Fallito ridimensionamento immagine: %s (uso originale)", exc)

        total_size = actual_path.stat().st_size

        # Notifica inizio
        if progress:
            progress(0, total_size)

        # Upload effettivo
        try:
            result = self._file_api.upload_file(device_id, actual_path)
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()

        # Notifica completamento
        if progress:
            progress(total_size, total_size)

        logger.info(
            "FileUploader: %s caricato (%d byte) → %s",
            result.name, result.size, device_id,
        )
        return result
