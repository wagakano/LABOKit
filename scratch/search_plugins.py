import os
from pathlib import Path

plugins_dir = Path(__file__).resolve().parent.parent / "LABOKit Plugins" / "3.0"
print(f"Searching for 'original_pixmap' in {plugins_dir}...", flush=True)

found = False
for f in plugins_dir.glob("*.kit"):
    try:
        content = f.read_text(encoding="utf-8", errors="ignore")
        if "original_pixmap" in content:
            print(f"Found in: {f.name}", flush=True)
            # Find lines
            lines = content.splitlines()
            for idx, line in enumerate(lines):
                if "original_pixmap" in line:
                    print(f"  Line {idx+1}: {line.strip()}", flush=True)
            found = True
    except Exception as e:
        print(f"Error reading {f.name}: {e}", flush=True)

if not found:
    print("Not found in any plugins.", flush=True)
