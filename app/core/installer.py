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
        Handles exploit extraction + payload xex installation only.
        Catalog items are extracted by main_window._generate_extras.

        Returns (success: bool, checklist: list[dict])
        """
        checklist = []

        def mark(label, ok, note=""):
            checklist.append({"label": label, "ok": ok, "note": note})

        try:
            exploit = options.get("exploit", "abadavatar")
            payload = options.get("payload")

            # 1. Extract exploit → BadUpdatePayload/ and Content/ at USB root
            if exploit not in downloaded_files:
                log_callback(f"❌ ERROR: {exploit} no descargado")
                return False, checklist

            log_callback(f"Extrayendo exploit ({exploit})…")
            bad_ok, content_ok = self._extract_exploit(
                downloaded_files[exploit], usb_path, log_callback
            )
            mark("BadUpdatePayload/ extraído", bad_ok)
            mark("Content/ extraído", content_ok)

            if not bad_ok:
                log_callback("❌ BadUpdatePayload/ no encontrado en ZIP del exploit")
                return False, checklist

            # 2. Install payload → BadUpdatePayload/default.xex
            if payload and payload in downloaded_files:
                log_callback(f"Instalando payload ({payload})…")
                xex_ok = self._install_payload(
                    downloaded_files[payload], usb_path, log_callback
                )
                name_map = {"xeunshackle": "XeUnshackle", "freemyxe": "FreeMyXe"}
                mark(f"default.xex ({name_map.get(payload, payload)})", xex_ok)
            elif payload:
                log_callback(f"⚠ Payload {payload} no disponible — sin default.xex")
                mark("default.xex", False, "no descargado")

            log_callback("✓ Exploit instalado correctamente")
            return True, checklist

        except Exception as exc:
            log_callback(f"❌ ERROR: {exc}")
            return False, checklist

    # ------------------------------------------------------------------ #

    def _extract_exploit(self, zip_path: str, usb_path: str, log_callback) -> tuple:
        """
        Search for BadUpdatePayload/ and Content/ anywhere in ZIP tree and
        extract them to the USB root. Returns (bad_ok, content_ok).
        """
        bad_ok = False
        content_ok = False
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            bad_prefix     = self._find_folder_prefix(names, "BadUpdatePayload")
            content_prefix = self._find_folder_prefix(names, "Content")

            if bad_prefix:
                log_callback("  → Extrayendo BadUpdatePayload/")
                self._extract_subtree(
                    zf, names, bad_prefix,
                    os.path.join(usb_path, "BadUpdatePayload"),
                )
                bad_ok = True
            else:
                log_callback("  ⚠ BadUpdatePayload/ no encontrado en ZIP")

            if content_prefix:
                log_callback("  → Extrayendo Content/")
                self._extract_subtree(
                    zf, names, content_prefix,
                    os.path.join(usb_path, "Content"),
                )
                content_ok = True
            else:
                log_callback("  ⚠ Content/ no encontrado en ZIP")

        return bad_ok, content_ok

    def _install_payload(self, zip_path: str, usb_path: str, log_callback) -> bool:
        """Find .xex in payload ZIP and write it as BadUpdatePayload/default.xex."""
        dest_dir = os.path.join(usb_path, "BadUpdatePayload")
        os.makedirs(dest_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            default_xex  = None
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
                log_callback("  → default.xex instalado en BadUpdatePayload/")
                return True
            else:
                log_callback("  ⚠ No se encontró .xex en payload ZIP")
                return False

    # ------------------------------------------------------------------ #
    # Static utility: extract a ZIP to a destination folder               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def extract_zip_to(
        zip_path: str,
        usb_path: str,
        dest_rel: str,
        log_callback=None,
    ) -> int:
        """
        Extract zip_path into usb_path/dest_rel.

        Rules:
        • dest_rel == ""  → extract to usb_path preserving full ZIP structure (no strip)
        • dest_rel != ""  → extract to usb_path/dest_rel/, stripping a single
                            top-level wrapper folder if the ZIP has exactly one root entry
        • Removes __MACOSX/ directories and .DS_Store files from output.

        Returns the number of files extracted.
        """
        if dest_rel:
            target = os.path.join(usb_path, *dest_rel.split("/"))
        else:
            target = usb_path
        os.makedirs(target, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            # Filter Mac metadata noise
            all_names = zf.namelist()
            names = [
                n for n in all_names
                if not n.startswith("__MACOSX/") and ".DS_Store" not in n
            ]

            # Detect single top-level prefix to strip (only for subfolder extractions)
            prefix = ""
            if dest_rel:
                roots = {n.split("/")[0] for n in names if n}
                if len(roots) == 1:
                    candidate = list(roots)[0]
                    candidate_slash = candidate + "/"
                    if all(
                        n == candidate or n.startswith(candidate_slash)
                        for n in names
                    ):
                        prefix = candidate_slash

            count = 0
            for name in names:
                rel = name[len(prefix):] if prefix else name
                if not rel:
                    continue

                parts = [p for p in rel.replace("\\", "/").split("/") if p]
                if not parts:
                    continue

                dest = os.path.join(target, *parts)
                if name.endswith("/"):
                    os.makedirs(dest, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    count += 1

            if log_callback:
                log_callback(f"    → {count} archivos extraídos")
            return count

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
    def _extract_subtree(
        zf: zipfile.ZipFile, names: list, prefix: str, dest_dir: str
    ):
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

    @staticmethod
    def generate_launch_ini(usb_path: str, log_callback=None):
        """Write a default launch.ini only if one does not already exist."""
        def _log(msg):
            if log_callback:
                log_callback(msg)

        ini_path = os.path.join(usb_path, "launch.ini")
        if os.path.exists(ini_path):
            _log("  ℹ launch.ini existente preservado")
            return

        with open(ini_path, "w", newline="\r\n", encoding="utf-8") as f:
            f.write(LAUNCH_INI_CONTENT.lstrip("\n"))
        _log("  📄 launch.ini generado (puedes editarlo desde Tab 6 → Configuración)")
