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
loader = importlib.machinery.SourceFileLoader("sticker_plugin_logic_v4", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_logic_v4", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerLogicV4(unittest.TestCase):
    def setUp(self):
        self.img_path = "test_circle.png"
        self.out_dir = "tests_output_v4"
        os.makedirs(self.out_dir, exist_ok=True)

        # Create a 100x100 image with a 20px radius circle in center
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        arr = np.array(img)
        y, x = np.ogrid[:100, :100]
        mask = (x - 50)**2 + (y - 50)**2 <= 20**2
        arr[mask] = [255, 0, 0, 255] # Red Circle
        self.img = Image.fromarray(arr)
        self.img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_independent_masks(self):
        # Case: Border=10, Offset=-5.
        # Original Radius: 20
        # Expected Bleed Radius: 20 + 10 = 30
        # Expected Cut Line Radius: 20 + (10 - 5) = 25

        # NOTE: Logic changed.
        # New Logic: Cut Mask = Dilate(Original, Border + Offset)
        # So Cut Radius = 20 + (10 - 5) = 25.
        # This matches expectation.

        params = {
            "border": 10,
            "border_c": (0, 0, 0),
            "offset": -5,
            "stroke_w": 2,
            "stroke_c": (255, 0, 255),
            "pdf": True # Get contours
        }
        worker = StickerWorker([], None, params, mode="process")
        res = worker.process_image(self.img_path)

        # Result is tuple (img, contours, ...)
        contours = res[1]

        # Find contour with largest area (should be the cut line)
        import cv2
        max_area = 0
        max_cnt = None
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area:
                max_area = area
                max_cnt = cnt

        # Calculate approximate radius from area
        # Area = pi * r^2  => r = sqrt(Area / pi)
        radius = np.sqrt(max_area / np.pi)

        # Expected radius ~25. Allow some tolerance due to pixelation/blur
        self.assertAlmostEqual(radius, 25, delta=2.0, msg="Cut line radius should be approx 25px")

    def test_negative_expansion(self):
        # Case: Border=5, Offset=-10.
        # Total Expansion = 5 - 10 = -5.
        # Logic: Erode(Original, 5).
        # Original Radius: 20.
        # Expected Cut Radius: 15.

        params = {
            "border": 5,
            "border_c": (0, 0, 0),
            "offset": -10,
            "stroke_w": 2,
            "stroke_c": (255, 0, 255),
            "pdf": True
        }
        worker = StickerWorker([], None, params, mode="process")
        res = worker.process_image(self.img_path)
        contours = res[1]

        import cv2
        max_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area: max_area = area

        radius = np.sqrt(max_area / np.pi)
        self.assertAlmostEqual(radius, 15, delta=2.0, msg="Cut line radius should be approx 15px (Erosion)")

if __name__ == '__main__':
    unittest.main()
