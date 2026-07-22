# Changelog - LABOKit v3.3.2

All notable changes and updates made during this development cycle for the release of **LABOKit v3.3.2** are documented below.

---

## [3.3.2] - 2026-07-19

### Added
* **Theme System**: Implemented dynamic Light Mode and Dark Mode theme engine with persistent state storage in `%APPDATA%/LABOKit/settings.json` and menu selection under `Config -> Theme`.
* **Window Resizability & Native Border Dragging**: Made main window resizable (`resize(1200, 800)`, `setMinimumSize(900, 600)`) with double-click titlebar toggle, Maximize/Restore button control, and `WM_NCHITTEST` native Windows border hit-testing for frameless window resizing (Issue #22).
* **macOS Traffic Light Window Controls**: Redesigned title bar window control buttons to clean, borderless macOS traffic light color-coded circles (Red, Yellow, Green) without text symbols.
* **Universal Dithering FX Button Style**: Adopted the Dithering FX button design (rounded 5px, vertical linear gradient `#ffffff` -> `#d8dfee`, `#9ca7c2` border) as the universal button standard across all tabs and components, including WatermarkRemover's "Remove Watermark" button.
* **Consistent Setting Container Width**: Standardized the left Setting Container to 1:3 ratio across all tabs — `QRCodeGenerator.kit`, `ImageSequencer.kit`, and `VideoUpscaler.kit` updated to match BG Remover, Upscaler, and Dithering FX.
* **ImageSequencer Logs Relocated**: Moved process logs (`QPlainTextEdit`) and progress bar from the right preview panel to the left Setting Container, below the "Generate Sequence" button.
* **Seamless Workspace Layout**: Removed `border-radius` from all `QFrame` containers, `#MainFrame`, and `QTabWidget::pane` for a connected layout from tabs to workspace to status bar. Restored proper `1px solid #b3bcd1` borders on `QFrame` list box containers and Divergence Status Meter (`#PixelBar`).
* **Tab Scroller Arrows Removed**: Disabled right-side tab navigation scroll arrows on `QTabBar` (`setUsesScrollButtons(False)` and zeroed scroller dimensions in QSS).
* **VideoUpscaler Cleanup**: Removed "No video loaded." placeholder label.

### Changed
* **Documentation Clean-Up**: Removed release changelogs from `README.md` (moved exclusively to GitHub Releases descriptions), removed all emojis, and rewrote documentation with clear, natural language without AI buzzwords.

---

## [3.3.1] - 2026-07-18

### Added
* **Multi-Language Expansion**: Added full translations for 12 new languages (Chinese Simplified/Traditional, Korean, Spanish, Portuguese, French, German, Thai, Vietnamese, Russian, Arabic, Malay).
* **Empty State Guidance**: Added user-friendly placeholder hint ("Drop files here") to `FileDropListWidget` when list contains no files.

### Fixed
* **Numba/Rembg Crash**: Implemented automatic dynamic `numba` mock fallback in `core_config.py` to resolve `cannot import name 'njit' from 'numba'` error in compiled environments.

### Optimized
* **Batch Import Speed**: Implemented companion `set`-based membership checks for image deduplication in `BgRemoverTab` and `UpscalerTab`, reducing file addition search complexity from O(N) to O(1) and preventing UI lockups on large batch drops.

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
* **Update Download URL 404**: Fixed the release download URL in `latest_version.json` and `README.md` from `/download/3.3/` to `/download/v3.3.0/` to match the actual GitHub release tag.
* **Missing `realesrgan-ncnn-vulkan.exe` Error**: Added robust fallback execution paths in `core_config.py`, `upscaler_tab.py`, `ImageSequencer.kit`, and `VideoUpscaler.kit`. If `realesrgan-ncnn-vulkan.exe`, `ffmpeg.exe`, or `ffprobe.exe` are missing from `%APPDATA%` (e.g. blocked by antivirus), the app now runs them directly from the installer's internal folder (`_internal`).
* **PyInstaller `collect_metadata` Import**: Fixed `ImportError` in `LABOKit.spec` by replacing deprecated `collect_metadata` with `copy_metadata` for PyInstaller 6.x compatibility.

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
