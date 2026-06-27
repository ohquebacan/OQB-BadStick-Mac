APP_NAME = "OQB BadStick Mac"
APP_VERSION = "1.0.0"
APP_AUTHOR = "OQB / ohquebacan.com"
GITHUB_REPO = "ohquebacan/OQB-BadStick-Mac"
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

LAUNCH_INI_CONTENT = r"""[Launch]
Default = Usb:\Apps\Aurora\Aurora.xex

[Plugins]
; plugin1 = Usb:\Plugins\mi_plugin.xex

[Settings]
"""
