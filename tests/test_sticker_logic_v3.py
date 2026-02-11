import sys
import os
import unittest
from unittest.mock import MagicMock
import importlib.machinery
import importlib.util
from PIL import Image
import numpy as np
import shutil
from pathlib import Path

# Mock ui_shared dependencies BEFORE module load
sys.modules['ui_shared'] = MagicMock()
sys.modules['translations'] = MagicMock()

# Load Plugin Module
plugin_path = "plugins/StickerPrepper.kit"
loader = importlib.machinery.SourceFileLoader("sticker_plugin_logic_v3", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_logic_v3", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerLogicV3(unittest.TestCase):
    def setUp(self):
        # Create a tiny 1x1 pixel image to test border color
        self.img_path = "test_dot.png"
        self.out_dir = "tests_output_v3"
        os.makedirs(self.out_dir, exist_ok=True)

        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_black_border_default(self):
        # Test if the border is black by default
        params = {
            "border": 5, # Enough to see
            # border_c defaulting to (0,0,0) in code if not present, but let's pass explicitly to verify worker logic
            "border_c": (0, 0, 0),
            "offset": 0,
            "stroke_w": 0, # Disable stroke for clarity
            "stroke_c": (255, 0, 255),
            "pdf": False
        }
        worker = StickerWorker([], None, params, mode="process")
        res = worker.process_image(self.img_path)

        # Check a pixel in the border area (not source)
        # Source is 10x10. Border is 5. Padded image is ~20x20.
        # Center is source.
        # Check pixel at (0, 0) of the result? No, result is cropped.
        # If crop works, we should see black pixels around the red center.

        arr = np.array(res)

        # Check for presence of Black (0,0,0,255) pixels
        # And absence of White (255,255,255,255) if it was default before

        # Find pixels that are opaque
        alpha = arr[:,:,3]
        opaque_mask = alpha > 0

        # In opaque area, find black pixels
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
        is_black = (r == 0) & (g == 0) & (b == 0) & opaque_mask

        # Should have substantial black pixels (the border)
        self.assertGreater(np.sum(is_black), 10, "Should contain black border pixels")

    def test_custom_border_color(self):
        # Test Blue Border
        params = {
            "border": 5,
            "border_c": (0, 0, 255), # Blue
            "offset": 0,
            "stroke_w": 0,
            "stroke_c": (255, 0, 255),
            "pdf": False
        }
        worker = StickerWorker([], None, params, mode="process")
        res = worker.process_image(self.img_path)

        arr = np.array(res)
        alpha = arr[:,:,3]
        opaque_mask = alpha > 0

        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
        is_blue = (r == 0) & (g == 0) & (b == 255) & opaque_mask

        self.assertGreater(np.sum(is_blue), 10, "Should contain blue border pixels")

if __name__ == '__main__':
    unittest.main()
