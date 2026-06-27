#!/bin/bash
# Build OQB BadStick Mac.app + DMG
# Uso: ./build.sh
# Requiere: macOS, Python 3.9+, pip3
set -e

APP_NAME="OQB BadStick Mac"
VERSION="1.0.1"
DMG_NAME="OQB_BadStick_Mac_v${VERSION}.dmg"
DIST_DIR="dist"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
DMG_PATH="$DIST_DIR/$DMG_NAME"

# ── 1. Dependencias ──────────────────────────────────────────────────
echo "→ Instalando dependencias..."
pip3 install -r requirements.txt --quiet
pip3 install pyinstaller --quiet

# ── 2. Ícono ─────────────────────────────────────────────────────────
echo "→ Verificando ícono..."
if [[ -f "assets/icon.png" ]]; then
    echo "  ✓ assets/icon.png existente — usando el real (no se sobreescribe)"
else
    echo "  ⚠ assets/icon.png no encontrado — generando placeholder..."
    python3 -c "
import os, sys
sys.path.insert(0, '.')
from app.utils.helpers import generate_icon
os.makedirs('assets', exist_ok=True)
generate_icon('assets/icon.png')
"
fi

ICON_FILE="assets/icon.png"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "→ Convirtiendo a .icns..."
    ICONSET="/tmp/oqb_badstick.iconset"
    rm -rf "$ICONSET" && mkdir -p "$ICONSET"
    for size in 16 32 64 128 256 512; do
        sips -z $size $size assets/icon.png \
            --out "$ICONSET/icon_${size}x${size}.png" 2>/dev/null
    done
    sips -z 512 512 assets/icon.png \
        --out "$ICONSET/icon_256x256@2x.png" 2>/dev/null
    iconutil -c icns "$ICONSET" -o assets/icon.icns 2>/dev/null \
        && ICON_FILE="assets/icon.icns" && echo "  ✓ icon.icns listo"
fi

# ── 3. PyInstaller → .app bundle (SIN --onefile) ─────────────────────
echo "→ Generando .app bundle con PyInstaller..."
rm -rf build "$DIST_DIR"

pyinstaller \
    --name "$APP_NAME" \
    --windowed \
    --icon "$ICON_FILE" \
    --add-data "assets:assets" \
    --clean \
    --noconfirm \
    main.py

if [[ ! -d "$APP_BUNDLE" ]]; then
    echo "❌ ERROR: No se generó $APP_BUNDLE"
    exit 1
fi
echo "  ✓ $APP_BUNDLE generado"

# ── 4. DMG (solo macOS) ──────────────────────────────────────────────
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠  DMG solo se genera en macOS. En Linux: dist/$APP_NAME (binario)"
    exit 0
fi

echo "→ Construyendo DMG..."

# Staging folder: .app + symlink a /Applications
STAGING="/tmp/oqb_dmg_staging"
rm -rf "$STAGING"
mkdir -p "$STAGING"
cp -r "$APP_BUNDLE" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

# Crear DMG comprimido directamente desde staging
rm -f "$DMG_PATH"
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$STAGING" \
    -ov \
    -format UDZO \
    -fs HFS+ \
    "$DMG_PATH"

rm -rf "$STAGING"

echo ""
echo "════════════════════════════════════════"
echo "✅  Build completado"
echo "   App:  $APP_BUNDLE"
echo "   DMG:  $DMG_PATH"
SIZE=$(du -sh "$DMG_PATH" | cut -f1)
echo "   Size: $SIZE"
echo ""
echo "Para distribuir: subí $DMG_PATH al release de GitHub"
echo "════════════════════════════════════════"
