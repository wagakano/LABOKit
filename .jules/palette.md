## 2026-05-27 - Empty States on PySide6 List Widgets
**Learning:** PySide6's `QListWidget` defaults to an unhelpful white box when empty. Overriding `paintEvent` and drawing a muted text onto `self.viewport()` is a robust, safe pattern to provide helpful "Drag & Drop" guidance without interfering with normal rendering when items are present.
**Action:** Always check `QListWidget` and `QTableWidget` for empty states. If none exists, implement an override in `paintEvent` painting onto the `viewport()`.
## 2026-05-27 - Disabled Buttons in Custom PySide6 Stylesheets
**Learning:** Applying a custom `setStyleSheet()` in PySide6 completely overrides default OS-level styles, meaning missing pseudo-classes like `:disabled` cause inactive buttons to look perfectly active. Additionally, blindly applying cursors via an `EventFilter` (`QEvent.Enter`) or a monkeypatch ignores the `isEnabled()` state, resulting in a clickable hand cursor on a disabled element.
**Action:** Always ensure that custom button stylesheets explicitly define a `:disabled` state with muted styles. When filtering cursor events globally, explicitly check `obj.isEnabled()` and listen for `QEvent.EnabledChange` to set the correct `Qt.ForbiddenCursor` or `Qt.ArrowCursor`.
## 2026-05-27 - Accessible Icon-only Buttons in PySide6
**Learning:** Custom UI controls like 'Minimize' or 'Close' buttons that only use symbols (e.g., "−", "×") or icons are opaque to screen readers and can be confusing to users without context.
**Action:** Always explicitly implement `setAccessibleName` (for screen reader accessibility) and `setToolTip` (for visual context on hover) for icon-only or non-textual UI buttons.
## 2026-05-27 - QListWidget Selection Mode UX
**Learning:** By default, PySide6's `QListWidget` only allows single item selection (`SingleSelection`). If the application's backend logic (e.g. processing selected items) supports arrays of elements, leaving the UI in single selection mode causes a severe disconnect in UX and wastes the user's time.
**Action:** When working with list widgets where batch processing is available, explicitly enable `QAbstractItemView.ExtendedSelection` so users can use standard Shift/Ctrl modifiers to select multiple items, and update tooltips to communicate this feature.
