# LABOKit ⌀ v2.0 [DOWNLOAD](https://github.com/wagakano/LABOKit?tab=readme-ov-file#-download-portable-version)

<img width="1365" height="416" alt="Banner" src="https://github.com/user-attachments/assets/f4ab1e1b-de1c-4a0f-a648-25b210f0ea4f" />

**LABOKit** is a modular desktop tool for offline image processing Built with Python (PySide6), it aims to provide a fast, simple, and user-friendly batch-processing workflow with a retro "Steins;Gate" divergence meter aesthetic.

> *"El Psy Kongroo."*

## Features

* **User-Friendly & Fast:** Designed for simplicity and speed. Just load your images and click.
* **Batch Background Removal:** Powered by `rembg` (U^2-Net).
* **Batch Upscaling (Hybrid):** Supports both GPU (Vulkan) and CPU (PyTorch) processing.
* **ImageLAB:** Built-in editor for creative effects and glitches.
* **World Line Meter:** Visual decoration displaying divergence numbers.
* **Plugin System:** Extend functionality using `.kit` files.
* **Offline Mode:** All processing is done locally on your machine.

<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/515b5725-dcde-4384-a91d-d56f8badfb49" />
<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/9566a831-61ea-4e3d-8237-2fbcb614ea51" />

![Image](https://github.com/user-attachments/assets/f38a6769-3242-4527-9863-790afc4c2c7b)

## What's New in v2.0
* **New Feature: ImageLAB:** A built-in image editor playground! Add effects like Pattern Overlay, Partial Color, Artifact Glitch, and Randomizer to your images.
* **CPU-Friendly Upscaling:** Added `realesr-general-x4v3` model. This allows upscaling on computers *without* Vulkan GPUs (Low-end PC friendly).
* **ONNX Loader Plugin:** Load your own custom `.onnx` upscaling models. LABOKit now serves as a GUI for your personal models.
* **UI Overhaul:** Significant improvements to the overall user interface for a cleaner look.
* **Auto-Updates:** Get notified when a new version of LABOKit is available. Plus, installed plugins now **update automatically**, eliminating manual redownloads.
* **Plugin Improvements:**
    * **Dithering FX:** Refreshed UI, improved dithering results, and added more configuration options.
    * **Quick Vector:** Added **Zoom** feature to inspect vector details.
    * **Image Converter:** Fixed Transparency Glitch when converting PNG to JPG.
* **General:** Minor bug fixes and performance improvements.

## 📥 Download (Portable Version)

1.  Go to the **[Releases](https://github.com/wagakano/LABOKit/releases)** page.
2.  Download the `LABOKit_v2.0.exe` (or latest version).
3.  Run `LABOKit.exe` and enjoy! (☆▽☆)

> **⚠️ Hardware Requirement:**
> LABOKit processes everything locally using advanced AI models.
> * **Standard Upscaling (x4plus):** Requires a **Vulkan-compatible GPU**.
> * **CPU Upscaling (General x4v3):** Works on **any computer** (including non-Vulkan/Integrated Graphics).
> * **Performance:** High-end PCs will process images instantly. Low-end PCs may experience longer processing times during upscaling.
> * **Note For Linux Users:** You Must Manually download the ffmpeg file on [ffmpeg official website](https://github.com/BtbN/FFmpeg-Builds/releases) and choose **ffmpeg-master-latest-linux64-gpl.tar.xz**.

## Plugins
LABOKit capabilities can be extended using `.kit` plugins.

### How to Install Plugins (.kit)
1.  Open **LABOKit**.
2.  Go to menu **Config** > **Load Plugin (.kit)...**
3.  Select the plugin file. It will be installed permanently.
*(To uninstall, simply delete the file from the plugins folder via **Config > Open Plugins Folder**).*

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

<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/e130932c-84e3-4252-b81a-d8511eda4b21" />

### 2. ONNX Loader
**File:** **[ONNXLoader.kit](https://github.com/wagakano/LABOKit/releases/download/v2.0/ONNXLoader.kit)**
**Status:** Released

A bridge for advanced users. Allows you to load external `.onnx` Upscaler models into LABOKit's interface, making it easy to test and use custom models found online.

<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/5c746637-00cc-4582-9a30-93e433a83ab0" />

### 3. QR-Code Generator
**File:** **[QRCode.kit](https://github.com/wagakano/LABOKit/releases)**
**Status:** Work in Progress

A batch-able QR-Code generator.

## Advanced Plugins
Also you can get the **Advanced Plugin Bundle** by supporting the development (Donation/Pay What You Want).

### 1. Quick Vector
Turn your raster images (JPG/PNG/BMP) into scalable vector graphics (SVG) instantly. (Batch-able!)
* **Best for:** Logos, icons, signatures, and black & white line art.
* **Features:** Threshold slider, smoothness control, real-time binary preview, Zoom inspection, and batch processing.

<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/68f4b04d-81e6-469c-b53f-aaf61122f2c6" />

### 2. Dithering FX
Give your images a stunning retro aesthetic. Apply old-school shading and color palettes inspired by vintage hardware. (Batch-able!)
* **Styles:** GameBoy (Classic/Pocket), Cyberpunk, Halftone, and Lines.
* **Algorithms:** Floyd-Steinberg, Bayer Matrix (Ordered), and Noise.
* **STEINS;GATE Special:** Unique "Glitch" animation on the World Line Meter.

* 🍌 If you're from r/steinsgate, you can get this Plugin for free! Just DM me your email (u/Lazy-Time-1807) and I'll send the .kit to you.

![Image](https://github.com/user-attachments/assets/d1492680-1d2e-40c0-a48a-1783d8431dc8)

### 3. Image Converter
Batch convert WebP/JPG/PNG/ICO/BMP with quality control and transparency handling. (Batch-able!)
* **Formats:** JPG, PNG, WEBP, BMP, ICO.
* **Features:** Auto-flatten transparency, quality sliders for compression, and detailed file info inspector.

<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/462317a8-f070-495a-b803-e0dc187d1fe0" />

## 💖 Support & Rewards
**Donate & Get the Plugins**

[![Ko-fi](https://img.shields.io/badge/Ko--fi-F16063?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/s/a367e473fe)
[![Trakteer](https://img.shields.io/badge/Trakteer-C32aa3?style=for-the-badge&logo=trakteer&logoColor=white)](https://trakteer.id/kano-bbif7/showcase/labokit-advanced-plugins-m84J6)

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
    * LABOKit will attempt to download necessary models on the first run.
    * For the Upscaler, ensure the `realesrgan_ncnn` folder (containing the executable) and the `models` folder (containing .pth files) are correctly placed in the project directory.

4.  Run the application:
    ```bash
    python main.py
    ```

## How to Use
> A detailed user guide explaining all terms and features is available directly inside the app. Just go to the **Help** menu in the top bar!

## 📄 License & Credits
See [LABOKit_NOTICE.txt](LABOKit_NOTICE.txt) for detailed license information regarding third-party components (rembg, Real-ESRGAN, Qt, etc.).

**LABOKit** is a fan-inspired tool and is not affiliated with the creators of Steins;Gate.