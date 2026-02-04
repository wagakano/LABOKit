from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon, QAction, QFont, QCursor, QGuiApplication, QMovie
from PySide6.QtWidgets import (
    QListWidget, QScrollArea, QLabel, QPushButton, QMenu, QFrame, QHBoxLayout, QApplication
)
import random
from pathlib import Path
import psutil
import os

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
        self.original_movie = None

        self.result_pixmap = None
        self.result_movie = None

        self.current_target_pixmap = None
        self.current_target_movie = None

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
        
        self.setFocusPolicy(Qt.StrongFocus)

    def set_images(self, original_path, result_path):
        self.original_pixmap = None
        self.original_movie = None
        self.result_pixmap = None
        self.result_movie = None

        if original_path:
            p = Path(original_path)
            if p.exists():
                if p.suffix.lower() == ".gif":
                    self.original_movie = QMovie(str(p))
                    self.original_movie.start()
                else:
                    self.original_pixmap = QPixmap(str(p))

        if result_path:
            p = Path(result_path)
            if p.exists():
                if p.suffix.lower() == ".gif":
                    self.result_movie = QMovie(str(p))
                    self.result_movie.start()
                else:
                    self.result_pixmap = QPixmap(str(p))
        
        self.fit_to_view()
        self.btn_toggle.setChecked(False)

        has_orig = bool(self.original_pixmap or self.original_movie)
        has_res = bool(self.result_pixmap or self.result_movie)
        self.btn_toggle.setVisible(has_orig and has_res)

        self.update_display()

    def set_image_pixmaps(self, original_pixmap, result_pixmap, preserve_zoom=False):
        self.original_pixmap = original_pixmap
        self.original_movie = None

        self.result_pixmap = result_pixmap
        self.result_movie = None
        
        if not preserve_zoom:
            self.fit_to_view()
        
        self.btn_toggle.setChecked(False)
        self.btn_toggle.setVisible(bool(self.original_pixmap and self.result_pixmap))
        self.update_display()

    # --- NEW METHOD ---
    def set_result_pixmap(self, result_pixmap):
        """Updates ONLY the result pixmap without clearing original (pixmap or movie)."""
        self.result_pixmap = result_pixmap
        self.result_movie = None

        # Ensure toggle is visible if we have original
        has_orig = bool(self.original_pixmap or self.original_movie)
        self.btn_toggle.setVisible(has_orig and bool(self.result_pixmap))

        # If currently showing result (or trying to), refresh
        if not self.btn_toggle.isChecked():
            self.update_display()
    # ------------------

    def fit_to_view(self):
        target_size = QSize(0,0)

        if self.original_pixmap: target_size = self.original_pixmap.size()
        elif self.original_movie: target_size = self.original_movie.currentImage().size()
        elif self.result_pixmap: target_size = self.result_pixmap.size()
        elif self.result_movie: target_size = self.result_movie.currentImage().size()

        if target_size.isValid():
            w_ratio = self.width() / target_size.width()
            h_ratio = self.height() / target_size.height()
            fit_scale = min(w_ratio, h_ratio)
            self.scale_factor = min(fit_scale, 1.0) * 0.95 
        else:
            self.scale_factor = 1.0

    def update_display(self):
        self.current_target_pixmap = None
        self.current_target_movie = None

        if self.btn_toggle.isChecked():
            if self.original_movie: self.current_target_movie = self.original_movie
            else: self.current_target_pixmap = self.original_pixmap
        else:
            if self.result_movie: self.current_target_movie = self.result_movie
            elif self.result_pixmap: self.current_target_pixmap = self.result_pixmap
            elif self.original_movie: self.current_target_movie = self.original_movie
            else: self.current_target_pixmap = self.original_pixmap
        
        self._refresh_view()

    def _refresh_view(self):
        if self.current_target_movie:
            movie = self.current_target_movie
            if not movie.isValid():
                self.image_label.setText("Invalid Movie")
                return

            if movie.currentPixmap().isNull():
                movie.jumpToFrame(0)

            orig_size = movie.currentPixmap().size()
            if orig_size.isValid():
                new_size = orig_size * self.scale_factor
                movie.setScaledSize(new_size)

            self.image_label.setMovie(movie)
            if movie.state() != QMovie.Running:
                movie.start()

        elif self.current_target_pixmap and not self.current_target_pixmap.isNull():
            new_size = self.current_target_pixmap.size() * self.scale_factor
            scaled = self.current_target_pixmap.scaled(
                new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            self.image_label.adjustSize()
        else:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("No Image")
        
    def set_zoom_level(self, zoom_float):
        self.scale_factor = zoom_float
        self._refresh_view()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0: self.scale_factor *= 1.25
            else: self.scale_factor *= 0.8
            self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
            self._refresh_view()
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        bw, bh = self.btn_toggle.width(), self.btn_toggle.height()
        self.btn_toggle.move(self.width() - bw - 20, 20)

class DivergenceMeter(QFrame):
    RUNNING_VALUES = [
        "0.000000α", "0.134891α", "0.210317α", "0.295582α",
        "0.334581α", "0.337187α", "0.409420α", "0.456903α",
        "0.571024α", "0.571046α", "0.615483α", "0.934587α",
        "1.048596β", "1.130205β", "1.130426β", "3.019430δ",
        "3.372329δ", "4.456441ε"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PixelBar")
        self.setStyleSheet("""
            #PixelBar { background-color: #dde4f5; border-radius: 6px; border: 1px solid #b3bcd1; }
            QLabel { color: #4b556b; font-family: 'Consolas'; font-size: 9pt; background: transparent; }
            QLabel#StatusBox { 
                background-color: #cbd5e1; 
                border: 1px solid #94a3b8; 
                border-radius: 4px;
                color: #334155;
                padding-left: 8px;
            }
        """)
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10,3,10,4)
        self._layout.setSpacing(18)
        
        self.labels = []
        self._running_index = 0
        self.override_message = None
        
        # 8 Small Boxes (Updated from 6)
        font = QFont("Consolas", 9)
        for _ in range(8):
            l = QLabel("0.000000α")
            l.setFont(font)
            self.labels.append(l)
            self._layout.addWidget(l)
            
        self._layout.addStretch()
        
        # 1 Long Status Box
        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setObjectName("StatusBox")
        self.status_label.setFont(font)
        self.status_label.setFixedWidth(300) 
        self.status_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._layout.addWidget(self.status_label)
            
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_text)
        self.timer.start(100) 
        self._update_text() 

    def set_message(self, text):
        self.override_message = text
        self._update_status_box()

    def _update_status_box(self):
        if self.override_message:
            self.status_label.setText(f"➤ {self.override_message}")
            self.status_label.setStyleSheet("background-color: #a5f3fc; border: 1px solid #22d3ee; color: #0e7490;") 
        else:
            # Idle / RAM (Process Only)
            try:
                process = psutil.Process(os.getpid())
                mem_bytes = process.memory_info().rss
                ram_mb = mem_bytes / (1024 * 1024)
                self.status_label.setText(f"App Memory Usage: {ram_mb:.1f} MB")
            except:
                self.status_label.setText("SYSTEM READY")
            self.status_label.setStyleSheet("")

    def _update_text(self):
        idx = self._running_index % len(self.labels)
        self._running_index += 1
        val = random.choice(self.RUNNING_VALUES)
        self.labels[idx].setText(f"{val}  •")
        
        if not self.override_message and self._running_index % 10 == 0: 
            self._update_status_box()

def create_plus_icon():
    pix = QPixmap(16, 16)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#333333"))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawLine(8, 3, 8, 13)
    painter.drawLine(3, 8, 13, 8)
    painter.end()
    return QIcon(pix)
