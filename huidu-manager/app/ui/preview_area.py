from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
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
        # Gli Item vengono stampati in ordine su layer sovrapposti whole screen.
        for idx, item in enumerate(self.layers):
            itype = item.get("type", "unknown")
            is_selected = (idx == self.selected_layer_idx)
            
            # Layer Canvas full
            item_rect = QRect(0, 0, int(draw_w), int(draw_h))
            
            # Simple rendering per test
            if itype == "image":
                 painter.fillRect(item_rect, QColor(26, 58, 90, 150))
                 painter.setPen(QColor(85, 170, 255))
                 painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, "🖼 Immagine")
            elif itype == "video":
                 painter.fillRect(item_rect, QColor(58, 26, 26, 150))
                 painter.setPen(QColor(255, 136, 136))
                 painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, "▶ Video")
            elif itype == "text":
                 painter.fillRect(item_rect, QColor(42, 42, 26, 150))
                 painter.setPen(QColor(238, 221, 136))
                 painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, item.get("string", "T Testo"))
            elif itype in ("digitalClock", "dialClock"):
                 painter.fillRect(item_rect, QColor(26, 42, 58, 150))
                 painter.setPen(QColor(136, 204, 255))
                 painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, "🕐 Orologio")
                 
            if is_selected:
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
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header Canvas Label Overlay Like
        top_layout = QHBoxLayout()
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #888888; font-size: 10pt;")
        
        self.btn_screenshot = QPushButton("📷 Screenshot reale")
        self.btn_screenshot.setVisible(False) # Visibile solo se online
        
        top_layout.addWidget(self.lbl_info)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_screenshot)
        layout.addLayout(top_layout)
        
        # Canvas reale
        self.canvas = CanvasWidget()
        layout.addWidget(self.canvas)
        
    def update_screen_info(self, width, height, is_online):
        self.canvas.set_screen_size(width, height)
        self.lbl_info.setText(f"Schermo: {width}x{height} px")
        self.btn_screenshot.setVisible(is_online)
        
    def clear_screen_info(self):
        self.lbl_info.setText("")
        self.btn_screenshot.setVisible(False)
        self.canvas.clear_screen()
        
    def update_layers(self, items, selected_idx=-1):
        self.canvas.set_layers(items, selected_idx)
