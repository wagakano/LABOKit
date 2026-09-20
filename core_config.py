import sys
import os

class SafeStream:
    def __init__(self, original_stream=None):
        self.original_stream = original_stream

    def write(self, data):
        if self.original_stream:
            try:
                self.original_stream.write(data)
                return
            except Exception:
                pass

    def flush(self):
        if self.original_stream:
            try:
                self.original_stream.flush()
            except Exception:
                pass

    def isatty(self):
        return False

if sys.stdout is None or not hasattr(sys.stdout, 'write'):
    sys.stdout = SafeStream(None)
else:
    sys.stdout = SafeStream(sys.stdout)

if sys.stderr is None or not hasattr(sys.stderr, 'write'):
    sys.stderr = SafeStream(None)
else:
    sys.stderr = SafeStream(sys.stderr)

# Prevent OpenMP multi-threading duplicate library conflicts and loading deadlocks
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import json
import shutil
import zipfile
from pathlib import Path
from packaging import version

# Ensure main directory is in path for plugins to import other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# --- NUMBA MISSING NJIT PATCH FOR PYMATTING (dependency of REMBG) ---
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

# --- APP INFO ---
APP_VERSION = "3.3.2"
APP_UPDATE_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/latest_version.json"
PLUGIN_MANIFEST_URL = "https://raw.githubusercontent.com/wagakano/LABOKit/main_windows/plugins_manifest.json"

# --- PATH & ASSETS SETUP ---
# 1. Internal Path (Source files inside EXE/Build)
INTERNAL_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

def resource_path(relative_path):
    """Return absolute path to resource, working for dev and for PyInstaller."""
    return str(INTERNAL_DIR / relative_path)

# 2. Persistent Path (User AppData folder: %APPDATA%/LABOKit)
_app_data = os.getenv('APPDATA')
if not _app_data:
    _app_data = os.path.expanduser("~") # Fallback
APP_DATA = Path(_app_data) / "LABOKit"
APP_DATA.mkdir(parents=True, exist_ok=True)

# 3. Settings Persistence
SETTINGS_FILE = APP_DATA / "settings.json"

def load_settings():
    default_settings = {"theme": "light"}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_settings.update(data)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return default_settings

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

MODEL_DIR = APP_DATA / "models"
REALESRGAN_DIR = APP_DATA / "realesrgan"
PLUGIN_DIR = APP_DATA / "plugins"
FFMPEG_DIR = APP_DATA / "ffmpeg"

# Setup Environment Variables
os.environ["MODEL_CHECKSUM_DISABLED"] = "1"
os.environ["U2NET_HOME"] = str(MODEL_DIR)

def get_u2net_home(model_name="u2net"):
    """Locates the directory containing the given .onnx model without copying or downloading."""
    fname = f"{model_name}.onnx"
    # 1. User AppData models folder
    if (MODEL_DIR / fname).exists():
        return MODEL_DIR
    # 2. Bundled _internal/models folder
    if (INTERNAL_DIR / "models" / fname).exists():
        return INTERNAL_DIR / "models"
    # 3. Bundled root/models folder
    if (INTERNAL_DIR.parent / "models" / fname).exists():
        return INTERNAL_DIR.parent / "models"
    # 4. Development models folder
    dev_path = Path("models") / fname
    if dev_path.exists():
        return dev_path.parent.resolve()
    return MODEL_DIR

def ensure_offline_models_extracted():
    """100% Offline bootstrap: Unpack local bundled models.zip if models directory is missing weights."""
    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        local_archive = INTERNAL_DIR / "models.zip"
        if local_archive.exists():
            existing = list(MODEL_DIR.glob("*"))
            if not existing:
                with zipfile.ZipFile(local_archive, 'r') as z:
                    z.extractall(MODEL_DIR)
                print(f"Offline model archive unpacked to {MODEL_DIR}")
    except Exception as e:
        print(f"Offline model extraction check warning: {e}")

ensure_offline_models_extracted()

def cleanup_temp_model_files():
    if MODEL_DIR.exists():
        for f in MODEL_DIR.glob("tmp*"):
            try:
                if f.is_file(): f.unlink()
                elif f.is_dir(): shutil.rmtree(f, ignore_errors=True)
            except Exception:
                pass

cleanup_temp_model_files()

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
_last_ai_engine_error = ""
GLOBAL_UPSAMPLER_CACHE = {}
GLOBAL_REMBG_SESSION_CACHE = {}

class SRVGGNetCompact:
    pass

class RealESRGANer:
    pass

