# UI_LAYOUT.md — Layout e comportamento interfaccia

Questo documento descrive il layout dell'interfaccia e il comportamento atteso
di ogni componente. È la fonte di verità per implementare `app/ui/`.

---

## Layout principale

```
┌─────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                        │
│  [Nuovo] [Modifica] [Duplica] [Elimina] | [Invia ora] [Prog.]  │
│           [Schermi ▾] [Impostazioni] [Aggiorna]                 │
├───────────────────┬─────────────────────────────────────────────┤
│                   │                                             │
│  SIDEBAR          │  AREA ANTEPRIMA                             │
│  Presentazioni    │                                             │
│  ─────────────    │  [canvas simulazione schermo LED]           │
│  > Presentaz. 1   │                                             │
│    Presentaz. 2   │                                             │
│    Presentaz. 3   │                                             │
│                   │                                             │
│  Schermi          │                                             │
│  ─────────────    │                                             │
│  ● Schermo A      │                                             │
│  ● Schermo B      │                                             │
│  ○ Schermo C      │  [stato: Schermo A — 128×64px — Online]     │
└───────────────────┴─────────────────────────────────────────────┘
│  STATUSBAR: versione app | schermo selezionato | stato licenza  │
└─────────────────────────────────────────────────────────────────┘
```

---

## MainWindow (`main_window.py`)

### Responsabilità
- Crea e organizza tutti i widget figli
- Gestisce il ciclo di vita dell'applicazione
- Al primo avvio mostra `LoginDialog` prima di tutto
- Mantiene riferimento al `ScreenManager` e alla lista presentazioni

### Layout PyQt6
```python
# Schema struttura
QMainWindow
└── QWidget (central widget)
    └── QVBoxLayout
        ├── ToolBar (QToolBar)
        └── QSplitter (horizontal)
            ├── Sidebar (QWidget, larghezza fissa 220px)
            └── PreviewArea (QWidget, espansione flessibile)
└── QStatusBar
```

### Segnali da gestire
- `sidebar.presentation_selected(presentation_id)` → aggiorna preview
- `sidebar.screen_selected(screen_id)` → aggiorna preview e toolbar
- `toolbar.send_now_clicked()` → invia presentazione selezionata allo schermo selezionato
- `toolbar.new_presentation_clicked()` → apre editor presentazione

---

## Toolbar (`toolbar.py`)

### Pulsanti e azioni

| Pulsante | Azione | Abilitato quando |
|---|---|---|
| Nuova | Apre dialog editor presentazione | Sempre |
| Modifica | Apre editor con presentazione selezionata | Presentazione selezionata |
| Duplica | Copia presentazione selezionata | Presentazione selezionata |
| Elimina | Conferma + elimina presentazione | Presentazione selezionata |
| — | Separatore | — |
| Invia ora | Invia presentazione allo schermo | Presentazione + schermo selezionati |
| Programma | Apre dialog pianificazione | Presentazione + schermo selezionati |
| — | Separatore | — |
| Schermi | Menu dropdown lista schermi | Sempre |
| Impostazioni | Apre dialog impostazioni schermo | Schermo selezionato |
| Aggiorna | Ricarica lista schermi dal gateway | Sempre |

### Segnali emessi
```python
new_presentation_requested = pyqtSignal()
edit_presentation_requested = pyqtSignal(str)      # presentation_uuid
send_now_requested = pyqtSignal(str, str)           # presentation_uuid, screen_id
schedule_requested = pyqtSignal(str, str)           # presentation_uuid, screen_id
settings_requested = pyqtSignal(str)                # screen_id
refresh_screens_requested = pyqtSignal()
```

---

## Sidebar (`sidebar.py`)

### Struttura
Due sezioni verticali con `QSplitter` o layout fisso:

**Sezione superiore — Presentazioni**
- `QListWidget` con le presentazioni salvate localmente
- Ogni item mostra: nome presentazione + icona tipo (testo / immagine / video)
- Click singolo → seleziona e aggiorna preview
- Click destro → menu contestuale (Modifica, Duplica, Elimina, Invia ora)

