# Fase 2 — Interfaccia Utente PyQt6

Descrizione: Implementa l'interfaccia grafica PyQt6. Solo dopo che
il checkpoint è superato. I task 10-14 possono girare in parallelo.

Prerequisito: `/checkpoint` superato con tutti i controlli verdi.

---

## Step 1 — Verifica prerequisito

Conferma che il commit `[CHECKPOINT] Fase 1 completata` esiste in git.
Se non esiste, esegui `/checkpoint` prima di procedere.

---

## Step 2 — LoginDialog (TASK-10) [parallelo]

Leggi @/docs/UI_LAYOUT.md sezione "LoginDialog".

Implementa `app/ui/login_dialog.py`:
- Campo email (`QLineEdit`) e pulsante "Accedi"
- Verifica licenza in `QThread` separato — mai nel thread UI
- Gestione di tutti gli stati `LicenseStatus` con messaggi in italiano
- Salvataggio email in `QSettings`
- Spinner durante la verifica

---

## Step 3 — Sidebar (TASK-11) [parallelo]

Leggi @/docs/UI_LAYOUT.md sezione "Sidebar".

Implementa `app/ui/sidebar.py`:
- Sezione superiore: lista presentazioni da `data/` con icone tipo
- Sezione inferiore: lista schermi con indicatori ● online / ○ offline
- Menu contestuale click destro
- Segnali `presentation_selected(str)` e `screen_selected(str)`

---

## Step 4 — Toolbar (TASK-12) [parallelo]

Leggi @/docs/UI_LAYOUT.md sezione "Toolbar".

Implementa `app/ui/toolbar.py`:
- Tutti i pulsanti con icone Qt standard e tooltip in italiano
- Enable/disable basato su selezione presentazione + schermo
- Tutti i segnali verso MainWindow come da spec

---

## Step 5 — PreviewArea (TASK-13) [parallelo]

Leggi @/docs/UI_LAYOUT.md sezione "PreviewArea".

Implementa `app/ui/preview_area.py`:
- Canvas `QPainter` con aree scalate proporzionalmente
- Sfondo nero (simula LED spento)
- Placeholder per testo, immagine, video
- Pulsante "Screenshot reale" → chiama `/api/screenshot/`

---

## Step 6 — ScreenSettingsDialog (TASK-14) [parallelo]

Leggi @/docs/UI_LAYOUT.md sezione "ScreenSettingsDialog" e @/docs/HUIDU_API.md sezione 3.1.

Implementa `app/ui/screen_settings.py`:
- Slider luminosità e volume con invio via `setDeviceProperty`
- Pulsanti accendi/spegni e riavvia con conferma
- Tutte le operazioni dispositivo in `QThread`

---

## Step 7 — MainWindow e integrazione (TASK-15) [dopo step 2-6]

Leggi @/docs/UI_LAYOUT.md sezione "MainWindow".

Implementa `app/ui/main_window.py` e `main.py`:
- Layout `QSplitter` con sidebar 220px fissa e preview flessibile
- Connessione di tutti i segnali tra i componenti
- Flusso avvio: `LoginDialog` → se `VALID` apri `MainWindow`, altrimenti chiudi
- Salvataggio stato finestra in `QSettings`
- Applica `assets/style.qss` con tema dark

---

## Step 8 — Smoke test manuale

Avvia l'app con `python main.py` e verifica:
- LoginDialog appare prima di tutto
- Con email valida si apre MainWindow
- La lista schermi si popola
- L'invio di una presentazione funziona end-to-end

Se tutto funziona → procedi con `/fase-3`.
