import sys
from PySide6.QtWidgets import QApplication
import importlib.machinery
import importlib.util

sys.path.append(r'C:\Users\shira\Projects\LABOKit')

app = QApplication(sys.argv)
loader = importlib.machinery.SourceFileLoader('qrcode', r'C:\Users\shira\Projects\LABOKit\LABOKit Plugins\3.0\QRCodeGenerator.kit')
spec = importlib.util.spec_from_file_location('qrcode', r'C:\Users\shira\Projects\LABOKit\LABOKit Plugins\3.0\QRCodeGenerator.kit', loader=loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

widget = mod.create_tab()
widget.show()
widget.resize(800, 600)
# Force event loop to process so layout updates
app.processEvents()
widget.grab().save(r'C:\Users\shira\.gemini\antigravity\brain\4aeb917d-d910-4256-bf58-6a816b893f18\qrcode_preview.png')
