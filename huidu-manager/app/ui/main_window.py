from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QStatusBar, 
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QSettings
import uuid

# UI Imports
from app.ui.toolbar import Toolbar
from app.ui.sidebar import Sidebar
from app.ui.preview_area import PreviewArea
from app.ui.screen_settings import ScreenSettingsDialog
from app.ui.dialogs.image_dialog import ImageDialog
from app.ui.dialogs.video_dialog import VideoDialog
from app.ui.dialogs.text_dialog import TextDialog
from app.ui.dialogs.clock_dialog import ClockDialog
from app.ui.workers import DeviceListWorker, ProgramFetchWorker, ProgramPushWorker, FileUploadWorker

class MainWindow(QMainWindow):
    def __init__(self, app_manager=None, parent=None):
        super().__init__(parent)
        self.manager = app_manager # Mock or real ScreenManager/AppManager
        
        self.setWindowTitle("SLPlayer - Huidu Manager")
        self.resize(1024, 768)
        
        self.active_screen_id = None
        self.active_presentation_uuid = None
        
        self.presentations_cache = {}
        
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
        
        # Toolbar Actions
        self.toolbar.new_playlist_requested.connect(self.create_playlist)
        self.toolbar.new_item_requested.connect(self.open_item_dialog)
        self.toolbar.screen_settings_requested.connect(self.open_screen_settings)

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
        # Assuming Screen has dimensions 128x64
        self.preview_area.update_screen_info(128, 64, True)
        self.statusbar.showMessage(f"Schermo selezionato: {device_id} | 128x64")
        self._refresh_presentations(self.active_screen_id)
        
    def open_screen_settings(self):
        if not self.active_screen_id: return
        # In actual code, fetch real properties
        mock_props = {"width": 128, "height": 64, "luminance": 50, "volume": 30, "firmwareVersion": "1.0.0"}
        from app.ui.screen_settings import ScreenSettingsDialog
        dlg = ScreenSettingsDialog(self.active_screen_id, mock_props, self.manager, self)
        dlg.exec()
        
    # --- Slots Gestione Presentazioni e Livelli ---
    def on_presentations_refresh_ui_triggered(self):
        if not self.active_screen_id: return
        self._refresh_presentations(self.active_screen_id)
        
    def _refresh_presentations(self, screen_id: str) -> None:
        if not screen_id or not self.manager: return
        self.statusbar.showMessage("Lettura programmi...")
        
        self.prog_worker = ProgramFetchWorker(self.manager, screen_id)
        
        def on_programs(programs, s_id):
            self.statusbar.showMessage(f"Trovati {len(programs)} programmi", 3000)
            cache = self.presentations_cache.setdefault(s_id, {})
            new_cache = {}
            for p in programs:
                uid = p.get("uuid")
                name = p.get("name")
                existing = cache.get(uid, {"items": []})
                new_cache[uid] = {"uuid": uid, "name": name, "items": existing.get("items", [])}
            self.presentations_cache[s_id] = new_cache
            self.sidebar.set_presentations(list(new_cache.values()))

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
            screen_pres = self.mock_presentations.setdefault(self.active_screen_id, {})
            screen_pres[new_uuid] = {"uuid": new_uuid, "name": name, "items": []}
            self._refresh_presentations(self.active_screen_id)
            
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
        self.preview_area.update_layers(
            self.presentations_cache[self.active_screen_id][self.active_presentation_uuid]["items"],
            selected_idx=idx
        )
        
    def on_layers_reordered(self, new_indices):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        pres = self.presentations_cache[self.active_screen_id][self.active_presentation_uuid]
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
        self.presentations_cache[self.active_screen_id][self.active_presentation_uuid]["items"].append(item_data)
        self.on_presentation_selected(self.active_presentation_uuid) # Refresh visual
        self.statusbar.showMessage("Nuovo livello aggiunto", 3000)

    def on_presentation_edit_requested(self, uuid_id):
        if not self.active_screen_id: return
        pres = self.presentations_cache[self.active_screen_id].get(uuid_id)
        if not pres: return
        new_name, ok = QInputDialog.getText(self, "Rinomina", "Nuovo nome:", text=pres["name"])
        if ok and new_name:
            pres["name"] = new_name
            self._refresh_presentations(self.active_screen_id)

    def on_presentation_duplicate_requested(self, uuid_id):
        if not self.active_screen_id: return
        pres = self.presentations_cache[self.active_screen_id].get(uuid_id)
        if not pres: return
        import copy
        new_pres = copy.deepcopy(pres)
        new_pres["uuid"] = str(uuid.uuid4())
        new_pres["name"] = new_pres["name"] + " (Copia)"
        self.presentations_cache[self.active_screen_id][new_pres["uuid"]] = new_pres
        self._refresh_presentations(self.active_screen_id)

    def on_presentation_delete_requested(self, uuid_id):
        if not self.active_screen_id: return
        pres = self.presentations_cache[self.active_screen_id].get(uuid_id)
        if not pres: return
        ret = QMessageBox.question(self, "Conferma", f"Vuoi davvero eliminare la presentazione '{pres['name']}'?")
        if ret == QMessageBox.StandardButton.Yes:
            del self.presentations_cache[self.active_screen_id][uuid_id]
            if self.active_presentation_uuid == uuid_id:
                self.on_presentation_selected("")
            self._refresh_presentations(self.active_screen_id)

    def on_layer_edit_requested(self, idx):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        items = self.presentations_cache[self.active_screen_id][self.active_presentation_uuid]["items"]
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
            self.on_presentation_selected(self.active_presentation_uuid)
            self.statusbar.showMessage(f"Livello {idx} modificato", 3000)
            
        dlg.item_created.connect(on_item_edited)
        dlg.exec()

    def on_layer_delete_requested(self, idx):
        if not self.active_screen_id or not self.active_presentation_uuid: return
        items = self.presentations_cache[self.active_screen_id][self.active_presentation_uuid]["items"]
        if idx < 0 or idx >= len(items): return
        
        ret = QMessageBox.question(self, "Conferma", "Vuoi eliminare il livello selezionato?")
        if ret == QMessageBox.StandardButton.Yes:
            del items[idx]
            self.on_presentation_selected(self.active_presentation_uuid)

    # --- Window State ---
    def closeEvent(self, event):
        settings = QSettings("StarLed", "SLPlayer")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)
        
    def restore_settings(self):
        settings = QSettings("StarLed", "SLPlayer")
        if settings.value("geometry"): self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"): self.restoreState(settings.value("windowState"))
