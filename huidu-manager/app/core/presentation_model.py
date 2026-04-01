"""Modello dati per le presentazioni Huidu.

Implementa le dataclass descritte in docs/PRESENTATION_FORMAT.md.

Gerarchia: ``Presentation → Area → Item``

Tipi di item supportati:
- ``TextItem`` — testo statico
- ``ImageItem`` — immagine (URL firmato da ``/api/file/``)
- ``VideoItem`` — video (URL firmato da ``/api/file/``)
- ``DigitalClockItem`` — orologio digitale con data/ora/giorno settimana

NON importa da ``app/ui/`` né da ``app/api/`` — logica pura.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipi alias
# ---------------------------------------------------------------------------

Alignment = Literal["left", "center", "right"]
VAlignment = Literal["top", "middle", "bottom"]
FitMode = Literal["fill", "center", "stretch", "tile"]
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Effect:
        """Deserializza da dizionario JSON Huidu."""
        return cls(
            type=data.get("type", 0),
            speed=data.get("speed", 5),
            hold=data.get("hold", 5000),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Font:
        """Deserializza da dizionario JSON Huidu."""
        return cls(
            name=data.get("name", "Arial"),
            size=data.get("size", 14),
            bold=data.get("bold", False),
            italic=data.get("italic", False),
            underline=data.get("underline", False),
            color=data.get("color", "#ffffff"),
        )


# ---------------------------------------------------------------------------
# Item: Testo
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TextItem:
        """Deserializza da dizionario JSON Huidu."""
        return cls(
            string=data.get("string", ""),
            font=Font.from_dict(data.get("font", {})),
            effect=Effect.from_dict(data.get("effect", {})),
            multiLine=data.get("multiLine", False),
            alignment=data.get("alignment", "center"),
            valignment=data.get("valignment", "middle"),
            PlayText=data.get("PlayText", False),
        )


# ---------------------------------------------------------------------------
# Item: Immagine
# ---------------------------------------------------------------------------


@dataclass
class ImageItem:
    """Item di tipo immagine.

    Attributes:
        file: URL firmato dell'immagine (restituito da ``/api/file/``).
        fileMd5: MD5 del file originale.
        fileSize: Dimensione in byte del file originale.
        fit: Modalità di adattamento all'area.
        effect: Effetto di transizione.
        type: Sempre ``"image"`` — non modificare.
    """

    file: str
    fileMd5: str
    fileSize: int
    fit: FitMode = "stretch"
    effect: Effect = field(default_factory=Effect)
    type: str = field(default="image", init=False)

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu."""
        return {
            "type": self.type,
            "file": self.file,
            "fileMd5": self.fileMd5,
            "fileSize": self.fileSize,
            "fit": self.fit,
            "effect": self.effect.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImageItem:
        """Deserializza da dizionario JSON Huidu."""
        return cls(
            file=data.get("file", ""),
            fileMd5=data.get("fileMd5", ""),
            fileSize=data.get("fileSize", 0),
            fit=data.get("fit", "stretch"),
            effect=Effect.from_dict(data.get("effect", {})),
        )


# ---------------------------------------------------------------------------
# Item: Video
# ---------------------------------------------------------------------------


@dataclass
class VideoItem:
    """Item di tipo video.

    Attributes:
        file: URL firmato del video (restituito da ``/api/file/``).
        fileMd5: MD5 del file originale.
        fileSize: Dimensione in byte del file originale.
        aspectRatio: Se ``True`` mantiene le proporzioni originali.
        effect: Effetto di transizione.
        type: Sempre ``"video"`` — non modificare.
    """

    file: str
    fileMd5: str
    fileSize: int
    aspectRatio: bool = False
    effect: Effect = field(default_factory=Effect)
    type: str = field(default="video", init=False)

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu."""
        return {
            "type": self.type,
            "file": self.file,
            "fileMd5": self.fileMd5,
            "fileSize": self.fileSize,
            "aspectRatio": self.aspectRatio,
            "effect": self.effect.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VideoItem:
        """Deserializza da dizionario JSON Huidu."""
        return cls(
            file=data.get("file", ""),
            fileMd5=data.get("fileMd5", ""),
            fileSize=data.get("fileSize", 0),
            aspectRatio=data.get("aspectRatio", False),
            effect=Effect.from_dict(data.get("effect", {})),
        )


# ---------------------------------------------------------------------------
# Item: Orologio digitale
# ---------------------------------------------------------------------------

# Valori di default per i sub-oggetti dell'orologio digitale
_DEFAULT_CLOCK_DATE = {"format": 0, "color": "#ffffff", "display": "true"}
_DEFAULT_CLOCK_TIME = {"format": 0, "color": "#00ff00", "display": "true"}
_DEFAULT_CLOCK_WEEK = {"format": 0, "color": "#ffff00", "display": "false"}


@dataclass
class DigitalClockItem:
    """Item di tipo orologio digitale.

    Attributes:
        timezone: Fuso orario (es. ``"+1:00"``).
        multiLine: Se ``True`` mostra data e ora su righe separate.
        date: Configurazione visualizzazione data (format, color, display).
        time: Configurazione visualizzazione ora (format, color, display).
        week: Configurazione visualizzazione giorno settimana.
        type: Sempre ``"digitalClock"`` — non modificare.
    """

    timezone: str = "+1:00"
    multiLine: bool = True
    date: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULT_CLOCK_DATE))
    time: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULT_CLOCK_TIME))
    week: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULT_CLOCK_WEEK))
    type: str = field(default="digitalClock", init=False)

    def to_dict(self) -> dict[str, Any]:
        """Serializza in formato JSON Huidu."""
        return {
            "type": self.type,
            "timezone": self.timezone,
            "multiLine": self.multiLine,
            "date": dict(self.date),
            "time": dict(self.time),
            "week": dict(self.week),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DigitalClockItem:
        """Deserializza da dizionario JSON Huidu."""
        return cls(
            timezone=data.get("timezone", "+1:00"),
            multiLine=data.get("multiLine", True),
            date=data.get("date", dict(_DEFAULT_CLOCK_DATE)),
            time=data.get("time", dict(_DEFAULT_CLOCK_TIME)),
            week=data.get("week", dict(_DEFAULT_CLOCK_WEEK)),
        )


# ---------------------------------------------------------------------------
# Dispatcher tipo item
# ---------------------------------------------------------------------------

# Union type per tutti gli item supportati
ItemType = TextItem | ImageItem | VideoItem | DigitalClockItem


def item_from_dict(data: dict[str, Any]) -> ItemType:
    """Ricostruisce un item dal suo dizionario JSON in base al campo ``type``.

    Args:
        data: Dizionario JSON con almeno il campo ``type``.

    Returns:
        L'item ricostruito del tipo corretto.

    Raises:
        ValueError: Se il tipo non è riconosciuto.
    """
    tipo = data.get("type", "")
    match tipo:
        case "text":
            return TextItem.from_dict(data)
        case "image":
            return ImageItem.from_dict(data)
        case "video":
            return VideoItem.from_dict(data)
        case "digitalClock":
            return DigitalClockItem.from_dict(data)
        case _:
            raise ValueError(f"Tipo item sconosciuto: {tipo!r}")


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Area:
        """Deserializza da dizionario JSON Huidu.

        Ricostruisce gli item usando ``item_from_dict()`` per il dispatch
        automatico in base al campo ``type``.
        """
        items = [item_from_dict(it) for it in data.get("item", [])]
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            item=items,
            uuid=data.get("uuid", str(uuid4())),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Presentation:
        """Deserializza da dizionario JSON Huidu.

        Ricostruisce l'intera gerarchia: presentazione → aree → item.
        """
        areas = [Area.from_dict(a) for a in data.get("area", [])]
        pres = cls(
            name=data.get("name", ""),
            area=areas,
            uuid=data.get("uuid", str(uuid4())),
            play_control=data.get("playControl"),
        )
        return pres

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
    ) -> Presentation:
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

    @classmethod
    def simple_image(
        cls,
        name: str,
        file_url: str,
        file_md5: str,
        file_size: int,
        *,
        screen_width: int = 128,
        screen_height: int = 64,
        fit: FitMode = "stretch",
    ) -> Presentation:
        """Crea una presentazione con una singola immagine a schermo intero.

        Args:
            name: Nome della presentazione.
            file_url: URL firmato dell'immagine.
            file_md5: MD5 del file originale.
            file_size: Dimensione in byte del file originale.
            screen_width: Larghezza dello schermo in pixel.
            screen_height: Altezza dello schermo in pixel.
            fit: Modalità di adattamento.

        Returns:
            Oggetto ``Presentation`` pronto per ``to_dict()``.
        """
        item = ImageItem(file=file_url, fileMd5=file_md5, fileSize=file_size, fit=fit)
        area = Area(x=0, y=0, width=screen_width, height=screen_height, item=[item])
        return cls(name=name, area=[area])
