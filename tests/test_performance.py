import sys
import os
from unittest.mock import MagicMock, patch
import unittest
from pathlib import Path

# --- MOCK APPDATA ---
os.environ["APPDATA"] = "/tmp/LABOKit_AppData"

# --- MOCK PY SIDE 6 ---
mock_qt = MagicMock()
sys.modules["PySide6"] = mock_qt
sys.modules["PySide6.QtCore"] = mock_qt.QtCore
sys.modules["PySide6.QtGui"] = mock_qt.QtGui
sys.modules["PySide6.QtWidgets"] = mock_qt.QtWidgets

# Custom Mock QWidget to ensure subclass methods execute
class MockQWidget:
    def __init__(self, parent=None):
        pass
    def setContentsMargins(self, *args): pass
    def setSpacing(self, *args): pass
    def addLayout(self, *args): pass
    def addWidget(self, *args): pass
    def setLayout(self, *args): pass
    def setWindowTitle(self, *args): pass
    def show(self): pass
    def resizeEvent(self, e): pass
    # Catch-all for other Qt methods
    def __getattr__(self, name):
        return MagicMock()

mock_qt.QtWidgets.QWidget = MockQWidget

# --- MOCK DEPENDENCIES ---
mock_requests = MagicMock()
sys.modules["requests"] = mock_requests

mock_packaging = MagicMock()
sys.modules["packaging"] = mock_packaging
sys.modules["packaging.version"] = MagicMock()

mock_urllib3 = MagicMock()
sys.modules["urllib3"] = mock_urllib3
sys.modules["urllib3.exceptions"] = MagicMock()

mock_svgwrite = MagicMock()
sys.modules["svgwrite"] = mock_svgwrite

# --- MOCK HEAVY ML LIBS ---
mock_torch = MagicMock()
sys.modules["torch"] = mock_torch
sys.modules["torch.nn"] = MagicMock()

mock_cv2 = MagicMock()
sys.modules["cv2"] = mock_cv2

mock_numpy = MagicMock()
sys.modules["numpy"] = mock_numpy

mock_basicsr = MagicMock()
sys.modules["basicsr"] = mock_basicsr
sys.modules["basicsr.archs"] = MagicMock()
sys.modules["basicsr.archs.srvgg_arch"] = MagicMock()

mock_realesrgan = MagicMock()
sys.modules["realesrgan"] = mock_realesrgan

# --- MOCK TORCHVISION ---
sys.modules["torchvision"] = MagicMock()
sys.modules["torchvision.transforms"] = MagicMock()
sys.modules["torchvision.transforms.functional"] = MagicMock()

# Ensure psutil is available
try:
    import psutil
except ImportError:
    sys.modules["psutil"] = MagicMock()

# Import main (which imports ui_shared)
import main

class TestUpscalerPerformance(unittest.TestCase):
    def setUp(self):
        # Reset the lazy loader
        main.AI_MODULES = None

        # Setup the mocks that load_ai_engine will return
        self.mock_srvgg = MagicMock()
        self.mock_realesrganer = MagicMock()

        # Fix the return value of enhance to avoid ValueError unpacking
        # enhance returns (output, output_img)
        self.mock_realesrganer.return_value.enhance.return_value = (MagicMock(), MagicMock())

        # Configure the sys.modules mocks to return our specific mocks
        sys.modules["basicsr.archs.srvgg_arch"].SRVGGNetCompact = self.mock_srvgg
        sys.modules["realesrgan"].RealESRGANer = self.mock_realesrganer

        # Also mock cv2.imread and imwrite
        mock_cv2.imread.return_value = MagicMock()
        mock_cv2.imwrite.return_value = True

    @patch("main.QMessageBox")
    @patch("main.QApplication")
    @patch("main.QProgressDialog")
    def test_reinitialization_optimization(self, mock_dlg_cls, mock_app, mock_mb):
        """
        Tests that the optimized implementation initializes the model ONLY ONCE for multiple images.
        """
        # Configure progress dialog to not be canceled
        mock_dlg_instance = mock_dlg_cls.return_value
        mock_dlg_instance.wasCanceled.return_value = False

        mock_meter = MagicMock()
        tab = main.UpscalerTab(meter=mock_meter)

        paths = [Path(f"test_img_{i}.png") for i in range(3)]

        # Mock file existence so it proceeds
        with patch("pathlib.Path.exists", return_value=True):
            # Select "General - Performance" to trigger .pth / python mode
            tab.combo_m.currentText.return_value = "General - Performance"

            # Reset again
            main.AI_MODULES = None

            # Run the process
            tab._run(paths)

            print(f"\n[VERIFY] SRVGGNetCompact call count: {self.mock_srvgg.call_count}")
            print(f"[VERIFY] RealESRGANer call count: {self.mock_realesrganer.call_count}")

            # Optimized expectation: instantiated once in total
            self.assertEqual(self.mock_srvgg.call_count, 1, "Optimization: Model should be instantiated only once")
            self.assertEqual(self.mock_realesrganer.call_count, 1, "Optimization: Upsampler should be instantiated only once")

if __name__ == "__main__":
    unittest.main()
