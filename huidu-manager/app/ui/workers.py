import os
# pyrefly: ignore [missing-import]
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

    def __init__(self, manager, device_id, cache_dict, screen_w, screen_h, action="avvia_carosello", target_uuid=None):
        super().__init__()
        self.manager = manager
        self.device_id = device_id
        self.cache_dict = cache_dict
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.action = action
        self.target_uuid = target_uuid

    def run(self):
        try:
            import os
            from app.core.presentation_model import (
                Presentation, Area, TextItem, ImageItem, VideoItem, DigitalClockItem, Effect, Font
            )
            from app.core.payload_generator import generate_payload
            from datetime import datetime
            
            def build_presentation(pres_data: dict, is_active: bool) -> Presentation | None:
                items_data = pres_data.get("items", [])
                pres_name = pres_data.get("name", "Playlist")
                
                built_items = []
                for i, item in enumerate(items_data):
                    itype = item.get("type", "").lower()
                    effect_cfg = item.get("effect", {})
                    # Requisito Tecnico Tassativo per image e text
                    if itype in ("image", "text"):
                        hold_val = effect_cfg.get("hold", 10000)
                    else:
                        hold_val = effect_cfg.get("hold", 5000)
                    effect = Effect(type=effect_cfg.get("type", 0), speed=effect_cfg.get("speed", 5), hold=hold_val)
                    
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
                            msg = f"File non trovato: {file_path}\nVerifica che il file esista ancora nel percorso indicato."
                            raise FileNotFoundError(msg)
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
                        # Legge la configurazione salvata in cache (non usa più solo i defaults)
                        tz = item.get("timezone", "+1:00")
                        # Supporta sia "multi_line" (chiave dialog) che "multiLine"
                        multi = item.get("multiLine", item.get("multi_line", True))

                        def _to_display(val) -> str:
                            """Converte bool/str in 'true'/'false' per Huidu."""
                            if isinstance(val, bool):
                                return "true" if val else "false"
                            return str(val).lower()

                        def _build_clock_sub(raw: dict, default_color: str) -> dict:
                            """Costruisce sub-oggetto date/time/week compatibile Huidu.
                            Il dialog salva 'visible', Huidu vuole 'display' (stringa).
                            """
                            visible = raw.get("visible", raw.get("display", True))
                            return {
                                "format": int(raw.get("format", 0)),
                                "color": raw.get("color", default_color),
                                "display": _to_display(visible),
                            }

                        date_cfg = _build_clock_sub(item.get("date", {}), "#ffffff")
                        time_cfg = _build_clock_sub(item.get("time", {}), "#00ff00")
                        week_cfg = _build_clock_sub(item.get("week", {}), "#ffff00")
                        # Di default week è nascosto se non esplicitamente configurato
                        if not item.get("week"):
                            week_cfg["display"] = "false"

                        built_items.append(DigitalClockItem(
                            timezone=tz,
                            multiLine=multi,
                            date=date_cfg,
                            time=time_cfg,
                            week=week_cfg,
                        ))

                if not built_items:
                    return None

                areas = []
                built_items.reverse()
                for item in built_items:
                    areas.append(Area(0, 0, self.screen_w, self.screen_h, item=[item]))

                pres = Presentation(name=pres_name, area=areas, uuid=pres_data.get("uuid"))
                # Fix: lo status ora si chiama "programmed" (non più "scheduled")
                status = pres_data.get("status", "live")
                if status == "programmed":
                    pres.play_control = pres_data.get("playControl")
                else:
                    pres.play_control = None
                return pres

            # Sincronizzazione Orologio (Pre-flight)
            self.progress.emit("Sincronizzazione orologio dispositivo...")
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                self.manager.device_api.set_device_property(self.device_id, time=time_str)
            except Exception as e:
                self.progress.emit(f"Errore sync orologio (ignorabile): {e}")

            self.progress.emit("Generazione del nuovo palinsesto...")
            payload_data = generate_payload(self.cache_dict, self.action, self.target_uuid)
                
            built_presentations = []
            for p_data in payload_data:
                if not p_data.get("items"):
                    continue
                pres = build_presentation(p_data, False)
                if pres:
                    built_presentations.append(pres)
            
            # Se la lista è vuota e l'azione lo prevede, inviamo un replace vuoto → schermo nero.
            # Blocchiamo solo le azioni che non hanno senso senza presentazioni.
            actions_require_content = ("manda_live", "disabilita")
            if not built_presentations and self.action in actions_require_content:
                self.error.emit("Nessuna presentazione valida da inviare.")
                return
            
            import json as _json
            self.progress.emit(f"Invio di {len(built_presentations)} programmi al dispositivo (REPLACE)...")
            for bp in built_presentations:
                d = bp.to_dict()
                pc = d.get("playControl")
                print(f"[DEBUG PAYLOAD] name={d.get('name')} | playControl={'PRESENTE' if pc else 'ASSENTE'}: {_json.dumps(pc, ensure_ascii=False)}")
            self.manager.programs_api.send_presentations(self.device_id, built_presentations, method="replace")
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


class ScheduleFetchWorker(QThread):
    finished = pyqtSignal(dict) # Restituisce task per il device
    error = pyqtSignal(str)

    def __init__(self, manager, device_id):
        super().__init__()
        self.manager = manager
        self.device_id = device_id

    def run(self):
        try:
            tasks = self.manager.device_api.get_scheduled_task(self.device_id)
            self.finished.emit(tasks)
        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Errore lettura task schermo: {msg}")


class ScheduleSyncWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, manager, device_id, screen_tasks, program_updates):
        super().__init__()
        self.manager = manager
        self.device_id = device_id
        self.screen_tasks = screen_tasks
        self.program_updates = program_updates

    def run(self):
        try:
            from datetime import datetime
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                self.manager.device_api.set_device_property(self.device_id, time=time_str)
            except Exception as e:
                print(f"Errore sync orologio: {e}")

            # 1. Aggiorna accensione/spegnimento schermo
            if self.screen_tasks is not None:
                self.manager.device_api.set_scheduled_task(self.device_id, {"screen": self.screen_tasks})
            
            # 2. Aggiorna palinsesto programmi (se ci sono update validi)
            if self.program_updates:
                self.manager.programs_api.update_programs_partial(self.device_id, self.program_updates)
                
            self.finished.emit()
        except Exception as e:
            msg = getattr(e, "message", str(e))
            self.error.emit(f"Errore sincronizzazione palinsesto: {msg}")


