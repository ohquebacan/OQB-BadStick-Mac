import contextlib
import os
import platform
import subprocess
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from app.core.catalog import CATALOG, METHOD_DL_MAP
from app.ui.quick_profiles import HARDMOD_KEYS
from app.core.config import (
    APP_NAME, APP_VERSION, GITHUB_REPO, DISCORD_URL, TEMP_DIR,
)
from app.core.device_manager import DeviceManager
from app.core.downloader import Downloader
from app.core.installer import Installer
from app.ui.tabs.install_tab import InstallTab
from app.ui.tabs.dashboards_tab import DashboardsTab
from app.ui.tabs.homebrew_tab import HomebrewTab
from app.ui.tabs.stealth_tab import StealthTab
from app.ui.tabs.plugins_tab import PluginsTab
from app.ui.tabs.settings_tab import SettingsTab
from app.ui.quick_profiles import QuickProfiles

_ASSETS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")
)


# ====================================================================== #
# Floating log window                                                     #
# ====================================================================== #

_LOG_COLORS = {
    "info":    "#cccccc",
    "success": "#4CAF50",
    "error":   "#EF5350",
    "warning": "#FFA726",
    "ts":      "#555555",
}


class LogWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"Log — {APP_NAME}")
        self.geometry("650x420")
        self._build()

    def _build(self):
        self._tb = ctk.CTkTextbox(
            self, fg_color="#0d0d0d",
            font=ctk.CTkFont(family="Courier", size=11),
            state="disabled", wrap="word",
        )
        self._tb.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        for tag, color in _LOG_COLORS.items():
            self._tb._textbox.tag_configure(tag, foreground=color)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkButton(
            row, text="Copiar", command=self._copy,
            fg_color="#2d2d2d", hover_color="#3d3d3d", width=80, height=26,
        ).pack(side="left")
        ctk.CTkButton(
            row, text="Limpiar", command=self._clear,
            fg_color="#2d2d2d", hover_color="#3d3d3d", width=80, height=26,
        ).pack(side="left", padx=6)

    def log(self, message: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self._tb.configure(state="normal")
        self._tb._textbox.insert("end", f"[{ts}] ", "ts")
        self._tb._textbox.insert("end", f"{message}\n", level)
        self._tb._textbox.see("end")
        self._tb.configure(state="disabled")

    def _copy(self):
        content = self._tb._textbox.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)

    def _clear(self):
        self._tb.configure(state="normal")
        self._tb.delete("1.0", "end")
        self._tb.configure(state="disabled")


