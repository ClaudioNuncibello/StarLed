# Fase 3 — Build e Distribuzione Windows

Descrizione: Pacchettizza l'applicazione come eseguibile Windows
con PyInstaller e prepara lo script di build.

Prerequisito: Fase 2 completata, smoke test manuale superato.

---

## Step 1 — Configurazione PyInstaller (TASK-16)

Crea `huidu_manager.spec` con:
- Modalità single-file (`onefile=True`)
- Inclusione della cartella `assets/` con le risorse statiche
- Gestione del caricamento `.env` in modalità frozen via `sys._MEIPASS`
- Nome output: `HuiduManager.exe`

```python
# Esempio gestione .env in modalità frozen
import sys, os
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
```

---

## Step 2 — Script di build

Crea `build.bat` nella root:

```bat
@echo off
echo Building HuiduManager...
pip install pyinstaller
pyinstaller huidu_manager.spec --clean
echo Done. Output in dist\HuiduManager.exe
```

---

## Step 3 — Test su macchina Windows pulita

Copia `dist/HuiduManager.exe` su una macchina Windows senza Python installato.
Crea un file `.env` nella stessa cartella dell'eseguibile con le credenziali reali.

Verifica:
- L'app si avvia senza errori
- LoginDialog appare correttamente
- La comunicazione con il gateway Huidu funziona
- L'invio di una presentazione funziona end-to-end

---

## Step 4 — Commit finale

```bash
git tag v1.0.0
git push origin v1.0.0
```
