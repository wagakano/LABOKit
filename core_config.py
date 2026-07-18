import sys
import os
import shutil
from pathlib import Path
from packaging import version
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure main directory is in path for plugins to import other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# --- NUMBA MISSING NJIT PATCH FOR PYMATTING (dependency of REMBG) ---
import sys
import types
try:
    from numba import njit
except ImportError:
    try:
        import numpy as np
        ndindex = np.ndindex
    except ImportError:
        ndindex = lambda *args: []

    numba_mock = types.ModuleType("numba")
    def _dummy_jit(*args, **kwargs):
        def decorator(func): return func
        if len(args) == 1 and callable(args[0]): return args[0]
        return decorator
    numba_mock.njit = _dummy_jit
    numba_mock.jit = _dummy_jit
    numba_mock.prange = range
    numba_mock.pndindex = ndindex
    sys.modules["numba"] = numba_mock
    sys.modules["numba.core"] = types.ModuleType("numba.core")
    sys.modules["numba.core.decorators"] = numba_mock

# --- PYINSTALLER IMPORTLIB.METADATA PATCH FOR REMBG/PYMATTING ---
import importlib.metadata
_orig_version = importlib.metadata.version
def _patched_version(package_name):
    try:
        return _orig_version(package_name)
    except importlib.metadata.PackageNotFoundError:
        if package_name == "pymatting":
            return "1.1.8"
        elif package_name == "rembg":
            return "2.0.69"
        raise
importlib.metadata.version = _patched_version

try:
    _orig_metadata = importlib.metadata.metadata
    def _patched_metadata(package_name):
        try:
            return _orig_metadata(package_name)
        except importlib.metadata.PackageNotFoundError:
            if package_name == "pymatting":
                from email.message import Message
                msg = Message()
                msg["Version"] = "1.1.8"
                msg["Name"] = "pymatting"
                return msg
            elif package_name == "rembg":
                from email.message import Message
                msg = Message()
                msg["Version"] = "2.0.69"
                msg["Name"] = "rembg"
                return msg
            raise
    importlib.metadata.metadata = _patched_metadata
except AttributeError:
    pass


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- APP INFO ---
APP_VERSION = "3.3.1"
APP_UPDATE_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/latest_version.json"
PLUGIN_MANIFEST_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/plugins_manifest.json"

# --- PATH & ASSETS SETUP ---
# 1. Internal Path (Source files inside EXE/Build)
INTERNAL_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

# 2. Persistent Path (User AppData folder: %APPDATA%/LABOKit)
_app_data = os.getenv('APPDATA')
if not _app_data:
    _app_data = os.path.expanduser("~") # Fallback
APP_DATA = Path(_app_data) / "LABOKit"
APP_DATA.mkdir(parents=True, exist_ok=True)

MODEL_DIR = APP_DATA / "models"
REALESRGAN_DIR = APP_DATA / "realesrgan"
PLUGIN_DIR = APP_DATA / "plugins"
FFMPEG_DIR = APP_DATA / "ffmpeg"

# Setup Environment Variables
os.environ["U2NET_HOME"] = str(MODEL_DIR)

# Fallback: check if the executable exists in AppData, if not use the bundled version directly
_realesrgan_exe_appdata = REALESRGAN_DIR / "realesrgan-ncnn-vulkan.exe"
_realesrgan_exe_internal = INTERNAL_DIR / "realesrgan_ncnn" / "realesrgan-ncnn-vulkan.exe"

if _realesrgan_exe_appdata.exists():
    REALESRGAN_EXE = _realesrgan_exe_appdata
    REALESRGAN_RUN_DIR = REALESRGAN_DIR
elif _realesrgan_exe_internal.exists():
    REALESRGAN_EXE = _realesrgan_exe_internal
    REALESRGAN_RUN_DIR = INTERNAL_DIR / "realesrgan_ncnn"
else:
    REALESRGAN_EXE = _realesrgan_exe_appdata
    REALESRGAN_RUN_DIR = REALESRGAN_DIR

# Icon & Assets
ICON_PATH = INTERNAL_DIR / "labokit.ico"

IMAGE_FILTER = (
    "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.gif "
    "*.JPG *.JPEG *.PNG *.BMP *.TIF *.TIFF *.WEBP *.GIF)"
)

# --- BG REMOVER PRESETS ---
BG_PRESETS = {
    "Standard": {"alpha_matting": False, "post_process_mask": False},
    "Medium": {"alpha_matting": False, "post_process_mask": True},
    "High": {"alpha_matting": True, "alpha_matting_foreground_threshold": 240, "alpha_matting_background_threshold": 10, "alpha_matting_erode_structure_size": 10, "alpha_matting_base_size": 1000, "post_process_mask": True},
}
DEFAULT_PRESET_NAME = "Standard"

# --- LAZY LOADING AI ENGINE ---
AI_MODULES = None
GLOBAL_UPSAMPLER_CACHE = {}
GLOBAL_REMBG_SESSION_CACHE = {}

def load_ai_engine():
    global AI_MODULES
    if AI_MODULES:
        return AI_MODULES

    try:
        # Patch torchvision
        import torchvision.transforms.functional as F
        try:
            from torchvision.transforms import functional_tensor
        except ImportError:
            import sys
            from types import ModuleType
            ft_module = ModuleType('torchvision.transforms.functional_tensor')
            ft_module.rgb_to_grayscale = F.rgb_to_grayscale
            sys.modules['torchvision.transforms.functional_tensor'] = ft_module

        import torch
        from torch import nn
        import cv2
        import numpy as np
        from basicsr.archs.srvgg_arch import SRVGGNetCompact 
        from realesrgan import RealESRGANer
        
        AI_MODULES = {
            "torch": torch,
            "cv2": cv2,
            "SRVGGNetCompact": SRVGGNetCompact,
            "RealESRGANer": RealESRGANer
        }
        return AI_MODULES
    except ImportError as e:
        print(f"AI Engine Load Error: {e}")
        return None
