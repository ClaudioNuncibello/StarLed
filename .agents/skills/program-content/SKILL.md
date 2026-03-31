---
name: program-content-management
description: Flusso operativo per creare e aggiornare programmi con testo, immagine e video su controller Huidu. Usare quando si implementa upload file, creazione programma con append/update, lettura dimensioni schermo, storico file caricati, o logica anti-duplicato MD5. Per la struttura JSON dei payload e le dataclass Python vedere presentation-format.
---

# PROGRAM_CONTENT_MANAGEMENT.md — Flusso operativo contenuti

> Per la struttura JSON completa (campi, tipi, dataclass) → vedere `presentation-format`.  
> Questa skill copre esclusivamente il **flusso procedurale**: lettura schermo, upload, creazione programma, sincronizzazione DB.

---

## REGOLE GENERALI

- **Un solo programma è attivo** in riproduzione per volta sul controller.
- Le **dimensioni dello schermo devono essere lette dinamicamente** prima di costruire qualsiasi payload (→ STEP 0).
- Per default ogni area è **fullscreen**: `x=0, y=0, width=screen_w, height=screen_h`.
- I file media vengono **uploadati dal PC al controller** via `/api/file/`, poi referenziati per nome nel programma.
- Lo storico file è tenuto **sia nel DB locale di SLPlayer che sul dispositivo** — i due devono essere sincronizzati.
- UUID di programmi e aree generati lato Python con `uuid.uuid4()`.
- Autenticazione HMAC-MD5 → vedere `HUIDU_API.md`.

---

## STEP 0 — LEGGERE DIMENSIONI SCHERMO

**Endpoint:** `POST /api/device/{device_id}`  
**Firma:** regola 1

```python
payload = {
    "method": "getDeviceProperty",
    "data": []
}

screen_w = int(response["data"][0]["data"]["screen.width"])
screen_h = int(response["data"][0]["data"]["screen.height"])
```

> ⚠️ Obbligatorio prima di ogni costruzione payload. Non hardcodare mai le dimensioni.

---

## STEP 1 — UPLOAD FILE MEDIA

**Endpoint:** `POST /api/file/{device_id}`  
**Content-Type:** `multipart/form-data`  
**Firma:** regola 2 — `sign = HMACMD5(sdkKey + date, sdkSecret)` ← diversa dalla regola standard

```python
from requests_toolbelt import MultipartEncoder

def upload_file(device_id, file_path, base_url, sdk_key, sign, date):
    url = f"{base_url}/api/file/{device_id}"
    m = MultipartEncoder(fields={
        "file": (os.path.basename(file_path), open(file_path, "rb"))
    })
    headers = {
        "sdkKey": sdk_key,
        "date": date,
        "sign": sign,
        "Content-Type": m.content_type
    }
    return requests.post(url, data=m, headers=headers).json()
```

**Risposta rilevante:**

```json
{
    "data": [{
        "message": "ok",
        "name": "video.mp4",
        "md5": "46318c4df4968f716061e5fc2ad22401",
        "size": "33417203"
    }]
}
```

> Il campo `name` restituito è il nome con cui il file è referenziabile nel payload programma.

### Logica anti-duplicato (da eseguire PRIMA dell'upload)

```python
def file_already_on_device(db, md5: str, device_id: str) -> dict | None:
    """Ritorna il record DB se il file è già stato caricato, None altrimenti."""
    return db.query(
        "SELECT * FROM uploaded_files WHERE md5=? AND device_id=?",
        (md5, device_id)
    ).fetchone()
```

Se esiste → skip upload, usa `name` + `md5` + `size` dal DB direttamente nel payload.

---

## STEP 2 — CREARE PROGRAMMA (append)

**Endpoint:** `POST /api/program/{device_id}`  
**Firma:** regola 1  
**Struttura JSON completa** → vedere `presentation-format`

```python
import uuid

payload = {
    "method": "append",
    "data": [{
        "name": nome_scelto_dall_utente,    # stringa libera, es. "Promozione Estate"
        "type": "normal",
        "uuid": str(uuid.uuid4()).upper(),
        "playControl": build_play_control(...),  # vedi STEP 3
        "area": [{
            "uuid": str(uuid.uuid4()).upper(),
            "x": 0,
            "y": 0,
            "width": screen_w,    # da STEP 0
            "height": screen_h,   # da STEP 0
            "item": [build_item(...)]  # TextItem | ImageItem | VideoItem da presentation-format
        }]
    }]
}
```

