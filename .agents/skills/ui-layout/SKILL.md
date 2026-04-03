---
name: ui-layout
description: Layout e comportamento atteso di ogni componente dell'interfaccia PyQt6 di SLPlayer. Usare quando si implementa qualsiasi file in app/ui/: MainWindow, Toolbar, Sidebar, LayerPanel, PreviewArea, LoginDialog, ScreenSettingsDialog, ImageDialog, VideoDialog, TextDialog, ClockDialog. Contiene struttura widget, segnali, stile visivo, logica layer e convenzioni per i dialog modali.
---

# UI_LAYOUT.md — Layout e comportamento interfaccia

Fonte di verità per implementare `app/ui/`. Contiene struttura widget, segnali,
logica dati e riferimenti visivi HTML per ogni componente.

---

## Modello dati che guida la UI

```
Schermo (device_id)
└── Presentazione (Program — uuid)
    └── Area unica fullscreen (x=0, y=0, w=screen_w, h=screen_h)
        └── item: [Item, Item, Item, ...]   ← ordinati = ordine riproduzione
```

- **Un'unica Area fullscreen** per presentazione — niente multi-area nella UI
- **Ogni layer = un Item** (ImageItem | VideoItem | TextItem | ClockItem)
- **L'ordine dei layer** nel panel corrisponde all'ordine dell'array `item[]`
- L'ordine determina la sequenza di riproduzione (layer 1 si vede per primo)
- Per la struttura JSON completa dei payload → vedere `presentation-format`
- Per il flusso upload/sync → vedere `program-content-management`

---

## Layout principale

```
┌─────────────────────────────────────────────────────────────────────┐
│  TITLEBAR                                                           │
├─────────────────────────────────────────────────────────────────────┤
│  TOOLBAR                                                            │
│  [+ Nuova playlist] | [🖼 Immagine] [▶ Video] [T Testo] [🕐 Orologio] | [⚙ Schermo] │
├──────────────────────┬──────────────────────────────────────────────┤
│  SIDEBAR             │                                              │
│  ── Schermi ──       │  PREVIEW AREA                                │
│  ● A3L-D24-A05C1     │                                              │
│  ○ A3L-D24-A05C2     │  [canvas LED scalato proporzionalmente]      │
│  ── Presentazioni ↻  │                                              │
│  > Vetrina Primavera │                                              │
│    Promo Luglio      │                                              │
│  ── Livelli ──       │                                              │
│  ⠿ [IMG] banner.png  │                                              │
│  ⠿ [VID] spot.mp4    │  [📷 Screenshot reale]                       │
│  ⠿ [TXT] Offerta!    │                                              │
│  ⠿ [CLK] Orologio    ├──────────────────────────────────────────────┤
│                      │  STATUSBAR: schermo | dimensioni | firmware  │
└──────────────────────┴──────────────────────────────────────────────┘
```

---

## Stile visivo — Palette colori

| Elemento | Colore |
|---|---|
| Background principale | `#1a1a1a` |
| Sidebar | `#1a1a1a` |
| Toolbar / Dialog | `#1e1e1e` |
| Titlebar / Statusbar | `#111111` |
| Preview canvas | `#111111` |
| Accent principale | `#e07820` (arancione LED) |
| Testo primario | `#cccccc` |
| Testo secondario | `#888888` |
| Testo muted | `#555555` |
| Bordi | `#2a2a2a` |
| Indicatore online | `#e07820` |
| Indicatore offline | cerchio vuoto `#555555` |
| Layer IMG badge | bg `#1a3a5a` testo `#55aaff` |
| Layer VID badge | bg `#3a1a1a` testo `#ff8888` |
| Layer TXT badge | bg `#2a2a1a` testo `#eedd88` |
| Layer CLK badge | bg `#1a2a3a` testo `#88ccff` |

Applicare via `assets/style.qss` caricato in `main.py`.

---

## MainWindow (`main_window.py`)

### Responsabilità

- Crea e organizza tutti i widget figli
- Gestisce il ciclo di vita dell'applicazione
- Al primo avvio mostra `LoginDialog` — bloccante, non chiudibile con X
- Se `VALID` → apre MainWindow; altrimenti chiude l'app
- Mantiene riferimento al device selezionato e alla presentazione selezionata

### Layout PyQt6

```python
QMainWindow
└── QWidget (central widget)
    └── QVBoxLayout
        ├── QToolBar
        └── QSplitter (horizontal)
            ├── Sidebar (QWidget, larghezza fissa 215px)
            └── PreviewArea (QWidget, espansione flessibile)
└── QStatusBar
```

