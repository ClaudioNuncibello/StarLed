#!/usr/bin/env python3
"""Script prototipo CLI per validare la comunicazione con i device Huidu (Fase P).

Usa i moduli backend implementati per interagire con uno schermo reale,
leggendo le credenziali dal file .env.
Fornisce un menu interattivo da terminale.
"""

import os
import sys

from dotenv import load_dotenv

from app.api.device_api import DeviceApi
from app.api.huidu_client import HuiduApiError, HuiduClient
from app.api.program_api import ProgramApi
from app.core.presentation_model import Presentation


def check_env() -> dict[str, str]:
    """Carica e valida le variabili d'ambiente. Falla se mancano in modo esplicito."""
    load_dotenv()
    required = [
        "HUIDU_GATEWAY_HOST",
        "HUIDU_GATEWAY_PORT",
        "HUIDU_SDK_KEY",
        "HUIDU_SDK_SECRET",
    ]
    env_vars = {}
    missing = []
    for var in required:
        val = os.getenv(var)
        if not val:
            missing.append(var)
        else:
            env_vars[var] = val

    if missing:
        print("✗ ERRORE: Variabili d'ambiente mancanti nel file .env:")
        for m in missing:
            print(f"  - {m}")
        print("\nAssicurati di aver configurato correttamente il file .env.")
        sys.exit(1)
    return env_vars


def print_menu() -> None:
    print("\n--- Huidu Manager Prototipo CLI ---")
    print("1 — Lista schermi connessi al gateway")
    print("2 — Stato di uno schermo (acceso/spento, IP)")
    print("3 — Invia testo 'Hello LED' allo schermo")
    print("4 — Accendi schermo")
    print("5 — Spegni schermo")
    print("0 — Esci")
    print("-----------------------------------")


def prompt_device_id(devices: list[str]) -> str | None:
    """Richiede all'utente di selezionare o inserire un device_id."""
    if not devices:
        val = input("Inserisci ID del dispositivo (es. C16-D00-A000F): ").strip()
        return val if val else None

    print("\nDispositivi noti:")
    for i, dev in enumerate(devices, 1):
        print(f"  [{i}] {dev}")
    val = input("\nScegli numero (o premi Invio per annullare): ").strip()
    if not val:
        return None
    try:
        idx = int(val) - 1
        if 0 <= idx < len(devices):
            return devices[idx]
        print("✗ Scelta non valida.")
        return None
    except ValueError:
        # Se ha inserito una stringa, usala direttamente
        return val


def main() -> None:
    # 1. Carica configurazione
    env = check_env()

    print("Inizializzazione client Huidu...")
    client = HuiduClient(
        host=env["HUIDU_GATEWAY_HOST"],
        port=int(env["HUIDU_GATEWAY_PORT"]),
        sdk_key=env["HUIDU_SDK_KEY"],
        sdk_secret=env["HUIDU_SDK_SECRET"],
        timeout=5,  # timeout breve per uso interattivo
        
    )
    device_api = DeviceApi(client)
    program_api = ProgramApi(client)

    known_devices: list[str] = []

    while True:
        print_menu()
        scelta = input("Scelta: ").strip()

        if scelta == "0":
            print("Uscita.")
            break

        try:
            if scelta == "1":
                print("Recupero lista dispositivi...")
                devices = device_api.get_device_list()
                if devices:
                    print(f"✓ Trovati {len(devices)} dispositivi:")
                    for idx, d in enumerate(devices, 1):
                        print(f"  {idx}. {d}")
                    known_devices = devices
                else:
                    print("✓ Nessun dispositivo attualmente connesso al gateway.")

            elif scelta == "2":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print(f"Lettura stato per {dev}...")
                status = device_api.get_device_status(dev)
                open_status = status.get("screen.openStatus", "Sconosciuto")
                ip = status.get("eth.ip", "Sconosciuto")
                print(f"✓ Stato letto con successo:")
                print(f"  - Schermo acceso: {open_status}")
                print(f"  - IP Ethernet:    {ip}")

            elif scelta == "3":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                testo = input("Testo da inviare [default: 'Hello LED']: ").strip()
                if not testo:
                    testo = "Hello LED"

                print(f"Invio presentazione a {dev} in corso...")
                pres = Presentation.simple_text("Demo CLI", testo, effect_type=1)  # Scorri sx
                program_api.send_presentation(dev, pres)
                print(f"✓ Presentazione '{testo}' inviata e attivata con successo.")

            elif scelta == "4":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print(f"Accensione schermo {dev}...")
                device_api.open_screen(dev)
                print("✓ Comando accensione inviato con successo.")

            elif scelta == "5":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print(f"Spegnimento schermo {dev}...")
                device_api.close_screen(dev)
                print("✓ Comando spegnimento inviato con successo.")

            else:
                print("✗ Scelta non valida, riprova.")

        except HuiduApiError as e:
            print(f"✗ ERRORE API HUIDU: {e.message}")
            if e.status_code:
                print(f"  (Codice HTTP: {e.status_code})")
        except Exception as e:
            print(f"✗ ERRORE IMPREVISTO: {str(e)}")


if __name__ == "__main__":
    main()
