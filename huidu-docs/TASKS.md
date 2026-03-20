# TASKS.md — Lista task di sviluppo

Questo file guida lo sviluppo modulare del progetto.
Ogni task è autonomo e può essere assegnato a un agente separatamente.

Leggere sempre `CLAUDE.md` prima di iniziare qualsiasi task.

---

## STRATEGIA DI SVILUPPO — LEGGERE PRIMA DI TUTTO

### Regola fondamentale: backend prima, UI mai prima del checkpoint

**NON esiste PyQt6 nelle Fasi 0, P e 1.**

L'ordine di sviluppo è rigido e non negoziabile:

```
FASE 0  →  Setup + struttura vuota
            ↓
FASE P  →  ⚡ PROTOTIPO RAPIDO — 5 file + cli_test.py
            solo i moduli strettamente necessari
            per parlare con uno schermo reale da terminale
            ↓
     🟢 PROTOTIPO FUNZIONANTE
            connessione reale, testo su schermo, accendi/spegni
            ↓
FASE 1  →  Completamento backend (moduli rimasti, test, upload file)
            ↓
     ⛔ CHECKPOINT — tutti i pytest devono passare
     ⛔ cli_test.py completo deve funzionare
            ↓
FASE 2  →  Solo a checkpoint superato → interfaccia PyQt6
FASE 3  →  Build e distribuzione
```

**Motivazione:** il prototipo rapido permette di validare subito
che la comunicazione con gli schermi funziona davvero,
prima di investire tempo nel completamento del backend.
Se c'è un problema con le credenziali Huidu o con la rete,
lo scopri in ore invece che in giorni.

### Parallelismo (per Antigravity Manager View)

I task `[PARALLELO]` non hanno dipendenze reciproche e possono essere
eseguiti contemporaneamente da agenti diversi nella Manager View.
I task `[SEQUENZIALE]` devono aspettare i loro prerequisiti.

---

## FASE 0 — Setup progetto

### TASK-00 — Scaffolding iniziale `[SEQUENZIALE — primo in assoluto]`

- [ ] Creare `pyproject.toml` con tutte le dipendenze
- [ ] Creare `requirements.txt`
- [ ] Creare `.env.example` con tutte le variabili necessarie
- [ ] Creare l'intera struttura di cartelle con `__init__.py` vuoti
- [ ] Creare `assets/style.qss` con tema dark base (usato solo in Fase 2)
- [ ] Creare `tests/conftest.py` con fixture condivise (env mock, presentation di test)
- [ ] Verificare che `python -m pytest tests/` giri senza errori (zero test = zero fallimenti)

**Prompt per l'agente:**
> Leggi CLAUDE.md. Crea il setup iniziale del progetto: pyproject.toml,
> requirements.txt, .env.example e TUTTA la struttura di cartelle con __init__.py.
> Crea tests/conftest.py con fixture pytest di base (mock delle variabili d'ambiente,
> una Presentation di esempio). NON creare ancora nessun file di logica —
> solo la struttura vuota. Verifica che `python -m pytest tests/` giri pulito.

---

## FASE P — Prototipo rapido ⚡

**Obiettivo:** avere uno script `cli_test_proto.py` funzionante contro uno schermo
reale nel minor tempo possibile. Nessun test pytest, nessuna gestione errori
elaborata — solo il minimo per validare che la comunicazione funziona.

I 5 file da implementare in questa fase, nell'ordine:

```
auth_signer.py      ← già fatto
      ↓
huidu_client.py     ← usa auth_signer, fa requests.post
      ↓
presentation_model.py  ← costruisce il JSON (solo TextItem per ora)
      ↓
device_api.py       ← list, status, accendi, spegni
program_api.py      ← send_presentation
      ↓
cli_test_proto.py   ← collega tutto, menu da terminale
```

---

### TASK-P1 — Client HTTP base `[SEQUENZIALE dopo TASK-00]`

