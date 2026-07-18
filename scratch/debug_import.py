import sys
import importlib.util
from pathlib import Path
import os

_app_data = os.getenv('APPDATA')
APP_DATA = Path(_app_data) / "LABOKit"
PLUGIN_DIR = APP_DATA / "plugins"

print("STARTING TEST")
plugin_file = PLUGIN_DIR / "DitheringFX.kit"
print(f"Loading {plugin_file.name}")
spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
module = importlib.util.module_from_spec(spec)
print("Before exec_module")
spec.loader.exec_module(module)
print("After exec_module")
