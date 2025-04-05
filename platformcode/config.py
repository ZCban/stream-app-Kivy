# -*- coding: utf-8 -*-
# Configuration parameters (standalone - no Kodi)

import sys, os, json
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    unichr = chr
    long = int

PLUGIN_NAME = "s4me"
SETTINGS_PATH = os.path.join(os.path.expanduser("~"), f".{PLUGIN_NAME}_settings.json")

# Helper to read/write settings

def _load_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_settings(settings):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def get_setting(name, channel="", server="", default=None):
    settings = _load_settings()
    return settings.get(name, default)

def set_setting(name, value, channel="", server=""):
    settings = _load_settings()
    settings[name] = value
    _save_settings(settings)
    return value

def get_addon_version(with_fix=True):
    version = "1.0.0"
    return version + " DEV" if with_fix else version

def get_addon_core():
    return {"name": PLUGIN_NAME, "path": get_runtime_path()}

def get_localized_string(code):
    fake_strings = {
        20000: "Version",
        20001: "Language",
        30122: "Movie",
        30123: "TV Show",
        30124: "Anime",
        30125: "Documentary",
        30136: "VOS",
        70566: "Sub ITA",
        30137: "Direct",
        70015: "Torrent",
        30138: "Live",
        30139: "Music"
    }
    return fake_strings.get(code, f"String {code}")

def get_localized_category(categ):
    categories = {
        'movie': get_localized_string(30122),
        'tvshow': get_localized_string(30123),
        'anime': get_localized_string(30124),
        'documentary': get_localized_string(30125),
        'vos': get_localized_string(30136),
        'sub-ita': get_localized_string(70566),
        'direct': get_localized_string(30137),
        'torrent': get_localized_string(70015),
        'live': get_localized_string(30138),
        'music': get_localized_string(30139),
    }
    return categories.get(categ, categ)

def get_data_path():
    path = os.path.join(os.getcwd(), "data")
    os.makedirs(path, exist_ok=True)
    return path

def get_runtime_path():
    return os.getcwd()

def get_cookie_data():
    cookie_path = os.path.join(get_data_path(), "cookies.dat")
    if os.path.exists(cookie_path):
        with open(cookie_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_icon():
    return os.path.join(get_runtime_path(), "icon.png")

def get_fanart():
    return os.path.join(get_runtime_path(), "fanart.jpg")

def get_system_platform():
    import platform
    return platform.system().lower()

def get_language():
    return get_localized_string(20001)

def dev_mode():
    return os.path.isdir(os.path.join(get_runtime_path(), '.git'))

def get_platform(full_version=False):
    import platform
    name = platform.system()
    version = platform.version()
    codename = name.lower()
    if full_version:
        return {
            "name_version": codename,
            "num_version": version,
            "platform": codename
        }
    return codename

def is_xbmc():
    return False

def get_videolibrary_support():
    return False

def get_temp_file(filename):
    return os.path.join(get_data_path(), filename)

def get_online_server_thumb(server):
    return f"https://raw.github.com/Stream4me/media/master/resources/servers/{server.lower().replace('_server','')}.png"
