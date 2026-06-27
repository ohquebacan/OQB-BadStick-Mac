import os

import customtkinter as ctk

from app.core.catalog import CATALOG
from app.core.config import LAUNCH_INI_CONTENT

# (key, button_label, desc, base_color, active_color, base_border, active_border)
_PROFILE_DEFS = [
    (
        "minimal",
        "⚡  MÍNIMA",
        "Solo lo esencial\npara arrancar",
        "#252525", "#333333", "#505050", "#aaaaaa",
    ),
    (
        "recommended",
        "✅  RECOMENDADA",
        "Lo que usa\nla mayoría",
        "#0a4a0a", "#107C10", "#0d6a0d", "#4CAF50",
    ),
    (
        "full",
        "🚀  COMPLETA",
        "Todo lo disponible\nautomático",
        "#0d1d35", "#1a3a5c", "#1a3060", "#4a90d9",
    ),
]

_METHODS = [
    ("badupdate",    "BadUpdate"),
    ("abadavatar",   "BadAvatar  (recomendado)"),
    ("badavatarhdd", "BadAvatarHDD"),
    ("abadmemunit",  "ABadMemUnit"),
]

_PATCHES = [
    ("xeunshackle", "XeUnshackle  (recomendado)"),
    ("freemyxe",    "FreeMyXe"),
]

_CONFIG_LABELS = [
    ("skip_xexmenu",    "Omitir XeXMenu"),
    ("skip_rock_band",  "Omitir Rock Band"),
    ("skip_main_files", "Omitir archivos principales"),
    ("skip_format",     "Omitir formateo  (USB en FAT32)"),
    ("install_all",     "Instalar todos los archivos"),
    ("exit_when_done",  "Salir al terminar"),
]


