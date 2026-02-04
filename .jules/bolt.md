## 2024-02-04 - Startup Performance & Lazy Loading
**Learning:** Python imports of heavy ML libraries like `torch` and `cv2` can take 1-3 seconds at the module level.
**Action:** Always move heavy imports inside the function that needs them, or use a lazy loader pattern for optional/heavy dependencies to keep startup instant.