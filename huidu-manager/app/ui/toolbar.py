from PyQt6.QtWidgets import QToolBar, QPushButton, QWidget, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt

class Toolbar(QToolBar):
    new_playlist_requested = pyqtSignal()
    new_item_requested = pyqtSignal(str)   # "image" | "video" | "text" | "clock"
    push_playlist_requested = pyqtSignal()
    screen_settings_requested = pyqtSignal()
    schedule_requested = pyqtSignal()
    discovery_requested = pyqtSignal()
    clear_screen_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setStyleSheet("""
            QToolBar { 
                spacing: 4px; 
                padding: 2px 4px;
            }
            QPushButton {
                padding: 4px 8px;
                text-align: center;
            }
        """)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Pulsante Discovery — sempre abilitato
        self.btn_discover = QPushButton("🔍 Cerca")
        self.btn_discover.setObjectName("AccentTextButton")
        self.btn_discover.setToolTip("Scansiona la rete locale alla ricerca di controller Huidu (porta 30080)")
        self.btn_discover.clicked.connect(self.discovery_requested.emit)
        self.addWidget(self.btn_discover)

        self.addSeparator()

        # Pulsante Playlist
        self.btn_new_playlist = QPushButton("+ Playlist")
        self.btn_new_playlist.setObjectName("AccentTextButton")
        self.btn_new_playlist.setEnabled(False) # Abilitato se schermo selezionato
        self.btn_new_playlist.clicked.connect(self.new_playlist_requested.emit)
        self.addWidget(self.btn_new_playlist)
        
        # Pulsante Palinsesto (spostato qui vicino alle playlist)
        self.btn_schedule = QPushButton("📅 Palinsesto")
        self.btn_schedule.setEnabled(False) # Abilitato se schermo selezionato
        self.btn_schedule.clicked.connect(self.schedule_requested.emit)
        self.addWidget(self.btn_schedule)
        
        self.addSeparator()
        
        # Pulsanti Items
        self.btn_image = QPushButton("🖼 Immagine")
        self.btn_video = QPushButton("▶ Video")
        self.btn_text = QPushButton("T Testo")
        self.btn_clock = QPushButton("🕐 Orologio")
        
        self.item_buttons = [self.btn_image, self.btn_video, self.btn_text, self.btn_clock]
        for btn in self.item_buttons:
            btn.setEnabled(False) # Abilitati se presentazione selezionata
            self.addWidget(btn)
            
        self.btn_image.clicked.connect(lambda: self.new_item_requested.emit("image"))
        self.btn_video.clicked.connect(lambda: self.new_item_requested.emit("video"))
        self.btn_text.clicked.connect(lambda: self.new_item_requested.emit("text"))
        self.btn_clock.clicked.connect(lambda: self.new_item_requested.emit("clock"))
        
        # Spaziatore elastico
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
        
        # Pulsante Invio a Schermo
        self.btn_push_playlist = QPushButton("🚀 Sincronizza")
        self.btn_push_playlist.setObjectName("PrimaryButton")
        self.btn_push_playlist.setEnabled(False) # Abilitato se presentazione selezionata
        self.btn_push_playlist.clicked.connect(self.push_playlist_requested.emit)
        self.addWidget(self.btn_push_playlist)
        
        # Pulsante Svuota Schermo
        self.btn_clear_screen = QPushButton("Svuota Schermo")
        self.btn_clear_screen.setEnabled(False)
        self.btn_clear_screen.clicked.connect(self.clear_screen_requested.emit)
        self.addWidget(self.btn_clear_screen)

        self.addSeparator()
        
        # Pulsante Schermo
        self.btn_screen_settings = QPushButton("⚙ Schermo")
        self.btn_screen_settings.setEnabled(False) # Abilitato se schermo selezionato
        self.btn_screen_settings.clicked.connect(self.screen_settings_requested.emit)
        self.addWidget(self.btn_screen_settings)

    def on_screen_selected(self, active: bool):
        self.btn_new_playlist.setEnabled(active)
        self.btn_screen_settings.setEnabled(active)
        self.btn_schedule.setEnabled(active)
        self.btn_clear_screen.setEnabled(active)
        
    def on_presentation_selected(self, active: bool):
        for btn in self.item_buttons:
            btn.setEnabled(active)
        self.btn_push_playlist.setEnabled(active)
