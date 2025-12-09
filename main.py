import importlib.machinery
import importlib.util
import os
import random
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

# --- PATH & ASSETS SETUP ---
# 1. Internal Path (Source files inside EXE/Build)
INTERNAL_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

# 2. Persistent Path (cross-platform)
def get_app_data_dir(app_name="LABOKit"):
    system = platform.system().lower()

    # Windows
    if system == "windows":
        base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / app_name
        return Path.home() / "AppData" / "Roaming" / app_name  # fallback

    # macOS
    if system == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name

    # Linux / other unix
    base = os.getenv("XDG_DATA_HOME")
    if base:
        return Path(base) / app_name
    return Path.home() / ".local" / "share" / app_name


APP_DATA = get_app_data_dir()
APP_DATA.mkdir(parents=True, exist_ok=True)

MODEL_DIR = APP_DATA / "models"
REALESRGAN_DIR = APP_DATA / "realesrgan"
PLUGIN_DIR = APP_DATA / "plugins"
FFMPEG_DIR = APP_DATA / "ffmpeg"

# Setup Environment Variables
os.environ["U2NET_HOME"] = str(MODEL_DIR)
# Real-ESRGAN executable (cross-platform name)
if sys.platform == "win32":
    REALESRGAN_EXE = REALESRGAN_DIR / "realesrgan-ncnn-vulkan.exe"
else:
    REALESRGAN_EXE = REALESRGAN_DIR / "realesrgan-ncnn-vulkan"

# Icon & Assets
ICON_PATH = INTERNAL_DIR / "labokit.ico"
remove = None

# --- IMPORTS ---
from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QFileDialog,
    QMessageBox, QProgressDialog, QFrame, QComboBox, QTabWidget,
    QDialog, QPlainTextEdit, QSplashScreen
)

IMAGE_FILTER = (
    "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.gif "
    "*.JPG *.JPEG *.PNG *.BMP *.TIF *.TIFF *.WEBP *.GIF)"
)

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
    "High": {
        "alpha_matting": True,
        "alpha_matting_foreground_threshold": 240,
        "alpha_matting_background_threshold": 10,
        "alpha_matting_erode_structure_size": 10,
        "alpha_matting_base_size": 1000,
        "post_process_mask": True,
    },
}
DEFAULT_PRESET_NAME = "Standard"


# --- SMART DEPLOYMENT (SILENT) ---
def deploy_assets():
    """Copy assets from EXE to AppData on first run (Silent Mode)"""

    # 1. Models
    if not MODEL_DIR.exists():
        try:
            shutil.copytree(INTERNAL_DIR / "models", MODEL_DIR)
        except Exception as e:
            print(f"Model deploy error: {e}")

    # 2. Real-ESRGAN
    if not REALESRGAN_DIR.exists():
        try:
            shutil.copytree(INTERNAL_DIR / "realesrgan", REALESRGAN_DIR)
        except Exception as e:
            print(f"Tool deploy error: {e}")

    # 3. FFMPEG
    if not FFMPEG_DIR.exists():
        try:
            shutil.copytree(INTERNAL_DIR / "ffmpeg", FFMPEG_DIR)
        except Exception as e:
            print(f"FFmpeg deploy error: {e}")

    # 4. Plugins Folder
    if not PLUGIN_DIR.exists():
        PLUGIN_DIR.mkdir(exist_ok=True)
        # Copy built-in plugins if available
        internal_plugins = INTERNAL_DIR / "plugins"
        if internal_plugins.exists():
            for item in internal_plugins.glob("*.kit"):
                try:
                    shutil.copy2(item, PLUGIN_DIR / item.name)
                except:
                    pass


# ==========================================
# TABS
# ==========================================


class BgRemoverTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_paths = []
        self.output_dir = None
        self.output_map = {}
        self.current_preset_name = DEFAULT_PRESET_NAME
        self.presets = BG_PRESETS
        self.pixel_labels = []
        self._running_index = 0
        self._setup_ui()
        self._init_running_text()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)
        main = QHBoxLayout()
        outer.addLayout(main)

        # Left Panel
        left = QVBoxLayout()
        main.addLayout(left, 1)
        self.list_w = QListWidget()
        self.list_w.currentRowChanged.connect(self.on_file_selected)
        lbl = QLabel("LOADED IMAGES (BG Remover):")
        lbl.setStyleSheet("border:none; background:transparent;")
        left.addWidget(lbl)
        left.addWidget(self.list_w)

        btns = QHBoxLayout()
        b_add = QPushButton("Add Images…")
        b_add.clicked.connect(self.add_images)
        b_clr = QPushButton("Clear List")
        b_clr.clicked.connect(self.clear_list)
        btns.addWidget(b_add)
        btns.addWidget(b_clr)
        left.addLayout(btns)

        # Right Panel
        right = QVBoxLayout()
        main.addLayout(right, 3)
        self.out_lbl = QLabel("BG OUTPUT FOLDER: (auto)")
        self.out_lbl.setWordWrap(True)
        right.addWidget(self.out_lbl)

        # Previews
        prev = QHBoxLayout()
        right.addLayout(prev, 5)
        self.lbl_orig = self._create_box("Original")
        self.lbl_res = self._create_box("Result (Background Removed)")
        prev.addWidget(self.lbl_orig)
        prev.addWidget(self.lbl_res)

        # Controls
        right.addSpacing(6)
        pres_row = QHBoxLayout()
        pres_row.addWidget(QLabel("Sensitivity:"))
        self.combo = QComboBox()
        self.combo.addItems(self.presets.keys())
        self.combo.currentTextChanged.connect(self.on_preset)
        pres_row.addWidget(self.combo)
        right.addLayout(pres_row)

        right.addSpacing(10)
        proc_row = QHBoxLayout()
        b_sel = QPushButton("Remove BG (Selected)")
        b_sel.clicked.connect(self.proc_sel)
        b_all = QPushButton("Remove BG (All)")
        b_all.clicked.connect(self.proc_all)
        proc_row.addWidget(b_sel)
        proc_row.addWidget(b_all)
        right.addLayout(proc_row)
        right.addStretch()

        # Footer (Pixel Bar)
        bot = QFrame()
        bot.setObjectName("PixelBar")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(10, 3, 10, 4)
        bl.setSpacing(18)
        font = QFont("Consolas", 9)
        for _ in range(10):
            l = QLabel("0.000000α")
            l.setFont(font)
            self.pixel_labels.append(l)
            bl.addWidget(l)
        outer.addWidget(bot)

    def _create_box(self, title):
        f = QFrame()
        f.setFrameShape(QFrame.StyledPanel)
        l = QVBoxLayout(f)
        l.addWidget(QLabel(title))
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        img.setMinimumSize(QSize(200, 200))
        l.addWidget(img, 1)
        f.img_lbl = img
        return f

    def _init_running_text(self):
        for l in self.pixel_labels:
            l.setText(random.choice(RUNNING_VALUES) + "  •")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_text)
        self.timer.start(1000)

    def _update_text(self):
        idx = self._running_index % len(self.pixel_labels)
        self._running_index += 1
        self.pixel_labels[idx].setText(random.choice(RUNNING_VALUES) + "  •")

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", IMAGE_FILTER)
        if not files:
            return
        for f in files:
            p = Path(f)
            if p not in self.image_paths:
                self.image_paths.append(p)
                item = QListWidgetItem(p.name)
                item.setData(Qt.UserRole, p)
                self.list_w.addItem(item)
        if self.list_w.count() > 0:
            self.list_w.setCurrentRow(0)

    def clear_list(self):
        self.image_paths.clear()
        self.output_map.clear()
        self.list_w.clear()
        self._update_prev(None)

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.image_paths):
            self._update_prev(None)
        else:
            self._update_prev(self.image_paths[row])

    def _update_prev(self, path):
        orig, res = self.lbl_orig.img_lbl, self.lbl_res.img_lbl
        if not path:
            orig.setPixmap(QPixmap())
            orig.setText("(no image)")
            res.setPixmap(QPixmap())
            res.setText("(no result)")
            return

        pix = QPixmap(str(path))
        if not pix.isNull():
            orig.setPixmap(
                pix.scaled(orig.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            orig.setText("")
        else:
            orig.setText("(error)")

        out = self.output_map.get(path)
        if out and out.exists():
            rpix = QPixmap(str(out))
            res.setPixmap(
                rpix.scaled(res.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            res.setText("")
        else:
            res.setPixmap(QPixmap())
            res.setText("(no result)")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        r = self.list_w.currentRow()
        if r >= 0:
            self._update_prev(self.image_paths[r])

    def on_preset(self, n):
        self.current_preset_name = n

    def ensure_out(self, sample):
        if not self.output_dir:
            self.output_dir = sample.parent / "LABOKit_BG"
            self.output_dir.mkdir(exist_ok=True)
            self.out_lbl.setText(f"BG OUTPUT FOLDER: {self.output_dir}")
            QMessageBox.information(
                self, "Info", f"Output folder set to:\n{self.output_dir}"
            )
        return self.output_dir

    def change_output_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.output_dir = Path(d)
            self.out_lbl.setText(f"BG OUTPUT FOLDER: {self.output_dir}")

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel:
            return QMessageBox.info(self, "Info", "Select images first.")
        self._run(sel)

    def proc_all(self):
        if not self.image_paths:
            return QMessageBox.info(self, "Info", "Add images first.")
        self._run(self.image_paths)

    def _run(self, paths):
        out = self.ensure_out(paths[0])
        dlg = QProgressDialog("Removing BG...", "Cancel", 0, len(paths), self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()

        cnt = 0
        import rembg

        for i, p in enumerate(paths):
            if dlg.wasCanceled():
                break
            dlg.setLabelText(f"Processing {p.name}...")
            QApplication.processEvents()
            try:
                res = rembg.remove(
                    p.read_bytes(), **self.presets.get(self.current_preset_name, {})
                )
                opath = out / f"{p.stem}_nobg.png"
                opath.write_bytes(res)
                self.output_map[p] = opath
                cnt += 1
            except Exception as e:
                print(e)
            dlg.setValue(i + 1)
        dlg.close()
        QMessageBox.information(self, "Done", f"Processed {cnt} images.\nFolder: {out}")
        if self.list_w.currentRow() >= 0:
            self._update_prev(self.image_paths[self.list_w.currentRow()])

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_paths = []
        self.output_dir = None
        self.output_map = {}
        self.view_path = None
        self.pixel_labels = []
        self._running_index = 0
        self._setup_ui()
        self._init_running_text()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)
        main = QHBoxLayout()
        outer.addLayout(main)

        # Left Panel
        left = QVBoxLayout()
        main.addLayout(left, 1)
        self.list_w = QListWidget()
        self.list_w.currentItemChanged.connect(self.on_item)
        lbl = QLabel("LOADED IMAGES (Upscaler):")
        lbl.setStyleSheet("border:none; background:transparent;")
        left.addWidget(lbl)
        left.addWidget(self.list_w)

        btns = QHBoxLayout()
        b_add = QPushButton("Add Images…")
        b_add.clicked.connect(self.add_images)
        b_clr = QPushButton("Clear List")
        b_clr.clicked.connect(self.clear_list)
        btns.addWidget(b_add)
        btns.addWidget(b_clr)
        left.addLayout(btns)

        # Right Panel
        right = QVBoxLayout()
        main.addLayout(right, 3)
        self.out_lbl = QLabel("UPSCALE OUTPUT FOLDER: (auto)")
        self.out_lbl.setWordWrap(True)
        right.addWidget(self.out_lbl)

        # Previews
        prev = QHBoxLayout()
        right.addLayout(prev, 5)
        self.lbl_orig = self._create_box("Original")
        self.lbl_res = self._create_box("Result (Upscaled)")
        prev.addWidget(self.lbl_orig)
        prev.addWidget(self.lbl_res)

        # Options
        right.addSpacing(6)
        opt = QHBoxLayout()
        opt.addWidget(QLabel("Scale:"))
        self.combo_s = QComboBox()
        self.combo_s.addItems(["2x", "4x"])
        self.combo_s.setCurrentText("4x")
        opt.addWidget(self.combo_s)
        opt.addWidget(QLabel("Model:"))
        self.combo_m = QComboBox()
        self.combo_m.addItems(["realesrgan-x4plus", "realesrgan-x4plus-anime"])
        opt.addWidget(self.combo_m)
        right.addLayout(opt)

        # Buttons
        right.addSpacing(10)
        proc = QHBoxLayout()
        b_sel = QPushButton("Upscale (Selected)")
        b_sel.clicked.connect(self.proc_sel)
        b_all = QPushButton("Upscale (All)")
        b_all.clicked.connect(self.proc_all)
        proc.addWidget(b_sel)
        proc.addWidget(b_all)
        right.addLayout(proc)
        right.addStretch()

        # Footer
        bot = QFrame()
        bot.setObjectName("PixelBar")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(10, 3, 10, 4)
        bl.setSpacing(18)
        font = QFont("Consolas", 9)
        for _ in range(10):
            l = QLabel("0.000000α")
            l.setFont(font)
            self.pixel_labels.append(l)
            bl.addWidget(l)
        outer.addWidget(bot)

    def _create_box(self, title):
        f = QFrame()
        f.setFrameShape(QFrame.StyledPanel)
        l = QVBoxLayout(f)
        l.addWidget(QLabel(title))
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        img.setMinimumSize(QSize(200, 200))
        l.addWidget(img, 1)
        f.img_lbl = img
        return f

    def _init_running_text(self):
        for l in self.pixel_labels:
            l.setText(random.choice(RUNNING_VALUES) + "  •")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_text)
        self.timer.start(1000)

    def _update_text(self):
        idx = self._running_index % len(self.pixel_labels)
        self._running_index += 1
        self.pixel_labels[idx].setText(random.choice(RUNNING_VALUES) + "  •")

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", IMAGE_FILTER)
        if not files:
            return
        for f in files:
            p = Path(f)
            if p not in self.image_paths:
                self.image_paths.append(p)
                item = QListWidgetItem(p.name)
                item.setData(Qt.UserRole, p)
                self.list_w.addItem(item)
        if self.list_w.count() > 0:
            self.list_w.setCurrentRow(0)

    def clear_list(self):
        self.image_paths.clear()
        self.output_map.clear()
        self.list_w.clear()
        self._update_prev(None)

    def on_item(self, curr, prev):
        if not curr:
            self._update_prev(None)
        else:
            self._update_prev(curr.data(Qt.UserRole))

    def _update_prev(self, path):
        self.view_path = path
        orig, res = self.lbl_orig.img_lbl, self.lbl_res.img_lbl
        if not path:
            orig.setPixmap(QPixmap())
            orig.setText("(no image)")
            res.setPixmap(QPixmap())
            res.setText("(no result)")
            return

        pix = QPixmap(str(path))
        if not pix.isNull():
            orig.setPixmap(
                pix.scaled(orig.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            orig.setText("")
        else:
            orig.setText("(error)")

        out = self.output_map.get(path)
        if out and out.exists():
            rpix = QPixmap(str(out))
            res.setPixmap(
                rpix.scaled(res.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            res.setText("")
        else:
            res.setPixmap(QPixmap())
            res.setText("(no result)")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.view_path:
            self._update_prev(self.view_path)

    def ensure_out(self, sample):
        if not self.output_dir:
            self.output_dir = sample.parent / "LABOKit_UP"
            self.output_dir.mkdir(exist_ok=True)
            self.out_lbl.setText(f"UPSCALE OUTPUT FOLDER: {self.output_dir}")
            QMessageBox.information(
                self, "Info", f"Output folder set to:\n{self.output_dir}"
            )
        return self.output_dir

    def change_output_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.output_dir = Path(d)
            self.out_lbl.setText(f"UPSCALE OUTPUT FOLDER: {self.output_dir}")

    def proc_sel(self):
        sel = [i.data(Qt.UserRole) for i in self.list_w.selectedItems()]
        if not sel:
            return QMessageBox.info(self, "Info", "Select images first.")
        self._run(sel)

    def proc_all(self):
        if not self.image_paths:
            return QMessageBox.info(self, "Info", "Add images first.")
        self._run(self.image_paths)

    def _run(self, paths):
        if not REALESRGAN_EXE.exists():
            return QMessageBox.warning(
                self,
                "Error",
                f"Executable not found at:\n{REALESRGAN_EXE}\nWait for install.",
            )

        out = self.ensure_out(paths[0])
        dlg = QProgressDialog("Upscaling...", "Cancel", 0, len(paths), self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()

        cnt = 0
        target_scale = int(self.combo_s.currentText().replace("x", ""))
        model = self.combo_m.currentText()

        for i, p in enumerate(paths):
            if dlg.wasCanceled():
                break
            dlg.setLabelText(f"Processing {p.name}...")
            QApplication.processEvents()

            try:
                opath = out / f"{p.stem}_up{target_scale}x.png"

                exec_scale = 4

                cmd = [
                    str(REALESRGAN_EXE),
                    "-i",
                    str(p),
                    "-o",
                    str(opath),
                    "-n",
                    model,
                    "-s",
                    str(exec_scale),
                ]

                flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

                subprocess.run(
                    cmd,
                    capture_output=True,
                    creationflags=flags,
                    cwd=str(REALESRGAN_DIR),
                )

                if target_scale == 2:
                    with Image.open(opath) as img:
                        new_w = img.width // 2
                        new_h = img.height // 2
                        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        img.save(opath)

                self.output_map[p] = opath
                cnt += 1
            except Exception as e:
                print(f"Upscale Error: {e}")

            dlg.setValue(i + 1)

        dlg.close()
        QMessageBox.information(self, "Done", f"Upscaled {cnt} images.\nFolder: {out}")
        if self.list_w.currentItem():
            self.on_item(self.list_w.currentItem(), None)

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
            "</ul>"
            "<b>3. Scale Factor</b><br>"
            "Choose <b>4x</b> for maximum detail or <b>2x</b> for a quicker resize.<br><br>"
            "<b>⚠️ Hardware Note:</b><br>"
            "This feature requires a Vulkan-compatible GPU. On first run, it might take a few seconds to initialize."
        )
        QMessageBox.information(self, "Help – Upscaler", text)


# ==========================================
# MAIN WINDOW
# ==========================================


class LABOKitMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LABOKit")
        self.tabs = QTabWidget()
        self.bg_tab = BgRemoverTab(self)
        self.up_tab = UpscalerTab(self)
        self.tabs.addTab(self.bg_tab, "BG Remover")
        self.tabs.addTab(self.up_tab, "Upscaler")
        self.setCentralWidget(self.tabs)
        self.loaded_plugins = []
        self._setup_menu()
        self._load_plugins()

    def _load_plugins(self):
        if not PLUGIN_DIR.exists():
            PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

        # Remove old tabs
        for p in self.loaded_plugins:
            if p.get("tab"):
                idx = self.tabs.indexOf(p["tab"])
                if idx != -1:
                    self.tabs.removeTab(idx)
        self.loaded_plugins.clear()

        # Load new
        for f in PLUGIN_DIR.glob("*.kit"):
            try:
                mod_name = f"plugin_{f.stem}"
                loader = importlib.machinery.SourceFileLoader(mod_name, str(f))
                spec = importlib.util.spec_from_file_location(
                    mod_name, str(f), loader=loader
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                if hasattr(mod, "create_tab"):
                    tab = mod.create_tab(self)
                    name = getattr(mod, "PLUGIN_NAME", f.stem)
                    self.tabs.addTab(tab, name)
                    self.loaded_plugins.append(
                        {
                            "name": name,
                            "tab": tab,
                            "help": getattr(mod, "HELP_TEXT", ""),
                        }
                    )
            except Exception as e:
                print(f"Plugin Error {f.name}: {e}")

        self._refresh_plugin_menu()

    def _refresh_plugin_menu(self):
        if hasattr(self, "menu_plugins"):
            self.menu_plugins.clear()
            if not self.loaded_plugins:
                self.menu_plugins.addAction(
                    QAction("(No plugins loaded)", self, enabled=False)
                )
            else:
                for p in self.loaded_plugins:
                    a = QAction(p["name"], self)
                    a.triggered.connect(
                        lambda c, x=p: QMessageBox.information(self, "Help", x["help"])
                    )
                    self.menu_plugins.addAction(a)

    def load_plugin_file(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Load Plugin", "", "LABOKit Plugin (*.kit)"
        )
        if f:
            try:
                shutil.copy2(f, PLUGIN_DIR)
                self._load_plugins()
                QMessageBox.information(self, "Success", "Plugin loaded!")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def open_url(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def _setup_menu(self):
        mb = self.menuBar()

        file = mb.addMenu("&File")
        file.addAction("Add Images...", self.add_images_curr)
        file.addAction("Change Output Folder...", self.change_out_curr)
        file.addSeparator()
        file.addAction("Exit", self.close)

        conf = mb.addMenu("&Config")
        conf.addAction("Load Plugin (.kit)...", self.load_plugin_file)
        conf.addAction(
            "Open Plugins Folder",
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(PLUGIN_DIR))),
        )

        help = mb.addMenu("&Help")
        help.addAction("BG Remover Help", self.bg_tab.show_help)
        help.addAction("Upscaler Help", self.up_tab.show_help)
        help.addSeparator()
        help.addAction("Licenses / NOTICE", self.show_notice)
        self.menu_plugins = help.addMenu("Plugins")

        supp = mb.addMenu("&Support")
        supp.addAction(
            "Get Plugins (Trakteer ID)",
            lambda: self.open_url(
                "https://trakteer.id/kano-bbif7/showcase/labokit-advanced-plugins-m84J6"
            ),
        )
        supp.addAction(
            "Get Plugins (Ko-fi)",
            lambda: self.open_url("https://ko-fi.com/s/a367e473fe"),
        )

    def add_images_curr(self):
        w = self.tabs.currentWidget()
        if hasattr(w, "add_images"):
            w.add_images()

    def change_out_curr(self):
        w = self.tabs.currentWidget()
        if hasattr(w, "change_output_folder"):
            w.change_output_folder()

    def show_bg_help(self):
        self.bg_tab.show_help()

    def show_upscale_help(self):
        self.up_tab.show_help()

    def show_notice(self):
        p = INTERNAL_DIR / "LABOKit_NOTICE.txt"
        if not p.exists():
            return QMessageBox.warning(self, "Error", "Notice file missing.")
        dlg = QDialog(self)
        dlg.setWindowTitle("NOTICE")
        dlg.resize(600, 400)
        lay = QVBoxLayout(dlg)
        t = QPlainTextEdit(p.read_text(encoding="utf-8"))
        t.setReadOnly(True)
        t.setFont(QFont("Consolas", 9))
        lay.addWidget(t)
        dlg.exec()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LABOKit")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    default_font = QFont("Consolas", 9)
    app.setFont(default_font)

    # Simple Splash (Image Only)
    splash_img_path = INTERNAL_DIR / "splash.png"
    pix = (
        QPixmap(str(splash_img_path)) if splash_img_path.exists() else QPixmap(400, 100)
    )
    if not splash_img_path.exists():
        pix.fill(Qt.white)

    splash = QSplashScreen(
        pix.scaledToWidth(400, Qt.SmoothTransformation), Qt.WindowStaysOnTopHint
    )
    splash.show()
    app.processEvents()

    # Silent Deploy
    deploy_assets()

    # Warmup
    try:
        from rembg import remove as r_rem

        r_rem(b"\x00" * 10)
    except:
        pass

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

    win = LABOKitMainWindow()
    win.show()
    splash.finish(win)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
