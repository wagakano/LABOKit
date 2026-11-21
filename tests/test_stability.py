import base64
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QMessageBox, QToolButton, QWidget


ROOT = Path(__file__).resolve().parents[1]


def load_plugin(name):
    path = ROOT / "plugins" / f"{name}.kit"
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    plugin = importlib.util.module_from_spec(spec)
    loader.exec_module(plugin)
    return plugin


class WindowsStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = tempfile.TemporaryDirectory(dir=ROOT)
        cls.addClassCleanup(cls.profile.cleanup)
        profile_env = patch.dict(os.environ, {"APPDATA": cls.profile.name, "QT_QPA_PLATFORM": "offscreen"})
        profile_env.start()
        cls.addClassCleanup(profile_env.stop)

        import main

        cls.main = main
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.app.setProperty("labokitTheme", "light")
        self.app.setStyleSheet(self.main.get_app_stylesheet("light"))

    def wait_for_worker(self, tab):
        deadline = time.monotonic() + 10
        while tab.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertIsNone(tab.worker, "worker did not finish")
        QTest.qWait(30)  # Let Qt deliver any additional queued completion signals.

    def test_plugin_update_preserves_previous_version_on_failure_and_newer_version_on_restart(self):
        baseline = b'PLUGIN_VERSION = "1.5"\ndef create_tab():\n    pass\n'
        newer = baseline.replace(b"1.5", b"1.6")
        address = "https://example.invalid/VideoUpscaler.kit"
        manifest = {"VideoUpscaler": {"version": "1.6", "url_encoded": base64.b64encode(address.encode()).decode()}}
        response = MagicMock()
        response.__enter__.return_value = response

        def interrupted(**kwargs):
            yield newer[:15]
            raise OSError("connection interrupted")

        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            root = Path(folder)
            bundled = root / "runtime" / "plugins"
            installed = root / "profile"
            bundled.mkdir(parents=True)
            installed.mkdir()
            target = installed / "VideoUpscaler.kit"
            target.write_bytes(baseline)
            (bundled / target.name).write_bytes(baseline)
            updater = self.main.PluginUpdater()
            completed = []
            updater.plugin_updated.connect(lambda *event: completed.append(event))

            with (
                patch.object(self.main, "PLUGIN_DIR", installed),
                patch.object(self.main, "INTERNAL_DIR", bundled.parent),
                patch.object(self.main, "sync_folder"),
                patch("urllib.request.urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(json.dumps(manifest).encode())),
                patch("requests.get", return_value=response),
            ):
                response.iter_content.side_effect = interrupted
                updater.run()
                self.assertEqual(target.read_bytes(), baseline)
                response.iter_content.side_effect = None
                response.iter_content.return_value = iter([b'<html>not a plugin</html>'])
                updater.run()
                self.assertEqual(target.read_bytes(), baseline)
                self.assertEqual(completed, [])
                self.assertEqual(list(installed.iterdir()), [target])

                response.iter_content.return_value = iter([newer])
                updater.run()
                self.main.deploy_assets()
                self.assertEqual(target.read_bytes(), newer)
                self.assertEqual(completed, [("VideoUpscaler", "1.6")])

    def test_app_update_manifest_and_download_verify_the_installer(self):
        installer = b"test Windows installer data"
        digest = hashlib.sha256(installer).hexdigest()
        release = "https://github.com/wagakano/LABOKit/releases/tag/v3.3.3-windows"
        address = "https://github.com/wagakano/LABOKit/releases/download/v3.3.3-windows/LABOKit_Setup.exe"
        manifest = {"version": "3.3.3", "url": release, "changelog": "Update", "installer": {"url": address, "sha256": digest}}
        checker = self.main.AppUpdateChecker()
        notices = []
        checker.found_update.connect(lambda *event: notices.append(event))
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(manifest).encode())):
            checker.run()
        self.assertEqual(notices, [("3.3.3", release, "Update", (address, digest))])
        manifest.pop("installer")
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(manifest).encode())):
            checker.run()
        self.assertIsNone(notices[-1][3])

        response = MagicMock()
        response.__enter__.return_value = response
        response.headers = {"content-length": str(len(installer))}
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            staged = Path(folder) / "LABOKit-update.exe"
            staged.write_bytes(b"previous verified installer")
            with patch.object(self.main, "APP_DATA", staged.parent), patch("requests.get", return_value=response):
                downloader = self.main.InstallerDownloader(address, digest)
                completed, errors = [], []
                downloader.downloaded.connect(completed.append)
                downloader.error.connect(errors.append)
                response.iter_content.return_value = iter([b"incomplete installer"])
                downloader.run()
                self.assertEqual(completed, [])
                self.assertIn("checksum", errors[0])
                self.assertEqual(staged.read_bytes(), b"previous verified installer")
                self.assertEqual(list(staged.parent.iterdir()), [staged])

                response.iter_content.return_value = iter([installer])
                downloader.run()
                self.assertEqual(completed, [str(staged)])
                self.assertEqual(staged.read_bytes(), installer)

    def test_app_update_asks_before_closing_to_open_setup(self):
        window = MagicMock()
        window._closing = False
        installer = ("https://github.com/wagakano/LABOKit/releases/download/v3.3.3-windows/LABOKit_Setup.exe", "a" * 64)
        release = "https://github.com/wagakano/LABOKit/releases/tag/v3.3.3-windows"

        with patch.object(sys, "frozen", True, create=True), patch.object(self.main.ModernDialog, "confirm", return_value=True):
            self.main.LABOKitMainWindow.show_app_update_dialog(window, "3.3.3", release, "Update", installer)
        window.download_installer.assert_called_once_with(*installer)

        with patch.object(self.main.ModernDialog, "confirm", return_value=False):
            self.main.LABOKitMainWindow.on_installer_downloaded(window, "update.exe")
        window.close.assert_not_called()

        with patch.object(self.main.ModernDialog, "confirm", return_value=True):
            self.main.LABOKitMainWindow.on_installer_downloaded(window, "update.exe")
        self.assertEqual(window.pending_installer, "update.exe")
        window.close.assert_called_once()

    def test_dropdown_popup_rows_have_opaque_backgrounds(self):
        combo = QComboBox()
        combo.addItems(["General", "Anime", "General - Performance"])
        combo.resize(260, 32)
        combo.show()
        self.addCleanup(combo.close)
        for theme, background in (("light", "#ffffff"), ("dark", "#1c1c1c")):
            with self.subTest(theme=theme):
                self.app.setStyleSheet(self.main.get_app_stylesheet(theme))
                combo.setCurrentIndex(0)
                combo.showPopup()
                try:
                    self.app.processEvents()
                    view = combo.view()
                    row = view.visualRect(combo.model().index(1, 0))
                    viewport = view.viewport()
                    image = viewport.grab().toImage()
                    pixel = image.pixelColor(image.width() - 15, row.center().y())
                    self.assertEqual(pixel.alpha(), 255)
                    self.assertEqual(pixel.name(), background)
                    QTest.mouseClick(viewport, Qt.LeftButton, pos=row.center())
                    self.assertEqual(combo.currentText(), "Anime")
                finally:
                    combo.hidePopup()

    def test_dialogs_use_dark_mode_with_a_nested_parent(self):
        root = QWidget()
        root.current_theme = "dark"
        nested_tab = QWidget(root)
        self.app.setProperty("labokitTheme", "dark")
        self.app.setStyleSheet(self.main.get_app_stylesheet("dark"))

        message = self.main.ModernDialog(nested_tab, message="A result message")
        progress = self.main.ModernProgressDialog(parent=nested_tab)
        native = QMessageBox(nested_tab)
        native.setText("Another result message")
        for dialog, expected in [
            (message, "A result message"),
            (progress, "Processing..."),
            (native, "Another result message"),
        ]:
            label = next(label for label in dialog.findChildren(QLabel) if label.text() == expected)
            label.ensurePolished()
            self.assertEqual(label.palette().color(QPalette.WindowText).name(), "#e1e1e6")

        explicit_light = self.main.ModernDialog(nested_tab, message="Light preview", theme="light")
        label = next(label for label in explicit_light.findChildren(QLabel) if label.text() == "Light preview")
        label.ensurePolished()
        self.assertEqual(label.palette().color(QPalette.WindowText).name(), "#1c2333")

    def test_dropdown_arrows_render_with_a_fresh_profile(self):
        combo = QComboBox()
        combo.addItem("Export format")
        combo.resize(160, 36)
        for theme in ("light", "dark"):
            with self.subTest(theme=theme):
                arrow = f"arrow_{theme}.png"
                self.assertFalse((self.main.APP_DATA / arrow).exists())
                stylesheet = self.main.get_app_stylesheet(theme)
                self.app.setStyleSheet(stylesheet)
                with_arrow = combo.grab().toImage()
                self.app.setStyleSheet(stylesheet.replace(arrow, "missing-arrow.png"))
                without_arrow = combo.grab().toImage()
                self.assertNotEqual(with_arrow, without_arrow)

    def test_overflow_tabs_are_reachable_and_theme_preserves_other_settings(self):
        with (
            patch.object(self.main.LABOKitMainWindow, "check_app_updates", lambda self: None),
            patch.object(self.main.LABOKitMainWindow, "check_plugin_updates", lambda self: None),
        ):
            self.main.save_settings({"theme": "light", "existing_preference": "preserve"})
            window = self.main.LABOKitMainWindow()
        self.addCleanup(window.close)
        for index in range(10):
            window.tabs.addTab(QWidget(), f"Additional Tool {index + 1}")
        window.resize(900, 650)
        window.apply_theme("dark")
        window.show()
        QTest.qWait(75)

        expected = {"theme": "dark", "existing_preference": "preserve"}
        self.assertEqual(self.main.load_settings(), expected)
        tab_bar = window.tabs.tabBar()
        right = next(button for button in tab_bar.findChildren(QToolButton) if button.arrowType() == Qt.RightArrow)
        self.assertTrue(right.isVisible())
        for _ in range(window.tabs.count()):
            if not right.isEnabled():
                break
            QTest.mouseClick(right, Qt.LeftButton)
        last = window.tabs.count() - 1
        QTest.mouseClick(tab_bar, Qt.LeftButton, pos=tab_bar.tabRect(last).center())
        self.assertEqual(window.tabs.currentIndex(), last)

    def test_example_plugin_browses_drops_exports_and_reports_partial_failure(self):
        plugin = load_plugin("ExamplePlugin")
        tab = plugin.create_tab()
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            directory = Path(folder)
            jpeg = directory / "input.jpg"
            bad = directory / "broken.png"
            bad.write_bytes(b"invalid PNG")
            Image.new("RGB", (16, 16), "white").save(jpeg)

            with patch.object(plugin.QFileDialog, "getOpenFileNames", return_value=([str(jpeg)], "")):
                tab.btn_add.click()
            tab.file_list.files_dropped.emit([jpeg, bad])
            self.assertEqual(tab.file_list.count(), 2)

            with patch.object(plugin.ModernDialog, "show_warning") as warning:
                tab.btn_process.click()
                self.wait_for_worker(tab)
                warning.assert_called_once()
                self.assertIn("Processed 1 of 2", warning.call_args.args[-1])
                self.assertIn(bad.name, warning.call_args.args[-1])

                tab.btn_process.click()
                self.wait_for_worker(tab)
                self.assertEqual(warning.call_count, 2)

            for name in ("processed_input.jpg", "processed_input_2.jpg"):
                with Image.open(directory / name) as result:
                    self.assertEqual(result.format, "JPEG")
                    self.assertEqual(result.size, (16, 16))
                    self.assertLess(result.getpixel((0, 0))[0], 255)
            self.assertFalse((directory / "processed_broken.png").exists())

            tab.btn_clear.click()
            self.assertEqual(tab.file_list.count(), 0)
            self.assertEqual(tab.lbl_status.text(), "Ready")

    def test_close_waits_for_active_worker(self):
        may_finish = threading.Event()

        class Worker(QThread):
            def run(self):
                may_finish.wait(5)

            def stop(self):
                self.requestInterruption()

        with (
            patch.object(self.main.LABOKitMainWindow, "check_app_updates", lambda self: None),
            patch.object(self.main.LABOKitMainWindow, "check_plugin_updates", lambda self: None),
        ):
            window = self.main.LABOKitMainWindow()
        window.show()
        worker = Worker(window.bg_tab)
        window.bg_tab.worker = worker
        worker.start()
        try:
            self.assertFalse(window.close())
            self.assertTrue(window.isVisible())
        finally:
            may_finish.set()
            self.assertTrue(worker.wait(2000))
            QTest.qWait(300)
        self.assertFalse(window.isVisible())

    def test_video_announces_one_completion_and_preserves_output_on_failure(self):
        plugin = load_plugin("VideoUpscaler")
        tab = plugin.create_tab()
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            directory = Path(folder)
            source = directory / "input.mp4"
            source.write_bytes(b"input fixture")
            output = directory / "input_upscaled_2x.mp4"
            tab.file_list.files_dropped.emit([source])
            self.assertEqual(tab.input_file, source)

            def successful_export(worker, frame_dir, target):
                target.write_bytes(b"completed export")

            def failed_export(worker, frame_dir, target):
                target.write_bytes(b"partial export")
                raise RuntimeError("encoder failed")

            with (
                patch.object(plugin.ModernDialog, "show_info") as success,
                patch.object(plugin.ModernDialog, "show_critical") as error,
            ):
                with patch.object(plugin.VideoWorker, "_upscale", successful_export):
                    tab.btn_run.click()
                    self.wait_for_worker(tab)
                error.assert_not_called()
                success.assert_called_once()
                self.assertEqual(tab.log_text.toPlainText().count("Finished!"), 1)

                with patch.object(plugin.VideoWorker, "_upscale", failed_export):
                    tab.btn_run.click()
                    self.wait_for_worker(tab)
                success.assert_called_once()
                error.assert_called_once()
                self.assertIn("encoder failed", error.call_args.args[-1])

            self.assertEqual(output.read_bytes(), b"completed export")
            self.assertEqual(set(directory.iterdir()), {source, output})
            self.assertTrue(tab.btn_run.isEnabled())
