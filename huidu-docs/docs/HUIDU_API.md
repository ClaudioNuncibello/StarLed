# HUIDU_API.md — Specifica API HTTP Huidu

Questo documento descrive tutti gli endpoint HTTP esposti dal Gateway Huidu SDK (porta 30080).
È la fonte di verità per implementare `app/api/`.

---

## Prerequisiti

### Autenticazione — firma HMAC-MD5

Ogni richiesta deve includere questi header HTTP:

```
sdkKey:     <il tuo SDK Key ottenuto da Huidu>
date:       <data corrente in formato HTTP — es. Wed, 09 Aug 2023 07:27:44 GMT>
sign:       <firma calcolata — vedi sotto>
requestId:  <UUID v4 univoco per ogni richiesta>
Content-Type: application/json
```

**Calcolo firma (regola generale):**
```
sign = HMAC-MD5(body + sdkKey + date,  sdkSecret)
```

**Calcolo firma (solo upload file):**
```
sign = HMAC-MD5(sdkKey + date,  sdkSecret)
```

Dove:
- `body` = stringa JSON del corpo della richiesta (vuota `""` per richieste GET senza body)
- `sdkKey` = il tuo SDK Key
- `sdkSecret` = il tuo SDK Secret (NON viene trasmesso — solo usato per firmare)
- `date` = stesso valore dell'header `date`

### Indirizzamento dispositivi

Gli endpoint accettano l'ID del dispositivo in tre modi:
1. Nessun ID → opera sul dispositivo locale: `/api/device/`
2. Nel path: `/api/device/C16-D23-A0001,C16-D23-A0002`
3. Come query param: `/api/device/?id=C16-D23-A0001,C16-D23-A0002`

---

## 3.1 API Dispositivo — `/api/device/`

Metodo HTTP: **POST** per tutte le operazioni, **GET** solo per la lista.

### 3.1.1 Lista dispositivi online

```
GET 127.0.0.1:30080/api/device/list/
```

Response:
```json
{
  "total": "1",
  "message": "ok",
  "data": ["C16-D00-A000F"]
}
```

---

### 3.1.2 Proprietà dispositivo

```
POST 127.0.0.1:30080/api/device/{id}
```

Request body:
```json
{ "method": "getDeviceProperty", "data": [] }
```

Response (campi rilevanti):
```json
{
  "method": "getDeviceProperty",
  "message": "ok",
  "data": [{
    "id": "C16L-D00-A000F",
    "message": "ok",
    "data": {
      "name": "BoxPlayer",
      "screen.width": "128",
      "screen.height": "64",
      "screen.rotation": "0",
      "version.app": "7.10.78.1",
      "time": "2025-07-08 17:05:06",
      "volume": "100",
      "luminance": "100",
      "eth.ip": "192.168.90.153"
    }
  }]
}
```

---

### 3.1.3 Aggiorna proprietà dispositivo

```
POST 127.0.0.1:30080/api/device/{id}
```

Request body:
```json
{
  "method": "setDeviceProperty",
  "data": {
    "name": "MioSchermo",
    "volume": "80",
    "luminance": "70"
  }
}
```

---

### 3.1.4 Stato dispositivo

```
POST 127.0.0.1:30080/api/device/{id}
```

Request body:
```json
{ "method": "getDeviceStatus", "data": [] }
```

Campi rilevanti nella response:
- `screen.openStatus` — `"true"` / `"false"` (schermo acceso/spento)
- `eth.ip` — IP corrente
- `wifi.enabled` — Wi-Fi attivo

---

### 3.1.5 / 3.1.6 Task pianificati (schermo/volume/luminosità)

**Get:**
```json
{
  "method": "getScheduledTask",
  "data": ["screen", "volume", "luminance"]
}
```

**Set:**
```json
{
  "method": "setScheduledTask",
  "data": {
    "screen": [
      {
        "timeRange": "00:00:00~06:00:00",
        "dateRange": "2024-01-01~2025-12-31",
        "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
        "data": "false"
      }
    ],
    "luminance": [
      {
        "timeRange": "08:00:00~20:00:00",
        "dateRange": "2024-01-01~2025-12-31",
        "WeekFilter": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
        "data": "80"
      }
    ]
  }
}
```

---

### 3.1.10 Riavvio dispositivo

```json
{ "method": "rebootDevice", "data": { "delay": 5 } }
```

---

### 3.1.11 / 3.1.12 Accensione / spegnimento schermo

```json
{ "method": "openDeviceScreen", "data": {} }
{ "method": "closeDeviceScreen", "data": {} }
```

---

## 3.2 API Programmi — `/api/program/`

Metodo HTTP: **POST**

### Metodi disponibili

| method | Descrizione |
|---|---|
| `getAll` | Ottieni lista programmi sul dispositivo |
| `append` | Aggiungi uno o più programmi |
| `replace` | Sostituisce tutti i programmi esistenti |
| `update` | Aggiorna programmi esistenti per UUID |
| `remove` | Rimuove programmi per UUID |

### 3.2.2 Lista programmi

```json
{ "method": "getAll", "data": [], "id": "C16-D00-A000F" }
```

Response:
```json
{
  "method": "getAll",
  "message": "ok",
  "data": [{
    "id": "C16L-D00-A000F",
    "message": "ok",
    "data": {
      "item": [
        { "uuid": "2A7C2C2C-B2E3-475C-A501-0A3B7E6451E3", "name": "Programma 1" }
      ]
    }
  }]
}
```

---

### 3.2.1 Struttura playControl (pianificazione)

