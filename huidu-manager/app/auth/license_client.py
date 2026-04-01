"""Interfaccia e implementazione del modulo licenze — TASK-03.

Verifica la licenza dell'utente contro un server remoto,
con cache locale per evitare richieste ripetute.

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum

import requests

from app.auth.license_cache import LicenseCache
from app.auth.mac_helper import get_mac_address

logger = logging.getLogger(__name__)


class LicenseStatus(Enum):
    """Stati possibili per una verifica licenza."""

    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"


@dataclass
class LicenseResult:
    """Risultato di una verifica licenza.

    Attributes:
        status: Stato della licenza.
        message: Messaggio leggibile (vuoto se tutto ok).
        customer_name: Nome del cliente registrato.
        expiry_date: Data di scadenza in formato ISO (es. ``"2026-12-31"``).
        max_screens: Numero massimo di schermi gestibili con questa licenza.
    """

    status: LicenseStatus
    message: str = ""
    customer_name: str = ""
    expiry_date: str = ""
    max_screens: int = 1


class LicenseClient:
    """Interfaccia unica per la verifica licenze.

    Legge la configurazione del server da variabili d'ambiente:
    - ``LICENSE_SERVER_URL`` — endpoint di verifica
    - ``LICENSE_SERVER_TIMEOUT`` — timeout in secondi (default 10)

    Example:
        >>> client = LicenseClient()
        >>> result = client.verify("AA:BB:CC:DD:EE:FF", "utente@email.com")
        >>> result.status == LicenseStatus.VALID
    """

    def __init__(
        self,
        *,
        server_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Inizializza il client con URL server e timeout.

        Args:
            server_url: URL del server licenze. Se ``None``, legge da env.
            timeout: Timeout in secondi. Se ``None``, legge da env (default 10).
        """
        self._server_url = server_url or os.getenv("LICENSE_SERVER_URL", "")
        self._timeout = timeout or int(os.getenv("LICENSE_SERVER_TIMEOUT", "10"))
        self._cache = LicenseCache()

    def verify(self, mac_address: str, email: str) -> LicenseResult:
        """Verifica la licenza sul server remoto.

        Controlla prima la cache locale. Se la cache è valida,
        restituisce il risultato in cache senza contattare il server.

        Args:
            mac_address: Indirizzo MAC nel formato ``XX:XX:XX:XX:XX:XX``.
            email: Email dell'utente inserita nel dialog di login.

        Returns:
            ``LicenseResult`` con lo stato della licenza.
        """
        # Prima controlla la cache
        cached = self._cache.get()
        if cached is not None:
            logger.info("Licenza in cache: %s", cached.status.value)
            return cached

        if not self._server_url:
            logger.warning("LICENSE_SERVER_URL non configurato.")
            return LicenseResult(
                status=LicenseStatus.SERVER_ERROR,
                message="URL server licenze non configurato.",
            )

        try:
            response = requests.post(
                self._server_url,
                json={"mac": mac_address, "email": email},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                result = LicenseResult(
                    status=LicenseStatus.VALID,
                    customer_name=data.get("customer_name", ""),
                    expiry_date=data.get("expiry_date", ""),
                    max_screens=data.get("max_screens", 1),
                )
            elif response.status_code == 404:
                result = LicenseResult(
                    status=LicenseStatus.NOT_FOUND,
                    message="Licenza non trovata per questo dispositivo.",
                )
            elif response.status_code == 403:
                result = LicenseResult(
                    status=LicenseStatus.EXPIRED,
                    message="Licenza scaduta.",
                )
            else:
                result = LicenseResult(
                    status=LicenseStatus.INVALID,
                    message=f"Errore server: {response.status_code}",
                )

            # Salva in cache solo se valida
            if result.status == LicenseStatus.VALID:
                self._cache.save(result)

            logger.info("Verifica licenza: %s", result.status.value)
            return result

        except requests.exceptions.ConnectionError:
            logger.error("Impossibile raggiungere il server licenze.")
            return LicenseResult(
                status=LicenseStatus.NETWORK_ERROR,
                message="Impossibile raggiungere il server licenze.",
            )
        except requests.exceptions.Timeout:
            logger.error("Timeout connessione al server licenze.")
            return LicenseResult(
                status=LicenseStatus.NETWORK_ERROR,
                message="Timeout connessione al server licenze.",
            )

    def get_cached_result(self) -> LicenseResult | None:
        """Restituisce il risultato in cache se ancora valido.

        Returns:
            ``LicenseResult`` se la cache è valida, ``None`` altrimenti.
        """
        return self._cache.get()
