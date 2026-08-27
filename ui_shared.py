from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QSize, QObject, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon, QAction, QFont, QMovie, QImage
from PySide6.QtWidgets import (
    QListWidget, QScrollArea, QLabel, QPushButton, QMenu, QFrame, QHBoxLayout, QApplication, QWidget, QVBoxLayout, QSlider, QDialog, QProgressBar, QListView, QGraphicsOpacityEffect
)

def setup_combobox(combo, is_dark=False):
    if combo:
        combo.setMaxVisibleItems(15)
        border_col = "#3d3d3d" if is_dark else "#b3bcd1"
        bg_col = "#1c1c1c" if is_dark else "#ffffff"
        text_col = "#ffffff" if is_dark else "#1c2333"
        hover_bg = "#333333" if is_dark else "#d4e3fc"
        
        combo.setStyleSheet(f"""
            QComboBox QAbstractItemView {{
                border: 1px solid {border_col} !important;
                background-color: {bg_col};
                color: {text_col};
                outline: 0px;
                padding: 2px;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 22px;
                padding: 4px 8px;
                border-radius: 3px;
                color: {text_col};
                background-color: transparent;
            }}
            QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {{
                background-color: {hover_bg};
                color: {text_col};
            }}
        """)
    return combo
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
        self.current_theme = "light"
        self.setAccessibleName("File Drop List")
        self.setToolTip("Drag and drop files here. Right-click an item for more options.")
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
        self.setAccessibleName("Split View Comparison")
        
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

        self.setAccessibleName("Zoomable Image Viewer")
        self.setToolTip("Ctrl + Mouse Wheel to zoom")

        self.btn_toggle = QPushButton("Split View", self)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(True)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setAccessibleName("Toggle Split View")
        self.btn_toggle.setToolTip("Switch between split view and full image view")
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
        self.zoom_slider.setToolTip("Adjust image zoom level (Ctrl + Mouse Wheel)")
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider)
        self.zoom_slider.hide()

        # Debounce timer for resize events to avoid flooding the thread pool
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(150)
        self._resize_timer.timeout.connect(self._do_fit_and_update)

    def set_theme(self, theme="light"):
        is_dark = (theme == "dark")
        btn_bg = "rgba(28, 28, 34, 0.9)" if is_dark else "rgba(255, 255, 255, 0.9)"
        btn_text = "#e1e1e6" if is_dark else "#333"
        btn_border = "#3e3e4e" if is_dark else "#999"
        
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{ background-color: {btn_bg}; border: 1px solid {btn_border}; border-radius: 4px; padding: 6px 10px; color: {btn_text}; font-weight: bold; }}
            QPushButton:checked {{ background-color: #ff9933; color: white; border: 1px solid #d67a18; }}
        """)
        self.zoom_slider.setStyleSheet(f"""
            QSlider {{ background: {"rgba(28, 28, 34, 0.7)" if is_dark else "rgba(255, 255, 255, 0.7)"}; border-radius: 4px; padding: 2px; }}
            QSlider::groove:horizontal {{ border: 1px solid {btn_border}; height: 6px; background: {"#242430" if is_dark else "#eee"}; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: #ff9933; border: 1px solid #d67a18; width: 14px; margin: -4px 0; border-radius: 7px; }}
        """)


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
            if not self.btn_toggle.isChecked() and self.result_movie:
                movie = self.result_movie
                
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
        if not self.btn_toggle.isChecked() and r_pix:
            o_pix = None # only show result if split is disabled
        self.image_label.set_images(o_pix, r_pix, use_split)

    def _zoom_relative(self, new_scale, cursor_pos=None):
        old_scale = self.scale_factor
        if old_scale <= 0 or new_scale <= 0:
            return
            
        self.auto_fit = False
        self.scale_factor = max(0.1, min(new_scale, 10.0))
        
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()
        
        if cursor_pos is None:
            cursor_pos = self.viewport().rect().center()
            
        old_point = cursor_pos + QPoint(h_bar.value(), v_bar.value())
        scale_ratio = self.scale_factor / old_scale
        new_point = old_point * scale_ratio
        
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(self.scale_factor * 100))
        self.zoom_slider.blockSignals(False)
        
        self.update_display()
        
        new_h = int(new_point.x() - cursor_pos.x())
        new_v = int(new_point.y() - cursor_pos.y())
        h_bar.setValue(new_h)
        v_bar.setValue(new_v)

    def _on_zoom_slider(self, val):
        self._zoom_relative(val / 100.0)

    def set_zoom_level(self, zoom_float):
        self._zoom_relative(zoom_float)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if abs(self.scale_factor - 1.0) < 0.05 and not self.auto_fit:
                self.fit_to_view()
            else:
                self.set_zoom_level(1.0)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta != 0:
            factor = 1.25 if delta > 0 else 0.8
            self._zoom_relative(self.scale_factor * factor, event.position().toPoint())
            event.accept()

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
        if text:
            # Only use the first line to prevent the divergence meter from doubling in height
            text = text.split("\n")[0]
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
    from PySide6.QtWidgets import QApplication, QStyle
    app = QApplication.instance()
    if app:
        _PLUS_ICON_CACHE = app.style().standardIcon(QStyle.SP_FileDialogNewFolder)
        return _PLUS_ICON_CACHE
    return QIcon()


class ModernDialog(QDialog):
    def __init__(self, parent=None, title="Notice", message="", is_confirm=False, theme="light"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        self.container = QFrame(self)
        self.container.setObjectName("DialogContainer")
        
        is_dark = (theme == "dark")
        bg_color = "#16161a" if is_dark else "#f5f7fb"
        text_color = "#e1e1e6" if is_dark else "#1c2333"
        border_color = "#2e2e38" if is_dark else "#b3bcd1"
        header_bg = "#121216" if is_dark else "#dde4f5"
        
        self.container.setStyleSheet(f"""
            #DialogContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{ color: {text_color}; font-family: 'Segoe UI', sans-serif; }}
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 12)
        container_layout.setSpacing(10)
        
        # Header bar
        header = QFrame(self.container)
        header.setStyleSheet(f"background-color: {header_bg}; border-top-left-radius: 7px; border-top-right-radius: 7px; border-bottom: 1px solid {border_color};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 8, 6)
        
        title_lbl = QLabel(title, header)
        title_lbl.setStyleSheet(f"font-weight: bold; font-size: 10pt; color: {text_color}; border: none;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        btn_close = QPushButton("✕", header)
        btn_close.setFixedSize(22, 22)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#2a2a36" if is_dark else "#cbd5e1"};
                border: 1px solid {"#3f3f4e" if is_dark else "#94a3b8"};
                color: {"#a0a0b0" if is_dark else "#475569"};
                font-weight: bold;
                border-radius: 11px;
                font-size: 8.5pt;
            }}
            QPushButton:hover {{
                background-color: #ef4444;
                border: 1px solid #dc2626;
                color: #ffffff;
            }}
        """)
        btn_close.clicked.connect(self.reject)
        header_layout.addWidget(btn_close)
        container_layout.addWidget(header)
        
        # Content Body
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(16, 8, 16, 8)
        
        lbl_msg = QLabel(message, self.container)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("font-size: 9.5pt; border: none;")
        body_layout.addWidget(lbl_msg, 1)
        container_layout.addLayout(body_layout)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(16, 0, 16, 4)
        btn_layout.addStretch()
        
        btn_style = f"""
            QPushButton {{
                background-color: {"#282832" if is_dark else "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #d8dfee)"};
                border: 1px solid {"#383846" if is_dark else "#9ca7c2"};
                border-radius: 5px;
                padding: 5px 14px;
                font-weight: bold;
                color: {"#e1e1e6" if is_dark else "#1c2333"};
            }}
            QPushButton:hover {{ background-color: {"#383846" if is_dark else "#e6ecf7"}; }}
        """

        if is_confirm:
            btn_cancel = QPushButton("Cancel", self.container)
            btn_cancel.setCursor(Qt.PointingHandCursor)
            btn_cancel.setFixedWidth(80)
            btn_cancel.setStyleSheet(btn_style)
            btn_cancel.clicked.connect(self.reject)
            btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("OK", self.container)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setFixedWidth(80)
        btn_ok.setStyleSheet(btn_style)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        container_layout.addLayout(btn_layout)
        
        main_layout.addWidget(self.container)
        self.setMinimumWidth(372)
        
        # Apply drop shadow
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 100 if is_dark else 60))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_anim_started'):
            self._anim_started = True
            
            # Opacity animation on the QDialog window
            self.setWindowOpacity(0.0)
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade_anim.setDuration(200)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
            
            # Pop-out slide animation on the dialog container
            self._pos_anim = QPropertyAnimation(self.container, b"pos", self)
            self._pos_anim.setDuration(200)
            target_pos = self.container.pos()
            start_pos = QPoint(target_pos.x(), target_pos.y() + 16)
            self.container.move(start_pos)
            self._pos_anim.setStartValue(start_pos)
            self._pos_anim.setEndValue(target_pos)
            self._pos_anim.setEasingCurve(QEasingCurve.OutBack)
            
            self._fade_anim.start()
            self._pos_anim.start()

    def _do_accept(self):
        QDialog.accept(self)

    def _do_reject(self):
        QDialog.reject(self)

    def accept(self):
        self._fade_out_and_close(self._do_accept)

    def reject(self):
        self._fade_out_and_close(self._do_reject)

    def _fade_out_and_close(self, callback):
        if getattr(self, '_is_closing', False):
            callback()
            return
        self._is_closing = True
        
        self._fade_out = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_out.setDuration(120)
        self._fade_out.setStartValue(self.windowOpacity())
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.InCubic)
        self._fade_out.finished.connect(callback)
        self._fade_out.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    @staticmethod
    def _get_theme(parent):
        if parent:
            if hasattr(parent, 'current_theme'):
                return parent.current_theme
            if hasattr(parent, 'is_dark_theme'):
                return "dark" if parent.is_dark_theme else "light"
        return "light"

    @staticmethod
    def show_info(parent, title, message):
        dlg = ModernDialog(parent, title=title, message=message, is_confirm=False, theme=ModernDialog._get_theme(parent))
        dlg.exec()

    @staticmethod
    def show_warning(parent, title, message):
        dlg = ModernDialog(parent, title=title, message=message, is_confirm=False, theme=ModernDialog._get_theme(parent))
        dlg.exec()

    @staticmethod
    def show_critical(parent, title, message):
        dlg = ModernDialog(parent, title=title, message=message, is_confirm=False, theme=ModernDialog._get_theme(parent))
        dlg.exec()

    @staticmethod
    def confirm(parent, title, message):
        dlg = ModernDialog(parent, title=title, message=message, is_confirm=True, theme=ModernDialog._get_theme(parent))
        return dlg.exec() == QDialog.Accepted


class ModernProgressDialog(QDialog):
    canceled = Signal()

    def __init__(self, title="Processing...", cancel_text="Cancel", minimum=0, maximum=100, parent=None, theme="light"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._was_canceled = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        self.container = QFrame(self)
        self.container.setObjectName("ProgressContainer")

        is_dark = (theme == "dark")
        bg_color = "#16161a" if is_dark else "#f5f7fb"
        text_color = "#e1e1e6" if is_dark else "#1c2333"
        border_color = "#2e2e38" if is_dark else "#b3bcd1"
        header_bg = "#121216" if is_dark else "#dde4f5"

        self.container.setStyleSheet(f"""
            #ProgressContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{ color: {text_color}; font-family: 'Segoe UI', sans-serif; }}
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 12)
        container_layout.setSpacing(10)

        # Header bar
        header = QFrame(self.container)
        header.setStyleSheet(f"background-color: {header_bg}; border-top-left-radius: 7px; border-top-right-radius: 7px; border-bottom: 1px solid {border_color};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 8, 6)

        title_lbl = QLabel(title, header)
        title_lbl.setStyleSheet(f"font-weight: bold; font-size: 10pt; color: {text_color}; border: none;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        container_layout.addWidget(header)

        # Status Label + Progress Bar
        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(16, 6, 16, 6)
        body_layout.setSpacing(8)

        self.lbl_status = QLabel("Processing...", self.container)
        self.lbl_status.setStyleSheet("font-size: 9.5pt; border: none;")
        body_layout.addWidget(self.lbl_status)

        self.pbar = QProgressBar(self.container)
        self.pbar.setRange(minimum, maximum)
        self.pbar.setValue(minimum)
        self.pbar.setFixedHeight(18)
        self.pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {"#242430" if is_dark else "#e2e8f0"};
                border: 1px solid {border_color};
                border-radius: 4px;
                text-align: center;
                color: {text_color};
                font-size: 8.5pt;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: #3b82f6;
                border-radius: 3px;
            }}
        """)
        body_layout.addWidget(self.pbar)
        container_layout.addLayout(body_layout)

        # Cancel Button
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(16, 0, 16, 4)
        btn_layout.addStretch()

        if cancel_text:
            self.btn_cancel = QPushButton(cancel_text, self.container)
            self.btn_cancel.setCursor(Qt.PointingHandCursor)
            self.btn_cancel.setFixedWidth(80)
            self.btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#282832" if is_dark else "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #d8dfee)"};
                    border: 1px solid {"#383846" if is_dark else "#9ca7c2"};
                    border-radius: 5px;
                    padding: 5px 14px;
                    font-weight: bold;
                    color: {"#e1e1e6" if is_dark else "#1c2333"};
                }}
                QPushButton:hover {{ background-color: {"#383846" if is_dark else "#e6ecf7"}; }}
            """)
            self.btn_cancel.clicked.connect(self._on_cancel)
            btn_layout.addWidget(self.btn_cancel)

        container_layout.addLayout(btn_layout)
        main_layout.addWidget(self.container)
        self.setMinimumWidth(392)
        
        # Apply drop shadow
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 100 if is_dark else 60))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_anim_started'):
            self._anim_started = True
            
            # Opacity animation on the QDialog window
            self.setWindowOpacity(0.0)
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade_anim.setDuration(200)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
            
            # Pop-out slide animation on the dialog container
            self._pos_anim = QPropertyAnimation(self.container, b"pos", self)
            self._pos_anim.setDuration(200)
            target_pos = self.container.pos()
            start_pos = QPoint(target_pos.x(), target_pos.y() + 16)
            self.container.move(start_pos)
            self._pos_anim.setStartValue(start_pos)
            self._pos_anim.setEndValue(target_pos)
            self._pos_anim.setEasingCurve(QEasingCurve.OutBack)
            
            self._fade_anim.start()
            self._pos_anim.start()

    def _do_accept(self):
        QDialog.accept(self)

    def _do_reject(self):
        QDialog.reject(self)

    def accept(self):
        self._fade_out_and_close(self._do_accept)

    def reject(self):
        self._fade_out_and_close(self._do_reject)

    def _fade_out_and_close(self, callback):
        if getattr(self, '_is_closing', False):
            callback()
            return
        self._is_closing = True
        
        self._fade_out = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_out.setDuration(120)
        self._fade_out.setStartValue(self.windowOpacity())
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.InCubic)
        self._fade_out.finished.connect(callback)
        self._fade_out.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _on_cancel(self):
        self._was_canceled = True
        self.canceled.emit()
        self.reject()

    def setValue(self, val):
        self.pbar.setValue(val)

    def setLabelText(self, text):
        self.lbl_status.setText(text)

    def setMaximum(self, val):
        self.pbar.setMaximum(val)

    def wasCanceled(self):
        return self._was_canceled



