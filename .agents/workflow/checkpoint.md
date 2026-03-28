# Checkpoint

Descrizione: Verifica obbligatoria tra Fase 1 e Fase 2.
Tutti e tre i controlli devono passare. Se anche uno fallisce, non iniziare la Fase 2.

---

## Step 1 — Esegui i test

```bash
python -m pytest tests/ -v
```

Risultato atteso: tutti i test passano, zero fallimenti.

Se ci sono fallimenti → identifica il modulo, correggilo, riesegui.
Non procedere finché `pytest` non è verde.

---

## Step 2 — Verifica CLI completo

```bash
python cli_test.py
```

Esegui manualmente almeno queste opzioni contro il gateway reale:

- Lista schermi (opzione 1)
- Proprietà schermo (opzione 6)
- Screenshot (opzione 8)
- Verifica licenza (opzione 9)

Se qualcosa crasha → correggi prima di procedere.

---

## Step 3 — Verifica assenza PyQt6 nel backend

```bash
grep -r "PyQt6" app/api/ app/core/ app/auth/
```

Equivalente Windows (cmd):

```cmd
findstr /r /s "PyQt6" app\api\*.py app\core\*.py app\auth\*.py
```

Risultato atteso: nessun output (nessun file importa PyQt6).

Se escono risultati → rimuovi gli import e riesegui il check.

---

## Step 4 — Risultato

Se tutti e tre i controlli passano:

- Scrivi un commit: `[CHECKPOINT] Fase 1 completata — tutti i check passano`
- Procedi con `/fase-2`

Se anche solo uno fallisce:

- Non iniziare la Fase 2
- Torna al task corrispondente in `/fase-1` e correggi
