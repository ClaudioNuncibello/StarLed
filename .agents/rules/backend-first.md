# Backend First

Always On — regola strategica che governa l'ordine di sviluppo dell'intero progetto.

## Ambiente di sviluppo

Windows 11 — sviluppo e produzione sullo stesso tipo di macchina.
Il SDK Huidu gateway è in ascolto su 127.0.0.1:30080.
Prima di avviare qualsiasi script verificare che il gateway sia attivo:

```cmd
netstat -an | findstr 30080
```

Se non restituisce nulla → avviare il Huidu Device SDK Gateway prima di procedere.

## Regola fondamentale

**PyQt6 non esiste nelle Fasi 0, P e 1.**

Non importare, non installare, non menzionare PyQt6 in nessun file di `app/api/`,
`app/core/` o `app/auth/` fino a quando il checkpoint tra Fase 1 e Fase 2 non è superato.

## Ordine di sviluppo — non negoziabile

```text
FASE 0  →  Setup e struttura vuota
FASE P  →  Prototipo rapido: 5 file + cli_test_proto.py
            ↓ validare su hardware reale prima di procedere
FASE 1  →  Completamento backend + test completi
            ↓ CHECKPOINT obbligatorio (vedi /checkpoint)
FASE 2  →  Interfaccia PyQt6 — solo dopo il checkpoint
FASE 3  →  Build e distribuzione Windows
```

## Perché questo ordine

Il prototipo rapido (Fase P) valida che la comunicazione con gli schermi Huidu
funziona davvero prima di investire tempo nel backend completo.
Problemi con credenziali o rete emergono in ore invece che in giorni.

## Cosa fare se si è tentati di anticipare la UI

Fermarsi. Tornare a TASKS.md. Verificare che il checkpoint sia superato.
Se il checkpoint non è superato, non iniziare nessun task della Fase 2.

## Commit per ogni task

Ogni task completato corrisponde a un commit con messaggio:
`[TASK-NN] descrizione breve`
