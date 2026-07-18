import sys
import os
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = QApplication.instance() or QApplication(sys.argv)

import importlib.util
import importlib.machinery

# Load main.py
main_file = Path(__file__).resolve().parent.parent / "main.py"
mod_name = "main_app"
loader = importlib.machinery.SourceFileLoader(mod_name, str(main_file))
spec = importlib.util.spec_from_file_location(mod_name, str(main_file), loader=loader)
module = importlib.util.module_from_spec(spec)
sys.modules[mod_name] = module
spec.loader.exec_module(module)

print("MainWindow instantiating...", flush=True)
window = module.LABOKitMainWindow()
window.show()

# Get the ImageLAB tab
tabs = window.tabs
imagelab_tab = None
for i in range(tabs.count()):
    if tabs.tabText(i) == "ImageLAB":
        imagelab_tab = tabs.widget(i)
        break

if imagelab_tab is None:
    print("ImageLAB tab not found!", flush=True)
    sys.exit(1)

print("Found ImageLAB tab!", flush=True)

# Let's mock file selected item
image_path = Path(__file__).resolve().parent.parent / "splash.png"
print(f"Loading image in ImageLAB: {image_path}", flush=True)

class MockItem:
    def data(self, role):
        return image_path
mock_item = MockItem()

# Load image
imagelab_tab.on_file_selected_item(mock_item)

# Wait 3 seconds for scaling thread pool to finish and print status
def check_preview():
    print("Checking preview widget images...", flush=True)
    orig_img = imagelab_tab.preview_widget.original_image
    res_img = imagelab_tab.preview_widget.result_image
    print(f"Original image in widget: {orig_img}", flush=True)
    if orig_img:
        print(f"Original image size: {orig_img.size()}", flush=True)
    print(f"Result image in widget: {res_img}", flush=True)
    if res_img:
        print(f"Result image size: {res_img.size()}", flush=True)
    
    label = imagelab_tab.preview_widget.image_label
    print(f"Split label show_split: {label.show_split}", flush=True)
    print(f"Split label orig_pixmap: {label.orig_pixmap}", flush=True)
    if label.orig_pixmap:
         print(f"Split label orig_pixmap size: {label.orig_pixmap.size()}", flush=True)
    print(f"Split label res_pixmap: {label.res_pixmap}", flush=True)
    if label.res_pixmap:
         print(f"Split label res_pixmap size: {label.res_pixmap.size()}", flush=True)
    
    window.close()
    app.quit()

timer = QTimer()
timer.setSingleShot(True)
timer.timeout.connect(check_preview)
timer.start(3000)

app.exec()
