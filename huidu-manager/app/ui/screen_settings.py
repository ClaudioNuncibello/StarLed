from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QSlider, QPushButton,
    QGridLayout, QMessageBox, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

class DeviceWorker(QThread):
    def __init__(self, action, manager, device_id, *args):
        super().__init__()
        self.action = action
        self.manager = manager
        self.device_id = device_id
        self.args = args

    def run(self):
        try:
            if self.action == "set_prop":
                self.manager.gateway.set_device_property(self.device_id, *self.args)
            elif self.action == "reboot":
                self.manager.gateway.reboot_device(self.device_id, delay=5)
            elif self.action == "open":
                self.manager.gateway.open_device_screen(self.device_id)
            elif self.action == "close":
                self.manager.gateway.close_device_screen(self.device_id)
        except Exception as e:
            print(f"Error executing DeviceWorker action {self.action}: {e}")

class ScreenSettingsDialog(QDialog):
    def __init__(self, device_id, device_props, screen_manager, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self.props = device_props
        self.manager = screen_manager
        
        self.setWindowTitle("Impostazioni Schermo")
        self.setFixedSize(380, 480)
        
        self.worker = None
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(500)
        self.debounce_timer.timeout.connect(self._apply_properties)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header_text = f"● {self.device_id}  |  FW: {self.props.get('firmwareVersion', 'N/D')}"
        header_label = QLabel(header_text)
        header_label.setStyleSheet("color: #e07820; font-weight: bold; font-size: 13pt;")
        layout.addWidget(header_label)
        
        # Brightness Slider
        layout.addWidget(QLabel("Luminosità"))
        lum_layout = QHBoxLayout()
        self.lum_slider = QSlider(Qt.Orientation.Horizontal)
        self.lum_slider.setRange(0, 100)
        self.lum_slider.setValue(self.props.get('luminance', 50))
        
        self.lum_val_label = QLabel(str(self.lum_slider.value()))
        self.lum_slider.valueChanged.connect(lambda v: self.on_slider_change(self.lum_val_label, v))
        
        lum_layout.addWidget(self.lum_slider)
        lum_layout.addWidget(self.lum_val_label)
        layout.addLayout(lum_layout)
        
        # Volume Slider
        layout.addWidget(QLabel("Volume"))
        vol_layout = QHBoxLayout()
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.props.get('volume', 50))
        
        self.vol_val_label = QLabel(str(self.vol_slider.value()))
        self.vol_slider.valueChanged.connect(lambda v: self.on_slider_change(self.vol_val_label, v))
        
        vol_layout.addWidget(self.vol_slider)
        vol_layout.addWidget(self.vol_val_label)
        layout.addLayout(vol_layout)
        
        # Action Buttons
        self.btn_accendi = QPushButton("⏻ Accendi schermo")
        self.btn_accendi.clicked.connect(self.on_accendi)
        layout.addWidget(self.btn_accendi)
        
        self.btn_spegni = QPushButton("◻ Spegni schermo")
        self.btn_spegni.clicked.connect(self.on_spegni)
        layout.addWidget(self.btn_spegni)
        
        self.btn_riavvia = QPushButton("↺ Riavvia dispositivo")
        self.btn_riavvia.setObjectName("DangerButton")
        self.btn_riavvia.clicked.connect(self.on_riavvia)
        layout.addWidget(self.btn_riavvia)
        
        layout.addSpacing(16)
        
        # Network and Hardware Info Grid
        grid = QGridLayout()
        grid.addWidget(QLabel("IP Gateway:"), 0, 0)
        try:
            gateway_ip = self.manager.gateway.ip if self.manager else "N/D"
        except AttributeError:
            gateway_ip = "N/D"
        grid.addWidget(QLabel(gateway_ip), 0, 1)
        grid.addWidget(QLabel("Larghezza:"), 1, 0)
        grid.addWidget(QLabel(f"{self.props.get('width', 0)} px"), 1, 1)
        grid.addWidget(QLabel("Altezza:"), 2, 0)
        grid.addWidget(QLabel(f"{self.props.get('height', 0)} px"), 2, 1)
        grid.addWidget(QLabel("Hardware:"), 3, 0)
        grid.addWidget(QLabel(self.props.get('hardwareVersion', 'N/D')), 3, 1)
        
        layout.addLayout(grid)
        layout.addStretch()

    def on_slider_change(self, label, value):
        label.setText(str(value))
        self.debounce_timer.start()

    def _apply_properties(self):
        lum = self.lum_slider.value()
        vol = self.vol_slider.value()
        self._run_async("set_prop", {"luminance": lum, "volume": vol})

    def on_accendi(self):
        self._run_async("open")

    def on_spegni(self):
        self._run_async("close")

    def on_riavvia(self):
        reply = QMessageBox.question(
            self, 'Riavvio', 'Sei sicuro di voler riavviare il dispositivo? L\'operazione causerà disservizio momentaneo.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_async("reboot")
            self.accept()
            
    def _run_async(self, action, *args):
        self.worker = DeviceWorker(action, self.manager, self.device_id, *args)
        self.worker.start()
