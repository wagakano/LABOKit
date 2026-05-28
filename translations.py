import json
import os
from pathlib import Path

# --- CONFIG MANAGEMENT ---
# Robust path determination
_app_data = os.getenv('APPDATA')
if not _app_data:
    _app_data = os.path.expanduser("~") # Fallback for non-Windows or missing var

APP_DATA = Path(_app_data) / "LABOKit"
CONFIG_FILE = APP_DATA / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_config(key, value):
    cfg = load_config()
    cfg[key] = value
    try:
        APP_DATA.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
    except Exception as e:
        print(f"Failed to save config: {e}")

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "en": {
        "menu_file": "&File",
        "menu_config": "&Config",
        "menu_help": "&Help",
        "menu_support": "♥ Support",
        "menu_plugins": "Plugins",
        "tab_bg": "BG Remover",
        "tab_up": "Upscaler",
        "lbl_loaded_bg": "LOADED IMAGES (BG Remover):",
        "lbl_loaded_up": "LOADED IMAGES (Upscaler):",
        "btn_add": "Add Images…",
        "btn_clear": "Clear List",
        "lbl_out": "Output Folder:",
        "btn_change": "Change Folder",
        "btn_proc_sel": "Process (Selected)",
        "btn_proc_all": "Process (All)",
        "lbl_model": "Model:",
        "lbl_scale": "Scale:",
        "lbl_sens": "Sensitivity:",
        "msg_done": "Done",
        "msg_error": "Error",
        "msg_select": "Select images first.",
        "msg_add": "Add images first.",
        # Common Plugin Strings
        "lbl_loaded": "LOADED IMAGES:",
        "lbl_loaded_video": "LOADED VIDEO:",

        "btn_close_img": "Close Image",
        "btn_save": "Save Result",
        "btn_open": "Open Image",
        "btn_open_out": "Open Output Folder",
        # DitheringFX
        "dfx_palette": "Palette:",
        "dfx_mode": "Dither Mode:",
        "dfx_strength": "Pixel Strength:",
        "dfx_bloom": "Bloom / Glow:",
        "dfx_pre": "Pre-Process:",
        "dfx_btn_gif": "Add GIF",
        "dfx_btn_prev_gif": "Preview GIF"
    },
    "ja": {
        "menu_file": "ファイル(&F)",
        "menu_config": "設定(&C)",
        "menu_help": "ヘルプ(&H)",
        "menu_support": "♥ サポート",
        "menu_plugins": "プラグイン",
        "tab_bg": "背景透過",
        "tab_up": "超解像 (高画質化)",
        "lbl_loaded_bg": "読み込み済み画像 (背景透過):",
        "lbl_loaded_up": "読み込み済み画像 (高画質化):",
        "btn_add": "画像を追加…",
        "btn_clear": "リストをクリア",
        "lbl_out": "出力フォルダ:",
        "btn_change": "フォルダ変更",
        "btn_proc_sel": "選択した画像を処理",
        "btn_proc_all": "すべての画像を処理",
        "lbl_model": "モデル:",
        "lbl_scale": "拡大率:",
        "lbl_sens": "感度:",
        "msg_done": "完了",
        "msg_error": "エラー",
        "msg_select": "画像を選択してください。",
        "msg_add": "画像を追加してください。",
        "lbl_loaded": "読み込み済み画像:",
        "lbl_loaded_video": "読み込み済み映像:",

        "btn_close_img": "画像を閉じる",
        "btn_save": "保存",
        "btn_open": "画像を開く",
        "btn_open_out": "出力フォルダを開く",
        "dfx_palette": "パレット:",
        "dfx_mode": "ディザモード:",
        "dfx_strength": "ピクセル強度:",
        "dfx_bloom": "ブルーム / 発光エフェクト:",
        "dfx_pre": "前処理:",
        "dfx_btn_gif": "GIFを追加",
        "dfx_btn_prev_gif": "GIFプレビュー"
    },
    "id": {
        "menu_file": "&Berkas",
        "menu_config": "&Konfigurasi",
        "menu_help": "&Bantuan",
        "menu_support": "♥ Dukungan",
        "menu_plugins": "Plugin",
        "tab_bg": "Hapus Latar Belakang",
        "tab_up": "Peningkat Kualitas",
        "lbl_loaded_bg": "GAMBAR DIMUAT (Hapus Latar Belakang):",
        "lbl_loaded_up": "GAMBAR DIMUAT (Peningkat Kualitas):",
        "btn_add": "Tambah Gambar…",
        "btn_clear": "Bersihkan Daftar",
        "lbl_out": "Folder Keluaran:",
        "btn_change": "Ganti Folder",
        "btn_proc_sel": "Proses Item Terpilih",
        "btn_proc_all": "Proses Semua",
        "lbl_model": "Model:",
        "lbl_scale": "Skala:",
        "lbl_sens": "Sensitivitas:",
        "msg_done": "Selesai",
        "msg_error": "Error",
        "msg_select": "Silakan pilih gambar terlebih dahulu.",
        "msg_add": "Silakan tambahkan gambar terlebih dahulu.",
        "lbl_loaded": "GAMBAR DIMUAT:",
        "lbl_loaded_video": "VIDEO DIMUAT:",

        "btn_close_img": "Tutup Gambar",
        "btn_save": "Simpan Hasil",
        "btn_open": "Buka Gambar",
        "btn_open_out": "Buka Folder Keluaran",
        "dfx_palette": "Palet:",
        "dfx_mode": "Mode Dithering:",
        "dfx_strength": "Intensitas Piksel:",
        "dfx_bloom": "Bloom / Efek Cahaya:",
        "dfx_pre": "Pra-pemrosesan:",
        "dfx_btn_gif": "Tambah GIF",
        "dfx_btn_prev_gif": "Pratinjau GIF"
    }
}

# Load language on init
_cfg = load_config()
CURRENT_LANG = _cfg.get("language", "en")

def set_language(lang_code):
    global CURRENT_LANG
    if lang_code in TRANSLATIONS:
        CURRENT_LANG = lang_code
        save_config("language", lang_code)

def tr(key, default=None):
    res = TRANSLATIONS.get(CURRENT_LANG, {}).get(key)
    if res: return res
    # Fallback to EN
    res = TRANSLATIONS.get("en", {}).get(key)
    return res if res else (default if default else key)
