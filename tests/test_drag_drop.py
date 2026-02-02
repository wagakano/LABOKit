import sys
import os
from unittest.mock import MagicMock

# Set APPDATA to avoid crash in main.py
os.environ['APPDATA'] = "/tmp/appdata"

# Mock modules that might be missing or heavy
sys.modules['torchvision'] = MagicMock()
sys.modules['torchvision.transforms'] = MagicMock()
sys.modules['torchvision.transforms.functional'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['basicsr'] = MagicMock()
sys.modules['basicsr.archs'] = MagicMock()
sys.modules['basicsr.archs.srvgg_arch'] = MagicMock()
sys.modules['realesrgan'] = MagicMock()
sys.modules['rembg'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['packaging'] = MagicMock()
sys.modules['packaging.version'] = MagicMock()
sys.modules['urllib3'] = MagicMock()
sys.modules['svgwrite'] = MagicMock()
sys.modules['requests'] = MagicMock()

import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QMimeData, QUrl, Qt, QPointF
from PySide6.QtGui import QDropEvent

# Add parent dir to path to import main
sys.path.append(str(Path(__file__).parent.parent))
from main import FileDropListWidget

class TestFileDropListWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if it doesn't exist
        # Headless mode
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_drop_event(self):
        widget = FileDropListWidget()

        # Capture signal
        received_files = []
        widget.files_dropped.connect(lambda f: received_files.extend(f))

        # Simulate MimeData
        mime_data = QMimeData()
        fake_path = Path.cwd() / "test_image.png"
        url = QUrl.fromLocalFile(str(fake_path))
        mime_data.setUrls([url])

        # Create QDropEvent
        # QDropEvent(pos, possibleActions, data, buttons, modifiers)
        event = QDropEvent(
            QPointF(10, 10),
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier
        )

        # Trigger dropEvent
        widget.dropEvent(event)

        # Assertions
        self.assertEqual(len(received_files), 1, "Should have received 1 file")
        self.assertEqual(received_files[0], fake_path, "Path should match")
        print(f"Verified drop of {fake_path}")

if __name__ == '__main__':
    unittest.main()
