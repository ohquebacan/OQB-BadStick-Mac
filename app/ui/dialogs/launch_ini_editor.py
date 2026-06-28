"""
LaunchIniEditor — modal .ini editor with 3 tabs: Launch.ini, JRPC.ini, XBDM.ini.
Includes quick presets, inline tips panel, and save-time validation.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.core.config import LAUNCH_INI_CONTENT


# ── Per-tab defaults ──────────────────────────────────────────────────────── #

_DEFAULT_JRPC_INI = r""""Settings"
{
    "KV Stealer Protection" "False"
}
"Plugins"
{
    "plugin1"   "Hdd:\Insert plugin 1 here"
    "plugin2"   "Hdd:\Insert plugin 2 here"
    "plugin3"   "Hdd:\Insert plugin 3 here"
}
"""

_DEFAULT_XBDM_INI = 'dbgname name="Bad Update Console"\nsetcolor name="nosidecar"\n'

_TABS = [
    ("Launch.ini", LAUNCH_INI_CONTENT, "launch.ini"),
    ("JRPC.ini",   _DEFAULT_JRPC_INI,  "JRPC.ini"),
    ("XBDM.ini",   _DEFAULT_XBDM_INI,  "XBDM.ini"),
]

# ── Preset patches ─────────────────────────────────────────────────────────── #

_PRESETS = {
    "seguro": {
        "liveblock":  "true",
        "livestrong": "true",
        "fakelive":   "true",
        "autofake":   "true",
        "nohealth":   "true",
        "nooobe":     "true",
    },
    "casual": {
        "Default":    r"Usb:\Dashboards\Aurora\Aurora.xex",
        "plugin1":    r"Usb:\Plugins\xbPirate\xbPirate.xex",
        "plugin2":    r"Usb:\Plugins\ftpsrv\ftpsrv.xex",
        "ftpserv":    "true",
        "liveblock":  "true",
        "livestrong": "true",
    },
    "avanzado": {
        "Default":    r"Usb:\Dashboards\Aurora\Aurora.xex",
        "plugin1":    r"Usb:\Plugins\xbdm.xex",
        "plugin2":    r"Usb:\Plugins\JRPC2.xex",
        "plugin3":    r"Usb:\Plugins\xbPirate\xbPirate.xex",
        "liveblock":  "true",
        "livestrong": "true",
        "fakelive":   "true",
        "autofake":   "true",
    },
}

_PRESET_LABELS = {
    "seguro":   "Seguro (anti-ban)",
    "casual":   "Casual (jugar)",
    "avanzado": "Avanzado (dev)",
}

# ── Tips content ──────────────────────────────────────────────────────────── #

_TIPS_TEXT = """\
OPTIMIZACIONES RECOMENDADAS PARA LAUNCH.INI
══════════════════════════════════════════════

📺  Default Dashboard:
    Default = Usb:\\Dashboards\\Aurora\\Aurora.xex
    → Cambia "Aurora" por tu dashboard favorito
      (Freestyle, Emerald, IngeniouX, Viper360…)

🛡️  Plugin Protection (Anti-ban):
    plugin1 = Usb:\\Plugins\\xbPirate\\xbPirate.xex
    → Oculta tu KV en Xbox Live (evita bans por spoofing)

📡  FTP Access (desde tu PC):
    plugin2 = Usb:\\Plugins\\ftpsrv\\ftpsrv.xex
    ftpserv = true
    ftpport = 21
    → Explora el HDD de la Xbox desde FileZilla

🔒  Máxima Protección Anti-ban:
    liveblock  = true  ✓  mantener siempre así
    livestrong = true  ✓  mantener siempre así
    fakelive   = true  ←  activar si usas stealth servers
    autofake   = true  ←  activar junto con fakelive

🎮  Presets rápidos:
    Usa los botones de presets para aplicar
    configuraciones prearmadas con un solo click.
    Solo modifican las claves del preset —
    el resto del archivo queda intacto.
