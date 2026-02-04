
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
# cv2 removed from here
from pathlib import Path
# PIL removed from here (unused)
from packaging import version
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    QScrollArea, QMenu
)
from ui_shared import FileDropListWidget, ZoomableImageWidget, DivergenceMeter, create_plus_icon, VALID_EXTENSIONS

IMAGE_FILTER = (
    "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.gif "
    "*.JPG *.JPEG *.PNG *.BMP *.TIF *.TIFF *.WEBP *.GIF)"
)

# --- LAZY LOADING AI ENGINE ---
AI_MODULES = None

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
        self.list_w = FileDropListWidget()
        self.list_w.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_w.customContextMenuRequested.connect(self.show_list_context_menu)
        self.list_w.files_dropped.connect(self.add_dropped_files)
        self.list_w.currentRowChanged.connect(self.on_file_selected)
        lbl = QLabel("LOADED IMAGES (BG Remover):"); lbl.setStyleSheet("border:none; background:transparent;")
        left.addWidget(lbl); left.addWidget(self.list_w)
        # Buttons (Add/Clear) moved to bottom area
        btns = QHBoxLayout()
        b_add = QPushButton("Add Images…"); b_add.setIcon(create_plus_icon()); b_add.clicked.connect(self.add_images)
        b_clr = QPushButton("Clear List"); b_clr.clicked.connect(self.clear_list)
        btns.addWidget(b_add); btns.addWidget(b_clr); left.addLayout(btns)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("border: none; background-color: #b3bcd1; min-height: 1px; max-height: 1px; margin: 10px 0;")
        left.addWidget(line)

        # Options in sidebar
        l_out = QLabel("Output Folder:"); l_out.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        left.addWidget(l_out)
        self.out_lbl = QLabel("(auto)"); self.out_lbl.setWordWrap(True)
        self.out_lbl.setStyleSheet("color: #666; margin-bottom: 5px; border: none; background: transparent;")
        left.addWidget(self.out_lbl)

        b_change = QPushButton("Change Folder"); b_change.clicked.connect(self.change_output_folder)
        left.addWidget(b_change)
        
        pres_row = QVBoxLayout() 
        pres_row.setSpacing(5)

        l_mod = QLabel("Model:"); l_mod.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        pres_row.addWidget(l_mod)
        self.combo_model = QComboBox()
        self.combo_model.addItems(["General", "Anime"])
        pres_row.addWidget(self.combo_model)

        l_sen = QLabel("Sensitivity:"); l_sen.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        pres_row.addWidget(l_sen)
        self.combo = QComboBox(); self.combo.addItems(self.presets.keys())
        self.combo.currentTextChanged.connect(self.on_preset)
        pres_row.addWidget(self.combo)
        left.addLayout(pres_row)

        left.addSpacing(10)
        b_sel = QPushButton("Remove BG (Selected)"); b_sel.clicked.connect(self.proc_sel)
        b_all = QPushButton("Remove BG (All)"); b_all.clicked.connect(self.proc_all)
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
        self._update_prev(None)

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.image_paths): self._update_prev(None)
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
                self._update_prev(None)
            elif row < len(self.image_paths):
                self.list_w.setCurrentRow(row) # Select next
            else:
                self.list_w.setCurrentRow(len(self.image_paths) - 1) # Select last

    def _update_prev(self, path):
        out = self.output_map.get(path)
        self.preview_widget.set_images(path, out)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        r = self.list_w.currentRow()
        if r >= 0: self._update_prev(self.image_paths[r])

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

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel: return QMessageBox.information(self, "Info", "Select images first.")
        self._run(sel)

    def proc_all(self):
        if not self.image_paths: return QMessageBox.information(self, "Info", "Add images first.")
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
        
        # Collect output paths as we go? 
        # Actually the worker writes files. We need to update self.output_map 
        # But we can do that at the end or if we pass signals. 
        # For now, let's update map at the end or assume filenames.
        # Ideally we'd pass the result path back.
        # But sticking to the pattern:
        # We can reconstruct the path: out_dir / {stem}_nobg.png
        # Let's verify files at the end.

    def on_worker_finished(self, cnt, out_dir):
        self.dlg.close()
        if self.meter: self.meter.set_message(None)
        
        # Update output map
        for p in self.image_paths:
            opath = out_dir / f"{p.stem}_nobg.png"
            if opath.exists():
                self.output_map[p] = opath

        QMessageBox.information(self, "Done", f"Processed {cnt} images.\nFolder: {out_dir}")
        if self.list_w.currentRow() >= 0: self._update_prev(self.image_paths[self.list_w.currentRow()])

    def on_worker_error(self, err):
        self.dlg.close()
        if self.meter: self.meter.set_message(None)
        QMessageBox.critical(self, "Error", f"BG Removal Failed:\n{err}")

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
        self.list_w = FileDropListWidget()
        self.list_w.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_w.customContextMenuRequested.connect(self.show_list_context_menu)
        self.list_w.files_dropped.connect(self.add_dropped_files)
        self.list_w.currentItemChanged.connect(self.on_item)
        lbl = QLabel("LOADED IMAGES (Upscaler):"); lbl.setStyleSheet("border:none; background:transparent;")
        left.addWidget(lbl); left.addWidget(self.list_w)
        
        # Buttons
        btns = QHBoxLayout()
        b_add = QPushButton("Add Images…"); b_add.setIcon(create_plus_icon()); b_add.clicked.connect(self.add_images)
        b_clr = QPushButton("Clear List"); b_clr.clicked.connect(self.clear_list)
        btns.addWidget(b_add); btns.addWidget(b_clr); left.addLayout(btns)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("border: none; background-color: #b3bcd1; min-height: 1px; max-height: 1px; margin: 10px 0;")
        left.addWidget(line)

        # Options sidebar
        l_out = QLabel("Output Folder:"); l_out.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        left.addWidget(l_out)
        self.out_lbl = QLabel("(auto)"); self.out_lbl.setWordWrap(True)
        self.out_lbl.setStyleSheet("color: #666; margin-bottom: 5px; border: none; background: transparent;")
        left.addWidget(self.out_lbl)

        b_change = QPushButton("Change Folder"); b_change.clicked.connect(self.change_output_folder)
        left.addWidget(b_change)
        
        opt_layout = QVBoxLayout()
        opt_layout.setSpacing(5)
        
        l_scale = QLabel("Scale:"); l_scale.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        opt_layout.addWidget(l_scale)
        self.combo_s = QComboBox(); self.combo_s.addItems(["2x", "4x"]); self.combo_s.setCurrentText("4x")
        opt_layout.addWidget(self.combo_s)
        
        l_mod = QLabel("Model:"); l_mod.setStyleSheet("font-weight: bold; border: none; background: transparent;")
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
        b_sel = QPushButton("Upscale (Selected)"); b_sel.clicked.connect(self.proc_sel)
        b_all = QPushButton("Upscale (All)"); b_all.clicked.connect(self.proc_all)
        left.addWidget(b_sel)
        left.addWidget(b_all)

        # Right Panel (Preview)
        right = QVBoxLayout(); main.addLayout(right, 3)
        self.preview_widget = ZoomableImageWidget()
        right.addWidget(self.preview_widget)

    def init_upsampler(self, model_name):
        ai = load_ai_engine()
        if not ai:
            QMessageBox.critical(self, "Error", "(torch/basicsr/realesrgan) is not ready.")
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
        self._update_prev(None)

    def on_item(self, curr, prev):
        if not curr: self._update_prev(None)
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
                self._update_prev(None)
            elif self.list_w.currentItem():
                self.on_item(self.list_w.currentItem(), None)

    def _update_prev(self, path):
        self.view_path = path
        out = self.output_map.get(path)
        self.preview_widget.set_images(path, out)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.view_path: self._update_prev(self.view_path)

    def ensure_out(self, sample):
        if not self.output_dir:
            self.output_dir = sample.parent / "LABOKit_UP"; self.output_dir.mkdir(exist_ok=True)
            self.out_lbl.setText(f"UPSCALE OUTPUT FOLDER: {self.output_dir}")
            QMessageBox.information(self, "Info", f"Output folder set to:\n{self.output_dir}")
        return self.output_dir
    
    def change_output_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.output_dir = Path(d); self.out_lbl.setText(f"UPSCALE OUTPUT FOLDER: {self.output_dir}")

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel: return QMessageBox.information(self, "Info", "Select images first.")
        self._run(sel)

    def proc_all(self):
        if not self.image_paths: return QMessageBox.information(self, "Info", "Add images first.")
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
        dlg = QProgressDialog("Upscaling...", "Cancel", 0, len(paths), self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setFixedWidth(350)
        dlg.show()
        dlg.setValue(0)
        QApplication.processEvents()
        
        cnt = 0
        target_scale = 4 # Default model scale

        upsampler = None
        if is_python_mode:
            upsampler = self.init_upsampler(model_name)
            if not upsampler:
                dlg.close()
                return

        for i, p in enumerate(paths):
            if dlg.wasCanceled(): break
            if self.meter: self.meter.set_message(f"Processing {i+1}/{len(paths)}")
            dlg.setLabelText(f"Processing {p.name}...")
            QApplication.processEvents()
            
            try:
                opath = out / f"{p.stem}_up4x.png"
                success = False

                if is_python_mode:
                    success = self.run_python_inference(p, opath, upsampler)
                
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
        if self.meter: self.meter.set_message(None)
        QMessageBox.information(self, "Done", f"Upscaled {cnt} images.\nFolder: {out}")
        if self.list_w.currentItem(): self.on_item(self.list_w.currentItem(), None)

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
        self.tabs.addTab(self.bg_tab, "BG Remover")
        self.tabs.addTab(self.up_tab, "Upscaler")
        
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.meter) # Added global meter
        self.main_layout.addSpacing(5) 

        self.loaded_plugins = []
        self._setup_menu()
        self._load_plugins()
        self.check_app_updates()
        self.check_plugin_updates()

    def resizeEvent(self, event):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        
        super().resizeEvent(event)
    def _load_plugins(self):
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
                spec.loader.exec_module(mod)
                
                if hasattr(mod, "create_tab"):
                    tab = mod.create_tab(self)
                    # Pass meter if supported
                    if hasattr(tab, "set_meter"):
                        tab.set_meter(self.meter)
                    
                    name = getattr(mod, "PLUGIN_NAME", f.stem)
                    self.tabs.addTab(tab, name)
                    self.loaded_plugins.append({"name": name, "tab": tab, "help": getattr(mod, "HELP_TEXT", "")})
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

        conf = mb.addMenu("&Config")
        conf.addAction("Load Plugin (.kit)...", self.load_plugin_file)
        conf.addAction("Open Plugins Folder", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(PLUGIN_DIR))))

        help = mb.addMenu("&Help")
        help.addAction("BG Remover Help", self.bg_tab.show_help)
        help.addAction("Upscaler Help", self.up_tab.show_help)
        help.addSeparator()
        help.addAction("Licenses / NOTICE", self.show_notice)
        self.menu_plugins = help.addMenu("Plugins")

        supp = mb.addMenu("♥ Support")
        supp.addAction("Get Plugins (Trakteer ID)", lambda: self.open_url("https://trakteer.id/kano-bbif7/reward/labokit-advanced-plugins-m84J6"))
        supp.addAction("Get Plugins (Ko-fi)", lambda: self.open_url("https://ko-fi.com/s/a367e473fe"))

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

