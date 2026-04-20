from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFontComboBox, QSpinBox, QCheckBox, 
    QMessageBox, QColorDialog, QTabWidget, QWidget, QStackedWidget
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal

class ColorPickerButton(QPushButton):
    def __init__(self, default_color="#ffffff", parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.current_color = QColor(default_color)
        self.update_style()
        self.clicked.connect(self.choose_color)
        
    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Scegli colore")
        if color.isValid():
            self.current_color = color
            self.update_style()
            
    def update_style(self):
        self.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid #aaa;")

class ClockDialog(QDialog):
    item_created = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Livello Orologio")
        self.setFixedSize(500, 650)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Clock Type switcher
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo di orologio:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Digitale (digitalClock)", "Analogico (dialClock)"])
        self.combo_type.currentIndexChanged.connect(self.switch_clock_type)
        type_layout.addWidget(self.combo_type)
        layout.addLayout(type_layout)
        
        # Timezone
        tz_layout = QHBoxLayout()
        tz_layout.addWidget(QLabel("Fuso orario:"))
        self.combo_tz = QComboBox()
        self.combo_tz.addItems(["+0:00 (UTC)", "+1:00 (CET)", "+2:00 (EET)", "+8:00 (CST)", "-5:00 (EST)"])
        self.combo_tz.setCurrentIndex(1)
        tz_layout.addWidget(self.combo_tz)
        layout.addLayout(tz_layout)
        
        # General Font Settings
        font_layout = QHBoxLayout()
        self.font_combo = QFontComboBox()
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 256)
        self.font_spin.setValue(14)
        self.btn_font_color = ColorPickerButton("#ffffff")
        
        font_layout.addWidget(QLabel("Font base:"))
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(QLabel("Dim:"))
        font_layout.addWidget(self.font_spin)
        font_layout.addWidget(self.btn_font_color)
        layout.addLayout(font_layout)
        
        # Stack wrapper per Digitale o Analogico
        self.stack = QStackedWidget()
        
        # --- Pagina Digitale ---
        page_digital = QWidget()
        dig_layout = QVBoxLayout(page_digital)
        
        self.chk_multiline = QCheckBox("Testo Multiriga")
        dig_layout.addWidget(self.chk_multiline)
        
        # Funzione helper date/time format settings
        def create_format_row(label_text, default_formats):
            row = QHBoxLayout()
            chk = QCheckBox(label_text)
            chk.setChecked(True)
            cmb = QComboBox()
            if default_formats:
                cmb.addItems(default_formats)
            col = ColorPickerButton("#ffffff")
            row.addWidget(chk)
            row.addWidget(cmb)
            row.addStretch()
            row.addWidget(col)
            return row, chk, cmb, col
            
        self.date_row, self.chk_date, self.cmb_date, self.col_date = create_format_row(
            "Data (YYYY/MM/DD)", ["0 (YYYY/MM/DD)", "1 (MM/DD/YYYY)", "2 (DD/MM/YYYY)"]
        )
        self.time_row, self.chk_time, self.cmb_time, self.col_time = create_format_row(
            "Ora (hh:mm:ss)", ["0 (hh:mm:ss)", "1 (hh:mm)", "2 (hh时mm分ss秒)"]
        )
        self.week_row, self.chk_week, self.cmb_week, self.col_week = create_format_row(
            "Giorno della settimana", ["0 (星期一)", "1 (Monday)", "2 (Mon)"]
        )
        
        # Lunar è solo visible e color
        lunar_layout = QHBoxLayout()
        self.chk_lunar = QCheckBox("Calendario Lunare")
        self.col_lunar = ColorPickerButton("#ffffff")
        lunar_layout.addWidget(self.chk_lunar)
        lunar_layout.addStretch()
        lunar_layout.addWidget(self.col_lunar)
        
        dig_layout.addLayout(self.date_row)
        dig_layout.addLayout(self.time_row)
        dig_layout.addLayout(self.week_row)
        dig_layout.addLayout(lunar_layout)
        dig_layout.addStretch()
        
        # --- Pagina Analogico ---
        page_analog = QWidget()
        ana_layout = QVBoxLayout(page_analog)
        
        for lbl_text, col_ref, default_c in [
            ("Lancetta Ore", "col_hour_hand", "#ffffff"),
            ("Lancetta Minuti", "col_minute_hand", "#ffffff"),
            ("Lancetta Secondi", "col_second_hand", "#ff0000"),
            ("Scala Ore (tacche)", "col_hour_scale", "#ffffff"),
            ("Scala Minuti", "col_minute_scale", "#ffffff")
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(lbl_text))
            col = ColorPickerButton(default_c)
            setattr(self, col_ref, col)
            row.addStretch()
            row.addWidget(col)
            ana_layout.addLayout(row)
            
        ana_layout.addStretch()
        
        self.stack.addWidget(page_digital)
        self.stack.addWidget(page_analog)
        layout.addWidget(self.stack)
        
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
        
    def switch_clock_type(self, index):
        self.stack.setCurrentIndex(index)
        
    def submit(self):
        is_digital = self.combo_type.currentIndex() == 0
        clock_type = "digitalClock" if is_digital else "dialClock"
        tz_str = self.combo_tz.currentText().split(" ")[0]
        
        font_data = {
            "name": self.font_combo.currentText(),
            "size": self.font_spin.value(),
            "color": self.btn_font_color.current_color.name(),
            "bold": False,
            "italic": False,
            "underline": False
        }
        
        item_data = {
            "type": clock_type,
            "timezone": tz_str,
            "font": font_data
        }
        
        if is_digital:
            item_data["multi_line"] = self.chk_multiline.isChecked()
            item_data["date"] = {
                "visible": self.chk_date.isChecked(),
                "format": int(self.cmb_date.currentText()[0]),
                "color": self.col_date.current_color.name()
            }
            item_data["time"] = {
                "visible": self.chk_time.isChecked(),
                "format": int(self.cmb_time.currentText()[0]),
                "color": self.col_time.current_color.name()
            }
            item_data["week"] = {
                "visible": self.chk_week.isChecked(),
                "format": int(self.cmb_week.currentText()[0]),
                "color": self.col_week.current_color.name()
            }
            item_data["lunar"] = {
                "visible": self.chk_lunar.isChecked(),
                "color": self.col_lunar.current_color.name()
            }
        else:
            item_data["hour_hand_color"] = getattr(self, "col_hour_hand").current_color.name()
            item_data["minute_hand_color"] = getattr(self, "col_minute_hand").current_color.name()
            item_data["second_hand_color"] = getattr(self, "col_second_hand").current_color.name()
            item_data["hour_scale_color"] = getattr(self, "col_hour_scale").current_color.name()
            item_data["minute_scale_color"] = getattr(self, "col_minute_scale").current_color.name()
            
        self.item_created.emit(item_data)
        self.accept()
