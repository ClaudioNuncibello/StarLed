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

class PlaylistPushWorker(QThread):
    progress = pyqtSignal(str) # operation info
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, manager, device_id, presentation_data, screen_w, screen_h, method="append", active_uuid=None):
        super().__init__()
        self.manager = manager
        self.device_id = device_id
        self.presentation_data = presentation_data  # Può essere un dict o una list[dict]
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.method = method  # "append" = accoda, "replace" = manda in onda esclusivo
        self.active_uuid = active_uuid

    def run(self):
        try:
            import os
            from app.core.presentation_model import (
                Presentation, Area, TextItem, ImageItem, VideoItem, DigitalClockItem, Effect, Font
            )
            
            def build_presentation(pres_data: dict, is_active: bool) -> Presentation | None:
                items_data = pres_data.get("items", [])
                pres_name = pres_data.get("name", "Playlist")
                
                built_items = []
                for i, item in enumerate(items_data):
                    itype = item.get("type", "").lower()
                    effect_cfg = item.get("effect", {})
                    effect = Effect(type=effect_cfg.get("type", 0), speed=effect_cfg.get("speed", 5), hold=effect_cfg.get("hold", 5000))
                    
                    if itype in ("image", "video"):
                        file_path = item.get("file")
                        if file_path and os.path.exists(file_path):
                            self.progress.emit(f"Upload media: {os.path.basename(file_path)}...")
                            up_res = self.manager.uploader.upload(self.device_id, file_path)
                            
                            if itype == "image":
                                fit = item.get("fit", "stretch")
                                built_items.append(ImageItem(file=up_res.url, fileMd5=up_res.md5, fileSize=up_res.size, fit=fit, effect=effect))
                            else:
                                built_items.append(VideoItem(file=up_res.url, fileMd5=up_res.md5, fileSize=up_res.size, effect=effect))
                        else:
                            print(f"Skipping empty or missing file: {file_path}")
                    elif itype == "text":
                        text_str = item.get("string", "")
                        font_cfg = item.get("font", {})
                        font = Font(
                            name=font_cfg.get("name", "Arial"),
                            size=font_cfg.get("size", 14),
                            bold=font_cfg.get("bold", False),
                            italic=font_cfg.get("italic", False),
                            underline=font_cfg.get("underline", False),
                            color=font_cfg.get("color", "#ffffff")
                        )
                        multi_line = item.get("multi_line", False)
                        play_text = item.get("play_text", False)
                        align_str = item.get("alignment", "middle,center")
                        parts = align_str.split(",")
                        valign = parts[0] if len(parts) > 0 else "middle"
                        align = parts[1] if len(parts) > 1 else "center"
                        
                        built_items.append(TextItem(
                            string=text_str,
                            font=font,
                            effect=effect,
                            multiLine=multi_line,
                            alignment=align,
                            valignment=valign,
                            PlayText=play_text
                        ))
                    elif itype in ("digitalclock", "clock", "dialclock"):
                        built_items.append(DigitalClockItem())

                if not built_items:
                    return None

                areas = []
                built_items.reverse()
                for item in built_items:
                    areas.append(Area(0, 0, self.screen_w, self.screen_h, item=[item]))

                pres = Presentation(name=pres_name, area=areas, uuid=pres_data.get("uuid"))
                if not is_active:
                    pres.play_control = {"date": [{"start": "2000-01-01", "end": "2000-01-02"}]}
                return pres

            if self.method == "replace":
                self.progress.emit("Elaborazione del nuovo palinsesto...")
                if isinstance(self.presentation_data, list):
                    all_pres_data = self.presentation_data
                else:
                    all_pres_data = [self.presentation_data]
                    
                built_presentations = []
                for p_data in all_pres_data:
                    # Includi solo se ha elementi e un UUID valido
                    if not p_data.get("items"):
                        continue
                    
                    is_active = (p_data.get("uuid") == self.active_uuid)
                    pres = build_presentation(p_data, is_active)
                    if pres:
                        built_presentations.append(pres)
                
                if not built_presentations:
                    self.error.emit("Nessuna presentazione valida da inviare.")
                    return
                
                self.progress.emit(f"Invio di {len(built_presentations)} programmi al dispositivo...")
                self.manager.programs_api.send_presentations(self.device_id, built_presentations, method="replace")
                
            else:
                self.progress.emit("Invio programma al dispositivo...")
                pres = build_presentation(self.presentation_data, is_active=True)
                if not pres:
                    self.error.emit("Nessun livello valido per l'invio.")
                    return
                self.manager.programs_api.send_presentation(self.device_id, pres, method="append")
                
            self.finished.emit()
            
        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Errore push playlist: {msg}")

class ProgramRemoveWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, manager, device_id, uuids):
        super().__init__()
        self.manager = manager
        self.device_id = device_id
        self.uuids = uuids

    def run(self):
        try:
            self.manager.programs_api.remove_presentation(self.device_id, self.uuids)
            self.finished.emit()
        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Errore rimozione: {msg}")

class ProgramRenameWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, manager, device_id, uuid_id, new_name):
        super().__init__()
        self.manager = manager
        self.device_id = device_id
        self.uuid_id = uuid_id
        self.new_name = new_name

    def run(self):
        try:
            payload = {
                "method": "update",
                "id": self.device_id,
                "data": [{
                    "uuid": self.uuid_id,
                    "name": self.new_name,
                    "type": "normal"
                }]
            }
            res = self.manager.programs_api._client.post("/api/program/", payload)
            self.manager.programs_api._check_device_response(res, self.device_id)
            self.finished.emit()
        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Errore rinomina: {msg}")


class DiscoveryWorker(QThread):
    """Scansiona la subnet locale alla ricerca di gateway Huidu (porta 30080).

    Emette ``finished`` con la lista di ``DiscoveredGateway`` trovati,
    o ``error`` in caso di problemi di rete.

    Example::

        worker = DiscoveryWorker(sdk_key="k", sdk_secret="s")
        worker.finished.connect(on_gateways_found)
        worker.error.connect(on_error)
        worker.start()
    """

    finished = pyqtSignal(list)   # list[DiscoveredGateway]
    error = pyqtSignal(str)
    progress = pyqtSignal(str)    # messaggio di stato opzionale

    def __init__(self, sdk_key: str, sdk_secret: str, *, subnet: str | None = None):
        """Inizializza il worker con le credenziali SDK.

        Args:
            sdk_key: Chiave SDK Huidu.
            sdk_secret: Segreto SDK Huidu.
            subnet: Subnet CIDR opzionale (es. ``"192.168.1.0/24"``).
                    Se ``None``, viene rilevata automaticamente.
        """
        super().__init__()
        self._sdk_key = sdk_key
        self._sdk_secret = sdk_secret
        self._subnet = subnet

    def run(self) -> None:
        try:
            from app.api.discovery import discover_gateways
            self.progress.emit("Scansione rete in corso...")
            gateways = discover_gateways(
                sdk_key=self._sdk_key,
                sdk_secret=self._sdk_secret,
                subnet=self._subnet,
            )
            self.finished.emit(gateways)
        except Exception as e:
            self.error.emit(f"Errore discovery: {e}")