# ====================================================================== #
# Main window                                                             #
# ====================================================================== #

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("980x760")
        self.resizable(False, False)

        self._system = platform.system()
        self._device_manager = DeviceManager()
        self.device_manager  = self._device_manager   # public alias for child widgets
        self._downloader = Downloader()
        self._installer = Installer()
        self._devices = []
        self._last_usb_path = None
        self._log_window = None
        self._log_history = []  # (message, level) tuples for replay

        self._build_ui()
        self._build_menu()
        self._wire_profiles()
        self._on_startup()

    # ------------------------------------------------------------------ #
    # Build UI                                                             #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        icon_path = os.path.join(_ASSETS, "icon.png")

        # ── Bottom bar (always visible) ────────────────────────────────
        bottom = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0, height=105)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        # Row 1: USB dropdown + action buttons
        row1 = ctk.CTkFrame(bottom, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(8, 2))

        self._usb_var = ctk.StringVar(value="Sin dispositivos USB detectados")
        self._usb_dd = ctk.CTkOptionMenu(
            row1, variable=self._usb_var,
            values=["Sin dispositivos USB detectados"],
            fg_color="#2d2d2d", button_color="#107C10",
            button_hover_color="#0d6a0d",
            dynamic_resizing=False, width=390,
        )
        self._usb_dd.pack(side="left")

        self._reset_btn = ctk.CTkButton(
            row1, text="Reset Drives", command=self._refresh_devices,
            fg_color="#2d2d2d", hover_color="#3d3d3d", width=100, height=32,
        )
        self._reset_btn.pack(side="left", padx=(8, 0))

        self._log_btn = ctk.CTkButton(
            row1, text="Ver Log", command=self._toggle_log,
            fg_color="#2d2d2d", hover_color="#3d3d3d", width=80, height=32,
        )
        self._log_btn.pack(side="left", padx=(8, 0))

        self._start_btn = ctk.CTkButton(
            row1, text="  START  ",
            command=self._start_install,
            fg_color="#107C10", hover_color="#0d6a0d",
            font=ctk.CTkFont(size=15, weight="bold"),
            width=110, height=38,
        )
        self._start_btn.pack(side="right")

        # Row 2: progress + status
        row2 = ctk.CTkFrame(bottom, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(0, 6))

        self._progress = ctk.CTkProgressBar(
            row2, fg_color="#252525", progress_color="#107C10", height=6,
        )
        self._progress.pack(fill="x", pady=(0, 3))
        self._progress.set(0)

        status_row = ctk.CTkFrame(row2, fg_color="transparent")
        status_row.pack(fill="x")

        self._status_lbl = ctk.CTkLabel(
            status_row, text="Status: Idle",
            font=ctk.CTkFont(size=10), text_color="#555555", anchor="w",
        )
        self._status_lbl.pack(side="left")

        self._speed_lbl = ctk.CTkLabel(
            status_row, text="",
            font=ctk.CTkFont(size=10), text_color="#555555", anchor="e",
        )
        self._speed_lbl.pack(side="right")

        # ── CTkTabview ─────────────────────────────────────────────────
        self._tabs = ctk.CTkTabview(
            self,
            fg_color="#1a1a1a",
            segmented_button_fg_color="#111111",
            segmented_button_selected_color="#107C10",
            segmented_button_selected_hover_color="#0d6a0d",
            segmented_button_unselected_color="#111111",
            segmented_button_unselected_hover_color="#252525",
            text_color="#aaaaaa",
            text_color_disabled="#444444",
            command=self._on_tab_changed,
        )
        self._tabs.pack(fill="both", expand=True)

        tab_names = [
            "Instalar",
            "Dashboards / Launchers",
            "Homebrew",
            "Stealth Servers",
            "Plugins / Otros",
            "Configuración",
        ]
        for name in tab_names:
            self._tabs.add(name)

        self.install_tab = InstallTab(
            self._tabs.tab("Instalar"), icon_path=icon_path
        )
        self.install_tab.pack(fill="both", expand=True)

        self.dashboards_tab = DashboardsTab(self._tabs.tab("Dashboards / Launchers"))
        self.dashboards_tab.pack(fill="both", expand=True)

        self.homebrew_tab = HomebrewTab(self._tabs.tab("Homebrew"))
        self.homebrew_tab.pack(fill="both", expand=True)

        self.stealth_tab = StealthTab(self._tabs.tab("Stealth Servers"))
        self.stealth_tab.pack(fill="both", expand=True)

        self.plugins_tab = PluginsTab(self._tabs.tab("Plugins / Otros"))
        self.plugins_tab.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(
            self._tabs.tab("Configuración"),
            icon_path=icon_path,
            get_usb_path=lambda: self._last_usb_path,
        )
        self.settings_tab.pack(fill="both", expand=True)

        self.after(100, self.update_idletasks)

    def _on_tab_changed(self):
        self.update_idletasks()
        self.update()

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.configure(menu=menubar)

        app_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=APP_NAME, menu=app_menu)
        app_menu.add_command(label="Acerca de…", command=self._show_about)
        app_menu.add_separator()
        app_menu.add_command(label="Salir", command=self.quit)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Ver Log", command=self._toggle_log)
        file_menu.add_command(
            label="Abrir USB en Finder",
            command=lambda: self._open_usb(),
        )
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(
            label="Documentación",
            command=lambda: webbrowser.open(f"https://github.com/{GITHUB_REPO}"),
        )
        help_menu.add_command(
            label="Reportar problema",
            command=lambda: webbrowser.open(f"https://github.com/{GITHUB_REPO}/issues"),
        )

    # ------------------------------------------------------------------ #
    # Startup & devices                                                    #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Quick profiles                                                       #
    # ------------------------------------------------------------------ #

    def _wire_profiles(self):
        self._quick_profiles = QuickProfiles(self)
        for tab in (
            self.install_tab, self.dashboards_tab, self.homebrew_tab,
            self.stealth_tab, self.plugins_tab,
        ):
            tab.set_change_callback(self._on_manual_change)
        self.install_tab.set_profile_callback(self._on_profile_select)
        self._quick_profiles.apply("recommended")

    def _on_profile_select(self, profile: str):
        self._quick_profiles.apply(profile)

    def _on_manual_change(self):
        self.install_tab.set_active_profile(None)

    # ------------------------------------------------------------------ #

    def _on_startup(self):
        self._log("OQB BadStick Mac iniciado", "success")
        self._log("DESCONECTA TU XBOX 360 DE INTERNET antes de usar este USB", "warning")
        if self._system == "Windows":
            self._log("Windows detectado — solo macOS / Linux soportados", "error")
            self._start_btn.configure(state="disabled")
        self._refresh_devices()

    def _refresh_devices(self):
        devices = self._device_manager.list_usb_devices()
        self._devices = devices
        if devices:
            values = [self._device_label(d) for d in devices]
            self._usb_dd.configure(values=values)
            self._usb_var.set(values[0])
            self._log(f"{len(devices)} dispositivo(s) USB detectado(s)", "success")
        else:
            self._usb_dd.configure(values=["Sin dispositivos USB detectados"])
            self._usb_var.set("Sin dispositivos USB detectados")
            self._log("Sin dispositivos USB detectados")

    def _get_selected_device(self) -> dict:
        if not self._devices:
            return None
        sel = self._usb_var.get()
        for d in self._devices:
            if self._device_label(d) == sel:
                return d
        return self._devices[0] if self._devices else None

    def _device_label(self, d: dict) -> str:
        return f"{d['name']} ({d['size']}) — /dev/{d['identifier']}"

    # ------------------------------------------------------------------ #
    # Log                                                                  #
    # ------------------------------------------------------------------ #

    def _log(self, message: str, level: str = "info"):
        self._log_history.append((message, level))
        if self._log_window and self._log_window.winfo_exists():
            self._log_window.log(message, level)

    def _toggle_log(self):
        if self._log_window and self._log_window.winfo_exists():
            self._log_window.focus()
            return
        self._log_window = LogWindow(self)
        for msg, lvl in self._log_history:
            self._log_window.log(msg, lvl)

    # ------------------------------------------------------------------ #
    # Status & progress helpers                                            #
    # ------------------------------------------------------------------ #

    def _set_status(self, text: str, progress: float = None):
        self._status_lbl.configure(text=f"Status: {text}")
        if progress is not None:
            self._progress.set(max(0.0, min(1.0, progress)))

    def _set_speed(self, bps: float, dl: int = 0, total: int = 0):
        if bps <= 0:
            self._speed_lbl.configure(text="")
            return

        def _fmt_speed(b):
            if b >= 1_048_576:
                return f"{b/1_048_576:.1f} MB/s"
            if b >= 1024:
                return f"{b/1024:.0f} KB/s"
            return f"{b:.0f} B/s"

        def _fmt_bytes(n):
            if n >= 1_048_576:
                return f"{n/1_048_576:.1f} MB"
            if n >= 1024:
                return f"{n/1024:.0f} KB"
            return f"{n} B"

        if total > 0:
            self._speed_lbl.configure(
                text=f"{_fmt_bytes(dl)} / {_fmt_bytes(total)}  {_fmt_speed(bps)}"
            )
        else:
            self._speed_lbl.configure(text=_fmt_speed(bps))

    def _set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._start_btn.configure(state=state)
        self._reset_btn.configure(state=state)
        self._usb_dd.configure(state=state)
        for tab in (
            self.install_tab, self.dashboards_tab, self.homebrew_tab,
            self.stealth_tab, self.plugins_tab,
        ):
            tab.set_enabled(enabled)

    # ------------------------------------------------------------------ #
    # Install flow                                                         #
    # ------------------------------------------------------------------ #

    def _show_hardmod_warning(self, item_names: list) -> bool:
        """Show modal warning for hardmod-only items. Returns True to keep, False to remove."""
        result = [True]
        win = ctk.CTkToplevel(self)
        win.title("⚠️ Hardmod-Only Options Detected")
        win.geometry("480x320")
        win.resizable(False, False)
        win.grab_set()

        ctk.CTkLabel(
            win,
            text="⚠️  Hardmod-Only Options Detected",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ff6b6b",
        ).pack(pady=(20, 8))

        bullet_list = "\n".join(f"  •  {name}" for name in item_names)
        ctk.CTkLabel(
            win,
            text=(
                "The following selected options only work on hardware-modded\n"
                "consoles (RGH/JTAG) and may cause freezes on softmod\n"
                "(ABadAvatar/BadUpdate) consoles:\n\n"
                f"{bullet_list}\n\n"
                "Are you sure you want to include these?\n"
                'Select NO to remove them automatically.'
            ),
            font=ctk.CTkFont(size=11),
            text_color="#cccccc",
            justify="left",
        ).pack(padx=24, pady=(0, 16))

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack()

        def _keep():
            result[0] = True
            win.destroy()

        def _remove():
            result[0] = False
            win.destroy()

        ctk.CTkButton(
            btn_row, text="Yes, I have RGH/JTAG",
            command=_keep,
            fg_color="#1a3a5c", hover_color="#2a4a6c",
            width=180,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="No, remove them",
            command=_remove,
            fg_color="#3a1010", hover_color="#5a1818",
            width=160,
        ).pack(side="left")

        self.wait_window(win)
        return result[0]

    def _start_install(self):
        device = self._get_selected_device()
        if not device:
            messagebox.showerror("Error", "Selecciona un dispositivo USB primero.")
            return

        install_opts   = self.install_tab.get_options()
        dashboard_opts = self.dashboards_tab.get_options()
        homebrew_opts  = self.homebrew_tab.get_options()
        stealth_opts   = self.stealth_tab.get_options()
        plugin_opts    = self.plugins_tab.get_options()

        # ── Hardmod-only warning ──────────────────────────────────────
        selected_hardmod = {
            k: CATALOG[k]["name"]
            for opts in (homebrew_opts, plugin_opts)
            for k, v in opts.items()
            if v and k in HARDMOD_KEYS
        }
        hardmod_skipped_count = 0
        if selected_hardmod:
            keep = self._show_hardmod_warning(list(selected_hardmod.values()))
            if not keep:
                for k in selected_hardmod:
                    if k in homebrew_opts:
                        homebrew_opts[k] = False
                    if k in plugin_opts:
                        plugin_opts[k] = False
                self.homebrew_tab.set_selections(homebrew_opts)
                self.plugins_tab.set_selections(plugin_opts)
                hardmod_skipped_count = len(selected_hardmod)

        # Build confirmation summary
        method_key = install_opts["method"]
        patch_key  = install_opts["patch"]
        method_name = CATALOG.get(method_key, {}).get("name", method_key)
        patch_name  = CATALOG.get(patch_key, {}).get("name", patch_key)

        lines = [f"Dispositivo: {self._device_label(device)}\n"]
        if method_key == "badupdate":
            lines.append(f"✓ Método: {method_name}  (sin parche)")
        else:
            lines.append(f"✓ Método: {method_name} + {patch_name}")

        for tab_label, opts in [
            ("Dashboards", dashboard_opts),
            ("Homebrew",   homebrew_opts),
            ("Stealth",    stealth_opts),
            ("Plugins",    plugin_opts),
        ]:
            selected = [CATALOG[k]["name"] for k, v in opts.items() if v]
            if selected:
                lines.append(f"✓ {tab_label}: {', '.join(selected)}")

        if not install_opts.get("skip_format"):
            lines.append("\n⚠  SE FORMATEARÁ EL USB — se borrarán todos los datos")

        ok = messagebox.askyesno(
            "Confirmar instalación",
            "Se instalarán los siguientes componentes:\n\n" +
            "\n".join(lines) + "\n\n¿Continuar?",
        )
        if not ok:
            return

        self._set_controls_enabled(False)
        self._set_status("Iniciando…", 0.0)
        self._speed_lbl.configure(text="")
        self._log("=" * 50)
        self._log("Iniciando instalación…")

        all_opts = {
            "install":              install_opts,
            "dashboards":           dashboard_opts,
            "homebrew":             homebrew_opts,
            "stealth":              stealth_opts,
            "plugins":              plugin_opts,
            "hardmod_skipped":      hardmod_skipped_count,
        }
        threading.Thread(
            target=self._install_worker,
            args=(device, all_opts),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------ #
    # Install worker — background thread                                   #
    # ------------------------------------------------------------------ #

    def _install_worker(self, device: dict, all_opts: dict):
        def log(msg, level="info"):
            self.after(0, lambda m=msg, lv=level: self._log(m, lv))

        def prog(val, status=""):
            self.after(0, lambda v=val, s=status: self._set_status(s, v))

        install_opts = all_opts["install"]
        method_key   = install_opts["method"]
        patch_key    = install_opts["patch"]
        skip_format  = install_opts.get("skip_format", False)

        # Effective download key for the method
        dl_method_key = METHOD_DL_MAP.get(method_key, "abadavatar")

        try:
            # ── Step 1: Format / verify USB (0 → 15%) ────────────────
            if skip_format:
                log("⚡ Saltando formateo — actualizando USB existente")
                log("📁 Archivos existentes se mantienen")
                log("✏️  Solo items seleccionados se instalan/actualizan")
                prog(0.05, "Verificando USB…")
                usb_path = self._device_manager.get_mount_point(device["identifier"])
                if not usb_path or not os.path.exists(usb_path):
                    raise RuntimeError(
                        "USB no montado.\n"
                        "Conecta el USB formateado y desmarca '⚡ Actualizar USB existente'\n"
                        "si quieres hacer una instalación limpia."
                    )
                log(f"USB encontrado en {usb_path}", "success")
            else:
                log(f"Formateando /dev/{device['identifier']}…")
                prog(0.05, "Formateando…")
                success, usb_path = self._device_manager.format_device(
                    device["identifier"],
                    lambda line: self.after(0, lambda l=line: self._log(l)),
                )
                if not success:
                    raise RuntimeError("Error al formatear el dispositivo")
                if not usb_path:
                    usb_path = self._device_manager.get_mount_point(
                        device["identifier"]
                    )
                if not usb_path:
                    raise RuntimeError("No se pudo determinar el punto de montaje")
                log(f"USB formateado — montado en {usb_path}", "success")

            self._last_usb_path = usb_path
            prog(0.15, "Descargando…")

            # ── Step 2: Download (15 → 65%) ──────────────────────────
            # Core: exploit + payload
            keys_to_dl = [dl_method_key]
            if method_key != "badupdate":
                keys_to_dl.append(patch_key)
            # Auto-download any selected catalog item that has a download URL
            for _tab in ("dashboards", "homebrew", "stealth", "plugins"):
                for _k, _sel in all_opts[_tab].items():
                    if not _sel or _k in keys_to_dl:
                        continue
                    _e = CATALOG.get(_k, {})
                    if _e.get("type") == "auto" and (
                        _e.get("api_url") or _e.get("direct_url")
                    ):
                        keys_to_dl.append(_k)

            log(f"[DEBUG] keys_to_dl ({len(keys_to_dl)}): {keys_to_dl}")
            n = len(keys_to_dl)
            src_prog = [0.0] * n
            downloaded = {}

            def make_cb(idx, src_name):
                def cb(dl, total, speed):
                    src_prog[idx] = dl / total if total else 0
                    overall = 0.15 + (sum(src_prog) / n) * 0.50
                    self.after(
                        0,
                        lambda v=overall, s=f"Descargando {src_name}…",
                               dl_=dl, tot=total, spd=speed: (
                            self._set_status(s, v),
                            self._set_speed(spd, dl_, tot),
                        ),
                    )
                return cb

            os.makedirs(TEMP_DIR, exist_ok=True)
            with contextlib.nullcontext(TEMP_DIR) as tmp:
                for i, key in enumerate(keys_to_dl):
                    entry = CATALOG.get(key)
                    if not entry:
                        continue
                    name = entry["name"]

                    dest = os.path.join(tmp, f"{key}.zip")

                    # ── Cache hit: skip download ───────────────────────
                    if os.path.exists(dest) and os.path.getsize(dest) > 0:
                        size_mb = os.path.getsize(dest) / 1_048_576
                        log(f"⚡ {name} — usando caché local ({size_mb:.1f} MB)")
                        src_prog[i] = 1.0
                        downloaded[key] = dest
                        self.after(0, lambda: self._speed_lbl.configure(text=""))
                        continue

                    # ── Cache miss: resolve URL then download ──────────
                    log(f"⬇ {name} — descargando…")

                    url = None
                    if "direct_url" in entry:
                        url = entry["direct_url"]
                    elif "api_url" in entry:
                        api_url = entry["api_url"]
                        if "releases/download" in api_url:
                            url = api_url
                        else:
                            url = self._downloader.get_latest_release_url(
                                api_url, entry.get("asset_pattern", ".zip")
                            )
                            if not url:
                                url = entry.get("fallback_url")
                        if not url:
                            log("  → Sin URL disponible", "warning")

                    if not url:
                        log(f"  Saltando {name} — sin URL", "warning")
                        continue

                    ok = self._downloader.download_file(url, dest, make_cb(i, name))
                    if ok:
                        src_prog[i] = 1.0
                        size_mb = os.path.getsize(dest) / 1_048_576
                        self.after(0, lambda: self._speed_lbl.configure(text=""))
                        log(f"✅ {name} — descargado y guardado en caché ({size_mb:.1f} MB)",
                            "success")
                        downloaded[key] = dest
                        log(f"[DEBUG] ✓ {key} → {dest}")
                    else:
                        log(f"  Error descargando {name}", "error")
                        log(f"[DEBUG] ✗ {key} falló (url={url})")

                log(f"[DEBUG] downloaded keys: {list(downloaded.keys())}")

                if not os.path.exists(usb_path):
                    raise RuntimeError("USB desconectado durante la descarga")

                if dl_method_key not in downloaded:
                    raise RuntimeError(
                        f"No se pudo descargar el exploit ({dl_method_key}). "
                        "Verifica tu conexión a internet."
                    )

                prog(0.65, "Instalando exploit…")

                # ── Step 3: Install exploit + payload (65 → 85%) ─────
                installer_opts = {
                    "exploit": dl_method_key,
                    "payload": patch_key if method_key != "badupdate" else None,
                }

                log("Instalando archivos del exploit en USB…")
                success, checklist = self._installer.install(
                    downloaded, usb_path, installer_opts, log
                )
                if not success:
                    raise RuntimeError("Error durante la instalación de archivos")

                if not os.path.exists(usb_path):
                    raise RuntimeError("USB desconectado durante la instalación")

                prog(0.85, "Creando estructura…")

                # ── Step 4: Create folders + extras (85 → 100%) ──────
                log("Creando carpetas y archivos adicionales…")
                log(f"[DEBUG] Pasando {len(downloaded)} archivos a _generate_extras: {list(downloaded.keys())}")
                self._generate_extras(usb_path, all_opts, install_opts, log, downloaded)

                # ── Step 5: Filesystem verification ──────────────────
                v_results  = self._verify_installation(usb_path, all_opts, install_opts)
                v_total    = len(v_results)
                v_ok       = sum(1 for r in v_results if r["ok"])
                v_missing  = [r for r in v_results if not r["ok"]]

                # ── Done ─────────────────────────────────────────────
                prog(1.0, "¡Completado!")
                log("")
                log(f"✅  USB listo en {usb_path}", "success")
                log("")
                log("PASOS SIGUIENTES:")
                log("1. Desconecta tu Xbox 360 de Internet", "warning")
                log("2. Inserta el USB en tu Xbox 360")
                log("3. Enciende la consola — el exploit corre automático")
                log("4. Cuando veas la animación de éxito → presiona BACK")
                log("")
                log("⚠  Este exploit NO es permanente — debe repetirse en cada reinicio",
                    "warning")
                log("")

                # Manual download instructions
                manual_reminders = []
                for tab_key in ("dashboards", "homebrew", "stealth", "plugins"):
                    for k, sel in all_opts[tab_key].items():
                        if sel:
                            entry = CATALOG.get(k, {})
                            if entry.get("type") in ("manual",):
                                manual_reminders.append(entry)

                if manual_reminders:
                    log("── Descargas manuales requeridas ──", "warning")
                    for item in manual_reminders:
                        url = item.get("url", "")
                        if url:
                            log(f"  {item['name']:30}  {url}")
                        else:
                            log(f"  {item['name']:30}  (buscar en internet)")

                # Stealth-specific setup instructions
                selected_stealth = [
                    k for k, v in all_opts["stealth"].items() if v
                ]
                if selected_stealth:
                    log("")
                    log("── Instrucciones stealth ──", "warning")
                    for key in selected_stealth:
                        entry = CATALOG.get(key, {})
                        hint  = entry.get(
                            "log_hint",
                            f"Instala el cliente de {entry.get('name', key)} "
                            f"en USB/Plugins/{key}/ y configura en DashLaunch",
                        )
                        log(f"  {entry.get('name', key)}: {hint}")

                skipped_hm = all_opts.get("hardmod_skipped", 0)
                skip_suffix = (
                    f" ({skipped_hm} hardmod-only ignorado{'s' if skipped_hm > 1 else ''})"
                    if skipped_hm else ""
                )
                log("")
                log("── VERIFICACIÓN DE INSTALACIÓN ──")
                log(f"Seleccionados: {v_total} items{skip_suffix}")
                log(f"Instalados:    {v_ok} items")
                if not v_missing:
                    log(
                        f"✅ Todas las instalaciones completadas ({v_ok}/{v_total})",
                        "success",
                    )
                else:
                    log(
                        f"⚠️ ADVERTENCIA: Se esperaban {v_total} items "
                        f"pero solo se instalaron {v_ok}.",
                        "warning",
                    )
                    for r in v_missing:
                        log(f"  ❌ {r['label']}", "error")

                log("")
                log("── Checklist ──")
                for item in checklist:
                    sym = "✅" if item["ok"] else "⚠️ "
                    note = f"  ({item['note']})" if item.get("note") else ""
                    lvl = "success" if item["ok"] else "warning"
                    log(f"{sym}  {item['label']}{note}", lvl)

            def _on_success():
                self._set_controls_enabled(True)
                self._refresh_devices()
                self._toggle_log()

            self.after(0, _on_success)

        except Exception as exc:
            err = str(exc)

            def _on_error():
                self._log(f"ERROR: {err}", "error")
                self._set_status("Error", 0.0)
                self._speed_lbl.configure(text="")
                self._set_controls_enabled(True)
                messagebox.showerror(
                    "Error", f"Error durante la instalación:\n\n{err}"
                )

            self.after(0, _on_error)

    # ------------------------------------------------------------------ #
    # Installation verification                                           #
    # ------------------------------------------------------------------ #

    def _verify_installation(
        self, usb_path: str, all_opts: dict, install_opts: dict
    ) -> list:
        """
        Returns list of dicts: {label, path, ok, core}
        Checks every file/folder that should exist after a complete install.
        """
        results = []

        def chk(label, path, is_file=False, core=True):
            ok = os.path.isfile(path) if is_file else os.path.isdir(path)
            results.append({"label": label, "path": path, "ok": ok, "core": core})

        # ── Core: exploit ────────────────────────────────────────────────
        chk("BadUpdatePayload/",
            os.path.join(usb_path, "BadUpdatePayload"))
        chk("Content/",
            os.path.join(usb_path, "Content"))

        method_key = install_opts.get("method", "abadavatar")
        if method_key != "badupdate":
            chk("BadUpdatePayload/default.xex",
                os.path.join(usb_path, "BadUpdatePayload", "default.xex"),
                is_file=True)

        # ── Selected catalog items from all tabs ──────────────────────────
        for tab_key in ("dashboards", "homebrew", "stealth", "plugins"):
            for k, selected in all_opts[tab_key].items():
                if not selected:
                    continue
                entry = CATALOG.get(k)
                if not entry:
                    continue
                dest_rel = entry.get("dest", f"Homebrew/{k}")
                dest = os.path.join(usb_path, *dest_rel.split("/")) if dest_rel else usb_path
                chk(f"{entry['name']}  →  {dest_rel or 'raíz'}/", dest, core=False)

        return results

    # ------------------------------------------------------------------ #
    # Generate extras (placeholder folders + launch.ini)                  #
    # ------------------------------------------------------------------ #

    def _generate_extras(
        self,
        usb_path: str,
        all_opts: dict,
        install_opts: dict,
        log,
        downloaded: dict = None,
    ):
        # Base folders matching the real USB structure
        for folder in (
            "Dashboards", "Homebrew", "Plugins",
            "Stealth Networks", "Backwards Compatibility",
            "Customization", "FakeAnim", "FakeAnim Boot Animations",
        ):
            os.makedirs(os.path.join(usb_path, folder), exist_ok=True)

        # launch.ini — only writes if file doesn't already exist on USB
        Installer.generate_launch_ini(usb_path, log)

        # Install / stub all selected catalog items
        downloaded = downloaded or {}
        log(f"[DEBUG] _generate_extras recibió downloaded: {list(downloaded.keys())}")
        for tab_key in ("dashboards", "homebrew", "stealth", "plugins"):
            for k, selected in all_opts[tab_key].items():
                if not selected:
                    continue
                entry = CATALOG.get(k)
                if not entry:
                    continue

                item_type = entry.get("type", "manual")
                dest_rel  = entry.get("dest", f"Homebrew/{k}")

                zip_path = downloaded.get(k)
                log(f"[DEBUG]   {k}: type={item_type}, dest={dest_rel!r}, en downloaded={k in downloaded}, zip_exists={bool(zip_path and os.path.exists(zip_path))}")
                if item_type == "auto" and zip_path and os.path.exists(zip_path):
                    try:
                        Installer.extract_zip_to(zip_path, usb_path, dest_rel, log)
                        log(f"  ✓ {entry['name']} → {dest_rel or 'raíz'}/", "success")
                    except Exception as exc:
                        log(f"  ⚠ Error extrayendo {entry['name']}: {exc}", "error")
                        dest = os.path.join(usb_path, *dest_rel.split("/")) if dest_rel else usb_path
                        os.makedirs(dest, exist_ok=True)
                        self._write_leer_txt(dest, entry, dest_rel)
                        log(f"  ℹ️  {entry['name']} → carpeta creada (instalación manual)")
                else:
                    dest = os.path.join(usb_path, *dest_rel.split("/")) if dest_rel else usb_path
                    os.makedirs(dest, exist_ok=True)
                    self._write_leer_txt(dest, entry, dest_rel)
                    if item_type == "auto":
                        log(f"  ⚠ {entry['name']} no descargado → instrucciones manuales",
                            "warning")
                    else:
                        log(f"  ℹ️  {entry['name']} → carpeta creada (instalación manual)")

    def _extract_zip_to(self, zip_path: str, dest_dir: str, log):
        """Deprecated shim — delegates to Installer.extract_zip_to."""
        Installer.extract_zip_to(zip_path, dest_dir, "", log)

    def _write_leer_txt(self, dest: str, entry: dict, dest_rel: str):
        readme = os.path.join(dest, "LEER.txt")
        url  = entry.get("url", "")
        desc = entry.get("desc", "")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(f"{entry['name']}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Descripción:\n  {desc}\n\n")
            if url:
                f.write(f"Descarga:\n  {url}\n\n")
            f.write("Instrucciones:\n")
            f.write("  1. Descarga el archivo desde el link de arriba\n")
            f.write("  2. Extrae el contenido en esta misma carpeta\n")
            f.write(f"  3. Estructura final: {dest_rel}/\n")
            f.write(f"  4. Autor: {entry.get('author', 'Unknown')}\n")

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _show_about(self):
        win = ctk.CTkToplevel(self)
        win.title(f"Acerca de {APP_NAME}")
        win.geometry("400x280")
        win.resizable(False, False)
        win.grab_set()

        ctk.CTkLabel(
            win, text=APP_NAME,
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#107C10",
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            win, text=f"v{APP_VERSION}  •  MIT License",
            font=ctk.CTkFont(size=11), text_color="#666666",
        ).pack()
        ctk.CTkLabel(
            win, text="Preparador de USB para Xbox 360 — macOS / Linux",
            font=ctk.CTkFont(size=11), text_color="#555555",
        ).pack(pady=(4, 16))

        link_row = ctk.CTkFrame(win, fg_color="transparent")
        link_row.pack()
        ctk.CTkButton(
            link_row, text="GitHub",
            command=lambda: webbrowser.open(f"https://github.com/{GITHUB_REPO}"),
            fg_color="transparent", text_color="#107C10",
            hover_color="#1e1e1e", width=80,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            win, text="Cerrar", command=win.destroy,
            fg_color="#2d2d2d", hover_color="#3d3d3d", width=90,
        ).pack(pady=(16, 0))

    def _open_usb(self):
        path = self._last_usb_path
        if not path:
            return
        try:
            if self._system == "Darwin":
                subprocess.run(["open", path])
            elif self._system == "Linux":
                subprocess.run(["xdg-open", path])
        except Exception:
            pass
