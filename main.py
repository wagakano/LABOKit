# --- PATCH TORCHVISION BASICSR ---
try:
    import torchvision.transforms.functional as F
    try:
        from torchvision.transforms import functional_tensor
    except ImportError:
        import sys
        from types import ModuleType

        ft_module = ModuleType('torchvision.transforms.functional_tensor')
        ft_module.rgb_to_grayscale = F.rgb_to_grayscale
        sys.modules['torchvision.transforms.functional_tensor'] = ft_module
except ImportError:
    pass

import sys
import os
import random
import subprocess
import importlib.util
import importlib.machinery
import shutil
import json
import urllib.request
import base64
import ssl
import requests
import svgwrite
import cv2
from pathlib import Path
from PIL import Image
from packaging import version
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- IMPORT ENGINE AI  ---
try:
    import torch
    import cv2
    import numpy as np
    from basicsr.archs.srvgg_arch import SRVGGNetCompact 
    from realesrgan import RealESRGANer
    HAS_TORCH = True
except ImportError as e:
    HAS_TORCH = False
    print(f"Warning: AI Engine modules missing: {e}")

# --- APP INFO ---
APP_VERSION = "2.0.0"
APP_UPDATE_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/latest_version.json"
PLUGIN_MANIFEST_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/plugins_manifest.json"


# --- PATH & ASSETS SETUP ---
# 1. Internal Path (Source files inside EXE/Build)
INTERNAL_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

# 2. Persistent Path (User AppData folder: %APPDATA%/LABOKit)
APP_DATA = Path(os.getenv('APPDATA')) / "LABOKit"
APP_DATA.mkdir(parents=True, exist_ok=True)

MODEL_DIR = APP_DATA / "models"
REALESRGAN_DIR = APP_DATA / "realesrgan"
PLUGIN_DIR = APP_DATA / "plugins"
FFMPEG_DIR = APP_DATA / "ffmpeg"

# Setup Environment Variables
os.environ["U2NET_HOME"] = str(MODEL_DIR)
REALESRGAN_EXE = REALESRGAN_DIR / "realesrgan-ncnn-vulkan.exe"

# Icon & Assets
ICON_PATH = INTERNAL_DIR / "labokit.ico"
remove = None

# --- IMPORTS ---
from PySide6.QtCore import Qt, QSize, QTimer, QUrl, QRectF, QThread, Signal
from PySide6.QtGui import QAction, QPixmap, QFont, QIcon, QDesktopServices, QPainterPath, QRegion, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QFileDialog,
    QMessageBox, QProgressDialog, QFrame, QComboBox, QTabWidget,
    QDialog, QPlainTextEdit, QSplashScreen, QMenuBar, QSizePolicy,
    QStackedWidget, QButtonGroup
)

IMAGE_FILTER = (
    "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.gif "
    "*.JPG *.JPEG *.PNG *.BMP *.TIF *.TIFF *.WEBP *.GIF)"
)

# --- IMPORT LIBRARY PYTORCH & REALESRGAN ---
try:
    import torch
    from torch import nn
    import numpy as np
    import cv2
    from realesrgan import RealESRGANer 
    HAS_TORCH = True
except ImportError as e:
    HAS_TORCH = False
    print(f"Warning: PyTorch/RealESRGAN modules not found: {e}")

# --- RUNNING TEXT DATA (World Line Meter) ---
RUNNING_VALUES = [
    "0.000000α", "0.134891α", "0.210317α", "0.295582α",
    "0.334581α", "0.337187α", "0.409420α", "0.456903α",
    "0.571024α", "0.571046α", "0.615483α", "0.934587α",
    "1.048596β", "1.130205β", "1.130426β", "3.019430δ",
    "3.372329δ", "4.456441ε"
]

# --- BG REMOVER PRESETS ---
BG_PRESETS = {
    "Standard": {"alpha_matting": False, "post_process_mask": False},
    "Medium": {"alpha_matting": False, "post_process_mask": True},
    "High": {"alpha_matting": True, "alpha_matting_foreground_threshold": 240, "alpha_matting_background_threshold": 10, "alpha_matting_erode_structure_size": 10, "alpha_matting_base_size": 1000, "post_process_mask": True},
}
DEFAULT_PRESET_NAME = "Standard"

# --- SMART DEPLOYMENT (AUTO-UPDATE ASSETS) ---
def sync_folder(src_dir, dst_dir):
    if not src_dir.exists(): return

    dst_dir.mkdir(parents=True, exist_ok=True)

    for item in src_dir.iterdir():
        dst_item = dst_dir / item.name

        if item.is_dir():
            sync_folder(item, dst_item)
        else:
            if not dst_item.exists():
                try:
                    shutil.copy2(item, dst_item)
                    print(f"[Update] New asset deployed: {item.name}")
                except Exception as e:
                    print(f"Failed to deploy {item.name}: {e}")