---

## STEP 3 — PLAY CONTROL

```python
def build_play_control(
    duration_s: int,
    time_ranges: list[tuple[str, str]],   # es. [("09:00:00", "18:00:00")]
    date_ranges: list[tuple[str, str]],   # es. [("2025-01-01", "2025-12-31")]
    weekdays: list[str]                   # es. ["Mon","Tue","Wed","Thu","Fri"]
) -> dict:
    return {
        "duration": f"00:{duration_s//60:02d}:{duration_s%60:02d}",
        "time": [{"start": s, "end": e} for s, e in time_ranges],
        "date": [{"start": s, "end": e} for s, e in date_ranges],
        "week": {"enable": ",".join(weekdays)}
    }
```

Valori weekdays validi: `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, `Sun`

> Se nessuna restrizione oraria → omettere `playControl` dal payload o passare `None`.

---

## STEP 4 — AGGIORNARE PROGRAMMA ESISTENTE (update)

**Endpoint:** `POST /api/program/{device_id}`  
**Firma:** regola 1

```python
payload = {
    "method": "update",
    "data": [{
        "uuid": uuid_programma_esistente,   # ⚠️ DEVE corrispondere a quello sul controller
        "name": nuovo_nome,
        "type": "normal",
        "area": [...]
    }]
}
```

> ⚠️ Prima di `update` eseguire sempre `getAll` (STEP 5) per recuperare l'UUID reale del programma.

---

## STEP 5 — LISTA PROGRAMMI E SINCRONIZZAZIONE

**Endpoint:** `POST /api/program/{device_id}`  
**Firma:** regola 1

```python
payload = {
    "method": "getAll",
    "data": [],
    "id": device_id
}

# Estrarre lista programmi
programs = response["data"][0]["data"]["item"]
# → [{"uuid": "2A7C2C2C-...", "name": "Promozione Estate"}, ...]
```

Usare per:

- Recuperare UUID reali prima di `update`
- Sincronizzare il DB locale con lo stato del controller
- Verificare che un `append` sia andato a buon fine

---

## STORICO FILE — SCHEMA DB LOCALE

**Tabella:** `uploaded_files`

```python
{
    "id": int,           # PK
    "device_id": str,    # es. "A3L-D24-A05C1"
    "name": str,         # nome file sul dispositivo (da risposta upload)
    "md5": str,          # hash md5
    "size": int,         # bytes
    "type": str,         # "image" | "video"
    "uploaded_at": str   # ISO datetime
}
```

### Flusso completo upload + registrazione

```python
def upload_and_register(db, device_id, file_path, file_type):
    md5 = compute_md5(file_path)
    size = os.path.getsize(file_path)

    # 1. Controlla se già presente
    existing = file_already_on_device(db, md5, device_id)
    if existing:
        return existing  # usa direttamente

    # 2. Upload
    result = upload_file(device_id, file_path, ...)
    file_record = result["data"][0]

    # 3. Salva nel DB locale
    db.insert("uploaded_files", {
        "device_id": device_id,
        "name": file_record["name"],
        "md5": file_record["md5"],
        "size": int(file_record["size"]),
        "type": file_type,
        "uploaded_at": datetime.now().isoformat()
    })

    return file_record
```

---

## ERRORI COMUNI

| Errore | Causa | Fix |
|--------|-------|-----|
| Testo/immagine fuori schermo | `width`/`height` hardcoded | Sempre leggere da `getDeviceProperty` (STEP 0) |
| `kUnsupportMethod` su upload | Firma regola 1 usata invece di regola 2 | Upload file usa `sign = HMACMD5(sdkKey+date, sdkSecret)` |
| File non trovato sul controller | Nome file nel payload sbagliato | Usare esattamente il `name` restituito dalla risposta upload |
| `update` non ha effetto | UUID nel payload non corrisponde | Prima `getAll`, poi usa UUID reale dal controller |
| Effetto ticker (26-30) su immagine | Non supportato per immagini/video | Ticker solo su `type: "text"` — vedere tabella effetti in `presentation-format` |
