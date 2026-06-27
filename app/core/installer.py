import os
import shutil
import zipfile

from app.core.config import LAUNCH_INI_CONTENT


class Installer:
    def install(
        self,
        downloaded_files: dict,
        usb_path: str,
        options: dict,
        log_callback,
    ) -> tuple:
        """
        Returns (success: bool, checklist: list[dict])
        checklist entries: {"label": str, "ok": bool, "note": str}
        options keys: exploit, payload, nand_flasher, dashlaunch,
                      aurora, xexmenu, create_folders, launch_ini
        """
        checklist = []

        def mark(label, ok, note=""):
            checklist.append({"label": label, "ok": ok, "note": note})

        try:
            exploit = options.get("exploit", "abadavatar")
            payload = options.get("payload", "xeunshackle")

            # 1. Extract exploit (ABadAvatar or ABadMemUnit)
            if exploit not in downloaded_files:
                log_callback(f"❌ ERROR: {exploit} no descargado")
                return False, checklist

            log_callback(f"Extrayendo {exploit}...")
            payload_ok, content_ok = self._extract_exploit(
                downloaded_files[exploit], usb_path, log_callback
            )
            mark("BadUpdatePayload/ copiado", payload_ok)
            mark("Content/ copiado", content_ok)

            # 2. Install payload (XeUnshackle or FreeMyXe)
            if payload in downloaded_files:
                log_callback(f"Instalando payload ({payload})...")
                xex_ok = self._install_payload(
                    downloaded_files[payload], usb_path, log_callback
                )
                payload_name = "XeUnshackle" if payload == "xeunshackle" else "FreeMyXe"
                mark(f"default.xex instalado ({payload_name})", xex_ok)
            else:
                log_callback(f"⚠ Payload {payload} no disponible")
                mark("default.xex instalado", False, "no descargado")

            # 3. Folder structure
            if options.get("create_folders", True):
                log_callback("Creando estructura de carpetas...")
                self._create_folder_structure(usb_path, log_callback)

            # 4. launch.ini
            if options.get("launch_ini", True):
                log_callback("Creando launch.ini...")
                with open(os.path.join(usb_path, "launch.ini"), "w", encoding="utf-8") as f:
                    f.write(LAUNCH_INI_CONTENT)
                mark("launch.ini generado", True)

            # 5. NAND Flasher
            if options.get("nand_flasher") and "nand_flasher" in downloaded_files:
                log_callback("Instalando Simple 360 NAND Flasher...")
                self._install_zipped_app(
                    downloaded_files["nand_flasher"],
                    os.path.join(usb_path, "Apps", "NANDFlasher"),
                    log_callback,
                )

            # 6. DashLaunch
            if options.get("dashlaunch") and "dashlaunch" in downloaded_files:
                log_callback("Instalando DashLaunch...")
                self._install_zipped_app(
                    downloaded_files["dashlaunch"],
                    os.path.join(usb_path, "Apps", "DashLaunch"),
                    log_callback,
                )
                mark("DashLaunch instalado", True)
            elif options.get("dashlaunch"):
                mark("DashLaunch", False, "instalar manualmente")

            # 7. Manual-install reminders
            if options.get("aurora"):
                mark("Aurora Dashboard", False, "instalar manualmente")
            if options.get("xexmenu"):
                mark("XeXMenu", False, "instalar manualmente")

            log_callback("✓ Instalación completada")
            return True, checklist

        except Exception as e:
            log_callback(f"❌ ERROR: {e}")
            return False, checklist

    # ------------------------------------------------------------------ #

    def _extract_exploit(self, zip_path: str, usb_path: str, log_callback) -> tuple:
        """Returns (bad_payload_ok, content_ok)."""
        bad_ok = False
        content_ok = False
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            bad_prefix = self._find_folder_prefix(names, "BadUpdatePayload")
            content_prefix = self._find_folder_prefix(names, "Content")

            if bad_prefix:
                log_callback("  → Extrayendo BadUpdatePayload/")
                self._extract_subtree(zf, names, bad_prefix,
                                      os.path.join(usb_path, "BadUpdatePayload"))
                bad_ok = True
            else:
                log_callback("  ⚠ BadUpdatePayload/ no encontrado en ZIP")

            if content_prefix:
                log_callback("  → Extrayendo Content/")
                self._extract_subtree(zf, names, content_prefix,
                                      os.path.join(usb_path, "Content"))
                content_ok = True
            else:
                log_callback("  ⚠ Content/ no encontrado en ZIP")

        return bad_ok, content_ok

    def _install_payload(self, zip_path: str, usb_path: str, log_callback) -> bool:
        dest_dir = os.path.join(usb_path, "BadUpdatePayload")
        os.makedirs(dest_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            default_xex = None
            fallback_xex = None

            for name in names:
                bn = os.path.basename(name).lower()
                if bn == "default.xex" and not name.endswith("/"):
                    default_xex = name
                    break
                if bn.endswith(".xex") and not name.endswith("/") and fallback_xex is None:
                    fallback_xex = name

            xex_entry = default_xex or fallback_xex
            if xex_entry:
                dest = os.path.join(dest_dir, "default.xex")
                with zf.open(xex_entry) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                log_callback("  → default.xex instalado")
                return True
            else:
                log_callback("  ⚠ No se encontró .xex en el payload")
                return False

    def _create_folder_structure(self, usb_path: str, log_callback):
        for folder in ("Apps", "Games", "Emulators", "Plugins"):
            os.makedirs(os.path.join(usb_path, folder), exist_ok=True)

        readme = os.path.join(usb_path, "Apps", "README.txt")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                "Carpeta Apps/\n"
                "=============\n\n"
                "Coloca aquí tus aplicaciones para Xbox 360.\n\n"
                "  Apps/Aurora/      ← Aurora Dashboard  (descarga manual)\n"
                "  Apps/XeXMenu/     ← File manager      (descarga manual)\n"
                "  Apps/DashLaunch/  ← Plugin loader     (descarga manual)\n\n"
                "Aurora: https://phoenix.xboxunity.net/#/news\n"
            )
        log_callback("  → Estructura creada: Apps/, Games/, Emulators/, Plugins/")

    def _install_zipped_app(self, zip_path: str, dest_dir: str, log_callback):
        os.makedirs(dest_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".xex") and not name.endswith("/"):
                        bn = os.path.basename(name)
                        with zf.open(name) as src, open(os.path.join(dest_dir, bn), "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        log_callback(f"  → {bn} instalado")
        except Exception as e:
            log_callback(f"  ⚠ Error: {e}")

    # ------------------------------------------------------------------ #

    @staticmethod
    def _find_folder_prefix(names: list, folder_name: str) -> str:
        for name in names:
            parts = name.replace("\\", "/").split("/")
            for i, part in enumerate(parts):
                if part == folder_name:
                    return "/".join(parts[: i + 1]) + "/"
        return None

    @staticmethod
    def _extract_subtree(zf: zipfile.ZipFile, names: list, prefix: str, dest_dir: str):
        for name in names:
            if not name.startswith(prefix) or len(name) <= len(prefix):
                continue
            relative = name[len(prefix):]
            dest = os.path.join(dest_dir, relative)
            if name.endswith("/"):
                os.makedirs(dest, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with zf.open(name) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
