import re
from pathlib import Path
import json

version_map = {
    "DitheringFX.kit": "3.4",
    "ImageLAB.kit": "3.6",
    "IMGConverter.kit": "1.8",
    "ONNXLoader.kit": "1.2",
    "QRCodeGenerator.kit": "1.8",
    "QuickVector.kit": "1.7",
    "VideoUpscaler.kit": "1.4"
}

# 1. Update plugin files
for p in Path('LABOKit Plugins/3.0').glob('*.kit'):
    if p.name in version_map:
        new_ver = version_map[p.name]
        content = p.read_text(encoding='utf-8')
        content = re.sub(r'PLUGIN_VERSION\s*=\s*"[^"]+"', f'PLUGIN_VERSION = "{new_ver}"', content)
        p.write_text(content, encoding='utf-8')
        print(f"Updated {p.name} to {new_ver}")

# 2. Update plugins_manifest.json
manifest_path = Path('plugins_manifest.json')
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for name, info in manifest.items():
        # Match name to key in version_map
        for filename, new_ver in version_map.items():
            if name in filename: # e.g. DitheringFX in DitheringFX.kit
                info['version'] = new_ver
                print(f"Updated manifest version for {name} to {new_ver}")
    manifest_path.write_text(json.dumps(manifest, indent=4), encoding='utf-8')
