# LICENSE_MODULE.md — Modulo licenze

Questo documento descrive l'interfaccia del modulo licenze e come adattarlo
al server del committente una volta noti i dettagli.

---

## Obiettivo

All'avvio dell'app, prima di mostrare l'interfaccia principale, il sistema deve:
1. Leggere l'indirizzo MAC della macchina
2. Chiedere all'utente l'email (o leggerla dalla cache locale)
3. Chiamare il server licenze con MAC + email
4. Se la risposta è positiva → aprire l'app
5. Se la risposta è negativa → mostrare messaggio di errore e chiudere

---

## Interfaccia pubblica — NON modificare

Il resto dell'app usa solo questa interfaccia. L'implementazione interna è libera.

```python
# app/auth/license_client.py

from dataclasses import dataclass
from enum import Enum

class LicenseStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"

@dataclass
class LicenseResult:
    status: LicenseStatus
    message: str = ""
    customer_name: str = ""
    expiry_date: str = ""         # formato ISO: "2026-12-31"
    max_screens: int = 1          # numero massimo schermi gestibili

class LicenseClient:
    """
    Interfaccia unica per la verifica licenze.
    Implementare questa classe in base al server del committente.
    """

    def verify(self, mac_address: str, email: str) -> LicenseResult:
        """
        Verifica la licenza sul server remoto.

        Args:
            mac_address: Indirizzo MAC nel formato XX:XX:XX:XX:XX:XX
            email: Email dell'utente inserita nel dialog di login

        Returns:
            LicenseResult con lo stato della licenza
        """
        raise NotImplementedError

    def get_cached_result(self) -> LicenseResult | None:
        """
        Restituisce il risultato in cache se ancora valido.
        Returns None se non c'è cache o è scaduta.
        """
        raise NotImplementedError
```

---

## Implementazione adattabile

Una volta noti i dettagli del server del committente, implementare seguendo questo template:

```python
# app/auth/license_client.py — IMPLEMENTAZIONE

import requests
import os
from .mac_helper import get_mac_address
from .license_cache import LicenseCache

class LicenseClient:

    def __init__(self):
        self.server_url = os.getenv("LICENSE_SERVER_URL")
        self.timeout = int(os.getenv("LICENSE_SERVER_TIMEOUT", "10"))
        self._cache = LicenseCache()

    def verify(self, mac_address: str, email: str) -> LicenseResult:
        # Prima controlla la cache
        cached = self._cache.get()
        if cached:
            return cached

        try:
            # ---- ADATTARE QUESTA SEZIONE AL SERVER DEL COMMITTENTE ----
            # Esempio generico — sostituire con il formato richiesto
            response = requests.post(
                f"{self.server_url}",
                json={
                    "mac": mac_address,
                    "email": email
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                # Adattare la lettura della risposta al formato del server
                result = LicenseResult(
                    status=LicenseStatus.VALID,
                    customer_name=data.get("customer_name", ""),
                    expiry_date=data.get("expiry_date", ""),
                    max_screens=data.get("max_screens", 1)
                )
            elif response.status_code == 404:
                result = LicenseResult(
                    status=LicenseStatus.NOT_FOUND,
                    message="Licenza non trovata per questo dispositivo"
                )
            elif response.status_code == 403:
                result = LicenseResult(
                    status=LicenseStatus.EXPIRED,
                    message="Licenza scaduta"
                )
            else:
                result = LicenseResult(
                    status=LicenseStatus.INVALID,
                    message=f"Errore server: {response.status_code}"
                )
            # ---- FINE SEZIONE DA ADATTARE ----

            # Salva in cache solo se valida
            if result.status == LicenseStatus.VALID:
                self._cache.save(result)

            return result

        except requests.exceptions.ConnectionError:
            return LicenseResult(
                status=LicenseStatus.NETWORK_ERROR,
                message="Impossibile raggiungere il server licenze"
            )
        except requests.exceptions.Timeout:
            return LicenseResult(
                status=LicenseStatus.NETWORK_ERROR,
                message="Timeout connessione al server licenze"
            )
```

---

## mac_helper.py

```python
# app/auth/mac_helper.py

import uuid
import re

def get_mac_address() -> str:
    """
    Restituisce il MAC address della macchina nel formato XX:XX:XX:XX:XX:XX.
    Usa l'interfaccia di rete principale.
    """
    mac_int = uuid.getnode()
    mac_hex = f"{mac_int:012x}"
    return ":".join(mac_hex[i:i+2] for i in range(0, 12, 2)).upper()
```

---

## license_cache.py

```python
# app/auth/license_cache.py

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

CACHE_FILE = Path.home() / ".huidu_manager" / "license_cache.json"
CACHE_TTL_HOURS = 24  # la cache dura 24 ore — ricontrolliamo ogni giorno

class LicenseCache:

    def save(self, result: "LicenseResult") -> None:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "status": result.status.value,
            "message": result.message,
            "customer_name": result.customer_name,
            "expiry_date": result.expiry_date,
            "max_screens": result.max_screens,
            "cached_at": datetime.now().isoformat()
        }
        CACHE_FILE.write_text(json.dumps(data))

    def get(self) -> "LicenseResult | None":
        if not CACHE_FILE.exists():
            return None
        try:
            data = json.loads(CACHE_FILE.read_text())
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
                return None  # Cache scaduta
            # Importazione circolare evitata con import locale
            from .license_client import LicenseResult, LicenseStatus
            return LicenseResult(
                status=LicenseStatus(data["status"]),
                message=data.get("message", ""),
                customer_name=data.get("customer_name", ""),
                expiry_date=data.get("expiry_date", ""),
                max_screens=data.get("max_screens", 1)
            )
        except Exception:
            return None

    def clear(self) -> None:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
```

---

## Checklist adattamento al server del committente

Quando ricevi i dettagli del server, verificare:

- [ ] Qual è l'endpoint esatto? (es. `POST /api/v1/license/verify`)
- [ ] Il formato del payload JSON? (i campi potrebbero chiamarsi diversamente da `mac`/`email`)
- [ ] Il server richiede autenticazione? (API key nell'header? Basic auth?)
- [ ] Qual è il formato della risposta di successo?
- [ ] Quali HTTP status code usa per licenza invalida / scaduta?
- [ ] Il server usa HTTPS? (Verificare certificato SSL)

Modificare **solo** il blocco marcato `---- ADATTARE QUESTA SEZIONE ----` in `license_client.py`.
Il resto dell'app non va toccato.
