# CLAUDE.md — Contesto generale progetto

Questo file viene letto automaticamente da Claude Code all'avvio.
Contiene tutto il contesto necessario per lavorare su questo progetto senza domande ambigue.

---

## Riferimento progetto esterno — SLPlayer

Esiste un progetto open source (FlashPro-full/SLPlayer) che implementa
una soluzione simile con le stesse API Huidu. È stato analizzato e confrontato
con la documentazione ufficiale. Alcune osservazioni utili, alcune pericolose.

**Conferme utili prese da SLPlayer:**
- Il calcolo MD5 dei file va fatto in chunks da 4096 bytes
- La firma può andare nei parametri URL oltre che negli header (per link diretti ai file)
- Esiste un canale XML su `/raw/{id}` per operazioni avanzate (da verificare su hardware)
- L'upload file potrebbe essere asincrono con polling (da verificare su hardware)

**Bug di SLPlayer che NON vanno replicati:**
- Credenziali hardcoded nel codice — nel nostro progetto vanno SOLO nel `.env`
- Loop `while True` senza timeout — usare sempre `max_retries` o `timeout` esplicito
- Header condiviso come attributo di istanza modificato in-place — creare un nuovo
  dict per ogni chiamata (fondamentale per sicurezza con QThread)
- Content-Type non rimosso prima dell'upload multipart — rimuoverlo sempre

## Strategia di sviluppo — LEGGERE PRIMA DI TUTTO

**Questo progetto si sviluppa in ordine stretto: backend puro → collaudo CLI → UI.**

Le Fasi 0, 1 e 2 non contengono nessun import da PyQt6.
L'interfaccia grafica esiste solo nella Fase 3 e solo dopo che
il backend è completamente testato e funzionante via `cli_test.py`.

Verificare sempre prima di chiudere un task delle Fasi 0-2:
```bash
grep -r "PyQt6" app/api/ app/core/ app/auth/
# deve restituire: nessun risultato
```

Vedere `TASKS.md` per l'ordine completo e il checkpoint obbligatorio.

---

## Cos'è questo progetto

**huidu-manager** è un'applicazione desktop Windows sviluppata in Python + PyQt6.
Permette al cliente finale (sotto licenza) di gestire i propri schermi LED Huidu:
creare presentazioni, inviarle in onda, programmarle, controllare i dispositivi.

---

## Stack tecnologico

| Componente | Tecnologia |
|---|---|
| UI desktop | Python 3.11 + PyQt6 |
| Comunicazione schermi | HTTP REST locale (Huidu SDK, porta 30080) |
| Autenticazione API Huidu | HMAC-MD5 con sdkKey + sdkSecret |
| Sistema licenze | HTTP REST verso server committente (modulo intercambiabile) |
| Salvataggio dati locali | JSON su disco (cartella `data/`) |
| Packaging Windows | PyInstaller |

---

## Struttura cartelle

