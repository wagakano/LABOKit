import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Create QApplication
app = QApplication.instance() or QApplication(sys.argv)

# Import the kit
print("Importing IMGConverter...", flush=True)
import importlib.util
import importlib.machinery

plugin_file = Path(__file__).resolve().parent.parent / "LABOKit Plugins" / "3.0" / "IMGConverter.kit"
mod_name = "plugin_IMGConverter"
loader = importlib.machinery.SourceFileLoader(mod_name, str(plugin_file))
spec = importlib.util.spec_from_file_location(mod_name, str(plugin_file), loader=loader)
module = importlib.util.module_from_spec(spec)
module.tr = lambda key, default=None: default if default else key
spec.loader.exec_module(module)

print("Imported successfully. Now instantiating ImageConverterTab...", flush=True)

# Let's inspect class ImageConverterTab _setup_ui line by line
class ImageConverterTabDebug(module.ImageConverterTab):
    def _setup_ui(self):
        print("Starting _setup_ui...", flush=True)
        super()._setup_ui()
        print("Finished _setup_ui!", flush=True)

try:
    print("Creating widget instance...", flush=True)
    tab = ImageConverterTabDebug()
    print("Instance created successfully!", flush=True)
except Exception as e:
    print(f"Exception during instantiation: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("Script end.", flush=True)
