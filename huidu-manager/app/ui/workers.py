import os
from PyQt6.QtCore import QThread, pyqtSignal
from app.api.huidu_client import HuiduApiError

class DeviceListWorker(QThread):
    """Aggiorna in background la lista schermi e lo stato (Fase 3)."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def run(self):
        try:
            screens = self.manager.screens.refresh()
            self.finished.emit(screens)
        except Exception as e:
            # Catturiamo le eccezioni di rete e notifichiamo la GUI
            msg = getattr(e, "message", str(e))
            self.error.emit(msg)


class ProgramFetchWorker(QThread):
    """Scarica i programmi da un dispositivo (Fase 3)."""
    finished = pyqtSignal(list, str) # Ritorna item list + device_id
    error = pyqtSignal(str)

    def __init__(self, manager, device_id):
        super().__init__()
        self.manager = manager
        self.device_id = device_id

    def run(self):
        try:
            # Lista dict programs
            programs = self.manager.programs_api.get_programs(self.device_id)
            self.finished.emit(programs, self.device_id)
        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Lettura programmi fallita: {msg}")


class FileUploadWorker(QThread):
    """Si occupa di upload di un file Media al dispositivo Huidu con check anti-duplicato locale.
    Se il file è già su Huidu (hash md5 su local db), non ricarica il tutto via HTTP."""
    finished = pyqtSignal(dict) # Restituisce dict record (MD5, name, size, type)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int) # sent, total

    def __init__(self, manager, device_id, file_path, item_type):
        super().__init__()
        self.manager = manager
        self.device_id = device_id
        self.file_path = file_path
        self.item_type = item_type # "image" or "video"

    def run(self):
        try:
            from app.api.file_api import compute_md5
            md5_hash, size = compute_md5(self.file_path)
            
            # 1. Controlla DB per evitare upload di duplicati preesistenti
            existing = self.manager.db.file_already_on_device(md5_hash, self.device_id)
            if existing:
                self.finished.emit(existing)
                return

            # 2. Upload al gateway se non presente (usa progress_callback)
            def on_progress(sent, total):
                self.progress.emit(sent, total)
                
            upload_res = self.manager.uploader.upload(
                self.device_id, 
                self.file_path, 
                progress=on_progress
            )
            
            # 3. Aggiorna DB per la storicizzazione file caricato
            self.manager.db.insert_uploaded_file(
                self.device_id, upload_res.name, upload_res.md5, upload_res.size, self.item_type
            )
            
            payload_data = {
                "name": upload_res.name,
                "md5": upload_res.md5,
                "size": upload_res.size,
                "type": self.item_type
            }
            self.finished.emit(payload_data)

        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Upload di {os.path.basename(self.file_path)} fallito: {msg}")


class ProgramPushWorker(QThread):
    """Invia o aggiorna un Programma sul relativo device (Fase 3)."""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, manager, device_id, presentation, method="update"):
        super().__init__()
        self.manager = manager
        self.device_id = device_id
        self.presentation = presentation
        self.method = method # "append" o "update" o "replace"

    def run(self):
        try:
            self.manager.programs_api.send_presentation(
                self.device_id, self.presentation, method=self.method
            )
            self.finished.emit()
        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Errore scrittura programma: {msg}")
