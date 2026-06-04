# LABOKit ⌀ 3.2

<img width="1796" height="523" alt="Image" src="https://github.com/user-attachments/assets/2f0b033f-3cfb-4d59-b124-379dcef14b39" />

**LABOKit** is a modular desktop tool for offline image processing Built with Python (PySide6), it aims to provide a fast, simple, and user-friendly batch-processing workflow with a retro "Steins;Gate" divergence meter aesthetic.

> *"El Psy Kongroo."*

## Features
* **User-Friendly & Fast:** Designed for simplicity and speed. Just load your images and click.
* **Batch Background Removal:** Powered by `rembg`.
* **Batch Upscaling (Hybrid):** Supports both GPU (Vulkan) and CPU (PyTorch) processing.
* **ImageLAB:** Built-in editor for creative effects, ASCII art, and glitches.
* **World Line Meter:** Visual decoration displaying divergence numbers.
* **Plugin System:** Extend functionality using `.kit` files.
* **Offline Mode:** All processing is done locally on your machine.
* **Multilanguage:** Supports English, Japanese (日本語), and Indonesian (Bahasa Indonesia).
  
<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/6738e1d1-5892-4af8-93f0-0e00ed375786" />
<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/86b91723-42a6-4814-8c98-056d0c93bed8" />

## What's New in 3.2

**Major UI/UX Improvements (v3.2)**
* **Split-View Slider:** Completely redesigned the before/after image comparison slider.
* **Unified Output Layout:** Standardized the "Output Folder" UI across all plugins. The path display, "Change Folder", and "Open Folder" buttons have been moved into a clean, intuitive block directly beneath the loaded images list on the left sidebar.
* **Modernized Lists & Buttons:** Upgraded the FileDropListWidget with rounded corners, subtle drop-zone borders, and a sleek layout for the "Add Images" and "Clear List" action buttons.

**Core System & Engine**
* **Translation Engine Overhaul:** Fully implemented a robust i18n system (translations.py) and passed it into the plugin context for cross-language support.
* **Canvas Renderer Re-written:** Re-architected the ZoomableImageWidget backend. Removed QScrollArea wrappers in favor of a direct SplitImageLabel painter. This entirely fixes the blank preview rendering bug (collapsed layouts).
* **Official Windows Installer:** LABOKit now ships as an official Windows installer (`.exe`) with a streamlined setup process, rather than a standalone portable zip.

**Plugin Updates**
* **Dithering FX (v3.4):** 
  * Completely Live Previews: All sliders (Brightness, Dither Scale, Bloom, etc.) now instantly trigger background rendering while being dragged.
  * Live Animations: Rendering Animated GIFs is now fully live in the background—no more modal progress bars blocking the UI while tweaking settings.
  * Massive Algorithmic Optimization: Refactored the core Python pixel loops. Implemented 256-color lookup tables for Error Diffusion (Atkinson, Stucki, etc.) and fast C-level array multiplication for Pattern Mapping (Bayer, Halftone, etc.), yielding over a 10x performance speedup.
  * Disabled the Split View slider to optimize the interface. Add Animation to static image.
* **QR Code Generator (v1.5):** 
  * Batch Generator Mode: Overhauled the UI layout to include a dedicated Multi-Line Text Input box specifically for the "Paste List" batch generator mode.
* **Quick Vector (v1.7):** 
  * Removed the redundant "Preview Zoom" slider to unify controls with the new global core zooming engine.
* **ImageLAB (v2.3):** 
  * Updated UI/UX.

## What's New in 3.1
* **Library Fixes & Performance Update:** Resolves Upscaler issues and general bugs. Build format changed from single-file portable to directory for faster startup speeds.
* **Improved BG Remover:** Improved BG Remover to remove anime background more accurate.
* **ImageLAB ASCII:** adding ASCII art generation with 8 ASCII Types (character sets) and color modes.
* **Performance Improvement:** All processing (Upscaling, BG Removal, Dithering) now runs on background threads, preventing "Not Responding" freezes.
* **Drag n Drop:** Import your images instantly by dragging them into the app.
* **Zoom Feature:** Now you can do zoom-in and out via CTRL + Scroll.
* **Multilanguage Support:** Added Interface language options for Japanese (日本語) and Indonesian (Bahasa Indonesia).
* **DitheringFX v3.3:**
    * **True Error Diffusion:** Implemented accurate Atkinson, Stucki, Burkes, and Sierra algorithms (with total 11 Algorithms).
    * **GIF Support:** Full support for importing, processing, and previewing animated GIFs.
    * **Bloom Effect:** Add retro glow to your dithered images.
    * **Enhanced Controls:** New sliders for Softness, Noise, and Error Bleed.

## 📥 Download

