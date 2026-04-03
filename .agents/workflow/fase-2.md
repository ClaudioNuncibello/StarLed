# Fase 2 — Interfaccia Utente PyQt6

Descrizione: Implementa l'interfaccia grafica PyQt6. Solo dopo che
il checkpoint è superato. I task 10-15 possono girare in parallelo.
I task 16-19 (dialog contenuto) possono girare in parallelo tra loro,
ma dipendono da TASK-11 (Sidebar) per il segnale `layer_selected`.

Prerequisito: `/checkpoint` superato con tutti i controlli verdi.

Riferimento visivo: aprire i file HTML in `.agents/skills/ui-layout/`
prima di implementare qualsiasi componente.

---

## Step 1 — Verifica prerequisito

Conferma che il commit `[CHECKPOINT] Fase 1 completata` esiste in git.
Se non esiste, esegui `/checkpoint` prima di procedere.

---

## Step 2 — LoginDialog (TASK-10) [parallelo]

Leggi @.agents/skills/ui-layout/ sezione "LoginDialog".

Implementa `app/ui/login_dialog.py`:
- Campo email (`QLineEdit`) e pulsante "Accedi"
- Verifica licenza in `QThread` separato — mai nel thread UI
- Gestione di tutti gli stati `LicenseStatus` con messaggi in italiano
- Salvataggio email in `QSettings`
- Spinner durante la verifica

> **STUB TEMPORANEO**: la verifica licenza deve restituire sempre
> `LicenseStatus.VALID` senza chiamare alcun server esterno.
> Il `QThread` deve comunque esistere con un delay simulato (800ms)
> per mantenere il flusso UI realistico. Rimuovere lo stub e collegare
> il server reale a fine progetto.

---

## Step 3 — Sidebar con LayerPanel (TASK-11) [parallelo]

Leggi @.agents/skills/ui-layout/ sezione "Sidebar".

Implementa `app/ui/sidebar.py` con tre sezioni verticali:

**Sezione Schermi** (in alto, altezza fissa):
- `QListWidget` con indicatori ● online / ○ offline
- Segnale `screen_selected(device_id)`

**Sezione Presentazioni** (centrale, altezza fissa):
- `QListWidget` con icone tipo
- Pulsante `↻` refresh → segnale `refresh_requested()`
- Segnale `presentation_selected(uuid)`
- Click destro → menu contestuale (Modifica nome, Duplica, Elimina)

**Sezione Livelli** (in basso, stretch=1):
- `QListWidget` con drag & drop interno abilitato
- Ogni item: handle `⠿` + badge tipo colorato + nome file/testo + numero ordine
- Badge colori: IMG `#1a3a5a/#5af`, VID `#3a1a1a/#f88`, TXT `#2a2a1a/#ee8`, CLK `#1a2a3a/#8cf`
- Riordinamento drag & drop → aggiorna array `item[]` in memoria + rinnumera ordine
- Visibile e popolata solo quando una presentazione è selezionata
- Segnale `layer_selected(index)` e `layers_reordered(list)`
- Click destro → menu contestuale (Modifica, Elimina layer)

---

## Step 4 — Toolbar (TASK-12) [parallelo]

Leggi @.agents/skills/ui-layout/ sezione "Toolbar".

Implementa `app/ui/toolbar.py`:
- `+ Nuova playlist` — bordo e testo arancione `#e07820`, abilitato se schermo selezionato
- `🖼 Nuova immagine`, `▶ Nuovo video`, `T Nuovo testo`, `🕐 Nuovo orologio` — disabilitati finché nessuna presentazione selezionata
- `⚙ Schermo` — allineato a destra, abilitato se schermo selezionato
- Tutti i segnali verso MainWindow come da spec

---

## Step 5 — PreviewArea (TASK-13) [parallelo]

Leggi @.agents/skills/ui-layout/ sezione "PreviewArea".

Implementa `app/ui/preview_area.py`:
- Canvas `QPainter` con sfondo nero, dimensioni scalate proporzionalmente
- Rendering per tipo: immagine (thumbnail), video (icona ▶), testo (font/colore), orologio (placeholder)
- Layer selezionato → bordo arancione `#e07820`
- Pulsante `📷 Screenshot reale` → chiama `/api/screenshot/` solo se schermo online
- Label overlay: dimensioni schermo + scala

---

## Step 6 — ScreenSettingsDialog (TASK-14) [parallelo]

Leggi @.agents/skills/ui-layout/ sezione "ScreenSettingsDialog" e @.agents/skills/huidu-api/ sezione 3.1.

