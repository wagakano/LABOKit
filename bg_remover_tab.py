from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, 
    QFileDialog, QMessageBox, QProgressDialog, QComboBox, QListWidgetItem, QMenu
)
from ui_shared import FileDropListWidget, ZoomableImageWidget, create_plus_icon, VALID_EXTENSIONS
from translations import tr
import core_config

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
            
            self.progress.emit(0, f"Loading model ({self.model_name})...")
            
            # Create session (with cache lookup)
            if self.model_name in core_config.GLOBAL_REMBG_SESSION_CACHE:
                session = core_config.GLOBAL_REMBG_SESSION_CACHE[self.model_name]
            else:
                session = new_session(model_name=self.model_name)
                core_config.GLOBAL_REMBG_SESSION_CACHE[self.model_name] = session
            
            cnt = 0
            err_list = []
            self.out_dir.mkdir(parents=True, exist_ok=True)
            for i, p in enumerate(self.paths):
                if not self.is_running: break
                
                self.progress.emit(i, f"Processing {p.name} ({i+1}/{len(self.paths)})...")
                
                try:
                    with open(p, "rb") as f:
                        img_bytes = f.read()
                    res = rembg.remove(img_bytes, session=session, **self.preset)
                    opath = self.out_dir / f"{p.stem}_nobg.png"
                    with open(opath, "wb") as f:
                        f.write(res)
                    cnt += 1
                except Exception as e:
                    msg = f"{p.name}: {e}"
                    print(f"Error processing {msg}")
                    err_list.append(msg)
            
            if cnt == 0 and err_list:
                self.error.emit("\n".join(err_list))
            else:
                self.finished.emit(cnt)
            
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False


class BgRemoverTab(QWidget):
    def __init__(self, meter=None, parent=None):
        super().__init__(parent)
        self.meter = meter
        self.image_paths = []
        self.image_paths_set = set() # O(1) membership check
        self.output_dir = None
        self.output_map = {}
        self.current_preset_name = core_config.DEFAULT_PRESET_NAME
        self.presets = core_config.BG_PRESETS
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)
        main = QHBoxLayout()
        outer.addLayout(main)
        
        # Left Panel (Controls)
        left = QVBoxLayout()
        main.addLayout(left, 1)
        
        # Loaded Images Box
        self.list_box = QFrame()
        self.list_box.setObjectName("list_box")
        self.list_box.setAttribute(Qt.WA_StyledBackground, True)
        self.list_box.setStyleSheet("#list_box { border: 1px solid #b3bcd1; border-radius: 4px; background-color: #f5f7fb; }")
        list_box_layout = QVBoxLayout(self.list_box)
        list_box_layout.setContentsMargins(6, 6, 6, 6)
        list_box_layout.setSpacing(5)
        
        self.list_w = FileDropListWidget()
        self.list_w.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_w.customContextMenuRequested.connect(self.show_list_context_menu)
        self.list_w.files_dropped.connect(self.add_dropped_files)
        self.list_w.currentRowChanged.connect(self.on_file_selected)
        self.lbl_header = QLabel(tr("lbl_loaded_bg"))
        self.lbl_header.setStyleSheet("font-weight: bold; background-color: #e2e7f2; border: 1px solid #cbd2e1; border-radius: 3px; padding: 4px 6px; color: #333d51;")
        list_box_layout.addWidget(self.lbl_header)
        list_box_layout.addWidget(self.list_w)
        
        # Buttons (Add/Clear)
        btns = QHBoxLayout()
        b_add = QPushButton(tr("btn_add")); b_add.setIcon(create_plus_icon()); b_add.clicked.connect(self.add_images)
        b_clr = QPushButton(tr("btn_clear")); b_clr.clicked.connect(self.clear_list)
        btns.addWidget(b_add); btns.addWidget(b_clr)
        list_box_layout.addLayout(btns)
        
        left.addWidget(self.list_box)

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

    def set_theme(self, theme_name):
        if theme_name == "dark":
            self.lbl_header.setStyleSheet("font-weight: bold; background-color: #22222a; border: 1px solid #2e2e38; border-radius: 3px; padding: 4px 6px; color: #e1e1e6;")
            self.list_box.setStyleSheet("#list_box { border: 1px solid #2e2e38; border-radius: 4px; background-color: #16161a; }")
            if hasattr(self, 'list_w') and hasattr(self.list_w, 'set_theme'):
                self.list_w.set_theme("dark")
        else:
            self.lbl_header.setStyleSheet("font-weight: bold; background-color: #e2e7f2; border: 1px solid #cbd2e1; border-radius: 3px; padding: 4px 6px; color: #333d51;")
            self.list_box.setStyleSheet("#list_box { border: 1px solid #b3bcd1; border-radius: 4px; background-color: #f5f7fb; }")
            if hasattr(self, 'list_w') and hasattr(self.list_w, 'set_theme'):
                self.list_w.set_theme("light")
    
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr("btn_add"), "", core_config.IMAGE_FILTER)
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
                self.image_paths_set.discard(path)
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
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
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
        model_map = {
            "General": "u2net",
            "Performance": "u2netp",
            "Anime": "isnet-anime",
            "Human Portrait": "silueta"
        }
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
