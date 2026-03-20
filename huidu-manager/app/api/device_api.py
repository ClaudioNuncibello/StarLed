"""API Dispositivo Huidu — metodi essenziali per il prototipo (Fase P).

Endpoint: ``POST /api/device/{id}``

Metodi implementati in questa fase:
- ``get_device_list()`` — lista ID schermi connessi
- ``get_device_status()`` — stato (acceso/spento, IP)
- ``open_screen()`` / ``close_screen()`` — accensione/spegnimento

I metodi mancanti (``get_device_property``, ``set_device_property``,
``reboot_device``, ecc.) vengono aggiunti in TASK-04 (Fase 1).

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import logging
from typing import Any

from app.api.huidu_client import HuiduClient

logger = logging.getLogger(__name__)


class DeviceApi:
    """Interfaccia per le API dispositivo Huidu.

    Wrappa ``HuiduClient`` e espone metodi tipizzati per ogni operazione.

    Example:
        >>> client = HuiduClient(host="192.168.1.100", port=30080,
        ...                      sdk_key="k", sdk_secret="s")
        >>> api = DeviceApi(client)
        >>> ids = api.get_device_list()
    """

    def __init__(self, client: HuiduClient) -> None:
        """Inizializza l'API con il client HTTP condiviso.

        Args:
            client: Istanza ``HuiduClient`` già configurata.
        """
        self._client = client

    # ------------------------------------------------------------------
    # Metodi pubblici (Fase P)
    # ------------------------------------------------------------------

    def get_device_list(self) -> list[str]:
        """Restituisce la lista degli ID schermi attualmente connessi.

        Endpoint: ``GET /api/device/list/``

        Returns:
            Lista di ID dispositivo (es. ``["C16-D00-A000F"]``).
            Lista vuota se nessun dispositivo è connesso.

        Raises:
            HuiduApiError: Se il gateway non risponde o restituisce errore.
        """
        response = self._client.get("/api/device/list/")
        data = response.get("data", [])
        if not isinstance(data, list):
            logger.warning("get_device_list: campo 'data' inatteso: %r", data)
            return []
        logger.info("Dispositivi connessi: %s", data)
        return data

    def get_device_status(self, device_id: str) -> dict[str, Any]:
        """Restituisce lo stato corrente di uno schermo.

        Endpoint: ``POST /api/device/{id}`` — method ``getDeviceStatus``

        Args:
            device_id: ID del dispositivo (es. ``"C16-D00-A000F"``).

        Returns:
            Dizionario con i campi di stato. Campi rilevanti:
            - ``screen.openStatus``: ``"true"`` / ``"false"``
            - ``eth.ip``: IP corrente del dispositivo
            - ``wifi.enabled``: Wi-Fi attivo

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        body = {"method": "getDeviceStatus", "data": []}
        response = self._client.post(f"/api/device/{device_id}", body)
        return self._extract_device_data(response, device_id)

    def open_screen(self, device_id: str) -> bool:
        """Accende lo schermo LED.

        Endpoint: ``POST /api/device/{id}`` — method ``openDeviceScreen``

        Args:
            device_id: ID del dispositivo.

        Returns:
            ``True`` se l'operazione è riuscita.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        body = {"method": "openDeviceScreen", "data": {}}
        response = self._client.post(f"/api/device/{device_id}", body)
        self._extract_device_data(response, device_id)
        logger.info("Schermo %s acceso.", device_id)
        return True

    def close_screen(self, device_id: str) -> bool:
        """Spegne lo schermo LED.

        Endpoint: ``POST /api/device/{id}`` — method ``closeDeviceScreen``

        Args:
            device_id: ID del dispositivo.

        Returns:
            ``True`` se l'operazione è riuscita.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        body = {"method": "closeDeviceScreen", "data": {}}
        response = self._client.post(f"/api/device/{device_id}", body)
        self._extract_device_data(response, device_id)
        logger.info("Schermo %s spento.", device_id)
        return True

    # ------------------------------------------------------------------
    # Helper privato
    # ------------------------------------------------------------------

    def _extract_device_data(
        self, response: dict[str, Any], device_id: str
    ) -> dict[str, Any]:
        """Estrae il campo ``data`` dalla risposta di un singolo dispositivo.

        La risposta Huidu per le operazioni su singolo device è:
        ``{"data": [{"id": "...", "message": "ok", "data": {...}}]}``

        Args:
            response: Dizionario JSON dell'intera risposta.
            device_id: ID usato nella richiesta (per i log).

        Returns:
            Il contenuto di ``response["data"][0]["data"]``.

        Raises:
            HuiduApiError: Se il campo ``data`` del dispositivo
                           non contiene ``"message": "ok"``.
        """
        from app.api.huidu_client import HuiduApiError

        items = response.get("data", [])
        if not items:
            return {}
        device_resp = items[0] if isinstance(items, list) else {}
        device_message = device_resp.get("message", "")
        if device_message not in ("ok", "kSuccess", ""):
            raise HuiduApiError(
                f"Dispositivo {device_id!r} ha risposto: {device_message!r}",
                status_code=200,
            )
        return device_resp.get("data", {})
