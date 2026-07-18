import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, 
    QFileDialog, QMessageBox, QProgressDialog, QComboBox, QListWidgetItem, QMenu
)
from ui_shared import FileDropListWidget, ZoomableImageWidget, create_plus_icon, VALID_EXTENSIONS
from translations import tr
import core_config

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
                            str(core_config.REALESRGAN_EXE), 
                            "-i", str(p), 
                            "-o", str(opath), 
                            "-n", self.model_name, 
                            "-s", "4"
                        ]
                        flags = subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0
                        subprocess.run(cmd, capture_output=True, creationflags=flags, cwd=str(core_config.REALESRGAN_RUN_DIR))
                        success = opath.exists()

                    if success:
                        cnt += 1
                        
                except Exception as e:
                    print(f"Upscale Error: {e}")
            
            self.finished.emit(cnt)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def init_upsampler(self, model_name):
        if model_name in core_config.GLOBAL_UPSAMPLER_CACHE:
            return core_config.GLOBAL_UPSAMPLER_CACHE[model_name]

        ai = core_config.load_ai_engine()
        if not ai:
            return None

        # Unpack
        SRVGGNetCompact = ai["SRVGGNetCompact"]
        RealESRGANer = ai["RealESRGANer"]

        try:
            model_path = core_config.REALESRGAN_DIR / "models" / model_name 
            if not model_path.exists():
                model_path = core_config.MODEL_DIR / model_name
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
            core_config.GLOBAL_UPSAMPLER_CACHE[model_name] = upsampler
            return upsampler

        except Exception as e:
            print(f"Error: {e}")
            import traceback; traceback.print_exc()
            return None

    def run_python_inference(self, img_path, out_path, upsampler):
        ai = core_config.load_ai_engine()
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


class UpscalerTab(QWidget):
    def __init__(self, meter=None, parent=None):
        super().__init__(parent)
        self.meter = meter
        self.image_paths = []
        self.image_paths_set = set() # O(1) membership check
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
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", core_config.IMAGE_FILTER)
        if not files: return
        for f in files:
            p = Path(f)
            if p not in self.image_paths_set:
                self.image_paths.append(p)
                self.image_paths_set.add(p)
                item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                self.list_w.addItem(item)
        if self.list_w.count()>0: self.list_w.setCurrentRow(0)

    def add_dropped_files(self, files):
        for p in files:
            if p.suffix.lower() in VALID_EXTENSIONS:
                if p not in self.image_paths_set:
                    self.image_paths.append(p)
                    self.image_paths_set.add(p)
                    item = QListWidgetItem(p.name); item.setData(Qt.UserRole, p)
                    self.list_w.addItem(item)
        if self.list_w.count() > 0 and self.list_w.currentRow() < 0:
            self.list_w.setCurrentRow(0)

    def clear_list(self):
        self.image_paths.clear(); self.image_paths_set.clear(); self.output_map.clear(); self.list_w.clear()
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
                self.image_paths_set.discard(path)
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

        if not is_python_mode and not core_config.REALESRGAN_EXE.exists():
            return QMessageBox.warning(self, "Error", f"Executable not found at:\n{core_config.REALESRGAN_EXE}")
        
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
