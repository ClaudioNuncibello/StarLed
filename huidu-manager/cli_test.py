#!/usr/bin/env python3
"""Script CLI completo per validare tutte le funzionalità backend Huidu (Fase 1).

Estende il menu del prototipo con:
- 6: Proprietà complete di uno schermo
- 7: Carica immagine di test e invia presentazione
- 8: Verifica licenza (MAC + email)
- 9: Imposta task pianificato accensione/spegnimento
- 10: Riavvia dispositivo

Usa i moduli backend implementati nelle TASK-02 → TASK-06.
Credenziali da .env.
"""

import os
import sys

from dotenv import load_dotenv

from app.api.device_api import DeviceApi
from app.api.file_api import FileApi
from app.api.huidu_client import HuiduApiError, HuiduClient
from app.api.program_api import ProgramApi
from app.auth.license_client import LicenseClient
from app.auth.mac_helper import get_mac_address
from app.core.file_uploader import FileUploader
from app.core.presentation_model import Presentation
from app.core.screen_manager import ScreenManager


def check_env() -> dict[str, str]:
    """Carica e valida le variabili d'ambiente. Falla se mancano."""
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
    print("\n╔═══════════════════════════════════════════════╗")
    print("║     Huidu Manager — CLI Completo (Fase 1)     ║")
    print("╠═══════════════════════════════════════════════╣")
    print("║  1 — Lista schermi connessi al gateway         ║")
    print("║  2 — Stato di uno schermo (acceso/spento, IP)  ║")
    print("║  3 — Invia testo allo schermo                  ║")
    print("║  4 — Accendi schermo                           ║")
    print("║  5 — Spegni schermo                            ║")
    print("║ ─────────── Fase 1 ────────────                ║")
    print("║  6 — Proprietà complete di uno schermo         ║")
    print("║  7 — Carica immagine e invia presentazione     ║")
    print("║  8 — Verifica licenza                          ║")
    print("║  9 — Imposta task accensione/spegnimento        ║")
    print("║ 10 — Riavvia dispositivo                       ║")
    print("║  0 — Esci                                      ║")
    print("╚═══════════════════════════════════════════════╝")


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
        timeout=5,
    )
    device_api = DeviceApi(client)
    program_api = ProgramApi(client)
    file_api = FileApi(client)
    file_uploader = FileUploader(file_api)
    screen_manager = ScreenManager(device_api)

    known_devices: list[str] = []

    while True:
        print_menu()
        scelta = input("Scelta: ").strip()

        if scelta == "0":
            print("Uscita.")
            break

        try:
            # ── Fase P ──────────────────────────────────────
            if scelta == "1":
                print("Recupero lista dispositivi...")
                devices = device_api.get_device_list()
                if devices:
                    print(f"✓ Trovati {len(devices)} dispositivi:")
                    for idx, d in enumerate(devices, 1):
                        print(f"  {idx}. {d}")
                    known_devices = devices
                else:
                    print("✓ Nessun dispositivo connesso al gateway.")

            elif scelta == "2":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print(f"Lettura stato per {dev}...")
                status = device_api.get_device_status(dev)
                open_status = status.get("screen.openStatus", "Sconosciuto")
                ip = status.get("eth.ip", "Sconosciuto")
                print("✓ Stato letto con successo:")
                print(f"  - Schermo acceso: {open_status}")
                print(f"  - IP Ethernet:    {ip}")

            elif scelta == "3":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                testo = input("Testo da inviare [default: 'Hello LED']: ").strip()
                if not testo:
                    testo = "Hello LED"
                print(f"Invio presentazione a {dev}...")
                pres = Presentation.simple_text("Demo CLI", testo, effect_type=1)
                program_api.send_presentation(dev, pres)
                print(f"✓ Presentazione '{testo}' inviata con successo.")

            elif scelta == "4":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print(f"Accensione schermo {dev}...")
                device_api.open_screen(dev)
                print("✓ Comando accensione inviato.")

            elif scelta == "5":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print(f"Spegnimento schermo {dev}...")
                device_api.close_screen(dev)
                print("✓ Comando spegnimento inviato.")

            # ── Fase 1 ──────────────────────────────────────
            elif scelta == "6":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print(f"Lettura proprietà complete di {dev}...")
                props = device_api.get_device_property(dev)
                print("✓ Proprietà lette con successo:")
                print(f"  - Nome:        {props.get('name', 'N/A')}")
                print(f"  - Dimensioni:  {props.get('screen.width', '?')}x{props.get('screen.height', '?')} px")
                print(f"  - Rotazione:   {props.get('screen.rotation', '?')}°")
                print(f"  - IP:          {props.get('eth.ip', 'N/A')}")
                print(f"  - Firmware:    {props.get('version.app', 'N/A')}")
                print(f"  - Volume:      {props.get('volume', 'N/A')}%")
                print(f"  - Luminosità:  {props.get('luminance', 'N/A')}%")
                print(f"  - Schermo:     {'Acceso' if props.get('screen.openStatus') == 'true' else 'Spento'}")

            elif scelta == "7":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                file_path = input("Percorso immagine (es. /path/to/image.png): ").strip()
                if not file_path:
                    print("✗ Percorso vuoto.")
                    continue
                if not os.path.exists(file_path):
                    print(f"✗ File non trovato: {file_path}")
                    continue

                # Upload con callback progresso
                print(f"Upload {os.path.basename(file_path)}...")

                def on_progress(sent: int, total: int) -> None:
                    if total > 0:
                        pct = sent * 100 // total
                        print(f"  Progresso: {pct}% ({sent}/{total} byte)")

                result = file_uploader.upload(dev, file_path, progress=on_progress)
                print(f"✓ File caricato: {result.name} (MD5: {result.md5})")

                # Leggi dimensioni schermo per la presentazione
                props = device_api.get_device_property(dev)
                w = int(props.get("screen.width", 128))
                h = int(props.get("screen.height", 64))

                # Crea e invia presentazione con immagine
                pres = Presentation.simple_image(
                    name="Immagine CLI",
                    file_url=result.url,
                    file_md5=result.md5,
                    file_size=result.size,
                    screen_width=w,
                    screen_height=h,
                )
                program_api.send_presentation(dev, pres)
                print(f"✓ Presentazione immagine inviata ({w}x{h}).")

            elif scelta == "8":
                mac = get_mac_address()
                print(f"MAC address rilevato: {mac}")
                email = input("Email di registrazione licenza: ").strip()
                if not email:
                    print("✗ Email vuota.")
                    continue
                print("Verifica licenza in corso...")
                license_client = LicenseClient()
                lic_result = license_client.verify(mac, email)
                status_display = {
                    "valid": "✓ VALIDA",
                    "invalid": "✗ NON VALIDA",
                    "expired": "✗ SCADUTA",
                    "not_found": "✗ NON TROVATA",
                    "server_error": "✗ ERRORE SERVER",
                    "network_error": "✗ ERRORE RETE",
                }
                print(f"  Stato: {status_display.get(lic_result.status.value, lic_result.status.value)}")
                if lic_result.message:
                    print(f"  Messaggio: {lic_result.message}")
                if lic_result.customer_name:
                    print(f"  Cliente: {lic_result.customer_name}")
                if lic_result.expiry_date:
                    print(f"  Scadenza: {lic_result.expiry_date}")
                if lic_result.max_screens:
                    print(f"  Max schermi: {lic_result.max_screens}")

            elif scelta == "9":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                print("Imposta fascia oraria spegnimento automatico:")
                start = input("  Ora inizio spegnimento (es. 22:00:00): ").strip()
                end = input("  Ora fine spegnimento (es. 06:00:00): ").strip()
                if not start or not end:
                    print("✗ Orari vuoti.")
                    continue
                tasks = {
                    "screen": [
                        {
                            "timeRange": f"{start}~{end}",
                            "dateRange": "2024-01-01~2030-12-31",
                            "data": "false",
                        }
                    ]
                }
                device_api.set_scheduled_task(dev, tasks)
                print(f"✓ Spegnimento automatico {start}→{end} impostato.")

            elif scelta == "10":
                dev = prompt_device_id(known_devices)
                if not dev:
                    continue
                confirm = input(f"Riavviare {dev}? (s/n): ").strip().lower()
                if confirm != "s":
                    print("Operazione annullata.")
                    continue
                delay = input("Secondi di attesa prima del riavvio [default: 5]: ").strip()
                delay_int = int(delay) if delay else 5
                device_api.reboot_device(dev, delay=delay_int)
                print(f"✓ Riavvio programmato tra {delay_int} secondi.")

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
