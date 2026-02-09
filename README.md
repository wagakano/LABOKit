# LABOKit ⌀ v3.0

<img width="1365" height="416" alt="Banner" src="https://github.com/user-attachments/assets/f4ab1e1b-de1c-4a0f-a648-25b210f0ea4f" />

**LABOKit** is a modular desktop tool for offline image processing Built with Python (PySide6), it aims to provide a fast, simple, and user-friendly batch-processing workflow with a retro "Steins;Gate" divergence meter aesthetic.

> *"El Psy Kongroo."*

## Features

* **User-Friendly & Fast:** Designed for simplicity and speed. Just load your images and click.
* **Batch Background Removal:** Powered by `rembg` (U^2-Net).
* **Batch Upscaling (Hybrid):** Supports both GPU (Vulkan) and CPU (PyTorch) processing.
* **ImageLAB:** Built-in editor for creative effects, ASCII art, and glitches.
* **World Line Meter:** Visual decoration displaying divergence numbers.
* **Plugin System:** Extend functionality using `.kit` files.
* **Offline Mode:** All processing is done locally on your machine.
* **Multilanguage:** Supports English, Japanese (日本語), and Indonesian (Bahasa Indonesia).

## What's New in v3.0
* **Drag n Drop:** Import your images instantly by dragging them into the app.
* **Zoom Feature** Now you can do zoom-in and out via CTRL + Scroll.
* **Multilanguage Support:** Added Interface language options for Japanese (日本語) and Indonesian (Bahasa Indonesia).
* **Performance Boost:** All processing (Upscaling, BG Removal, Dithering) now runs on background threads, preventing "Not Responding" freezes.
* **Improved BG Remover:** Improved BG Remover to remove anime background more accurate and precise.
* **DitheringFX v3.3:**
    * **True Error Diffusion:** Implemented accurate Atkinson, Stucki, Burkes, and Sierra algorithms (with total 11 Algorithms).
    * **GIF Support:** Full support for importing, processing, and previewing animated GIFs.
    * **Bloom Effect:** Add retro glow to your dithered images.
    * **Enhanced Controls:** New sliders for Softness, Noise, and Error Bleed.
* **ImageLAB ASCII:** adding ASCII art generation with 8 ASCII Types (character sets) and color modes.
* **Improved Stability:** Fixed crashes related to Video Upscaling and GIF rendering.

## 📥 Download

**(Windows)**
1.  Go to the **[Releases](https://github.com/wagakano/LABOKit/releases/tag/v3.0)** page.
2.  Download the `LABOKit_v3.0.exe`.
3.  Run `LABOKit_v3.0.exe` and enjoy! (☆▽☆)

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

**Now you can zoom-in zoom-out via CTRL + Scroll**

## Available Plugin
### 1. Video Upscaler
**File:** **[VideoUpscaler.kit](https://github.com/wagakano/LABOKit/releases/download/v1.4/VideoUpscaler.kit)**
**Status:** Released

Upscale video files significantly using the power of **Real-ESRGAN** and **FFmpeg**. This plugin automates the complex process of frame-by-frame AI enhancement.

**Workflow:**
1.  **Extract:** Breaks down the video into individual frames.
2.  **Upscale:** Processes frames in batch using AI models (Scale 2x - 4x).
3.  **Merge:** Recombines frames into a video file while preserving the original audio.

> **⚠️ Note:** This process is resource-intensive (GPU/CPU) and may take a long time depending on the video length and upscaling factor.

### 2. ONNX Loader
**File:** **[ONNXLoader.kit](https://github.com/wagakano/LABOKit/releases/download/v2.0/ONNXLoader.kit)**
**Status:** Released

A bridge for advanced users. Allows you to load external `.onnx` Upscaler models into LABOKit's interface, making it easy to test and use custom models found online.

### 3. QR-Code Generator
**File:** **[QRCodeGenerator.kit](https://github.com/wagakano/LABOKit/releases/download/v2.0/QRCodeGenerator.kit)**
**Status:** Released

A batch-able QR-Code generator.

## Advanced Plugins
Also you can get the **Advanced Plugin Bundle** by supporting the development (Donation/Pay What You Want).

### 1. Quick Vector
Turn your raster images (JPG/PNG/BMP) into scalable vector graphics (SVG) instantly. (Batch-able!)
* **Best for:** Logos, icons, signatures, and black & white line art.
* **Features:** Threshold slider, smoothness control, real-time binary preview, Zoom inspection, and batch processing.

### 2. Dithering FX
Give your images a stunning retro aesthetic. Apply old-school shading and color palettes inspired by vintage hardware. (Batch-able!)
* **Styles:** GameBoy (Classic/Pocket), Cyberpunk, Halftone, and Lines.
* **Algorithms:** Floyd-Steinberg, Bayer Matrix (Ordered), and Noise.
* **STEINS;GATE Special:** Unique "Glitch" animation on the World Line Meter.

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

## Developer Setup (Source Code)
> **⚠️ Note:** You do NOT need to follow these steps if you just want to use the app. Please download the ready-to-use .exe from the **[Releases](https://github.com/wagakano/LABOKit/releases)** Page.

### Prerequisites
* Python 3.10+
* Windows (Recommended)

### Setup
1.  Clone the repository:
    ```bash
    git clone [https://github.com/wagakano/LABOKit.git](https://github.com/wagakano/LABOKit.git)
    cd LABOKit
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: PyTorch and RealESRGAN modules are required for full feature support)*

3.  **Model Setup**
    * BG Remover (rembg)
      * **Manual (Offline):** for manual setup, download [u2net.onnx](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx) and [isnet-anime.onnx](https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-anime.onnx), create a folder named `models` in the project root, and place the file there (`LABOKit/models/`).
    * Upscaler (realesrgan) - ensure the `realesrgan_ncnn` folder (containing the executable) and the `models` folder (containing .pth files) are correctly placed in the project directory.
        * Download [realesrgan-ncnn-vulkan.exe](https://github.com/xinntao/Real-ESRGAN?tab=readme-ov-file#portable-executable-files-ncnn) and the models (e.g., `realesrgan-x4plus.bin`, etc.).
        * Place them in the `realesrgan_ncnn/` folder inside the project directory.\
        * Add `realesr-general-x4v3.pth` into `realesrgan_ncnn/models/`
        * *(Note: Ensure the executable path matches the setup in `main.py`)*

4.  Run the application:
    ```bash
    python main.py
    ```

## How to Use
> A detailed user guide explaining all terms and features is available directly inside the app. Just go to the **Help** menu in the top bar!

## 📄 License & Credits
See [LABOKit_NOTICE.txt](LABOKit_NOTICE.txt) for detailed license information regarding third-party components (rembg, Real-ESRGAN, Qt, etc.).

**LABOKit** is a fan-inspired tool and is not affiliated with the creators of Steins;Gate.
