import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = QApplication.instance() or QApplication(sys.argv)

import importlib.util
import importlib.machinery

def load_and_instantiate(name):
    print(f"\n--- Loading {name} ---", flush=True)
    plugin_file = Path(__file__).resolve().parent.parent / "LABOKit Plugins" / "3.0" / name
    mod_name = f"plugin_{plugin_file.stem}"
    loader = importlib.machinery.SourceFileLoader(mod_name, str(plugin_file))
    spec = importlib.util.spec_from_file_location(mod_name, str(plugin_file), loader=loader)
    module = importlib.util.module_from_spec(spec)
    module.tr = lambda key, default=None: default if default else key
    spec.loader.exec_module(module)
    print(f"Imported {name}", flush=True)
    tab = module.create_tab()
    print(f"Instantiated {name} successfully", flush=True)
    return tab

try:
    t1 = load_and_instantiate("ImageLAB.kit")
    t2 = load_and_instantiate("IMGConverter.kit")
    
    if hasattr(t1, 'worker_thread'):
        print("Stopping t1.worker_thread...", flush=True)
        t1.worker_thread.quit()
        t1.worker_thread.wait()
        print("Stopped t1.worker_thread!", flush=True)
        
except Exception as e:
    import traceback
    traceback.print_exc()

print("Script exiting...", flush=True)
