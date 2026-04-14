import sys
import os
from PyQt6.QtWidgets import QApplication

from app.ui.login_dialog import LoginDialog
from app.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Carica stylesheet
    style_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            
    # Fase di Login as Blocking
    login_dialog = LoginDialog()
    if login_dialog.exec():
        print("Login Validation Superata (STUB)")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        print("Uscita app")
        sys.exit(0)

if __name__ == "__main__":
    main()
