
import sys
import time
from types import ModuleType

# --- MOCK PYSIDE6 ---
# We mock the parts of PySide6 used in main.py so we can run the logic flow without the library.

pyside_core = ModuleType('PySide6.QtCore')
pyside_gui = ModuleType('PySide6.QtGui')
pyside_widgets = ModuleType('PySide6.QtWidgets')

sys.modules['PySide6'] = ModuleType('PySide6')
sys.modules['PySide6.QtCore'] = pyside_core
sys.modules['PySide6.QtGui'] = pyside_gui
sys.modules['PySide6.QtWidgets'] = pyside_widgets

# Mocks
class MockQt:
    WindowStaysOnTopHint = 1
    SmoothTransformation = 1
    UserRole = 1
    CustomContextMenu = 1
    AlignCenter = 1
    KeepAspectRatio = 1
    ApplicationModal = 1
    LeftButton = 1
    WA_TransparentForMouseEvents = 1
    FramelessWindowHint = 1

class MockSignal:
    def __init__(self, *args): pass
    def connect(self, func): pass
    def emit(self, *args): pass

class MockQObject:
    def __init__(self, *args, **kwargs): pass

class MockQThread(MockQObject):
    started = MockSignal()
    finished = MockSignal()
    def start(self):
        print("[MockQt] Thread started (fake, runs synchronously for this test unless overridden)")
        self.run()
        self.finished.emit()
    def run(self): pass
    def wait(self): pass

class MockQTimer(MockQObject):
    timeout = MockSignal()
    def start(self, ms): print(f"[MockQt] Timer started: {ms}ms")
    def stop(self): pass

class MockQApplication:
    def __init__(self, args): print("[MockQt] QApplication initialized")
    def processEvents(self): print("[MockQt] processEvents() called")
    def exec(self):
        print("[MockQt] app.exec() called - Event Loop Started")
        return 0
    def primaryScreen(self): return MockScreen()
    def setApplicationName(self, name): pass
    def setWindowIcon(self, icon): pass
    def setFont(self, font): pass
    def setStyleSheet(self, sheet): pass

class MockScreen:
    def geometry(self): return MockRect(0,0,1920,1080)

class MockRect:
    def __init__(self, x,y,w,h):
        self._w = w
        self._h = h
    def height(self): return self._h
    def width(self): return self._w

class MockWidget(MockQObject):
    def show(self): print(f"[MockQt] {self.__class__.__name__}.show() called")
    def setFixedSize(self, w, h): pass
    def setWindowFlags(self, f): pass
    def setCentralWidget(self, w): pass
    def setAttribute(self, a): pass
    def setStyleSheet(self, s): pass
    def setWindowTitle(self, t): pass
    def close(self): print(f"[MockQt] {self.__class__.__name__}.close() called")
    def setFixedWidth(self, w): pass
    def setFixedHeight(self, h): pass
    def setWindowModality(self, m): pass
    def move(self, p): pass
    def frameGeometry(self): return MockRect(0,0,100,100)
    def mapToGlobal(self, p): return p
    def update(self): pass
    def hide(self): pass

class MockQSplashScreen(MockWidget):
    def finish(self, w): print("[MockQt] Splash.finish() called")

class MockQMainWindow(MockWidget): pass
class MockQLabel(MockWidget):
    def setText(self, t): pass
    def setStyleSheet(self, s): pass
    def setAttribute(self, a): pass
    def setWordWrap(self, b): pass
    def setAlignment(self, a): pass
    def setPixmap(self, p): pass
    def adjustSize(self): pass

class MockQPushButton(MockWidget):
    clicked = MockSignal()
    def setIcon(self, i): pass
    def setCheckable(self, b): pass
    def setCursor(self, c): pass
    def setVisible(self, b): pass
    def isChecked(self): return False
    def setChecked(self, b): pass

class MockQProgressBar(MockWidget): pass
class MockQProgressDialog(MockWidget):
    def setValue(self, v): pass
    def setLabelText(self, t): pass
    def wasCanceled(self): return False

