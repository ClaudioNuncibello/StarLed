from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QFontComboBox, QSpinBox, 
    QCheckBox, QMessageBox, QColorDialog
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal
from app.ui.dialogs.image_dialog import CommonEffectSection

class TextDialog(QDialog):
    item_created = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Livello Testo")
        self.setFixedSize(500, 600)
        self.current_color = QColor(255, 255, 255)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Text Input
        self.text_input = QTextEdit()
        self.text_input.setFixedHeight(50)
        self.text_input.setPlaceholderText("Inserisci il testo qui...")
        layout.addWidget(QLabel("Testo:"))
        layout.addWidget(self.text_input)
        
        # Font settings
        font_layout = QHBoxLayout()
        self.font_combo = QFontComboBox()
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 256)
        self.font_spin.setValue(14)
        
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(24, 24)
        self.update_color_button()
        self.btn_color.clicked.connect(self.choose_color)
        
        font_layout.addWidget(QLabel("Font:"))
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(QLabel("Dim:"))
        font_layout.addWidget(self.font_spin)
        font_layout.addWidget(self.btn_color)
        layout.addLayout(font_layout)
        
        # Font styling (B, I, U)
        style_layout = QHBoxLayout()
        self.chk_bold = QCheckBox("B")
        self.chk_bold.setStyleSheet("font-weight: bold;")
        self.chk_italic = QCheckBox("I")
        self.chk_italic.setStyleSheet("font-style: italic;")
        self.chk_underline = QCheckBox("U")
        self.chk_underline.setStyleSheet("text-decoration: underline;")
        
        style_layout.addWidget(self.chk_bold)
        style_layout.addWidget(self.chk_italic)
        style_layout.addWidget(self.chk_underline)
        style_layout.addStretch()
        layout.addLayout(style_layout)
        
        # Alignment
        align_layout = QHBoxLayout()
        self.combo_align = QComboBox()
        self.combo_align.addItems(["left", "center", "right"])
        self.combo_align.setCurrentText("center")
        
        self.combo_valign = QComboBox()
        self.combo_valign.addItems(["top", "middle", "bottom"])
        self.combo_valign.setCurrentText("middle")
        
        align_layout.addWidget(QLabel("Allineamento Orizzontale:"))
        align_layout.addWidget(self.combo_align)
        align_layout.addWidget(QLabel("Verticale:"))
        align_layout.addWidget(self.combo_valign)
        layout.addLayout(align_layout)
        
        # Toggles (Multiline, TTS)
        toggles_layout = QHBoxLayout()
        self.chk_multiline = QCheckBox("Multiriga")
        self.chk_playtext = QCheckBox("Voce TTS (PlayText)")
        toggles_layout.addWidget(self.chk_multiline)
        toggles_layout.addWidget(self.chk_playtext)
        layout.addLayout(toggles_layout)
        
        # Effect Section with text effects
        self.effect_section = CommonEffectSection(include_text_effects=True)
        # Adding text-specific effects
        self.effect_section.effect_type.addItem("26 - Scorrimento Continuo (Sinistra)", 26)
        self.effect_section.effect_type.addItem("27 - Scorrimento Continuo (Destra)", 27)
        self.effect_section.effect_type.addItem("30 - Lampeggio", 30)
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
        
    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Scegli Colore")
        if color.isValid():
            self.current_color = color
            self.update_color_button()
            
    def update_color_button(self):
        self.btn_color.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid #aaa;")
        
    def submit(self):
        text = self.text_input.toPlainText()
        if not text:
            QMessageBox.warning(self, "Attenzione", "Il testo non può essere vuoto.")
            return
            
        effect_data = self.effect_section.get_effect_data()
        
        font_data = {
            "name": self.font_combo.currentText(),
            "size": self.font_spin.value(),
            "color": self.current_color.name(),
            "bold": self.chk_bold.isChecked(),
            "italic": self.chk_italic.isChecked(),
            "underline": self.chk_underline.isChecked()
        }
        
        item_data = {
            "type": "text",
            "string": text,
            "font": font_data,
            "alignment": f"{self.combo_valign.currentText()},{self.combo_align.currentText()}",
            "multi_line": self.chk_multiline.isChecked(),
            "play_text": self.chk_playtext.isChecked(),
            "effect": effect_data
        }
        
        self.item_created.emit(item_data)
        self.accept()
