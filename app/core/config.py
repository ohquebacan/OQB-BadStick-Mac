import os

APP_NAME = "OQB BadStick Mac"
APP_VERSION = "1.0.1"
APP_AUTHOR = "OQB / ohquebacan.com"
GITHUB_REPO = "ohquebacan/OQB-BadStick-Mac"
TEMP_DIR = os.path.expanduser("~/OQB-BadStick-Mac/temp")
DISCORD_URL = "https://discord.gg/HzUP3shMgQ"

SOURCES = {
    "abadavatar": {
        "name": "ABadAvatar",
        "api_url": "https://api.github.com/repos/shutterbug2000/ABadAvatar/releases/latest",
        "fallback_url": "https://github.com/shutterbug2000/ABadAvatar/releases/download/vPB1.0/ABadAvatar-publicbeta1.0.zip",
        "asset_pattern": ".zip",
        "author": "shutterbug2000",
    },
    "abadmemunit": {
        "name": "ABadMemUnit",
        "api_url": "https://api.github.com/repos/shutterbug2000/ABadMemUnit/releases/latest",
        "fallback_url": None,
        "asset_pattern": ".zip",
        "author": "shutterbug2000",
    },
    "xeunshackle": {
        "name": "XeUnshackle",
        "api_url": "https://api.github.com/repos/Byrom90/XeUnshackle/releases/latest",
        "fallback_url": "https://github.com/Byrom90/XeUnshackle/releases/download/v1.03/XeUnshackle-v1.03.zip",
        "asset_pattern": ".zip",
        "author": "Byrom90",
    },
    "freemyxe": {
        "name": "FreeMyXe",
        "api_url": "https://api.github.com/repos/FreeMyXe/FreeMyXe/releases/latest",
        "fallback_url": "https://github.com/FreeMyXe/FreeMyXe/releases/download/v1.1/FreeMyXe-v1.1.zip",
        "asset_pattern": ".zip",
        "author": "InvoxiPlayGames",
    },
    "nand_flasher": {
        "name": "Simple 360 NAND Flasher",
        "direct_url": "https://github.com/Swizzy/XDK_Projects/raw/master/Simple%20360%20NAND%20Flasher/Simple%20360%20NAND%20Flasher.zip",
        "asset_pattern": ".zip",
        "author": "Swizzy",
    },
    "dashlaunch": {
        "name": "DashLaunch",
        "api_url": "https://api.github.com/repos/XboxUnity/Dashlaunch/releases/latest",
        "fallback_url": None,
        "asset_pattern": ".zip",
        "author": "XboxUnity",
    },
}

MANUAL_DOWNLOADS = {
    "aurora": {
        "name": "Aurora Dashboard",
        "url": "https://phoenix.xboxunity.net/#/news",
        "filename": "Aurora 0.7b.2 - Release Package.rar",
        "dest_folder": "Apps/Aurora",
        "author": "Phoenix Team",
    },
    "xexmenu": {
        "name": "XeXMenu",
        "url": "https://www.se7ensins.com/forums/threads/xex-menu-1-1.473740/",
        "dest_folder": "Apps/XeXMenu",
        "author": "Team XeDEV",
    },
}

EXPLOIT_INFO = {
    "abadavatar": "Requiere dashboard 17559 y datos de avatar instalados",
    "abadmemunit": "Alternativa si ABadAvatar no funciona en tu consola",
}

PAYLOAD_INFO = "XeUnshackle es más compatible con plugins y stealth servers"

_LAUNCH_INI_HEADER = """; launch.xex V3.0 config file
; parsed by simpleIni http://code.jellycan.com/simpleini/
; --- Generado por OQB BadStick Mac ---
"""

