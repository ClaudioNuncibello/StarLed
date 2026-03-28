# Architecture Rules

Always On — queste regole si applicano a ogni task senza eccezioni.

## Separazione dei layer

1. `app/ui/` non importa mai da `app/api/` — la UI chiama solo `app/core/`
2. `app/core/` non importa mai da `app/ui/` né da `app/api/` — solo dataclass e logica pura
3. `app/api/` non importa mai da `app/ui/` — riceve dati, restituisce dati
4. `app/auth/` espone solo `LicenseClient.verify()` — l'implementazione interna è intercambiabile

## Verifica obbligatoria prima di chiudere qualsiasi task nelle Fasi 0, P, 1

```bash
grep -r "PyQt6" app/api/ app/core/ app/auth/
# deve restituire: nessun risultato
```

Equivalente Windows (cmd):

```cmd
findstr /r /s "PyQt6" app\api\*.py app\core\*.py app\auth\*.py
REM deve restituire: nessun risultato
```

## Dimensione dei file

Se un file supera 200 righe, probabilmente va spezzato in moduli più piccoli.
Segnalarlo e proporre la suddivisione prima di procedere.

## Gestione errori

- Sollevare sempre `HuiduApiError` in caso di `message != "ok"` dalla API
- Gestire sempre `requests.exceptions.ConnectionError`
- Mai loop infiniti: ogni retry o polling deve avere `max_retries` o `timeout` esplicito
- Timeout: 10 secondi operazioni normali, 30 secondi upload file

## Credenziali

Nessuna credenziale hardcoded. Tutto passa da variabili d'ambiente lette con `python-dotenv`.
Il file `.env` non va mai committato. Usare solo `.env.example`.
