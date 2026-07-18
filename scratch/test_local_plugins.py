import sys
import os
from pathlib import Path
import importlib.util
import importlib.machinery
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure PLUGIN_DIR exists
_app_data = os.getenv('APPDATA')
if not _app_data:
    _app_data = os.path.expanduser("~")
APP_DATA = Path(_app_data) / "LABOKit"
PLUGIN_DIR = APP_DATA / "plugins"

# Create a QApplication instance for widget testing
app = QApplication.instance() or QApplication(sys.argv)

print("--- STARTING WIDGET INSTANTIATION TEST ---", flush=True)
for plugin_file in PLUGIN_DIR.glob('*.kit'):
    print(f"\n[Loader] Loading {plugin_file.name}...", flush=True)
    try:
        mod_name = f"plugin_{plugin_file.stem}"
        loader = importlib.machinery.SourceFileLoader(mod_name, str(plugin_file))
        spec = importlib.util.spec_from_file_location(mod_name, str(plugin_file), loader=loader)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            module.tr = lambda key, default=None: default if default else key
            spec.loader.exec_module(module)
            print(f"[Loader] Success: {plugin_file.name}", flush=True)
            if hasattr(module, "create_tab"):
                print(f"[Loader] Found create_tab in {plugin_file.name}, instantiating...", flush=True)
                try:
                    tab = module.create_tab(None)
                except TypeError:
                    tab = module.create_tab()
                print(f"[Loader] Instantiated {plugin_file.name} successfully!", flush=True)
                
                # Cleanup threads/workers if any
                if hasattr(tab, 'worker') and hasattr(tab.worker, 'quit'):
                    tab.worker.quit()
                    tab.worker.wait()
            else:
                print(f"[Loader] WARNING: create_tab not found in {plugin_file.name}", flush=True)
        else:
            print(f"[Loader] Failed: spec/loader is None for {plugin_file.name}", flush=True)
    except Exception as e:
        print(f"[Loader] Error with {plugin_file.name}: {e}", flush=True)
        import traceback
        traceback.print_exc()

print("\n--- WIDGET INSTANTIATION TEST COMPLETE ---", flush=True)
