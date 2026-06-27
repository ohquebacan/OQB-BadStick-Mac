import os
import platform
import shutil
import subprocess
import webbrowser
from tkinter import messagebox

import customtkinter as ctk

from app.core.config import APP_NAME, APP_VERSION, APP_AUTHOR, GITHUB_REPO, TEMP_DIR

def _cache_stats() -> tuple:
    """Return (total_bytes, file_count) for TEMP_DIR."""
    if not os.path.exists(TEMP_DIR):
        return 0, 0
    total, count = 0, 0
    for f in os.listdir(TEMP_DIR):
        fp = os.path.join(TEMP_DIR, f)
        if os.path.isfile(fp):
            total += os.path.getsize(fp)
            count += 1
    return total, count


def _fmt_size(size_bytes: int) -> str:
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.1f} GB"
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.0f} MB"
    return f"{size_bytes / 1024:.0f} KB"


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, icon_path: str = None, get_usb_path=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._icon_path    = icon_path
        self._get_usb_path = get_usb_path
        self._system       = platform.system()
        self._cache_lbl    = None
        self._build()
        self.update_idletasks()

    def _build(self):
        inner = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color="#3a3a3a",
        )
        inner.pack(fill="both", expand=True, padx=40, pady=10)

        # Logo / icon
        if self._icon_path and os.path.exists(self._icon_path):
            try:
                from PIL import Image
                pil_img = Image.open(self._icon_path).resize((120, 120), Image.LANCZOS)
                ctk_img = ctk.CTkImage(
                    light_image=pil_img, dark_image=pil_img, size=(120, 120)
                )
                ctk.CTkLabel(inner, image=ctk_img, text="").pack(pady=(10, 6))
            except Exception:
                self._fallback_logo(inner)
        else:
            self._fallback_logo(inner)

        ctk.CTkLabel(
            inner, text=APP_NAME,
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#107C10",
        ).pack()

        ctk.CTkLabel(
            inner, text=f"v{APP_VERSION}  •  {APP_AUTHOR}",
            font=ctk.CTkFont(size=11), text_color="#666666",
        ).pack(pady=(2, 14))

        # ── Cache section ────────────────────────────────────────────────
        cache_frame = ctk.CTkFrame(inner, fg_color="#1a1a1a", corner_radius=8)
        cache_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            cache_frame, text="Caché de descargas",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        row = ctk.CTkFrame(cache_frame, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 10))

        self._cache_lbl = ctk.CTkLabel(
            row, text=self._cache_text(),
            font=ctk.CTkFont(size=11), text_color="#777777",
        )
        self._cache_lbl.pack(side="left")

        ctk.CTkButton(
            row, text="Actualizar", command=self._refresh_cache_lbl,
            fg_color="#2d2d2d", hover_color="#3d3d3d",
            width=80, height=24, font=ctk.CTkFont(size=10),
        ).pack(side="left", padx=(10, 0))

        # ── Action buttons ────────────────────────────────────────────────
        btn_data = [
            ("⚙️  Editar launch.ini",          "#2d2d2d", self._open_launch_ini_editor),
            ("🗑  Limpiar caché de descargas", "#2d2d2d", self._clean_temp),
            ("📂  Abrir USB en Finder",        "#2d2d2d", self._open_usb),
            ("🐛  Reportar problema",           "#2d2d2d",
             lambda: webbrowser.open(f"https://github.com/{GITHUB_REPO}/issues")),
        ]
        for label, fg, cmd in btn_data:
            ctk.CTkButton(
                inner, text=label, command=cmd,
                fg_color=fg, hover_color="#3d3d3d",
                width=260, height=32,
            ).pack(pady=3)

        # Link buttons
        links_frame = ctk.CTkFrame(inner, fg_color="transparent")
        links_frame.pack(pady=(8, 0))

        ctk.CTkButton(
            links_frame, text="GitHub",
            command=lambda: webbrowser.open(f"https://github.com/{GITHUB_REPO}"),
            fg_color="transparent", hover_color="#1e1e1e",
            text_color="#107C10", font=ctk.CTkFont(size=11),
            width=80, height=24,
        ).pack(side="left", padx=4)

        # Credits box
        cred = ctk.CTkFrame(inner, fg_color="#1a1a1a", corner_radius=8)
        cred.pack(fill="x", pady=(14, 0))

        ctk.CTkLabel(
            cred, text="Créditos",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        for line in [
            "BadStick (Windows)               →  LxcyDr0p",
            "ABadAvatar / ABadMemUnit          →  shutterbug2000",
            "XeUnshackle                       →  Byrom90",
            "FreeMyXe                          →  InvoxiPlayGames",
            "Aurora Dashboard                  →  Phoenix Team",
            "XeXMenu                           →  Team XeDEV",
            "Simple 360 NAND Flasher           →  Swizzy",
            "Xbox360BadUpdate (exploit base)   →  Grimdoomer",
        ]:
            ctk.CTkLabel(
                cred, text=line,
                font=ctk.CTkFont(family="Courier", size=10), text_color="#555555",
            ).pack(anchor="w", padx=14)

        ctk.CTkLabel(
            cred, text=f"\nPara macOS / Linux por OQB / ohquebacan.com",
            font=ctk.CTkFont(size=10), text_color="#444444",
        ).pack(anchor="w", padx=14, pady=(0, 10))

    # ------------------------------------------------------------------ #

    def _fallback_logo(self, parent):
        logo = ctk.CTkFrame(parent, fg_color="#2a2a2a", corner_radius=8,
                            width=120, height=120)
        logo.pack(pady=(10, 6))
        logo.pack_propagate(False)
        ctk.CTkLabel(
            logo, text="OQB",
            font=ctk.CTkFont(size=32, weight="bold"), text_color="#107C10",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _cache_text(self) -> str:
        size, count = _cache_stats()
        if count == 0:
            return "Caché local: vacía"
        return f"Caché local: {_fmt_size(size)} ({count} archivo{'s' if count != 1 else ''})"

    def _refresh_cache_lbl(self):
        if self._cache_lbl:
            self._cache_lbl.configure(text=self._cache_text())

    def _clean_temp(self):
        size, count = _cache_stats()
        if count == 0:
            messagebox.showinfo("Caché", "La caché ya está vacía.")
            return

        confirmed = messagebox.askyesno(
            "¿Eliminar caché?",
            f"¿Eliminar {count} archivo(s) de caché?\n\n"
            f"Tamaño: {_fmt_size(size)}\n\n"
            "Esto obligará a re-descargar todo en la próxima instalación.",
        )
        if not confirmed:
            return

        deleted = 0
        freed   = 0
        for f in os.listdir(TEMP_DIR):
            fp = os.path.join(TEMP_DIR, f)
            if os.path.isfile(fp):
                freed += os.path.getsize(fp)
                os.remove(fp)
                deleted += 1

        messagebox.showinfo(
            "Caché eliminada",
            f"🗑  {deleted} archivo(s) borrado(s)\n"
            f"   {_fmt_size(freed)} liberados",
        )
        self._refresh_cache_lbl()

    def _open_usb(self):
        path = self._get_usb_path() if callable(self._get_usb_path) else None
        if not path:
            messagebox.showwarning(
                "USB",
                "No hay USB montado actualmente.\n"
                "Conecta un USB e instala primero.",
            )
            return
        try:
            if self._system == "Darwin":
                subprocess.run(["open", path])
            elif self._system == "Linux":
                subprocess.run(["xdg-open", path])
        except Exception:
            pass

    def _open_launch_ini_editor(self):
        from app.ui.dialogs.launch_ini_editor import LaunchIniEditor
        main_window   = self.winfo_toplevel()
        device_manager = getattr(main_window, "device_manager", None)
        LaunchIniEditor(
            main_window,
            get_usb_path=self._get_usb_path,
            device_manager=device_manager,
        )