```
huidu-manager/
├── main.py                  # Entry point — avvia QApplication e MainWindow
├── pyproject.toml
├── requirements.txt
├── .env.example             # Template variabili d'ambiente (mai committare .env)
│
├── app/
│   ├── ui/                  # Solo componenti PyQt6 — nessuna logica business
│   │   ├── main_window.py   # Finestra principale con layout toolbar/sidebar/preview
│   │   ├── toolbar.py       # Barra strumenti superiore
│   │   ├── sidebar.py       # Lista presentazioni con azioni contestuali
│   │   ├── preview_area.py  # Area anteprima schermo LED
│   │   ├── login_dialog.py  # Dialog autenticazione licenza (MAC + email)
│   │   └── screen_settings.py # Dialog impostazioni schermo (IP, nome, dimensioni)
│   │
│   ├── core/                # Logica business — nessun import da PyQt6
│   │   ├── presentation_model.py  # Dataclass Presentation, Area, Item
│   │   ├── screen_manager.py      # Gestione lista schermi connessi
│   │   ├── scheduler.py           # Pianificazione orari broadcast
│   │   ├── json_builder.py        # Costruisce payload JSON per API Huidu
│   │   └── file_uploader.py       # Upload file media verso gateway Huidu
│   │
│   ├── api/                 # Comunicazione HTTP con schermi Huidu
│   │   ├── huidu_client.py  # Client HTTP base con gestione errori
│   │   ├── auth_signer.py   # Calcolo firma HMAC-MD5 (sdkKey/sdkSecret)
│   │   ├── device_api.py    # Metodi /api/device/ (list, status, reboot, ecc.)
│   │   ├── program_api.py   # Metodi /api/program/ (replace, append, remove, ecc.)
│   │   └── file_api.py      # Metodi /api/file/ (upload media)
│   │
│   └── auth/                # Sistema licenze — modulo intercambiabile
│       ├── license_client.py  # Interfaccia: verify(mac, email) -> LicenseResult
│       ├── mac_helper.py      # Lettura indirizzo MAC della macchina
│       └── license_cache.py   # Cache locale risultato licenza (TTL configurabile)
│
├── assets/                  # Risorse statiche (icone, font, loghi)
├── data/                    # Presentazioni salvate localmente (JSON)
└── tests/                   # Test pytest
    ├── test_json_builder.py
    ├── test_auth_signer.py
    └── test_license_client.py
```

---

## Regole di architettura — SEMPRE rispettare

1. **`app/ui/` non importa mai da `app/api/`** — la UI chiama solo `app/core/`.
2. **`app/core/` non importa mai da `app/ui/` né da `app/api/`** — solo dataclass e logica pura.
3. **`app/api/` non importa mai da `app/ui/`** — riceve dati, restituisce dati.
4. **`app/auth/`** espone solo l'interfaccia `LicenseClient` con metodo `verify()`. L'implementazione interna è intercambiabile.
5. **Nessuna credenziale hardcoded** — tutto passa da variabili d'ambiente (`.env` letto con `python-dotenv`).
6. **Ogni file ha un solo scopo** — se un file supera 200 righe, probabilmente va spezzato.

---

## Variabili d'ambiente richieste

```env
# Credenziali API Huidu (ottenute da Huidu Technology)
HUIDU_SDK_KEY=xxxxxxxxxxxxxxxxxxxx
HUIDU_SDK_SECRET=xxxxxxxxxxxxxxxxxxxx

# Gateway Huidu (IP LAN del gateway nella rete del cliente)
HUIDU_GATEWAY_HOST=192.168.1.100
HUIDU_GATEWAY_PORT=30080

# Server licenze del committente
LICENSE_SERVER_URL=https://licenze.esempio.it/api/verify
LICENSE_SERVER_TIMEOUT=10

# App
APP_NAME=Huidu Manager
APP_VERSION=1.0.0
DEBUG=false
```

---

## Documentazione di riferimento

- `docs/HUIDU_API.md` — specifica completa API HTTP Huidu (endpoint, payload, firma)
- `docs/PRESENTATION_FORMAT.md` — struttura JSON presentazioni (program → area → item)
- `docs/LICENSE_MODULE.md` — interfaccia modulo licenze e come adattarlo
- `docs/UI_LAYOUT.md` — layout e comportamento atteso dell'interfaccia

---

## Dipendenze principali

```
PyQt6>=6.6.0
requests>=2.31.0
python-dotenv>=1.0.0
pyinstaller>=6.0.0   # solo per build Windows
pytest>=8.0.0
```

---

## Convenzioni codice

- **Python 3.11+** — usare `match/case`, `dataclass`, `TypeAlias` dove appropriato
- **Type hints ovunque** — ogni funzione ha signature completa
- **Docstring** su ogni classe e metodo pubblico (stile Google)
- **Nessun print()** in produzione — usare `logging` con livelli appropriati
- **Test** per ogni funzione in `app/core/` e `app/api/`