```json
"playControl": {
  "duration": "00:00:30",
  "week": { "enable": "Mon,Tue,Wed,Thu,Fri,Sat,Sun" },
  "date": [{ "start": "2024-01-01", "end": "2025-12-31" }],
  "time": [
    { "start": "08:00:00", "end": "20:00:00" }
  ]
}
```

---

## 3.3 API File — `/api/file/{id}`

Metodo HTTP: **POST** (multipart/form-data)

Header speciale: usa la **firma regola 2** (senza body).
Il campo `Content-Type` NON va impostato manualmente — `requests` lo genera
automaticamente con il boundary corretto per il multipart.

URL: `127.0.0.1:30080/api/file/{filename}` — il nome del file va nel path.

Request (form-data):
- campo `data`: il file binario con nome e content-type `application/octet-stream`

Response:
```json
{
  "data": [{
    "message": "ok",
    "name": "immagine.png",
    "md5": "9295dc4594e9fd82466c9c008a989e8e",
    "size": "21186",
    "data": "http://127.0.0.1:30080/api/file/immagine.png?..."
  }],
  "message": "ok"
}
```

Il campo `data` nella response è l'URL firmato da usare nel campo `file` dei programmi immagine/video.

### Calcolo MD5 prima dell'upload

Il MD5 va calcolato in chunks per gestire file grandi senza saturare la RAM:

```python
import hashlib
from pathlib import Path

def calcola_md5(file_path: str) -> tuple[str, int]:
    """Restituisce (md5_hex, dimensione_bytes)."""
    path = Path(file_path)
    md5 = hashlib.md5()
    size = 0
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
            size += len(chunk)
    return md5.hexdigest(), size
```

### Firma su URL (query string)

Gli URL firmati restituiti da `/api/file/` includono già la firma come
parametri query. Se in futuro serve generare URL firmati manualmente
(es. per link diretti ai file), la firma va nei parametri URL invece
che negli header:

```python
# La firma è identica — cambia solo dove viene messa
sign = HMAC-MD5(sdkKey + date, sdkSecret)

# Nei parametri URL invece che negli header:
url += f"?sdkKey={sdk_key}&date={date}&sign={sign}"
```

> **Nota implementativa:** aggiungere un metodo `sign_url(url)` ad `AuthSigner`
> che restituisce l'URL con la firma appesa come query string.

---

## 3.4 Screenshot — `/api/screenshot/{id}`

Metodo HTTP: **GET**

Request body:
```json
{ "method": "screenshot", "data": {} }
```

Response: immagine in base64.

---

## 3.5 Canale XML — `/raw/{id}` ⚠️ DA VERIFICARE

> **Attenzione:** questo canale è stato osservato in un progetto open source
> che usa le API Huidu, ma non è documentato ufficialmente nella specifica v1.0.
> I metodi qui sotto **vanno verificati empiricamente** sul dispositivo reale
> prima di implementarli in produzione.

Alcune operazioni avanzate userebbero un endpoint alternativo con body XML
invece del JSON standard:

```
POST 127.0.0.1:30080/raw/{device_id}
Content-Type: application/xml
```

**Operazioni osservate su questo canale:**

`GetTimeInfo` / `SetTimeInfo` — ora e fuso orario
`GetLuminancePloy` / `SetLuminancePloy` — curva luminosità automatica
`GetProgram` — lista programmi in formato XML
`AddFiles` — invio file locali al dispositivo (vedi sotto)

**Esempio body XML:**
```xml
<?xml version='1.0' encoding='utf-8'?>
<sdk guid="##GUID">
    <in method="GetTimeInfo"/>
</sdk>
```

### AddFiles — upload con polling ⚠️ DA VERIFICARE

I dispositivi Huidu potrebbero scaricare i file in modo **asincrono**.
Il pattern osservato è:

```
1. POST /raw/{id} con body XML AddFiles
2. Il dispositivo risponde: result="kDownloading" o "kDownloadingFile"
3. Ripeti la stessa chiamata ogni 2 secondi
4. Quando risponde result="kSuccess" → upload completato
5. Timeout dopo 300 secondi se non completa
```

**IMPORTANTE:** non implementare questo finché non è verificato su hardware reale.
Usare prima il canale JSON `/api/file/` (sezione 3.3) che è documentato ufficialmente.

---

## Codici di risposta

**Canale JSON:** tutte le API restituiscono `"message": "ok"` in caso di successo.
In caso di errore il campo `message` contiene la descrizione dell'errore.
Il campo `data` per il singolo dispositivo contiene `"kSuccess"` se l'operazione è riuscita.

**Canale XML:** la risposta contiene un attributo `result` nel tag `<out>`:
- `kSuccess` → operazione completata
- `kDownloading` / `kDownloadingFile` → operazione in corso, ripollare
- qualsiasi altro valore → errore

---

## Note implementative per `app/api/`

- Tutti i timestamp `date` usano formato RFC 7231 con nomi inglesi fissi
  (non usare `strftime` che dipende dalla locale di sistema):
  ```python
  weekdays = ("Mon","Tue","Wed","Thu","Fri","Sat","Sun")
  months = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
  ```
- Il `requestId` è un UUID v4 generato per ogni chiamata: `str(uuid.uuid4())`
- Gli header vanno creati come **dizionario nuovo per ogni chiamata** — mai
  riusare lo stesso dict tra chiamate diverse (rischio race condition con QThread)
- Timeout consigliato: 10 secondi per operazioni normali, 30 secondi per upload file
- In caso di `message != "ok"` sollevare eccezione custom `HuiduApiError`
- Gestire sempre `requests.exceptions.ConnectionError` (gateway non raggiungibile)
- **Mai loop infiniti**: ogni retry o polling deve avere `max_retries` o `timeout` esplicito
