## 2026-05-27 - Empty States on PySide6 List Widgets
**Learning:** PySide6's `QListWidget` defaults to an unhelpful white box when empty. Overriding `paintEvent` and drawing a muted text onto `self.viewport()` is a robust, safe pattern to provide helpful "Drag & Drop" guidance without interfering with normal rendering when items are present.
**Action:** Always check `QListWidget` and `QTableWidget` for empty states. If none exists, implement an override in `paintEvent` painting onto the `viewport()`.
