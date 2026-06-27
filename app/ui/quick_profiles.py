from app.core.catalog import CATALOG

_DASH_KEYS    = [k for k, v in CATALOG.items() if v["tab"] == "dashboards"]
_HB_KEYS      = [k for k, v in CATALOG.items() if v["tab"] == "homebrew"]
_STEALTH_KEYS = [k for k, v in CATALOG.items() if v["tab"] == "stealth"]
_PLUGIN_KEYS  = [k for k, v in CATALOG.items() if v["tab"] == "plugins"]

PROFILES = {
    "minimal": {
        "label":   "Mínima",
        "summary": "Solo el exploit, sin apps adicionales",
        "install": {
            "method":          "abadavatar",
            "patch":           "xeunshackle",
            "skip_xexmenu":    False,
            "skip_rock_band":  True,
            "skip_main_files": False,
            "skip_format":     False,
            "install_all":     False,
            "exit_when_done":  False,
        },
        "dashboards": {k: False for k in _DASH_KEYS},
        "homebrew":   {k: False for k in _HB_KEYS},
        "stealth":    {k: False for k in _STEALTH_KEYS},
        "plugins":    {k: False for k in _PLUGIN_KEYS},
    },
    "recommended": {
        "label":   "Recomendada",
        "summary": "Aurora, XM360, NXE2GOD, 360 Flasher, X-Notify, FakeAnim",
        "install": {
            "method":          "abadavatar",
            "patch":           "xeunshackle",
            "skip_xexmenu":    False,
            "skip_rock_band":  True,
            "skip_main_files": False,
            "skip_format":     False,
            "install_all":     False,
            "exit_when_done":  False,
        },
        "dashboards": {**{k: False for k in _DASH_KEYS}, "aurora": True},
        "homebrew":   {
            **{k: False for k in _HB_KEYS},
            "xm360":       True,
            "nxe2god":     True,
            "nand_flasher": True,
        },
        "stealth":    {k: False for k in _STEALTH_KEYS},
        "plugins":    {
            **{k: False for k in _PLUGIN_KEYS},
            "x_notify": True,
            "fakeanim":  True,
        },
    },
    "full": {
        "label":   "Completa",
        "summary": "Aurora + Freestyle, todos los Homebrew y Plugins",
        "install": {
            "method":          "abadavatar",
            "patch":           "xeunshackle",
            "skip_xexmenu":    False,
            "skip_rock_band":  True,
            "skip_main_files": False,
            "skip_format":     False,
            "install_all":     True,
            "exit_when_done":  False,
        },
        "dashboards": {
            **{k: False for k in _DASH_KEYS},
            "aurora":    True,
            "freestyle": True,
        },
        "homebrew":   {k: True  for k in _HB_KEYS},
        "stealth":    {k: False for k in _STEALTH_KEYS},
        "plugins":    {k: True  for k in _PLUGIN_KEYS},
    },
}


class QuickProfiles:
    def __init__(self, main_window):
        self._mw = main_window

    def apply(self, profile_name: str):
        if profile_name not in PROFILES:
            return
        data = PROFILES[profile_name]
        mw   = self._mw

        mw.install_tab.set_selections(data["install"])
        mw.dashboards_tab.set_selections(data["dashboards"])
        mw.homebrew_tab.set_selections(data["homebrew"])
        mw.stealth_tab.set_selections(data["stealth"])
        mw.plugins_tab.set_selections(data["plugins"])
        mw.install_tab.set_active_profile(profile_name)
        mw._set_status(f"Perfil: {data['label']} — {data['summary']}")
