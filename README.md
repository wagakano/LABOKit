<div align="center">

# LABOKit 3.3.2

<img width="1796" height="523" alt="LABOKit Banner" src="https://github.com/user-attachments/assets/2f0b033f-3cfb-4d59-b124-379dcef14b39" />

<p align="center">
  <a href="https://github.com/wagakano/LABOKit/releases/latest"><img src="https://img.shields.io/badge/VERSION-v3.3.2-d93f3f?style=flat-square" alt="Version" /></a>
  <a href="https://github.com/wagakano/LABOKit/blob/main/LICENSE"><img src="https://img.shields.io/badge/LICENSE-MIT-dfb317?style=flat-square" alt="License" /></a>
  <a href="https://github.com/wagakano/LABOKit/stargazers"><img src="https://img.shields.io/github/stars/wagakano/LABOKit?style=flat-square&label=STARS&color=dfb317" alt="Stars" /></a>
  <a href="https://github.com/wagakano/LABOKit/releases"><img src="https://img.shields.io/github/downloads/wagakano/LABOKit/total?style=flat-square&label=DOWNLOADS&color=007ec6" alt="Downloads" /></a>
</p>

LABOKit is a modular desktop tool for offline batch image processing. Built with Python and PySide6, it gives you a clean interface for background removal, upscaling, image sequencing, dithering, vectorization, and custom image editing.

*El Psy Kongroo.*

</div>

---

## What's New in LABOKit 3.3.2

- **Theme Engine**: Added dynamic Light Mode and Dark Mode theme engine with persistent state storage in settings.
- **Window Resizability & Native Border Dragging**: Made main window resizable with double-click titlebar toggle, Maximize/Restore button control, and native Windows border hit-testing.
- **PyInstaller Windowed EBADF Crashfix**: Resolved a crash on startup in `--noconsole` environments by introducing a global safe stream redirection.
- **Processing Freezes Throttled**: Decelerated the Divergence Meter status spinner refresh rate to prevent event queue starvation, resolving app lockups during batch runs.
- **Model Restorations**: Restored the `"Performance"` (`u2netp`) and `"Human Portrait"` (`silueta`) background remover models as pre-packaged offline weights.
- **UI Harmonization & Cleaner Looks**: Standardized list box components, scrollbars, dialog backgrounds, and buttons universally across all core tabs and plugins.
- **Dithering FX Animation Hint**: Added clear warning guidance in the Animation page to preview custom patterns and noise animations via the "Preview GIF" button.

---

## Features

- **Batch Background Removal:** Powered by `rembg`.
- **Batch Upscaling:** Supports GPU (Real-ESRGAN Vulkan) and CPU (PyTorch).
- **ImageLAB:** Built-in editor for creative filters, ASCII art, pixel adjustments, and glitches.
- **Image Sequencer:** Convert image frames into animated GIFs or MP4 videos.
- **Plugin System:** Add new tools with `.kit` plugin modules.
- **Offline & Private:** Runs entirely on your computer — no data leaves your machine.
- **Multilanguage Support:** Supports English, Japanese, Indonesian, Chinese, Korean, Spanish, French, German, and more.

---

## Download LABOKit 3.3.2 (Coming)

