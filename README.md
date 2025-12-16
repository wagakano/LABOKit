# LABOKit v2.0 (Linux Source Code)

<img width="1365" height="416" alt="Banner" src="https://github.com/user-attachments/assets/f4ab1e1b-de1c-4a0f-a648-25b210f0ea4f" />

**LABOKit** is a modular desktop tool for offline image processing. Built with Python (PySide6), it aims to provide a fast, simple, and user-friendly batch-processing workflow with a retro "Steins;Gate" divergence meter aesthetic.

> *"El Psy Kongroo."*

## Features

* **User-Friendly & Fast:** Designed for simplicity and speed. Just load your images and click.
* **Batch Background Removal:** Powered by `rembg` (U^2-Net).
* **Batch Upscaling (Hybrid):** Supports both GPU (Vulkan) and CPU (PyTorch) processing.
* **ImageLAB (New):** Built-in editor for creative effects and glitches.
* **World Line Meter:** Visual decoration displaying divergence numbers.
* **Plugin System:** Extend functionality using `.kit` files.
* **Offline Mode:** All processing is done locally on your machine.

<img width="1134" height="473" alt="Screen1" src="https://github.com/user-attachments/assets/580a586d-b778-41c3-a8e5-8692be7f370b" />
<img width="1132" height="476" alt="Screen2" src="https://github.com/user-attachments/assets/de3e61d1-d1b8-419f-9e70-94a95c63830d" />

## What's New in v2.0
**Latest Update:** 16 December 2025

* **✨ New Feature: ImageLAB:** A built-in image editor playground! Add effects like Pattern Overlay, Partial Color, Artifact Glitch, and Randomizer to your images.
* **🚀 CPU-Friendly Upscaling:** Added `realesr-general-x4v3` model. This allows high-quality upscaling on computers *without* Vulkan GPUs (Low-end PC friendly).
* **🔌 ONNX Loader Plugin:** Load your own custom `.onnx` upscaling models. LABOKit now serves as a GUI for your personal models.
* **🎨 UI Overhaul:** Significant improvements to the overall user interface for a cleaner look.
* **🔄 Auto-Updates:** Get notified when a new version of LABOKit is available. Plus, installed plugins now **update automatically**, eliminating manual redownloads.
* **✨ Plugin Improvements:**
    * **Dithering FX:** Refreshed UI, improved dithering results, and added more configuration options.
    * **Quick Vector:** Added **Zoom** feature to inspect vector details.
    * **Image Converter:** Fixed Transparency Glitch when converting PNG to JPG.
* **🐛 General:** Minor bug fixes and performance improvements.

<img width="1220" height="824" alt="v2_Screen1" src="https://github.com/user-attachments/assets/e81a883e-1717-44b6-b6f0-01d487c2c131" />
<img width="1213" height="816" alt="v2_Screen2" src="https://github.com/user-attachments/assets/d060263c-a7f8-4d3f-9463-fafcdade7ecf" />
<img width="1221" height="827" alt="v2_Screen3" src="https://github.com/user-attachments/assets/1c40365f-c567-4273-8c5a-f1707329bfcb" />

## 🐧 Linux Setup (Run from Source)

LABOKit for Linux must be run directly from the Python source code. You will need to install the necessary system and Python dependencies.

### Prerequisites

* Python 3.10+
* **Linux** 

### Setup

1.  **Clone Repository (Linux Branch):**
    Ensure you clone the correct branch:
    ```bash
    git clone -b main_linux [https://github.com/wagakano/LABOKit.git](https://github.com/wagakano/LABOKit.git)
    cd LABOKit
    ```

2.  **Install System Dependencies (Example Ubuntu/Debian):**
    Some Python packages, like `Pillow` and `opencv`, require system build tools and development libraries.
    ```bash
    sudo apt update
    sudo apt install build-essential python3-dev libjpeg-dev zlib1g-dev libgl1-mesa-glx
    ```
    *(Note: These commands may differ for other distributions like Arch or Fedora. Ensure you install basic development tools and image libraries.)*

3.  **Create and Activate Virtual Environment (Highly Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

4.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: This process will install large packages like PyTorch and RealESRGAN. Ensure you have a stable internet connection.)*

5.  **Model Setup**
    * LABOKit will attempt to download necessary models on the first run.
    * Ensure the `realesrgan_ncnn` folder (for Vulkan) and the `models` folder (for PyTorch) are present in the project directory. If not working, Put on "~/home/$user/.local/share/LABOKit/"

