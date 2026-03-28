# Fase P — Prototipo Rapido

Descrizione: Implementa i 5 moduli minimi per validare la comunicazione
con uno schermo Huidu reale da terminale. Nessun test, nessuna UI.

---

## Step 1 — Verifica prerequisiti

- Verifica che il SDK Huidu gateway sia in ascolto:
  ```cmd
  netstat -an | findstr 30080
  ```
  Se non risponde → avvialo prima di procedere.
- Il file `.env` deve contenere:
  ```env
  HUIDU_GATEWAY_HOST=127.0.0.1
  HUIDU_GATEWAY_PORT=30080
  ```

Controlla che TASK-00 sia completato:
- esiste `app/api/auth_signer.py`
- esiste `.env` con `HUIDU_SDK_KEY`, `HUIDU_SDK_SECRET`, `HUIDU_GATEWAY_HOST`, `HUIDU_GATEWAY_PORT`
- `python -m pytest tests/` gira senza errori (zero test = zero fallimenti)

Se manca qualcosa, fermarsi e completare TASK-00 prima di procedere.

---

## Step 2 — Client HTTP base (TASK-P1)

Leggi @/docs/HUIDU_API.md sezione "Autenticazione".

Implementa `app/api/huidu_client.py`:
- Classe `HuiduClient` con header firmati automatici da `AuthSigner`
- Eccezione custom `HuiduApiError(message, status_code)`
- Logging con `logging`, nessun `print()`
- Nessun import da `app/ui/`

Verifica:
- bash: `grep -r "PyQt6" app/api/` → nessun risultato.
- cmd: `findstr /r /s "PyQt6" app\api\*.py` → nessun risultato.

---

## Step 3 — Modello presentazioni minimo (TASK-P2)

Leggi @/docs/PRESENTATION_FORMAT.md.

Implementa `app/core/presentation_model.py`:
- Dataclass: `Effect`, `Font`, `TextItem`, `Area`, `Presentation`
- Solo `TextItem` per ora
- Metodo `to_dict()` compatibile con API Huidu
- Nessun import da `app/ui/`

---

## Step 4 — API Dispositivo e Programmi (TASK-P3)

Leggi @/docs/HUIDU_API.md sezioni 3.1 e 3.2.

Implementa `app/api/device_api.py` con soli questi metodi:
- `get_device_list()` → lista ID
- `get_device_status(device_id)` → stato acceso/spento, IP
- `open_screen(device_id)` / `close_screen(device_id)`

Implementa `app/api/program_api.py` con solo:
- `send_presentation(device_id, presentation)` → replace

Nessun test per ora. Nessun import da `app/ui/`.

---

## Step 5 — Script CLI prototipo (TASK-P4)

Leggi @/docs/HUIDU_API.md e @/docs/PRESENTATION_FORMAT.md.

Crea `cli_test_proto.py` nella root con menu interattivo:
- `1` Lista schermi connessi
- `2` Stato schermo (acceso/spento, IP)
- `3` Invia testo "Hello LED" allo schermo
- `4` Accendi schermo
- `5` Spegni schermo
- `0` Esci

Output in italiano con ✓ / ✗. Errori come messaggi leggibili, non stack trace.
Legge variabili dal file `.env` con `python-dotenv`.

---

## Step 6 — Validazione su hardware reale 🟢

Esegui `python cli_test_proto.py` contro uno schermo fisico.

Il prototipo è validato quando:
- Lista schermi funziona
- "Hello LED" appare sullo schermo reale
- Accensione e spegnimento funzionano

Se tutto passa → procedi con `/fase-1`.
Se ci sono errori → usa `@systematic-debugging` per diagnosticare.
