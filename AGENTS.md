# LABOKit - Agent Guide (AGENTS.md)

Welcome! This document provides the essential guidelines, architectural layout, and rules for AI agents working on the **LABOKit** project. Always refer to this document to ensure compatibility and consistency.

---

## 1. Project Overview & Architecture
LABOKit is a desktop utility application for image processing (background removal, upscaling, dithering, QR code generation, etc.) built with **Python 3.12** and **PySide6**.

### Core Files
* **[main.py](file:///C:/Users/shira/Projects/LABOKit/main.py)**: The main entry point. Houses the main window (`LABOKitMainWindow`), the tab widget, core tabs (BG Remover, Upscaler), update checking logic, and the dynamic plugin loader.
* **[ui_shared.py](file:///C:/Users/shira/Projects/LABOKit/ui_shared.py)**: Reusable UI components used by both core tabs and external plugins (e.g., `FileDropListWidget`, `ZoomableImageWidget`, `DivergenceMeter`).
* **[translations.py](file:///C:/Users/shira/Projects/LABOKit/translations.py)**: Translation dictionary and helper functions. Currently supports English (`en`), Japanese (`ja`), and Indonesian (`id`).
* **[LABOKit.spec](file:///C:/Users/shira/Projects/LABOKit/LABOKit.spec)**: The PyInstaller build specification file.

### Directory Structure
* `/plugins/`: Directory where the `.kit` plugin files reside.
* `/ffmpeg/`: Directory containing bundled `ffmpeg.exe` for video processing.
* `/models/`: Directory containing local AI model weights.
* `/realesrgan_ncnn/`: Directory containing the Real-ESRGAN Vulkan executable.
* `/scratch/`: Directory for utility scripts (e.g., `make_patch.py`, tests).
* `%APPDATA%/LABOKit/`: User-specific app data folder on Windows. Deployments copy model files, ffmpeg, and active plugins here on startup.

---

## 2. The Plugin System
Plugins are dynamically loaded on startup. They are named with a `.kit` extension but are standard Python modules. 

### Plugin Classifications
* **Built-in Plugins**: Pre-packaged and distributed inside the installer.
  * **ImageLAB** (`ImageLAB.kit`)
  * **ImageSequencer** (`ImageSequencer.kit`)
* **Free / Public Plugins**: Downloadable and updatable via the manifest.
  * **QRCodeGenerator** (`QRCodeGenerator.kit`)
  * **VideoUpscaler** (`VideoUpscaler.kit`)
  * **ONNXLoader** (`ONNXLoader.kit`)
  * **WatermarkRemover** (`WatermarkRemover.kit`)
* **Advanced / Paid Plugins**: Premium plugins sold/distributed separately.
  * **DitheringFX** (`DitheringFX.kit`)
  * **QuickVector** (`QuickVector.kit`)
  * **IMGConverter** (`IMGConverter.kit`)

### CRITICAL RULES
1. **No Paid Plugins in Builds**: Do NOT bundle advanced/paid plugins (`DitheringFX`, `QuickVector`, `IMGConverter`) into the `datas` section of the PyInstaller `LABOKit.spec` file. They must be downloaded separately.
2. **Update Manifest Rules**: All downloadable plugins are listed in [plugins_manifest.json](file:///C:/Users/shira/Projects/LABOKit/plugins_manifest.json). Local-only built-in plugins (like `ImageSequencer`) must have `"url_encoded": "-"` in the manifest.

---

## 3. Update & Patch Mechanisms
LABOKit has two systems for checking updates:
1. **In-App Patcher (System 1)**: Performs silent background checks against a manifest, downloads a patch `.zip`, extracts it locally using `tar -xf`, and restarts.
2. **Browser Redirection (System 2)**: Prompts the user and opens the download URL (e.g. the installer `.exe`) in the default web browser.

### Patch Rules
* **No Plugins in Patches**: Since version `3.3`, plugins are updated independently via `plugins_manifest.json`. Do NOT package `.kit` files inside the patch zip.
* **Cumulative Patches**: The patch zip file should be cumulative and contain all core Python files: `main.py`, `translations.py`, `ui_shared.py`, `latest_version.json`, `plugins_manifest.json`, and `README.md` (or `README2.md`).

---

## 4. Coding Conventions
* **Preserve Comments**: Maintain all existing comments, docstrings, and headers in all files.
* **Translations**: Use `tr("key")` for UI text. All strings should be registered in `translations.py`.
* **Async Workers**: Heavy processing (BG removal, upscaling, sequencing) must run in a separate `QThread` (e.g., `BgRemovalWorker`, `SequencerWorker`) to avoid freezing the PySide6 GUI.
* **Changelog Rule**: Update `CHANGELOG.md` every time a change, fix, or feature is made/implemented.
