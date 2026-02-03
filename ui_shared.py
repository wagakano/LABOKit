from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon, QAction
from PySide6.QtWidgets import (
    QListWidget, QScrollArea, QLabel, QPushButton, QMenu
)
from pathlib import Path

VALID_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".gif"
}

class FileDropListWidget(QListWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            files = []
            for u in event.mimeData().urls():
                if u.isLocalFile():
                    files.append(Path(u.toLocalFile()))
            if files:
                self.files_dropped.emit(files)
            event.accept()
        else:
            event.ignore()

class ZoomableImageWidget(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        self.setWidget(self.image_label)
        
        self.original_pixmap = None
        self.result_pixmap = None
        self.current_target_pixmap = None
        self.scale_factor = 1.0
        
        # Toggle Button (Top-Right)
        self.btn_toggle = QPushButton("Show Original", self)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.update_display)
        self.btn_toggle.hide()
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #999;
                border-radius: 4px;
                padding: 6px 10px;
                color: #333;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #ff9933; /* Orange accent */
                color: white;
                border: 1px solid #d67a18;
            }
        """)

    def set_images(self, original_path, result_path):
        self.original_pixmap = QPixmap(str(original_path)) if original_path and Path(original_path).exists() else None
        self.result_pixmap = QPixmap(str(result_path)) if result_path and Path(result_path).exists() else None
        
        # Auto-fit logic for initial load
        target = self.original_pixmap if self.original_pixmap else None
        if target and not target.isNull():
            # Calculate fit scale
            w_ratio = self.width() / target.width()
            h_ratio = self.height() / target.height()
            fit_scale = min(w_ratio, h_ratio)
            self.scale_factor = min(fit_scale, 1.0) * 0.95 # Slight margin, cap at 100%
        else:
            self.scale_factor = 1.0
        
        # Reset toggle
        self.btn_toggle.setChecked(False)
        self.btn_toggle.setVisible(bool(self.original_pixmap and self.result_pixmap))
        
        self.update_display()

    def update_display(self):
        # Determine which image to show
        if self.btn_toggle.isChecked() and self.original_pixmap:
            target = self.original_pixmap
        elif self.result_pixmap:
            target = self.result_pixmap
        else:
            target = self.original_pixmap
        
        self.current_target_pixmap = target
        self._refresh_view()

    def _refresh_view(self):
        if not self.current_target_pixmap or self.current_target_pixmap.isNull():
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("No Image")
            return
            
        # Scale
        new_size = self.current_target_pixmap.size() * self.scale_factor
        scaled = self.current_target_pixmap.scaled(
            new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
        self.image_label.adjustSize()
        
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_factor *= 1.25
            else:
                self.scale_factor *= 0.8
            
            # Clamp scale
            self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
            self._refresh_view()
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position button top-right with margin
        bw, bh = self.btn_toggle.width(), self.btn_toggle.height()
        self.btn_toggle.move(self.width() - bw - 20, 20)

def create_plus_icon():
    """Generates a simple flat '+' icon."""
    pix = QPixmap(16, 16)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Dark grey plus
    pen = QPen(QColor("#333333"))
    pen.setWidth(2)
    painter.setPen(pen)
    
    # Draw +
    # Vertical
    painter.drawLine(8, 3, 8, 13)
    # Horizontal
    painter.drawLine(3, 8, 13, 8)
    
    painter.end()
    return QIcon(pix)