### Segnali da gestire

```python
sidebar.screen_selected(screen_id)              → aggiorna preview + toolbar
sidebar.presentation_selected(presentation_id)  → aggiorna layer panel + preview
sidebar.layer_selected(layer_index)             → evidenzia layer in preview
sidebar.layers_reordered(new_order: list[int])  → aggiorna item[] e preview
toolbar.new_playlist_clicked()                  → apre dialog nome, crea presentazione
toolbar.new_item_clicked(item_type: str)        → apre dialog specifico per tipo
toolbar.screen_settings_clicked()              → apre ScreenSettingsDialog
sidebar.refresh_requested()                    → rilegge programmi dal controller
```

---

## Toolbar (`toolbar.py`)

### Pulsanti

| Pulsante | Stile | Abilitato quando |
|---|---|---|
| `+ Nuova playlist` | Bordo arancione, testo arancione | Schermo selezionato |
| `🖼 Nuova immagine` | Standard | Presentazione selezionata |
| `▶ Nuovo video` | Standard | Presentazione selezionata |
| `T Nuovo testo` | Standard | Presentazione selezionata |
| `🕐 Nuovo orologio` | Standard | Presentazione selezionata |
| `⚙ Schermo` | Standard, allineato a destra | Schermo selezionato |

I pulsanti contenuto (immagine/video/testo/orologio) sono **disabilitati** finché
non viene selezionata una presentazione nella sidebar.

### Segnali emessi

```python
new_playlist_requested = pyqtSignal()
new_item_requested = pyqtSignal(str)   # "image" | "video" | "text" | "clock"
screen_settings_requested = pyqtSignal(str)   # screen_id
```

---

## Sidebar (`sidebar.py`)

### Struttura — tre sezioni verticali

```python
QWidget (sidebar, width=215px)
└── QVBoxLayout
    ├── ScreenSection (QWidget, altezza fissa ~90px)
    │   ├── Header label "SCHERMI"
    │   └── QListWidget (schermi)
    ├── PlaylistSection (QWidget, altezza fissa ~120px)
    │   ├── Header label "PRESENTAZIONI" + QPushButton "↻"
    │   └── QListWidget (presentazioni)
    └── LayerSection (QWidget, stretch=1)
        ├── Header label "LIVELLI" + hint "drag per riordinare"
        └── LayerListWidget (QListWidget con drag&drop)
```

### Sezione Schermi

- Popolata da `GET /api/device/list/` via `ScreenManager`
- Ogni item: `● nome_device` (online) o `○ nome_device` (offline)
- Click singolo → emette `screen_selected(device_id)`
- Polling stato ogni 30 secondi in `QThread`

### Sezione Presentazioni

- Popolata dal DB locale (non dal controller direttamente)
- Ogni item: icona tipo + nome presentazione
- Click singolo → emette `presentation_selected(uuid)` + popola sezione Livelli
- Pulsante `↻` → legge `getAll` dal controller, sincronizza DB locale, ricarica lista
- Click destro → menu contestuale: Modifica nome, Duplica, Elimina

### Sezione Livelli

- Visibile e popolata solo quando una presentazione è selezionata
- Ogni item: `⠿` handle + badge tipo + nome file o testo troncato + numero ordine
- **Drag & drop interno** per riordinare → aggiorna array `item[]` in memoria
- Click singolo → emette `layer_selected(index)` → evidenzia layer in preview
- Click destro → menu contestuale: Modifica, Elimina layer

### Segnali emessi

```python
screen_selected = pyqtSignal(str)              # device_id
presentation_selected = pyqtSignal(str)        # presentation_uuid
layer_selected = pyqtSignal(int)               # indice layer
layers_reordered = pyqtSignal(list)            # nuova lista indici
refresh_requested = pyqtSignal()
```

---

## PreviewArea (`preview_area.py`)

### Responsabilità

Canvas che simula lo schermo LED, scalato proporzionalmente.

### Comportamento

- Sfondo nero `#000000` (simula LED spento)
- Dimensioni reali lette da `getDeviceProperty` → `screen.width` / `screen.height`
- Scala automatica per riempire l'area disponibile mantenendo proporzioni
- Layer selezionato → bordo arancione `#e07820` attorno all'area

### Rendering per tipo item

| Tipo | Rendering |
|---|---|
| `image` | Thumbnail proporzionale con `fit` applicato |
| `video` | Icona ▶ centrata + nome file |
| `text` | Testo con font e colore configurati (approssimato) |
| `digitalClock` / `dialClock` | Placeholder icona orologio + scritta tipo |

