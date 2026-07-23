from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QSize, QRunnable, QThreadPool, QObject
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon, QAction, QFont, QCursor, QGuiApplication, QMovie, QImage
from PySide6.QtWidgets import (
    QListWidget, QScrollArea, QLabel, QPushButton, QMenu, QFrame, QHBoxLayout, QApplication, QWidget, QVBoxLayout, QSlider
)
import random
from pathlib import Path
import psutil
import os

VALID_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".gif"
}

# --- Module-level icon cache (created once, reused everywhere) ---
_PLUS_ICON_CACHE = None


class FileDropListWidget(QListWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAccessibleName("File Drop List")
        self.setToolTip("Drag and drop files here, or right-click items for more options.")
        self.current_theme = "light"
        self.update_style()

    def set_theme(self, theme_name):
        self.current_theme = theme_name
        self.update_style()
        if self.viewport():
            self.viewport().update()

    def update_style(self, dragging=False):
        if self.current_theme == "dark":
            if dragging:
                self.setStyleSheet("""
                    FileDropListWidget, QListWidget { background-color: #22222c; border: 2px dashed #89b4fa; color: #e1e1e6; outline: 0; }
                    FileDropListWidget::viewport, QListWidget::viewport { background-color: #22222c; color: #e1e1e6; }
                """)
            else:
                self.setStyleSheet("""
                    FileDropListWidget, QListWidget { background-color: #16161a; border: 1px solid #2e2e38; color: #e1e1e6; outline: 0; }
                    FileDropListWidget::viewport, QListWidget::viewport { background-color: #16161a; color: #e1e1e6; }
                    FileDropListWidget::item:selected, QListWidget::item:selected { background-color: #323242; color: #ffffff; }
                """)
        else:
            if dragging:
                self.setStyleSheet("""
                    FileDropListWidget, QListWidget { background-color: #e0e5f0; border: 2px dashed #4b556b; color: #1c2333; outline: 0; }
                    FileDropListWidget::viewport, QListWidget::viewport { background-color: #e0e5f0; color: #1c2333; }
                """)
            else:
                self.setStyleSheet("""
                    FileDropListWidget, QListWidget { background-color: #ffffff; border: 1px solid #b3bcd1; color: #1c2333; outline: 0; }
                    FileDropListWidget::viewport, QListWidget::viewport { background-color: #ffffff; color: #1c2333; }
                    FileDropListWidget::item:selected, QListWidget::item:selected { background-color: #cce0ff; color: #1c2333; }
                """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.update_style(dragging=True)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.update_style(dragging=False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.update_style(dragging=False)
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

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            pen_col = QColor(166, 173, 200) if getattr(self, "current_theme", "light") == "dark" else QColor(120, 120, 120)
            painter.setPen(pen_col)
            font = painter.font()
            font.setItalic(True)
            painter.setFont(font)
            painter.drawText(self.viewport().rect(), Qt.AlignCenter, "Drop files here")

class SplitImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slider_ratio = 0.5
        self.is_dragging = False
        self.setMouseTracking(True)
        self.setAccessibleName("Split Image Compare")
        self.setToolTip("Drag left or right to compare original and result images.")
        
        self.orig_pixmap = None
        self.res_pixmap = None
        self.active_movie = None
        self.show_split = False

    def set_images(self, orig, res, use_split):
        self.orig_pixmap = orig
        self.res_pixmap = res
        self.show_split = use_split
        self.active_movie = None
        self.setPixmap(QPixmap()) # clear super label
        self.update()

    def set_movie_override(self, movie):
        self.active_movie = movie
        self.orig_pixmap = None
        self.res_pixmap = None
        self.setMovie(movie)

    def mousePressEvent(self, event):
        if self.show_split and self.orig_pixmap and self.res_pixmap and event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.update_slider(event.pos().x())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.show_split and self.orig_pixmap and self.res_pixmap:
            split_x = int(self.width() * self.slider_ratio)
            if abs(event.pos().x() - split_x) < 20 or self.is_dragging:
                self.setCursor(Qt.SplitHCursor)
                if self.is_dragging:
                    self.update_slider(event.pos().x())
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def update_slider(self, x):
        self.slider_ratio = max(0.01, min(0.99, x / self.width()))
        self.update()

    def paintEvent(self, event):
        if self.active_movie:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        w, h = self.width(), self.height()
        
        if self.show_split and self.orig_pixmap and self.res_pixmap:
            split_x = int(w * self.slider_ratio)
            painter.drawPixmap(0, 0, split_x, h, self.orig_pixmap, 0, 0, split_x, h)
            painter.drawPixmap(split_x, 0, w - split_x, h, self.res_pixmap, split_x, 0, w - split_x, h)
            
            painter.setPen(QPen(QColor(255, 153, 51), 2))
            painter.drawLine(split_x, 0, split_x, h)
            painter.setBrush(QColor(255, 153, 51))
            painter.drawEllipse(QPoint(split_x, h // 2), 6, 6)
        elif self.res_pixmap and not self.show_split:
            painter.drawPixmap(0, 0, self.res_pixmap)
        elif self.orig_pixmap:
            painter.drawPixmap(0, 0, self.orig_pixmap)
        else:
            super().paintEvent(event)

class ZoomableImageWidget(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("border: none; background: transparent;")
        if self.viewport():
            self.viewport().setStyleSheet("background: transparent;")
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        
        self.image_label = SplitImageLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        self.setWidget(self.image_label)
        
        self.original_image = None
        self.original_movie = None 
        self._original_movie_size = QSize()
        
        self.result_image = None
        self.result_movie = None   
        self._result_movie_size = QSize()
        
        self.scale_factor = 1.0
        self.auto_fit = True
        
        self._scale_timer = QTimer(self)
        self._scale_timer.setSingleShot(True)
        self._scale_timer.setInterval(50)
        self._scale_timer.timeout.connect(self._do_update_display)

        self.btn_toggle = QPushButton("Split View", self)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(True)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setAccessibleName("Toggle Split View")
        self.btn_toggle.setToolTip("Toggle split view mode (compare before/after)")
        self.btn_toggle.clicked.connect(self.update_display)
        self.btn_toggle.hide()
        self.btn_toggle.setStyleSheet("""
            QPushButton { background-color: rgba(255, 255, 255, 0.9); border: 1px solid #999; border-radius: 4px; padding: 6px 10px; color: #333; font-weight: bold; }
            QPushButton:checked { background-color: #ff9933; color: white; border: 1px solid #d67a18; }
        """)
        self.setFocusPolicy(Qt.StrongFocus)

        self.zoom_slider = QSlider(Qt.Horizontal, self)
        self.zoom_slider.setRange(10, 1000) # 0.1x to 10.0x
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.setAccessibleName("Zoom Level")
        self.zoom_slider.setToolTip("Zoom image (Ctrl + Mouse Wheel)")
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider)
        self.zoom_slider.setStyleSheet("""
            QSlider { background: rgba(255, 255, 255, 0.7); border-radius: 4px; padding: 2px; }
            QSlider::groove:horizontal { border: 1px solid #999; height: 6px; background: #eee; border-radius: 3px; }
            QSlider::handle:horizontal { background: #ff9933; border: 1px solid #d67a18; width: 14px; margin: -4px 0; border-radius: 7px; }
        """)
        self.zoom_slider.hide()

        # Debounce timer for resize events to avoid flooding the thread pool
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(150)
        self._resize_timer.timeout.connect(self._do_fit_and_update)


    def set_images(self, original_path, result_path):
        self.original_image = None
        self.original_movie = None
        self._original_movie_size = QSize()
        self.result_image = None
        self.result_movie = None
        self._result_movie_size = QSize()
        
        if original_path:
            p = Path(original_path)
            if p.exists():
                if p.suffix.lower() == ".gif":
                    self.original_movie = QMovie(str(p))
                    self.original_movie.start()
                    self.original_movie.jumpToFrame(0)
                    self._original_movie_size = self.original_movie.currentImage().size()
                else:
                    self.original_image = QImage(str(p))

        if result_path:
            p = Path(result_path)
            if p.exists():
                if p.suffix.lower() == ".gif":
                    self.result_movie = QMovie(str(p))
                    self.result_movie.start()
                    self.result_movie.jumpToFrame(0)
                    self._result_movie_size = self.result_movie.currentImage().size()
                else:
                    self.result_image = QImage(str(p))
        
        self.fit_to_view()
        
        has_orig = bool(self.original_image or self.original_movie)
        has_res = bool(self.result_image or self.result_movie)
        self.btn_toggle.setVisible(has_orig and has_res and not (self.original_movie or self.result_movie))
        
        if has_orig or has_res:
            self.zoom_slider.show()
        else:
            self.zoom_slider.hide()
            
        self.update_display()

    def set_image_pixmaps(self, original_pixmap, result_pixmap, preserve_zoom=False):
        self.original_image = None
        self.original_movie = None
        self._original_movie_size = QSize()
        self.result_image = None
        self.result_movie = None
        self._result_movie_size = QSize()
        
        if original_pixmap and not original_pixmap.isNull():
            self.original_image = original_pixmap.toImage().copy()
        if result_pixmap and not result_pixmap.isNull():
            self.result_image = result_pixmap.toImage().copy()
            
        if not preserve_zoom:
            self.fit_to_view()
            
        has_orig = bool(self.original_image)
        has_res = bool(self.result_image)
        self.btn_toggle.setVisible(has_orig and has_res)
        
        if has_orig or has_res:
            self.zoom_slider.show()
        else:
            self.zoom_slider.hide()
            
        self.update_display()

    def set_result_pixmap(self, pixmap, preserve_zoom=True):
        if pixmap and not pixmap.isNull():
            self.result_image = pixmap.toImage().copy()
        else:
            self.result_image = None
            
        if not preserve_zoom:
            self.fit_to_view()
            
        has_orig = bool(self.original_image or self.original_movie)
        has_res = bool(self.result_image or self.result_movie)
        self.btn_toggle.setVisible(has_orig and has_res and not (self.original_movie or self.result_movie))
        
        if has_orig or has_res:
            self.zoom_slider.show()
        else:
            self.zoom_slider.hide()
            
        self.update_display()

    def fit_to_view(self):
        target_size = QSize(0,0)
        if self.original_image: target_size = self.original_image.size()
        elif self.original_movie: target_size = self._original_movie_size
        elif self.result_image: target_size = self.result_image.size()
        elif self.result_movie: target_size = self._result_movie_size
        
        if target_size.isValid() and not target_size.isEmpty():
            w_ratio = self.width() / target_size.width()
            h_ratio = self.height() / target_size.height()
            fit_scale = min(w_ratio, h_ratio)
            self.scale_factor = min(fit_scale, 1.0) * 0.95 
        else:
            self.scale_factor = 1.0
            
        self.auto_fit = True
        
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(self.scale_factor * 100))
        self.zoom_slider.blockSignals(False)

    def update_display(self):
        # Debounce the update call to prevent UI thread lockup on slider drag
        self._scale_timer.start()

    def _do_update_display(self):
        try:
            import shiboken6
            if not shiboken6.isValid(self) or not shiboken6.isValid(self.image_label):
                return
        except:
            pass
            
        if self.original_movie or self.result_movie:
            movie = self.result_movie if self.result_movie else self.original_movie
            if not self.btn_toggle.isChecked() and self.original_movie:
                movie = self.original_movie
                
            base_size = self._result_movie_size if movie == self.result_movie else self._original_movie_size
            if base_size.isValid() and not base_size.isEmpty():
                new_size = QSize(int(base_size.width() * self.scale_factor), int(base_size.height() * self.scale_factor))
                if movie.scaledSize() != new_size:
                    movie.setScaledSize(new_size)
                self.image_label.setFixedSize(new_size)
            self.image_label.set_movie_override(movie)
        else:
            base_size = QSize(0,0)
            if self.original_image: base_size = self.original_image.size()
            elif self.result_image: base_size = self.result_image.size()
            
            if base_size.isValid() and not base_size.isEmpty():
                new_size = QSize(int(base_size.width() * self.scale_factor), int(base_size.height() * self.scale_factor))
                
                # Perform scaling synchronously
                orig_scaled = QImage()
                res_scaled = QImage()
                if new_size.width() > 0 and new_size.height() > 0:
                    if self.original_image and not self.original_image.isNull():
                        orig_scaled = self.original_image.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    if self.result_image and not self.result_image.isNull():
                        res_scaled = self.result_image.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                self.on_images_scaled(orig_scaled, res_scaled)
            else:
                self.image_label.set_images(None, None, False)

    def on_images_scaled(self, orig_scaled, res_scaled):
        # Update label on main thread
        o_pix = QPixmap.fromImage(orig_scaled) if not orig_scaled.isNull() else None
        r_pix = QPixmap.fromImage(res_scaled) if not res_scaled.isNull() else None
        
        if o_pix or r_pix:
            target = o_pix if o_pix else r_pix
            self.image_label.setFixedSize(target.size())
            
        use_split = self.btn_toggle.isChecked() and o_pix and r_pix
        if not self.btn_toggle.isChecked() and o_pix:
            r_pix = None # only show original if split is disabled
        self.image_label.set_images(o_pix, r_pix, use_split)

    def _on_zoom_slider(self, val):
        self.auto_fit = False
        self.scale_factor = val / 100.0
        self.update_display()

    def set_zoom_level(self, zoom_float):
        self.scale_factor = zoom_float
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(zoom_float * 100))
        self.zoom_slider.blockSignals(False)
        self.update_display()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.auto_fit = False
            delta = event.angleDelta().y()
            if delta > 0: self.scale_factor *= 1.25
            else: self.scale_factor *= 0.8
            self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(int(self.scale_factor * 100))
            self.zoom_slider.blockSignals(False)
            self.update_display()
            event.accept()
        else:
            super().wheelEvent(event)

    def _do_fit_and_update(self):
        """Deferred resize handler — called once after resize settles."""
        if self.auto_fit:
            self.fit_to_view()
        self.update_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        bw, bh = self.btn_toggle.width(), self.btn_toggle.height()
        self.btn_toggle.move(self.width() - bw - 20, 20)
        self.zoom_slider.move(self.width() - self.zoom_slider.width() - 20, self.height() - self.zoom_slider.height() - 20)
        # Debounce: defer fit-to-view until resize stops
        self._resize_timer.start()


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
        self.current_theme = "light"
        self._apply_style()
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10,3,10,4)
        self._layout.setSpacing(18)
        
        self.labels = []
        self._running_index = 0
        self.override_message = None
        
        # Optimization: Cache process object
        try:
            self.process = psutil.Process(os.getpid())
        except:
            self.process = None

        # 8 Small Boxes (Updated from 6)
        font = QFont("Consolas", 9)
        for _ in range(8):
            l = QLabel("0.000000α")
            l.setObjectName("NumberBox")
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
        self.timer.start(120)
        self._update_text()

    def set_message(self, text):
        self.override_message = text
        self._update_status_box()
        # Speed up animation when processing, slow down when idle
        if text:
            self.timer.setInterval(60)
        else:
            self.timer.setInterval(120)

    SPINNER_CHARS = ["|", "/", "-", "\\"]

    def _update_status_box(self):
        if self.override_message:
            spin_icon = self.SPINNER_CHARS[(self._running_index // 4) % len(self.SPINNER_CHARS)]
            self.status_label.setText(f"{spin_icon} {self.override_message}")
            self.status_label.setStyleSheet("background-color: #a5f3fc; border: 1px solid #22d3ee; color: #0e7490; border-radius: 4px; padding-left: 8px;") 
        else:
            # Idle / RAM (Process Only)
            try:
                # Optimized: Reuse cached process object
                if self.process:
                    mem_bytes = self.process.memory_info().rss
                    ram_mb = mem_bytes / (1024 * 1024)
                    self.status_label.setText(f"RAM USAGE: {ram_mb:.1f} MB")
                else:
                    self.status_label.setText("SYSTEM READY")
            except:
                self.status_label.setText("SYSTEM READY")
            self.status_label.setStyleSheet("")

    def _update_text(self):
        if not self.isVisible():
            return
        idx = self._running_index % len(self.labels)
        self._running_index += 1
        val = random.choice(self.RUNNING_VALUES)
        self.labels[idx].setText(f"{val}  •")
        
        if self.override_message:
            spin_icon = self.SPINNER_CHARS[(self._running_index // 4) % len(self.SPINNER_CHARS)]
            self.status_label.setText(f"{spin_icon} {self.override_message}")
        elif self._running_index % 30 == 0:
            self._update_status_box()

    def set_theme(self, theme_name):
        self.current_theme = theme_name
        self._apply_style()

    def _apply_style(self):
        if self.current_theme == "dark":
            self.setStyleSheet("""
                #PixelBar { 
                    background-color: #181818; 
                    border: none;
                    border-radius: 0px;
                }
                QLabel { color: #a0a0a0; font-family: 'Consolas'; font-size: 9pt; background: transparent; }
                QLabel#NumberBox, QLabel#StatusBox { 
                    background-color: #242424; 
                    border: 1px solid #3d3d3d; 
                    border-radius: 4px;
                    color: #ffffff;
                    padding-left: 6px;
                    padding-right: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                #PixelBar { 
                    background-color: #dde4f5; 
                    border: none;
                    border-radius: 0px;
                }
                QLabel { color: #4b556b; font-family: 'Consolas'; font-size: 9pt; background: transparent; }
                QLabel#NumberBox, QLabel#StatusBox { 
                    background-color: #cbd5e1; 
                    border: 1px solid #94a3b8; 
                    border-radius: 4px;
                    color: #334155;
                    padding-left: 6px;
                    padding-right: 6px;
                }
            """)


def create_plus_icon():
    global _PLUS_ICON_CACHE
    if _PLUS_ICON_CACHE is not None:
        return _PLUS_ICON_CACHE
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
    _PLUS_ICON_CACHE = QIcon(pix)
    return _PLUS_ICON_CACHE

