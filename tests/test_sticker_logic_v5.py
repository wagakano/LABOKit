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
loader = importlib.machinery.SourceFileLoader("sticker_plugin_logic_v5", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_logic_v5", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerLogicV5(unittest.TestCase):
    def setUp(self):
        self.img_path = "test_supersample.png"
        self.out_dir = "tests_output_v5"
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

    def test_smooth_contours(self):
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

        # Verify contours are floating point (indicating sub-pixel precision from supersampling)
        cnt = contours[0]
        # cnt is (N, 1, 2)
        self.assertTrue(np.issubdtype(cnt.dtype, np.floating), "Contours should be float32")

        # Verify simple approx
        # A circle approximated should have fewer points than the full pixel trace
        # Raw trace of circle r=30 is roughly perimeter ~188 pixels/points.
        # approxPolyDP should reduce this significantly (e.g., < 100).
        num_points = len(cnt)
        self.assertLess(num_points, 150, "approxPolyDP should reduce point count for smoothness")

if __name__ == '__main__':
    unittest.main()
