from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QRect

class CanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewCanvas")
        self.screen_w = 128
        self.screen_h = 64
        self.layers = []
        self.selected_layer_idx = -1
        self.has_screen = False
        
    def set_screen_size(self, w, h):
        self.has_screen = True
        self.screen_w = max(1, w)
        self.screen_h = max(1, h)
        self.update()
        
    def clear_screen(self):
        self.has_screen = False
        self.layers = []
        self.update()
        
    def set_layers(self, layers_list, selected_idx=-1):
        self.layers = layers_list
        self.selected_layer_idx = selected_idx
        self.update()
        
    def paintEvent(self, event):
        if not self.has_screen:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Sfondo Nero per LED
        rect = self.rect()
        painter.fillRect(rect, QColor("#000000"))
        
        # Calcolo scala
        scale_w = rect.width() / self.screen_w
        scale_h = rect.height() / self.screen_h
        scale = min(scale_w, scale_h)
        
        draw_w = self.screen_w * scale
        draw_h = self.screen_h * scale
        offset_x = (rect.width() - draw_w) / 2
        offset_y = (rect.height() - draw_h) / 2
        
        painter.translate(offset_x, offset_y)
        painter.setClipRect(0, 0, int(draw_w), int(draw_h))

        # Per il calcolo coord, noi abbiamo l'area full screen.
        # Stampiamo i layer dal fondo (ultimo nella lista) verso la cima (zero)
        # come un livello Photoshop
        for idx, item in reversed(list(enumerate(self.layers))):
            itype = item.get("type", "unknown")
            
            # Layer Canvas full
            item_rect = QRect(0, 0, int(draw_w), int(draw_h))
            
            if itype == "image":
                 file_path = item.get("file", "")
                 import os
                 from PyQt6.QtGui import QPixmap
                 if file_path and os.path.exists(file_path):
                     pixmap = QPixmap(file_path)
                     if not pixmap.isNull():
                         fit = item.get("fit", "stretch")
                         if fit == "stretch":
                             pixmap = pixmap.scaled(item_rect.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                         elif fit in ("center", "tile"):
                             pixmap = pixmap.scaled(item_rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                         elif fit == "fill":
                             pixmap = pixmap.scaled(item_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                         
                         x_offset = (item_rect.width() - pixmap.width()) // 2
                         y_offset = (item_rect.height() - pixmap.height()) // 2
                         painter.drawPixmap(item_rect.x() + x_offset, item_rect.y() + y_offset, pixmap)
                     else:
                         painter.fillRect(item_rect, QColor(26, 58, 90, 150))
                         painter.setPen(QColor(85, 170, 255))
                         painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, "🖼 Errore Immagine")
                 else:
                     painter.fillRect(item_rect, QColor(26, 58, 90, 150))
                     painter.setPen(QColor(85, 170, 255))
                     painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, "🖼 Immagine assente")
            elif itype == "video":
                 painter.fillRect(item_rect, QColor(58, 26, 26, 150))
                 painter.setPen(QColor(255, 136, 136))
                 file_path = item.get("file", "")
                 import os
                 filename = os.path.basename(file_path) if file_path else "Nuovo Video"
                 painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, f"▶ Video\n{filename}")
            elif itype == "text":
                 painter.fillRect(item_rect, QColor(42, 42, 26, 150))
                 painter.setPen(QColor(238, 221, 136))
                 painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, item.get("string", "T Testo"))
            elif itype in ("digitalclock", "dialclock"):
                 painter.fillRect(item_rect, QColor(26, 42, 58, 150))
                 painter.setPen(QColor(136, 204, 255))
                 painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, "🕐 Orologio")
                 
        # Draw selection rectangle on top of everything
        if self.selected_layer_idx != -1 and 0 <= self.selected_layer_idx < len(self.layers):
             pen = QPen(QColor("#e07820"))
             pen.setWidth(3)
             painter.setPen(pen)
             painter.setBrush(Qt.BrushStyle.NoBrush)
             painter.drawRect(0, 0, int(draw_w), int(draw_h))


class PreviewArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Canvas reale (Anteprima)
        self.canvas = CanvasWidget()
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas, 1)
        
        # Barra Info (Misure Schermo)
        self.info_bar = QWidget()
        self.info_bar.setObjectName("InfoBar")
        self.info_bar.setStyleSheet("background-color: #1e1e1e; border-top: 1px solid #333333;")
        self.info_bar.setFixedHeight(24)
        
        info_layout = QHBoxLayout(self.info_bar)
        info_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #888888; font-size: 9pt;")
        info_layout.addWidget(self.lbl_info, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.info_bar, 0)
        
    def update_screen_info(self, width, height, is_online):
        self.canvas.set_screen_size(width, height)
        self.lbl_info.setText(f"Dimensioni schermo: {width}x{height} px")
        
    def clear_screen_info(self):
        self.lbl_info.setText("")
        self.canvas.clear_screen()
        
    def update_layers(self, items, selected_idx=-1):
        self.canvas.set_layers(items, selected_idx)
