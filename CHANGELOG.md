# Changelog - LABOKit v3.3.0

All notable changes and updates made during this development cycle for the release of **LABOKit v3.3.0** are documented below in chronological order.

---

## [3.3.0] - 2026-06-06

### Added
* **New Built-in Plugin: Image Sequencer (`ImageSequencer.kit`)**:
  * Added support for importing image sequences (PNG, JPG, JPEG, BMP) and converting them into animated formats.
  * Added **GIF Export**: Powered by Pillow, supporting custom frame rates (1-60 FPS).
  * Added **MP4 Export**: Compiles frames and renders high-quality videos using the bundled `ffmpeg.exe` binary.
  * Added **Natural Alphanumeric Sorting**: Ensures frames are ordered correctly (e.g. `frame9` sorted before `frame10`).
  * Added **Background Color Customization**: Allows choosing between **Transparent**, **White**, or **Black** backgrounds.
* **New BG Remover Models**:
  * Added **Performance** (`u2netp` model) for faster, lightweight background removal.
  * Added **Human Portrait** (`silueta` model) specialized for rapid and clean human silhouette extraction.
* **Documentation Files**:
  * Created `AGENTS.md` to define architectural boundaries and rules for AI assistant sessions.
  * Created `README2.md` to outline developer environment setups, prerequisites, and paths.
  * Created `SKILLS.md` to document compiling, packaging, testing, and plugin development processes.
  * Added a development rule in `AGENTS.md` requiring `CHANGELOG.md` to be updated whenever code changes, fixes, or enhancements are made.

### Fixed
* **QRCodeGenerator Loading Issue**: Added `qrcode` and `svgwrite` to `hiddenimports` in `LABOKit.spec` to prevent dynamic loading crashes (`ModuleNotFoundError`) in compiled environments.
* **First-run Metadata Crash**: Added a startup monkeypatch in `main.py` for `importlib.metadata.version` and `importlib.metadata.metadata`. This intercepts and resolves `PackageNotFoundError` crashes when `rembg` initializes in frozen PyInstaller environments.
* **GIF Transparency Trail**: Resolved a ghosting/stacking trail issue by setting `disposal=2` (restore to background color) in Pillow's GIF exporter.
* **MP4 Dimension Alignment**: Implemented automatic padding/resizing of frames to ensure dimensions are multiples of 2, resolving H.264 video rendering constraints.
* **Sequencer QTimer Crash**: Resolved an `AttributeError` during filename generation by replacing an invalid `QTimer` reference with a timestamp-based filename format.
* **Patch Downloader Import Error**: Fixed a crash in the update checker by correcting the `url2pathname` import location from `urllib.parse` to `urllib.request`.
* **Sequencer APPDATA Fallback**: Added a fallback for the `APPDATA` environment variable in `ImageSequencer.kit` to prevent crashes when executing in environments where `APPDATA` is not set.
* **Sequencer Indexed Image Transparency**: Ensured sequence frames are explicitly converted to `RGBA` before applying background fills, fixing transparency-mask/paste bugs on `P`-mode indexed images.

### Changed
* **Model Naming (UI)**:
  * Renamed `General - Fast` to `Performance` in the BG Remover dropdown.
  * Renamed `Silueta` to `Human Portrait` in the BG Remover dropdown.
* **Installer Version**: Updated version number to `3.3.0` across the application (`main.py` metadata, window titles, `latest_version.json`, `plugins_manifest.json`, and Inno Setup `LABOKit_Installer.iss` definitions).
* **Patch Zip Structure**:
  * Modified `scratch/make_patch.py` to generate `LABOKit_v3.3_Patch.zip`.
  * Removed all `.kit` plugins from the patch zip, as they are updated independently via `plugins_manifest.json`.
  * Included `translations.py` and `ui_shared.py` in the zip to make the code patch fully cumulative.

### Refactored
* **Modularized main.py**: Extracted `BgRemoverTab`/`BgRemovalWorker` (to `bg_remover_tab.py`) and `UpscalerTab`/`UpscalerWorker` (to `upscaler_tab.py`). Created `core_config.py` for shared caches, path declarations, and startup patches to improve code readability and maintainability.

### Cleaned
* Removed 20+ MB of legacy log files, crash dumps, and one-off test scripts (`trace.log`, `nuitka-crash-report.xml`, `test_out*.png`, `check_*.py`, `test_*.py`) from the project root to keep the workspace pristine.
