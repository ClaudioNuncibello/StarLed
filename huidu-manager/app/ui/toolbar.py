from PyQt6.QtWidgets import QToolBar, QPushButton, QWidget, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt

class Toolbar(QToolBar):
    new_playlist_requested = pyqtSignal()
    new_item_requested = pyqtSignal(str)   # "image" | "video" | "text" | "clock"
    screen_settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setStyleSheet("QToolBar { spacing: 10px; }")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Pulsante Playlist
        self.btn_new_playlist = QPushButton("+ Nuova playlist")
        self.btn_new_playlist.setObjectName("AccentTextButton")
        self.btn_new_playlist.setEnabled(False) # Abilitato se schermo selezionato
        self.btn_new_playlist.clicked.connect(self.new_playlist_requested.emit)
        self.addWidget(self.btn_new_playlist)
        
        self.addSeparator()
        
        # Pulsanti Items
        self.btn_image = QPushButton("🖼 Nuova immagine")
        self.btn_video = QPushButton("▶ Nuovo video")
        self.btn_text = QPushButton("T Nuovo testo")
        self.btn_clock = QPushButton("🕐 Nuovo orologio")
        
        self.item_buttons = [self.btn_image, self.btn_video, self.btn_text, self.btn_clock]
        for btn in self.item_buttons:
            btn.setEnabled(False) # Abilitati se presentazione selezionata
            self.addWidget(btn)
            
        self.btn_image.clicked.connect(lambda: self.new_item_requested.emit("image"))
        self.btn_video.clicked.connect(lambda: self.new_item_requested.emit("video"))
        self.btn_text.clicked.connect(lambda: self.new_item_requested.emit("text"))
        self.btn_clock.clicked.connect(lambda: self.new_item_requested.emit("clock"))
        
        # Spacer per allineare a destra il pulsante settings
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.addWidget(spacer)
        
        self.addSeparator()
        
        # Pulsante Schermo
        self.btn_screen_settings = QPushButton("⚙ Schermo")
        self.btn_screen_settings.setEnabled(False) # Abilitato se schermo selezionato
        self.btn_screen_settings.clicked.connect(self.screen_settings_requested.emit)
        self.addWidget(self.btn_screen_settings)

    def on_screen_selected(self, active: bool):
        self.btn_new_playlist.setEnabled(active)
        self.btn_screen_settings.setEnabled(active)
        
    def on_presentation_selected(self, active: bool):
        for btn in self.item_buttons:
            btn.setEnabled(active)
