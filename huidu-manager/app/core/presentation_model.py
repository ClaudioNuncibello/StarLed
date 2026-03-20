"""Modello dati per le presentazioni Huidu.

Implementa le dataclass descritte in docs/PRESENTATION_FORMAT.md.
Questa versione (Fase P) include solo ``TextItem`` — ImageItem, VideoItem
e DigitalClockItem vengono aggiunti in TASK-02 (Fase 1).

Gerarchia: ``Presentation → Area → Item``

NON importa da ``app/ui/`` né da ``app/api/`` — logica pura.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipi alias
# ---------------------------------------------------------------------------

Alignment = Literal["left", "center", "right"]
VAlignment = Literal["top", "middle", "bottom"]
EffectType = int  # vedi tabella effetti in PRESENTATION_FORMAT.md


# ---------------------------------------------------------------------------
# Componenti condivisi
# ---------------------------------------------------------------------------


@dataclass
class Effect:
    """Effetto di transizione per un item.

    Attributes:
        type: Codice effetto (0=diretto, 1=scorri sx, 17=dissolvenza, …).
        speed: Velocità da 0 (velocissimo) a 8 (lentissimo).
        hold: Pausa in millisecondi (0–9_999_999).
    """

    type: int = 0
    speed: int = 5
    hold: int = 5000

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu."""
        return {"type": self.type, "speed": self.speed, "hold": self.hold}


@dataclass
class Font:
    """Configurazione font per item testo.

    Attributes:
        name: Nome del font (es. ``"Arial"``).
        size: Dimensione in pt.
        bold: Grassetto.
        italic: Corsivo.
        underline: Sottolineato.
        color: Colore esadecimale (es. ``"#ffffff"``).
    """

    name: str = "Arial"
    size: int = 14
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str = "#ffffff"

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu."""
        return {
            "name": self.name,
            "size": self.size,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "color": self.color,
        }


# ---------------------------------------------------------------------------
# Item — Fase P: solo TextItem
# ---------------------------------------------------------------------------


@dataclass
class TextItem:
    """Item di tipo testo.

    Attributes:
        string: Contenuto testuale da visualizzare.
        font: Configurazione font.
        effect: Effetto di transizione.
        type: Sempre ``"text"`` — non modificare.
        multiLine: Abilita testo su più righe.
        alignment: Allineamento orizzontale.
        valignment: Allineamento verticale.
        PlayText: Abilita annuncio vocale TTS.
    """

    string: str
    font: Font = field(default_factory=Font)
    effect: Effect = field(default_factory=Effect)
    type: str = field(default="text", init=False)
    multiLine: bool = False
    alignment: Alignment = "center"
    valignment: VAlignment = "middle"
    PlayText: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu.

        Returns:
            Dizionario compatibile con il payload ``/api/program/``.
        """
        return {
            "type": self.type,
            "string": self.string,
            "multiLine": self.multiLine,
            "PlayText": self.PlayText,
            "alignment": self.alignment,
            "valignment": self.valignment,
            "font": self.font.to_dict(),
            "effect": self.effect.to_dict(),
        }


# ---------------------------------------------------------------------------
# Area
# ---------------------------------------------------------------------------


@dataclass
class Area:
    """Area di visualizzazione sul display LED.

    Attributes:
        x: Posizione orizzontale in pixel.
        y: Posizione verticale in pixel.
        width: Larghezza in pixel.
        height: Altezza in pixel.
        item: Lista di item nell'area (TextItem, ImageItem, ecc.).
        uuid: Identificatore univoco generato automaticamente.
    """

    x: int
    y: int
    width: int
    height: int
    item: list[Any] = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu.

        Returns:
            Dizionario compatibile con il payload ``/api/program/``.

        Raises:
            ValueError: Se l'area non ha nessun item.
        """
        if not self.item:
            raise ValueError(
                f"Area {self.uuid!r}: almeno un item è obbligatorio."
            )
        return {
            "uuid": self.uuid,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "item": [it.to_dict() for it in self.item],
        }


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------


@dataclass
class Presentation:
    """Programma (presentazione) Huidu.

    Contiene una o più aree e i metadati di pianificazione.

    Attributes:
        name: Nome della presentazione.
        area: Lista delle aree.
        uuid: UUID univoco (generato automaticamente).
        type: Tipo programma — sempre ``"normal"``.
        play_control: Dizionario playControl opzionale (orari broadcast).
    """

    name: str
    area: list[Area] = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid4()))
    type: str = field(default="normal", init=False)
    play_control: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu (un elemento dell'array ``data``).

        Questo metodo produce l'oggetto da inserire nell'array ``data``
        del payload root (il livello ``method`` / ``id`` è costruito
        da ``program_api.py``).

        Returns:
            Dizionario compatibile con la struttura program Huidu.

        Raises:
            ValueError: Se la presentazione non ha nessuna area.
        """
        if not self.area:
            raise ValueError(
                f"Presentation {self.uuid!r}: almeno un'area è obbligatoria."
            )
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "uuid": self.uuid,
            "area": [a.to_dict() for a in self.area],
        }
        if self.play_control is not None:
            result["playControl"] = self.play_control
        return result

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def simple_text(
        cls,
        name: str,
        text: str,
        *,
        screen_width: int = 128,
        screen_height: int = 64,
        effect_type: int = 1,
        font_size: int = 14,
        color: str = "#ffffff",
    ) -> "Presentation":
        """Crea una presentazione con un singolo testo a schermo intero.

        Convenienza per il prototipo CLI — crea automaticamente area e item.

        Args:
            name: Nome della presentazione.
            text: Testo da visualizzare.
            screen_width: Larghezza dello schermo in pixel.
            screen_height: Altezza dello schermo in pixel.
            effect_type: Codice effetto (default 1 = scorri sx).
            font_size: Dimensione font in pt.
            color: Colore testo esadecimale.

        Returns:
            Oggetto ``Presentation`` pronto per ``to_dict()``.
        """
        item = TextItem(
            string=text,
            font=Font(size=font_size, color=color),
            effect=Effect(type=effect_type),
        )
        area = Area(x=0, y=0, width=screen_width, height=screen_height, item=[item])
        return cls(name=name, area=[area])
