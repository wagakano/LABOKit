
import sys
import os
import random
import subprocess
import shutil
import psutil

# Ensure main directory is in path for plugins to import other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)



def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from pathlib import Path
from packaging import version
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- TRANSLATIONS ---
from translations import tr, set_language, CURRENT_LANG

# --- APP INFO ---
APP_VERSION = "3.2.0"
APP_UPDATE_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/latest_version.json"
PLUGIN_MANIFEST_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/plugins_manifest.json"


# --- PATH & ASSETS SETUP ---
# 1. Internal Path (Source files inside EXE/Build)
INTERNAL_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

# 2. Persistent Path (User AppData folder: %APPDATA%/LABOKit)
_app_data = os.getenv('APPDATA')
if not _app_data:
    _app_data = os.path.expanduser("~") # Fallback
APP_DATA = Path(_app_data) / "LABOKit"
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
from PySide6.QtCore import Qt, QSize, QTimer, QUrl, QRectF, QThread, Signal, QObject, QDateTime, QEvent

from PySide6.QtGui import QAction, QPixmap, QFont, QIcon, QDesktopServices, QPainterPath, QRegion, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QFileDialog,
    QMessageBox, QProgressDialog, QFrame, QComboBox, QTabWidget,
    QDialog, QPlainTextEdit, QSplashScreen, QMenuBar, QSizePolicy,
    QScrollArea, QMenu
)
from ui_shared import FileDropListWidget, ZoomableImageWidget, DivergenceMeter, create_plus_icon, VALID_EXTENSIONS

# --- MONKEYPATCH FOR CLICKABLE BUTTON CURSOR ---
_orig_btn_init = QPushButton.__init__
def _new_btn_init(self, *args, **kwargs):
    _orig_btn_init(self, *args, **kwargs)
    self.setCursor(Qt.PointingHandCursor)
QPushButton.__init__ = _new_btn_init


IMAGE_FILTER = (
    "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.gif "
    "*.JPG *.JPEG *.PNG *.BMP *.TIF *.TIFF *.WEBP *.GIF)"
)

APP_VERSION = "3.2"

class AppUpdater(QThread):
    update_available = Signal(str, str, str) # version, download_url, changelog
    
    def run(self):
        try:
            import requests
            url = "https://raw.githubusercontent.com/wagakano/LABOKit-assets/main/app_manifest.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("version", "0.0")
                if latest_version != APP_VERSION:
                    self.update_available.emit(latest_version, data.get("download_url"), data.get("changelog", "No changelog provided."))
        except Exception as e:
            print(f"Failed to check for app updates: {e}")