### Azioni

- Label overlay in alto a sinistra → dimensioni schermo + scala
- Badge in alto a destra nella preview-header → nome schermo + stato online
- Pulsante `📷 Screenshot reale` (visibile solo se schermo online) → chiama
  `GET /api/screenshot/{device_id}`, mostra immagine reale nel canvas
- Statusbar in basso → `schermo | WxH px | luminosità | firmware`

---

## LoginDialog (`login_dialog.py`)

Mostrato all'avvio, modale, non chiudibile con X (`setWindowFlags`).

### Flusso

1. Utente inserisce email → click "Accedi"
2. Pulsante disabilitato + spinner animato + label "Verifica in corso..."
3. `LicenseWorker(QThread)` esegue la verifica (mai nel thread UI)
4. Worker emette `verification_done(LicenseStatus)`
5. Se `VALID` → `dialog.accept()` → MainWindow apre
6. Altrimenti → mostra messaggio errore, riabilita pulsante

### STUB TEMPORANEO

Il `LicenseWorker` deve restituire sempre `LicenseStatus.VALID` senza
chiamare alcun server esterno. Simulare un delay di 800ms con `QThread.msleep(800)`
per mantenere il flusso UI realistico (spinner visibile, pulsante disabilitato).
Rimuovere lo stub e collegare il server reale a fine progetto.

### Messaggi per stato

```python
LicenseStatus.VALID        → (chiude dialog)
LicenseStatus.INVALID      → "Licenza non valida per questa email."
LicenseStatus.EXPIRED      → "Licenza scaduta. Contatta il supporto."
LicenseStatus.NOT_FOUND    → "Email non riconosciuta."
LicenseStatus.NETWORK_ERROR → "Impossibile contattare il server. Controlla la connessione."
```

### Layout widget

```python
QDialog
└── QVBoxLayout (padding 28px)
    ├── QLabel (logo "S" — sfondo arancione, 44×44px, border-radius 8px)
    ├── QLabel "SLPlayer" (15pt, centrato)
    ├── QLabel sottotitolo (12pt, grigio, centrato)
    ├── QLineEdit email (placeholder "email@esempio.it")
    ├── QLabel stato (spinner + messaggio, nascosto di default)
    ├── QPushButton "Accedi" (background arancione #e07820)
    └── QLabel "Starled Italia s.r.l.s" (10pt, grigio, centrato)
```

---

## ScreenSettingsDialog (`screen_settings.py`)

Dialog per configurare e controllare il dispositivo selezionato.

### Layout widget

```python
QDialog
└── QVBoxLayout
    ├── Header: ● device_id + firmware version
    ├── QSlider luminosità (0-100) + QLabel valore
    ├── QSlider volume (0-100) + QLabel valore
    ├── QPushButton "⏻ Accendi schermo"
    ├── QPushButton "◻ Spegni schermo"
    ├── QPushButton "↺ Riavvia dispositivo" (colore rosso/warning)
    └── Grid info: IP | Larghezza | Hardware | Altezza
```

### Comportamento

