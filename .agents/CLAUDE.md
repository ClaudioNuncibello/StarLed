# CLAUDE.md — Contesto progetto Huidu Manager

## Stack tecnologico

| Componente           | Tecnologia                                 |
| -------------------- | ------------------------------------------ |
| Linguaggio           | Python 3.11+                               |
| UI (Fase 2)          | PyQt6                                      |
| HTTP                 | requests                                   |
| Autenticazione API   | HMAC-MD5 custom (AuthSigner)               |
| Config               | python-dotenv (.env)                       |
| Test                 | pytest + unittest.mock                     |
| Build (Fase 3)       | PyInstaller                                |
| Ambiente di sviluppo | Windows 11 — stesso ambiente di produzione |

## Variabili d'ambiente

Il file `.env` nella root `huidu-manager/` contiene le credenziali e la configurazione del gateway.
Non va mai committato — usare `.env.example` come riferimento.

```env
HUIDU_GATEWAY_HOST=127.0.0.1
HUIDU_GATEWAY_PORT=30080
```

> **Nota:** il SDK Huidu gateway gira in locale sul PC Windows sulla porta 30080.
> In sviluppo si usa sempre `127.0.0.1`.
> In produzione è lo stesso setup — la tua app e il gateway girano sulla stessa macchina Windows del cliente.

## Prerequisiti ambiente Windows

- Python 3.11+ installato con "Add Python to PATH" spuntato
- Git for Windows
- Huidu Device SDK Gateway installato e avviato (porta 30080)
- HDPlayer installato e configurato per il pannello A3L
- Pannello testato: A3L-D24-A05C1

## Struttura progetto

```text
huidu-manager/
├── app/
│   ├── api/       → comunicazione HTTP con gateway Huidu
│   ├── core/      → modelli dati e logica pura
│   ├── auth/      → modulo licenze
│   └── ui/        → interfaccia PyQt6 (solo Fase 2+)
├── tests/         → test pytest
├── assets/        → risorse statiche (icone, QSS)
├── data/          → dati persistenti locali
├── cli_test_proto.py → script CLI prototipo (Fase P)
├── main.py        → entry point
└── .env           → credenziali (non committato)
```
