from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QSlider, QPushButton,
    QGridLayout, QMessageBox, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

class DeviceWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, action, manager, device_id, *args):
        super().__init__()
        self.action = action
        self.manager = manager
        self.device_id = device_id
        self.args = args

    def run(self):
        try:
            if self.action == "set_prop":
                self.manager.device_api.set_device_property(self.device_id, **self.args[0])
            elif self.action == "reboot":
                self.manager.device_api.reboot_device(self.device_id, delay=5)
            elif self.action == "open":
                self.manager.device_api.open_screen(self.device_id)
            elif self.action == "close":
                self.manager.device_api.close_screen(self.device_id)
            self.finished.emit()
        except Exception as e:
            err_msg = getattr(e, 'message', str(e))
            print(f"Error executing DeviceWorker action {self.action}: {err_msg}")
            self.error.emit(err_msg)

class ScreenSettingsDialog(QDialog):
    def __init__(self, device_id, device_props, screen_manager, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self.props = device_props
        self.manager = screen_manager
        
        self.setWindowTitle("Impostazioni Schermo")
        self.setFixedSize(380, 480)
        
        self._workers = set()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(500)
        self.debounce_timer.timeout.connect(self._apply_properties)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        def safe_int(key, default):
            try:
                return int(self.props.get(key, default))
            except (TypeError, ValueError):
                return default
        
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
        self.lum_slider.setValue(safe_int('luminance', 50))
        
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
        self.vol_slider.setValue(safe_int('volume', 50))
        
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
        grid.addWidget(QLabel("IP Ethernet:"), 0, 0)
        try:
            eth_ip = self.props.get('eth.ip', "N/D")
        except AttributeError:
            eth_ip = "N/D"
        grid.addWidget(QLabel(eth_ip), 0, 1)
        grid.addWidget(QLabel("Larghezza:"), 1, 0)
        grid.addWidget(QLabel(f"{self.props.get('screen.width', 0)} px"), 1, 1)
        grid.addWidget(QLabel("Altezza:"), 2, 0)
        grid.addWidget(QLabel(f"{self.props.get('screen.height', 0)} px"), 2, 1)
        grid.addWidget(QLabel("Firmware OS:"), 3, 0)
        grid.addWidget(QLabel(self.props.get('version.app', 'N/D')), 3, 1)
        
        layout.addLayout(grid)
        layout.addStretch()

    def on_slider_change(self, label, value):
        label.setText(str(value))
        self.debounce_timer.start()

    def _apply_properties(self):
        lum = self.lum_slider.value()
        vol = self.vol_slider.value()
        self._run_async("set_prop", {"luminance": str(lum), "volume": str(vol)})

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
        worker = DeviceWorker(action, self.manager, self.device_id, *args)
        self._workers.add(worker)
        
        def on_finished():
            self._workers.discard(worker)
            
        def on_error(msg):
            self._workers.discard(worker)
            QMessageBox.warning(self, "Errore Dispositivo", f"L'azione '{action}' è fallita:\n{msg}")
            
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