- Valori slider letti da `getDeviceProperty` all'apertura del dialog
- Modifica slider → invio `setDeviceProperty` in `QThread` con debounce 500ms
  (non inviare ad ogni movimento, solo quando l'utente smette)
- Accendi/Spegni → `openDeviceScreen` / `closeDeviceScreen` in `QThread`
- Riavvia → `QMessageBox.question()` di conferma → `rebootDevice(delay=5)` in `QThread`
- Info (IP, dimensioni, hardware) → sola lettura, da `getDeviceProperty`

---

## Dialog contenuto — regole comuni

Tutti i dialog di inserimento contenuto (`ImageDialog`, `VideoDialog`,
`TextDialog`, `ClockDialog`) seguono queste convenzioni:

- `QDialog` con `exec()` (bloccante)
- Pulsanti `Aggiungi livello` (OK) e `Annulla` nel footer
- `Enter` → conferma, `Esc` → annulla
- Al click su `Aggiungi livello` → valida input → emette `item_created(item_dict)`
  verso MainWindow → MainWindow aggiunge item all'area e aggiorna layer panel

### Sezione effetti — comune a ImageDialog, VideoDialog, TextDialog

```python
# Campi comuni (NON presenti in ClockDialog)
effect_type: QComboBox   # valori da tabella effetti in presentation-format
effect_speed: QSlider    # 0-8, label live
hold_ms: QSpinBox        # 0-9999999 ms, default 5000
```

Nota: gli effetti 26-30 (scorrimento continuo, lampeggio) sono disponibili
**solo nel TextDialog** — filtrarli negli altri dialog.

---

## ImageDialog (`image_dialog.py`)

### Campi specifici

```python
file_path: QPushButton "Sfoglia..."  # apre QFileDialog filtrato su immagini
                                      # formati: jpg, jpeg, png, bmp, gif
fit: QComboBox   # "stretch", "fill", "center", "tile"
                 # default: "stretch"
```

### Comportamento

- Dopo selezione file → calcola MD5 → controlla DB locale (anti-duplicato)
- Mostra anteprima thumbnail del file selezionato (QLabel 80×50px)
- `Aggiungi livello` → restituisce `ImageItem` completo

---

## VideoDialog (`video_dialog.py`)

### Campi specifici

```python
file_path: QPushButton "Sfoglia..."  # apre QFileDialog filtrato su video
                                      # formati: mp4, avi, mkv, mov
aspect_ratio: QCheckBox "Mantieni proporzioni"   # default: False
```

### Comportamento

- Dopo selezione file → calcola MD5 → controlla DB locale (anti-duplicato)
- Mostra nome file + dimensione in MB
- `Aggiungi livello` → restituisce `VideoItem` completo

---

## TextDialog (`text_dialog.py`)

### Campi specifici

```python
string: QTextEdit (2 righe)
font_name: QFontComboBox
font_size: QSpinBox (default 14)
font_color: QPushButton (apre QColorDialog, mostra swatch colore)
bold: QCheckBox
italic: QCheckBox
underline: QCheckBox
alignment: QComboBox     # "left", "center", "right" — default "center"
valignment: QComboBox    # "top", "middle", "bottom" — default "middle"
multi_line: QCheckBox    # default False
play_text: QCheckBox     # TTS — default False
```

### Effetti disponibili nel TextDialog

Tutti gli effetti 0-25 + esclusivi testo: 26, 27, 28, 29, 30.

---

## ClockDialog (`clock_dialog.py`)

### Campi

```python
# Tipo
clock_type: QButtonGroup   # "digitalClock" | "dialClock"

# Comune
timezone: QComboBox        # es. "+1:00", "+0:00", "+8:00"
font_name: QFontComboBox
font_size: QSpinBox
font_color: QPushButton    # QColorDialog

# Solo digitalClock
multi_line: QCheckBox

# Elementi (ognuno ha: visible QCheckBox, format QComboBox, color QPushButton)
date_visible / date_format / date_color
time_visible / time_format / time_color
week_visible / week_format / week_color
lunar_visible / lunar_color          # solo visible + color, niente format

# Solo dialClock (analogico)
hour_hand_color: QPushButton
minute_hand_color: QPushButton
second_hand_color: QPushButton
hour_scale_color: QPushButton
minute_scale_color: QPushButton
```

### Formati data disponibili

| Valore | Formato |
|---|---|
| 0 | YYYY/MM/DD |
| 1 | MM/DD/YYYY |
| 2 | DD/MM/YYYY |
| 5 | YYYY年MM月DD日 |
| 6 | MM月DD日 |

### Formati ora disponibili

| Valore | Formato |
|---|---|
| 0 | hh:mm:ss |
| 1 | hh:mm |
| 2 | hh时mm分ss秒 |
| 3 | hh时mm分 |

### Formati giorno settimana

| Valore | Formato |
|---|---|
| 0 | 星期一 |
| 1 | Monday |
| 2 | Mon |

### Nessun effetto transizione per ClockDialog

L'orologio non ha `effect` — omettere completamente la sezione effetti.

---

## Dialogs modali — convenzione generale

- Sempre `QDialog` con `exec()` (non `show()`)
- `Enter` → OK, `Esc` → Annulla
- Operazioni di rete sempre in `QThread` (mai nel thread UI)
- Errori API → `QMessageBox.warning()` con messaggio in italiano
- Operazioni lunghe → `QProgressDialog` indeterminato

---

## Riferimento visivo — Mockup HTML

I mockup interattivi di riferimento sono disponibili come file HTML allegati
alla skill nella cartella `.agents/skills/ui-layout/`:

- `mockup_main.html` — MainWindow completa con sidebar a tre sezioni e layer panel drag&drop
- `mockup_dialogs.html` — tutti e 4 i dialog contenuto con tab switching
- `mockup_login_settings.html` — LoginDialog e ScreenSettingsDialog

Aprire nel browser per riferimento visivo durante l'implementazione.