- [ ] Classe `HuiduClient` con header firmati automatici usando `AuthSigner`
- [ ] Eccezione custom `HuiduApiError(message, status_code)`
- [ ] Logging base con `logging`
- [ ] **NO test per ora** — arrivano nella Fase 1
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/HUIDU_API.md (sezione "Autenticazione").
> Implementa app/api/huidu_client.py: client HTTP che inietta automaticamente
> gli header di autenticazione calcolati da AuthSigner (già implementato in
> app/api/auth_signer.py), gestisce errori di rete e solleva HuiduApiError.
> NON scrivere test per ora — servono solo nella Fase 1.
> IMPORTANTE: nessun import da app/ui/.

---

### TASK-P2 — Modello presentazioni minimo `[PARALLELO con TASK-P1]`

- [ ] Dataclass `Effect`, `Font`, `TextItem`, `Area`, `Presentation`
- [ ] Solo `TextItem` per ora — Image e Video arrivano nella Fase 1
- [ ] Metodo `to_dict()` compatibile con API Huidu
- [ ] **NO test per ora** — arrivano nella Fase 1
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/PRESENTATION_FORMAT.md.
> Implementa app/core/presentation_model.py con le dataclass
> Effect, Font, TextItem, Area, Presentation.
> Per ora implementa SOLO TextItem — ImageItem e VideoItem arrivano nella Fase 1.
> Il metodo to_dict() deve produrre il JSON atteso dall'API Huidu.
> NON scrivere test per ora.
> IMPORTANTE: nessun import da app/ui/.

---

### TASK-P3 — API Dispositivo e Programmi `[SEQUENZIALE dopo TASK-P1, TASK-P2]`

- [ ] `device_api.py` — solo i metodi essenziali:
  - `get_device_list()` → lista ID
  - `get_device_status(device_id)` → stato (acceso/spento, IP)
  - `open_screen(device_id)` / `close_screen(device_id)`
- [ ] `program_api.py` — solo il metodo essenziale:
  - `send_presentation(device_id, presentation)` → replace
- [ ] **NO test per ora** — arrivano nella Fase 1
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/HUIDU_API.md (sezioni 3.1 e 3.2).
> Implementa app/api/device_api.py con SOLO i metodi:
> get_device_list, get_device_status, open_screen, close_screen.
> Implementa app/api/program_api.py con SOLO il metodo send_presentation.
> send_presentation accetta un oggetto Presentation e usa to_dict() per il payload.
> NON scrivere test per ora — solo il codice funzionante.
> IMPORTANTE: nessun import da app/ui/.

---

### TASK-P4 — Script prototipo CLI `[SEQUENZIALE — ultimo della Fase P]` 🟢

Questo è il **primo traguardo concreto** del progetto.
Quando questo script funziona contro uno schermo reale, il prototipo è validato.

- [ ] Creare `cli_test_proto.py` nella root
- [ ] Menu da terminale con queste opzioni:
  - `1` — Lista schermi connessi al gateway
  - `2` — Stato di uno schermo (acceso/spento, IP)
  - `3` — Invia testo "Hello LED" allo schermo
  - `4` — Accendi schermo
  - `5` — Spegni schermo
  - `0` — Esci
- [ ] Legge `HUIDU_GATEWAY_HOST`, `HUIDU_GATEWAY_PORT`, `HUIDU_SDK_KEY`,
      `HUIDU_SDK_SECRET` dal file `.env`
- [ ] Output pulito in italiano con ✓ / ✗
- [ ] Errori mostrati come messaggi leggibili, non stack trace

**Prompt per l'agente:**
> Leggi CLAUDE.md, docs/HUIDU_API.md, docs/PRESENTATION_FORMAT.md.
> Crea cli_test_proto.py nella root: script Python eseguibile da terminale
> (python cli_test_proto.py) con un menu interattivo che usa i moduli già
> implementati in app/api/ e app/core/ per comunicare con uno schermo Huidu reale.
> L'obiettivo è validare che auth_signer, huidu_client, device_api e program_api
> funzionano correttamente contro il gateway fisico.
> Output in italiano, pulito, con ✓ per successo e ✗ per errore.
> Legge le variabili d'ambiente dal file .env con python-dotenv.

