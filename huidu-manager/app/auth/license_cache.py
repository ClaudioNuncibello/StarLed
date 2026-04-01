"""Cache locale licenza con TTL — TASK-03.

Salva il risultato della verifica licenza su file JSON locale,
e lo restituisce se ancora valido (entro il TTL di 24 ore).

Il file di cache è: ``~/.huidu_manager/license_cache.json``

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.auth.license_client import LicenseResult

logger = logging.getLogger(__name__)

CACHE_FILE = Path.home() / ".huidu_manager" / "license_cache.json"
CACHE_TTL_HOURS = 24


class LicenseCache:
    """Cache locale per il risultato di verifica licenza.

    La cache viene salvata su disco e ha un TTL configurabile.
    Quando la cache è scaduta o corrotta, restituisce ``None``.

    Attributes:
        cache_file: Percorso del file di cache.
        ttl_hours: Ore di validità della cache.
    """

    def __init__(
        self,
        *,
        cache_file: Path | None = None,
        ttl_hours: int = CACHE_TTL_HOURS,
    ) -> None:
        """Inizializza la cache con percorso e TTL opzionali.

        Args:
            cache_file: Percorso del file di cache. Default ``~/.huidu_manager/license_cache.json``.
            ttl_hours: Ore di validità della cache. Default 24.
        """
        self._cache_file = cache_file or CACHE_FILE
        self._ttl_hours = ttl_hours

    def save(self, result: LicenseResult) -> None:
        """Salva il risultato della licenza su disco.

        Crea la directory padre se non esiste.

        Args:
            result: Risultato della verifica licenza da salvare.
        """
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "status": result.status.value,
            "message": result.message,
            "customer_name": result.customer_name,
            "expiry_date": result.expiry_date,
            "max_screens": result.max_screens,
            "cached_at": datetime.now().isoformat(),
        }
        self._cache_file.write_text(json.dumps(data), encoding="utf-8")
        logger.debug("Cache licenza salvata: %s", self._cache_file)

    def get(self) -> LicenseResult | None:
        """Restituisce il risultato in cache se ancora valido.

        Returns:
            ``LicenseResult`` se la cache è valida, ``None`` se:
            - il file non esiste
            - il file è corrotto
            - la cache è scaduta (oltre il TTL)
        """
        if not self._cache_file.exists():
            return None
        try:
            data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_at > timedelta(hours=self._ttl_hours):
                logger.debug("Cache licenza scaduta.")
                return None
            # Import locale per evitare circolarità
            from app.auth.license_client import LicenseResult, LicenseStatus

            return LicenseResult(
                status=LicenseStatus(data["status"]),
                message=data.get("message", ""),
                customer_name=data.get("customer_name", ""),
                expiry_date=data.get("expiry_date", ""),
                max_screens=data.get("max_screens", 1),
            )
        except Exception:
            logger.warning("Cache licenza corrotta, verrà ignorata.", exc_info=True)
            return None

    def clear(self) -> None:
        """Cancella la cache dal disco."""
        if self._cache_file.exists():
            self._cache_file.unlink()
            logger.debug("Cache licenza cancellata.")
