import base64

plugins = ['DitheringFX','QuickVector','IMGConverter','VideoUpscaler','ONNXLoader','QRCodeGenerator','ImageLAB','WatermarkRemover']
for p in plugins:
    url = f"https://github.com/wagakano/LABOKit-assets/releases/download/update2/{p}.kit"
    encoded = base64.b64encode(url.encode()).decode()
    print(f"{p}: {encoded}")
