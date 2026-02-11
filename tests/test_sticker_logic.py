import sys
import os
import unittest
from unittest.mock import MagicMock
import importlib.machinery
import importlib.util
from PIL import Image
import numpy as np
import shutil

# Mock ui_shared dependencies BEFORE module load
sys.modules['ui_shared'] = MagicMock()
sys.modules['translations'] = MagicMock()

# Load Plugin Module
plugin_path = "plugins/StickerPrepper.kit"
loader = importlib.machinery.SourceFileLoader("sticker_plugin_logic", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_logic", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerLogic(unittest.TestCase):
    def setUp(self):
        # Create a synthetic image
        self.img_path = "test_synthetic.png"
        self.out_dir = "tests_output"
        os.makedirs(self.out_dir, exist_ok=True)

        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        # Draw a shape in center
        for x in range(40, 60):
            for y in range(40, 60):
                img.putpixel((x, y), (255, 0, 0, 255))
        img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_process_image(self):
        params = {
            "border": 10,
            "offset": 5,
            "stroke_w": 2,
            "stroke_c": (0, 255, 0) # Green
        }
        # Instantiate worker (mock parent)
        # QThread constructor requires QObject parent or None. None is fine.
        # But if QApp not running, QThread might warn.
        # We are not starting the thread, just calling method.
        worker = StickerWorker([], None, params, mode="process")

        # Call process_image directly
        res = worker.process_image(self.img_path)

        self.assertIsNotNone(res)
        self.assertIsInstance(res, Image.Image)

        # Check size validity
        self.assertGreater(res.width, 40)
        self.assertGreater(res.height, 40)

        # Check for presence of Green stroke (G > 200)
        arr = np.array(res)
        # Check if any pixel has high Green component
        green_pixels = np.sum(arr[:,:,1] > 200)
        self.assertGreater(green_pixels, 0, "Output image should contain green stroke pixels")

    def test_negative_offset(self):
        params = {
            "border": 20,
            "offset": -5, # Inside
            "stroke_w": 2,
            "stroke_c": (0, 0, 255) # Blue
        }
        worker = StickerWorker([], None, params, mode="process")
        res = worker.process_image(self.img_path)
        self.assertIsNotNone(res)

        arr = np.array(res)
        blue_pixels = np.sum(arr[:,:,2] > 200)
        self.assertGreater(blue_pixels, 0, "Output image should contain blue stroke pixels")

if __name__ == '__main__':
    unittest.main()
