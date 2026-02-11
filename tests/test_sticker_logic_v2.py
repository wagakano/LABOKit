import sys
import os
import unittest
from unittest.mock import MagicMock
import importlib.machinery
import importlib.util
from PIL import Image, ImageDraw
import numpy as np
import shutil
from pathlib import Path

# Mock ui_shared dependencies BEFORE module load
sys.modules['ui_shared'] = MagicMock()
sys.modules['translations'] = MagicMock()

# Load Plugin Module
plugin_path = "plugins/StickerPrepper.kit"
loader = importlib.machinery.SourceFileLoader("sticker_plugin_logic_v2", plugin_path)
spec = importlib.util.spec_from_file_location("sticker_plugin_logic_v2", plugin_path, loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

StickerWorker = mod.StickerWorker

class TestStickerLogicV2(unittest.TestCase):
    def setUp(self):
        # Create a synthetic image with a HOLE
        self.img_path = "test_donut.png"
        self.out_dir = "tests_output_v2"
        os.makedirs(self.out_dir, exist_ok=True)

        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Draw outer circle (White Body base)
        draw.ellipse((50, 50, 150, 150), fill=(255, 0, 0, 255))
        # Draw inner hole (Transparent) - Donut
        # To make a hole in PIL draw, we need to composite or mask.
        # Easier: Draw larger circle then erase center.

        # Reset
        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((50, 50, 150, 150), fill=(255, 0, 0, 255))

        # Erase center
        # Since ImageDraw doesn't do "erase" easily on same layer without mask logic,
        # let's just manipulate pixels or use composite.
        # Simple approach: Draw transparent circle? No, draw replaces color but alpha 0 on alpha 255...
        # Let's use numpy
        arr = np.array(img)
        # Center is (100, 100). Radius 20 hole.
        y, x = np.ogrid[:200, :200]
        mask = (x - 100)**2 + (y - 100)**2 <= 20**2
        arr[mask] = [0, 0, 0, 0]

        self.img = Image.fromarray(arr)
        self.img.save(self.img_path)

    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)

    def test_internal_hole_detection(self):
        # If we use RETR_EXTERNAL, we only get 1 contour.
        # If RETR_TREE, we get >= 2 (outer + inner).

        params = {
            "border": 5,
            "offset": 0,
            "stroke_w": 2,
            "stroke_c": (0, 255, 0),
            "pdf": True # Trigger tuple return
        }
        worker = StickerWorker([], None, params, mode="process")

        # Process
        res = worker.process_image(self.img_path)

        # Expect tuple: (final_comp, contours, crop_box, size)
        self.assertIsInstance(res, tuple)
        contours = res[1]

        # Should have at least 2 contours (outer ring, inner hole)
        # Note: Dilation might close the hole if border is too big.
        # Hole radius 20. Border 5. Dilation expands body by 5 -> Hole shrinks by 5 -> Radius 15. Still exists.
        self.assertGreaterEqual(len(contours), 2, "Should detect internal hole contour")

    def test_pdf_generation(self):
        params = {
            "border": 5,
            "offset": 0,
            "stroke_w": 2,
            "stroke_c": (0, 255, 0),
            "pdf": True
        }
        # Run Batch to trigger save_as_pdf
        worker = StickerWorker([Path(self.img_path)], Path(self.out_dir), params, mode="process")

        # Mocking save_as_pdf is an option, but we want to test if it runs without error.
        # ReportLab is installed.
        worker.run()

        out_pdf = Path(self.out_dir) / "test_donut_sticker.pdf"
        self.assertTrue(out_pdf.exists(), "PDF should be generated")
        self.assertGreater(out_pdf.stat().st_size, 100, "PDF should not be empty")

if __name__ == '__main__':
    unittest.main()
