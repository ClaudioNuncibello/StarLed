# PRESENTATION_FORMAT.md — Struttura JSON delle presentazioni

Questo documento descrive il formato JSON delle presentazioni Huidu.
È la fonte di verità per implementare `app/core/json_builder.py` e `app/core/presentation_model.py`.

---

## Gerarchia degli oggetti

```
Presentation (program)
└── Area  (1..N aree di visualizzazione)
    └── Item  (1..N contenuti nell'area)
```

- **Program** — controlla il cambio contenuto, orari, date di broadcast
- **Area** — definisce posizione (x, y) e dimensione (width, height) sul display
- **Item** — il contenuto effettivo: testo, immagine, video, orologio digitale, ecc.

---

## Struttura completa payload

```json
{
  "method": "replace",
  "id": "C16-D00-A000F",
  "data": [
    {
      "name": "Nome presentazione",
      "type": "normal",
      "uuid": "UUID-UNIVOCO-A1",
      "playControl": { ... },
      "area": [
        {
          "uuid": "UUID-AREA-B1",
          "x": 0,
          "y": 0,
          "width": 128,
          "height": 64,
          "border": { ... },
          "item": [
            { ... }
          ]
        }
      ]
    }
  ]
}
```

---

## Oggetto Program

| Campo | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `name` | string | sì | Nome visualizzato nella lista |
| `type` | string | sì | Sempre `"normal"` |
| `uuid` | string | sì | Identificatore univoco (es. `"A1"`, UUID v4) |
| `playControl` | object | no | Pianificazione orari — vedi sotto |
| `area` | array | sì | Lista delle aree |

---

## Oggetto playControl

```json
"playControl": {
  "duration": "00:00:30",
  "week": { "enable": "Mon,Tue,Wed,Thu,Fri,Sat,Sun" },
  "date": [
    { "start": "2024-01-01", "end": "2025-12-31" }
  ],
  "time": [
    { "start": "08:00:00", "end": "20:00:00" },
    { "start": "21:00:00", "end": "23:00:00" }
  ]
}
```

- `duration` — durata visualizzazione nel ciclo (formato `HH:MM:SS`)
- `week.enable` — giorni attivi separati da virgola
- `date` — array di intervalli data (può essere multiplo)
- `time` — array di fasce orarie (può essere multipla)

---

## Oggetto Area

| Campo | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `uuid` | string | no | Identificatore area |
| `x` | int | sì | Posizione orizzontale in pixel |
| `y` | int | sì | Posizione verticale in pixel |
| `width` | int | sì | Larghezza in pixel |
| `height` | int | sì | Altezza in pixel |
| `border` | object | no | Bordo decorativo |
| `item` | array | sì | Lista degli item nell'area |

### Border

```json
"border": {
  "type": 0,
  "speed": 5,
  "effect": "rotate"
}
```
`effect` può essere: `"rotate"`, `"twinkle"`, `"static"`

---

## Item: Testo (`type: "text"`)

```json
{
  "type": "text",
  "string": "Testo da visualizzare",
  "multiLine": false,
  "PlayText": false,
  "alignment": "center",
  "valignment": "middle",
  "font": {
    "name": "Arial",
    "size": 14,
    "bold": false,
    "italic": false,
    "underline": false,
    "color": "#ffffff"
  },
  "effect": {
    "type": 1,
    "speed": 3,
    "hold": 5000
  }
}
```

| Campo | Descrizione |
|---|---|
| `multiLine` | Testo su più righe |
| `PlayText` | Annuncio vocale (TTS) |
| `alignment` | `"left"`, `"center"`, `"right"` |
| `valignment` | `"top"`, `"middle"`, `"bottom"` |

---

## Item: Immagine (`type: "image"`)

```json
{
  "type": "image",
  "file": "http://127.0.0.1:30080/api/file/foto.jpg?...",
  "fileMd5": "498c7bbab17011a3d257cf0468bcff08",
  "fileSize": 337460,
  "fit": "stretch",
  "effect": {
    "type": 0,
    "speed": 5,
    "hold": 5000
  }
}
```

