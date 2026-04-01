"""Costruisce payload JSON per API Huidu — TASK-06.

Fornisce ``build_payload()`` che assembla il payload root completo
per ``/api/program/`` a partire da oggetti ``Presentation``.

Include validazione strutturale con messaggi di errore chiari.

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.presentation_model import Presentation

logger = logging.getLogger(__name__)


def build_payload(
    presentations: list[Presentation],
    method: str,
    device_id: str,
) -> dict[str, Any]:
    """Costruisce il payload root completo per ``/api/program/``.

    Valida la struttura delle presentazioni e solleva ``ValueError``
    con messaggi chiari se qualcosa non è valido.

    Args:
        presentations: Lista di presentazioni da includere nel payload.
        method: Metodo API (``"replace"``, ``"append"``, ``"update"``, ``"remove"``).
        device_id: ID del dispositivo destinatario.

    Returns:
        Dizionario payload pronto per ``json.dumps()``.

    Raises:
        ValueError: Se la struttura è invalida (aree vuote, coordinate
            negative, UUID vuoti, lista presentazioni vuota).
    """
    if not presentations:
        raise ValueError("Almeno una presentazione è obbligatoria.")

    if not device_id:
        raise ValueError("device_id non può essere vuoto.")

    # Validazione strutturale
    for pres in presentations:
        _validate_presentation(pres)

    payload: dict[str, Any] = {
        "method": method,
        "id": device_id,
        "data": [p.to_dict() for p in presentations],
    }

    logger.debug(
        "build_payload | method=%s device=%s presentations=%d",
        method, device_id, len(presentations),
    )
    return payload


def _validate_presentation(pres: Presentation) -> None:
    """Valida la struttura di una presentazione prima della serializzazione.

    Args:
        pres: Presentazione da validare.

    Raises:
        ValueError: Se la struttura non è valida.
    """
    if not pres.uuid:
        raise ValueError("Presentation UUID non può essere vuoto.")

    if not pres.area:
        raise ValueError(
            f"Presentation {pres.name!r}: almeno un'area è obbligatoria."
        )

    for area in pres.area:
        if not area.uuid:
            raise ValueError(
                f"Area in {pres.name!r}: UUID non può essere vuoto."
            )

        if area.x < 0 or area.y < 0:
            raise ValueError(
                f"Area {area.uuid!r} in {pres.name!r}: "
                f"coordinate negative non ammesse (x={area.x}, y={area.y})."
            )

        if area.width <= 0 or area.height <= 0:
            raise ValueError(
                f"Area {area.uuid!r} in {pres.name!r}: "
                f"dimensioni devono essere positive (w={area.width}, h={area.height})."
            )

        if not area.item:
            raise ValueError(
                f"Area {area.uuid!r} in {pres.name!r}: "
                "almeno un item è obbligatorio."
            )
