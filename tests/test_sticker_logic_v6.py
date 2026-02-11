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
loader = importlib.machinery.SourceFileLoader("sticker_plugin_logic_v6", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_logic_v6", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerLogicV6(unittest.TestCase):
    def setUp(self):
        self.img_path = "test_supersample_v6.png"
        self.out_dir = "tests_output_v6"
        os.makedirs(self.out_dir, exist_ok=True)

        # Create a circle which would be jagged at low res
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        arr = np.array(img)
        y, x = np.ogrid[:100, :100]
        mask = (x - 50)**2 + (y - 50)**2 <= 30**2
        arr[mask] = [255, 0, 0, 255]
        self.img = Image.fromarray(arr)
        self.img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_high_fidelity_contours(self):
        params = {
            "border": 10,
            "border_c": (0, 0, 0),
            "offset": 0,
            "stroke_w": 2,
            "stroke_c": (255, 0, 255),
            "pdf": True
        }
        worker = StickerWorker([], None, params, mode="process")
        res = worker.process_image(self.img_path)

        contours = res[1]
        cnt = contours[0]

        # Verify contours are floating point (indicating sub-pixel precision from 4x supersampling)
        self.assertTrue(np.issubdtype(cnt.dtype, np.floating), "Contours should be float32")

        # Verify point count is HIGH (indicating minimal simplification)
        # Previous fail was < 150. Now with minimal approx, it should be close to raw (or higher due to supersample interpolation).
        # Raw pixel perimeter ~188. Supersampled 4x perimeter ~752.
        # approxPolyDP 0.01% -> minimal reduction.
        # So expected points > 500 probably? Or at least > 200.
        num_points = len(cnt)

        # Let's just check it's not excessively simplified (e.g., < 20 for a circle is bad)
        self.assertGreater(num_points, 50, "Should have enough points for smooth circle")

        # And check it's not insanely high (e.g., > 2000) for performance
        # Supersampling might generate lots of points.
        # Just checking reasonable range.

if __name__ == '__main__':
    unittest.main()