### Windows
1. Download the installer: **[LABOKit_v3.3.2_Setup.exe](https://github.com/wagakano/LABOKit/releases/download/v3.3.2/LABOKit_v3.3.2_Setup.exe)**
2. Run `LABOKit_v3.3.2_Setup.exe` to install.

### Linux
Source code and Linux build instructions are on the [main_linux branch](https://github.com/wagakano/LABOKit/tree/main_linux).

### Alternative UI (Electron Version)
Contributed by **[Chizuu](https://github.com/Chizuui)**:
- **[LABOKit Electron v1.3 Repository](https://github.com/Chizuui/labokit-electron)**

---

## Plugins & Downloads

LABOKit features can be extended using `.kit` plugins. You can download `.kit` files directly below or update them in the app via **Config** > **Check for Plugin Updates**.

### Installing Plugins (.kit)
1. Open **LABOKit**.
2. Go to **Config** > **Load Plugin (.kit)...**
3. Choose the `.kit` file to install.
4. *(To remove a plugin, delete its `.kit` file in **Config** > **Open Plugins Folder**)*.

### Available Plugins Download List

| Plugin Name | Type | Description | Download |
| :--- | :---: | :--- | :---: |
| **Video Upscaler** | Free | Upscale video files frame-by-frame using Real-ESRGAN and FFmpeg. | [`VideoUpscaler.kit`](https://github.com/wagakano/LABOKit-assets/releases/download/update2/VideoUpscaler.kit) |
| **ONNX Loader** | Free | Load custom `.onnx` upscaler models directly into LABOKit. | [`ONNXLoader.kit`](https://github.com/wagakano/LABOKit-assets/releases/download/update2/ONNXLoader.kit) |
| **QR Code Generator** | Free | Batch generate single or multi-line QR codes into PNG images. | [`QRCodeGenerator.kit`](https://github.com/wagakano/LABOKit-assets/releases/download/update2/QRCodeGenerator.kit) |
| **Watermark Remover** | Free | Remove watermarks with brush masking powered by LaMa ONNX. | [`WatermarkRemover.kit`](https://github.com/wagakano/LABOKit-assets/releases/download/update2/WatermarkRemover.kit) |
| **Quick Vector** | Advanced | Convert raster images (PNG, JPG, BMP) into SVG vector files. | Supporters Only |
| **Dithering FX** | Advanced | Retro pixel dithering, custom color palettes, and GIF animations. | Supporters Only |
| **Image Converter** | Advanced | Batch convert WebP, JPG, PNG, ICO, and BMP formats with transparency handling. | Supporters Only |

---

## 💖 Support & Rewards

If you enjoy using LABOKit and want to support ongoing development, consider donating to unlock Advanced Plugins (`Quick Vector`, `Dithering FX`, `Image Converter`):

<p align="left">
  <a href="https://ko-fi.com/s/a367e473fe"><img src="https://img.shields.io/badge/KO--FI-DONATE-ff5e5b?style=flat-square&logo=ko-fi&logoColor=white" alt="Ko-fi" /></a>
  <a href="https://trakteer.id/kano-bbif7/reward/labokit-advanced-plugins-m84J6"><img src="https://img.shields.io/badge/TRAKTEER-DONATE-c22525?style=flat-square" alt="Trakteer" /></a>
</p>

---

## Project Structure

```
LABOKit/
├── main.py                 # Main entry point, window, plugin loader, update checker
├── core_config.py          # Shared paths, constants, lazy AI engine loader
├── bg_remover_tab.py       # Background Remover tab & worker thread
├── upscaler_tab.py         # Upscaler tab & worker thread (Vulkan + PyTorch)
├── ui_shared.py            # Reusable UI components (FileDropListWidget, ZoomableImageWidget, etc.)
├── translations.py         # Translation dictionary & helper functions
├── latest_version.json     # Version metadata for in-app update checker
├── plugins_manifest.json   # Plugin registry with versions & download URLs
├── LABOKit_Installer.iss   # Inno Setup installer script
├── splash.png              # Splash screen image
├── labokit.ico             # Application icon
│
├── plugins/                # .kit plugin files
│   ├── ImageLAB.kit        # Creative effects, ASCII art, glitches
│   ├── ImageSequencer.kit  # GIF & MP4 sequence compiler
│   └── ...                 # Additional downloadable plugins
│
├── models/                 # AI model weights
├── ffmpeg/                 # Bundled ffmpeg executable
├── realesrgan_ncnn/        # Real-ESRGAN Vulkan executable & models
└── scratch/                # Utility scripts
```

---

## Running from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wagakano/LABOKit.git
   cd LABOKit
   git checkout main_windows
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

---

## Building

### Standalone Executable
```bash
.venv\Scripts\pyinstaller LABOKit.spec
```

### Windows Installer
Requires Inno Setup 6:
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" LABOKit_Installer.iss
```

---

## Plugin Development

Plugins are Python modules saved with a `.kit` extension. They are loaded dynamically at startup from `%APPDATA%/LABOKit/plugins/`.

### Plugin Template

```python
# LABOKit Plugin: My Plugin
# ID: labokit.my_plugin

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

PLUGIN_ID = "labokit.my_plugin"
PLUGIN_NAME = "My Plugin"
PLUGIN_VERSION = "1.0"

HELP_TEXT = "<h3>My Plugin</h3><p>Description here.</p>"

def create_tab(ctx=None):
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.addWidget(QLabel("Hello from My Plugin!"))
    return tab
```

---

## License & Credits

This project is licensed under the [MIT License](LICENSE).
See [LABOKit_NOTICE.txt](LABOKit_NOTICE.txt) for license details regarding bundled third-party libraries.
