"""Client HTTP base per le API Huidu SDK.

Gestisce:
- Iniezione automatica degli header di autenticazione (``AuthSigner``)
- Eccezione custom ``HuiduApiError`` per errori API e di rete
- Logging strutturato (mai ``print()``)

NON importa da ``app/ui/`` — backend puro, Fase P.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from app.api.auth_signer import AuthSigner

logger = logging.getLogger(__name__)

# Timeout di default per le operazioni normali (secondi)
_DEFAULT_TIMEOUT = 10
# Timeout esteso per upload file (secondi)
_UPLOAD_TIMEOUT = 30


class HuiduApiError(Exception):
    """Eccezione sollevata per qualsiasi errore delle API Huidu.

    Attributes:
        message: Descrizione leggibile dell'errore in italiano.
        status_code: Codice HTTP della risposta (0 se errore di rete).
    """

    def __init__(self, message: str, status_code: int = 0) -> None:
        """Inizializza l'errore con messaggio e codice HTTP.

        Args:
            message: Descrizione dell'errore.
            status_code: Codice HTTP (0 per errori di rete/connessione).
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __repr__(self) -> str:
        return f"HuiduApiError(status_code={self.status_code}, message={self.message!r})"


class HuiduClient:
    """Client HTTP che comunica con il gateway Huidu SDK.

    Ogni metodo che costruisce richieste crea un **nuovo dizionario header**
    per ogni chiamata — mai riusare lo stesso dict (race condition con QThread).

    Example:
        >>> client = HuiduClient(
        ...     host="192.168.1.100",
        ...     port=30080,
        ...     sdk_key="myKey",
        ...     sdk_secret="mySecret",
        ... )
        >>> data = client.post("/api/device/list/", body={})
    """

    def __init__(
        self,
        host: str,
        port: int,
        sdk_key: str,
        sdk_secret: str,
        *,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        """Inizializza il client con le coordinate del gateway.

        Args:
            host: IP o hostname del gateway Huidu (es. ``"192.168.1.100"``).
            port: Porta del gateway (default ``30080``).
            sdk_key: Chiave SDK pubblica.
            sdk_secret: Segreto SDK (usato solo per firmare, mai trasmesso).
            timeout: Timeout in secondi per le richieste normali.
        """
        if not host:
            raise ValueError("host non può essere vuoto.")
        self._base_url = f"http://{host}:{port}"
        self._signer = AuthSigner(sdk_key=sdk_key, sdk_secret=sdk_secret)
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Metodi pubblici
    # ------------------------------------------------------------------

    def get(self, path: str) -> dict[str, Any]:
        """Esegue una GET firmata e restituisce il JSON parsato.

        Args:
            path: Percorso relativo (es. ``"/api/device/list/"``).

        Returns:
            Dizionario JSON della risposta.

        Raises:
            HuiduApiError: Se la risposta contiene ``message != "ok"``
                           o se c'è un errore di rete.
        """
        url = self._base_url + path
        # GET senza body → stringa vuota per la firma
        headers = self._signer.sign_request(body="")
        logger.debug("GET %s", url)
        try:
            response = requests.get(url, headers=headers, timeout=self._timeout)
        except requests.exceptions.ConnectionError as exc:
            raise HuiduApiError(
                f"Impossibile connettersi al gateway ({url}): {exc}", status_code=0
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise HuiduApiError(
                f"Timeout durante la connessione al gateway ({url}).", status_code=0
            ) from exc
        return self._parse_response(response)

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Esegue una POST firmata con body JSON e restituisce il JSON parsato.

        Args:
            path: Percorso relativo (es. ``"/api/device/C16-D00-A000F"``).
            body: Dizionario da serializzare come corpo JSON.

        Returns:
            Dizionario JSON della risposta.

        Raises:
            HuiduApiError: Se la risposta contiene ``message != "ok"``
                           o se c'è un errore di rete.
        """
        url = self._base_url + path
        body_str = json.dumps(body, separators=(",", ":"))
        # Nuovo dict per ogni chiamata — fondamentale per sicurezza con QThread
        headers = self._signer.sign_request(body=body_str)
        logger.debug("POST %s body_len=%d", url, len(body_str))
        try:
            response = requests.post(
                url,
                data=body_str.encode("utf-8"),
                headers=headers,
                timeout=self._timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise HuiduApiError(
                f"Impossibile connettersi al gateway ({url}): {exc}", status_code=0
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise HuiduApiError(
                f"Timeout durante la POST al gateway ({url}).", status_code=0
            ) from exc
        return self._parse_response(response)

    def post_file(
        self,
        path: str,
        file_path: str,
        *,
        timeout: int = _UPLOAD_TIMEOUT,
    ) -> dict[str, Any]:
        """Esegue l'upload di un file con multipart/form-data.

        Usa la **firma regola file** (senza body). Il ``Content-Type``
        NON viene impostato manualmente — ``requests`` lo genera con
        il boundary corretto per il multipart.

        Args:
            path: Percorso relativo (es. ``"/api/file/immagine.png"``).
            file_path: Percorso assoluto o relativo al file da caricare.
            timeout: Timeout in secondi per l'upload. Default 30s.

        Returns:
            Dizionario JSON della risposta con l'URL firmato del file.

        Raises:
            HuiduApiError: Se l'upload fallisce o c'è un errore di rete.
            FileNotFoundError: Se ``file_path`` non esiste.
        """
        import os
        from pathlib import Path

        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")

        url = self._base_url + path
        # Firma regola file — Content-Type assente (gestito da requests)
        headers = self._signer.sign_file_upload()
        logger.debug("POST_FILE %s file=%s size=%d", url, p.name, p.stat().st_size)
        try:
            with open(p, "rb") as fh:
                files = {"data": (p.name, fh, "application/octet-stream")}
                response = requests.post(
                    url, headers=headers, files=files, timeout=timeout
                )
        except requests.exceptions.ConnectionError as exc:
            raise HuiduApiError(
                f"Impossibile connettersi al gateway ({url}): {exc}", status_code=0
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise HuiduApiError(
                f"Timeout durante l'upload al gateway ({url}).", status_code=0
            ) from exc
        return self._parse_response(response)

    # ------------------------------------------------------------------
    # Helper privato
    # ------------------------------------------------------------------

    def _parse_response(self, response: requests.Response) -> dict[str, Any]:
        """Verifica la risposta HTTP e restituisce il JSON parsato.

        Args:
            response: Risposta HTTP ottenuta da ``requests``.

        Returns:
            Dizionario JSON della risposta.

        Raises:
            HuiduApiError: Se il codice HTTP non è 2xx o se
                           ``message != "ok"`` nella risposta JSON.
        """
        logger.debug(
            "HTTP %d %s — %d byte",
            response.status_code,
            response.url,
            len(response.content),
        )
        if not response.ok:
            raise HuiduApiError(
                f"Errore HTTP {response.status_code} da {response.url}.",
                status_code=response.status_code,
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise HuiduApiError(
                f"Risposta non JSON dal gateway: {response.text[:200]!r}",
                status_code=response.status_code,
            ) from exc

        message = data.get("message", "")
        if message != "ok":
            raise HuiduApiError(
                f"Il gateway ha risposto con errore: {message!r}",
                status_code=response.status_code,
            )
        return data
