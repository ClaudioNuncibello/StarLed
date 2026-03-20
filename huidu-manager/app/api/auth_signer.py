"""Calcolo firma HMAC-MD5 per le API Huidu SDK.

Implementa le tre regole di firma documentate in docs/HUIDU_API.md:

- **Regola generale**: ``HMAC-MD5(body + sdkKey + date, sdkSecret)``
- **Regola file** (upload multipart): ``HMAC-MD5(sdkKey + date, sdkSecret)``
- **Regola URL** (link diretti ai file): stessa di file, firma come query string

Genera inoltre gli header HTTP completi necessari per ogni richiesta.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import TypedDict

logger = logging.getLogger(__name__)


class HuiduHeaders(TypedDict):
    """Intestazioni HTTP richieste da ogni endpoint Huidu SDK."""

    sdkKey: str
    date: str
    sign: str
    requestId: str
    Content_Type: str  # chiave con underscore — convertire a "Content-Type" nell'invio


def _http_date(dt: datetime | None = None) -> str:
    """Restituisce la data nel formato RFC 7231 richiesto dall'header ``date``.

    Args:
        dt: Datetime da formattare. Se ``None`` usa l'ora UTC corrente.

    Returns:
        Stringa nel formato ``Wed, 09 Aug 2023 07:27:44 GMT``.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    # strftime locale-sensitive — usando valori fissi per i nomi inglesi
    weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    months = (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )
    return (
        f"{weekdays[dt.weekday()]}, "
        f"{dt.day:02d} {months[dt.month - 1]} {dt.year} "
        f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} GMT"
    )


def _hmac_md5(message: str, secret: str) -> str:
    """Calcola HMAC-MD5 e restituisce il digest esadecimale minuscolo.

    Args:
        message: Stringa da firmare (concatenazione dei campi).
        secret: ``sdkSecret`` ottenuto da Huidu Technology.

    Returns:
        Stringa esadecimale del digest MD5 (32 caratteri, lowercase).
    """
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.md5,
    ).hexdigest()


class AuthSigner:
    """Calcola le firme HMAC e genera gli header per le API Huidu.

    Example:
        >>> signer = AuthSigner(sdk_key="myKey", sdk_secret="mySecret")
        >>> headers = signer.sign_request(body='{"method":"getAll","data":[]}')
        >>> assert "sign" in headers
    """

    def __init__(self, sdk_key: str, sdk_secret: str) -> None:
        """Inizializza il signer con le credenziali Huidu.

        Args:
            sdk_key: Chiave SDK pubblica (trasmessa in chiaro negli header).
            sdk_secret: Segreto SDK (MAI trasmesso — solo usato per firmare).
        """
        if not sdk_key or not sdk_secret:
            raise ValueError("sdk_key e sdk_secret non possono essere vuoti.")
        self._sdk_key = sdk_key
        self._sdk_secret = sdk_secret

    # ------------------------------------------------------------------
    # API pubblica
    # ------------------------------------------------------------------

    def sign_request(
        self,
        body: str = "",
        *,
        date: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, str]:
        """Genera gli header per una richiesta normale (non upload file).

        Regola: ``sign = HMAC-MD5(body + sdkKey + date, sdkSecret)``

        Quando il body è assente (es. GET senza payload) passare stringa vuota.

        Args:
            body: Corpo JSON della richiesta come stringa. Default ``""``.
            date: Header ``date`` nel formato RFC 7231. Se ``None``, viene
                  generato automaticamente dall'ora UTC corrente.
            request_id: UUID della richiesta. Se ``None``, viene generato.

        Returns:
            Dizionario con chiavi ``sdkKey``, ``date``, ``sign``,
            ``requestId``, ``Content-Type``.
        """
        date_str = date if date is not None else _http_date()
        req_id = request_id if request_id is not None else str(uuid.uuid4())
        message = body + self._sdk_key + date_str
        sign = _hmac_md5(message, self._sdk_secret)
        logger.debug(
            "sign_request | requestId=%s message_len=%d sign=%s",
            req_id,
            len(message),
            sign,
        )
        return self._build_headers(date_str, sign, req_id)

    def sign_file_upload(
        self,
        *,
        date: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, str]:
        """Genera gli header per upload file (multipart/form-data).

        Regola: ``sign = HMAC-MD5(sdkKey + date, sdkSecret)``
        Non include il body perché il payload è multipart, non JSON.

        Args:
            date: Header ``date`` nel formato RFC 7231. Se ``None``, UTC ora.
            request_id: UUID della richiesta. Se ``None``, viene generato.

        Returns:
            Dizionario con chiavi ``sdkKey``, ``date``, ``sign``,
            ``requestId``. **Non include** ``Content-Type`` (gestito da
            ``requests`` per i multipart).
        """
        date_str = date if date is not None else _http_date()
        req_id = request_id if request_id is not None else str(uuid.uuid4())
        message = self._sdk_key + date_str
        sign = _hmac_md5(message, self._sdk_secret)
        logger.debug(
            "sign_file_upload | requestId=%s sign=%s",
            req_id,
            sign,
        )
        headers = self._build_headers(date_str, sign, req_id)
        # Per upload multipart Content-Type viene gestito da requests
        headers.pop("Content-Type", None)
        return headers

    def sign_url(self, url: str, *, date: str | None = None) -> str:
        """Restituisce l'URL con la firma Huidu appesa come query string.

        Usato per generare link diretti ai file sul gateway.
        La firma è identica alla regola file: ``HMAC-MD5(sdkKey + date, sdkSecret)``.

        Nota: gli URL firmati restituiti da ``/api/file/`` includono già
        questa firma — questo metodo è utile se si devono costruire
        link diretti manualmente.

        Args:
            url: URL base (senza parametri di firma).
            date: Data RFC 7231. Se ``None``, viene generata dall'ora UTC.

        Returns:
            URL con ``sdkKey``, ``date`` e ``sign`` aggiunti come query param.

        Example:
            >>> signer = AuthSigner(sdk_key="k", sdk_secret="s")
            >>> signed = signer.sign_url("http://127.0.0.1:30080/api/file/img.png")
            >>> assert "sdkKey=k" in signed
            >>> assert "sign=" in signed
        """
        from urllib.parse import quote

        date_str = date if date is not None else _http_date()
        message = self._sdk_key + date_str
        sign = _hmac_md5(message, self._sdk_secret)
        separator = "&" if "?" in url else "?"
        signed_url = (
            f"{url}{separator}"
            f"sdkKey={quote(self._sdk_key)}"
            f"&date={quote(date_str)}"
            f"&sign={sign}"
        )
        logger.debug("sign_url | url=%s sign=%s", url, sign)
        return signed_url

    # ------------------------------------------------------------------
    # Helper privato
    # ------------------------------------------------------------------

    def _build_headers(
        self, date: str, sign: str, request_id: str
    ) -> dict[str, str]:
        """Costruisce il dizionario header completo.

        Args:
            date: Header ``date`` già formattato.
            sign: Digest HMAC-MD5 già calcolato.
            request_id: UUID della richiesta.

        Returns:
            Dizionario pronto per essere passato a ``requests``.
        """
        return {
            "sdkKey": self._sdk_key,
            "date": date,
            "sign": sign,
            "requestId": request_id,
            "Content-Type": "application/json",
        }
