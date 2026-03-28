# Fase 1 — Completamento Backend

Descrizione: Completa tutti i moduli backend rimasti dalla Fase P,
aggiunge i test completi e prepara il CLI esteso. Nessun import PyQt6.

Prerequisito: prototipo Fase P validato su hardware reale.

---

## Step 1 — Verifica punto di partenza

Conferma che `cli_test_proto.py` funziona contro il gateway reale.
Se non funziona, tornare a `/fase-p` e risolvere prima di procedere.

---

## Step 2 — Test auth e client (TASK-01) [parallelo]

Leggi @/docs/HUIDU_API.md sezione "Autenticazione".

Scrivi `tests/test_auth_signer.py`:
- Test deterministici con input noti e firma attesa calcolata a mano

Scrivi `tests/test_huidu_client.py`:
- Test con `unittest.mock` per simulare risposte HTTP
- Coprire: successo, `HuiduApiError`, `ConnectionError`, `Timeout`

---

## Step 3 — Modello presentazioni completo (TASK-02) [parallelo]

Leggi @/docs/PRESENTATION_FORMAT.md.

Estendi `app/core/presentation_model.py`:
- Aggiungi `ImageItem`, `VideoItem`, `DigitalClockItem`
- Aggiungi metodo `from_dict()` per deserializzazione
- Scrivi test per `to_dict()` e `from_dict()` per ogni tipo di item

---

## Step 4 — Modulo licenze (TASK-03) [parallelo]

Leggi @/docs/LICENSE_MODULE.md.

Implementa `app/auth/license_client.py`, `mac_helper.py`, `license_cache.py`
esattamente come descritto nel documento.
Scrivi test con mock per tutti gli stati di `LicenseStatus`.
Nessun import da `app/ui/`.

---

## Step 5 — API Device e Program complete (TASK-04) [parallelo]

Leggi @/docs/HUIDU_API.md sezioni 3.1 e 3.2.

Completa `app/api/device_api.py` con i metodi mancanti:
- `get_device_property`, `set_device_property`, `reboot_device`
- `get_scheduled_task`, `set_scheduled_task`

Completa `app/api/program_api.py`:
- `get_programs`, `append_presentation`, `remove_presentation`

Scrivi test completi con mock per ogni nuovo metodo.

---

## Step 6 — API File e uploader (TASK-05) [parallelo]

Leggi @/docs/HUIDU_API.md sezione 3.3.

Implementa `app/api/file_api.py`:
- `upload_file(device_id, file_path)` → URL firmato
- Calcolo MD5 in chunks da 4096 bytes prima dell'upload

Implementa `app/core/file_uploader.py`:
- Callback progresso `Callable[[int, int], None]`

Scrivi test con mock. Nessun import da `app/ui/`.

---

## Step 7 — JSON Builder e Screen Manager (TASK-06) [dopo step 3 e 5]

Leggi @/docs/PRESENTATION_FORMAT.md e @/docs/HUIDU_API.md.

Implementa `app/core/json_builder.py`:
- `build_payload(presentations, method, device_ids)` → dict
- Validazione: area con almeno un item, coordinate ≥ 0, uuid non vuoto
- Solleva `ValueError` con messaggio chiaro se struttura invalida

Implementa `app/core/screen_manager.py`:
- `ScreenManager` con `refresh()` e `get_screen(id)`
- Dataclass `Screen` con tutti i campi da `getDeviceProperty`

Scrivi test per entrambi.

---

## Step 8 — CLI completo (TASK-07) [ultimo]

Leggi @/docs/HUIDU_API.md, @/docs/PRESENTATION_FORMAT.md, @/docs/LICENSE_MODULE.md.

Crea `cli_test.py` nella root (mantieni `cli_test_proto.py` intatto) aggiungendo:
- `6` Proprietà complete di uno schermo
- `7` Carica immagine di test e invia presentazione con immagine
- `8` Screenshot schermo → salva `screenshot_test.png`
- `9` Verifica licenza (MAC + email)
- `10` Imposta task pianificato accensione/spegnimento

---

## Step 9 — Checkpoint

Esegui `/checkpoint` per verificare che tutto sia pronto prima della Fase 2.
