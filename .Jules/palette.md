## 2026-05-27 - Empty States on PySide6 List Widgets
**Learning:** PySide6's `QListWidget` defaults to an unhelpful white box when empty. Overriding `paintEvent` and drawing a muted text onto `self.viewport()` is a robust, safe pattern to provide helpful "Drag & Drop" guidance without interfering with normal rendering when items are present.
**Action:** Always check `QListWidget` and `QTableWidget` for empty states. If none exists, implement an override in `paintEvent` painting onto the `viewport()`.
## 2026-05-27 - Disabled Buttons in Custom PySide6 Stylesheets
**Learning:** Applying a custom `setStyleSheet()` in PySide6 completely overrides default OS-level styles, meaning missing pseudo-classes like `:disabled` cause inactive buttons to look perfectly active. Additionally, blindly applying cursors via an `EventFilter` (`QEvent.Enter`) or a monkeypatch ignores the `isEnabled()` state, resulting in a clickable hand cursor on a disabled element.
**Action:** Always ensure that custom button stylesheets explicitly define a `:disabled` state with muted styles. When filtering cursor events globally, explicitly check `obj.isEnabled()` and listen for `QEvent.EnabledChange` to set the correct `Qt.ForbiddenCursor` or `Qt.ArrowCursor`.
## 2026-05-27 - Accessible Labels for Icon-Only PySide6 Buttons
**Learning:** PySide6 UI elements that only use icons or simple characters (like "×" for close or "−" for minimize) lack context for screen readers. Using `setAccessibleName` provides this crucial context for screen readers while `setToolTip` helps visual users on hover.
**Action:** Always ensure icon-only or non-textual buttons in PySide6 interfaces have `setAccessibleName` and `setToolTip` set to provide clear context for all users.
