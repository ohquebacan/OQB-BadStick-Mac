import os
import platform
import subprocess
import tempfile
import threading
from tkinter import messagebox

import customtkinter as ctk

from app.core.config import APP_NAME, APP_VERSION, SOURCES
from app.core.device_manager import DeviceManager
from app.core.downloader import Downloader
from app.core.installer import Installer
from app.ui.device_frame import DeviceFrame
from app.ui.footer import FooterFrame
from app.ui.header import HeaderFrame
from app.ui.options_frame import OptionsFrame
from app.ui.progress_frame import ProgressFrame


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("780x640")
        self.resizable(False, False)

        self._system = platform.system()
        self._device_manager = DeviceManager()
        self._downloader = Downloader()
        self._installer = Installer()
        self._last_usb_path: str = None

        self._build_ui()
        self._on_startup()

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self.header = HeaderFrame(self, APP_NAME, APP_VERSION)
        self.header.pack(fill="x")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=4)

        self.device_frame = DeviceFrame(
            content,
            on_refresh=self._refresh_devices,
            on_format=self._format_device_only,
        )
        self.device_frame.pack(fill="x", pady=(0, 4))

        self.options_frame = OptionsFrame(content)
        self.options_frame.pack(fill="x", pady=(0, 4))

        self.progress_frame = ProgressFrame(content)
        self.progress_frame.pack(fill="x", pady=(0, 4))

        self.install_btn = ctk.CTkButton(
            content,
            text="INSTALAR EN USB",
            command=self._start_install,
            fg_color="#107C10",
            hover_color="#0d6a0d",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            corner_radius=8,
        )
        self.install_btn.pack(fill="x", pady=(0, 4))

        self.open_btn = ctk.CTkButton(
            content,
            text="Abrir USB en Finder",
            command=self._open_usb,
            fg_color="#2d2d2d",
            hover_color="#3d3d3d",
            height=32,
        )
        # Packed dynamically after successful install

        self.footer = FooterFrame(self)
        self.footer.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------ #
    # Startup                                                              #
    # ------------------------------------------------------------------ #

    def _on_startup(self):
        if self._system == "Windows":
            self.progress_frame.log(
                "⚠ Para Windows usa BadStick: github.com/LxcyDr0p/BadStick"
            )
            self.install_btn.configure(
                state="disabled",
                text="INSTALAR EN USB  (solo macOS/Linux)",
            )
        self._refresh_devices()
        self.progress_frame.log(
            "⚠ DESCONECTA TU XBOX 360 DE INTERNET antes de usar este USB"
        )

    def _refresh_devices(self):
        devices = self._device_manager.list_usb_devices()
        self.device_frame.update_devices(devices)
        count = len(devices)
        if count:
            self.progress_frame.log(f"✓ {count} dispositivo(s) USB detectado(s)")
        else:
            self.progress_frame.log("Sin dispositivos USB detectados")

    # ------------------------------------------------------------------ #
    # Format only (device_frame button)                                   #
    # ------------------------------------------------------------------ #

    def _format_device_only(self):
        device = self.device_frame.get_selected_device()
        if not device:
            messagebox.showerror("Error", "Selecciona un dispositivo USB primero.")
            return

        ok = messagebox.askyesno(
            "Confirmar formateo",
            f"¿Formatear /dev/{device['identifier']} ({device['name']}, {device['size']}) a FAT32?\n\n"
            "Esto borrará todo el contenido del dispositivo.",
        )
        if not ok:
            return

        self._set_controls_enabled(False)
        self.progress_frame.set_progress(0.05, "Formateando...")
        self.progress_frame.log(f"Formateando /dev/{device['identifier']}...")

        def _worker():
            success, mount_point = self._device_manager.format_device(
                device["identifier"],
                lambda line: self.after(0, lambda l=line: self.progress_frame.log(l)),
            )
            def _done():
                self._set_controls_enabled(True)
                if success:
                    self.progress_frame.set_progress(1.0, "Formateado completado")
                    self.progress_frame.log(f"✓ Montado en: {mount_point or 'desconocido'}")
                    self._refresh_devices()
                else:
                    self.progress_frame.set_progress(0.0, "Error al formatear")
                    self.progress_frame.log("❌ ERROR: No se pudo formatear el dispositivo")
                    messagebox.showerror("Error", "No se pudo formatear el dispositivo.\nVerifica los permisos e inténtalo de nuevo.")
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Full install flow                                                    #
    # ------------------------------------------------------------------ #

    def _start_install(self):
        device = self.device_frame.get_selected_device()
        if not device:
            messagebox.showerror("Error", "Selecciona un dispositivo USB primero.")
            return

        ok = messagebox.askyesno(
            "⚠ ADVERTENCIA",
            f"Esto formateará {device['name']} y borrará todo su contenido.\n\n"
            f"Dispositivo: /dev/{device['identifier']}\n"
            f"Tamaño: {device['size']}\n\n"
            "¿Continuar?",
        )
        if not ok:
            return

        options = self.options_frame.get_options()
        self._set_controls_enabled(False)
        self.open_btn.pack_forget()
        self.progress_frame.clear_log()
        self.progress_frame.set_progress(0.0, "Iniciando...")
        self.progress_frame.log("Iniciando instalación...")

        threading.Thread(
            target=self._install_worker,
            args=(device, options),
            daemon=True,
        ).start()

    def _install_worker(self, device: dict, options: dict):
        def log(msg):
            self.after(0, lambda m=msg: self.progress_frame.log(m))

        def prog(val, status=""):
            self.after(0, lambda v=val, s=status: self.progress_frame.set_progress(v, s))

        try:
            # ── Step 1: Format (0 → 20%) ────────────────────────────────
            log(f"Formateando /dev/{device['identifier']}...")
            prog(0.05, "Formateando USB...")

            success, usb_path = self._device_manager.format_device(
                device["identifier"],
                lambda line: self.after(0, lambda l=line: self.progress_frame.log(l)),
            )
            if not success:
                raise RuntimeError("Error al formatear el dispositivo")

            if not usb_path:
                usb_path = self._device_manager.get_mount_point(device["identifier"])
            if not usb_path:
                raise RuntimeError("No se pudo determinar el punto de montaje del USB")

            self._last_usb_path = usb_path
            log(f"✓ USB formateado — montado en {usb_path}")
            prog(0.20, "Descargando archivos...")

            # ── Step 2: Download (20 → 70%) ─────────────────────────────
            sources_to_dl = ["abadavatar", options["payload"]]
            if options.get("nand_flasher"):
                sources_to_dl.append("nand_flasher")

            n = len(sources_to_dl)
            src_progress = [0.0] * n

            def make_dl_cb(idx, name):
                def cb(dl, total):
                    src_progress[idx] = dl / total if total else 0
                    overall = 0.20 + (sum(src_progress) / n) * 0.50
                    self.after(
                        0,
                        lambda v=overall, s=f"Descargando {name}...":
                            self.progress_frame.set_progress(v, s),
                    )
                return cb

            downloaded = {}
            with tempfile.TemporaryDirectory() as tmp:
                for i, key in enumerate(sources_to_dl):
                    if key not in SOURCES:
                        continue
                    source = SOURCES[key]
                    name = source["name"]
                    log(f"Descargando {name}...")

                    url = None
                    if "api_url" in source:
                        url = self._downloader.get_latest_release_url(
                            source["api_url"], source["asset_pattern"]
                        )
                        log("  → Usando release más reciente" if url else
                            "  → API no disponible, usando respaldo")
                        if not url:
                            url = source.get("fallback_url")
                    elif "direct_url" in source:
                        url = source["direct_url"]

                    if not url:
                        log(f"  ❌ Sin URL para {name}")
                        continue

                    dest = os.path.join(tmp, f"{key}.zip")
                    ok = self._downloader.download_file(url, dest, make_dl_cb(i, name))
                    if ok:
                        src_progress[i] = 1.0
                        log(f"  ✓ {name} listo")
                        downloaded[key] = dest
                    else:
                        log(f"  ❌ Error descargando {name}")

                if "abadavatar" not in downloaded:
                    raise RuntimeError("ABadAvatar no se pudo descargar")

                prog(0.70, "Instalando en USB...")

                # ── Step 3: Install (70 → 95%) ───────────────────────────
                log("Instalando archivos en USB...")
                ok = self._installer.install(
                    downloaded, usb_path, options["payload"], log
                )
                if not ok:
                    raise RuntimeError("Error durante la instalación de archivos")

                prog(0.95, "Expulsando USB...")

                # ── Step 4: Eject (95 → 100%) ────────────────────────────
                log("Expulsando USB de forma segura...")
                # Keep mounted so user can open Finder; eject is optional
                prog(1.0, "¡Completado!")

                # Success summary
                summary_lines = [
                    "",
                    f"✅ USB listo en {usb_path}",
                    "",
                    "PASOS SIGUIENTES:",
                    "1. Descarga Aurora desde phoenix.xboxunity.net",
                    "   Extrae y copia como: USB/Apps/Aurora/",
                    "2. Desconecta tu Xbox 360 de Internet",
                    "3. Inserta el USB en tu Xbox 360",
                    "4. Enciende la consola — el exploit corre automático",
                    "5. Cuando veas la animación de éxito → presiona BACK",
                    "",
                    "⚠ Este exploit NO es permanente. Debes repetirlo",
                    "  cada vez que reinicias la consola.",
                ]
                for line in summary_lines:
                    log(line)

            def _on_success():
                self._set_controls_enabled(True)
                self._refresh_devices()
                self.open_btn.pack(fill="x", pady=(0, 4), before=self.footer)

            self.after(0, _on_success)

        except Exception as exc:
            err = str(exc)
            def _on_error():
                self.progress_frame.log(f"❌ ERROR: {err}")
                self.progress_frame.set_progress(0.0, "Error")
                self._set_controls_enabled(True)
                messagebox.showerror("Error", f"Error durante la instalación:\n\n{err}")
            self.after(0, _on_error)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _open_usb(self):
        if not self._last_usb_path:
            return
        try:
            if self._system == "Darwin":
                subprocess.run(["open", self._last_usb_path])
            elif self._system == "Linux":
                subprocess.run(["xdg-open", self._last_usb_path])
        except Exception:
            pass

    def _set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.install_btn.configure(state=state)
        self.device_frame.set_enabled(enabled)
        self.options_frame.set_enabled(enabled)