class PatchDownloader(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            import tempfile
            patch_path = Path(tempfile.gettempdir()) / "labokit_patch.zip"
            
            downloaded = 0
            with open(patch_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.progress.emit(int((downloaded / total_size) * 100))
                            
            self.finished.emit(str(patch_path))
        except Exception as e:
            self.error.emit(str(e))

# --- LAZY LOADING AI ENGINE ---
AI_MODULES = None
GLOBAL_UPSAMPLER_CACHE = {}
GLOBAL_REMBG_SESSION_CACHE = {}

def load_ai_engine():
    global AI_MODULES
    if AI_MODULES:
        return AI_MODULES

    try:
        # Patch torchvision
        import torchvision.transforms.functional as F
        try:
            from torchvision.transforms import functional_tensor
        except ImportError:
            import sys
            from types import ModuleType
            ft_module = ModuleType('torchvision.transforms.functional_tensor')
            ft_module.rgb_to_grayscale = F.rgb_to_grayscale
            sys.modules['torchvision.transforms.functional_tensor'] = ft_module

        import torch
        from torch import nn
        import cv2
        import numpy as np
        from basicsr.archs.srvgg_arch import SRVGGNetCompact 
        from realesrgan import RealESRGANer
        
        AI_MODULES = {
            "torch": torch,
            "cv2": cv2,
            "SRVGGNetCompact": SRVGGNetCompact,
            "RealESRGANer": RealESRGANer
        }
        return AI_MODULES
    except ImportError as e:
        print(f"AI Engine Load Error: {e}")
        return None

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

    # 4b. Local Plugins for Development/Testing
    # If there is a local 'LABOKit Plugins/3.0' directory, copy the plugins to PLUGIN_DIR
    local_dev_plugins = Path(__file__).resolve().parent / "LABOKit Plugins" / "3.0"
    if local_dev_plugins.exists():
        PLUGIN_DIR.mkdir(exist_ok=True)
        for item in local_dev_plugins.glob("*.kit"):
            if "stickerprepper" in item.name.lower():
                continue
            dst_item = PLUGIN_DIR / item.name
            try:
                shutil.copy2(item, dst_item)
                print(f"[System] Developer plugin deployed/updated: {item.name}")
            except Exception as e:
                print(f"Failed to deploy dev plugin {item.name}: {e}")

# ==========================================
# TABS
# ==========================================

class BgRemoverTab(QWidget):
    def __init__(self, meter=None, parent=None):
        super().__init__(parent)
        self.meter = meter
        self.image_paths = []
        self.output_dir = None
        self.output_map = {}
        self.current_preset_name = DEFAULT_PRESET_NAME
        self.presets = BG_PRESETS
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8,8,8,8); outer.setSpacing(6)
        main = QHBoxLayout(); outer.addLayout(main)
        
        # Left Panel (Controls)
        left = QVBoxLayout(); main.addLayout(left, 1)
        
        # Loaded Images Box
        list_box = QFrame()
        list_box_layout = QVBoxLayout(list_box)
        list_box_layout.setContentsMargins(6, 6, 6, 6)
        list_box_layout.setSpacing(5)
        
        self.list_w = FileDropListWidget()
        self.list_w.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_w.customContextMenuRequested.connect(self.show_list_context_menu)
        self.list_w.files_dropped.connect(self.add_dropped_files)
        self.list_w.currentRowChanged.connect(self.on_file_selected)
        lbl = QLabel(tr("lbl_loaded_bg"))
        lbl.setStyleSheet("font-weight: bold; background-color: #e2e7f2; border: 1px solid #cbd2e1; border-radius: 3px; padding: 4px 6px; color: #333d51;")
        list_box_layout.addWidget(lbl)
        list_box_layout.addWidget(self.list_w)
        
        # Buttons (Add/Clear)
        btns = QHBoxLayout()
        b_add = QPushButton(tr("btn_add")); b_add.setIcon(create_plus_icon()); b_add.clicked.connect(self.add_images)
        b_clr = QPushButton(tr("btn_clear")); b_clr.clicked.connect(self.clear_list)
        btns.addWidget(b_add); btns.addWidget(b_clr)
        list_box_layout.addLayout(btns)
        
        left.addWidget(list_box)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("border: none; background-color: #b3bcd1; min-height: 1px; max-height: 1px; margin: 10px 0;")
        left.addWidget(line)

        # Options in sidebar
        l_out = QLabel(tr("lbl_out")); l_out.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        left.addWidget(l_out)
        self.out_lbl = QLabel("(auto)"); self.out_lbl.setWordWrap(True)
        self.out_lbl.setStyleSheet("color: #666; margin-bottom: 5px; border: none; background: transparent;")
        left.addWidget(self.out_lbl)

        out_btn_lay = QHBoxLayout()
        out_btn_lay.setSpacing(5)
        b_change = QPushButton(tr("btn_change")); b_change.clicked.connect(self.change_output_folder)
        b_open_out = QPushButton(tr("btn_open_out", "Open Folder")); b_open_out.clicked.connect(self.open_output_folder)
        out_btn_lay.addWidget(b_change)
        out_btn_lay.addWidget(b_open_out)
        left.addLayout(out_btn_lay)
        
        pres_row = QVBoxLayout() 
        pres_row.setSpacing(5)

        l_mod = QLabel(tr("lbl_model")); l_mod.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        pres_row.addWidget(l_mod)
        self.combo_model = QComboBox()
        self.combo_model.addItems(["General", "Anime"])
        pres_row.addWidget(self.combo_model)

        l_sen = QLabel(tr("lbl_sens")); l_sen.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        pres_row.addWidget(l_sen)
        self.combo = QComboBox(); self.combo.addItems(self.presets.keys())
        self.combo.currentTextChanged.connect(self.on_preset)
        pres_row.addWidget(self.combo)
        left.addLayout(pres_row)

        left.addSpacing(10)
        b_sel = QPushButton(tr("btn_proc_sel")); b_sel.clicked.connect(self.proc_sel)
        b_all = QPushButton(tr("btn_proc_all")); b_all.clicked.connect(self.proc_all)
        left.addWidget(b_sel)
        left.addWidget(b_all)

        # Right Panel (Preview)
        right = QVBoxLayout(); main.addLayout(right, 3)
        self.preview_widget = ZoomableImageWidget()
        right.addWidget(self.preview_widget)
    
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr("btn_add"), "", IMAGE_FILTER)
        if not files: return
        for f in files:
            p = Path(f)
            if p not in self.image_paths:
                self.image_paths.append(p)
                item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                self.list_w.addItem(item)
        if self.list_w.count()>0: self.list_w.setCurrentRow(0)

    def add_dropped_files(self, files):
        for p in files:
            if p.suffix.lower() in VALID_EXTENSIONS:
                if p not in self.image_paths:
                    self.image_paths.append(p)
                    item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                    self.list_w.addItem(item)
        if self.list_w.count() > 0 and self.list_w.currentRow() < 0:
            self.list_w.setCurrentRow(0)

    def clear_list(self):
        self.image_paths.clear(); self.output_map.clear(); self.list_w.clear()
        self.preview_widget.set_images(None, None) # Explicitly clear

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.image_paths): 
            self.preview_widget.set_images(None, None)
        else: self._update_prev(self.image_paths[row])

    def show_list_context_menu(self, pos):
        item = self.list_w.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        action_remove = QAction("Remove", self)
        action_remove.triggered.connect(lambda: self.remove_selected_image(item))
        menu.addAction(action_remove)
        menu.exec(self.list_w.mapToGlobal(pos))

    def remove_selected_image(self, item):
        row = self.list_w.row(item)
        if row >= 0:
            self.list_w.takeItem(row)
            if row < len(self.image_paths):
                path = self.image_paths.pop(row)
                if path in self.output_map:
                    del self.output_map[path]
            # Clear preview if list empty or selection changed
            if not self.image_paths:
                self.preview_widget.set_images(None, None)
            elif row < len(self.image_paths):
                self.list_w.setCurrentRow(row) # Select next
            else:
                self.list_w.setCurrentRow(len(self.image_paths) - 1) # Select last

    def _update_prev(self, path):
        if path is None:
            self.preview_widget.set_images(None, None)
            return
        out = self.output_map.get(path)
        self.preview_widget.set_images(path, out)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # The preview widget handles fit+update via its own debounce timer


    def on_preset(self, n): self.current_preset_name = n

    def ensure_out(self, sample):
        if not self.output_dir:
            self.output_dir = sample.parent / "LABOKit_BG"; self.output_dir.mkdir(exist_ok=True)
            self.out_lbl.setText(f"BG OUTPUT FOLDER: {self.output_dir}")
            QMessageBox.information(self, "Info", f"Output folder set to:\n{self.output_dir}")
        return self.output_dir

    def change_output_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.output_dir = Path(d); self.out_lbl.setText(f"BG OUTPUT FOLDER: {self.output_dir}")

    def open_output_folder(self):
        d = self.output_dir
        if not d and self.image_paths:
            d = self.image_paths[0].parent / "LABOKit_BG"
        if d and d.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))
        else:
            QMessageBox.information(self, "Info", "Output folder does not exist yet. Process an image first.")

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel: return QMessageBox.information(self, "Info", tr("msg_select"))
        self._run(sel)

    def proc_all(self):
        if not self.image_paths: return QMessageBox.information(self, "Info", tr("msg_add"))
        self._run(self.image_paths)

    def _run(self, paths):
        out = self.ensure_out(paths[0])
        self.dlg = QProgressDialog("Initializing BG Remover", "Cancel", 0, len(paths), self)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.setFixedWidth(350)
        self.dlg.show()
        self.dlg.setValue(0)
        
        # Model Map
        model_map = {"General": "u2net", "Anime": "isnet-anime"}
        sel_model = model_map.get(self.combo_model.currentText(), "u2net")
        preset = self.presets.get(self.current_preset_name, {})
        
        # Start Worker
        self.worker = BgRemovalWorker(paths, out, sel_model, preset, self)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(lambda cnt: self.on_worker_finished(cnt, out))
        self.worker.error.connect(self.on_worker_error)
        
        self.dlg.canceled.connect(self.worker.stop)
        
        self.worker.start()

    def on_worker_progress(self, i, msg):
        if self.meter: self.meter.set_message(f"{msg}")
        self.dlg.setLabelText(msg)
        self.dlg.setValue(i)

    def on_worker_finished(self, cnt, out_dir):
        self.dlg.close()
        if self.meter: self.meter.set_message(None)
        
        # Update output map
        for p in self.image_paths:
            opath = out_dir / f"{p.stem}_nobg.png"
            if opath.exists():
                self.output_map[p] = opath

        QMessageBox.information(self, tr("msg_done"), f"Processed {cnt} images.\nFolder: {out_dir}")
        if self.list_w.currentRow() >= 0: self._update_prev(self.image_paths[self.list_w.currentRow()])

    def on_worker_error(self, err):
        self.dlg.close()
        if self.meter: self.meter.set_message(None)
        QMessageBox.critical(self, tr("msg_error"), f"BG Removal Failed:\n{err}")

    def show_help(self):
        text = (
            "<h3>LABOKit – Background Remover</h3>"
            "<p>Powered by <b>U^2-Net</b> (Machine Learning).</p>"
            "<hr>"
            "<b>1. Add Images</b><br>"
            "Drag & drop files or use the 'Add Images' button. Supports JPG, PNG, WEBP, BMP.<br><br>"
            "<b>2. Sensitivity Presets</b>"
            "<ul>"
            "<li><b>Standard:</b> Best for general use. Fast & clean edges.</li>"
            "<li><b>Medium:</b> Applies post-processing to smooth rough edges.</li>"
            "<li><b>High:</b> Aggressive alpha matting. Good for hair/fur details but slower.</li>"
            "</ul>"
            "<b>3. Processing</b><br>"
            "Click 'Remove BG (All)' to process the entire list.<br>"
            "Results are saved automatically to the <b>LABOKit_BG</b> folder next to your input files.<br><br>"
        )
        QMessageBox.information(self, "Help – BG Remover", text)