def deploy_assets():
    print("Checking assets...")

    # 1. Models (U2Net)
    sync_folder(INTERNAL_DIR / "models", MODEL_DIR)

    # 2. Real-ESRGAN (Exe & Models)
    sync_folder(INTERNAL_DIR / "realesrgan_ncnn", REALESRGAN_DIR)

    # 3. FFMPEG
    sync_folder(INTERNAL_DIR / "ffmpeg", FFMPEG_DIR)

    # 4. Plugins Folder (Default Plugins)
    internal_plugins = INTERNAL_DIR / "plugins"
    if internal_plugins.exists():
        PLUGIN_DIR.mkdir(exist_ok=True)
        for item in internal_plugins.glob("*.kit"):
            dst_item = PLUGIN_DIR / item.name
            try:
                shutil.copy2(item, dst_item)
                # print(f"[System] Built-in plugin deployed/updated: {item.name}")
            except Exception as e:
                print(f"Failed to deploy built-in {item.name}: {e}")

# ==========================================
# CUSTOM WIDGETS
# ==========================================

class BottomNavBar(QFrame):
    tab_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setObjectName("BottomNavBar")

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.buttonClicked.connect(self._on_btn_clicked)

    def add_tab(self, name, index, checked=False):
        btn = QPushButton(name)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(45)
        btn.setObjectName("NavButton")

        self.group.addButton(btn, index)
        self.layout.addWidget(btn)

        if checked:
            btn.setChecked(True)
        return btn

    def clear_plugins(self):
        for btn in self.group.buttons():
            if self.group.id(btn) >= 2:
                self.group.removeButton(btn)
                self.layout.removeWidget(btn)
                btn.deleteLater()

    def _on_btn_clicked(self, btn):
        self.tab_changed.emit(self.group.id(btn))

# ==========================================
# TABS
# ==========================================

class BgRemoverTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.image_paths = []
        self.output_dir = None
        self.output_map = {}
        self.current_preset_name = DEFAULT_PRESET_NAME
        self.presets = BG_PRESETS
        self.pixel_labels = []
        self._running_index = 0
        self._current_view_path = None
        self._setup_ui()
        self._init_running_text()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10); layout.setSpacing(10)
        
        # 1. Preview (Top)
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("PreviewFrame")
        self.preview_frame.setFrameShape(QFrame.StyledPanel)
        self.preview_frame.setStyleSheet("""
            #PreviewFrame {
                border: 1px solid #b3bcd1;
                border-radius: 4px;
                background-color: #f7f9fc;
            }
        """)
        
        pv_layout = QVBoxLayout(self.preview_frame)
        pv_layout.setContentsMargins(0,0,0,0)

        self.img_lbl = QLabel("Drag & Drop Images Here")
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.img_lbl.setMinimumHeight(200)
        self.img_lbl.setStyleSheet("border: none; color: #888;")
        pv_layout.addWidget(self.img_lbl)

        layout.addWidget(self.preview_frame, 3)

        # 2. Controls (Middle)
        controls = QFrame()
        controls.setObjectName("ControlFrame")
        c_layout = QVBoxLayout(controls)
        c_layout.setContentsMargins(0,5,0,5)

        # Row 1
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Model:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems(["Standard", "Anime"])
        row1.addWidget(self.combo_model)

        row1.addWidget(QLabel("Level:"))
        self.combo = QComboBox()
        self.combo.addItems(self.presets.keys())
        self.combo.currentTextChanged.connect(self.on_preset)
        row1.addWidget(self.combo)
        c_layout.addLayout(row1)

        # Row 2
        row2 = QHBoxLayout()
        self.btn_compare = QPushButton("Hold to Compare")
        self.btn_compare.setCursor(Qt.PointingHandCursor)
        self.btn_compare.pressed.connect(self.show_original)
        self.btn_compare.released.connect(self.show_result)
        self.btn_compare.setEnabled(False)
        row2.addWidget(self.btn_compare)

        self.btn_process = QPushButton("Remove BG")
        self.btn_process.setCursor(Qt.PointingHandCursor)
        self.btn_process.setStyleSheet("background-color: #e0f0ff; border: 1px solid #a0c0e0;")
        self.btn_process.clicked.connect(self.proc_all)
        row2.addWidget(self.btn_process)
        c_layout.addLayout(row2)

        layout.addWidget(controls)

        self.out_lbl = QLabel("Output: (Auto)"); self.out_lbl.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.out_lbl)

        # 3. List (Bottom)
        list_con = QWidget()
        lc = QVBoxLayout(list_con); lc.setContentsMargins(0,0,0,0)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Queue:"))
        b_clr = QPushButton("Clear"); b_clr.setFixedSize(50,20)
        b_clr.clicked.connect(self.clear_list)
        hl.addWidget(b_clr); hl.addStretch()
        lc.addLayout(hl)

        self.list_w = QListWidget()
        self.list_w.setFixedHeight(120)
        self.list_w.currentRowChanged.connect(self.on_file_selected)
        lc.addWidget(self.list_w)

        layout.addWidget(list_con, 1)

        # 4. Pixel Bar
        bot = QFrame(); bot.setObjectName("PixelBar")
        bl = QHBoxLayout(bot); bl.setContentsMargins(5,2,5,2); bl.setSpacing(10)
        font = QFont("Consolas", 8)
        for _ in range(5):
            l = QLabel("0.000000α"); l.setFont(font); self.pixel_labels.append(l); bl.addWidget(l)
        layout.addWidget(bot)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.add_files(files)

    def add_files(self, files):
        for f in files:
            p = Path(f)
            if p.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff']:
                if p not in self.image_paths:
                    self.image_paths.append(p)
                    item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                    self.list_w.addItem(item)
        if self.list_w.count()>0 and self.list_w.currentRow()<0: self.list_w.setCurrentRow(0)

    def _init_running_text(self):
        for l in self.pixel_labels: l.setText(random.choice(RUNNING_VALUES) + " •")
        self.timer = QTimer(self); self.timer.timeout.connect(self._update_text)
        self.timer.start(1000)

    def _update_text(self):
        idx = self._running_index % len(self.pixel_labels); self._running_index += 1
        self.pixel_labels[idx].setText(random.choice(RUNNING_VALUES) + " •")

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", IMAGE_FILTER)
        if files: self.add_files(files)

    def clear_list(self):
        self.image_paths.clear(); self.output_map.clear(); self.list_w.clear()
        self._update_prev(None)

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.image_paths): self._update_prev(None)
        else: self._update_prev(self.image_paths[row])

    def _update_prev(self, path):
        self._current_view_path = path
        self.btn_compare.setEnabled(False)
        self.btn_compare.setText("Hold to Compare")

        if not path:
            self.img_lbl.setText("Drag & Drop Images Here")
            self.img_lbl.setPixmap(QPixmap())
            return

        out = self.output_map.get(path)
        if out and out.exists():
            self.show_result()
            self.btn_compare.setEnabled(True)
        else:
            self.show_original()

    def show_original(self):
        if not self._current_view_path: return
        pix = QPixmap(str(self._current_view_path))
        if not pix.isNull():
            self.img_lbl.setPixmap(pix.scaled(self.img_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.img_lbl.setText("")

    def show_result(self):
        if not self._current_view_path: return
        out = self.output_map.get(self._current_view_path)
        if out and out.exists():
            pix = QPixmap(str(out))
            self.img_lbl.setPixmap(pix.scaled(self.img_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.img_lbl.setText("")
        else: self.show_original()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._current_view_path: self._update_prev(self._current_view_path)

    def on_preset(self, n): self.current_preset_name = n

    def ensure_out(self, sample):
        if not self.output_dir:
            self.output_dir = sample.parent / "LABOKit_BG"; self.output_dir.mkdir(exist_ok=True)
            self.out_lbl.setText(f"Output: {self.output_dir.name}")
            QMessageBox.information(self, "Info", f"Output folder set to:\n{self.output_dir}")
        return self.output_dir

    def change_output_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.output_dir = Path(d); self.out_lbl.setText(f"Output: {self.output_dir.name}")

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel: return QMessageBox.information(self, "Info", "Select images first.")
        self._run(sel)

    def proc_all(self):
        if not self.image_paths: return QMessageBox.information(self, "Info", "Add images first.")
        self._run(self.image_paths)

    def _run(self, paths):
        out = self.ensure_out(paths[0])
        dlg = QProgressDialog("Removing BG...", "Cancel", 0, len(paths), self)
        dlg.setWindowModality(Qt.ApplicationModal); dlg.show()
        
        cnt = 0
        import rembg
        from rembg import new_session

        model_map = {"Standard": "u2net", "Anime": "isnet-anime"}
        sel_model = model_map.get(self.combo_model.currentText(), "u2net")
        session = new_session(model_name=sel_model)

        for i, p in enumerate(paths):
            if dlg.wasCanceled(): break
            dlg.setLabelText(f"Processing {p.name}...")
            QApplication.processEvents()
            try:
                res = rembg.remove(p.read_bytes(), session=session, **self.presets.get(self.current_preset_name, {}))
                opath = out / f"{p.stem}_nobg.png"
                opath.write_bytes(res)
                self.output_map[p] = opath
                cnt += 1
            except Exception as e: print(e)
            dlg.setValue(i+1)
        dlg.close()
        QMessageBox.information(self, "Done", f"Processed {cnt} images.\nFolder: {out}")
        if self.list_w.currentRow() >= 0: self._update_prev(self.image_paths[self.list_w.currentRow()])

    def show_help(self):
        text = (
            "<h3>LABOKit – Background Remover</h3>"
            "<p>Powered by <b>U^2-Net</b> (Machine Learning).</p>"
            "<hr>"
            "<b>1. Add Images</b><br>"
            "Drag & drop files or use the 'Add Images' button.<br><br>"
            "<b>2. Sensitivity Presets</b>"
            "<ul>"
            "<li><b>Standard:</b> Best for general use. Fast & clean edges.</li>"
            "<li><b>Medium:</b> Applies post-processing to smooth rough edges.</li>"
            "<li><b>High:</b> Aggressive alpha matting. Good for hair/fur details but slower.</li>"
            "</ul>"
        )
        QMessageBox.information(self, "Help – BG Remover", text)

class UpscalerTab(QWidget):
    MODEL_MAP = {
        "General": "realesrgan-x4plus",
        "Anime/2D": "realesrgan-x4plus-anime",
        "General - Performance Mode": "realesr-general-x4v3.pth"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.image_paths = []
        self.output_dir = None
        self.output_map = {}
        self.pixel_labels = []
        self._running_index = 0
        self._current_view_path = None
        self._setup_ui()
        self._init_running_text()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10); layout.setSpacing(10)
        
        # 1. Preview (Top)
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("PreviewFrame")
        self.preview_frame.setFrameShape(QFrame.StyledPanel)
        self.preview_frame.setStyleSheet("""
            #PreviewFrame {
                border: 1px solid #b3bcd1;
                border-radius: 4px;
                background-color: #f7f9fc;
            }
        """)
        
        pv_layout = QVBoxLayout(self.preview_frame)
        pv_layout.setContentsMargins(0,0,0,0)

        self.img_lbl = QLabel("Drag & Drop Images Here")
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.img_lbl.setMinimumHeight(200)
        self.img_lbl.setStyleSheet("border: none; color: #888;")
        pv_layout.addWidget(self.img_lbl)

        layout.addWidget(self.preview_frame, 3)

        # 2. Controls (Middle)
        controls = QFrame()
        controls.setObjectName("ControlFrame")
        c_layout = QVBoxLayout(controls)
        c_layout.setContentsMargins(0,5,0,5)

        # Row 1
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Scale:"))
        self.combo_s = QComboBox(); self.combo_s.addItems(["2x", "4x"]); self.combo_s.setCurrentText("4x")
        self.combo_s.setFixedWidth(60)
        row1.addWidget(self.combo_s)

        row1.addWidget(QLabel("Model:"))
        self.combo_m = QComboBox()
        self.combo_m.addItems(list(self.MODEL_MAP.keys()))
        row1.addWidget(self.combo_m)
        c_layout.addLayout(row1)

        # Row 2
        row2 = QHBoxLayout()
        self.btn_compare = QPushButton("Hold to Compare")
        self.btn_compare.setCursor(Qt.PointingHandCursor)
        self.btn_compare.pressed.connect(self.show_original)
        self.btn_compare.released.connect(self.show_result)
        self.btn_compare.setEnabled(False)
        row2.addWidget(self.btn_compare)

        self.btn_process = QPushButton("Upscale")
        self.btn_process.setCursor(Qt.PointingHandCursor)
        self.btn_process.setStyleSheet("background-color: #e0f0ff; border: 1px solid #a0c0e0;")
        self.btn_process.clicked.connect(self.proc_all)
        row2.addWidget(self.btn_process)
        c_layout.addLayout(row2)

        layout.addWidget(controls)

        self.out_lbl = QLabel("Output: (Auto)"); self.out_lbl.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.out_lbl)

        # 3. List
        list_con = QWidget()
        lc = QVBoxLayout(list_con); lc.setContentsMargins(0,0,0,0)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Queue:"))
        b_clr = QPushButton("Clear"); b_clr.setFixedSize(50,20)
        b_clr.clicked.connect(self.clear_list)
        hl.addWidget(b_clr); hl.addStretch()
        lc.addLayout(hl)

        self.list_w = QListWidget()
        self.list_w.setFixedHeight(120)
        self.list_w.currentItemChanged.connect(self.on_item)
        lc.addWidget(self.list_w)
        layout.addWidget(list_con, 1)

        # 4. Pixel Bar
        bot = QFrame(); bot.setObjectName("PixelBar")
        bl = QHBoxLayout(bot); bl.setContentsMargins(5,2,5,2); bl.setSpacing(10)
        font = QFont("Consolas", 8)
        for _ in range(5):
            l = QLabel("0.000000α"); l.setFont(font); self.pixel_labels.append(l); bl.addWidget(l)
        layout.addWidget(bot)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.add_files(files)

    def add_files(self, files):
        for f in files:
            p = Path(f)
            if p.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff']:
                if p not in self.image_paths:
                    self.image_paths.append(p)
                    item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                    self.list_w.addItem(item)
        if self.list_w.count()>0: self.list_w.setCurrentRow(0)

    def run_python_inference(self, img_path, out_path, model_name):
        if not HAS_TORCH:
            QMessageBox.critical(self, "Error", "(torch/basicsr/realesrgan) is not ready.")
            return False

        try:
            model_path = REALESRGAN_DIR / "models" / model_name 
            if not model_path.exists():
                model_path = MODEL_DIR / model_name
                if not model_path.exists(): return False

            model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
            
            upsampler = RealESRGANer(
                scale=4,
                model_path=str(model_path),
                model=model,
                tile=400,       
                tile_pad=10,
                pre_pad=0,
                half=False,   
                gpu_id=None
            )

            img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
            output, _ = upsampler.enhance(img, outscale=4)
            cv2.imwrite(str(out_path), output)
            return True

        except Exception as e:
            print(f"Error: {e}")
            import traceback; traceback.print_exc()
            return False

    def _init_running_text(self):
        for l in self.pixel_labels: l.setText(random.choice(RUNNING_VALUES) + " •")
        self.timer = QTimer(self); self.timer.timeout.connect(self._update_text)
        self.timer.start(1000)

    def _update_text(self):
        idx = self._running_index % len(self.pixel_labels); self._running_index += 1
        self.pixel_labels[idx].setText(random.choice(RUNNING_VALUES) + " •")

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", IMAGE_FILTER)
        if files: self.add_files(files)

    def clear_list(self):
        self.image_paths.clear(); self.output_map.clear(); self.list_w.clear()
        self._update_prev(None)

    def on_item(self, curr, prev):
        if not curr: self._update_prev(None)
        else: self._update_prev(curr.data(Qt.UserRole))

    def _update_prev(self, path):
        self._current_view_path = path
        self.btn_compare.setEnabled(False)
        self.btn_compare.setText("Hold to Compare")

        if not path:
            self.img_lbl.setText("Drag & Drop Images Here")
            self.img_lbl.setPixmap(QPixmap())
            return

        out = self.output_map.get(path)
        if out and out.exists():
            self.show_result()
            self.btn_compare.setEnabled(True)
        else:
            self.show_original()

    def show_original(self):
        if not self._current_view_path: return
        pix = QPixmap(str(self._current_view_path))
        if not pix.isNull():
            self.img_lbl.setPixmap(pix.scaled(self.img_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.img_lbl.setText("")

    def show_result(self):
        if not self._current_view_path: return
        out = self.output_map.get(self._current_view_path)
        if out and out.exists():
            pix = QPixmap(str(out))
            self.img_lbl.setPixmap(pix.scaled(self.img_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.img_lbl.setText("")
        else: self.show_original()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._current_view_path: self._update_prev(self._current_view_path)

    def ensure_out(self, sample):
        if not self.output_dir:
            self.output_dir = sample.parent / "LABOKit_UP"; self.output_dir.mkdir(exist_ok=True)
            self.out_lbl.setText(f"Output: {self.output_dir.name}")
            QMessageBox.information(self, "Info", f"Output folder set to:\n{self.output_dir}")
        return self.output_dir
    
    def change_output_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.output_dir = Path(d); self.out_lbl.setText(f"Output: {self.output_dir.name}")

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel: return QMessageBox.information(self, "Info", "Select images first.")
        self._run(sel)

    def proc_all(self):
        if not self.image_paths: return QMessageBox.information(self, "Info", "Add images first.")
        self._run(self.image_paths)

    def _run(self, paths):
        display_name = self.combo_m.currentText()
        model_name = self.MODEL_MAP.get(display_name, "realesrgan-x4plus")

        is_python_mode = model_name.endswith(".pth")

        if not is_python_mode and not REALESRGAN_EXE.exists():
            return QMessageBox.warning(self, "Error", f"Executable not found at:\n{REALESRGAN_EXE}")
        
        out = self.ensure_out(paths[0])
        dlg = QProgressDialog("Upscaling...", "Cancel", 0, len(paths), self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()
        
        cnt = 0
        target_scale = 4 # Default model scale
        
        for i, p in enumerate(paths):
            if dlg.wasCanceled(): break
            dlg.setLabelText(f"Processing {p.name}...")
            QApplication.processEvents()
            
            try:
                opath = out / f"{p.stem}_up4x.png"
                success = False

                if is_python_mode:
                    success = self.run_python_inference(p, opath, model_name)
                
                else:
                    cmd = [
                        str(REALESRGAN_EXE), 
                        "-i", str(p), 
                        "-o", str(opath), 
                        "-n", model_name, 
                        "-s", "4"
                    ]
                    flags = subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0
                    subprocess.run(cmd, capture_output=True, creationflags=flags, cwd=str(REALESRGAN_DIR))
                    success = opath.exists()

                if success:
                    self.output_map[p] = opath
                    cnt += 1
                    
            except Exception as e: 
                print(f"Upscale Error: {e}")
            
            dlg.setValue(i+1)
        
        dlg.close()
        QMessageBox.information(self, "Done", f"Upscaled {cnt} images.\nFolder: {out}")
        if self.list_w.currentItem(): self.on_item(self.list_w.currentItem(), None)

    def show_help(self):
        text = (
            "<h3>LABOKit – Upscaler</h3>"
            "<p>Powered by <b>Real-ESRGAN</b> (NCNN Vulkan).</p>"
            "<hr>"
            "<b>1. Add Images</b><br>"
            "Drag & drop files or use the 'Add Images' button.<br><br>"
            "<b>2. Model Selection</b>"
            "<ul>"
            "<li><b>General:</b> Best for photos, realistic textures (Standard x4plus).</li>"
            "<li><b>Anime/2D:</b> Optimized for 2D illustration/line art (x4plus-anime).</li>"
            "<li><b>General - Performance:</b> CPU optimized (x4v3).</li>"
            "</ul>"
        )
        QMessageBox.information(self, "Help – Upscaler", text)
        

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.parent_win = parent
        self.pressing = False
        self.start_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.title_lbl = QLabel("LABOKit")
        self.title_lbl.setStyleSheet("font-weight: bold; color: #333; border: none; background: transparent;")
        self.title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.menu_container = QWidget()
        self.menu_container.setStyleSheet("background: transparent; border: none;") 
        self.menu_layout = QHBoxLayout(self.menu_container)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(5)

        btn_size = 18
        radius = btn_size // 2
        
        btn_style = f"""
            QPushButton {{
                background-color: #808080;
                border: none;
                border-radius: {radius}px;
                font-family: "Arial", "Segoe UI", sans-serif; 
                font-size: 13px;
                font-weight: 450;
                color: white;
                margin: 0px;
                padding: 0px; 
                padding-bottom: 2px;
            }}
            QPushButton:hover {{
                background-color: #666666;
            }}
            QPushButton:pressed {{
                background-color: #444444;
            }}
        """

        self.btn_min = QPushButton("−") 
        self.btn_min.setFixedSize(btn_size, btn_size)
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(self.minimize_window)

        self.btn_close = QPushButton("×") 
        self.btn_close.setFixedSize(btn_size, btn_size)
        self.btn_close.setStyleSheet(btn_style)
        self.btn_close.clicked.connect(self.close_window)

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.menu_container)
        layout.addStretch(1) 
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_close)

        self.setStyleSheet("""
            CustomTitleBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f0f0f0, 
                                            stop:0.5 #dcdcdc,
                                            stop:1 #b0b0b0);
                border: none;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start_pos = event.globalPosition().toPoint() - self.parent_win.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.pressing and event.buttons() & Qt.LeftButton:
            self.parent_win.move(event.globalPosition().toPoint() - self.start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.pressing = False

    def minimize_window(self):
        self.parent_win.showMinimized()

    def close_window(self):
        self.parent_win.close()

# --- UPDATE WORKERS ---

class AppUpdateChecker(QThread):
    found_update = Signal(str, str, str) # version, url, changelog

    def run(self):
        try:
            with urllib.request.urlopen(APP_UPDATE_URL) as url:
                data = json.loads(url.read().decode())
                remote_ver = data.get("version", "0.0.0")
                if remote_ver > APP_VERSION:
                    self.found_update.emit(remote_ver, data.get("url", ""), data.get("changelog", ""))
        except Exception as e:
            print(f"App Update Check Failed: {e}")

class PluginUpdater(QThread):
    update_found = Signal(str, str, str, str) 

    def run(self):
        try:
            if not PLUGIN_DIR.exists(): return
            
            with urllib.request.urlopen(PLUGIN_MANIFEST_URL) as url:
                remote_data = json.loads(url.read().decode())

            for kit_file in PLUGIN_DIR.glob("*.kit"):
                plugin_id = kit_file.stem 
                
                if plugin_id in remote_data:
                    remote_info = remote_data[plugin_id]
                    
                    local_ver = self.get_local_version(kit_file)
                    remote_ver = remote_info.get("version", "1.0")
                    
                    if remote_ver > local_ver:
                        enc_url = remote_info.get("url_encoded", "")
                        try:
                            if enc_url == "-" or not enc_url: continue
                            real_url = base64.b64decode(enc_url).decode("utf-8")
                            self.update_found.emit(plugin_id, remote_ver, remote_info.get("changelog", ""), real_url)
                        except: pass

        except Exception as e:
            print(f"Plugin Update Check Failed: {e}")

    def get_local_version(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            import re
            match = re.search(r'PLUGIN_VERSION\s*=\s*["\']([^"\']+)["\']', content)
            
            if match:
                return match.group(1) 
            
            return "1.0" 
            
        except Exception as e:
            # print(f"Version check error for {path.name}: {e}")
            return "1.0"

# ==========================================
# MAIN WINDOW
# ==========================================

class LABOKitMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LABOKit")
        self.resize(450, 850) # Portrait Mode (Default)
        self.setMinimumSize(400, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        self.central_container = QWidget()
        self.setCentralWidget(self.central_container)
        
        self.outer_layout = QVBoxLayout(self.central_container)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)
        
        # Main Frame (Background)
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.outer_layout.addWidget(self.main_frame)
        
        self.main_layout = QVBoxLayout(self.main_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Custom Title Bar
        self.custom_title_bar = CustomTitleBar(self)
        self.main_layout.addWidget(self.custom_title_bar)

        # 2. Content Area (Stacked)
        self.stack = QStackedWidget()
        self.bg_tab = BgRemoverTab(self)
        self.up_tab = UpscalerTab(self)
        
        self.stack.addWidget(self.bg_tab) # Index 0
        self.stack.addWidget(self.up_tab) # Index 1

        self.main_layout.addWidget(self.stack)

        # 3. Bottom Navigation
        self.navbar = BottomNavBar()
        self.navbar.add_tab("BG Remove", 0, checked=True)
        self.navbar.add_tab("Upscale", 1)
        self.navbar.tab_changed.connect(self.switch_tab)

        self.main_layout.addWidget(self.navbar)

        self.loaded_plugins = []
        self._setup_menu()
        self._load_plugins()
        self.check_app_updates()
        self.check_plugin_updates()

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)

    def resizeEvent(self, event):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        
        super().resizeEvent(event)

    def _load_plugins(self):
        if not PLUGIN_DIR.exists(): PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        
        # Remove old plugins from Stack and Navbar
        # Note: Index 0 and 1 are fixed (BG, Upscale)
        while self.stack.count() > 2:
            w = self.stack.widget(2)
            self.stack.removeWidget(w)
            w.deleteLater()

        self.navbar.clear_plugins()
        self.loaded_plugins.clear()

        # Load new
        plugin_index = 2
        for f in PLUGIN_DIR.glob("*.kit"):
            try:
                mod_name = f"plugin_{f.stem}"
                loader = importlib.machinery.SourceFileLoader(mod_name, str(f))
                spec = importlib.util.spec_from_file_location(mod_name, str(f), loader=loader)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                if hasattr(mod, "create_tab"):
                    tab = mod.create_tab(self)
                    name = getattr(mod, "PLUGIN_NAME", f.stem)

                    self.stack.addWidget(tab)
                    self.navbar.add_tab(name, plugin_index)

                    self.loaded_plugins.append({"name": name, "tab": tab, "help": getattr(mod, "HELP_TEXT", "")})
                    plugin_index += 1
            except Exception as e: print(f"Plugin Error {f.name}: {e}")

        self._refresh_plugin_menu()

    def _refresh_plugin_menu(self):
        if hasattr(self, "menu_plugins"):
            self.menu_plugins.clear()
            if not self.loaded_plugins:
                self.menu_plugins.addAction(QAction("(No plugins loaded)", self, enabled=False))
            else:
                for p in self.loaded_plugins:
                    a = QAction(p["name"], self)
                    a.triggered.connect(lambda c, x=p: QMessageBox.information(self, "Help", x["help"]))
                    self.menu_plugins.addAction(a)

    def load_plugin_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Load Plugin", "", "LABOKit Plugin (*.kit)")
        if f:
            try:
                shutil.copy2(f, PLUGIN_DIR)
                self._load_plugins()
                QMessageBox.information(self, "Success", "Plugin loaded!")
            except Exception as e: QMessageBox.warning(self, "Error", str(e))

    def open_url(self, url): QDesktopServices.openUrl(QUrl(url))
    def _setup_menu(self):
        mb = QMenuBar()
        mb.setStyleSheet("""
            QMenuBar { 
                background: transparent; 
                border: none;
            }
            QMenuBar::item { 
                background: transparent; 
                color: #333; 
                padding: 4px 8px;
                border-radius: 4px;
            }
            QMenuBar::item:selected { 
                background-color: rgba(0, 0, 0, 0.1);
                color: #000; 
            }
            
            QMenu {
                background-color: #f7f9fc; 
                border: 1px solid #b3bcd1;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 4px 24px 4px 10px; 
                color: #1c2333;
                border-radius: 3px;
                background: transparent;
            }
            QMenu::item:selected {
                background-color: #cfe2ff;
                color: #101522;
            }
        """)
        
        self.custom_title_bar.menu_layout.addWidget(mb)

        file = mb.addMenu("&File")
        file.addAction("Add Images...", self.add_images_curr)
        file.addAction("Change Output Folder...", self.change_out_curr)
        file.addSeparator()
        file.addAction("Exit", self.close)

        conf = mb.addMenu("&Config")
        conf.addAction("Load Plugin (.kit)...", self.load_plugin_file)
        conf.addAction("Open Plugins Folder", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(PLUGIN_DIR))))

        help = mb.addMenu("&Help")
        help.addAction("BG Remover Help", self.bg_tab.show_help)
        help.addAction("Upscaler Help", self.up_tab.show_help)
        help.addSeparator()
        help.addAction("Licenses / NOTICE", self.show_notice)
        self.menu_plugins = help.addMenu("Plugins")

        supp = mb.addMenu("&Support")
        supp.addAction("Get Plugins (Trakteer ID)", lambda: self.open_url("https://trakteer.id/kano-bbif7/showcase/labokit-advanced-plugins-m84J6"))
        supp.addAction("Get Plugins (Ko-fi)", lambda: self.open_url("https://ko-fi.com/s/a367e473fe"))

    def add_images_curr(self):
        w = self.stack.currentWidget()
        if hasattr(w, "add_images"): w.add_images()

    def change_out_curr(self):
        w = self.stack.currentWidget()
        if hasattr(w, "change_output_folder"): w.change_output_folder()

    def show_bg_help(self): self.bg_tab.show_help()
    def show_upscale_help(self): self.up_tab.show_help()

    def show_notice(self):
        p = INTERNAL_DIR / "LABOKit_NOTICE.txt"
        if not p.exists(): return QMessageBox.warning(self, "Error", "Notice file missing.")
        dlg = QDialog(self); dlg.setWindowTitle("NOTICE"); dlg.resize(600,400)
        lay = QVBoxLayout(dlg); t = QPlainTextEdit(p.read_text(encoding="utf-8")); t.setReadOnly(True)
        t.setFont(QFont("Consolas",9)); lay.addWidget(t); dlg.exec()

    def check_app_updates(self):
        self.app_checker = AppUpdateChecker()
        self.app_checker.found_update.connect(self.show_app_update_dialog)
        self.app_checker.start()

    def show_app_update_dialog(self, new_ver, url, log):
        msg = QMessageBox(self)
        msg.setWindowTitle("Update Available!")
        msg.setText(f"<b>New version {new_ver} is available!</b>")
        msg.setInformativeText(f"Current: v{APP_VERSION}\n\n<b>What's New:</b>\n{log}")
        msg.setIcon(QMessageBox.Information)
        btn_download = msg.addButton("Download Now", QMessageBox.AcceptRole)
        msg.addButton("Later", QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_download:
            QDesktopServices.openUrl(QUrl(url))

    def check_plugin_updates(self):
        self.plugin_updater = PluginUpdater()
        self.plugin_updater.update_found.connect(self.download_and_install_plugin)
        self.plugin_updater.start()

    def download_and_install_plugin(self, name, new_ver, log, url):
        try:
            prog = QProgressDialog(f"Auto-updating {name} to v{new_ver}...", None, 0, 0, self)
            prog.setWindowModality(Qt.WindowModal)
            prog.setStyleSheet("QProgressDialog { background-color: #f5f7fb; }")
            prog.show()
            QApplication.processEvents()
            
            target_file = PLUGIN_DIR / f"{name}.kit"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            with requests.get(url, headers=headers, stream=True, verify=False, timeout=30) as r:
                r.raise_for_status() # Cek error 403/404/500
                with open(target_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        if chunk: f.write(chunk)
            
            prog.close()
            
            QMessageBox.information(self, "Plugin Updated", f"<b>{name}</b> has been auto-updated to v{new_ver}!\n\nChangelog:\n{log}")
            self._load_plugins() 
            
        except Exception as e:
            print(f"Auto-update failed for {name}: {e}")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LABOKit")
    if ICON_PATH.exists(): app.setWindowIcon(QIcon(str(ICON_PATH)))
    default_font = QFont("Consolas", 9)
    app.setFont(default_font)

    # Simple Splash (Image Only)
    splash_img_path = INTERNAL_DIR / "splash.png"
    pix = QPixmap(str(splash_img_path)) if splash_img_path.exists() else QPixmap(400,100)
    if not splash_img_path.exists(): pix.fill(Qt.white)
    
    splash = QSplashScreen(pix.scaledToWidth(400, Qt.SmoothTransformation), Qt.WindowStaysOnTopHint)
    splash.show(); app.processEvents()

    # Silent Deploy
    deploy_assets()

    # Style
    app.setStyleSheet("""
        QMainWindow { background-color: #f0f2f5; }

        /* Menu Bar */
        QMenuBar { background-color: #ffffff; color: #333; border-bottom: 1px solid #eee; }
        QMenuBar::item { background: transparent; padding: 6px 12px; color: #444; }
        QMenuBar::item:selected { background-color: #f0f0f0; color: #000; border-radius: 4px; }

        /* Menu */
        QMenu { background-color: #ffffff; border: 1px solid #ddd; border-radius: 6px; padding: 4px; }
        QMenu::item { padding: 6px 24px 6px 12px; color: #333; border-radius: 4px; }
        QMenu::item:selected { background-color: #e6efff; color: #0066ff; }

        /* List Widget */
        QListWidget { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; outline: none; }
        QListWidget::item { padding: 8px 10px; color: #333; border-bottom: 1px solid #f5f5f5; }
        QListWidget::item:selected { background-color: #e6efff; color: #0066ff; border-radius: 4px; }

        /* Frames */
        QFrame { border: none; }
        #MainFrame { background-color: #f0f2f5; border: 1px solid #ccc; border-radius: 12px; }
        #PreviewFrame { background-color: #e3e6eb; border-radius: 8px; border: 1px solid #d0d0d0; }
        #ControlFrame { background-color: #ffffff; border-radius: 8px; border: 1px solid #e0e0e0; }
        #BottomNavBar { background-color: #ffffff; border-top: 1px solid #e0e0e0; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }
        #PixelBar { background-color: #2b303b; border-radius: 0px; }
        #PixelBar QLabel { color: #d00000; font-family: "Consolas"; font-weight: bold; }

        /* Buttons */
        QPushButton {
            color: #333;
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            padding: 6px 16px;
            font-weight: 500;
        }
        QPushButton:hover { background-color: #f8f9fa; border-color: #b0b0b0; }
        QPushButton:pressed { background-color: #e9ecef; border-color: #a0a0a0; }

        /* Nav Button Specifics */
        #NavButton {
            background-color: transparent;
            border: none;
            color: #888;
            font-size: 11px;
            text-align: center;
        }
        #NavButton:checked {
            color: #0066ff;
            background-color: #f0f7ff;
            font-weight: bold;
        }
        #NavButton:hover {
            color: #555;
            background-color: #f5f5f5;
        }

        /* Labels */
        QLabel { color: #333; }

        /* Inputs */
        QComboBox { background-color: #ffffff; border: 1px solid #d0d0d0; border-radius: 6px; padding: 4px 8px; color: #333; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background-color: #ffffff; border: 1px solid #d0d0d0; selection-background-color: #e6efff; selection-color: #0066ff; }

        QProgressDialog { background-color: #f0f2f5; }
        QDialog, QMessageBox { background-color: #f0f2f5; }
    """)

    win = LABOKitMainWindow()
    win.show()
    splash.finish(win)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()