"""

# ── Editor theming ────────────────────────────────────────────────────────── #

_EDITOR_BG   = "#1e1e1e"
_LINENUM_BG  = "#252525"
_LINENUM_FG  = "#555555"
_EDITOR_FG   = "#d4d4d4"
_FONT        = ("Courier New", 11)


# ── INI helpers ───────────────────────────────────────────────────────────── #

def _parse_ini_kv(content: str) -> dict:
    """Return {lowercase_key: value} for all non-comment key=value lines."""
    kv = {}
    for line in content.splitlines():
        s = line.strip()
        if s.startswith(";") or s.startswith("[") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        kv[k.strip().lower()] = v.strip()
    return kv


def _apply_ini_patch(content: str, patch: dict) -> str:
    """Replace matching key = value lines; keys not found are left unchanged."""
    lines = content.splitlines()
    result = []
    for line in lines:
        s = line.strip()
        if s.startswith(";") or s.startswith("[") or "=" not in s:
            result.append(line)
            continue
        k, _, _ = s.partition("=")
        key = k.strip()
        if key in patch:
            result.append(f"{key} = {patch[key]}")
        else:
            result.append(line)
    return "\n".join(result)


# ══════════════════════════════════════════════════════════════════════════════
# Editor window
# ══════════════════════════════════════════════════════════════════════════════

class LaunchIniEditor(ctk.CTkToplevel):
    def __init__(self, master, get_usb_path=None, device_manager=None):
        super().__init__(master)
        self._get_usb_path = get_usb_path
        if device_manager is not None:
            self._device_manager = device_manager
        else:
            from app.core.device_manager import DeviceManager as _DM
            self._device_manager = _DM()

        self.title("Editor de archivos .ini — OQB BadStick Mac")
        self.geometry("880x640")
        self.minsize(680, 460)
        self.resizable(True, True)
        self.configure(fg_color="#1a1a1a")

        self._editors = {}
        self._tabview = None

        self._build()

        self.grab_set()
        self.focus_set()
        self.lift()

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def _build(self):
        # ── Tab view ──────────────────────────────────────────────────── #
        self._tabview = ctk.CTkTabview(
            self,
            fg_color="#1a1a1a",
            segmented_button_fg_color="#2d2d2d",
            segmented_button_selected_color="#107C10",
            segmented_button_selected_hover_color="#0d6b0d",
            segmented_button_unselected_color="#2d2d2d",
            segmented_button_unselected_hover_color="#3d3d3d",
            text_color="#cccccc",
        )
        self._tabview.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        for label, default, filename in _TABS:
            self._tabview.add(label)
            editor, line_nums = self._make_editor(self._tabview.tab(label), label)
            self._editors[label] = {
                "editor":    editor,
                "line_nums": line_nums,
                "default":   default,
                "filename":  filename,
            }
            editor.insert("1.0", default)
            self._refresh_line_nums(label)

        # ── Presets bar ───────────────────────────────────────────────── #
        presets_bar = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=0, height=42)
        presets_bar.pack(fill="x", side="bottom")
        presets_bar.pack_propagate(False)

        ctk.CTkLabel(
            presets_bar, text="Presets rápidos:",
            font=ctk.CTkFont(size=11), text_color="#666666",
        ).pack(side="left", padx=(12, 8), pady=12)

        for label, key in [
            ("🛡  Seguro (anti-ban)", "seguro"),
            ("🎮  Casual (jugar)",    "casual"),
            ("🔧  Avanzado (dev)",    "avanzado"),
        ]:
            ctk.CTkButton(
                presets_bar, text=label,
                command=lambda k=key: self._apply_preset(k),
                fg_color="#2a2a2a", hover_color="#3a3a3a",
                width=152, height=26,
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=(0, 6), pady=8)

        # ── Main button bar ───────────────────────────────────────────── #
        bar = ctk.CTkFrame(self, fg_color="#222222", corner_radius=0, height=48)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(side="left", padx=10, pady=9)

        for text, fg, cmd in [
            ("💾  Guardar",       "#107C10", self._save),
            ("🗑  Limpiar",        "#2d2d2d", self._clear),
            ("📂  Abrir",          "#2d2d2d", self._open_file),
            ("🔄  Recargar USB",  "#1a3a1a", self._reload_from_usb),
            ("📄  New Launch.ini", "#2d2d2d", self._new),
            ("💡  Consejos",       "#2d2d2d", self._show_tips),
            ("↩  Volver",          "#3a3a3a", self.destroy),
        ]:
            ctk.CTkButton(
                inner, text=text, command=cmd,
                fg_color=fg,
                hover_color=(
                    "#0d6b0d" if fg == "#107C10"
                    else "#2a5a2a" if fg == "#1a3a1a"
                    else "#4a4a4a"
                ),
                width=120, height=30,
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=(0, 5))

        self.after(100, self._auto_load_from_usb)

    # ------------------------------------------------------------------ #
    # Editor factory                                                       #
    # ------------------------------------------------------------------ #

    def _make_editor(self, parent, tab_label: str):
        """Line-numbered text editor built from plain tk widgets."""
        outer = ctk.CTkFrame(parent, fg_color=_EDITOR_BG, corner_radius=6)
        outer.pack(fill="both", expand=True, padx=4, pady=4)

        vbar = tk.Scrollbar(outer, orient="vertical",
                             bg="#3a3a3a", troughcolor="#1e1e1e",
                             activebackground="#555555", width=12)
        vbar.pack(side="right", fill="y")

        hbar = tk.Scrollbar(outer, orient="horizontal",
                             bg="#3a3a3a", troughcolor="#1e1e1e",
                             activebackground="#555555")
        hbar.pack(side="bottom", fill="x")

        line_nums = tk.Text(
            outer, width=4, padx=6, pady=4,
            state="disabled",
            bg=_LINENUM_BG, fg=_LINENUM_FG,
            font=_FONT, bd=0, relief="flat",
            cursor="arrow", takefocus=0,
        )
        line_nums.pack(side="left", fill="y")

        editor = tk.Text(
            outer, wrap="none", padx=6, pady=4,
            bg=_EDITOR_BG, fg=_EDITOR_FG,
            insertbackground="#aeafad",
            font=_FONT, bd=0, relief="flat",
            undo=True,
            selectbackground="#264f78",
            selectforeground="#d4d4d4",
            xscrollcommand=hbar.set,
        )
        editor.pack(side="left", fill="both", expand=True)

        hbar.configure(command=editor.xview)

        def _vsync(*args):
            editor.yview(*args)
            line_nums.yview(*args)

        vbar.configure(command=_vsync)

        def _on_yscroll(first, last):
            vbar.set(first, last)
            line_nums.yview_moveto(first)

        editor.configure(yscrollcommand=_on_yscroll)
        editor.bind("<KeyRelease>",    lambda e, t=tab_label: self._refresh_line_nums(t))
        editor.bind("<ButtonRelease>", lambda e, t=tab_label: self._refresh_line_nums(t))

        return editor, line_nums

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _current_tab(self) -> str:
        return self._tabview.get()

    def _refresh_line_nums(self, tab_label: str):
        d         = self._editors[tab_label]
        editor    = d["editor"]
        line_nums = d["line_nums"]
        num  = int(editor.index("end-1c").split(".")[0])
        text = "\n".join(str(i) for i in range(1, num + 1))
        line_nums.configure(state="normal")
        line_nums.delete("1.0", "end")
        line_nums.insert("1.0", text)
        line_nums.configure(state="disabled")

    # ------------------------------------------------------------------ #
    # USB path resolver                                                    #
    # ------------------------------------------------------------------ #

    def _resolve_usb_path(self) -> str | None:
        """Return the active USB mount point, trying multiple sources."""
        # Fast path: callback set by main_window after install
        if callable(self._get_usb_path):
            path = self._get_usb_path()
            if path:
                return path
        # Fallback: live scan via device_manager
        try:
            devices = self._device_manager.list_usb_devices()
            if devices:
                return devices[0]["mount_point"]
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------ #
    # Save validation (Launch.ini only)                                    #
    # ------------------------------------------------------------------ #

    def _validate_before_save(self, content: str) -> bool:
        """Show warnings/errors about Launch.ini content. Returns False to abort."""
        kv = _parse_ini_kv(content)

        # RED — liveblock = false: dangerous, ask before saving
        if kv.get("liveblock", "true") == "false":
            ok = messagebox.askyesno(
                "⚠️  ¡Riesgo de ban!",
                "liveblock = false puede resultar en ban de Xbox Live.\n\n"
                "Se recomienda mantener  liveblock = true\n"
                "para bloquear el acceso de Microsoft a tu consola.\n\n"
                "¿Guardar de todas formas?",
                icon="warning",
                parent=self,
            )
            if not ok:
                return False

        # YELLOW — empty Default
        if kv.get("default", "") == "":
            messagebox.showwarning(
                "⚠️  Sin dashboard por defecto",
                "La clave Default está vacía en [Paths].\n"
                "La consola arrancará en el NXE original (dashboard de fábrica).\n\n"
                "Ejemplo:\n"
                r"  Default = Usb:\Dashboards\Aurora\Aurora.xex",
                parent=self,
            )

        # INFO — no plugins
        plugins = [kv.get(f"plugin{i}", "") for i in range(1, 4)]
        if all(p == "" for p in plugins):
            messagebox.showinfo(
                "ℹ️  Sin plugins",
                "plugin1, plugin2 y plugin3 están vacíos en [Plugins].\n\n"
                "Puedes configurarlos después de instalar los plugins\n"
                "en el USB desde las tabs de la app principal.",
                parent=self,
            )

        # WARN — duplicated plugin paths
        plugin_vals = [
            kv.get(f"plugin{i}", "").strip()
            for i in range(1, 6)
        ]
        non_empty = [v for v in plugin_vals if v]
        if len(non_empty) != len(set(non_empty)):
            from collections import Counter
            dupes = [v for v, c in Counter(non_empty).items() if c > 1]
            ok = messagebox.askyesno(
                "⚠️  Plugins duplicados",
                "Hay plugins repetidos en los slots:\n\n"
                + "\n".join(f"  • {d}" for d in dupes)
                + "\n\n¿Guardar de todas formas?",
                icon="warning",
                parent=self,
            )
            if not ok:
                return False

        return True

    # ------------------------------------------------------------------ #
    # Button actions                                                       #
    # ------------------------------------------------------------------ #

    def _save(self):
        usb_path = self._resolve_usb_path()
        if not usb_path:
            messagebox.showerror(
                "Sin USB",
                "No hay USB montado.\nConecta un USB e intenta de nuevo.",
                parent=self,
            )
            return

        tab     = self._current_tab()
        d       = self._editors[tab]
        fname   = d["filename"]
        dest    = os.path.join(usb_path, fname)
        content = d["editor"].get("1.0", "end-1c")

        if tab == "Launch.ini" and not self._validate_before_save(content):
            return

        try:
            with open(dest, "w", newline="\r\n", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Guardado", f"✅ {fname} guardado en USB", parent=self)
        except Exception as exc:
            messagebox.showerror("Error al guardar", str(exc), parent=self)

    def _clear(self):
        tab   = self._current_tab()
        fname = self._editors[tab]["filename"]
        if not messagebox.askyesno(
            "¿Limpiar?", f"¿Eliminar todo el contenido de {fname}?", parent=self
        ):
            return
        self._editors[tab]["editor"].delete("1.0", "end")
        self._refresh_line_nums(tab)

    def _open_file(self):
        tab   = self._current_tab()
        d     = self._editors[tab]
        fname = d["filename"]
        path  = filedialog.askopenfilename(
            title=f"Abrir {fname}",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
            parent=self,
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as exc:
            messagebox.showerror("Error al abrir", str(exc), parent=self)
            return
        d["editor"].delete("1.0", "end")
        d["editor"].insert("1.0", content)
        self._refresh_line_nums(tab)

    def _new(self):
        tab    = self._current_tab()
        d      = self._editors[tab]
        editor = d["editor"]
        fname  = d["filename"]
        if editor.get("1.0", "end-1c").strip():
            if not messagebox.askyesno(
                "¿Reemplazar?",
                f"El editor de {fname} tiene contenido.\n"
                f"¿Reemplazar con el template por defecto?",
                parent=self,
            ):
                return
        editor.delete("1.0", "end")
        editor.insert("1.0", d["default"])
        self._refresh_line_nums(tab)

    def _show_tips(self):
        win = ctk.CTkToplevel(self)
        win.title("💡 Consejos — launch.ini")
        win.geometry("540x460")
        win.resizable(False, False)
        win.configure(fg_color="#1a1a1a")
        win.grab_set()
        win.focus_set()
        win.lift()

        txt = ctk.CTkTextbox(
            win, wrap="word",
            fg_color="#1e1e1e", text_color="#cccccc",
            font=ctk.CTkFont(family="Courier New", size=12),
            border_width=0,
        )
        txt.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        txt.insert("1.0", _TIPS_TEXT)
        txt.configure(state="disabled")

        ctk.CTkButton(
            win, text="Cerrar", command=win.destroy,
            fg_color="#2d2d2d", hover_color="#4a4a4a",
            width=100, height=30,
        ).pack(pady=(0, 10))

    def _apply_preset(self, key: str):
        # Always target the Launch.ini tab
        self._tabview.set("Launch.ini")
        d      = self._editors["Launch.ini"]
        editor = d["editor"]
        patch  = _PRESETS[key]
        label  = _PRESET_LABELS[key]

        current = editor.get("1.0", "end-1c")
        if current.strip():
            if not messagebox.askyesno(
                f"Preset: {label}",
                f"¿Aplicar el preset '{label}'?\n\n"
                "Los plugin slots se limpiarán primero para evitar\n"
                "duplicados, luego se aplica el preset.",
                parent=self,
            ):
                return

        # Clear all plugin slots first, then overlay the preset
        clean_patch = {f"plugin{i}": "" for i in range(1, 6)}
        clean_patch.update(patch)

        new_content = _apply_ini_patch(current, clean_patch)
        editor.delete("1.0", "end")
        editor.insert("1.0", new_content)
        self._refresh_line_nums("Launch.ini")

    # ------------------------------------------------------------------ #
    # USB auto-load / reload                                               #
    # ------------------------------------------------------------------ #

    def _auto_load_from_usb(self):
        """Si hay un launch.ini en el USB, cargarlo automáticamente."""
        usb_path = self._resolve_usb_path()
        if not usb_path:
            return
        ini_path = os.path.join(usb_path, "launch.ini")
        if not os.path.exists(ini_path):
            return
        try:
            with open(ini_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            d = self._editors["Launch.ini"]
            d["editor"].delete("1.0", "end")
            d["editor"].insert("1.0", content)
            self._refresh_line_nums("Launch.ini")
            self.title("Editor — launch.ini cargado desde USB  ✓")
        except Exception:
            pass

    def _reload_from_usb(self):
        """Recargar el launch.ini actual del USB, descartando cambios no guardados."""
        usb_path = self._resolve_usb_path()
        if not usb_path:
            messagebox.showerror("Sin USB",
                "No hay USB montado.", parent=self)
            return
        ini_path = os.path.join(usb_path, "launch.ini")
        if not os.path.exists(ini_path):
            messagebox.showwarning("No encontrado",
                "No hay launch.ini en el USB todavía.\n"
                "Generá uno primero con '📄 Solo launch.ini'.",
                parent=self)
            return
        d = self._editors["Launch.ini"]
        if d["editor"].get("1.0", "end-1c").strip():
            if not messagebox.askyesno("¿Recargar?",
                "¿Reemplazar el contenido actual con el launch.ini del USB?",
                parent=self):
                return
        try:
            with open(ini_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            d["editor"].delete("1.0", "end")
            d["editor"].insert("1.0", content)
            self._refresh_line_nums("Launch.ini")
            self.title("Editor — launch.ini cargado desde USB  ✓")
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
