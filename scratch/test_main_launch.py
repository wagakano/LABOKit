import sys
import os
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("--- LAUNCHING LABOKit MAIN APP ---", flush=True)

# We load main.py dynamically
import importlib.util
import importlib.machinery

main_file = Path(__file__).resolve().parent.parent / "main.py"
mod_name = "main_app"
loader = importlib.machinery.SourceFileLoader(mod_name, str(main_file))
spec = importlib.util.spec_from_file_location(mod_name, str(main_file), loader=loader)
module = importlib.util.module_from_spec(spec)
sys.modules[mod_name] = module
spec.loader.exec_module(module)

print("main.py imported successfully!", flush=True)

# Now instantiate the App and main window
app = QApplication.instance() or QApplication(sys.argv)
print("Creating LABOKitMainWindow instance...", flush=True)
window = module.LABOKitMainWindow()
print("LABOKitMainWindow created successfully! Showing...", flush=True)
window.show()

# Setup auto-close timer after 2 seconds
print("Starting 2-second auto-close timer...", flush=True)
timer = QTimer()
timer.setSingleShot(True)
timer.timeout.connect(lambda: (print("Timer fired, closing window...", flush=True), window.close(), app.quit()))
timer.start(2000)

print("Entering Qt event loop...", flush=True)
sys.exit(app.exec())
