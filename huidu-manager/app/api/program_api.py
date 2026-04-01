"""API Programmi Huidu — tutti i metodi per Fase 1.

Endpoint: ``POST /api/program/``

Metodi implementati:
- ``send_presentation()`` — invia una presentazione (method: ``replace``)
- ``get_programs()`` — lista programmi sul dispositivo
- ``append_presentation()`` — aggiunge senza sostituire
- ``remove_presentation()`` — rimuove programmi per UUID

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.api.huidu_client import HuiduApiError, HuiduClient
from app.core.presentation_model import Presentation

logger = logging.getLogger(__name__)


class ProgramApi:
    """Interfaccia per le API programmi Huidu.

    Example:
        >>> client = HuiduClient(host="192.168.1.100", port=30080,
        ...                      sdk_key="k", sdk_secret="s")
        >>> api = ProgramApi(client)
        >>> pres = Presentation.simple_text("Demo", "Hello LED")
        >>> api.send_presentation("C16-D00-A000F", pres)
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

    def send_presentation(
        self,
        device_id: str,
        presentation: Presentation,
        *,
        method: str = "replace",
    ) -> bool:
        """Invia una presentazione allo schermo, sostituendo quelle esistenti.

        Endpoint: ``POST /api/program/``

        Il payload viene costruito automaticamente da ``presentation.to_dict()``.
        Il metodo ``replace`` cancella tutti i programmi presenti sul dispositivo
        e li sostituisce con quello inviato.

        Args:
            device_id: ID del dispositivo destinatario.
            presentation: Oggetto ``Presentation`` da inviare.
            method: Metodo API (``"replace"`` o ``"append"``).
                    Default ``"replace"``.

        Returns:
            ``True`` se l'invio è andato a buon fine.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
            ValueError: Se la presentazione ha struttura non valida.
        """
        payload = {
            "method": method,
            "id": device_id,
            "data": [presentation.to_dict()],
        }
        body_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        logger.info(
            "send_presentation | device=%s method=%s uuid=%s body_len=%d",
            device_id,
            method,
            presentation.uuid,
            len(body_str),
        )
        response = self._client.post("/api/program/", payload)
        self._check_device_response(response, device_id)
        logger.info(
            "Presentazione %r inviata con successo a %s.", presentation.name, device_id
        )
        return True

    # ------------------------------------------------------------------
    # Metodi pubblici — Fase 1 (TASK-04)
    # ------------------------------------------------------------------

    def get_programs(self, device_id: str) -> list[dict[str, Any]]:
        """Restituisce la lista dei programmi attualmente sul dispositivo.

        Endpoint: ``POST /api/program/``

        Args:
            device_id: ID del dispositivo.

        Returns:
            Lista di dizionari con ``uuid`` e ``name`` di ogni programma.
            Lista vuota se non ci sono programmi.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
        """
        payload = {"method": "getAll", "data": [], "id": device_id}
        response = self._client.post("/api/program/", payload)
        items = response.get("data", [])
        if not items or not isinstance(items, list):
            return []
        device_resp = items[0]
        device_data = device_resp.get("data", {})
        programs = device_data.get("item", [])
        if not isinstance(programs, list):
            return []
        logger.info("Programmi su %s: %d trovati.", device_id, len(programs))
        return programs

    def append_presentation(
        self,
        device_id: str,
        presentation: Presentation,
    ) -> bool:
        """Aggiunge una presentazione senza sostituire quelle esistenti.

        Endpoint: ``POST /api/program/``

        Args:
            device_id: ID del dispositivo destinatario.
            presentation: Oggetto ``Presentation`` da aggiungere.

        Returns:
            ``True`` se l'invio è andato a buon fine.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
            ValueError: Se la presentazione ha struttura non valida.
        """
        return self.send_presentation(device_id, presentation, method="append")

    def remove_presentation(
        self,
        device_id: str,
        uuids: list[str],
    ) -> bool:
        """Rimuove uno o più programmi dal dispositivo per UUID.

        Endpoint: ``POST /api/program/``

        Args:
            device_id: ID del dispositivo.
            uuids: Lista di UUID dei programmi da rimuovere.

        Returns:
            ``True`` se la rimozione è andata a buon fine.

        Raises:
            HuiduApiError: Se il gateway restituisce un errore.
            ValueError: Se la lista UUID è vuota.
        """
        if not uuids:
            raise ValueError("Almeno un UUID da rimuovere è obbligatorio.")
        payload: dict[str, Any] = {
            "method": "remove",
            "id": device_id,
            "data": [{"uuid": uid} for uid in uuids],
        }
        response = self._client.post("/api/program/", payload)
        self._check_device_response(response, device_id)
        logger.info("Rimossi %d programmi da %s.", len(uuids), device_id)
        return True

    # ------------------------------------------------------------------
    # Helper privato
    # ------------------------------------------------------------------

    def _check_device_response(
        self, response: dict[str, Any], device_id: str
    ) -> None:
        """Verifica la risposta del dispositivo dentro il payload gateway.

        Args:
            response: Dizionario JSON dell'intera risposta.
            device_id: ID usato nella richiesta (per i messaggi di errore).

        Raises:
            HuiduApiError: Se il dispositivo risponde con errore.
        """
        items = response.get("data", [])
        if items and isinstance(items, list):
            device_resp = items[0]
            device_message = device_resp.get("message", "")
            if device_message not in ("ok", "kSuccess", ""):
                raise HuiduApiError(
                    f"Dispositivo {device_id!r} ha risposto: {device_message!r}",
                    status_code=200,
                )
