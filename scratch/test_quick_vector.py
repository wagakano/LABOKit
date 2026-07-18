import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = QApplication.instance() or QApplication(sys.argv)

import importlib.util
import importlib.machinery

plugin_file = Path(__file__).resolve().parent.parent / "LABOKit Plugins" / "3.0" / "QuickVector.kit"
mod_name = "plugin_QuickVector"
loader = importlib.machinery.SourceFileLoader(mod_name, str(plugin_file))
spec = importlib.util.spec_from_file_location(mod_name, str(plugin_file), loader=loader)
module = importlib.util.module_from_spec(spec)
module.tr = lambda key, default=None: default if default else key
spec.loader.exec_module(module)

print("Instantiating VectorTab...", flush=True)
tab = module.create_tab()

image_path = Path(__file__).resolve().parent.parent / "splash.png"
print(f"Testing with image: {image_path}", flush=True)

# Simulate adding the file
tab.image_paths.append(image_path)
class MockItem:
    def text(self):
        return image_path.name
mock_item = MockItem()

# Run selection logic
print("Triggering file selection...", flush=True)
tab.on_file_selected(mock_item, None)

print("Verifying binary map generation...", flush=True)
binary, shape = tab.get_binary_map()
print(f"Binary map shape: {shape}", flush=True)

# Run process all
print("Running process_all...", flush=True)
tab.process_all()

print("Quick Vector test completed successfully!", flush=True)
