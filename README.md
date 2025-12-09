# LABOKit v1.4

<img width="1365" height="416" alt="Image" src="https://github.com/user-attachments/assets/f4ab1e1b-de1c-4a0f-a648-25b210f0ea4f" />

**LABOKit** is a modular desktop tool for offline image processing Built with Python (PySide6), it aims to provide a fast, simple, and user-friendly batch-processing workflow with a retro "Steins;Gate" divergence meter aesthetic.

> *"El Psy Kongroo."*

## Features

* User-Friendly & Fast: Designed for simplicity and speed. The interface is clean and easy to understand—just load your images and click.
* Batch Background Removal: Powered by `rembg` (U^2-Net).
* Batch Upscaling: Powered by `Real-ESRGAN-ncnn-vulkan`.
* World Line Meter: Visual decoration displaying divergence numbers.
* Plugin System: Extend functionality using `.kit` files.
* Offline Mode: All processing is done locally on your machine.

<img width="1134" height="473" alt="Image" src="https://github.com/user-attachments/assets/580a586d-b778-41c3-a8e5-8692be7f370b" />
<img width="1132" height="476" alt="Image" src="https://github.com/user-attachments/assets/de3e61d1-d1b8-419f-9e70-94a95c63830d" />

## 📥 Download (Portable Version)

1.  Go to the **[Releases](https://github.com/wagakano/LABOKit/releases)** page.
2.  Download the `LABOKit_v1.4.exe` (or latest version).
3.  Run `LABOKit.exe`.

> **Note:** The portable version is larger in size because it bundles the Python engine and necessary libraries.

> **⚠️ Hardware Requirement:**
> The **Upscaling** feature is powered by Real-ESRGAN (NCNN) and requires a **GPU with Vulkan support**. If your GPU does not support Vulkan, the upscaler process may fail or crash.
> **⚠️ Performance Notice:**
> Since LABOKit processes everything locally using advanced AI models, performance depends entirely on your computer's specifications.
> * **High-end PC / Dedicated GPU:** Fast & smooth processing.
> * **Low-end PC / Integrated Graphics:** Expect longer processing times and potential lag during heavy tasks (like Upscaling).
> * **Note For Linux Users:** You Must Manually download the ffmpeg file on [ffmpeg official website](https://github.com/BtbN/FFmpeg-Builds/releases) and choose **ffmpeg-master-latest-linux64-gpl.tar.xz**.

## Plugins
LABOKit capabilities can be extended using `.kit` plugins. 

### How to Install Plugins (.kit)
1.  Open **LABOKit**.
2.  Go to menu **Config** > **Load Plugin (.kit)...**
3.  Select the plugin file. It will be installed permanently.
*(To uninstall, simply delete the file from the plugins folder via **Config > Open Plugins Folder**).*

### Available Plugin 
* **VideoUpscaler.kit** (Work in Progress)
* **PhotoPull.kit** (Work in Progress)

## Advanced Plugins
Also you can get the **Advanced Plugin Bundle** by supporting the development (Donation/Pay What You Want).

### 1. Quick Vector
Turn your raster images (JPG/PNG/BMP) into scalable vector graphics (SVG) instantly. (Batch-able!)
* **Best for:** Logos, icons, signatures, and black & white line art.
* **Features:** Threshold slider, smoothness control, real-time binary preview, and batch processing.

<img width="1132" height="560" alt="Image" src="https://github.com/user-attachments/assets/a13e5f55-bd17-40ca-841f-e1c001506a14" />

### 2. Dithering FX 
Give your images a stunning retro aesthetic. Apply old-school shading and color palettes inspired by vintage hardware. (Batch-able!)
* **Styles:** GameBoy (Classic/Pocket), Macintosh 1-Bit, Cyberpunk, and Halftone.
* **Algorithms:** Floyd-Steinberg, Bayer Matrix (Ordered), and Noise.
* **STEINS;GATE Special:** Unique "Glitch" animation on the World Line Meter.

![Dithering FX Preview](gif/Dithering_FX_Preview.gif)

### 3. Image Converter
Batch convert WebP/JPG/PNG/ICO/BMP with quality control and transparency handling. (Batch-able!)
* **Formats:** JPG, PNG, WEBP, BMP, ICO.
* Auto-flatten transparency for JPG, quality sliders for compression, and detailed file info inspector.

<img width="1134" height="475" alt="Image" src="https://github.com/user-attachments/assets/c974205b-f711-4a89-ae20-9cbd2cfd3dad" />

## 💖 Support & Rewards
**Donate & Get the Plugins**

[![Ko-fi](https://img.shields.io/badge/Ko--fi-F16063?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/s/a367e473fe)
[![Trakteer](https://img.shields.io/badge/Trakteer-C32aa3?style=for-the-badge&logo=trakteer&logoColor=white)](https://trakteer.id/kano-bbif7/showcase/labokit-advanced-plugins-m84J6)

LABOKit is free and open-source. By purchasing this bundle (Pay What You Want), you directly support the maintenance of the app and the creation of future tools. Thank you! ( ´∀｀ )b

*By supporting, you get the `LABOKit_Advanced_Plugins.zip` containing all 3 plugins above.*

## Installation

### Prerequisites
* Python 3.10+
* Windows (Recommended)
* **Vulkan-compatible GPU** (Required for the Upscaler feature)

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

3.  **Model Setup (Important)**
    
    * **Background Removal (`rembg`):**
        * **Automatic:** The application will automatically download the required model (`u2net.onnx`, ~170MB) into the `models/` folder on the first run.
        * **Manual (Offline):** If you prefer manual setup, download [u2net.onnx](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx), create a folder named `models` in the project root, and place the file there (`LABOKit/models/u2net.onnx`).

    * **Upscaler (`Real-ESRGAN`):**
        * Download `realesrgan-ncnn-vulkan.exe` and the models (e.g., `realesrgan-x4plus.bin`, etc.).
        * Place them in the `realesrgan/` folder inside the project directory.
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