---

## 🟢 PROTOTIPO VALIDATO

Quando `cli_test_proto.py` riesce a:
- listare gli schermi connessi
- mostrare "Hello LED" su uno schermo reale
- accendere e spegnere lo schermo

→ **il prototipo è validato**, la comunicazione funziona.
Si può procedere alla Fase 1 per completare il backend.

---

## FASE 1 — Completamento backend `[nessun import PyQt6]`

Completamento di tutto ciò che mancava nella Fase P.
I task P1-P4 possono girare in parallelo dopo TASK-00.

---

### TASK-01 — Test auth_signer e huidu_client `[PARALLELO]`

- [ ] Test deterministici per `auth_signer.py` in `tests/test_auth_signer.py`
- [ ] Test con mock per `huidu_client.py` in `tests/test_huidu_client.py`
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/HUIDU_API.md (sezione "Autenticazione").
> Scrivi test completi per app/api/auth_signer.py e app/api/huidu_client.py.
> I test di auth_signer devono usare input noti con firma attesa calcolata a mano.
> I test di huidu_client devono usare unittest.mock per simulare le risposte HTTP.

---

### TASK-02 — Modello presentazioni completo `[PARALLELO]`

- [ ] Aggiungere `ImageItem`, `VideoItem`, `DigitalClockItem` a `presentation_model.py`
- [ ] Metodo `from_dict()` per deserializzazione
- [ ] Metodo `save(path)` / `load(path)` per persistenza locale in `data/`
- [ ] Test completi in `tests/test_presentation_model.py`
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/PRESENTATION_FORMAT.md.
> Estendi app/core/presentation_model.py aggiungendo ImageItem, VideoItem,
> DigitalClockItem e i metodi from_dict(), save(), load().
> Scrivi test completi che verificano to_dict() e from_dict()
> con tutti i tipi di item.

---

### TASK-03 — Modulo licenze `[PARALLELO]`

- [ ] `mac_helper.py` — lettura MAC address
- [ ] `license_cache.py` — cache JSON su disco con TTL 24h
- [ ] `license_client.py` — interfaccia pubblica + template adattabile
- [ ] Test con mock del server HTTP
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/LICENSE_MODULE.md.
> Implementa app/auth/mac_helper.py, app/auth/license_cache.py,
> app/auth/license_client.py esattamente come descritto.
> Scrivi test con mock di requests per tutti gli stati LicenseStatus.
> IMPORTANTE: nessun import da app/ui/.

---

### TASK-04 — API Device e Program complete `[PARALLELO]`

- [ ] Completare `device_api.py` con i metodi mancanti:
  - `get_device_property(device_id)` → dict proprietà
  - `set_device_property(device_id, props)` → bool
  - `reboot_device(device_id, delay=5)` → bool
  - `get_scheduled_task(device_id)` / `set_scheduled_task(...)`
- [ ] Completare `program_api.py` con i metodi mancanti:
  - `get_programs(device_id)` → list
  - `append_presentation(...)` / `remove_presentation(...)`
- [ ] Test completi con mock per tutti i nuovi metodi
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/HUIDU_API.md (sezioni 3.1 e 3.2).
> Estendi app/api/device_api.py e app/api/program_api.py
> con tutti i metodi non ancora implementati nella Fase P.
> Scrivi test completi con mock per ogni nuovo metodo.

---

### TASK-05 — API File e uploader `[PARALLELO]`

- [ ] `file_api.py` — `upload_file(device_id, file_path)` → URL firmato
- [ ] Calcolo MD5 del file prima dell'upload
- [ ] `file_uploader.py` in core con callback progresso `(bytes_sent, total) -> None`
- [ ] Test con mock
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/HUIDU_API.md (sezione 3.3).
> Implementa app/api/file_api.py e app/core/file_uploader.py.
> Il callback progresso è Callable[[int, int], None].
> IMPORTANTE: nessun import da app/ui/.