**Sezione inferiore — Schermi**
- `QListWidget` con gli schermi rilevati dal gateway
- Ogni item mostra: nome schermo + indicatore stato (● verde online, ○ grigio offline)
- Click singolo → seleziona schermo attivo

### Segnali emessi
```python
presentation_selected = pyqtSignal(str)   # presentation_uuid
screen_selected = pyqtSignal(str)          # screen_id
```

---

## PreviewArea (`preview_area.py`)

### Responsabilità
Mostra un'anteprima semplificata della presentazione selezionata,
scalata proporzionalmente alle dimensioni dello schermo LED selezionato.

### Comportamento
- Se nessuna presentazione selezionata → mostra placeholder grigio con testo "Nessuna presentazione selezionata"
- Se presentazione selezionata → disegna le aree con i contenuti simulati
- Proporzionale: se lo schermo è 128×64, la preview è scala 4x → 512×256px
- Per item `text` → disegna il testo con il font e colore configurati
- Per item `image` → mostra thumbnail dell'immagine
- Per item `video` → mostra primo frame o icona video
- Bordo del canvas = colore scuro (simula il corpo fisico dello schermo)

### Azioni
- Pulsante "Screenshot reale" (se schermo online) → chiama `/api/screenshot/` e mostra immagine reale
- Label in basso → mostra dimensioni schermo e stato connessione

---

## LoginDialog (`login_dialog.py`)

Mostrato all'avvio dell'app, modale, non chiudibile con X.

### Campi
- Campo email (QLineEdit)
- Pulsante "Accedi"
- Label stato (messaggio errore o "Verifica in corso...")
- Link "Contatta il supporto"

### Flusso
1. Utente inserisce email → click "Accedi"
2. Mostra spinner / "Verifica in corso..."
3. Chiama `LicenseClient.verify(mac, email)` in un thread separato (`QThread`)
4. Se `VALID` → chiude dialog → apre MainWindow
5. Se `INVALID` / `EXPIRED` / `NOT_FOUND` → mostra messaggio errore, permette riprovare
6. Se `NETWORK_ERROR` → mostra errore di connessione

**IMPORTANTE:** La verifica deve avvenire in `QThread` per non bloccare la UI.

---

## ScreenSettingsDialog (`screen_settings.py`)

Dialog per configurare un singolo schermo.

### Campi
- Nome schermo (modifica `name` via `setDeviceProperty`)
- Larghezza / Altezza display in pixel (sola lettura — da `getDeviceProperty`)
- IP Gateway (configurato localmente nell'app, non sul dispositivo)
- Luminosità (slider 0-100 → `luminance`)
- Volume (slider 0-100 → `volume`)
- Pulsante "Riavvia schermo" → `rebootDevice` con conferma
- Pulsante "Accendi/Spegni" → `openDeviceScreen` / `closeDeviceScreen`

---

## Stile visivo generale

- **Tema**: scuro (dark theme) — coerente con l'ambiente di utilizzo (sale controllo, ecc.)
- **Font**: sistema operativo default, 10-11pt per UI
- **Palette colori**:
  - Background principale: `#1e1e1e`
  - Sidebar: `#252526`
  - Toolbar: `#2d2d30`
  - Accent: `#007acc` (blu VSCode-like — familiare per operatori tecnici)
  - Testo primario: `#d4d4d4`
  - Testo secondario: `#858585`
  - Online indicator: `#4ec94e`
  - Offline indicator: `#555555`
- **Applicare con QSS** (Qt Style Sheet) in `main.py` tramite file `assets/style.qss`

---

## Dialogs modali — convenzione

Tutti i dialog modali (conferme, impostazioni, editor) devono:
- Essere `QDialog` con `exec()` (non `show()`)
- Avere pulsanti OK/Annulla con shortcut standard (`Enter` / `Esc`)
- Restituire il risultato tramite `dialog.result()` o attributi pubblici

---

## Gestione errori nella UI

- Errori API Huidu → `QMessageBox.warning()` con messaggio leggibile
- Operazioni lunghe (upload file, invio presentazione) → `QProgressDialog` indeterminato
- Aggiornamento lista schermi → indicatore di caricamento nella sidebar
- Tutte le operazioni di rete → eseguite in `QThread` (mai nel thread UI)
