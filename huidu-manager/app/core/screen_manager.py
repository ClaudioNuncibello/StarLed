"""Gestione lista schermi connessi — TASK-06.

Fornisce ``ScreenManager`` che mantiene una lista aggiornata degli schermi
connessi al gateway Huidu e le loro proprietà complete.

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.api.device_api import DeviceApi

logger = logging.getLogger(__name__)


@dataclass
class Screen:
    """Rappresenta uno schermo Huidu con le sue proprietà.

    Attributes:
        id: ID del dispositivo (es. ``"C16-D00-A000F"``).
        name: Nome assegnato allo schermo.
        width: Larghezza display in pixel.
        height: Altezza display in pixel.
        ip: Indirizzo IP corrente.
        version: Versione firmware.
        open_status: ``True`` se lo schermo è acceso.
        volume: Volume corrente (0–100).
        luminance: Luminosità corrente (0–100).
    """

    id: str
    name: str = ""
    width: int = 0
    height: int = 0
    ip: str = ""
    version: str = ""
    open_status: bool = False
    volume: int = 100
    luminance: int = 100

    @classmethod
    def from_property_data(cls, device_id: str, data: dict[str, Any]) -> Screen:
        """Costruisce uno ``Screen`` dal dizionario ``getDeviceProperty``.

        Args:
            device_id: ID del dispositivo.
            data: Dizionario restituito da ``DeviceApi.get_device_property()``.

        Returns:
            Istanza ``Screen`` con tutti i campi popolati.
        """
        return cls(
            id=device_id,
            name=data.get("name", ""),
            width=int(data.get("screen.width", 0)),
            height=int(data.get("screen.height", 0)),
            ip=data.get("eth.ip", ""),
            version=data.get("version.app", ""),
            open_status=data.get("screen.openStatus", "false") == "true",
            volume=int(data.get("volume", 100)),
            luminance=int(data.get("luminance", 100)),
        )


class ScreenManager:
    """Gestisce la lista degli schermi connessi e le loro proprietà.

    Example:
        >>> manager = ScreenManager(device_api)
        >>> screens = manager.refresh()
        >>> for s in screens:
        ...     print(f"{s.name}: {s.width}x{s.height}")
    """

    def __init__(self, device_api: DeviceApi) -> None:
        """Inizializza il manager con l'API dispositivo.

        Args:
            device_api: Istanza ``DeviceApi`` configurata.
        """
        self._device_api = device_api
        self._screens: dict[str, Screen] = {}

    def refresh(self) -> list[Screen]:
        """Aggiorna la lista degli schermi connessi.

        Chiama ``get_device_list()`` e poi ``get_device_property()``
        per ogni dispositivo. Aggiorna la cache interna.

        Returns:
            Lista di ``Screen`` con proprietà aggiornate.
        """
        device_ids = self._device_api.get_device_list()
        updated: dict[str, Screen] = {}

        for device_id in device_ids:
            try:
                props = self._device_api.get_device_property(device_id)
                screen = Screen.from_property_data(device_id, props)
                updated[device_id] = screen
            except Exception:
                logger.warning(
                    "Impossibile leggere proprietà di %s, skip.",
                    device_id,
                    exc_info=True,
                )

        self._screens = updated
        logger.info("ScreenManager: %d schermi aggiornati.", len(updated))
        return list(updated.values())

    def get_screen(self, device_id: str) -> Screen | None:
        """Restituisce uno schermo dalla cache.

        Args:
            device_id: ID del dispositivo.

        Returns:
            ``Screen`` se presente nella cache, ``None`` altrimenti.
        """
        return self._screens.get(device_id)

    @property
    def screens(self) -> list[Screen]:
        """Lista degli schermi nella cache (ultimo refresh)."""
        return list(self._screens.values())
