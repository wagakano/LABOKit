from PySide6.QtWidgets import QApplication
from ui_shared import FileDropListWidget

app = QApplication([])
widget = FileDropListWidget()
print(widget.toolTip())