**(Windows)**
1.  **[Download](https://github.com/wagakano/LABOKit/releases/download/3.2/LABOKit_v3.2_Setup.exe)**
2.  Run the installer `LABOKit_v3.2_Setup.exe` and enjoy! (☆▽☆)

**(Linux)**
* **[Source Code](https://github.com/wagakano/LABOKit/tree/main_linux)**

**LABOKit Electron Ver - Alternative UI**
Contributed by: **Chizzui**
* **[Download v1.3](https://github.com/Chizuui/labokit-electron)**

## Plugins
LABOKit capabilities can be extended using `.kit` plugins.

### How to Install Plugins (.kit)
1.  Open **LABOKit**.
2.  Go to menu **Config** > **Load Plugin (.kit)...**
3.  Select the plugin file. It will be installed permanently.
*(To uninstall, simply delete the file from the plugins folder via **Config > Open Plugins Folder**).*

## Available Plugin
### 1. Video Upscaler
**File:** **[VideoUpscaler.kit](https://github.com/wagakano/LABOKit-assets/releases/download/update2/VideoUpscaler.kit)**
**Status:** Released

Upscale video files significantly using the power of **Real-ESRGAN** and **FFmpeg**. This plugin automates the complex process of frame-by-frame AI enhancement.

**Workflow:**
1.  **Extract:** Breaks down the video into individual frames.
2.  **Upscale:** Processes frames in batch using modules (Scale 2x - 4x).
3.  **Merge:** Recombines frames into a video file while preserving the original audio.

> **⚠️ Note:** This process is resource-intensive (GPU/CPU) and may take a long time depending on the video length and upscaling factor.

### 2. ONNX Loader
**File:** **[ONNXLoader.kit](https://github.com/wagakano/LABOKit-assets/releases/download/update2/ONNXLoader.kit)**
**Status:** Released

A bridge for advanced users. Allows you to load external `.onnx` Upscaler models into LABOKit's interface, making it easy to test and use custom models found online.

### 3. QR-Code Generator
**File:** **[QRCodeGenerator.kit](https://github.com/wagakano/LABOKit-assets/releases/download/update2/QRCodeGenerator.kit)**
**Status:** Released

A batch-able QR-Code generator.

### 4. Watermark Remover
**File:** **[WatermarkRemover.kit](https://github.com/wagakano/LABOKit-assets/releases/download/update2/WatermarkRemover.kit)**
**Status:** Released

Remove watermarks, text, or objects from your images using state-of-the-art Inpainting (LaMa).
* **Features:** Built-in interactive brush masking UI, auto-model downloading, and seamless background blending.

## Advanced Plugins
Also you can get the **Advanced Plugin Bundle** by supporting the development (Donation/Pay What You Want).

### 1. Quick Vector
Turn your raster images (JPG/PNG/BMP) into scalable vector graphics (SVG) instantly. (Batch-able!)
* **Best for:** Logos, icons, signatures, and black & white line art.
* **Features:** Threshold slider, smoothness control, real-time binary preview, Zoom inspection, and batch processing.

### 2. Dithering FX
Give your images a stunning retro aesthetic. Apply old-school shading and color palettes inspired by vintage hardware. (Batch-able!)
* **True Error Diffusion:** Implemented accurate Atkinson, Stucki, Burkes, and Sierra algorithms (with total 11 Algorithms).
* **GIF Support:** Full support for importing, processing, and previewing animated GIFs.
* **Bloom Effect:** Add retro glow to your dithered images.
* **Enhanced Controls:** New sliders for Softness, Noise, and Error Bleed.
* **Animation Support:** Animate your static image with dither effect!
* 🍌 If you're from r/steinsgate, you can get this Plugin for free! Just DM me your email (u/Lazy-Time-1807) and I'll send the .kit to you.

### 3. Image Converter
Batch convert WebP/JPG/PNG/ICO/BMP with quality control and transparency handling. (Batch-able!)
* **Formats:** JPG, PNG, WEBP, BMP, ICO.
* **Features:** Auto-flatten transparency, quality sliders for compression, and detailed file info inspector.

## 💖 Support & Rewards
**Donate & Get the Plugins**

[![Ko-fi](https://img.shields.io/badge/Ko--fi-F16063?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/s/a367e473fe)
[![Trakteer](https://img.shields.io/badge/Trakteer-C32aa3?style=for-the-badge&logo=trakteer&logoColor=white)](https://trakteer.id/kano-bbif7/reward/labokit-advanced-plugins-m84J6)

LABOKit is free and open-source. By purchasing this bundle (Pay What You Want), you directly support the maintenance of the app and the creation of future tools. Thank you! ( ´∀｀ )b

*By supporting, you get the `LABOKit_Advanced_Plugins.zip` containing all 3 plugins above.*


## How to Use
> A detailed user guide explaining all terms and features is available directly inside the app. Just go to the **Help** menu in the top bar!

## 📄 License & Credits
See [LABOKit_NOTICE.txt](LABOKit_NOTICE.txt) for detailed license information regarding third-party components (rembg, Real-ESRGAN, Qt, etc.).

**LABOKit** is a fan-inspired tool and is not affiliated with the creators of Steins;Gate.
