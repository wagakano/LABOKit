## 2026-05-27 - Empty States on PySide6 List Widgets
**Learning:** PySide6's `QListWidget` defaults to an unhelpful white box when empty. Overriding `paintEvent` and drawing a muted text onto `self.viewport()` is a robust, safe pattern to provide helpful "Drag & Drop" guidance without interfering with normal rendering when items are present.
**Action:** Always check `QListWidget` and `QTableWidget` for empty states. If none exists, implement an override in `paintEvent` painting onto the `viewport()`.
## 2026-05-27 - Disabled Buttons in Custom PySide6 Stylesheets
**Learning:** Applying a custom `setStyleSheet()` in PySide6 completely overrides default OS-level styles, meaning missing pseudo-classes like `:disabled` cause inactive buttons to look perfectly active. Additionally, blindly applying cursors via an `EventFilter` (`QEvent.Enter`) or a monkeypatch ignores the `isEnabled()` state, resulting in a clickable hand cursor on a disabled element.
**Action:** Always ensure that custom button stylesheets explicitly define a `:disabled` state with muted styles. When filtering cursor events globally, explicitly check `obj.isEnabled()` and listen for `QEvent.EnabledChange` to set the correct `Qt.ForbiddenCursor` or `Qt.ArrowCursor`.
## 2026-05-27 - Accessible Icon-only Buttons in PySide6
**Learning:** Custom UI controls like 'Minimize' or 'Close' buttons that only use symbols (e.g., "−", "×") or icons are opaque to screen readers and can be confusing to users without context.
**Action:** Always explicitly implement `setAccessibleName` (for screen reader accessibility) and `setToolTip` (for visual context on hover) for icon-only or non-textual UI buttons.
## 2024-05-14 - Interactive Widget Accessibility and Discoverability
**Learning:** PySide6 applications often suffer from "hidden functionality" where interactive behaviors (like right-click context menus in list widgets, keyboard shortcuts for sliders, or dragging behaviors in custom split views) are not obvious to the user or screen readers.
**Action:** Always proactively implement `setToolTip()` to explain hidden interactions (e.g., "Right-click to remove", "Drag to compare") and `setAccessibleName()` on non-textual controls (like sliders or icon-only toggle buttons) to ensure screen reader compatibility and improve overall UX discoverability.
