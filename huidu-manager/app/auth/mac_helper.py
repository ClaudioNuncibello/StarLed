"""Lettura MAC address della macchina — TASK-03.

Fornisce un'interfaccia semplice per ottenere il MAC address
dell'interfaccia di rete principale nel formato ``XX:XX:XX:XX:XX:XX``.

NON importa da ``app/ui/`` — backend puro.
"""

from __future__ import annotations

import uuid


def get_mac_address() -> str:
    """Restituisce il MAC address della macchina nel formato ``XX:XX:XX:XX:XX:XX``.

    Usa l'interfaccia di rete principale tramite ``uuid.getnode()``.

    Returns:
        Stringa MAC address in formato uppercase con separatore ``:``.

    Example:
        >>> mac = get_mac_address()
        >>> len(mac)
        17
        >>> mac.count(":")
        5
    """
    mac_int = uuid.getnode()
    mac_hex = f"{mac_int:012x}"
    return ":".join(mac_hex[i : i + 2] for i in range(0, 12, 2)).upper()