| `fit` | Descrizione |
|---|---|
| `"fill"` | Proporzionale + crop al centro |
| `"center"` | Ridimensiona proporzionale con bande nere |
| `"stretch"` | Distorce per riempire |
| `"tile"` | Tiling |

> Il campo `file` deve essere l'URL firmato restituito dall'API `/api/file/` dopo l'upload.
> Il campo `fileMd5` è l'MD5 del file locale prima dell'upload.

---

## Item: Video (`type: "video"`)

```json
{
  "type": "video",
  "file": "http://127.0.0.1:30080/api/file/video.mp4?...",
  "fileMd5": "46318c4df4968f716061e5fc2ad22401",
  "fileSize": 33417203,
  "aspectRatio": false,
  "effect": {
    "type": 0,
    "speed": 5,
    "hold": 5000
  }
}
```

---

## Item: Orologio digitale (`type: "digitalClock"`)

```json
{
  "type": "digitalClock",
  "timezone": "+1:00",
  "multiLine": true,
  "date": { "format": 0, "color": "#ffffff", "display": "true" },
  "time": { "format": 0, "color": "#00ff00", "display": "true" },
  "week": { "format": 0, "color": "#ffff00", "display": "false" }
}
```

| `date.format` | Formato |
|---|---|
| 0 | YYYY/MM/DD |
| 1 | MM/DD/YYYY |
| 2 | DD/MM/YYYY |
| 5 | YYYY-MM-DD-dd |

| `time.format` | Formato |
|---|---|
| 0 | hh:mm:ss |
| 1 | hh:mm |
| 2 | hh ora, mm minuti, ss secondi |

---

## Item: Testo dinamico (`type: "dynamic"`)

Permette di inserire placeholder che vengono aggiornati via `pushStatus`.

```json
{
  "type": "dynamic",
  "string": "Temperatura: {{Temp}} °C — Umidità: {{Hum}} %",
  "keys": "Temp,Hum",
  "alignment": "center",
  "font": { "name": "Arial", "size": 14, "color": "#ffffff" },
  "effect": { "type": 26, "speed": 3, "hold": 5000 }
}
```

Per aggiornare i valori dinamici si usa `pushStatus`:
```json
{ "method": "pushStatus", "data": [{ "Temp": "22.5", "Hum": "65" }] }
```

---

## Tabella effetti (`effect.type`)

| Codice | Effetto |
|---|---|
| 0 | Visualizzazione diretta |
| 1 | Scorrimento a sinistra |
| 2 | Scorrimento a destra |
| 3 | Scorrimento verso l'alto |
| 4 | Scorrimento verso il basso |
| 17 | Dissolvenza |
| 25 | Effetto casuale |
| 26 | Scorrimento continuo sinistra (solo testo) |
| 27 | Scorrimento continuo destra (solo testo) |
| 30 | Lampeggio |

`speed`: da 0 (velocissimo) a 8 (lentissimo)
`hold`: tempo di pausa in millisecondi (0–9.999.999)

---

## Dataclass Python suggerite per `presentation_model.py`

```python
from dataclasses import dataclass, field
from typing import Literal, Optional
from uuid import uuid4

@dataclass
class Effect:
    type: int = 0
    speed: int = 5
    hold: int = 5000

@dataclass
class Font:
    name: str = "Arial"
    size: int = 14
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str = "#ffffff"

@dataclass
class TextItem:
    string: str
    font: Font = field(default_factory=Font)
    effect: Effect = field(default_factory=Effect)
    type: str = "text"
    multiLine: bool = False
    alignment: str = "center"
    valignment: str = "middle"
    PlayText: bool = False

@dataclass
class ImageItem:
    file: str
    fileMd5: str
    fileSize: int
    effect: Effect = field(default_factory=Effect)
    type: str = "image"
    fit: str = "stretch"

@dataclass
class VideoItem:
    file: str
    fileMd5: str
    fileSize: int
    effect: Effect = field(default_factory=Effect)
    type: str = "video"
    aspectRatio: bool = False

@dataclass
class Area:
    x: int
    y: int
    width: int
    height: int
    item: list = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid4()))

@dataclass
class Presentation:
    name: str
    area: list[Area] = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid4()))
    type: str = "normal"
    playControl: Optional[dict] = None
```
