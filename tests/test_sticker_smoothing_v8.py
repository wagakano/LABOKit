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
loader = importlib.machinery.SourceFileLoader("sticker_plugin_smoothing_test_v8", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_smoothing_test_v8", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerSmoothingV8(unittest.TestCase):
    def setUp(self):
        self.img_path = "test_pixelated_source.png"
        self.out_dir = "tests_output_v8"
        os.makedirs(self.out_dir, exist_ok=True)

        # Create a jagged "stairs" image
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        arr = np.array(img)
        # Staircase pattern
        for i in range(10):
            # Step 10x10
            x_start, y_start = 10 + i*5, 10 + i*5
            arr[y_start:y_start+5, x_start:x_start+5] = [255, 0, 0, 255]

        self.img = Image.fromarray(arr)
        self.img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_smooth_source_logic(self):
        # 1. Run WITHOUT source smoothing
        params_sharp = {
            "border": 5, "border_c": (0,0,0), "offset": 0, "stroke_w": 2, "stroke_c": (255,0,0),
            "pdf": True,
            "smooth_source": False, # Disabled
            "blur_strength": 3
        }
        worker = StickerWorker([], None, params_sharp, mode="process")
        res_sharp = worker.process_image(self.img_path)
        contours_sharp = res_sharp[1]
        pts_sharp = len(contours_sharp[0])

        # 2. Run WITH source smoothing
        params_smooth = {
            "border": 5, "border_c": (0,0,0), "offset": 0, "stroke_w": 2, "stroke_c": (255,0,0),
            "pdf": True,
            "smooth_source": True, # Enabled
            "blur_strength": 3
        }
        worker = StickerWorker([], None, params_smooth, mode="process")
        res_smooth = worker.process_image(self.img_path)
        contours_smooth = res_smooth[1]
        pts_smooth = len(contours_smooth[0])

        # NOTE: With 8x supersampling + chaikin, point counts might vary.
        # But generally, a smoothed source should result in fewer "jagged" turns,
        # or at least the *shape* should be different (rounded corners).
        # Checking logic execution is key.

        # Since we threshold after blur, we expect the count to be somewhat different or the shape to be less area?
        # Actually, blurred stairs -> straight diagonal slope.
        # Staircase perimeter >> Slope perimeter.

        import cv2
        # Convert list of tuples back to numpy for arcLength
        # Chaikin returns list of (x,y)
        # We need to test the logic path.

        # Let's check that logic indeed changes the result.
        self.assertNotEqual(pts_sharp, pts_smooth, "Smoothing source should alter the contour generation")

if __name__ == '__main__':
    unittest.main()
