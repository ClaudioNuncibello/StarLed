# Code Conventions

Always On — convenzioni da rispettare in ogni file Python del progetto.

## Versione Python e sintassi

- Python 3.11+ — usare `match/case`, `dataclass`, `TypeAlias` dove appropriato
- Type hints su ogni funzione, metodo e variabile di modulo
- Docstring stile Google su ogni classe e metodo pubblico

## Logging

Mai usare `print()` in produzione.
Usare sempre il modulo `logging` con il livello appropriato:

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("dettaglio interno")
logger.info("operazione completata")
logger.warning("situazione anomala ma gestita")
logger.error("errore non recuperabile")
```

## Struttura header e dict

Gli header HTTP vanno creati come dizionario nuovo per ogni chiamata.
Mai riusare lo stesso dict tra chiamate diverse — rischio race condition con QThread.

```python
# SBAGLIATO
self.headers["date"] = new_date  # modifica in-place

# GIUSTO
headers = {**self.base_headers, "date": new_date}  # nuovo dict
```

## Thread e UI

Tutte le operazioni di rete vanno eseguite in `QThread`.
Mai chiamare API Huidu o server licenze nel thread UI principale.

## Test

Ogni funzione in `app/core/` e `app/api/` deve avere test corrispondenti in `tests/`.
Usare `unittest.mock` per simulare risposte HTTP — mai chiamare il gateway reale nei test.

## Timestamp RFC 7231

Non usare `strftime` per i timestamp HTTP — dipende dalla locale di sistema.
Usare sempre i nomi inglesi fissi:

```python
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
```
