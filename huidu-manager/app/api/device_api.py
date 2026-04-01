"""API Dispositivo Huidu — tutti i metodi per Fase 1.

Endpoint: ``POST /api/device/{id}``

Metodi implementati:
- ``get_device_list()`` — lista ID schermi connessi
- ``get_device_status()`` — stato (acceso/spento, IP)
- ``open_screen()`` / ``close_screen()`` — accensione/spegnimento
- ``get_device_property()`` — proprietà complete (dimensioni, IP, versione)
- ``set_device_property()`` — impostazione proprietà (nome, volume, luminosità)
- ``reboot_device()`` — riavvio dispositivo
- ``get_scheduled_task()`` — lettura task pianificati
- ``set_scheduled_task()`` — impostazione task pianificati

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import logging
from typing import Any

from app.api.huidu_client import HuiduApiError, HuiduClient

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
    # Metodi pubblici — Fase P
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
    # Metodi pubblici — Fase 1 (TASK-04)
    # ------------------------------------------------------------------

    def get_device_property(self, device_id: str) -> dict[str, Any]:
        """Restituisce le proprietà complete di uno schermo.

        Endpoint: ``POST /api/device/{id}`` — method ``getDeviceProperty``

        Args:
            device_id: ID del dispositivo.

        Returns:
            Dizionario con i campi proprietà. Campi rilevanti:
            - ``name``: nome dispositivo
            - ``screen.width`` / ``screen.height``: dimensioni in pixel
            - ``screen.rotation``: rotazione (0, 90, 180, 270)
            - ``version.app``: versione firmware
            - ``volume``: volume (0–100)
            - ``luminance``: luminosità (0–100)
            - ``eth.ip``: IP Ethernet

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        body = {"method": "getDeviceProperty", "data": []}
        response = self._client.post(f"/api/device/{device_id}", body)
        data = self._extract_device_data(response, device_id)
        logger.info(
            "Proprietà %s: %sx%s, IP=%s",
            device_id,
            data.get("screen.width", "?"),
            data.get("screen.height", "?"),
            data.get("eth.ip", "?"),
        )
        return data

    def set_device_property(
        self, device_id: str, **properties: str
    ) -> bool:
        """Aggiorna le proprietà di uno schermo.

        Endpoint: ``POST /api/device/{id}`` — method ``setDeviceProperty``

        Args:
            device_id: ID del dispositivo.
            **properties: Proprietà da aggiornare come keyword arguments.
                Esempi: ``name="MioSchermo"``, ``volume="80"``,
                ``luminance="70"``.

        Returns:
            ``True`` se l'operazione è riuscita.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
            ValueError: Se non vengono specificate proprietà.
        """
        if not properties:
            raise ValueError("Almeno una proprietà da impostare è obbligatoria.")
        body: dict[str, Any] = {"method": "setDeviceProperty", "data": properties}
        response = self._client.post(f"/api/device/{device_id}", body)
        self._extract_device_data(response, device_id)
        logger.info("Proprietà %s aggiornate: %s", device_id, list(properties.keys()))
        return True

    def reboot_device(self, device_id: str, *, delay: int = 5) -> bool:
        """Riavvia il dispositivo.

        Endpoint: ``POST /api/device/{id}`` — method ``rebootDevice``

        Args:
            device_id: ID del dispositivo.
            delay: Secondi di attesa prima del riavvio (default 5).

        Returns:
            ``True`` se il comando è stato accettato.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        body: dict[str, Any] = {"method": "rebootDevice", "data": {"delay": delay}}
        response = self._client.post(f"/api/device/{device_id}", body)
        self._extract_device_data(response, device_id)
        logger.info("Riavvio %s in %d secondi.", device_id, delay)
        return True

    def get_scheduled_task(
        self, device_id: str, categories: list[str] | None = None
    ) -> dict[str, Any]:
        """Legge i task pianificati sul dispositivo.

        Endpoint: ``POST /api/device/{id}`` — method ``getScheduledTask``

        Args:
            device_id: ID del dispositivo.
            categories: Lista di categorie da leggere (es. ``["screen", "volume", "luminance"]``).
                Se ``None``, legge tutte e tre.

        Returns:
            Dizionario con le categorie e le relative pianificazioni.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        if categories is None:
            categories = ["screen", "volume", "luminance"]
        body: dict[str, Any] = {"method": "getScheduledTask", "data": categories}
        response = self._client.post(f"/api/device/{device_id}", body)
        data = self._extract_device_data(response, device_id)
        logger.info("Task pianificati %s letti.", device_id)
        return data

    def set_scheduled_task(
        self,
        device_id: str,
        tasks: dict[str, list[dict[str, Any]]],
    ) -> bool:
        """Imposta i task pianificati sul dispositivo.

        Endpoint: ``POST /api/device/{id}`` — method ``setScheduledTask``

        Args:
            device_id: ID del dispositivo.
            tasks: Dizionario con categorie e relative pianificazioni.
                Esempio::

                    {
                        "screen": [{"timeRange": "00:00:00~06:00:00",
                                     "dateRange": "2024-01-01~2025-12-31",
                                     "data": "false"}],
                        "luminance": [{"timeRange": "08:00:00~20:00:00",
                                        "data": "80"}]
                    }

        Returns:
            ``True`` se l'operazione è riuscita.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        body: dict[str, Any] = {"method": "setScheduledTask", "data": tasks}
        response = self._client.post(f"/api/device/{device_id}", body)
        self._extract_device_data(response, device_id)
        logger.info("Task pianificati %s aggiornati.", device_id)
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