---

### TASK-06 — JSON Builder e Screen Manager `[SEQUENZIALE dopo TASK-02, TASK-04]`

- [ ] `json_builder.py` — `build_payload(presentations, method, device_ids)` → dict
- [ ] Validazione struttura (area con almeno un item, coordinate ≥ 0, uuid non vuoto)
- [ ] `screen_manager.py` — `ScreenManager` con `refresh()`, `get_screen(id)`
- [ ] Dataclass `Screen` con tutti i campi da `getDeviceProperty`
- [ ] Test per entrambi
- [ ] **Verificare: zero import da `app/ui/`**

**Prompt per l'agente:**
> Leggi CLAUDE.md, docs/PRESENTATION_FORMAT.md, docs/HUIDU_API.md.
> Implementa app/core/json_builder.py e app/core/screen_manager.py.
> Il builder solleva ValueError con messaggio chiaro se la struttura è invalida.
> IMPORTANTE: nessun import da app/ui/.

---

### TASK-07 — CLI completo `[SEQUENZIALE — ultimo della Fase 1]` ⚠️

Estensione di `cli_test_proto.py` in `cli_test.py` completo.

- [ ] Creare `cli_test.py` nella root (mantieni `cli_test_proto.py` funzionante)
- [ ] Aggiungere le opzioni mancanti rispetto al prototipo:
  - `6` — Proprietà complete di uno schermo
  - `7` — Carica immagine di test e invia presentazione con immagine
  - `8` — Screenshot schermo → salva `screenshot_test.png`
  - `9` — Verifica licenza (MAC + email)
  - `10` — Imposta task pianificato (accensione/spegnimento)
- [ ] Output in italiano, pulito, con ✓ / ✗

**Prompt per l'agente:**
> Leggi CLAUDE.md, docs/HUIDU_API.md, docs/PRESENTATION_FORMAT.md, docs/LICENSE_MODULE.md.
> Crea cli_test.py nella root estendendo le funzionalità di cli_test_proto.py
> con tutte le opzioni aggiuntive descritte. Mantieni cli_test_proto.py invariato.

---

## ⛔ CHECKPOINT OBBLIGATORIO TRA FASE 1 E FASE 2

**Eseguire questi tre controlli. Tutti devono passare.**

```bash
# 1. Tutti i test devono passare
python -m pytest tests/ -v

# 2. CLI completo deve girare senza crash
python cli_test.py

# 3. Nessun modulo backend deve importare PyQt6
grep -r "PyQt6" app/api/ app/core/ app/auth/
# → deve restituire: nessun risultato
```

**Se anche solo uno fallisce → tornare indietro, non iniziare la Fase 2.**

---

## FASE 2 — Interfaccia utente PyQt6

Solo dopo il checkpoint. I task 10-14 possono girare in parallelo.

---

### TASK-10 — LoginDialog `[PARALLELO]`

- [ ] Dialog con campo email e pulsante "Accedi"
- [ ] Verifica licenza in `QThread` separato (mai nel thread UI)
- [ ] Gestione di tutti gli stati `LicenseStatus` con messaggi in italiano
- [ ] Salvataggio email in `QSettings`
- [ ] Spinner durante la chiamata di verifica

**Dipende da:** TASK-03, checkpoint superato

**Prompt per l'agente:**
> Leggi CLAUDE.md, docs/UI_LAYOUT.md (sezione LoginDialog), docs/LICENSE_MODULE.md.
> Implementa app/ui/login_dialog.py. La verifica licenza DEVE girare in QThread.
> Gestisci tutti i casi LicenseStatus con messaggi user-friendly in italiano.

---

### TASK-11 — Sidebar `[PARALLELO]`

