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
loader = importlib.machinery.SourceFileLoader("sticker_plugin_smoothing_test", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_smoothing_test", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerSmoothing(unittest.TestCase):
    def setUp(self):
        self.img_path = "test_chaikin.png"
        self.out_dir = "tests_output_chaikin"
        os.makedirs(self.out_dir, exist_ok=True)

        # Create a diamond shape (sharp corners)
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        arr = np.array(img)
        # Diamond
        for y in range(100):
            for x in range(100):
                if abs(x-50) + abs(y-50) <= 30:
                    arr[y,x] = [255, 0, 0, 255]
        self.img = Image.fromarray(arr)
        self.img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_chaikin_smoothing_implementation(self):
        # We want to test the chaikin_smooth function inside save_as_pdf
        # Since it's nested, we can't unit test it directly easily without exposing it.
        # But we can verify PDF generation succeeds with it.

        params = {
            "border": 5,
            "border_c": (0, 0, 0),
            "offset": 0,
            "stroke_w": 2,
            "stroke_c": (255, 0, 255),
            "pdf": True
        }
        worker = StickerWorker([Path(self.img_path)], Path(self.out_dir), params, mode="process")

        # Run process to get contours (StickerWorker.process_image logic)
        res = worker.process_image(self.img_path)
        # res is tuple: (final_comp, contours, crop_box, size)
        contours = res[1]

        # Verify contours exist
        self.assertTrue(len(contours) > 0)

        # Test save_as_pdf execution (which runs Chaikin)
        out_pdf = Path(self.out_dir) / "test_chaikin.pdf"
        worker.save_as_pdf(res[0], contours, res[2], res[3], out_pdf)

        self.assertTrue(out_pdf.exists())
        self.assertGreater(out_pdf.stat().st_size, 100)

if __name__ == '__main__':
    unittest.main()
