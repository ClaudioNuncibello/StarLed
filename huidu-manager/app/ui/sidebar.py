from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMenu, QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LayerListWidget(QListWidget):
    layers_reordered = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        
    def dropEvent(self, event):
        super().dropEvent(event)
        # Quando un drop avviene, calcoliamo i nuovi indici
        new_order = [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]
        self.layers_reordered.emit(new_order)
        # Ritoccare la UI per aggiornare i numeretti d'ordine
        self.update_layer_numbers()
        
    def update_layer_numbers(self):
        for i in range(self.count()):
            item = self.item(i)
            # Estrarre il tipo
            text = item.text()
            parts = text.split("]", 1)
            if len(parts) == 2:
                # ⠿ [IMG] banner.png — 0
                base_text = parts[1].rsplit("—", 1)[0].strip()
                item.setText(f"⠿ {parts[0]}] {base_text} — {i}")
            # we also reassign the new data ID to match its current visual index if necessary 
            # Or the backend does it based on the signal array. We let backend handle the array list update.

class Sidebar(QWidget):
    screen_selected = pyqtSignal(str)
    presentation_selected = pyqtSignal(str)
    layer_selected = pyqtSignal(int)
    layers_reordered = pyqtSignal(list)
    
    screens_refresh_requested = pyqtSignal()
    presentations_refresh_requested = pyqtSignal()
    presentation_add_requested = pyqtSignal()
    
    layer_edit_requested = pyqtSignal(int)
    layer_delete_requested = pyqtSignal(int)
    presentation_edit_requested = pyqtSignal(str)
    presentation_duplicate_requested = pyqtSignal(str)
    presentation_delete_requested = pyqtSignal(str)
    presentation_activate_requested = pyqtSignal(str)  # "Manda in onda" — replace sul device

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(215)
        self.setObjectName("Sidebar")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Sezione Schermi ---
        screens_header_layout = QHBoxLayout()
        screens_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.screens_header = QLabel("SCHERMI")
        self.screens_header.setObjectName("SectionHeader")
        self.screens_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        self.btn_refresh_screens = QPushButton()
        self.btn_refresh_screens.setIcon(QIcon(os.path.join(BASE_DIR, "assets", "icon", "refresh.png")))
        self.btn_refresh_screens.setIconSize(QSize(16, 16))
        self.btn_refresh_screens.setFixedSize(24, 24)
        self.btn_refresh_screens.clicked.connect(self.screens_refresh_requested.emit)
        
        screens_header_layout.addWidget(self.screens_header)
        screens_header_layout.addStretch()
        screens_header_layout.addWidget(self.btn_refresh_screens)
        
        w_screens_header = QWidget()
        w_screens_header.setLayout(screens_header_layout)
        w_screens_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(w_screens_header, 0)
        
        self.screens_list = QListWidget()
        self.screens_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.screens_list.itemClicked.connect(self.on_screen_clicked)
        layout.addWidget(self.screens_list, 0)
        
        # --- Sezione Presentazioni ---
        self.pres_section = QWidget()
        pres_section_layout = QVBoxLayout(self.pres_section)
        pres_section_layout.setContentsMargins(0, 0, 0, 0)
        pres_section_layout.setSpacing(0)

        pres_header_layout = QHBoxLayout()
        pres_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pres_header = QLabel("PRESENTAZIONI")
        self.pres_header.setObjectName("SectionHeader")
        self.pres_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        self.btn_add_pres = QPushButton()
        self.btn_add_pres.setIcon(QIcon(os.path.join(BASE_DIR, "assets", "icon", "plus.png")))
        self.btn_add_pres.setIconSize(QSize(16, 16))
        self.btn_add_pres.setFixedSize(24, 24)
        self.btn_add_pres.clicked.connect(self.presentation_add_requested.emit)
        
        self.btn_refresh_pres = QPushButton()
        self.btn_refresh_pres.setIcon(QIcon(os.path.join(BASE_DIR, "assets", "icon", "refresh.png")))
        self.btn_refresh_pres.setIconSize(QSize(16, 16))
        self.btn_refresh_pres.setFixedSize(24, 24)
        self.btn_refresh_pres.clicked.connect(self.presentations_refresh_requested.emit)
        
        pres_header_layout.addWidget(self.pres_header)
        pres_header_layout.addStretch()
        pres_header_layout.addWidget(self.btn_add_pres)
        pres_header_layout.addWidget(self.btn_refresh_pres)
        
        w_pres_header = QWidget()
        w_pres_header.setLayout(pres_header_layout)
        w_pres_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        pres_section_layout.addWidget(w_pres_header, 0)
        
        self.pres_list = QListWidget()
        self.pres_list.setFixedHeight(120)
        self.pres_list.itemClicked.connect(self.on_screen_presentation_clicked)
        self.pres_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pres_list.customContextMenuRequested.connect(self.show_pres_context_menu)
        pres_section_layout.addWidget(self.pres_list, 0)

        layout.addWidget(self.pres_section, 0)
        self.pres_section.setVisible(False)
        
        # --- Sezione Livelli ---
        layer_header_layout = QHBoxLayout()
        layer_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.layer_header = QLabel("LIVELLI")
        self.layer_header.setObjectName("SectionHeader")
        self.layer_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        self.layer_hint = QLabel("(drag per riord.)")
        self.layer_hint.setStyleSheet("color: #555555; font-size: 9pt;")
        
        layer_header_layout.addWidget(self.layer_header)
        layer_header_layout.addStretch()
        layer_header_layout.addWidget(self.layer_hint)
        
        w_layer_header = QWidget()
        w_layer_header.setLayout(layer_header_layout)
        w_layer_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        self.layer_section = QWidget()
        layer_section_layout = QVBoxLayout(self.layer_section)
        layer_section_layout.setContentsMargins(0, 0, 0, 0)
        layer_section_layout.setSpacing(0)
        layer_section_layout.addWidget(w_layer_header, 0)
        
        self.layer_list = LayerListWidget()
        # Settiamo un'altezza approssimativa anche per il Layer se impostato a stretch=0
        self.layer_list.setFixedHeight(180)
        self.layer_list.layers_reordered.connect(self.layers_reordered.emit)
        self.layer_list.itemClicked.connect(self.on_layer_clicked)
        self.layer_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self.show_layer_context_menu)
        
        layer_section_layout.addWidget(self.layer_list, 0)
        
        layout.addWidget(self.layer_section, 0)
        self.layer_section.setVisible(False) # Visibile solo se presentazione attiva
        
        layout.addStretch(1)
        
    def set_screens(self, screens):
        self.screens_list.clear()
        for scr in screens:
            icon = "●" if scr.get("online") else "○"
            item = QListWidgetItem(f"{icon} {scr.get('deviceId')}")
            item.setData(Qt.ItemDataRole.UserRole, scr.get("deviceId"))
            self.screens_list.addItem(item)
            
    def set_presentations(self, presentations):
        self.pres_list.clear()
        for pres in presentations:
            item = QListWidgetItem(f"> {pres.get('name')}")
            item.setData(Qt.ItemDataRole.UserRole, pres.get("uuid"))
            self.pres_list.addItem(item)
            
    def set_layers(self, layers):
        self.layer_list.clear()
        self.layer_section.setVisible(True)
        for i, lyr in enumerate(layers):
            typ = lyr.get("type", "").upper()
            if typ.startswith("DIGITAL") or typ.startswith("DIAL"):
                typ = "CLK"
            elif typ == "IMAGE": typ = "IMG"
            elif typ == "VIDEO": typ = "VID"
            elif typ == "TEXT": typ = "TXT"
            
            # Formattazione semplice handle ⠿
            desc = lyr.get("file", lyr.get("string", "Orologio")).split("/")[-1][:12]
            # HTML for Badge doesn't work in QListWidget default Delegate, so we use string
            # In a real app we'd use QStyledItemDelegate
            text_str = f"⠿ [{typ}] {desc} — {i}"
            item = QListWidgetItem(text_str)
            item.setData(Qt.ItemDataRole.UserRole, i) # Store original index
            self.layer_list.addItem(item)
            
    def hide_layers(self):
        self.layer_list.clear()
        self.layer_section.setVisible(False)

    def on_screen_clicked(self, item):
        device_id = item.data(Qt.ItemDataRole.UserRole)
        if hasattr(self, '_active_screen') and self._active_screen == device_id:
            self.screens_list.clearSelection()
            self._active_screen = None
            self.pres_section.setVisible(False)
            self.layer_section.setVisible(False)
            self.screen_selected.emit("")
        else:
            self._active_screen = device_id
            self.pres_section.setVisible(True)
            self.screen_selected.emit(device_id)

    def on_screen_presentation_clicked(self, item):
        uuid = item.data(Qt.ItemDataRole.UserRole)
        if hasattr(self, '_active_pres') and self._active_pres == uuid:
            self.pres_list.clearSelection()
            self._active_pres = None
            self.layer_section.setVisible(False)
            self.presentation_selected.emit("")
        else:
            self._active_pres = uuid
            self.layer_section.setVisible(True)
            self.presentation_selected.emit(uuid)
        
    def on_layer_clicked(self, item):
        # We find its visual index to emit since the underlying list might be mutating
        visual_index = self.layer_list.row(item)
        self.layer_selected.emit(visual_index)

    def show_pres_context_menu(self, pos):
        item = self.pres_list.itemAt(pos)
        if item is None:
            return
            
        uuid = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        activate_act = menu.addAction("▶ Manda in onda")
        activate_act.setToolTip("Invia questa presentazione al dispositivo come unica attiva")
        menu.addSeparator()
        mod_act = menu.addAction("Rinomina")
        dup_act = menu.addAction("Duplica")
        del_act = menu.addAction("Elimina")
        
        activate_act.triggered.connect(lambda: self.presentation_activate_requested.emit(uuid))
        mod_act.triggered.connect(lambda: self.presentation_edit_requested.emit(uuid))
        dup_act.triggered.connect(lambda: self.presentation_duplicate_requested.emit(uuid))
        del_act.triggered.connect(lambda: self.presentation_delete_requested.emit(uuid))
        
        menu.exec(self.pres_list.mapToGlobal(pos))
            
    def show_layer_context_menu(self, pos):
        item = self.layer_list.itemAt(pos)
        if item is None:
            return
            
        idx = self.layer_list.row(item)
        
        menu = QMenu()
        mod_act = menu.addAction("Modifica Livello")
        del_act = menu.addAction("Elimina Livello")
        
        mod_act.triggered.connect(lambda: self.layer_edit_requested.emit(idx))
        del_act.triggered.connect(lambda: self.layer_delete_requested.emit(idx))
        
        menu.exec(self.layer_list.mapToGlobal(pos))
