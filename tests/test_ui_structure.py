import sys
import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QScrollArea, QListWidget, QSlider, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Signal, QObject

# Fix: Create proper signal mock or use real signal if needed
# Actually, for UI tests, we can use a helper object
class SignalHelper(QObject):
    triggered = Signal()

# Mock UI dependencies
mock_ui = MagicMock()

# Mock FileDropListWidget
class MockFileDropListWidget(QListWidget):
    files_dropped = Signal(list) # Use real signal to avoid issues
    def __init__(self, parent=None):
        super().__init__(parent)

# Mock ZoomableImageWidget
class MockZoomableImageWidget(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
    def set_images(self, a, b): pass
    def set_image_pixmaps(self, a, b, preserve_zoom=False): pass

mock_ui.FileDropListWidget = MockFileDropListWidget
mock_ui.ZoomableImageWidget = MockZoomableImageWidget
# IMPORTANT: Return valid QIcon to prevent segfault in C++ binding
mock_ui.create_plus_icon = lambda: QIcon()
mock_ui.VALID_EXTENSIONS = {".png"}

sys.modules['ui_shared'] = mock_ui

# Mock translations
mock_trans = MagicMock()
mock_trans.tr = lambda k: k
sys.modules['translations'] = mock_trans

import importlib.machinery
import importlib.util

class TestUIStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        # Re-import to ensure clean state? No, module is cached.
        # But for plugin loading via path, it's fine.
        plugin_path = "plugins/StickerPrepper.kit"
        loader = importlib.machinery.SourceFileLoader("sticker_plugin_ui_test", plugin_path)
        spec = importlib.util.spec_from_file_location("sticker_plugin_ui_test", plugin_path, loader=loader)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_tab_creation(self):
        tab = self.mod.create_tab(None)
        self.assertIsNotNone(tab)

        # Verify default params
        params = tab.get_params()
        self.assertEqual(params['border'], 30)

        # Verify interaction
        # Find slider. It's an attribute self.sl_border
        slider = tab.sl_border
        slider.setValue(60)

        # Check if param updated
        self.assertEqual(tab.p_border, 60)

        # Check preview update triggered
        # It uses a timer. check if timer active?
        self.assertTrue(tab.debounce_timer.isActive())

if __name__ == '__main__':
    unittest.main()
