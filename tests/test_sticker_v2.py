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
plugin_path = "plugins/StickerPrepperV2.kit"
loader = importlib.machinery.SourceFileLoader("sticker_plugin_v2_test", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_v2_test", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerLogicV2(unittest.TestCase):
    def setUp(self):
        self.img_path = "test_circle_v2.png"
        self.out_dir = "tests_output_v2_kit"
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

    def test_distance_transform_logic(self):
        # Case: Border=10, Offset=0
        # Expected Bleed Radius: 30+10 = 40

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

        # Verify contours are floating point (from distance transform thresholding)
        self.assertTrue(np.issubdtype(cnt.dtype, np.floating), "Contours should be float32")

        # Check approximated radius via area
        import cv2
        area = cv2.contourArea(cnt.astype(np.float32)) # Ensure correct type for area
        radius = np.sqrt(area / np.pi)

        # Expected ~40px radius. Distance transform is sub-pixel accurate usually.
        # Allow small delta.
        self.assertAlmostEqual(radius, 40, delta=1.5, msg="Radius should match Border expansion (30+10)")

    def test_offset_contraction(self):
        # Case: Border=10, Offset=-5
        # Expected Bleed Radius: 40
        # Expected Cut Radius: 30 + (10 - 5) = 35

        params = {
            "border": 10,
            "border_c": (0, 0, 0),
            "offset": -5,
            "stroke_w": 2,
            "stroke_c": (255, 0, 255),
            "pdf": True
        }
        worker = StickerWorker([], None, params, mode="process")
        res = worker.process_image(self.img_path)
        contours = res[1]
        cnt = contours[0]

        import cv2
        area = cv2.contourArea(cnt.astype(np.float32))
        radius = np.sqrt(area / np.pi)

        self.assertAlmostEqual(radius, 35, delta=1.5, msg="Cut radius should handle offset correctly")

if __name__ == '__main__':
    unittest.main()