def load_ai_engine():
    global AI_MODULES, _last_ai_engine_error
    if AI_MODULES:
        return AI_MODULES

    try:
        import math
        import cv2
        import numpy as np
        import torch
        from torch import nn
        from torch.nn import functional as F

        class _SRVGGNetCompact(nn.Module):
            """A compact VGG-style network structure for super-resolution."""

            def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu'):
                super().__init__()
                self.num_in_ch = num_in_ch
                self.num_out_ch = num_out_ch
                self.num_feat = num_feat
                self.num_conv = num_conv
                self.upscale = upscale
                self.act_type = act_type

                self.body = nn.ModuleList()
                self.body.append(nn.Conv2d(num_in_ch, num_feat, 3, 1, 1))
                if act_type == 'relu':
                    activation = nn.ReLU(inplace=True)
                elif act_type == 'prelu':
                    activation = nn.PReLU(num_parameters=num_feat)
                elif act_type == 'leakyrelu':
                    activation = nn.LeakyReLU(negative_slope=0.1, inplace=True)
                self.body.append(activation)

                for _ in range(num_conv):
                    self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
                    if act_type == 'relu':
                        activation = nn.ReLU(inplace=True)
                    elif act_type == 'prelu':
                        activation = nn.PReLU(num_parameters=num_feat)
                    elif act_type == 'leakyrelu':
                        activation = nn.LeakyReLU(negative_slope=0.1, inplace=True)
                    self.body.append(activation)

                self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
                self.upsampler = nn.PixelShuffle(upscale)

            def forward(self, x):
                out = x
                for i in range(0, len(self.body)):
                    out = self.body[i](out)
                out = self.upsampler(out)
                base = F.interpolate(x, scale_factor=self.upscale, mode='nearest')
                out += base
                return out

        class _RealESRGANer:
            """Self-contained inference engine for RealESRGAN models."""

            def __init__(self, scale, model_path, dni_weight=None, model=None, tile=0, tile_pad=10, pre_pad=10, half=False, device=None, gpu_id=None):
                self.scale = scale
                self.tile_size = tile
                self.tile_pad = tile_pad
                self.pre_pad = pre_pad
                self.mod_scale = None
                self.half = half

                if gpu_id is not None:
                    self.device = torch.device(f'cuda:{gpu_id}' if torch.cuda.is_available() else 'cpu') if device is None else device
                else:
                    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if device is None else device

                loadnet = torch.load(model_path, map_location=torch.device('cpu'), weights_only=False)
                keyname = 'params_ema' if 'params_ema' in loadnet else 'params'
                model.load_state_dict(loadnet[keyname], strict=True)
                model.eval()
                self.model = model.to(self.device)
                if self.half:
                    self.model = self.model.half()

            def pre_process(self, img):
                img = torch.from_numpy(np.transpose(img, (2, 0, 1))).float()
                self.img = img.unsqueeze(0).to(self.device)
                if self.half:
                    self.img = self.img.half()
                if self.pre_pad != 0:
                    self.img = F.pad(self.img, (0, self.pre_pad, 0, self.pre_pad), 'reflect')
                if self.scale == 2:
                    self.mod_scale = 2
                elif self.scale == 1:
                    self.mod_scale = 4
                if self.mod_scale is not None:
                    self.mod_pad_h, self.mod_pad_w = 0, 0
                    _, _, h, w = self.img.size()
                    if (h % self.mod_scale != 0):
                        self.mod_pad_h = (self.mod_scale - h % self.mod_scale)
                    if (w % self.mod_scale != 0):
                        self.mod_pad_w = (self.mod_scale - w % self.mod_scale)
                    self.img = F.pad(self.img, (0, self.mod_pad_w, 0, self.mod_pad_h), 'reflect')

            def process(self):
                self.output = self.model(self.img)

            def tile_process(self):
                batch, channel, height, width = self.img.shape
                output_height = height * self.scale
                output_width = width * self.scale
                output_shape = (batch, channel, output_height, output_width)
                self.output = self.img.new_zeros(output_shape)
                tiles_x = math.ceil(width / self.tile_size)
                tiles_y = math.ceil(height / self.tile_size)

                for y in range(tiles_y):
                    for x in range(tiles_x):
                        ofs_x = x * self.tile_size
                        ofs_y = y * self.tile_size
                        input_start_x = ofs_x
                        input_end_x = min(ofs_x + self.tile_size, width)
                        input_start_y = ofs_y
                        input_end_y = min(ofs_y + self.tile_size, height)

                        input_start_x_pad = max(input_start_x - self.tile_pad, 0)
                        input_end_x_pad = min(input_end_x + self.tile_pad, width)
                        input_start_y_pad = max(input_start_y - self.tile_pad, 0)
                        input_end_y_pad = min(input_end_y + self.tile_pad, height)

                        input_tile_width = input_end_x - input_start_x
                        input_tile_height = input_end_y - input_start_y
                        input_tile = self.img[:, :, input_start_y_pad:input_end_y_pad, input_start_x_pad:input_end_x_pad]

                        with torch.no_grad():
                            output_tile = self.model(input_tile)

                        output_start_x = input_start_x * self.scale
                        output_end_x = input_end_x * self.scale
                        output_start_y = input_start_y * self.scale
                        output_end_y = input_end_y * self.scale

                        output_start_x_tile = (input_start_x - input_start_x_pad) * self.scale
                        output_end_x_tile = output_start_x_tile + input_tile_width * self.scale
                        output_start_y_tile = (input_start_y - input_start_y_pad) * self.scale
                        output_end_y_tile = output_start_y_tile + input_tile_height * self.scale

                        self.output[:, :, output_start_y:output_end_y, output_start_x:output_end_x] = output_tile[:, :, output_start_y_tile:output_end_y_tile, output_start_x_tile:output_end_x_tile]

            def post_process(self):
                if self.mod_scale is not None:
                    _, _, h, w = self.output.size()
                    self.output = self.output[:, :, 0:h - self.mod_pad_h * self.scale, 0:w - self.mod_pad_w * self.scale]
                if self.pre_pad != 0:
                    _, _, h, w = self.output.size()
                    self.output = self.output[:, :, 0:h - self.pre_pad * self.scale, 0:w - self.pre_pad * self.scale]
                return self.output

            @torch.no_grad()
            def enhance(self, img, outscale=None, alpha_upsampler='realesrgan'):
                h_input, w_input = img.shape[0:2]
                img = img.astype(np.float32)
                max_range = 65535 if np.max(img) > 256 else 255
                img = img / max_range

                if len(img.shape) == 2:
                    img_mode = 'L'
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                elif img.shape[2] == 4:
                    img_mode = 'RGBA'
                    alpha = img[:, :, 3]
                    img = cv2.cvtColor(img[:, :, 0:3], cv2.COLOR_BGR2RGB)
                    if alpha_upsampler == 'realesrgan':
                        alpha = cv2.cvtColor(alpha, cv2.COLOR_GRAY2RGB)
                else:
                    img_mode = 'RGB'
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                self.pre_process(img)
                if self.tile_size > 0:
                    self.tile_process()
                else:
                    self.process()
                output_img = self.post_process()
                output_img = output_img.data.squeeze().float().cpu().clamp_(0, 1).numpy()
                output_img = np.transpose(output_img[[2, 1, 0], :, :], (1, 2, 0))

                if img_mode == 'L':
                    output_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2GRAY)

                if img_mode == 'RGBA':
                    if alpha_upsampler == 'realesrgan':
                        self.pre_process(alpha)
                        if self.tile_size > 0:
                            self.tile_process()
                        else:
                            self.process()
                        output_alpha = self.post_process()
                        output_alpha = output_alpha.data.squeeze().float().cpu().clamp_(0, 1).numpy()
                        output_alpha = np.transpose(output_alpha[[2, 1, 0], :, :], (1, 2, 0))
                        output_alpha = cv2.cvtColor(output_alpha, cv2.COLOR_BGR2GRAY)
                    else:
                        output_alpha = cv2.resize(alpha, (w_input * self.scale, h_input * self.scale), interpolation=cv2.INTER_LINEAR)

                    output_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2BGRA)
                    output_img[:, :, 3] = output_alpha

                if max_range == 65535:
                    output = (output_img * 65535.0).round().astype(np.uint16)
                else:
                    output = (output_img * 255.0).round().astype(np.uint8)

                if outscale is not None and outscale != float(self.scale):
                    output = cv2.resize(output, (int(w_input * outscale), int(h_input * outscale)), interpolation=cv2.INTER_LANCZOS4)

                return output, img_mode

        AI_MODULES = {
            "torch": torch,
            "cv2": cv2,
            "SRVGGNetCompact": _SRVGGNetCompact,
            "RealESRGANer": _RealESRGANer
        }
        return AI_MODULES
    except Exception as e:
        _last_ai_engine_error = f"{type(e).__name__}: {e}"
        print(f"AI Engine Load Error: {e}")
        try:
            import datetime, traceback
            with open(APP_DATA / "crash_log.txt", "a", encoding="utf-8") as f:
                f.write(f"\n--- AI Engine Load Error at {datetime.datetime.now()} ---\n")
                traceback.print_exc(file=f)
        except:
            pass
        return None


REMBG_MODULE = None

def load_rembg_engine():
    global REMBG_MODULE
    if REMBG_MODULE:
        return REMBG_MODULE

    try:
        import rembg
        REMBG_MODULE = rembg
        return REMBG_MODULE
    except Exception as e:
        print(f"Rembg Engine Load Error: {e}")
        return None
