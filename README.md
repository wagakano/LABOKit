# LABOKit

<img width="1796" height="523" alt="Image" src="https://github.com/user-attachments/assets/2f0b033f-3cfb-4d59-b124-379dcef14b39" />

<p align="left">
  <a href="https://github.com/wagakano/LABOKit/releases/latest"><img src="https://img.shields.io/badge/VERSION-v3.3.2-d93f3f?style=flat-square" alt="Version" /></a>
  <a href="https://github.com/wagakano/LABOKit/blob/main/LICENSE"><img src="https://img.shields.io/badge/LICENSE-MIT-dfb317?style=flat-square" alt="License" /></a>
  <a href="https://github.com/wagakano/LABOKit/stargazers"><img src="https://img.shields.io/github/stars/wagakano/LABOKit?style=flat-square&label=STARS&color=dfb317" alt="Stars" /></a>
  <a href="https://github.com/wagakano/LABOKit/releases"><img src="https://img.shields.io/github/downloads/wagakano/LABOKit/total?style=flat-square&label=DOWNLOADS&color=007ec6" alt="Downloads" /></a>
</p>

LABOKit is a modular desktop tool for offline batch image processing. Built with Python and PySide6, it gives you a clean interface for background removal, upscaling, image sequencing, dithering, and custom image operations.

"El Psy Kongroo."

## Features

- **Batch Background Removal:** Powered by `rembg`.
- **Batch Upscaling:** Supports both GPU (Vulkan) and CPU (PyTorch) processing.
- **ImageLAB:** Built-in editor for creative effects, ASCII art, and pixel adjustments.
- **Image Sequencer:** Convert sequence frames into animated GIFs or MP4 videos.
- **Plugin System:** Extend functionality using `.kit` plugin modules.
- **Offline Processing:** Runs entirely on your local machine without sending data externally.
- **Multilanguage Support:** Supports English, Japanese, Indonesian, Chinese, Korean, Spanish, French, German, and more.

## Download

### Windows
1. Download the latest installer: **[LABOKit_v3.3.2_Setup.exe](https://github.com/wagakano/LABOKit/releases/download/v3.3.2/LABOKit_v3.3.2_Setup.exe)**
2. Run `LABOKit_v3.3.2_Setup.exe` to install.

### Linux
Source instructions and Linux build steps are located in the [main_linux branch](https://github.com/wagakano/LABOKit/tree/main_linux).

## Plugins

LABOKit capabilities can be extended using `.kit` plugins.

### Installing Plugins (.kit)
1. Open **LABOKit**.
2. Go to **Config** > **Load Plugin (.kit)...**
3. Select the plugin file to install.
To remove a plugin, delete its `.kit` file via **Config** > **Open Plugins Folder**.

### Free Plugins
- **Video Upscaler:** Upscale video files using Real-ESRGAN and FFmpeg.
- **ONNX Loader:** Load custom `.onnx` upscaler models directly into LABOKit.
- **QR Code Generator:** Batch generate QR codes from multi-line text input.
- **Watermark Remover:** Interactive brush masking and inpainting using LaMa ONNX.

### Advanced Plugins
Additional plugins are available for project supporters:
- **Quick Vector:** Convert raster images (PNG, JPG, BMP) into SVG vector files.
- **Dithering FX:** Apply retro pixel dithering, custom color palettes, and GIF animations.
- **Image Converter:** Batch convert WebP, JPG, PNG, ICO, and BMP formats with transparency handling.

## Support & Rewards

Donate to support ongoing development:
- [Ko-fi](https://ko-fi.com/s/a367e473fe)
- [Trakteer](https://trakteer.id/kano-bbif7/reward/labokit-advanced-plugins-m84J6)

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

## License & Credits

This project is licensed under the [MIT License](LICENSE).
See [LABOKit_NOTICE.txt](LABOKit_NOTICE.txt) for license details regarding bundled third-party libraries.
