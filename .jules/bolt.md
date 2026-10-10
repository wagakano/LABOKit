## 2024-05-18 - Avoid Caching Local Plugin Versions

**Learning:** Do not cache local plugin versions in memory (`self.plugin_versions`) to optimize background updater threads if the application supports hot-swapping or replacing files without a restart. While caching avoids disk reads (O(N) file opens and regex parsing), it introduces a stale cache problem where hot-updated plugins are incorrectly perceived as their original version, leading to repeated false-positive update prompts. The background thread's network latency vastly overshadows the local disk read overhead, making this a premature optimization.

**Action:** In background update loops, rely on real-time disk reads (e.g., `get_local_version`) to check plugin versions rather than an in-memory cache populated at launch.

## 2024-05-18 - File Filtering Disk I/O Optimization

**Learning:** When using `Path.rglob("*")` to recursively find files in a directory, checking string-based properties (like `f.suffix.lower() in VALID_EXTENSIONS`) before performing disk operations (like `f.is_file()`) can yield significant performance improvements, avoiding unnecessary filesystem stats on subdirectories or non-matching files.

**Action:** Order boolean condition checks in directory traversal from least expensive (string matching) to most expensive (OS stat calls).

## 2024-06-25 - PySide6 Event Filter `isinstance` Optimization

**Learning:** When writing global event filters in PySide6 (which intercept thousands of events per second), using `event.type()` requires a cross-boundary C++ call to the Qt framework, which introduces significant overhead in hot paths. Using Python's native `isinstance()` function to check against parent event classes (like `QInputEvent` instead of specifically checking for `MouseMove`, `MouseButtonPress`, and `KeyPress`) is significantly faster.

**Action:** Prefer `isinstance(event, BaseEventClass)` over `event.type() in (...)` when filtering high-frequency events in PySide6.
