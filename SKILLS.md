# LABOKit - Developer Skills Guide (SKILLS.md)

This document contains instructions for common development, testing, and release packaging workflows in LABOKit.

---

## 1. Creating a New Plugin
To build a new plugin (e.g. `NewPlugin.kit`), follow these rules:

1. **Naming**: Create a file named `NewPlugin.kit` inside the `plugins/` folder.
2. **Metadata**: Define the following global variables at the top of the file:
   ```python
   PLUGIN_NAME = "My New Plugin"
   HELP_TEXT = "Describe how to use this plugin."
   ```
3. **Entry Point**: Implement a `create_tab(parent)` function that returns a `QWidget` representing the plugin's UI:
   ```python
   def create_tab(parent):
       return MyPluginWidget(parent)
   ```
4. **Translations**: Plugins can access the global translation helper `tr` which is automatically injected as `mod.tr = tr` by the main app loader.
5. **No GUI Freezes**: Use `QThread` for long-running operations.

---

## 2. Generating a Release Patch
We use a python script to package a cumulative update patch containing all core files (excluding plugins, which are updated via the manifest):

1. Run the patch creation script:
   ```powershell
   .venv\Scripts\python.exe scratch\make_patch.py
   ```
2. This creates `dist/LABOKit_v[Version]_Patch.zip`.
3. Verify the zip contains:
   * `main.py`
   * `core_config.py`
   * `bg_remover_tab.py`
   * `upscaler_tab.py`
   * `translations.py`
   * `ui_shared.py`
   * `latest_version.json`
   * `plugins_manifest.json`
   * `README.md` (or `README2.md`)

---

## 3. Building the Standalone Executable
We use PyInstaller to compile the source code into a standalone directory-based bundle:

1. Compile the app using the spec file:
   ```powershell
   .venv\Scripts\pyinstaller LABOKit.spec
   ```
2. The compiled application is output to `dist/LABOKit/`.
3. To build the installer `.exe` from this bundle, compile the Inno Setup script `LABOKit_Installer.iss` using Inno Setup Compiler.

---

## 4. Local Testing & Verification
Before releasing any updates, run the automated verification scripts:

* **Startup & Tab Load Test**: Verifies that the GUI starts up without errors and all tabs load correctly.
  ```powershell
  .venv\Scripts\python.exe C:\Users\shira\.gemini\antigravity\brain\a02a180f-9201-4790-bfbc-ed2c0553b717\scratch\test_ui_startup.py
  ```
* **Image Sequencer Encoding Test**: Verifies GIF and MP4 exports.
  ```powershell
  .venv\Scripts\python.exe C:\Users\shira\.gemini\antigravity\brain\a02a180f-9201-4790-bfbc-ed2c0553b717\scratch\test_sequencer.py
  ```
