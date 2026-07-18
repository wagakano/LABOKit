import os
import zipfile

def create_patch_zip():
    output_path = 'dist/LABOKit_v3.3_Patch.zip'
    
    files_to_zip = [
        'main.py',
        'core_config.py',
        'bg_remover_tab.py',
        'upscaler_tab.py',
        'translations.py',
        'ui_shared.py',
        'latest_version.json',
        'plugins_manifest.json',
        'README.md',
    ]
    
    plugins_to_include = []
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files_to_zip:
            if os.path.exists(f):
                zf.write(f, f)
            else:
                print(f"Warning: {f} not found.")
                
        for p in plugins_to_include:
            p_path = os.path.join('plugins', p)
            if os.path.exists(p_path):
                zf.write(p_path, p_path)
            else:
                print(f"Warning: {p_path} not found.")
                
    print(f"Successfully created {output_path}")

if __name__ == "__main__":
    create_patch_zip()