class StartupWorker(QThread):
    def run(self):
        deploy_assets()

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
            
            # Create session
            session = new_session(model_name=self.model_name)
            
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

    # Worker Setup
    worker = StartupWorker()
    
    def on_complete():
        # Warmup
        try:
            # Style
            app.setStyleSheet("""
                QMainWindow { background-color: #e9edf5; }
                QTabWidget::pane { border: 1px solid #b3bcd1; border-radius: 4px; top: -1px; }
                QTabBar::tab { background-color: #dde4f5; border: 1px solid #b3bcd1; padding: 4px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #1c2333; }
                QTabBar::tab:selected { background-color: #f5f7fb; }
                QMenuBar { background-color: #dbe2f2; color: #1c2333; border-bottom: 1px solid #b3bcd1; }
                QMenuBar::item { background: transparent; padding: 3px 8px; color: #1c2333; }
                QMenuBar::item:selected { background-color: #cfe2ff; color: #101522; }
                QMenu { background-color: #f7f9fc; border: 1px solid #b3bcd1; }
                QMenu::item { padding: 4px 20px; color: #1c2333; }
                QMenu::item:selected { background-color: #cfe2ff; color: #101522; }
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
            app.main_window.show()
            splash.finish(app.main_window)
        except Exception as e:
            print(f"Error during startup: {e}")

    worker.finished.connect(on_complete, Qt.QueuedConnection)
    worker.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
