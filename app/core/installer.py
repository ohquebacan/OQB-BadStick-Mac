import os
import shutil
import zipfile

from app.core.config import LAUNCH_INI_CONTENT


class Installer:
    def install(
        self,
        downloaded_files: dict,
        usb_path: str,
        payload_choice: str,
        log_callback,
    ) -> bool:
        try:
            # 1. Extract ABadAvatar
            if "abadavatar" not in downloaded_files:
                log_callback("❌ ERROR: ABadAvatar no descargado")
                return False

            log_callback("Extrayendo ABadAvatar...")
            self._extract_abadavatar(downloaded_files["abadavatar"], usb_path, log_callback)

            # 2. Install chosen payload
            if payload_choice in downloaded_files:
                log_callback(f"Instalando payload ({payload_choice})...")
                self._install_payload(
                    downloaded_files[payload_choice], usb_path, log_callback
                )
            else:
                log_callback(f"⚠ Payload {payload_choice} no disponible")

            # 3. Folder structure
            log_callback("Creando estructura de carpetas...")
            self._create_folder_structure(usb_path, log_callback)

            # 4. launch.ini
            log_callback("Creando launch.ini...")
            with open(os.path.join(usb_path, "launch.ini"), "w", encoding="utf-8") as f:
                f.write(LAUNCH_INI_CONTENT)

            # 5. NAND Flasher (optional)
            if "nand_flasher" in downloaded_files:
                log_callback("Instalando Simple 360 NAND Flasher...")
                self._install_nand_flasher(
                    downloaded_files["nand_flasher"], usb_path, log_callback
                )

            log_callback("✓ Instalación completada")
            return True

        except Exception as e:
            log_callback(f"❌ ERROR: {e}")
            return False

    # ------------------------------------------------------------------ #

    def _extract_abadavatar(self, zip_path: str, usb_path: str, log_callback):
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()

            bad_payload_prefix = self._find_folder_prefix(names, "BadUpdatePayload")
            content_prefix = self._find_folder_prefix(names, "Content")

            if bad_payload_prefix:
                log_callback("  → Extrayendo BadUpdatePayload/")
                self._extract_subtree(zf, names, bad_payload_prefix,
                                      os.path.join(usb_path, "BadUpdatePayload"))
            else:
                log_callback("  ⚠ BadUpdatePayload/ no encontrado en ZIP")

            if content_prefix:
                log_callback("  → Extrayendo Content/")
                self._extract_subtree(zf, names, content_prefix,
                                      os.path.join(usb_path, "Content"))
            else:
                log_callback("  ⚠ Content/ no encontrado en ZIP")

    def _install_payload(self, zip_path: str, usb_path: str, log_callback):
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
            else:
                log_callback("  ⚠ No se encontró .xex en el payload")

    def _create_folder_structure(self, usb_path: str, log_callback):
        for folder in ("Apps", "Games", "Emulators", "Plugins"):
            os.makedirs(os.path.join(usb_path, folder), exist_ok=True)

        readme = os.path.join(usb_path, "Apps", "README.txt")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                "Carpeta Apps/\n"
                "=============\n\n"
                "Coloca aquí tus aplicaciones para Xbox 360.\n\n"
                "  Apps/Aurora/   ← Aurora Dashboard  (descarga manual)\n"
                "  Apps/XeXMenu/  ← File manager      (descarga manual)\n\n"
                "Aurora: https://phoenix.xboxunity.net/#/news\n"
            )
        log_callback("  → Estructura creada: Apps/, Games/, Emulators/, Plugins/")

    def _install_nand_flasher(self, zip_path: str, usb_path: str, log_callback):
        dest_dir = os.path.join(usb_path, "Apps", "NANDFlasher")
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
            log_callback(f"  ⚠ Error instalando NAND Flasher: {e}")

    # ------------------------------------------------------------------ #

    @staticmethod
    def _find_folder_prefix(names: list, folder_name: str) -> str:
        """Find the deepest prefix ending with folder_name/ in the zip."""
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
