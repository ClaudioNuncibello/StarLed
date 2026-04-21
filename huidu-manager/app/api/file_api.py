"""API file upload Huidu — TASK-05.

Endpoint: ``POST /api/file/{filename}`` (multipart/form-data)

Implementa l'upload di file media (immagini, video) al gateway Huidu
e restituisce le informazioni del file caricato (URL firmato, MD5, size).

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.api.huidu_client import HuiduApiError, HuiduClient

logger = logging.getLogger(__name__)


@dataclass
class FileUploadResult:
    """Risultato di un upload file al gateway Huidu.

    Attributes:
        name: Nome del file come registrato sul gateway.
        md5: Hash MD5 del file (calcolato dal gateway).
        size: Dimensione in byte del file caricato.
        url: URL firmato del file sul gateway (usabile nei payload programma).
    """

    name: str
    md5: str
    size: int
    url: str


def compute_md5(file_path: str | Path) -> tuple[str, int]:
    """Calcola l'MD5 di un file in chunks per gestire file grandi.

    Args:
        file_path: Percorso del file.

    Returns:
        Tupla ``(md5_hex, dimensione_bytes)``.

    Raises:
        FileNotFoundError: Se il file non esiste.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {file_path}")
    md5 = hashlib.md5()
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
            size += len(chunk)
    return md5.hexdigest(), size


class FileApi:
    """Interfaccia per le API file upload Huidu.

    Example:
        >>> client = HuiduClient(host="192.168.1.100", port=30080,
        ...                      sdk_key="k", sdk_secret="s")
        >>> api = FileApi(client)
        >>> result = api.upload_file("C16-D00-A000F", "/path/to/image.png")
        >>> print(result.url)
    """

    def __init__(self, client: HuiduClient) -> None:
        """Inizializza l'API con il client HTTP condiviso.

        Args:
            client: Istanza ``HuiduClient`` già configurata.
        """
        self._client = client

    def upload_file(
        self,
        device_id: str,
        file_path: str | Path,
    ) -> FileUploadResult:
        """Carica un file media sul gateway Huidu.

        Endpoint: ``POST /api/file/{filename}``

        Il file viene caricato come multipart/form-data con la firma
        regola 2 (senza body). L'URL firmato restituito nella risposta
        va usato nei campi ``file`` dei payload programma.

        Args:
            device_id: ID del dispositivo destinatario (usato nel path).
            file_path: Percorso locale del file da caricare.

        Returns:
            ``FileUploadResult`` con nome, MD5, dimensione e URL firmato.

        Raises:
            HuiduApiError: Se l'upload fallisce.
            FileNotFoundError: Se il file non esiste.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")

        # Calcola MD5 locale prima dell'upload
        local_md5, local_size = compute_md5(path)
        
        # Genera un nome sicuro usando hash e suffisso puro per evitare problemi Huidu
        # con spazi e caratteri speciali nei percorsi PC Windows
        safe_name = f"{local_md5}{path.suffix.lower()}"
        
        logger.info(
            "Upload %s (%d byte, MD5=%s) a %s come %s",
            path.name, local_size, local_md5, device_id, safe_name
        )

        # Upload via client
        response = self._client.post_file(f"/api/file/{device_id}", str(path), file_name=safe_name)

        # Estrai risultato dalla risposta
        items = response.get("data", [])
        if not items or not isinstance(items, list):
            raise HuiduApiError(
                f"Risposta upload vuota per {path.name}.",
                status_code=200,
            )

        file_data = items[0]
        file_message = file_data.get("message", "")
        if file_message not in ("ok", "kSuccess", ""):
            raise HuiduApiError(
                f"Upload {path.name} fallito: {file_message!r}",
                status_code=200,
            )

        raw_url = file_data.get("data", "")
        if not raw_url.startswith("http"):
            # fallback: costruisci URL canonico dal nome file sicuro
            ret_name = file_data.get("name", safe_name)
            raw_url = f"{self._client._base_url}/api/file/{ret_name}"

        result = FileUploadResult(
            name=file_data.get("name", safe_name),
            md5=file_data.get("md5", local_md5),
            size=int(file_data.get("size", local_size)),
            url=raw_url,
        )
        logger.info("Upload completato: %s → %s", result.name, result.url[:80])
        return result