class InstallTab(ctk.CTkFrame):
    def __init__(self, parent, icon_path: str = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._icon_path = icon_path
        self._method_var = ctk.StringVar(value="abadavatar")
        self._patch_var  = ctk.StringVar(value="xeunshackle")
        self._config_vars = {
            "skip_xexmenu":     ctk.BooleanVar(value=False),
            "skip_rock_band":   ctk.BooleanVar(value=True),
            "skip_main_files":  ctk.BooleanVar(value=False),
            "skip_format":      ctk.BooleanVar(value=False),
            "install_all":      ctk.BooleanVar(value=False),
            "exit_when_done":   ctk.BooleanVar(value=False),
        }
        self._toggleable         = []
        self._custom_launch_ini  = None
        self._active_profile_key = None
        self._profile_btns       = {}   # key -> (btn, base_c, act_c, base_b, act_b)
        self._profile_callback   = None
        self._on_change_cb       = None
        self._build()
        self.update_idletasks()

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def _build(self):
        # Two columns: fixed left + expanding right
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Left panel ─────────────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="#161616", corner_radius=0, width=260)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        if self._icon_path and os.path.exists(self._icon_path):
            try:
                from PIL import Image
                pil_img = Image.open(self._icon_path).resize((220, 220), Image.LANCZOS)
                self._ctk_img = ctk.CTkImage(
                    light_image=pil_img, dark_image=pil_img, size=(220, 220)
                )
                ctk.CTkLabel(left, image=self._ctk_img, text="").pack(pady=(20, 8))
            except Exception:
                self._fallback_logo(left)
        else:
            self._fallback_logo(left)

        ctk.CTkLabel(
            left, text="Xbox 360  •  macOS / Linux",
            font=ctk.CTkFont(size=9), text_color="#333333",
        ).pack()

        # ── Right panel (normal CTkFrame, NOT scrollable) ───────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 4), pady=8)

        # ── 1. Header ─────────────────────────────────────────────────
        ctk.CTkLabel(
            right, text="Instalación Rápida",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#888888",
        ).pack(anchor="w", pady=(0, 4))

        # ── 2. Profile buttons ────────────────────────────────────────
        self._btn_row = ctk.CTkFrame(right, fg_color="transparent")
        self._btn_row.pack(anchor="w", pady=(0, 2))

        for key, label, desc, base_c, act_c, base_b, act_b in _PROFILE_DEFS:
            btn = ctk.CTkButton(
                self._btn_row,
                text=f"{label}\n{desc}",
                command=lambda k=key: self._on_profile_btn_click(k),
                fg_color=base_c,
                hover_color=act_c,
                border_color=base_b,
                border_width=1,
                corner_radius=8,
                width=190,
                height=72,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#dddddd",
            )
            btn.pack(side="left", padx=(0, 6))
            self._profile_btns[key] = (btn, base_c, act_c, base_b, act_b)

        self._custom_lbl = ctk.CTkLabel(
            right, text="Configuración personalizada",
            font=ctk.CTkFont(size=9), text_color="#555555",
        )

        # ── Separator ─────────────────────────────────────────────────
        ctk.CTkFrame(right, fg_color="#2a2a2a", height=1).pack(
            fill="x", pady=(6, 8)
        )

        # ── 4–6. Método de Instalación ────────────────────────────────
        ctk.CTkLabel(
            right, text="Método de Instalación",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa",
        ).pack(anchor="w", pady=(0, 3))

        method_frame = ctk.CTkFrame(right, fg_color="transparent")
        method_frame.pack(anchor="w")

        for val, lbl in _METHODS:
            rb = ctk.CTkRadioButton(
                method_frame, text=lbl, value=val, variable=self._method_var,
                command=self._on_method_change,
                fg_color="#107C10", hover_color="#0d6a0d",
            )
            rb.pack(anchor="w", pady=1)
            self._toggleable.append(rb)

        self._method_info = ctk.CTkLabel(
            right, text=CATALOG["abadavatar"]["desc"],
            font=ctk.CTkFont(size=9), text_color="#555555", anchor="w",
        )
        self._method_info.pack(anchor="w", pady=(2, 0))

        # ── Separator ─────────────────────────────────────────────────
        ctk.CTkFrame(right, fg_color="#2a2a2a", height=1).pack(
            fill="x", pady=(8, 8)
        )

        # ── 8–10. Parches ─────────────────────────────────────────────
        ctk.CTkLabel(
            right, text="Parches",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa",
        ).pack(anchor="w", pady=(0, 3))

        patch_frame = ctk.CTkFrame(right, fg_color="transparent")
        patch_frame.pack(anchor="w")

        for val, lbl in _PATCHES:
            rb = ctk.CTkRadioButton(
                patch_frame, text=lbl, value=val, variable=self._patch_var,
                command=self._on_change,
                fg_color="#107C10", hover_color="#0d6a0d",
            )
            rb.pack(anchor="w", pady=1)
            self._toggleable.append(rb)

        self._patch_note = ctk.CTkLabel(
            right, text="(No aplica para BadUpdate)",
            font=ctk.CTkFont(size=9), text_color="#3a3a3a",
        )

        ctk.CTkLabel(
            right,
            text="XeUnshackle: compatible con plugins y stealth.  FreeMyXe: open-source.",
            font=ctk.CTkFont(size=9), text_color="#555555",
        ).pack(anchor="w", pady=(2, 0))

        # ── Separator ─────────────────────────────────────────────────
        ctk.CTkFrame(right, fg_color="#2a2a2a", height=1).pack(
            fill="x", pady=(8, 8)
        )

        # ── 12–13. Configuración ──────────────────────────────────────
        ctk.CTkLabel(
            right, text="Configuración",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa",
        ).pack(anchor="w", pady=(0, 4))

        cfg_frame = ctk.CTkFrame(right, fg_color="transparent")
        cfg_frame.pack(anchor="w")
        cfg_frame.grid_columnconfigure((0, 1), weight=0)

        for i, (key, lbl) in enumerate(_CONFIG_LABELS):
            row, col = divmod(i, 2)
            cb = ctk.CTkCheckBox(
                cfg_frame, text=lbl, variable=self._config_vars[key],
                command=self._on_change,
                fg_color="#107C10", hover_color="#0d6a0d",
                font=ctk.CTkFont(size=11),
            )
            cb.grid(row=row, column=col, sticky="w", padx=(0, 20), pady=2)
            self._toggleable.append(cb)

        ctk.CTkButton(
            right, text="Editor de Configuración  →",
            command=self._open_config_editor,
            fg_color="#2d2d2d", hover_color="#3d3d3d",
            height=28, width=210, anchor="w",
        ).pack(anchor="w", pady=(8, 0))

    # ------------------------------------------------------------------ #
    # Private helpers                                                       #
    # ------------------------------------------------------------------ #

    def _fallback_logo(self, parent):
        logo = ctk.CTkFrame(parent, fg_color="#2a2a2a", corner_radius=8,
                            width=200, height=200)
        logo.pack(pady=(20, 8))
        logo.pack_propagate(False)
        ctk.CTkLabel(
            logo, text="360",
            font=ctk.CTkFont(size=52, weight="bold"), text_color="#107C10",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _update_method_ui(self):
        method = self._method_var.get()
        info   = CATALOG.get(method, {}).get("desc", "")
        self._method_info.configure(text=info)
        if method == "badupdate":
            self._patch_note.pack(anchor="w", pady=(2, 0))
        else:
            self._patch_note.pack_forget()

    def _on_method_change(self):
        self._update_method_ui()
        self._on_change()

    def _on_change(self):
        if self._on_change_cb:
            self._on_change_cb()

    def _on_profile_btn_click(self, key: str):
        if self._profile_callback:
            self._profile_callback(key)

    def _open_config_editor(self):
        win = ctk.CTkToplevel(self)
        win.title("Editor de Configuración — launch.ini")
        win.geometry("500x420")
        win.resizable(True, True)
        win.grab_set()

        ctk.CTkLabel(
            win, text="launch.ini",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(12, 4))

        editor = ctk.CTkTextbox(
            win, font=ctk.CTkFont(family="Courier", size=11), height=310,
        )
        editor.pack(fill="both", expand=True, padx=12, pady=4)
        editor.insert("1.0", self._custom_launch_ini or LAUNCH_INI_CONTENT)

        def _save():
            self._custom_launch_ini = editor.get("1.0", "end")
            win.destroy()

        ctk.CTkButton(
            win, text="Guardar y cerrar", command=_save,
            fg_color="#107C10", hover_color="#0d6a0d",
        ).pack(pady=8)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def set_profile_callback(self, cb):
        self._profile_callback = cb

    def set_change_callback(self, cb):
        self._on_change_cb = cb

    def set_active_profile(self, key):
        self._active_profile_key = key
        for pkey, (btn, base_c, act_c, base_b, act_b) in self._profile_btns.items():
            if pkey == key:
                btn.configure(fg_color=act_c, border_color=act_b, border_width=2)
            else:
                btn.configure(fg_color=base_c, border_color=base_b, border_width=1)
        if key is None:
            self._custom_lbl.pack(anchor="w", pady=(2, 0), after=self._btn_row)
        else:
            self._custom_lbl.pack_forget()

    def set_selections(self, opts: dict):
        if "method" in opts:
            self._method_var.set(opts["method"])
            self._update_method_ui()
        if "patch" in opts:
            self._patch_var.set(opts["patch"])
        for k, var in self._config_vars.items():
            if k in opts:
                var.set(opts[k])

    def get_options(self) -> dict:
        opts = {
            "method": self._method_var.get(),
            "patch":  self._patch_var.get(),
            "custom_launch_ini": self._custom_launch_ini,
        }
        opts.update({k: v.get() for k, v in self._config_vars.items()})
        return opts

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for w in self._toggleable:
            w.configure(state=state)
