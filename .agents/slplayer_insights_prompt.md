# Prompt di Implementazione: Integrazione Feature da SLplayer

Questo documento contiene le specifiche tecniche estratte dal progetto precedente (SLplayer) per aggirare i limiti del Gateway Huidu SDK e migliorare l'architettura di **ProgettoSTAR**.
Puoi usare questo file come **Prompt** passandolo all'AI per richiedere l'implementazione automatica di queste feature, senza dover leggere la vecchia codebase.

---

## 1. Batching degli ID (Ottimizzazione Rete LAN)

**Il Problema:** Se ci sono N schermi sulla rete (es. IP `192.168.1.33`), fare N chiamate HTTP POST per ottenere le proprietà o caricare un programma causa timeout e blocca il Gateway Huidu.
**La Soluzione:** L'API Huidu supporta il "batching" degli ID.

**Richiesta di Implementazione:**
Modifica i metodi in `app/api/device_api.py` (es. `get_device_property`, `replace_program`) per:
1. Accettare `device_ids: list[str]` invece del singolo `device_id: str`.
2. Unire gli ID con una virgola nel payload JSON: `device_id_str = ",".join(device_ids)`.
3. Inviare un'unica richiesta POST. Il gateway restituirà un array di risposte nel campo `data` per tutti i dispositivi.

*Esempio di Payload generato:*
```json
{
    "method": "getDeviceProperty",
    "id": "C16-A,C16-B,C16-C",
    "data": []
}
```

---

## 2. Il Trucco del `_metadata` (Round-Tripping)

**Il Problema:** L'SDK Huidu "brucia" le informazioni proprietarie. Se scarichi un programma esistente dal controller (tramite `download_program`), non avrai più i nomi dei file originali, gli ID del tuo database locale o regole di rendering specifiche dell'app.
**La Soluzione:** Iniettare un campo fantasma `_metadata`. Huidu lo ignora per la visualizzazione ma lo salva nel database del controller.

**Richiesta di Implementazione:**
In `app/core/presentation_model.py`, modifica il metodo `to_dict()` delle classi `Area` e `Item` (es. `TextItem`, `ImageItem`) per includere una chiave `_metadata` opzionale.
Quando il payload viene costruito in `json_builder.py`, il JSON finale dovrà avere questa struttura:

*Esempio di Payload generato:*
```json
{
    "x": 0,
    "y": 0,
    "width": 1920,
    "height": 1080,
    "item": [ ... ],
    "_metadata": {
        "app_db_id": "uuid-interno-app",
        "original_file_name": "video_promo.mp4",
        "custom_ui_properties": {
            "fit_mode": "stretch",
            "is_locked": true
        }
    }
}
```

---

## 3. Palinsesti Tipizzati (PlayControl)

**Il Problema:** Attualmente la classe `Presentation` (in `presentation_model.py`) ha un `play_control: dict | None` generico che delega all'utente la responsabilità di conoscere il formato Huidu.
**La Soluzione:** Mappare la schedulazione con Dataclass tipizzate in Python.

**Richiesta di Implementazione:**
Sostituire il dict generico con oggetti Python solidi che, quando serializzati, producano esattamente questa struttura Huidu a livello di "Program":

*Esempio di Payload generato (Regole Huidu):*
```json
"playControl": {
    "duration": "0:00:30",                      // Forza la durata fissa del programma
    "time": [
        {"start": "08:00:00", "end": "12:00:00"} // Array di fasce orarie in cui è visibile
    ],
    "week": {
        "enable": "Mon, Tue, Wed, Thur, Fri"     // Stringa CSV dei giorni della settimana
    },
    "date": [
        {"start": "2024-12-01", "end": "2024-12-31"} // Date di validità della campagna
    ]
}
```

---

## 4. Ottimizzazione Upload (Sync Offline con Hash)

**Il Problema:** Ricaricare file video da 100MB ogni volta che si cambia un testo nel palinsesto è inaccettabile.
**La Soluzione:** Evitare l'upload controllando l'hash.

**Richiesta di Implementazione (Logica da aggiungere nei Service):**
1. Implementare una funzione che calcola l'hash `SHA-256` della stringa JSON di un Programma (in formato `app/core/presentation_model.py`).
2. Mantenere un database locale (es. file JSON) che associa ad ogni `device_id` l'ultimo hash caricato con successo.
3. Prima di invocare `replace_program` o caricare file multimediali, confrontare l'hash locale con l'hash calcolato.
4. Procedere all'invio dell'HTTP POST solo se gli hash differiscono.
