from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QStatusBar, 
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QSettings
import uuid
import json
import os

# UI Imports
from app.ui.toolbar import Toolbar
from app.ui.sidebar import Sidebar
from app.ui.preview_area import PreviewArea
from app.ui.screen_settings import ScreenSettingsDialog
from app.ui.dialogs.image_dialog import ImageDialog
from app.ui.dialogs.video_dialog import VideoDialog
from app.ui.dialogs.text_dialog import TextDialog
from app.ui.dialogs.clock_dialog import ClockDialog
from app.ui.workers import (
    DeviceListWorker, ProgramFetchWorker, ProgramPushWorker,
    FileUploadWorker, PlaylistPushWorker, DiscoveryWorker,
)

class MainWindow(QMainWindow):
    def __init__(self, app_manager=None, parent=None):
        super().__init__(parent)
        self.manager = app_manager # Mock or real ScreenManager/AppManager
        
        self.setWindowTitle("SLPlayer - Huidu Manager")
        self.resize(1024, 768)
        
        self.active_screen_id = None
        self.active_presentation_uuid = None
        
        self.presentations_cache = {}
        # UUID che esistono fisicamente sul dispositivo (da ultimo get_programs)
        # Serve per distinguere presentazioni locali da quelle sul device al momento del delete
        self._device_uuids: dict[str, set[str]] = {}
        
        self.setup_ui()
        self.connect_signals()
        self.restore_settings()
        
        self._refresh_screens()
        
    def setup_ui(self):
        # Toolbar
        self.toolbar = Toolbar()
        self.addToolBar(self.toolbar)
        
        # Central Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.sidebar = Sidebar()
        self.preview_area = PreviewArea()
        
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.preview_area)
        self.splitter.setSizes([215, 809]) # 215px fissi for sidebar come da spec
        self.splitter.setCollapsible(0, False)
        
        layout.addWidget(self.splitter)
        
        # StatusBar
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Pronto")
        
    def connect_signals(self):
        # Sidebar to MainWindow / Toolbar / Preview
        self.sidebar.screen_selected.connect(self.on_screen_selected)
        self.sidebar.presentation_selected.connect(self.on_presentation_selected)
        self.sidebar.layer_selected.connect(self.on_layer_selected)
        self.sidebar.layers_reordered.connect(self.on_layers_reordered)
        
        self.sidebar.screens_refresh_requested.connect(self.on_screens_refresh_ui_triggered)
        self.sidebar.presentations_refresh_requested.connect(self.on_presentations_refresh_ui_triggered)
        self.sidebar.presentation_add_requested.connect(self.create_playlist)
        
        self.sidebar.layer_edit_requested.connect(self.on_layer_edit_requested)
        self.sidebar.layer_delete_requested.connect(self.on_layer_delete_requested)
        self.sidebar.presentation_edit_requested.connect(self.on_presentation_edit_requested)
        self.sidebar.presentation_duplicate_requested.connect(self.on_presentation_duplicate_requested)
        self.sidebar.presentation_delete_requested.connect(self.on_presentation_delete_requested)
        self.sidebar.presentation_activate_requested.connect(self.on_presentation_activate_requested)
        
        # Toolbar Actions
        self.toolbar.new_playlist_requested.connect(self.create_playlist)
        self.toolbar.new_item_requested.connect(self.open_item_dialog)
        self.toolbar.screen_settings_requested.connect(self.open_screen_settings)
        self.toolbar.push_playlist_requested.connect(self.on_push_playlist_requested)
        self.toolbar.discovery_requested.connect(self._run_discovery)

    # --- Slots Gestione Schermi ---
    def on_screens_refresh_ui_triggered(self):
        from PyQt6.QtCore import QTimer
        self.sidebar.screens_header.setText("SCHERMI ...")
        QTimer.singleShot(500, self._refresh_screens)
        
    def _refresh_screens(self) -> None:
        self.sidebar.screens_header.setText("SCHERMI (aggiorn...)")
        self.statusbar.showMessage("Aggiornamento schermi...")
        if not self.manager: return
        
        self.dev_worker = DeviceListWorker(self.manager)
        
        def on_screens(screens):
            self.sidebar.screens_header.setText("SCHERMI")
            self.statusbar.showMessage(f"Trovati {len(screens)} schermi", 3000)
            screen_data = [{"deviceId": s.id, "online": s.open_status} for s in screens]
            self.sidebar.set_screens(screen_data)
            
        def on_error(err):
            self.sidebar.screens_header.setText("SCHERMI")
            self.statusbar.showMessage(f"Errore schermi: {err}")
            QMessageBox.warning(self, "Errore Rete", str(err))

        self.dev_worker.finished.connect(on_screens)
        self.dev_worker.error.connect(on_error)
        self.dev_worker.start()

    # --- Discovery automatica dispositivi ---

    def _run_discovery(self) -> None:
        """Avvia la scansione della subnet locale cercando gateway Huidu."""
        import os
        sdk_key = os.environ.get("HUIDU_SDK_KEY", "")
        sdk_secret = os.environ.get("HUIDU_SDK_SECRET", "")
        if not sdk_key or not sdk_secret:
            QMessageBox.warning(
                self,
                "Credenziali mancanti",
                "SDK Key e SDK Secret non trovati nel file .env.\n"
                "Impossibile eseguire la scansione autenticata.",
            )
            return

        self.toolbar.btn_discover.setEnabled(False)
        self.toolbar.btn_discover.setText("⏳ Scansione in corso...")
        self.statusbar.showMessage("Scansione rete locale (porta 30080)...")

        self._disc_worker = DiscoveryWorker(sdk_key=sdk_key, sdk_secret=sdk_secret)

        def on_gateways(gateways):
            self.toolbar.btn_discover.setEnabled(True)
            self.toolbar.btn_discover.setText("🔍 Cerca dispositivi")
            if not gateways:
                self.statusbar.showMessage("Nessun gateway Huidu trovato sulla rete", 5000)
                QMessageBox.information(
                    self,
                    "Discovery completata",
                    "Nessun controller Huidu trovato sulla subnet locale.\n"
                    "Verificare che i dispositivi siano accesi e connessi alla rete.",
                )
                return
            self._apply_discovered_gateways(gateways)

        def on_error(msg):
            self.toolbar.btn_discover.setEnabled(True)
            self.toolbar.btn_discover.setText("🔍 Cerca dispositivi")
            self.statusbar.showMessage(f"Errore discovery: {msg}", 5000)
            QMessageBox.warning(self, "Errore Discovery", msg)

        def on_progress(msg):
            self.statusbar.showMessage(msg)

        self._disc_worker.finished.connect(on_gateways)
        self._disc_worker.error.connect(on_error)
        self._disc_worker.progress.connect(on_progress)
        self._disc_worker.start()

    def _apply_discovered_gateways(self, gateways) -> None:
        """Aggiorna AppManager con il primo gateway trovato e ricarica la lista schermi.

        Se vengono trovati più gateway, mostra un dialogo di selezione.
        """
        from app.api.huidu_client import HuiduClient
        from app.api.device_api import DeviceApi
        from app.api.program_api import ProgramApi
        from app.api.file_api import FileApi
        from app.core.file_uploader import FileUploader
        from app.core.screen_manager import ScreenManager
        import os

        if len(gateways) == 1:
            chosen = gateways[0]
        else:
            # Più gateway: chiedi all'utente quale usare
            items = [
                f"{gw.host}:{gw.port}  ({len(gw.device_ids)} controller)"
                for gw in gateways
            ]
            from PyQt6.QtWidgets import QInputDialog
            choice, ok = QInputDialog.getItem(
                self,
                "Gateway trovati",
                f"Trovati {len(gateways)} gateway Huidu. Seleziona a quale connettersi:",
                items,
                editable=False,
            )
            if not ok:
                return
            chosen = gateways[items.index(choice)]

        sdk_key = os.environ.get("HUIDU_SDK_KEY", "")
        sdk_secret = os.environ.get("HUIDU_SDK_SECRET", "")

        new_client = HuiduClient(
            host=chosen.host,
            port=chosen.port,
            sdk_key=sdk_key,
            sdk_secret=sdk_secret,
        )
        self.manager.gateway = new_client
        self.manager.device_api = DeviceApi(new_client)
        self.manager.programs_api = ProgramApi(new_client)
        self.manager.file_api = FileApi(new_client)
        self.manager.uploader = FileUploader(self.manager.file_api)
        self.manager.screens = ScreenManager(self.manager.device_api)

        n_controllers = len(chosen.device_ids)
        self.statusbar.showMessage(
            f"Connesso a {chosen.host}:{chosen.port} — {n_controllers} controller trovati",
            5000,
        )
        # Ricarica la lista schermi con il nuovo gateway
        self._refresh_screens()
        
    def on_screen_selected(self, device_id):
        if not device_id:
            self.active_screen_id = None
            self.active_presentation_uuid = None
            self.toolbar.on_screen_selected(False)
            self.toolbar.on_presentation_selected(False)
            self.preview_area.clear_screen_info()
            self.statusbar.showMessage("Nessuno schermo selezionato")
            return
            
        self.active_screen_id = device_id
        self.toolbar.on_screen_selected(True)
        # Default placeholder during loading
        self.preview_area.update_screen_info(128, 64, True)
        self.statusbar.showMessage(f"Schermo selezionato: {device_id} | Interrogazione dimensioni in corso...")
        
        from PyQt6.QtCore import QThread, pyqtSignal
        class PropWorker(QThread):
            done = pyqtSignal(dict)
            error = pyqtSignal(str)
            def __init__(self, mgr, d_id):
                super().__init__()
                self.mgr = mgr
                self.d_id = d_id
            def run(self):
                try:
                    props = self.mgr.device_api.get_device_property(self.d_id)
                    self.done.emit(props)
                except Exception as e:
                    self.error.emit(str(e))
        
        self._screen_prop_worker = PropWorker(self.manager, device_id)
        
        def on_props_done(props):
            w = int(props.get('screen.width', 128))
            h = int(props.get('screen.height', 64))
            self.preview_area.update_screen_info(w, h, True)
            self.statusbar.showMessage(f"Schermo selezionato: {device_id} | {w}x{h}")
            if not hasattr(self, 'screen_dimensions'): self.screen_dimensions = {}
            self.screen_dimensions[device_id] = (w, h)
            self._refresh_presentations(self.active_screen_id)
            
        def on_props_err(err):
            self.statusbar.showMessage(f"Schermo selezionato: {device_id} | Errore lettura dimensioni")
            self._refresh_presentations(self.active_screen_id)

        self._screen_prop_worker.done.connect(on_props_done)
        self._screen_prop_worker.error.connect(on_props_err)
        self._screen_prop_worker.start()
        
    def open_screen_settings(self):
        if not self.active_screen_id: return
        from PyQt6.QtWidgets import QProgressDialog
        
        loading_dlg = QProgressDialog("Lettura proprietà dal dispositivo...", None, 0, 0, self)
        loading_dlg.setWindowTitle("Attendere")
        loading_dlg.setModal(True)
        loading_dlg.show()
        
        from PyQt6.QtCore import QThread, pyqtSignal
        class FetchPropsWorker(QThread):
            done = pyqtSignal(dict)
            error = pyqtSignal(str)
            def __init__(self, mgr, d_id):
                super().__init__()
                self.mgr = mgr
                self.d_id = d_id
            def run(self):
                try:
                    # Inizializzato in runtime/Fase 1
                    props = self.mgr.device_api.get_device_property(self.d_id)
                    self.done.emit(props)
                except Exception as e:
                    self.error.emit(str(e))
                    
        self.props_worker = FetchPropsWorker(self.manager, self.active_screen_id)
        
        def on_done(props):
            loading_dlg.accept()
            from app.ui.screen_settings import ScreenSettingsDialog
            dlg = ScreenSettingsDialog(self.active_screen_id, props, self.manager, self)
            dlg.exec()
            
        def on_err(err):
            loading_dlg.accept()
            QMessageBox.warning(self, "Errore", f"Impossibile leggere le proprietà:\n{err}\nControllare la connessione al controller.")
            
        self.props_worker.done.connect(on_done)
        self.props_worker.error.connect(on_err)
        self.props_worker.start()

    def on_push_playlist_requested(self):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        pres_data = self.presentations_cache[self.active_screen_id].get(self.active_presentation_uuid)
        if not pres_data: return
        
        from PyQt6.QtWidgets import QProgressDialog
        self.push_dialog = QProgressDialog("Avvio caricamento...", "Annulla", 0, 100, self)
        self.push_dialog.setWindowTitle("Invia a Schermo")
        self.push_dialog.setModal(True)
        self.push_dialog.show()
        
        sw, sh = self._get_screen_dimensions()
        pres_uuid = self.active_presentation_uuid
        
        all_pres_data = list(self.presentations_cache[self.active_screen_id].values())

        # "Invia a Schermo" usa replace con tutto il payload locale
        self.push_worker = PlaylistPushWorker(
            self.manager, self.active_screen_id, all_pres_data, sw, sh, method="replace", active_uuid=pres_uuid
        )
        
        def on_prog(msg):
            self.push_dialog.setLabelText(msg)
            self.push_dialog.setValue((self.push_dialog.value() + 10) % 100)
            
        def on_done():
            self.push_dialog.setValue(100)
            # Aggiorna il tracking con tutte le presentazioni appena inviate
            if self.active_screen_id not in self._device_uuids:
                self._device_uuids[self.active_screen_id] = set()
            for p in all_pres_data:
                if p.get("items"):
                    self._device_uuids[self.active_screen_id].add(p["uuid"])
            
            QMessageBox.information(
                self, "In onda!",
                f"La presentazione '{pres_data.get('name', '')}' è ora attiva sul controller."
            )
            
        def on_err(msg):
            self.push_dialog.cancel()
            QMessageBox.critical(self, "Errore", f"Impossibile inviare la playlist:\n{msg}")
            
        self.push_worker.progress.connect(on_prog)
        self.push_worker.finished.connect(on_done)
        self.push_worker.error.connect(on_err)
        self.push_worker.start()
        
    # --- Slots Gestione Presentazioni e Livelli ---
    def on_presentations_refresh_ui_triggered(self):
        if not self.active_screen_id: return
        self._refresh_presentations(self.active_screen_id)
        
    def _refresh_presentations(self, screen_id: str) -> None:
        if not screen_id or not self.manager: return
        self.statusbar.showMessage("Lettura programmi...")
        
        self.prog_worker = ProgramFetchWorker(self.manager, screen_id)
        
        def on_programs(programs, s_id):
            # MERGE: i programmi del device vengono aggiunti/aggiornati nella cache locale
            # senza mai rimuovere le presentazioni create localmente.
            # La cache locale è la fonte di verità per la sidebar.
            cache = self.presentations_cache.setdefault(s_id, {})
            device_uuids: set[str] = set()
            for p in programs:
                uid = p.get("uuid")
                name = p.get("name")
                existing = cache.get(uid, {"items": []})
                cache[uid] = {"uuid": uid, "name": name, "items": existing.get("items", [])}
                device_uuids.add(uid)
            self._device_uuids[s_id] = device_uuids
            n_local = len(cache) - len(device_uuids)
            msg = f"Trovati {len(device_uuids)} programmi sul device"
            if n_local > 0:
                msg += f" + {n_local} locali"
            self.statusbar.showMessage(msg, 3000)
            self._save_cache()  # Salva il merge su file
            self.sidebar.set_presentations(list(cache.values()))

        def on_error(err):
            self.statusbar.showMessage(f"Errore lettura programmi")
            QMessageBox.warning(self, "Errore Rete", err)

        self.prog_worker.finished.connect(on_programs)
        self.prog_worker.error.connect(on_error)
        self.prog_worker.start()
        
    def create_playlist(self):
        if not self.active_screen_id: return
        name, ok = QInputDialog.getText(self, "Nuova Playlist", "Nome:")
        if ok and name:
            new_uuid = str(uuid.uuid4())
            screen_pres = self.presentations_cache.setdefault(self.active_screen_id, {})
            screen_pres[new_uuid] = {"uuid": new_uuid, "name": name, "items": []}
            self._save_cache()
            self.sidebar.set_presentations(list(screen_pres.values()))
            
    def on_presentation_selected(self, pres_uuid):
        if not pres_uuid or not self.active_screen_id:
            self.active_presentation_uuid = None
            self.toolbar.on_presentation_selected(False)
            self.sidebar.hide_layers()
            self.preview_area.update_layers([], -1)
            return

        self.active_presentation_uuid = pres_uuid
        self.toolbar.on_presentation_selected(True)
        
        screen_pres = self.presentations_cache.setdefault(self.active_screen_id, {})
        pres = screen_pres.get(pres_uuid)
        items = pres.get("items", []) if pres else []
        self.sidebar.set_layers(items)
        self.preview_area.update_layers(items, -1)
        
    def on_layer_selected(self, idx):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        pres = self.presentations_cache[self.active_screen_id].get(self.active_presentation_uuid)
        if not pres: return
        self.preview_area.update_layers(
            pres.get("items", []),
            selected_idx=idx
        )
        
    def on_layers_reordered(self, new_indices):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        pres = self.presentations_cache[self.active_screen_id].get(self.active_presentation_uuid)
        if not pres: return
        old_items = pres["items"]
        new_items = [old_items[i] for i in new_indices]
        pres["items"] = new_items
        self.sidebar.set_layers(new_items)
        self.preview_area.update_layers(new_items, -1)
        self.statusbar.showMessage("Ordine livelli aggiornato", 2000)
        
    def open_item_dialog(self, item_type):
        if not self.active_presentation_uuid: return
        
        dialogs = {
            "image": ImageDialog,
            "video": VideoDialog,
            "text": TextDialog,
            "clock": ClockDialog
        }
        dlg_class = dialogs.get(item_type)
        if not dlg_class: return
        
        dlg = dlg_class(self)
        dlg.item_created.connect(self.add_layer_to_presentation)
        dlg.exec()
        
    def add_layer_to_presentation(self, item_data):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        pres = self.presentations_cache[self.active_screen_id].get(self.active_presentation_uuid)
        if not pres: return
        pres["items"].append(item_data)
        self._save_cache()
        self.on_presentation_selected(self.active_presentation_uuid) # Refresh visual
        self.statusbar.showMessage("Nuovo livello aggiunto", 3000)

    def on_presentation_edit_requested(self, uuid_id):
        if not self.active_screen_id: return
        pres = self.presentations_cache[self.active_screen_id].get(uuid_id)
        if not pres: return
        new_name, ok = QInputDialog.getText(self, "Rinomina", "Nuovo nome:", text=pres["name"])
        if ok and new_name:
            pres["name"] = new_name
            self.sidebar.set_presentations(list(self.presentations_cache[self.active_screen_id].values()))
            
            self.statusbar.showMessage("Rinomina in corso...")
            from app.ui.workers import ProgramRenameWorker
            self._ren_worker = ProgramRenameWorker(self.manager, self.active_screen_id, uuid_id, new_name)
            self._ren_worker.finished.connect(lambda: self.statusbar.showMessage("Presentazione rinominata", 3000))
            self._ren_worker.error.connect(lambda e: QMessageBox.warning(self, "Errore", e))
            self._ren_worker.start()

    def on_presentation_duplicate_requested(self, uuid_id):
        if not self.active_screen_id: return
        pres = self.presentations_cache[self.active_screen_id].get(uuid_id)
        if not pres: return
        import copy
        new_pres = copy.deepcopy(pres)
        new_pres["uuid"] = str(uuid.uuid4())
        new_pres["name"] = new_pres["name"] + " (Copia)"
        self.presentations_cache[self.active_screen_id][new_pres["uuid"]] = new_pres
        self.sidebar.set_presentations(list(self.presentations_cache[self.active_screen_id].values()))

    def on_presentation_delete_requested(self, uuid_id):
        if not self.active_screen_id: return
        pres = self.presentations_cache[self.active_screen_id].get(uuid_id)
        if not pres: return
        ret = QMessageBox.question(self, "Conferma", f"Vuoi davvero eliminare la presentazione '{pres['name']}'?")
        if ret == QMessageBox.StandardButton.Yes:
            del self.presentations_cache[self.active_screen_id][uuid_id]
            if self.active_presentation_uuid == uuid_id:
                self.on_presentation_selected("")
            self.sidebar.set_presentations(list(self.presentations_cache[self.active_screen_id].values()))

            # Chiama l'API di rimozione SOLO se la presentazione esiste sul device.
            # Le presentazioni create localmente ma mai inviate non hanno un UUID sul controller.
            is_on_device = uuid_id in self._device_uuids.get(self.active_screen_id, set())
            if is_on_device:
                self.statusbar.showMessage("Cancellazione dal dispositivo...")
                from app.ui.workers import ProgramRemoveWorker
                self._rem_worker = ProgramRemoveWorker(self.manager, self.active_screen_id, [uuid_id])
                self._rem_worker.finished.connect(lambda: self._on_delete_done(self.active_screen_id, uuid_id))
                self._rem_worker.error.connect(lambda e: QMessageBox.warning(self, "Errore Elimina", e))
                self._rem_worker.start()
            else:
                self.statusbar.showMessage("Presentazione locale eliminata", 3000)

    def _on_delete_done(self, screen_id: str, uuid_id: str) -> None:
        """Callback post-delete: rimuove UUID dal tracking device e aggiorna status."""
        self._device_uuids.get(screen_id, set()).discard(uuid_id)
        self.statusbar.showMessage("Presentazione eliminata dal dispositivo", 3000)

    def on_presentation_activate_requested(self, uuid_id: str) -> None:
        """Invia la presentazione selezionata come unica attiva sul device (method=replace).

        Usa ``replace`` quindi TUTTE le presentazioni esistenti sul controller vengono
        sostituite da questa sola. Le altre rimangono salvate localmente nell'app.
        """
        if not self.active_screen_id: return
        pres_data = self.presentations_cache.get(self.active_screen_id, {}).get(uuid_id)
        if not pres_data: return

        if not pres_data.get("items"):
            QMessageBox.warning(
                self,
                "Presentazione vuota",
                "Aggiungi almeno un livello prima di mandare in onda la presentazione.",
            )
            return

        from PyQt6.QtWidgets import QProgressDialog
        self._activate_dialog = QProgressDialog("Avvio invio...", "Annulla", 0, 100, self)
        self._activate_dialog.setWindowTitle("Manda in onda")
        self._activate_dialog.setModal(True)
        self._activate_dialog.show()

        sw, sh = self._get_screen_dimensions()
        all_pres_data = list(self.presentations_cache[self.active_screen_id].values())

        # method="replace" → invia tutte, ma attiva solo questa
        self._activate_worker = PlaylistPushWorker(
            self.manager, self.active_screen_id, all_pres_data, sw, sh, method="replace", active_uuid=uuid_id
        )

        def on_prog(msg):
            self._activate_dialog.setLabelText(msg)
            self._activate_dialog.setValue((self._activate_dialog.value() + 10) % 100)

        def on_done():
            self._activate_dialog.setValue(100)
            # Aggiorna il tracking
            if self.active_screen_id not in self._device_uuids:
                self._device_uuids[self.active_screen_id] = set()
            for p in all_pres_data:
                if p.get("items"):
                    self._device_uuids[self.active_screen_id].add(p["uuid"])
                    
            self.statusbar.showMessage(f"'​{pres_data['name']}' ora in onda", 5000)
            QMessageBox.information(
                self, "In onda!",
                f"La presentazione '​{pres_data['name']}' è ora l'unica attiva sul controller."
            )

        def on_err(msg):
            self._activate_dialog.cancel()
            QMessageBox.critical(self, "Errore", f"Impossibile mandare in onda:\n{msg}")

        self._activate_worker.progress.connect(on_prog)
        self._activate_worker.finished.connect(on_done)
        self._activate_worker.error.connect(on_err)
        self._activate_worker.start()

    def _get_screen_dimensions(self) -> tuple[int, int]:
        """Restituisce le dimensioni (w, h) dello schermo attivo dalla cache."""
        if hasattr(self, "screen_dimensions") and self.active_screen_id:
            return self.screen_dimensions.get(self.active_screen_id, (128, 64))
        return (128, 64)

    def on_layer_edit_requested(self, idx):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        pres = self.presentations_cache[self.active_screen_id].get(self.active_presentation_uuid)
        if not pres: return
        items = pres.get("items", [])
        if idx < 0 or idx >= len(items): return
        
        item_data = items[idx]
        item_type = item_data.get("type", "").lower()
        if item_type in ("digitalclock", "dialclock"):
            item_type = "clock"
            
        dialogs = {
            "image": ImageDialog,
            "video": VideoDialog,
            "text": TextDialog,
            "clock": ClockDialog
        }
        dlg_class = dialogs.get(item_type)
        if not dlg_class: return
        
        dlg = dlg_class(self)
        
        def on_item_edited(new_data):
            items[idx] = new_data
            self._save_cache()  # Salva modifica livello
            self.on_presentation_selected(self.active_presentation_uuid)
            self.statusbar.showMessage(f"Livello {idx} modificato", 3000)
            
        dlg.item_created.connect(on_item_edited)
        dlg.exec()

    def on_layer_delete_requested(self, idx):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        pres = self.presentations_cache[self.active_screen_id].get(self.active_presentation_uuid)
        if not pres: return
        items = pres.get("items", [])
        if idx < 0 or idx >= len(items): return
        
        ret = QMessageBox.question(self, "Conferma", "Vuoi eliminare il livello selezionato?")
        if ret == QMessageBox.StandardButton.Yes:
            del items[idx]
            self._save_cache()  # Salva eliminazione livello
            self.on_presentation_selected(self.active_presentation_uuid)

    # --- Window State ---
    def closeEvent(self, event):
        settings = QSettings("StarLed", "SLPlayer")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        # Salva la cache delle presentazioni su file
        self._save_cache()
        super().closeEvent(event)
        
    def restore_settings(self):
        settings = QSettings("StarLed", "SLPlayer")
        if settings.value("geometry"): self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"): self.restoreState(settings.value("windowState"))
        
        # Ripristina la cache delle presentazioni da file JSON locale
        if os.path.exists("presentations_cache.json"):
            try:
                with open("presentations_cache.json", "r", encoding="utf-8") as f:
                    self.presentations_cache = json.load(f)
            except Exception as e:
                print(f"Errore caricamento file cache presentazioni: {e}")
                self.presentations_cache = {}
        else:
            self.presentations_cache = {}

    def _save_cache(self):
        """Salva la cache su file JSON per persistenza immediata vera."""
        try:
            with open("presentations_cache.json", "w", encoding="utf-8") as f:
                json.dump(self.presentations_cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio file cache presentazioni: {e}")
