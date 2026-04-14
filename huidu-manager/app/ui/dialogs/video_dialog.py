import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from app.ui.dialogs.image_dialog import CommonEffectSection

class VideoDialog(QDialog):
    item_created = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Livello Video")
        self.setFixedSize(400, 350)
        
        self.selected_file = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # File selector
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Nessun video selezionato")
        self.info_label = QLabel("0 MB")
        self.info_label.setStyleSheet("color: #888888; font-size: 9pt;")
        
        self.btn_browse = QPushButton("Sfoglia...")
        self.btn_browse.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)
        layout.addWidget(self.info_label)
        
        # Aspect Ratio
        self.chk_aspect_ratio = QCheckBox("Mantieni proporzioni")
        self.chk_aspect_ratio.setChecked(False)
        layout.addWidget(self.chk_aspect_ratio)
        
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
            self, "Seleziona Video", "", 
            "Video (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(file_path.split("/")[-1])
            try:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                self.info_label.setText(f"{size_mb:.2f} MB")
            except Exception:
                self.info_label.setText("Sconosciuto")
            
    def submit(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Attenzione", "Devi selezionare un video.")
            return
            
        effect_data = self.effect_section.get_effect_data()
        
        item_data = {
            "type": "video",
            "file": self.selected_file,
            "aspect_ratio": self.chk_aspect_ratio.isChecked(),
            "effect": effect_data
        }
        
        self.item_created.emit(item_data)
        self.accept()