class MockQPixmap:
    def __init__(self, *args): pass
    def scaledToWidth(self, w, m): return self
    def fill(self, c): pass
    def scaled(self, s, a, m): return self
    def size(self): return MockRect(0,0,100,100)
    def isNull(self): return False
    def width(self): return 100
    def height(self): return 100

class MockQIcon:
    def __init__(self, *args): pass

class MockQFont:
    def __init__(self, *args): pass

class MockQAction:
    triggered = MockSignal()
    def __init__(self, text, parent=None, enabled=True): pass

class MockQFrame(MockWidget):
    HLine = 1
    Sunken = 1
    def setFrameShape(self, s): pass
    def setFrameShadow(self, s): pass
    def setContentsMargins(self, *args): pass

class MockLayout:
    def setContentsMargins(self, *args): pass
    def setSpacing(self, s): pass
    def addWidget(self, w): pass
    def addLayout(self, l, s=0): pass
    def addStretch(self, s): pass
    def addSpacing(self, s): pass

class MockQVBoxLayout(MockLayout):
    def __init__(self, parent=None): pass

class MockQHBoxLayout(MockLayout):
    def __init__(self, parent=None): pass

class MockQListWidget(MockWidget):
    customContextMenuRequested = MockSignal()
    files_dropped = MockSignal() # Custom
    currentRowChanged = MockSignal()
    currentItemChanged = MockSignal()
    def setContextMenuPolicy(self, p): pass
    def addItem(self, i): pass
    def setCurrentRow(self, r): pass
    def count(self): return 0
    def currentRow(self): return -1
    def clear(self): pass
    def itemAt(self, p): return None
    def takeItem(self, r): pass
    def row(self, i): return -1
    def currentItem(self): return None
    def selectedItems(self): return []
    def setAcceptDrops(self, b): pass

class MockQListWidgetItem:
    def __init__(self, text): pass
    def setData(self, r, d): pass
    def data(self, r): return None

class MockQFileDialog:
    @staticmethod
    def getOpenFileNames(*args): return ([], "")
    @staticmethod
    def getExistingDirectory(*args): return ""
    @staticmethod
    def getOpenFileName(*args): return ("", "")

class MockQMessageBox:
    Information = 1
    AcceptRole = 1
    RejectRole = 1
    def __init__(self, parent=None): pass
    def setWindowTitle(self, t): pass
    def setText(self, t): pass
    def setInformativeText(self, t): pass
    def setIcon(self, i): pass
    def addButton(self, t, r): return MockQPushButton()
    def exec(self): pass
    def clickedButton(self): return None
    @staticmethod
    def information(*args): pass
    @staticmethod
    def warning(*args): pass
    @staticmethod
    def critical(*args): pass

class MockQComboBox(MockWidget):
    currentTextChanged = MockSignal()
    def addItems(self, i): pass
    def setCurrentText(self, t): pass
    def currentText(self): return ""

class MockQTabWidget(MockWidget):
    def addTab(self, w, t): pass
    def indexOf(self, w): return -1
    def removeTab(self, i): pass
    def currentWidget(self): return MockWidget()

class MockQDialog(MockWidget):
    def exec(self): pass

class MockQPlainTextEdit(MockWidget):
    def setReadOnly(self, b): pass
    def setFont(self, f): pass

class MockQMenuBar(MockWidget):
    def addMenu(self, t): return MockQMenu()

class MockQMenu(MockWidget):
    def addAction(self, a, s=None): pass
    def addSeparator(self): pass
    def addMenu(self, m): return MockQMenu()
    def exec(self, p): pass
    def clear(self): pass

class MockQScrollArea(MockWidget):
    def setWidgetResizable(self, b): pass
    def setAlignment(self, a): pass
    def setWidget(self, w): pass

class MockQPainter:
    Antialiasing = 1
    def __init__(self, p): pass
    def setRenderHint(self, h): pass
    def setPen(self, p): pass
    def drawLine(self, x1, y1, x2, y2): pass
    def end(self): pass

class MockQPen:
    def __init__(self, c): pass
    def setWidth(self, w): pass

class MockQColor:
    def __init__(self, c): pass

class MockQDesktopServices:
    @staticmethod
    def openUrl(u): print(f"[MockQt] Opening URL: {u}")

