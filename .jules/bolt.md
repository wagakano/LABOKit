## 2024-05-18 - Avoid Caching Local Plugin Versions

**Learning:** Do not cache local plugin versions in memory (`self.plugin_versions`) to optimize background updater threads if the application supports hot-swapping or replacing files without a restart. While caching avoids disk reads (O(N) file opens and regex parsing), it introduces a stale cache problem where hot-updated plugins are incorrectly perceived as their original version, leading to repeated false-positive update prompts. The background thread's network latency vastly overshadows the local disk read overhead, making this a premature optimization.

**Action:** In background update loops, rely on real-time disk reads (e.g., `get_local_version`) to check plugin versions rather than an in-memory cache populated at launch.

## 2024-05-18 - File Filtering Disk I/O Optimization

**Learning:** When using `Path.rglob("*")` to recursively find files in a directory, checking string-based properties (like `f.suffix.lower() in VALID_EXTENSIONS`) before performing disk operations (like `f.is_file()`) can yield significant performance improvements, avoiding unnecessary filesystem stats on subdirectories or non-matching files.

**Action:** Order boolean condition checks in directory traversal from least expensive (string matching) to most expensive (OS stat calls).
## 2026-07-29 - Pre-compile Regex for Sorting Optimization
**Learning:** Python's `sorted()` function evaluates the `key` function for every item in the list, making any overhead inside that function extremely costly (O(N log N)). Inline `re.split(r'(...)`, ...)` inside the `key` lambda forces the regex engine to parse and fetch the compiled regex from cache on every single call.
**Action:** Always pre-compile static regular expressions (e.g., `NATURAL_SORT_RE = re.compile(...)`) at the module level when they are used inside tight loops or high-frequency callbacks like sorting keys. Call `NATURAL_SORT_RE.split(...)` directly to skip cache lookups and improve execution speed.