- [ ] Lista presentazioni da `data/` (JSON locali)
- [ ] Lista schermi dal `ScreenManager`
- [ ] Indicatori ● online / ○ offline
- [ ] Menu contestuale click destro
- [ ] Segnali `presentation_selected` e `screen_selected`

**Dipende da:** TASK-06, checkpoint superato

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/UI_LAYOUT.md (sezione Sidebar).
> Implementa app/ui/sidebar.py con le due sezioni e i segnali descritti.

---

### TASK-12 — Toolbar `[PARALLELO]`

- [ ] Tutti i pulsanti con icone Qt standard e tooltip in italiano
- [ ] Enable/disable basato su selezione presentazione + schermo
- [ ] Segnali verso MainWindow

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/UI_LAYOUT.md (sezione Toolbar).
> Implementa app/ui/toolbar.py.

---

### TASK-13 — PreviewArea `[PARALLELO]`

- [ ] Canvas QPainter con aree presentazione scalate proporzionalmente
- [ ] Placeholder per testo, immagine, video
- [ ] Pulsante "Screenshot reale" che chiama `/api/screenshot/`

**Dipende da:** TASK-02, TASK-04, checkpoint superato

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/UI_LAYOUT.md (sezione PreviewArea).
> Implementa app/ui/preview_area.py con QPainter. Sfondo nero (LED spento).

---

### TASK-14 — ScreenSettingsDialog `[PARALLELO]`

- [ ] Slider luminosità e volume → `setDeviceProperty`
- [ ] Pulsanti accendi/spegni e riavvia con conferma
- [ ] Operazioni dispositivo in QThread

**Dipende da:** TASK-04, checkpoint superato

**Prompt per l'agente:**
> Leggi CLAUDE.md, docs/UI_LAYOUT.md (sezione ScreenSettingsDialog),
> docs/HUIDU_API.md (sezione 3.1).
> Implementa app/ui/screen_settings.py. Operazioni dispositivo in QThread.

---

### TASK-15 — MainWindow e integrazione `[SEQUENZIALE dopo TASK-10..14]`

- [ ] Layout QSplitter (sidebar 220px + preview flessibile)
- [ ] Connessione di tutti i segnali tra i componenti
- [ ] Avvio con LoginDialog → se VALID apri MainWindow, altrimenti chiudi
- [ ] Salvataggio stato finestra in QSettings

**Prompt per l'agente:**
> Leggi CLAUDE.md e docs/UI_LAYOUT.md (sezione MainWindow).
> Implementa app/ui/main_window.py e main.py.
> Connetti tutti i segnali. Gestisci correttamente il ciclo di vita
> LoginDialog → MainWindow.

---

## FASE 3 — Build e distribuzione

### TASK-16 — Build Windows con PyInstaller `[SEQUENZIALE dopo TASK-15]`

- [ ] `huidu_manager.spec` configurato
- [ ] Inclusione `assets/`, gestione `.env` in modalità frozen con `sys._MEIPASS`
- [ ] Script `build.bat`
- [ ] Test del `.exe` su macchina Windows pulita

**Prompt per l'agente:**
> Leggi CLAUDE.md. Crea la configurazione PyInstaller single-file per Windows.
> Gestisci il caricamento del .env in modalità frozen. Crea build.bat.

---

## Regole per tutti gli agenti

- **Leggere sempre CLAUDE.md prima di iniziare**
- **Fasi 0, P, 1: zero import PyQt6** — verificare con `grep -r "PyQt6" app/api/ app/core/ app/auth/`
- **Fase P: niente test, solo codice funzionante** — i test arrivano nella Fase 1
- **Se un dettaglio non è nei doc, chiedere** — non inventare
- **Solo package in requirements.txt** — nessuna dipendenza extra
- **Ogni task = un commit** con messaggio `[TASK-NN] descrizione`
- **Il checkpoint tra Fase 1 e Fase 2 è bloccante** — non aggirarlo mai
