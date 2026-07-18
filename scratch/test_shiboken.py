import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel
import shiboken6

app = QApplication(sys.argv)
widget = QWidget()
label = QLabel(widget)

print(f"shiboken6.isValid(widget): {shiboken6.isValid(widget)}", flush=True)
print(f"shiboken6.isValid(label): {shiboken6.isValid(label)}", flush=True)

# Delete label
label.deleteLater()
app.processEvents()

print(f"After deleteLater, shiboken6.isValid(label): {shiboken6.isValid(label)}", flush=True)
