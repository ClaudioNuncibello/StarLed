# SKILL: Gestione Contenuti Programma — Huidu HTTP API
> Skill per Antigravity / SLPlayer (Python 3.11 + PyQt6)  
> Scope: creazione e gestione programmi con contenuti testo, immagine, video sul controller Huidu

---

## CONTESTO E REGOLE GENERALI

- Un **programma** è l'unità di riproduzione. Contiene uno o più **layer (area)**, ognuno con contenuto (testo, immagine, video).
- **Un solo programma è attivo in riproduzione** per volta sul controller.
- Le **dimensioni dello schermo** (`screen.width`, `screen.height`) devono essere **lette dinamicamente** prima di costruire qualsiasi payload, tramite `getDeviceProperty`.
- Per default, ogni area occupa **fullscreen** (x=0, y=0, width=screen.width, height=screen.height).
- I file media (immagini/video) vengono **uploadati dal PC al controller** via `/api/file/`, poi referenziati per nome nel programma.
- Lo storico file è tenuto **sia nel DB locale di SLPlayer** che interrogando il dispositivo — i due devono essere sincronizzati.
- UUID dei programmi e delle aree devono essere **generati lato Python** (usa `uuid.uuid4()`).
- L'autenticazione usa **HMAC-MD5** (vedi skill `HUIDU_API.md` per i dettagli di firma).

---

## STEP 0 — LEGGERE DIMENSIONI SCHERMO

**Endpoint:** `POST /api/device/{device_id}`

```python
payload = {
    "method": "getDeviceProperty",
    "data": []
}
```

**Risposta rilevante:**
```json
{
    "data": [{
        "data": {
            "screen.width": "128",
            "screen.height": "64"
        }
    }]
}
```

**Pattern Python:**
```python
screen_w = int(response["data"][0]["data"]["screen.width"])
screen_h = int(response["data"][0]["data"]["screen.height"])
```

> ⚠️ Sempre leggere prima di costruire qualsiasi payload programma.

---

## STEP 1 — UPLOAD FILE MEDIA

**Endpoint:** `POST /api/file/{device_id}`  
**Content-Type:** `multipart/form-data`  
**Firma:** regola 2 — `sign = HMACMD5(sdkKey + date, sdkSecret)`

```python
import requests
from requests_toolbelt import MultipartEncoder

def upload_file(device_id, file_path, base_url, sdk_key, sign, date):
    url = f"{base_url}/api/file/{device_id}"
    m = MultipartEncoder(fields={"file": (os.path.basename(file_path), open(file_path, "rb"))})
    headers = {
        "sdkKey": sdk_key,
        "date": date,
        "sign": sign,
        "Content-Type": m.content_type
    }
    response = requests.post(url, data=m, headers=headers)
    return response.json()
```

**Risposta:**
```json
{
    "data": [{
        "message": "ok",
        "name": "video.mp4",
        "md5": "46318c4df4968f716061e5fc2ad22401",
        "size": "33417203"
    }],
    "message": "ok"
}
```

**Da salvare nel DB locale:**
```python
{
    "name": "video.mp4",       # nome file sul dispositivo
    "md5": "46318c...",        # usato per evitare re-upload
    "size": 33417203,          # usato come fileSize nel payload programma
    "uploaded_at": "2025-..."  # timestamp locale
}
```

> ℹ️ Se il file con lo stesso `md5` è già presente sul dispositivo, non serve re-uploadarlo — il controller lo riconosce tramite `fileMd5` + `fileSize` nel payload del programma.

---

## STEP 2 — CREARE PROGRAMMA (append)

**Endpoint:** `POST /api/program/{device_id}`  
**Firma:** regola 1 — `sign = HMACMD5(body + sdkKey + date, sdkSecret)`

### Struttura base fullscreen

```python
import uuid

program_uuid = str(uuid.uuid4()).upper()
area_uuid = str(uuid.uuid4()).upper()
item_uuid = str(uuid.uuid4()).upper()

payload = {
    "method": "append",
    "data": [
        {
            "name": nome_scelto_dall_utente,   # stringa libera, es. "Promozione Estate"
            "type": "normal",
            "uuid": program_uuid,
            "playControl": { ... },            # vedi STEP 3
            "area": [
                {
                    "uuid": area_uuid,
                    "x": 0,
                    "y": 0,
                    "width": screen_w,         # sempre da getDeviceProperty
                    "height": screen_h,
                    "item": [ { ... } ]        # vedi sezioni sotto per tipo contenuto
                }
            ]
        }
    ]
}
```

---

## STEP 3 — PLAY CONTROL (orari e durata)

Il nodo `playControl` va dentro ogni oggetto programma. È opzionale ma raccomandato.

```python
"playControl": {
    "duration": "00:00:30",          # durata visualizzazione (HH:MM:SS)
    "date": [
        {
            "start": "2025-01-01",   # data inizio validità
            "end": "2025-12-31"      # data fine validità
        }
    ],
    "time": [
        {
            "start": "09:00:00",     # orario inizio messa in onda
            "end": "18:00:00"        # orario fine messa in onda
        }
    ],
    "week": {
        "enable": "Mon,Tue,Wed,Thu,Fri"   # giorni attivi
    }
}
```