_LAUNCH_INI_FOOTER = r"""
[Externals]
ftpserv = false
ftpport = 21
updserv = false
calaunch = false
fahrenheit = false

[Settings]
nxemini = true
pingpatch = true
contpatch = false
xblapatch = false
licpatch = false
fatalfreeze = false
fatalreboot = false
safereboot = true
regionspoof = false
region = 0x7fff
dvdexitdash = false
xblaexitdash = false
nosysexit = false
nohud = false
noupdater = true
debugout = true
exchandler = true
liveblock = true
livestrong = false
remotenxe = false
hddalive = false
hddtimer = 210
signnotice = false
autoshut = false
autooff = false
xhttp = false
tempbcast = false
temptime = 10
tempport = 7030
sockpatch = true
passlaunch = false
fakelive = false
nonetstore = true
shuttemps = false
devprof = false
devlink = false
autoswap = false
nohealth = true
nooobe = true
autofake = false
autofake0 = 0x00000000
autofake1 = 0x00000000
autofake2 = 0x00000000
autofake3 = 0x00000000
autofake4 = 0x00000000
autofake5 = 0x00000000
autofake6 = 0x00000000
autofake7 = 0x00000000
autofake8 = 0x00000000
autofake9 = 0x00000000
autocont = false
"""

XEXMENU_CONTENT_PATH = r"Usb:\Content\0000000000000000\C0DE9999\00080000\C0DE99990F586558"


def build_launch_ini(
    default_launcher_key: str,
    downloaded_keys: set,
    catalog: dict,
) -> str:
    """
    Genera launch.ini dinámicamente según lo que fue instalado.

    default_launcher_key: clave del CATALOG (ej: "aurora", "freestyle"),
        "xexmenu", o "official" (Sfc:\\dash.xex)
    downloaded_keys: set de claves que fueron descargadas/instaladas
    """

    def usb_path(dest: str, xex: str) -> str:
        return "Usb:\\" + dest.replace("/", "\\") + "\\" + xex

    # ── Default ────────────────────────────────────────────────────────
    if default_launcher_key == "official":
        default_path = r"Sfc:\dash.xex"
    elif default_launcher_key == "xexmenu":
        default_path = XEXMENU_CONTENT_PATH
    elif default_launcher_key in catalog and default_launcher_key in downloaded_keys:
        e = catalog[default_launcher_key]
        default_path = usb_path(e["dest"], e.get("xex", "default.xex"))
    else:
        default_path = ""

    # ── BUT_X: XeXMenu si está instalado, si no vacío ──────────────────
    but_x = XEXMENU_CONTENT_PATH if "xexmenu" in downloaded_keys else ""

    # ── BUT_Y: siempre el dashboard oficial como escape ─────────────────
    but_y = r"Sfc:\dash.xex"

    # ── Plugins: construir lista desde lo instalado ─────────────────────
    plugin_paths = []

    if "general_plugins" in downloaded_keys:
        e = catalog.get("general_plugins", {})
        for xex_name in e.get("plugin_xex_list", []):
            plugin_paths.append(f"Usb:\\Plugins\\{xex_name}")

    plugin_keys_ordered = ["xbpirate", "hiddriver360", "hvp2"]
    for key in plugin_keys_ordered:
        if key not in downloaded_keys:
            continue
        e = catalog.get(key, {})
        xex = e.get("xex")
        if xex and e.get("dest"):
            plugin_paths.append(usb_path(e["dest"], xex))

    plugin_lines = ""
    for i in range(1, 6):
        val = plugin_paths[i - 1] if i <= len(plugin_paths) else ""
        plugin_lines += f"plugin{i} = {val}\n"

    paths_block = (
        "[Paths]\n"
        f"BUT_A =\n"
        f"BUT_B =\n"
        f"BUT_X = {but_x}\n"
        f"BUT_Y = {but_y}\n"
        f"Start =\n"
        f"Back =\n"
        f"LBump =\n"
        f"RThumb =\n"
        f"LThumb =\n"
        f"\n"
        f"Default = {default_path}\n"
        f"Guide =\n"
        f"Power =\n"
        f"Configapp =\n"
        f"Fakeanim =\n"
        f"Dumpfile =\n"
        f"\n"
    )
    plugins_block = f"[Plugins]\n{plugin_lines}"

    return _LAUNCH_INI_HEADER + paths_block + plugins_block + _LAUNCH_INI_FOOTER