6.  **Run the Application:**
    ```bash
    python main.py
    ```

## Plugins
LABOKit capabilities can be extended using `.kit` plugins.

### How to Install Plugins (.kit)
1.  Open **LABOKit**.
2.  Go to menu **Config** > **Load Plugin (.kit)...**
3.  Select the plugin file. It will be installed permanently.
*(To uninstall, simply delete the file from the plugins folder via **Config > Open Plugins Folder**).*

## Available Plugins (Free)
### 1. Video Upscaler
**File:** **[VideoUpscaler.kit](https://github.com/wagakano/LABOKit/releases)**
**Status:** Released

Upscale video files significantly using the power of **Real-ESRGAN** and **FFmpeg**. This plugin automates the complex process of frame-by-frame AI enhancement.

**Workflow:**
1.  **Extract:** Breaks down the video into individual frames.
2.  **Upscale:** Processes frames in batch using AI models (Scale 2x - 4x).
3.  **Merge:** Recombines frames into a video file while preserving the original audio.

> **⚠️ Note:** This process is resource-intensive (GPU/CPU) and may take a long time depending on the video length and upscaling factor.

<img width="1134" height="467" alt="VideoUpscaler" src="https://github.com/user-attachments/assets/d327ebd1-9a5c-444d-8328-715bfe11f045" />

### 2. ONNX Loader
**File:** **[ONNXLoader.kit](https://github.com/wagakano/LABOKit/releases)**
**Status:** Released

A bridge for advanced users. Allows you to load external `.onnx` Super Resolution models into LABOKit's interface, making it easy to test and use custom models found online.

## Advanced Plugins
Also you can get the **Advanced Plugin Bundle** by supporting the development (Donation/Pay What You Want).

### 1. Quick Vector
Turn your raster images (JPG/PNG/BMP) into scalable vector graphics (SVG) instantly. (Batch-able!)
* **Best for:** Logos, icons, signatures, and black & white line art.
* **Features:** Threshold slider, smoothness control, real-time binary preview, Zoom inspection, and batch processing.

<img width="1132" height="560" alt="QuickVector" src="https://github.com/user-attachments/assets/a13e5f55-bd17-40ca-841f-e1c001506a14" />

### 2. Dithering FX
Give your images a stunning retro aesthetic. Apply old-school shading and color palettes inspired by vintage hardware. (Batch-able!)
* **Styles:** GameBoy (Classic/Pocket), Macintosh 1-Bit, Cyberpunk, and Halftone.
* **Algorithms:** Floyd-Steinberg, Bayer Matrix (Ordered), and Noise.
* **STEINS;GATE Special:** Unique "Glitch" animation on the World Line Meter.

* 🍌 If you're from r/steinsgate, you can get this Plugin for free! Just DM me your email (u/Lazy-Time-1807) and I'll send the .kit to you.

![Dithering FX Preview](gif/Dithering_FX_Preview.gif)

### 3. Image Converter
Batch convert WebP/JPG/PNG/ICO/BMP with quality control and transparency handling. (Batch-able!)
* **Formats:** JPG, PNG, WEBP, BMP, ICO.
* **Features:** Auto-flatten transparency, quality sliders for compression, and detailed file info inspector.

<img width="1134" height="475" alt="ImageConverter" src="https://github.com/user-attachments/assets/c974205b-f711-4a89-ae20-9cbd2cfd3dad" />

## 💖 Support & Rewards
**Donate & Get the Plugins**

[![Ko-fi](https://img.shields.io/badge/Ko--fi-F16063?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/s/a367e473fe)
[![Trakteer](https://img.shields.io/badge/Trakteer-C32aa3?style=for-the-badge&logo=trakteer&logoColor=white)](https://trakteer.id/kano-bbif7/showcase/labokit-advanced-plugins-m84J6)

LABOKit is free and open-source. By purchasing this bundle (Pay What You Want), you directly support the maintenance of the app and the creation of future tools. Thank you! ( ´∀｀ )b

*By supporting, you get the `LABOKit_Advanced_Plugins.zip` containing all 3 plugins above.*

## 📄 License & Credits
See [LABOKit_NOTICE.txt](LABOKit_NOTICE.txt) for detailed license information regarding third-party components (rembg, Real-ESRGAN, Qt, etc.).

**LABOKit** is a fan-inspired tool and is not affiliated with the creators of Steins;Gate.