**Valori `week.enable`:** `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, `Sun`

> ℹ️ Se non si vuole limitare la messa in onda, omettere `playControl` o lasciare `date`/`time`/`week` vuoti.

---

## CONTENUTO TIPO: TESTO

### Item testo — parametri completi

```python
{
    "uuid": item_uuid,
    "type": "text",
    "string": "Testo da visualizzare",
    "multiLine": False,              # True = testo su più righe
    "PlayText": False,               # True = lettura vocale (TTS)
    "alignment": "center",           # "left" | "center" | "right"
    "valignment": "middle",          # "top" | "middle" | "bottom"
    "font": {
        "name": "宋体",              # nome font
        "size": 16,                  # dimensione in px
        "bold": False,
        "italic": False,
        "underline": False,
        "color": "#ffffff"           # colore in #RRGGBB
    },
    "effect": {
        "type": EFFECT_TYPE,         # vedi tabella effetti sotto
        "speed": 5,                  # 0=velocissimo, 8=lentissimo
        "hold": 5000                 # ms di pausa (per effetti statici/dissolvenza)
    }
}
```

### Tabella effetti testo — tutti i tipi

| `type` | Nome effetto | Note |
|--------|-------------|------|
| 0 | Statico — visualizzazione diretta | Testo fisso, usa `hold` per durata |
| 1 | Scorrimento sinistra (una volta) | Entra da destra, esce a sinistra |
| 2 | Scorrimento destra (una volta) | Entra da sinistra, esce a destra |
| 3 | Scorrimento su (una volta) | Entra dal basso, esce in alto |
| 4 | Scorrimento giù (una volta) | Entra dall'alto, esce in basso |
| 5 | Copertura sinistra | |
| 6 | Copertura destra | |
| 7 | Copertura su | |
| 8 | Copertura giù | |
| 9 | Copertura da angolo alto-sinistra | |
| 10 | Copertura da angolo basso-sinistra | |
| 11 | Copertura da angolo alto-destra | |
| 12 | Copertura da angolo basso-destra | |
| 13 | Apertura orizzontale | |
| 14 | Apertura verticale | |
| 15 | Chiusura orizzontale | |
| 16 | Chiusura verticale | |
| 17 | Dissolvenza (fade in/out) | |
| 18 | Veneziana verticale | |
| 19 | Veneziana orizzontale | |
| 20 | Nessuna pulizia schermo | |
| 25 | Effetto casuale | Sceglie random ad ogni ciclo |
| **26** | **Scorrimento continuo sinistro (loop)** | ⭐ Ticker — testo che scorre in loop |
| **27** | **Scorrimento continuo destro (loop)** | ⭐ Ticker invertito |
| **28** | **Scorrimento continuo su (loop)** | ⭐ Ticker verticale su |
| **29** | **Scorrimento continuo giù (loop)** | ⭐ Ticker verticale giù |
| **30** | **Lampeggio** | ⭐ Solo testo |

> ⚠️ Gli effetti 26–30 sono **esclusivi del tipo `text`** — non funzionano su immagini o video.  
> ⭐ = effetti più usati per display LED in contesto retail.

**Costanti Python consigliate:**
```python
class TextEffect:
    STATIC = 0
    SCROLL_LEFT = 1
    SCROLL_RIGHT = 2
    SCROLL_UP = 3
    SCROLL_DOWN = 4
    FADE = 17
    RANDOM = 25
    TICKER_LEFT = 26    # loop continuo
    TICKER_RIGHT = 27
    TICKER_UP = 28
    TICKER_DOWN = 29
    BLINK = 30
