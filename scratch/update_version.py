import re
from pathlib import Path

# 1. Update main.py
main_path = Path('main.py')
content = main_path.read_text(encoding='utf-8')
# Find APP_VERSION
match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', content)
if match:
    old_ver = match.group(1)
    content = content.replace(f'APP_VERSION = "{old_ver}"', 'APP_VERSION = "3.2.0"')
    main_path.write_text(content, encoding='utf-8')
    print(f"Updated main.py: {old_ver} -> 3.2.0")
else:
    print("APP_VERSION not found in main.py")

# 2. Update all plugins
for p in Path('LABOKit Plugins/3.0').glob('*.kit'):
    content = p.read_text(encoding='utf-8')
    match = re.search(r'PLUGIN_VERSION\s*=\s*"([^"]+)"', content)
    if match:
        old_ver = match.group(1)
        # We replace PLUGIN_VERSION = "old_ver" with PLUGIN_VERSION = "3.2"
        # Or should we use "3.2.0" or "3.2"? The user requested "3.2".
        # Let's check how it is styled. Let's replace with "3.2".
        content = re.sub(r'PLUGIN_VERSION\s*=\s*"[^"]+"', 'PLUGIN_VERSION = "3.2"', content)
        p.write_text(content, encoding='utf-8')
        print(f"Updated {p.name}: {old_ver} -> 3.2")
    else:
        print(f"PLUGIN_VERSION not found in {p.name}")
