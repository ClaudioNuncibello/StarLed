import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from app.auth.license_client import LicenseStatus

class LicenseWorker(QThread):
    """
    Worker per validare la licenza asincronamente.
    ATTENZIONE: STUB TEMPORANEO (Fase 2)
    """
    verification_done = pyqtSignal(LicenseStatus)

    def __init__(self, email: str, mac: str = ""):
        super().__init__()
        self.email = email
        self.mac = mac
        
    def run(self):
        # STUB TEMPORANEO: simuliamo networking delay e ritorniamo VALID
        self.msleep(800)
        self.verification_done.emit(LicenseStatus.VALID)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Accesso SLPlayer")
        # Fix non chiudibile dalla 'X' o annullabile via Esc
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(360, 420)
        
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Logo S
        self.logo_label = QLabel("S")
        self.logo_label.setFixedSize(44, 44)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("""
            QLabel {
                background-color: #e07820;
                color: white;
                font-size: 24pt;
                font-weight: bold;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # Title "SLPlayer"
        self.title_label = QLabel("SLPlayer")
        self.title_label.setStyleSheet("font-size: 15pt; font-weight: bold; color: #cccccc;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel("Inserisci la tua email per attivare l'app")
        self.subtitle_label.setStyleSheet("font-size: 11pt; color: #888888;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label)
        
        layout.addSpacing(16)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@esempio.it")
        self.email_input.setFixedHeight(36)
        layout.addWidget(self.email_input)
        
        # Status label (spinner testuale)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #e07820;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # Login Button
        self.login_button = QPushButton("Accedi")
        self.login_button.setObjectName("PrimaryButton")
        self.login_button.setFixedHeight(38)
        self.login_button.clicked.connect(self.on_login_clicked)
        layout.addWidget(self.login_button)
        
        layout.addStretch()
        
        # Footer
        self.footer_label = QLabel("Starled Italia s.r.l.s")
        self.footer_label.setStyleSheet("font-size: 10pt; color: #555555;")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.footer_label)

    def on_login_clicked(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Errore", "Inserisci un indirizzo email valido.")
            return
            
        self.login_button.setDisabled(True)
        self.email_input.setDisabled(True)
        self.status_label.setText("Verifica in corso...")
        self.status_label.setVisible(True)
        
        # Inizializza il worker per validazione server in background
        self.worker = LicenseWorker(email)
        self.worker.verification_done.connect(self.on_verification_done)
        self.worker.start()

    def on_verification_done(self, status: LicenseStatus):
        self.worker.deleteLater()
        self.worker = None
        
        if status == LicenseStatus.VALID:
            # Login verificato correttamente, apre mainUI
            self.accept()
        else:
            self.login_button.setDisabled(False)
            self.email_input.setDisabled(False)
            self.status_label.setVisible(False)
            
            # Recupero msg d'errore
            errors = {
                LicenseStatus.INVALID: "Licenza non valida per questa email.",
                LicenseStatus.EXPIRED: "Licenza scaduta. Contatta il supporto.",
                LicenseStatus.NOT_FOUND: "Email non riconosciuta.",
                LicenseStatus.NETWORK_ERROR: "Impossibile contattare il server. Controlla la connessione."
            }
            msg = errors.get(status, "Errore sconosciuto.")
            QMessageBox.critical(self, "Autenticazione Fallita", msg)
    
    def reject(self):
        """Disabilita uscita con ESC"""
        pass