class UpscalerTab(QWidget):
    def __init__(self, meter=None, parent=None):
        super().__init__(parent)
        self.meter = meter
        self.image_paths = []
        self.output_dir = None
        self.output_map = {}
        self.view_path = None
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8,8,8,8); outer.setSpacing(6)
        main = QHBoxLayout(); outer.addLayout(main)
        
        # Left Panel (Controls)
        left = QVBoxLayout(); main.addLayout(left, 1)
        
        # Loaded Images Box
        list_box = QFrame()
        list_box_layout = QVBoxLayout(list_box)
        list_box_layout.setContentsMargins(6, 6, 6, 6)
        list_box_layout.setSpacing(5)
        
        self.list_w = FileDropListWidget()
        self.list_w.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_w.customContextMenuRequested.connect(self.show_list_context_menu)
        self.list_w.files_dropped.connect(self.add_dropped_files)
        self.list_w.currentItemChanged.connect(self.on_item)
        lbl = QLabel(tr("lbl_loaded_up"))
        lbl.setStyleSheet("font-weight: bold; background-color: #e2e7f2; border: 1px solid #cbd2e1; border-radius: 3px; padding: 4px 6px; color: #333d51;")
        list_box_layout.addWidget(lbl)
        list_box_layout.addWidget(self.list_w)
        
        # Buttons (Add/Clear)
        btns = QHBoxLayout()
        b_add = QPushButton(tr("btn_add")); b_add.setIcon(create_plus_icon()); b_add.clicked.connect(self.add_images)
        b_clr = QPushButton(tr("btn_clear")); b_clr.clicked.connect(self.clear_list)
        btns.addWidget(b_add); btns.addWidget(b_clr)
        list_box_layout.addLayout(btns)
        
        left.addWidget(list_box)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("border: none; background-color: #b3bcd1; min-height: 1px; max-height: 1px; margin: 10px 0;")
        left.addWidget(line)

        # Options sidebar
        l_out = QLabel(tr("lbl_out")); l_out.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        left.addWidget(l_out)
        self.out_lbl = QLabel("(auto)"); self.out_lbl.setWordWrap(True)
        self.out_lbl.setStyleSheet("color: #666; margin-bottom: 5px; border: none; background: transparent;")
        left.addWidget(self.out_lbl)

        out_btn_lay = QHBoxLayout()
        out_btn_lay.setSpacing(5)
        b_change = QPushButton(tr("btn_change")); b_change.clicked.connect(self.change_output_folder)
        b_open_out = QPushButton(tr("btn_open_out", "Open Folder")); b_open_out.clicked.connect(self.open_output_folder)
        out_btn_lay.addWidget(b_change)
        out_btn_lay.addWidget(b_open_out)
        left.addLayout(out_btn_lay)
        
        opt_layout = QVBoxLayout()
        opt_layout.setSpacing(5)
        
        l_scale = QLabel(tr("lbl_scale")); l_scale.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        opt_layout.addWidget(l_scale)
        self.combo_s = QComboBox(); self.combo_s.addItems(["2x", "4x"]); self.combo_s.setCurrentText("4x")
        opt_layout.addWidget(self.combo_s)
        
        l_mod = QLabel(tr("lbl_model")); l_mod.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        opt_layout.addWidget(l_mod)
        self.combo_m = QComboBox()
        self.combo_m.addItems([
            "General", 
            "Anime", 
            "General - Performance"
        ])
        opt_layout.addWidget(self.combo_m)
        left.addLayout(opt_layout)

        # Buttons
        left.addSpacing(10)
        b_sel = QPushButton(tr("btn_proc_sel")); b_sel.clicked.connect(self.proc_sel)
        b_all = QPushButton(tr("btn_proc_all")); b_all.clicked.connect(self.proc_all)
        left.addWidget(b_sel)
        left.addWidget(b_all)

        # Right Panel (Preview)
        right = QVBoxLayout(); main.addLayout(right, 3)
        self.preview_widget = ZoomableImageWidget()
        right.addWidget(self.preview_widget)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", IMAGE_FILTER)
        if not files: return
        for f in files:
            p = Path(f)
            if p not in self.image_paths:
                self.image_paths.append(p)
                item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                self.list_w.addItem(item)
        if self.list_w.count()>0: self.list_w.setCurrentRow(0)

    def add_dropped_files(self, files):
        for p in files:
            if p.suffix.lower() in VALID_EXTENSIONS:
                if p not in self.image_paths:
                    self.image_paths.append(p)
                    item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                    self.list_w.addItem(item)
        if self.list_w.count() > 0 and self.list_w.currentRow() < 0:
            self.list_w.setCurrentRow(0)

    def clear_list(self):
        self.image_paths.clear(); self.output_map.clear(); self.list_w.clear()
        self.preview_widget.set_images(None, None)

    def on_item(self, curr, prev):
        if not curr: 
            self.preview_widget.set_images(None, None)
        else: self._update_prev(curr.data(Qt.UserRole))

    def show_list_context_menu(self, pos):
        item = self.list_w.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        action_remove = QAction("Remove", self)
        action_remove.triggered.connect(lambda: self.remove_selected_image(item))
        menu.addAction(action_remove)
        menu.exec(self.list_w.mapToGlobal(pos))

    def remove_selected_image(self, item):
        row = self.list_w.row(item)
        if row >= 0:
            self.list_w.takeItem(row)
            if row < len(self.image_paths):
                path = self.image_paths.pop(row)
                if path in self.output_map:
                    del self.output_map[path]
            # Update preview
            if not self.image_paths:
                self.preview_widget.set_images(None, None)
            elif self.list_w.currentItem():
                self.on_item(self.list_w.currentItem(), None)

    def _update_prev(self, path):
        if path is None:
            self.preview_widget.set_images(None, None)
            return
        self.view_path = path
        out = self.output_map.get(path)
        self.preview_widget.set_images(path, out)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # The preview widget handles fit+update via its own debounce timer


    def ensure_out(self, sample):
        if not self.output_dir:
            self.output_dir = sample.parent / "LABOKit_UP"; self.output_dir.mkdir(exist_ok=True)
            self.out_lbl.setText(f"UPSCALE OUTPUT FOLDER: {self.output_dir}")
            QMessageBox.information(self, "Info", f"Output folder set to:\n{self.output_dir}")
        return self.output_dir
    
    def change_output_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.output_dir = Path(d); self.out_lbl.setText(f"UPSCALER FOLDER: {self.output_dir}")

    def open_output_folder(self):
        d = self.output_dir
        if not d and self.image_paths:
            d = self.image_paths[0].parent / "LABOKit_Upscaled"
        if d and d.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))
        else:
            QMessageBox.information(self, "Info", "Output folder does not exist yet. Process an image first.")

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel: return QMessageBox.information(self, "Info", tr("msg_select"))
        self._run(sel)

    def proc_all(self):
        if not self.image_paths: return QMessageBox.information(self, "Info", tr("msg_add"))
        self._run(self.image_paths)

    def _run(self, paths):
        display_name = self.combo_m.currentText()
        
        # Map Display Name -> Internal Name
        name_map = {
            "General": "realesrgan-x4plus",
            "Anime": "realesrgan-x4plus-anime",
            "General - Performance": "realesr-general-x4v3.pth"
        }
        model_name = name_map.get(display_name, "realesrgan-x4plus")
        
        is_python_mode = model_name.endswith(".pth")

        if not is_python_mode and not REALESRGAN_EXE.exists():
            return QMessageBox.warning(self, "Error", f"Executable not found at:\n{REALESRGAN_EXE}")
        
        out = self.ensure_out(paths[0])
        self.dlg = QProgressDialog("Initializing Upscaler...", "Cancel", 0, len(paths), self)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.setFixedWidth(350)
        self.dlg.show()
        self.dlg.setValue(0)
        
        self.worker = UpscalerWorker(paths, out, model_name, is_python_mode, self)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)
        
        self.dlg.canceled.connect(self.worker.stop)
        
        self.worker.start()

    def on_worker_progress(self, i, msg):
        if self.meter: self.meter.set_message(f"{msg}")
        self.dlg.setLabelText(msg)
        self.dlg.setValue(i)

    def on_worker_finished(self, cnt):
        self.dlg.close()
        if self.meter: self.meter.set_message(None)
        
        # Use the directory the worker actually wrote to
        actual_out_dir = self.worker.out_dir
        
        # Update output map
        for p in self.image_paths:
             opath = actual_out_dir / f"{p.stem}_up4x.png"
             if opath.exists():
                 self.output_map[p] = opath

        QMessageBox.information(self, tr("msg_done"), f"Upscaled {cnt} images.\nFolder: {actual_out_dir}")
        if self.list_w.currentItem(): self.on_item(self.list_w.currentItem(), None)

    def on_worker_error(self, err):
        self.dlg.close()
        if self.meter: self.meter.set_message(None)
        QMessageBox.critical(self, tr("msg_error"), f"Upscale Failed:\n{err}")

    def show_help(self):
        text = (
            "<h3>LABOKit – Upscaler</h3>"
            "<p>Powered by <b>Real-ESRGAN</b> (NCNN Vulkan).</p>"
            "<hr>"
            "<b>1. Add Images</b><br>"
            "Load low-resolution images you want to enhance.<br><br>"
            "<b>2. Model Selection</b>"
            "<ul>"
            "<li><b>realesrgan-x4plus:</b> Best for photos, realistic textures, and general images.</li>"
            "<li><b>realesrgan-x4plus-anime:</b> Optimized for 2D illustration, anime, and line art (faster & sharper lines).</li>"
            "<li><b>realesr-general-x4v3:</b> Optimized for Low-End/Non Vulkan/Integrated GPU PC.</li>"
            "</ul>"
            "<b>3. Scale Factor</b><br>"
            "Choose <b>4x</b> for maximum detail or <b>2x</b> for a quicker resize.<br><br>"
            "<b>⚠️ Hardware Note:</b><br>"
            "This feature requires a Vulkan-compatible GPU. On first run, it might take a few seconds to initialize."
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

        self.title_lbl = QLabel("LABOKit 3.2")
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
        import urllib.request
        import json
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
        import urllib.request
        import json
        import base64
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
        self.setWindowTitle("LABOKit 3.2")
        
        screen = QApplication.primaryScreen().geometry()
        screen_height = screen.height()
        base_height_ref = 1440
        base_w_ref = 1200
        base_h_ref = 800
        scale_factor = screen_height / base_height_ref
        new_w = int(base_w_ref * scale_factor)
        new_h = int(base_h_ref * scale_factor)
        final_w = max(900, new_w) 
        final_h = max(600, new_h)
        self.setFixedSize(final_w, final_h)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        self.central_container = QWidget()
        self.setCentralWidget(self.central_container)
        
        self.outer_layout = QVBoxLayout(self.central_container)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet("""
            #MainFrame {
                background-color: #e9edf5;
                border-radius: 10px; 
                border: 1px solid #999; 
            }
        """)
        
        self.outer_layout.addWidget(self.main_frame)
        
        self.main_layout = QVBoxLayout(self.main_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.custom_title_bar = CustomTitleBar(self)
        self.main_layout.addWidget(self.custom_title_bar)

        # Global Meter (Bottom)
        self.meter = DivergenceMeter()

        self.tabs = QTabWidget()
        self.bg_tab = BgRemoverTab(meter=self.meter, parent=self)
        self.up_tab = UpscalerTab(meter=self.meter, parent=self)
        self.tabs.addTab(self.bg_tab, tr("tab_bg"))
        self.tabs.addTab(self.up_tab, tr("tab_up"))
        
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.meter) # Added global meter
        
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.purge_ai_models)
        self.inactivity_timer.start(300000) # 5 mins

        self.loaded_plugins = []
        self._setup_menu()
        self._load_plugins()
        self.check_app_updates()
        self.check_plugin_updates()

    def purge_ai_models(self):
        global GLOBAL_REMBG_SESSION_CACHE, GLOBAL_UPSAMPLER_CACHE
        purged = False
        if GLOBAL_REMBG_SESSION_CACHE or GLOBAL_UPSAMPLER_CACHE:
            GLOBAL_REMBG_SESSION_CACHE.clear()
            GLOBAL_UPSAMPLER_CACHE.clear()
            import gc
            gc.collect()
            purged = True
        
        # Use status_label directly (not set_message) so we don't trigger the
        # fast-animation mode — this is an informational notice, not active work
        if purged and hasattr(self, 'meter'):
            self.meter.status_label.setText("➤ AI Models Unloaded (RAM freed)")
            self.meter.status_label.setStyleSheet(
                "background-color: #fef3c7; border: 1px solid #f59e0b; color: #92400e;"
            )
            self._purge_notice_active = True

    def reset_inactivity(self):
        if hasattr(self, 'inactivity_timer'):
            self.inactivity_timer.start(300000)
            # Clear purge notice on next activity
            if getattr(self, '_purge_notice_active', False) and hasattr(self, 'meter'):
                self.meter.status_label.setStyleSheet("")
                self._purge_notice_active = False


    def resizeEvent(self, event):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        
        super().resizeEvent(event)
    def _load_plugins(self):
        import importlib.util
        import importlib.machinery
        if not PLUGIN_DIR.exists(): PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        
        # Remove old tabs
        for p in self.loaded_plugins:
            if p.get("tab"): 
                idx = self.tabs.indexOf(p["tab"])
                if idx != -1: self.tabs.removeTab(idx)
        self.loaded_plugins.clear()

        # Load new
        for f in PLUGIN_DIR.glob("*.kit"):
            try:
                mod_name = f"plugin_{f.stem}"
                loader = importlib.machinery.SourceFileLoader(mod_name, str(f))
                spec = importlib.util.spec_from_file_location(mod_name, str(f), loader=loader)
                mod = importlib.util.module_from_spec(spec)
                mod.tr = tr
                spec.loader.exec_module(mod)
                
                if hasattr(mod, "create_tab"):
                    mod.tr = tr
                    tab = mod.create_tab(self)
                    # Pass meter if supported
                    if hasattr(tab, "set_meter"):
                        tab.set_meter(self.meter)
                    
                    name = getattr(mod, "PLUGIN_NAME", f.stem)
                    self.tabs.addTab(tab, name)
                    self.loaded_plugins.append({"name": name, "tab": tab, "help": getattr(mod, "HELP_TEXT", "")})
            except Exception as e: print(f"Plugin Error {f.name}: {e}")

        self._refresh_plugin_menu()

        # Check for updates
        self.updater = AppUpdater()
        self.updater.update_available.connect(self.on_update_available)
        self.updater.start()

    def _refresh_plugin_menu(self):
        if hasattr(self, "menu_plugins"):
            self.menu_plugins.clear()
            if not self.loaded_plugins:
                action = QAction("(No Plugins)", self)
                action.setEnabled(False)
                self.menu_plugins.addAction(action)
            else:
                for p in self.loaded_plugins:
                    action = QAction(p["name"], self)
                    # When clicked, switch to that tab
                    action.triggered.connect(lambda checked, t=p["tab"]: self.tabs.setCurrentWidget(t))
                    self.menu_plugins.addAction(action)

    def on_update_available(self, version, download_url, changelog):
        msg = QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setText(f"A new version of LABOKit (v{version}) is available!\n\nChangelog:\n{changelog}\n\nWould you like to download and install it now?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if msg.exec() == QMessageBox.Yes:
            self.apply_update(download_url)
            
    def apply_update(self, url):
        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()
        
        self.downloader = PatchDownloader(url)
        self.downloader.progress.connect(self.progress_dialog.setValue)
        self.downloader.error.connect(lambda e: QMessageBox.critical(self, "Update Failed", str(e)))
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.start()
        
    def on_download_finished(self, patch_path):
        import tempfile
        import subprocess
        
        patch_path_obj = Path(patch_path)
        bat_path = Path(tempfile.gettempdir()) / "labokit_updater.bat"
        target_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        
        if patch_path_obj.suffix.lower() == '.exe':
            bat_content = f"""@echo off
timeout /t 2 /nobreak > NUL
echo Installing Update...
start /wait "" "{patch_path_obj}" /SILENT /DIR="{target_dir}"
start "" "{target_dir}\\LABOKit.exe"
del "{patch_path_obj}"
del "%~f0"
"""
        else:
            bat_content = f"""@echo off
timeout /t 2 /nobreak > NUL
echo Updating LABOKit...
tar -xf "{patch_path_obj}" -C "{target_dir}"
if %errorlevel% neq 0 (
    echo Extraction failed!
    pause
    exit /b %errorlevel%
)
start "" "{target_dir}\\LABOKit.exe"
del "{patch_path_obj}"
del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
            
        QMessageBox.information(self, "Update Ready", "LABOKit will now close to apply the update.")
        
        subprocess.Popen(["cmd.exe", "/c", str(bat_path)], creationflags=subprocess.CREATE_NO_WINDOW)
        QApplication.quit()
        
    def populate_plugin_menu(self):
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

        conf = mb.addMenu(tr("menu_config"))
        conf.addAction("Load Plugin (.kit)...", self.load_plugin_file)
        conf.addAction("Open Plugins Folder", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(PLUGIN_DIR))))
        
        # Language Submenu
        lang_menu = conf.addMenu("Language")
        lang_menu.addAction("English", lambda: self.switch_language("en"))
        lang_menu.addAction("日本語", lambda: self.switch_language("ja"))
        lang_menu.addAction("Bahasa Indonesia", lambda: self.switch_language("id"))

        help = mb.addMenu(tr("menu_help"))
        help.addAction("BG Remover Help", self.bg_tab.show_help)
        help.addAction("Upscaler Help", self.up_tab.show_help)
        help.addSeparator()
        help.addAction("Licenses / NOTICE", self.show_notice)
        self.menu_plugins = help.addMenu(tr("menu_plugins"))

        supp = mb.addMenu(tr("menu_support"))
        supp.addAction("Get Plugins (Trakteer ID)", lambda: self.open_url("https://trakteer.id/kano-bbif7/reward/labokit-advanced-plugins-m84J6"))
        supp.addAction("Get Plugins (Ko-fi)", lambda: self.open_url("https://ko-fi.com/s/a367e473fe"))

    def switch_language(self, lang):
        set_language(lang)
        QMessageBox.information(self, "Restart Required", "Please restart LABOKit to apply language changes.\n\n言語変更を適用するには再起動してください。\nSilakan restart untuk menerapkan bahasa.")

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
        import requests
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

class StartupWorker(QThread):
    def run(self):
        deploy_assets()

class UpscalerWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, paths, out_dir, model_name, is_python_mode, parent=None):
        super().__init__(parent)
        self.paths = paths
        self.out_dir = out_dir
        self.model_name = model_name
        self.is_python_mode = is_python_mode
        self.is_running = True

    def run(self):
        try:
            upsampler = None
            if self.is_python_mode:
                self.progress.emit(0, "Initializing AI Engine...")
                upsampler = self.init_upsampler(self.model_name)
                if not upsampler:
                    self.error.emit("Failed to initialize upsampler.")
                    return

            cnt = 0
            for i, p in enumerate(self.paths):
                if not self.is_running: break
                
                self.progress.emit(i, f"Processing {p.name}...")
                
                try:
                    opath = self.out_dir / f"{p.stem}_up4x.png"
                    success = False

                    if self.is_python_mode:
                        success = self.run_python_inference(p, opath, upsampler)
                    else:
                        cmd = [
                            str(REALESRGAN_EXE), 
                            "-i", str(p), 
                            "-o", str(opath), 
                            "-n", self.model_name, 
                            "-s", "4"
                        ]
                        flags = subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0
                        subprocess.run(cmd, capture_output=True, creationflags=flags, cwd=str(REALESRGAN_DIR))
                        success = opath.exists()

                    if success:
                        cnt += 1
                        
                except Exception as e:
                    print(f"Upscale Error: {e}")
            
            self.finished.emit(cnt)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def init_upsampler(self, model_name):
        global GLOBAL_UPSAMPLER_CACHE
        if model_name in GLOBAL_UPSAMPLER_CACHE:
            return GLOBAL_UPSAMPLER_CACHE[model_name]

        ai = load_ai_engine()
        if not ai:
            return None

        # Unpack
        SRVGGNetCompact = ai["SRVGGNetCompact"]
        RealESRGANer = ai["RealESRGANer"]

        try:
            model_path = REALESRGAN_DIR / "models" / model_name 
            if not model_path.exists():
                model_path = MODEL_DIR / model_name
                if not model_path.exists(): return None

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
            GLOBAL_UPSAMPLER_CACHE[model_name] = upsampler
            return upsampler

        except Exception as e:
            print(f"Error: {e}")
            import traceback; traceback.print_exc()
            return None

    def run_python_inference(self, img_path, out_path, upsampler):
        ai = load_ai_engine()
        if not ai: return False
        
        cv2 = ai["cv2"]

        try:
            img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
            output, _ = upsampler.enhance(img, outscale=4)
            cv2.imwrite(str(out_path), output)
            return True

        except Exception as e:
            print(f"Error: {e}")
            import traceback; traceback.print_exc()
            return False

    def stop(self):
        self.is_running = False

class BgRemovalWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, paths, out_dir, model_name, preset, parent=None):
        super().__init__(parent)
        self.paths = paths
        self.out_dir = out_dir
        self.model_name = model_name
        self.preset = preset
        self.is_running = True

    def run(self):
        try:
            import rembg
            from rembg import new_session
            
            # Create session (with cache lookup)
            global GLOBAL_REMBG_SESSION_CACHE
            if self.model_name in GLOBAL_REMBG_SESSION_CACHE:
                session = GLOBAL_REMBG_SESSION_CACHE[self.model_name]
            else:
                session = new_session(model_name=self.model_name)
                GLOBAL_REMBG_SESSION_CACHE[self.model_name] = session
            
            cnt = 0
            for i, p in enumerate(self.paths):
                if not self.is_running: break
                
                self.progress.emit(i, f"Processing {p.name}...")
                
                try:
                    res = rembg.remove(p.read_bytes(), session=session, **self.preset)
                    opath = self.out_dir / f"{p.stem}_nobg.png"
                    opath.write_bytes(res)
                    cnt += 1
                except Exception as e:
                    print(f"Error processing {p.name}: {e}")
            
            self.finished.emit(cnt)
            
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False

class InactivityFilter(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._last_reset_ms = 0  # Cooldown to avoid resetting on every mouse-move

    def eventFilter(self, obj, event):
        if event.type() in (event.Type.MouseMove, event.Type.MouseButtonPress, event.Type.KeyPress):
            # Throttle: only call reset_inactivity() at most every 500ms
            now = QDateTime.currentMSecsSinceEpoch()
            if now - self._last_reset_ms > 500:
                self._last_reset_ms = now
                self.main_window.reset_inactivity()
        return False



def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    import traceback
    from datetime import datetime
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        with open("crash_log.txt", "a") as f:
            f.write(f"\n--- Crash at {datetime.now()} ---\n")
            f.write(err_msg)
    except: pass
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("LABOKit encountered a critical error.")
        msg.setDetailedText(err_msg)
        msg.setWindowTitle("Fatal Error")
        msg.exec()
    except: pass

def main():
    sys.excepthook = global_exception_handler
    
    # --- Windows Taskbar Icon Fix ---
    try:
        import ctypes
        myappid = 'wagakano.labokit.advanced.3.2' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
        
    app = QApplication(sys.argv)
    app.setApplicationName("LABOKit Advanced")
    if ICON_PATH.exists(): app.setWindowIcon(QIcon(str(ICON_PATH)))
    default_font = QFont("Consolas", 9)
    app.setFont(default_font)

    # Revert to Qt Splash Screen
    splash_img_path = INTERNAL_DIR / "splash.png"
    pix = QPixmap(str(splash_img_path)) if splash_img_path.exists() else QPixmap(400,100)
    if not splash_img_path.exists(): pix.fill(Qt.white)
    
    splash = QSplashScreen(pix.scaledToWidth(400, Qt.SmoothTransformation), Qt.WindowStaysOnTopHint)
    splash.show(); app.processEvents()

    class CursorFilter(QObject):
        def eventFilter(self, obj, event):
            if event.type() == QEvent.Enter:
                if isinstance(obj, QPushButton):
                    obj.setCursor(Qt.PointingHandCursor)
            return super().eventFilter(obj, event)

    cursor_filter = CursorFilter()
    app.installEventFilter(cursor_filter)

    # Worker Setup
    worker = StartupWorker()
    
    def on_complete():
        # Warmup
        try:
            # Style
            app.setStyleSheet("""
                QMessageBox { font-family: "Consolas"; }
                QMainWindow { background-color: #e9edf5; }
                QTabWidget::pane { border: 1px solid #b3bcd1; border-radius: 4px; top: -1px; }
                QTabBar::tab { background-color: #dde4f5; border: 1px solid #b3bcd1; padding: 4px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #1c2333; }
                QTabBar::tab:selected { background-color: #f5f7fb; }
                QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #e0e5ec); border: 1px solid #a3b0c2; border-radius: 4px; padding: 6px; color: #1c2333; }
                QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #d0d8e6); border: 1px solid #8294aa; }
                QPushButton:pressed { background-color: #d0d8e6; }
                QListWidget { background-color: #ffffff; border: 1px solid #b3bcd1; border-radius: 4px; outline: 0; padding: 4px; }
                QListWidget::item:selected { background-color: #cce0ff; color: #1c2333; border-radius: 3px; }
                QListWidget::item:hover { background-color: #e6f0ff; border-radius: 3px; }
                QComboBox { border: 1px solid #b3bcd1; border-radius: 4px; padding: 4px 8px; background-color: #ffffff; }
                QComboBox::drop-down { border-left: 1px solid #b3bcd1; }
                QScrollBar:vertical { background: #e9edf5; width: 12px; margin: 0px 0px 0px 0px; border-radius: 6px; }
                QScrollBar::handle:vertical { background: #b3bcd1; min-height: 20px; border-radius: 6px; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                QLabel#SectionHeader { background-color: #dce3f0; border-radius: 4px; padding: 4px; }
                QLabel { padding: 2px; }
                QMenuBar { background-color: #dbe2f2; color: #1c2333; border-bottom: 1px solid #b3bcd1; }
                QMenuBar::item { background: transparent; padding: 3px 8px; color: #1c2333; }
                QMenuBar::item:selected { background-color: #cfe2ff; color: #101522; }
                QMenu { background-color: #f7f9fc; border: 1px solid #b3bcd1; }
                QMenu::item { padding: 4px 20px; color: #1c2333; }
                QListWidget { background-color: #f7f9fc; border: 1px solid #b3bcd1; border-radius: 4px; }
                QListWidget::item { padding: 4px 6px; color: #1c2333; }
                QListWidget::item:selected { color: #102039; }
                QFrame { background-color: #f5f7fb; border: 1px solid #b3bcd1; border-radius: 6px; }
                #PixelBar { background-color: #dde4f5; border-radius: 6px; border: 1px solid #b3bcd1; }
                #PixelBar QLabel { color: #4b556b; }
                QLabel { color: #1c2333; }
                QPushButton { color: #1c2333; background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #d8dfee); border: 1px solid #9ca7c2; border-radius: 5px; padding: 4px 12px; }
                QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #e6ecf7); }
                QPushButton:pressed { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cfd6e8, stop:1 #b0bdd7); }
                QProgressDialog { background-color: #f5f7fb; }
                QDialog, QMessageBox { background-color: #f5f7fb; }
                QDialog QLabel, QMessageBox QLabel { color: #1c2333; }
                QDialog QPushButton, QMessageBox QPushButton { color: #1c2333; background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #d8dfee); border: 1px solid #9ca7c2; border-radius: 5px; padding: 4px 12px; }
                QPlainTextEdit { background-color: #f5f7fb; color: #1c2333; border: 1px solid #b3bcd1; border-radius: 4px; }
                QComboBox { background-color: #f7f9fc; border: 1px solid #b3bcd1; border-radius: 4px; padding: 2px 6px; color: #1c2333; }
                QComboBox QAbstractItemView { background-color: #ffffff; border: 1px solid #b3bcd1; selection-background-color: #cfe2ff; color: #1c2333; selection-color: #101522; }
            """)

            # Attach to app to prevent GC
            app.main_window = LABOKitMainWindow()
            
            # Install inactivity filter
            app.inactivity_filter = InactivityFilter(app.main_window)
            app.installEventFilter(app.inactivity_filter)

            app.main_window.show()
            splash.finish(app.main_window)
        except Exception as e:
            print(f"Error during startup: {e}")

    worker.finished.connect(lambda: QTimer.singleShot(0, app, on_complete))
    worker.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
