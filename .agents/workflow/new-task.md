# New Task

Descrizione: Procedura standard per iniziare qualsiasi task del progetto.
Garantisce che l'agente parta sempre con il contesto corretto.

---

## Step 1 — Leggi il contesto

Prima di scrivere qualsiasi codice:
- Leggi @/docs/HUIDU_API.md se il task riguarda `app/api/`
- Leggi @/docs/PRESENTATION_FORMAT.md se il task riguarda presentazioni o `json_builder`
- Leggi @/docs/LICENSE_MODULE.md se il task riguarda `app/auth/`
- Leggi @/docs/UI_LAYOUT.md se il task riguarda `app/ui/`

---

## Step 2 — Identifica la fase corrente

Controlla in TASKS.md qual è il task da implementare e in quale fase si trova.

- Fasi 0, P, 1 → nessun import PyQt6 — verificare con `grep -r "PyQt6" app/api/ app/core/ app/auth/`
- Fase P → nessun test pytest, solo codice funzionante
- Fase 1 → test obbligatori per ogni modulo
- Fase 2 → solo dopo il checkpoint superato

---

## Step 3 — Implementa

Segui le istruzioni nel prompt del task in TASKS.md.
Rispetta le convenzioni definite nelle rules (`architecture.md`, `conventions.md`, `backend-first.md`).

---

## Step 4 — Verifica

Al termine del task:

```bash
# Verifica architettura (Fasi 0, P, 1)
grep -r "PyQt6" app/api/ app/core/ app/auth/

# Esegui i test se siamo in Fase 1 o successiva
python -m pytest tests/ -v

# Controlla che il file non superi 200 righe
wc -l <file-implementato>
```

---

## Step 5 — Commit

```bash
git add .
git commit -m "[TASK-NN] descrizione breve di cosa è stato implementato"
```