Implementa `app/ui/screen_settings.py`:
- Header con nome device + firmware
- Slider luminosità e volume con debounce 500ms → `setDeviceProperty` in `QThread`
- Pulsanti Accendi / Spegni / Riavvia (con `QMessageBox.question()` di conferma)
- Grid info sola lettura: IP, larghezza, altezza, hardware

---

## Step 7 — MainWindow e integrazione (TASK-15) [dopo step 2-6]

Leggi @.agents/skills/ui-layout/ sezione "MainWindow".

Implementa `app/ui/main_window.py` e `main.py`:
- Layout `QSplitter` con sidebar 215px fissa e preview flessibile
- Connessione di tutti i segnali tra i componenti
- Flusso avvio: `LoginDialog` → se `VALID` apri `MainWindow`, altrimenti chiudi
- Salvataggio stato finestra in `QSettings`
- Applica `assets/style.qss` con tema dark

---

## Step 8 — ImageDialog (TASK-16) [parallelo, dopo TASK-11]

Leggi @.agents/skills/ui-layout/ sezione "ImageDialog".
Leggi @.agents/skills/presentation-format/ sezione "Item: Immagine".
Leggi @.agents/skills/program-content-management/ sezione "STEP 1".

Implementa `app/ui/dialogs/image_dialog.py`:
- `QFileDialog` filtrato su jpg, jpeg, png, bmp, gif
- `QComboBox` fit: stretch / fill / center / tile
- Thumbnail anteprima 80×50px dopo selezione file
- Calcolo MD5 + controllo anti-duplicato DB locale
- Sezione effetti comuni: tipo (no effetti 26-30), velocità slider, durata ms
- Emette `ImageItem` completo al click "Aggiungi livello"

---

## Step 9 — VideoDialog (TASK-17) [parallelo, dopo TASK-11]

Leggi @.agents/skills/ui-layout/ sezione "VideoDialog".
Leggi @.agents/skills/presentation-format/ sezione "Item: Video".
Leggi @.agents/skills/program-content-management/ sezione "STEP 1".

Implementa `app/ui/dialogs/video_dialog.py`:
- `QFileDialog` filtrato su mp4, avi, mkv, mov
- `QCheckBox` mantieni proporzioni (default False)
- Nome file + dimensione in MB dopo selezione
- Calcolo MD5 + controllo anti-duplicato DB locale
- Sezione effetti comuni: tipo (no effetti 26-30), velocità slider, durata ms
- Emette `VideoItem` completo al click "Aggiungi livello"

---

## Step 10 — TextDialog (TASK-18) [parallelo, dopo TASK-11]

Leggi @.agents/skills/ui-layout/ sezione "TextDialog".
Leggi @.agents/skills/presentation-format/ sezione "Item: Testo".

Implementa `app/ui/dialogs/text_dialog.py`:
- `QTextEdit` per il testo (2 righe)
- `QFontComboBox` + `QSpinBox` size + `QPushButton` colore (apre `QColorDialog`) + toggle B/I/U
- `QComboBox` allineamento H e V
- `QCheckBox` multiriga e TTS (PlayText)
- Sezione effetti: tutti i tipi inclusi 26-30 (scorrimento continuo, lampeggio)
- Emette `TextItem` completo al click "Aggiungi livello"

---

## Step 11 — ClockDialog (TASK-19) [parallelo, dopo TASK-11]

Leggi @.agents/skills/ui-layout/ sezione "ClockDialog".
Leggi @.agents/skills/presentation-format/ sezione "Item: Orologio digitale".

Implementa `app/ui/dialogs/clock_dialog.py`:
- Toggle tipo: Digitale (`digitalClock`) / Analogico (`dialClock`)
- `QComboBox` fuso orario
- **Se Digitale**: multiriga + elementi (data/ora/settimana/lunare) ognuno con visible + format + color
- **Se Analogico**: color picker per lancette ore/minuti/secondi e scala ore/minuti
- Font generale: `QFontComboBox` + size + colore
- Nessuna sezione effetti (l'orologio non ha `effect`)
- Emette item dict completo al click "Aggiungi livello"

---

## Step 12 — Smoke test manuale

Avvia l'app con `python main.py` e verifica:
- LoginDialog appare prima di tutto con spinner (800ms) poi apre MainWindow
- La lista schermi si popola dal gateway
- Selezionando uno schermo si abilitano i pulsanti toolbar
- Selezionando una presentazione si popola il layer panel
- Drag & drop nel layer panel riordina correttamente
- Ogni dialog contenuto si apre, si compila e aggiunge il layer correttamente
- ScreenSettingsDialog modifica luminosità e volume sul dispositivo

Se tutto funziona → procedi con `/fase-3`.