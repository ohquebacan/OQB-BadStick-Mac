import os
import platform
import shutil
import subprocess
import webbrowser
from tkinter import messagebox

import customtkinter as ctk

from app.core.config import APP_NAME, APP_VERSION, APP_AUTHOR, GITHUB_REPO


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, icon_path: str = None, get_usb_path=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._icon_path = icon_path
        self._get_usb_path = get_usb_path
        self._system = platform.system()
        self._build()
        self.update_idletasks()

    def _build(self):
        # Centered container
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

        # Action buttons
        btn_data = [
            ("Limpiar archivos temporales", "#2d2d2d", self._clean_temp),
            ("Abrir USB en Finder",          "#2d2d2d", self._open_usb),
            ("Reportar problema",            "#2d2d2d",
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

    def _fallback_logo(self, parent):
        logo = ctk.CTkFrame(parent, fg_color="#2a2a2a", corner_radius=8,
                            width=120, height=120)
        logo.pack(pady=(10, 6))
        logo.pack_propagate(False)
        ctk.CTkLabel(
            logo, text="OQB",
            font=ctk.CTkFont(size=32, weight="bold"), text_color="#107C10",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _clean_temp(self):
        temp_dir = os.path.join(os.path.expanduser("~"), "OQB-BadStick-Mac", "temp")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            messagebox.showinfo("Listo", "Archivos temporales eliminados.")
        else:
            messagebox.showinfo("Info", "No hay archivos temporales.")

    def _open_usb(self):
        path = self._get_usb_path() if callable(self._get_usb_path) else None
        if not path:
            messagebox.showwarning("USB", "No hay USB montado actualmente.\n"
                                   "Conecta un USB e instala primero.")
            return
        try:
            if self._system == "Darwin":
                subprocess.run(["open", path])
            elif self._system == "Linux":
                subprocess.run(["xdg-open", path])
        except Exception:
            pass
