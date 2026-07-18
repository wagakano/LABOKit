# LABOKit - Developer Readme (README2.md)

This file provides instructions for setting up the development environment, running from source, and building the project.

---

## 1. Prerequisites & Environment Setup

### Virtual Environment
We recommend using a Python virtual environment to manage dependencies. To set it up:
1. Initialize a virtual environment in the project directory:
   ```powershell
   python -m venv .venv
   ```
2. Activate the virtual environment:
   ```powershell
   .venv\Scripts\activate
   ```
3. Install required packages:
   ```powershell
   .venv\Scripts\pip.exe install -r requirements.txt
   ```

### Major Dependencies
* **PySide6**: The GUI framework.
* **Pillow (PIL)**: Used for image processing and GIF generation.
* **rembg**: Used for background removal (requires `onnxruntime`, `pymatting`).
* **realesrgan**: Used for image upscaling (requires `basicsr`).
* **requests**: Used for manifest fetching and downloading updates.
* **qrcode & svgwrite**: Used for QR code generation.

---

## 2. Running from Source
To run the application directly from source:
* Double-click **`LABOKit.bat`** (launches `main.py` using `.venv\Scripts\pythonw.exe`), or:
* Run via command line:
  ```powershell
  .venv\Scripts\python.exe main.py
  ```

---

## 3. Standard Directories & Paths (Windows)
On startup, LABOKit checks and copies necessary runtime assets from the installation/project directory into the user's local AppData directory:
* **Models**: `%APPDATA%/LABOKit/models/` (contains U2Net models used by BG Remover).
* **Real-ESRGAN**: `%APPDATA%/LABOKit/realesrgan/` (contains upscale model weights and the CLI executable).
* **FFMPEG**: `%APPDATA%/LABOKit/ffmpeg/` (contains `ffmpeg.exe` used by ImageSequencer for MP4 generation).
* **Plugins**: `%APPDATA%/LABOKit/plugins/` (where all dynamically loaded `.kit` files are located).

---

## 4. Building & Packaging
* To compile the app: `.venv\Scripts\pyinstaller LABOKit.spec`
* To generate a patch: `.venv\Scripts\python.exe scratch/make_patch.py`
* For details on testing and advanced plugin workflows, see [AGENTS.md](file:///C:/Users/shira/Projects/LABOKit/AGENTS.md) and [SKILLS.md](file:///C:/Users/shira/Projects/LABOKit/SKILLS.md).
