import hashlib
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog, QSlider, QSpinBox, QMessageBox, QWidget
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
try:
    from app.core.presentation_model import ImageItem, Effect
except ImportError:
    ImageItem = dict
    Effect = dict

def get_file_md5(path: str) -> str:
    hash_md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return ""

class CommonEffectSection(QWidget):
    def __init__(self, include_text_effects=False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Effetto e Transizione"))
        
        # Effect Type
        self.effect_type = QComboBox()
        # Mocking effect IDs. In reality should import the map.
        self.effect_type.addItem("0 - Rapido", 0)
        self.effect_type.addItem("1 - Spostamento Sinistra", 1)
        self.effect_type.addItem("5 - Cubo", 5)
        # add generic options 0 to 25
        # if include_text_effects: add 26 to 30
        layout.addWidget(self.effect_type)
        
        # Speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Velocità:"))
        self.effect_speed = QSlider(Qt.Orientation.Horizontal)
        self.effect_speed.setRange(0, 8)
        self.effect_speed.setValue(4)
        self.speed_label = QLabel("4")
        self.effect_speed.valueChanged.connect(lambda v: self.speed_label.setText(str(v)))
        speed_layout.addWidget(self.effect_speed)
        speed_layout.addWidget(self.speed_label)
        layout.addLayout(speed_layout)
        
        # Hold Time
        hold_layout = QHBoxLayout()
        hold_layout.addWidget(QLabel("Durata sosta (ms):"))
        self.hold_ms = QSpinBox()
        self.hold_ms.setRange(0, 9999999)
        self.hold_ms.setValue(5000)
        hold_layout.addWidget(self.hold_ms)
        layout.addLayout(hold_layout)
        
    def get_effect_data(self):
        # returns simple dict or Effect instance based on needs
        return {
            "type": self.effect_type.currentData() or 0,
            "speed": self.effect_speed.value(),
            "hold": self.hold_ms.value()
        }

class ImageDialog(QDialog):
    item_created = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Livello Immagine")
        self.setFixedSize(400, 450)
        
        self.selected_file = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # File selector
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Nessun file selezionato")
        self.btn_browse = QPushButton("Sfoglia...")
        self.btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)
        
        # Thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(80, 50)
        self.thumbnail.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555;")
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Fit options
        fit_layout = QHBoxLayout()
        fit_layout.addWidget(QLabel("Adattamento (Fit):"))
        self.combo_fit = QComboBox()
        self.combo_fit.addItems(["stretch", "fill", "center", "tile"])
        fit_layout.addWidget(self.combo_fit)
        layout.addLayout(fit_layout)
        
        # Effect Section
        self.effect_section = CommonEffectSection(include_text_effects=False)
        layout.addWidget(self.effect_section)
        
        layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annulla")
        self.btn_submit = QPushButton("Aggiungi livello")
        self.btn_submit.setObjectName("PrimaryButton")
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_submit.clicked.connect(self.submit)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_submit)
        layout.addLayout(btn_layout)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Immagine", "", 
            "Immagini (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(file_path.split("/")[-1])
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.thumbnail.setPixmap(pixmap.scaled(80, 50, Qt.AspectRatioMode.KeepAspectRatio))
            
            # Anti-duplication logic should go here via MD5
            # md5_hash = get_file_md5(file_path)
            
    def submit(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Attenzione", "Devi selezionare un'immagine.")
            return
            
        effect_data = self.effect_section.get_effect_data()
        
        item_data = {
            "type": "image",
            "file": self.selected_file,
            "fit": self.combo_fit.currentText(),
            "effect": effect_data
        }
        
        self.item_created.emit(item_data)
        self.accept()