class MockQUrl:
    def __init__(self, u): pass
    @staticmethod
    def fromLocalFile(f): return f

class MockQRegion:
    def __init__(self, *args): pass

class MockQPainterPath:
    def addRoundedRect(self, *args): pass
    def toFillPolygon(self): return MockQPainterPath()
    def toPolygon(self): return []

class MockQRectF:
    def __init__(self, *args): pass

# Assign Mocks
pyside_core.Qt = MockQt
pyside_core.QSize = lambda w,h: None
pyside_core.QTimer = MockQTimer
pyside_core.QUrl = MockQUrl
pyside_core.QRectF = MockQRectF
pyside_core.QThread = MockQThread
pyside_core.Signal = MockSignal

pyside_gui.QAction = MockQAction
pyside_gui.QPixmap = MockQPixmap
pyside_gui.QFont = MockQFont
pyside_gui.QIcon = MockQIcon
pyside_gui.QDesktopServices = MockQDesktopServices
pyside_gui.QPainterPath = MockQPainterPath
pyside_gui.QRegion = MockQRegion
pyside_gui.QColor = MockQColor
pyside_gui.QPalette = lambda: None
pyside_gui.QPainter = MockQPainter
pyside_gui.QPen = MockQPen

pyside_widgets.QApplication = MockQApplication
pyside_widgets.QMainWindow = MockQMainWindow
pyside_widgets.QWidget = MockWidget
pyside_widgets.QVBoxLayout = MockQVBoxLayout
pyside_widgets.QHBoxLayout = MockQHBoxLayout
pyside_widgets.QListWidget = MockQListWidget
pyside_widgets.QListWidgetItem = MockQListWidgetItem
pyside_widgets.QLabel = MockQLabel
pyside_widgets.QPushButton = MockQPushButton
pyside_widgets.QFileDialog = MockQFileDialog
pyside_widgets.QMessageBox = MockQMessageBox
pyside_widgets.QProgressDialog = MockQProgressDialog
pyside_widgets.QFrame = MockQFrame
pyside_widgets.QComboBox = MockQComboBox
pyside_widgets.QTabWidget = MockQTabWidget
pyside_widgets.QDialog = MockQDialog
pyside_widgets.QPlainTextEdit = MockQPlainTextEdit
pyside_widgets.QSplashScreen = MockQSplashScreen
pyside_widgets.QMenuBar = MockQMenuBar
pyside_widgets.QSizePolicy = lambda: None
pyside_widgets.QScrollArea = MockQScrollArea
pyside_widgets.QMenu = MockQMenu


# --- MOCK OTHER DEPENDENCIES ---
sys.modules['torch'] = ModuleType('torch')
sys.modules['cv2'] = ModuleType('cv2')
sys.modules['numpy'] = ModuleType('numpy')
sys.modules['basicsr'] = ModuleType('basicsr')
sys.modules['realesrgan'] = ModuleType('realesrgan')
sys.modules['svgwrite'] = ModuleType('svgwrite')
sys.modules['packaging'] = ModuleType('packaging')
sys.modules['PIL'] = ModuleType('PIL')

# --- REPRODUCTION SCRIPT LOGIC ---

# Copy of deploy_assets from main.py (simplified/modified for test)
def deploy_assets():
    print("[TEST] deploy_assets called - START")
    print("[TEST] simulating heavy work (sleep 3s)...")
    time.sleep(3)
    print("[TEST] deploy_assets - END")

# Copy of main from main.py (modified)
def main():
    print("[TEST] main() starting...")
    app = pyside_widgets.QApplication(sys.argv)

    # Splash
    pix = pyside_gui.QPixmap(400,100)
    splash = pyside_widgets.QSplashScreen(pix, 0)
    splash.show()
    app.processEvents()

    # The BLOCKING Call
    deploy_assets()

    # Post-load
    try:
        # We don't need full UI init for this test, just proving the blocking nature
        print("[TEST] Warmup done")

        # Simulate Window Load
        win = pyside_widgets.QMainWindow()
        win.show()
        splash.finish(win)

        sys.exit(app.exec())
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
