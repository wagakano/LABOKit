from reportlab.pdfgen import canvas
from reportlab.lib.colors import PCMYKColor
import sys

c = canvas.Canvas("test_spot.pdf")
spot = PCMYKColor(0, 100, 0, 0, spotName='CutContour_Cut')
c.setStrokeColor(spot)
c.line(0, 0, 100, 100)
c.save()

with open("test_spot.pdf", "rb") as f:
    data = f.read()
    if b"CutContour_Cut" in data:
        print("Found Spot Color!")
    else:
        print("Spot Color MISSING!")
