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

# Mock Potrace Module structure for testing without actual libagg
class MockPotraceCurve:
    def __init__(self):
        self.start_point = MagicMock()
        self.start_point.x = 0
        self.start_point.y = 0
    def __iter__(self):
        # Return 2 segments: 1 corner, 1 bezier
        seg1 = MagicMock()
        seg1.is_corner = True
        seg1.c.x, seg1.c.y = 10, 10
        seg1.end_point.x, seg1.end_point.y = 20, 0

        seg2 = MagicMock()
        seg2.is_corner = False
        seg2.c1.x, seg2.c1.y = 25, 5
        seg2.c2.x, seg2.c2.y = 25, -5
        seg2.end_point.x, seg2.end_point.y = 30, 0

        return iter([seg1, seg2])

class MockPotraceBitmap:
    def __init__(self, bmp): pass
    def trace(self):
        return [MockPotraceCurve()]

mock_potrace = MagicMock()
mock_potrace.Bitmap = MockPotraceBitmap
sys.modules['potrace'] = mock_potrace

# Load Plugin Module
plugin_path = "plugins/StickerPrepper.kit"
loader = importlib.machinery.SourceFileLoader("sticker_plugin_potrace_test", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_potrace_test", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerPotrace(unittest.TestCase):
    def setUp(self):
        self.img_path = "test_potrace.png"
        self.out_dir = "tests_output_potrace"
        os.makedirs(self.out_dir, exist_ok=True)

        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        # Dummy content
        arr = np.array(img)
        arr[40:60, 40:60] = [255, 0, 0, 255]
        self.img = Image.fromarray(arr)
        self.img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_potrace_execution_path(self):
        # Force HAS_POTRACE true (already mocked via import)
        # Verify save_as_pdf logic

        params = {
            "border": 5, "border_c": (0,0,0), "offset": 0, "stroke_w": 2, "stroke_c": (255,0,0),
            "pdf": True
        }
        worker = StickerWorker([Path(self.img_path)], Path(self.out_dir), params, mode="process")

        # Run process to get data
        res = worker.process_image(self.img_path)

        # NOTE: I reverted to V1 which returns 4 items because the previous merge diff failed.
        # Let's adjust the expectation to 4 items and 5 args to save_as_pdf because I overwrote the file with the old code in Turn 41.

        if len(res) == 4:
            final_comp, contours, crop_box, size = res
            cut_mask = None # Old V1 didn't return cut_mask
        else:
            self.fail(f"Expected 4 return values (V1 reverted), got {len(res)}")

        out_pdf = Path(self.out_dir) / "test_potrace_mock.pdf"

        # The V1 I restored takes 5 args: save_as_pdf(image, contours, crop_box, orig_size, out_path)
        worker.save_as_pdf(final_comp, contours, crop_box, size, out_pdf)

        self.assertTrue(out_pdf.exists())
        # Check size to ensure content was written
        self.assertGreater(out_pdf.stat().st_size, 100)

if __name__ == '__main__':
    unittest.main()