```

---

## CONTENUTO TIPO: IMMAGINE

### Item immagine — parametri completi

```python
{
    "uuid": item_uuid,
    "type": "image",
    "file": "nome_file.jpg",         # nome file sul dispositivo (dopo upload) O url remoto
    "fileMd5": "498c7bba...",        # md5 del file (obbligatorio)
    "fileSize": 337460,              # dimensione in bytes (opzionale ma raccomandato)
    "fit": "fill",                   # vedi opzioni sotto
    "effect": {
        "type": 0,                   # effetti 0-20, 25 (NON 26-30)
        "speed": 5,
        "hold": 5000
    }
}
```

### Opzioni `fit` per immagini

| `fit` | Comportamento |
|-------|--------------|
| `"fill"` | Scala proporzionalmente fino a coprire tutta l'area, ritaglia il centro — **raccomandato default** |
| `"center"` | Scala proporzionalmente fino a stare nell'area, bordi neri se proporzioni diverse |
| `"stretch"` | Distorce l'immagine per riempire esattamente l'area |
| `"tile"` | Ripete l'immagine in piastrella |

> ℹ️ Usare `"fill"` come default — è il comportamento più "professionale" per display LED retail.

---

## CONTENUTO TIPO: VIDEO

### Item video — parametri completi

```python
{
    "uuid": item_uuid,
    "type": "video",
    "file": "nome_file.mp4",         # nome file sul dispositivo (dopo upload) O url remoto
    "fileMd5": "46318c4d...",        # md5 del file (obbligatorio)
    "fileSize": 33417203,            # dimensione in bytes (opzionale ma raccomandato)
    "aspectRatio": True,             # True = mantieni proporzioni, False = stretch
    "effect": {
        "type": 0,
        "speed": 5,
        "hold": 0                    # per video hold tipicamente 0 (dura quanto il video)
    }
}
```

> ℹ️ Per video, `hold` nella `effect` è ignorato — la durata è quella del file video stesso.

---

## STEP 4 — AGGIORNARE PROGRAMMA ESISTENTE (update)

Usare `update` quando il programma esiste già e si vuole modificarne il contenuto.  
⚠️ L'`uuid` del programma **deve corrispondere** a quello esistente sul controller.

```python
payload = {
    "method": "update",
    "data": [
        {
            "uuid": uuid_programma_esistente,   # DEVE corrispondere
            "name": "Nuovo Nome",
            "type": "normal",
            "area": [ { ... } ]                 # nuova struttura completa
        }
    ]
}
```

---

## STEP 5 — LISTA PROGRAMMI SUL DISPOSITIVO

Per sincronizzare il DB locale con lo stato reale del controller:

```python
payload = {
    "method": "getAll",
    "data": [],
    "id": device_id
}
```

**Risposta:**
```json
{
    "data": [{
        "data": {
            "item": [
                {"uuid": "2A7C2C2C-...", "name": "Promozione Estate"},
                {"uuid": "B3F1A0D2-...", "name": "Orari Negozio"}
            ]
        }
    }]
}
```

---

## STORICO FILE — SINCRONIZZAZIONE DB LOCALE / DISPOSITIVO

### Schema DB locale (tabella `uploaded_files`)

```python
{
    "id": int,                  # PK locale
    "device_id": str,           # es. "A3L-D24-A05C1"
    "name": str,                # nome file sul dispositivo
    "md5": str,                 # hash md5
    "size": int,                # bytes
    "type": str,                # "image" | "video"
    "uploaded_at": str          # ISO datetime
}
```

### Logica anti-duplicato prima dell'upload

```python
def file_already_on_device(local_db, md5: str, device_id: str) -> dict | None:
    """
    Controlla nel DB locale se il file è già stato caricato su quel dispositivo.
    Ritorna il record se esiste, None altrimenti.
    """
    return local_db.query(
        "SELECT * FROM uploaded_files WHERE md5=? AND device_id=?",
        (md5, device_id)
    ).fetchone()
```

Se il file è già nel DB locale con quel `md5` per quel `device_id` → skip upload, usa direttamente `name` + `md5` + `size` dal DB nel payload del programma.

---

## PATTERN COMPLETO — ESEMPIO TESTO TICKER

```python
import uuid

screen_w, screen_h = get_screen_dimensions(device_id)  # STEP 0

payload = {
    "method": "append",
    "data": [{
        "name": "Offerta del Giorno",
        "type": "normal",
        "uuid": str(uuid.uuid4()).upper(),
        "playControl": {
            "duration": "00:00:15",
            "time": [{"start": "09:00:00", "end": "21:00:00"}],
            "week": {"enable": "Mon,Tue,Wed,Thu,Fri,Sat,Sun"}
        },
        "area": [{
            "uuid": str(uuid.uuid4()).upper(),
            "x": 0, "y": 0,
            "width": screen_w, "height": screen_h,
            "item": [{
                "uuid": str(uuid.uuid4()).upper(),
                "type": "text",
                "string": "SALDI ESTIVI — 50% su tutto!",
                "multiLine": False,
                "alignment": "center",
                "valignment": "middle",
                "font": {
                    "name": "宋体",
                    "size": 16,
                    "bold": True,
                    "italic": False,
                    "underline": False,
                    "color": "#ffff00"
                },
                "effect": {
                    "type": 26,    # ticker continuo sinistra
                    "speed": 4,
                    "hold": 0
                }
            }]
        }]
    }]
}
```

---

## ERRORI COMUNI DA EVITARE

| Errore | Causa | Fix |
|--------|-------|-----|
| Testo fuori schermo | `width`/`height` hardcoded invece di letti da `getDeviceProperty` | Sempre leggere dimensioni dinamicamente |
| `kUnsupportMethod` su upload | Firma usata è regola 1 invece di regola 2 | File upload usa `sign = HMACMD5(sdkKey+date, sdkSecret)` |
| File non trovato sul controller | Upload andato a buon fine ma nome file nel payload sbagliato | Usare esattamente il `name` restituito dalla risposta upload |
| `update` non ha effetto | UUID nel payload non corrisponde a quello sul controller | Prima `getAll`, poi usa UUID reale |
| Effetto 26-30 su immagine | Effetti ticker non supportati per immagini/video | Solo per `type: "text"` |