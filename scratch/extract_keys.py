import re
from pathlib import Path

keys = set()
# Search in main.py
with open('main.py', 'r', encoding='utf-8') as f:
    keys.update(re.findall(r'tr\(\s*"([^"]+)"', f.read()))

# Search in plugins
for p in Path('LABOKit Plugins/3.0').glob('*.kit'):
    with open(p, 'r', encoding='utf-8') as f:
        keys.update(re.findall(r'tr\(\s*"([^"]+)"', f.read()))

print("All keys used in app and plugins:", sorted(list(keys)))
