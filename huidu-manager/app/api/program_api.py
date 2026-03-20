"""API Programmi Huidu — metodi essenziali per il prototipo (Fase P).

Endpoint: ``POST /api/program/``

Metodi implementati in questa fase:
- ``send_presentation()`` — invia una presentazione (method: ``replace``)

I metodi mancanti (``get_programs``, ``append_presentation``, ecc.)
vengono aggiunti in TASK-04 (Fase 1).

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import json
import logging

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
    # Metodi pubblici (Fase P)
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

        # Verifica risposta dispositivo
        items = response.get("data", [])
        if items and isinstance(items, list):
            device_resp = items[0]
            device_message = device_resp.get("message", "")
            if device_message not in ("ok", "kSuccess", ""):
                raise HuiduApiError(
                    f"Dispositivo {device_id!r} ha risposto: {device_message!r}",
                    status_code=200,
                )
        logger.info(
            "Presentazione %r inviata con successo a %s.", presentation.name, device_id
        )
        return True
