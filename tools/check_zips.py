"""
tools/check_zips.py — Diagnóstico de ZIPs cacheados vs catalog.py

Verifica que cada entry "type=auto" del catálogo produce la extracción
correcta dada la combinación ZIP-structure + dest_rel.

Uso:
    python tools/check_zips.py

No requiere USB conectado. No modifica nada.
"""

import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.catalog import CATALOG
from app.core.config import TEMP_DIR

USB_ROOT = "USB:/"


def _simulate_extract(names: list, dest_rel: str) -> tuple[str, str, list[str]]:
    """
    Simula la lógica de extract_zip_to.
    Devuelve (prefix, target, [primeras rutas finales de archivos reales]).
    """
    clean = [n for n in names if not n.startswith("__MACOSX/") and ".DS_Store" not in n]

    if dest_rel:
        target = USB_ROOT + dest_rel.rstrip("/") + "/"
    else:
        target = USB_ROOT

    prefix = ""
    if dest_rel:
        remaining = list(clean)
        accumulated = ""
        while True:
            roots = {n.split("/")[0] for n in remaining if n}
            if len(roots) != 1:
                break
            candidate = list(roots)[0]
            candidate_slash = candidate + "/"
            has_children = any(n.startswith(candidate_slash) for n in remaining)
            if not has_children:
                break
            if not all(n == candidate or n.startswith(candidate_slash) for n in remaining):
                break
            accumulated += candidate_slash
            remaining = [
                n[len(candidate_slash):]
                for n in remaining
                if n.startswith(candidate_slash) and len(n) > len(candidate_slash)
            ]
            if not remaining:
                break
        prefix = accumulated

    real_files = [n for n in clean if not n.endswith("/")]
    previews = []
    for name in real_files[:5]:
        rel = name[len(prefix):] if prefix else name
        if rel:
            parts = [p for p in rel.replace("\\", "/").split("/") if p]
            if parts:
                previews.append(target + "/".join(parts))

    return prefix, target, previews


def _check_warnings(names: list, dest_rel: str, prefix: str) -> list[str]:
    clean = [n for n in names if not n.startswith("__MACOSX/") and ".DS_Store" not in n]
    roots = {n.split("/")[0] for n in clean if n}
    real_count = sum(1 for n in clean if not n.endswith("/"))
    warns = []

    if dest_rel and "Content" in roots:
        warns.append("Content Package instalado en subcarpeta — debería ir al root del USB (dest_rel vacío)")
    if dest_rel and prefix == "" and len(roots) > 1:
        warns.append(f"Múltiples roots sin strip ({sorted(roots)}) — archivos anidados en {dest_rel}/")
    if real_count == 0:
        warns.append("ZIP sin archivos extraíbles (solo carpetas o vacío)")

    return warns


def main():
    print(f"\nDiagnóstico de ZIPs — TEMP_DIR: {TEMP_DIR}\n")
    print("=" * 70)

    ok_count    = 0
    warn_count  = 0
    invalid_count = 0
    missing_count = 0

    auto_entries = [(k, v) for k, v in CATALOG.items() if v.get("type") == "auto"]

    for key, entry in auto_entries:
        name     = entry.get("name", key)
        dest_rel = entry.get("dest", "")
        tab      = entry.get("tab", "?")
        zip_path = os.path.join(TEMP_DIR, f"{key}.zip")

        # ── No cacheado ───────────────────────────────────────────────────
        if not os.path.exists(zip_path):
            print(f"⬇  {key:<22} ({name})")
            print(f"   [{tab}]  dest_rel: {dest_rel!r:<20}  NO CACHEADO")
            print()
            missing_count += 1
            continue

        size_kb = os.path.getsize(zip_path) // 1024
        size_str = f"{size_kb / 1024:.1f} MB" if size_kb >= 1024 else f"{size_kb} KB"

        # ── ZIP inválido ──────────────────────────────────────────────────
        if not zipfile.is_zipfile(zip_path):
            print(f"❌  {key:<22} ({name})")
            print(f"   [{tab}]  {size_str}  ZIP INVÁLIDO (descarga corrupta)")
            print()
            invalid_count += 1
            continue

        # ── ZIP válido: analizar ──────────────────────────────────────────
        with zipfile.ZipFile(zip_path, "r") as zf:
            all_names = zf.namelist()

        clean = [n for n in all_names if not n.startswith("__MACOSX/") and ".DS_Store" not in n]
        roots = {n.split("/")[0] for n in clean if n}
        real_count = sum(1 for n in clean if not n.endswith("/"))

        prefix, target, previews = _simulate_extract(clean, dest_rel)
        warns = _check_warnings(clean, dest_rel, prefix)

        prefix_display = f"'{prefix}'" if prefix else "ninguno (dest_rel vacío)" if not dest_rel else "ninguno (múltiples roots)"
        roots_display = str(roots) if len(roots) <= 3 else f"{len(roots)} roots"

        icon = "⚠ " if warns else "✅"
        print(f"{icon} {key:<22} ({name})")
        print(f"   [{tab}]  {size_str} | {real_count} archivos | roots: {roots_display}")
        print(f"   prefix strip: {prefix_display}")
        print(f"   dest_rel: {dest_rel!r:<20}  →  target: {target}")

        if previews:
            print(f"   Extrae como:")
            for p in previews:
                print(f"     {p}")
            if real_count > 5:
                print(f"     … y {real_count - 5} archivos más")

        for w in warns:
            print(f"   !! {w}")

        if warns:
            warn_count += 1
        else:
            ok_count += 1

        print()

    print("=" * 70)
    print(f"RESUMEN: ✅ {ok_count} correctos  |  ⚠  {warn_count} warnings  "
          f"|  ❌ {invalid_count} inválidos  |  ⬇ {missing_count} sin cachear")
    print()


if __name__ == "__main__":
    main()
