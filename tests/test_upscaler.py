import sys
import os
import unittest
from unittest.mock import MagicMock, patch, ANY

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set APPDATA for main.py (it assumes Windows)
if not os.getenv('APPDATA'):
    os.environ['APPDATA'] = os.path.expanduser('~/.local/share')

# Mock modules that might not be available in the test environment
sys.modules["cv2"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["torchvision"] = MagicMock()
sys.modules["basicsr"] = MagicMock()
sys.modules["realesrgan"] = MagicMock()
sys.modules["rembg"] = MagicMock()

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer

# Ensure QApplication exists
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

import main

class TestUpscalerWorker(unittest.TestCase):
    def setUp(self):
        self.mock_ai = {
            "cv2": MagicMock(),
            "torch": MagicMock(),
            "SRVGGNetCompact": MagicMock(),
            "RealESRGANer": MagicMock()
        }
        self.patcher_ai = patch('main.load_ai_engine', return_value=self.mock_ai)
        self.mock_load_ai = self.patcher_ai.start()

        self.patcher_sub = patch('subprocess.run')
        self.mock_sub = self.patcher_sub.start()

    def tearDown(self):
        self.patcher_ai.stop()
        self.patcher_sub.stop()

    def test_worker_init_upsampler(self):
        worker = main.UpscalerWorker([], main.Path("out"), "model.pth", True)
        with patch('main.Path.exists', return_value=True):
            upsampler = worker.init_upsampler("model.pth")
            self.mock_ai["SRVGGNetCompact"].assert_called()
            self.assertIsNotNone(upsampler)

    def test_worker_python_run(self):
        worker = main.UpscalerWorker([main.Path("img.png")], main.Path("out"), "model.pth", True)

        # Mock init_upsampler to return mock
        mock_ups = MagicMock()
        worker.init_upsampler = MagicMock(return_value=mock_ups)

        # Mock run_python_inference
        worker.run_python_inference = MagicMock(return_value=True)

        # We need to simulate the thread run manually
        worker.run()

        worker.init_upsampler.assert_called_with("model.pth")
        worker.run_python_inference.assert_called()

    def test_worker_subprocess_run(self):
        worker = main.UpscalerWorker([main.Path("img.png")], main.Path("out"), "model", False)

        with patch('main.REALESRGAN_EXE') as mock_exe:
            mock_exe.__str__.return_value = "exe"
            with patch('main.Path.exists', return_value=True):
                worker.run()

            self.mock_sub.assert_called()

class TestUpscalerTabRefactored(unittest.TestCase):
    def setUp(self):
        self.patcher_msg = patch('main.QMessageBox')
        self.mock_msg = self.patcher_msg.start()

        self.patcher_prog = patch('main.QProgressDialog')
        self.mock_prog = self.patcher_prog.start()
        self.mock_prog.return_value.wasCanceled.return_value = False

        self.tab = main.UpscalerTab()
        self.tab.ensure_out = MagicMock(return_value=main.Path("out"))

    def tearDown(self):
        self.patcher_msg.stop()
        self.patcher_prog.stop()
        self.tab.close()

    def test_start_worker(self):
        p1 = main.Path("test1.png")
        self.tab.image_paths = [p1]
        self.tab.combo_m.setCurrentText("General")

        with patch('main.UpscalerWorker') as MockWorker:
            with patch('main.REALESRGAN_EXE') as mock_exe:
                 mock_exe.exists.return_value = True
                 self.tab.proc_all()

            MockWorker.assert_called()
            worker_instance = MockWorker.return_value
            worker_instance.start.assert_called()

if __name__ == '__main__':
    unittest.main()
