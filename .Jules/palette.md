## 2026-08-02 - Buddy Links for Form Labels
**Learning:** PySide6/Qt `QLabel` objects require an explicit `.setBuddy(widget)` call to properly link the label to a target input widget (like `QComboBox` or `QListWidget`). Without this, screen readers may fail to associate the descriptive label text with the interactive control upon focus, and keyboard users lose the ability to focus the input via mnemonic shortcuts (Alt+Key).
**Action:** Always verify that form labels placed next to input controls in Qt layouts have `.setBuddy()` explicitly configured during UI setup.
