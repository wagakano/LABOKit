## 2026-08-01 - Link QLabel to inputs with setBuddy
**Learning:** PySide6/Qt requires explicit linking between `QLabel` and input controls (like `QComboBox` or `QListWidget`) using `.setBuddy(target_widget)` to ensure screen readers correctly announce the label text upon focus and to enable keyboard navigation shortcuts.
**Action:** Always use `.setBuddy()` when creating forms or labeled inputs in PySide6 to maintain keyboard accessibility and screen reader support.
