#!/bin/bash
# Build OQB BadStick Mac.app with PyInstaller
# Usage: ./build.sh
set -e

echo "Instalando dependencias..."
pip3 install -r requirements.txt
pip3 install pyinstaller

echo "Generando ícono..."
python3 -c "
import os, sys
sys.path.insert(0, '.')
from app.utils.helpers import generate_icon
os.makedirs('assets', exist_ok=True)
ok = generate_icon('assets/icon.png')
print('  ✓ icon.png generado' if ok else '  ⚠ No se pudo generar icon.png')
"

ICON_FILE="assets/icon.png"

# On macOS: convert PNG → ICNS for a proper .app icon
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Convirtiendo ícono a .icns..."
    ICONSET="/tmp/oqb_badstick.iconset"
    rm -rf "$ICONSET"
    mkdir -p "$ICONSET"
    sips -z 16   16   assets/icon.png --out "$ICONSET/icon_16x16.png"    2>/dev/null
    sips -z 32   32   assets/icon.png --out "$ICONSET/icon_16x16@2x.png" 2>/dev/null
    sips -z 32   32   assets/icon.png --out "$ICONSET/icon_32x32.png"    2>/dev/null
    sips -z 64   64   assets/icon.png --out "$ICONSET/icon_32x32@2x.png" 2>/dev/null
    sips -z 128  128  assets/icon.png --out "$ICONSET/icon_128x128.png"  2>/dev/null
    sips -z 256  256  assets/icon.png --out "$ICONSET/icon_128x128@2x.png" 2>/dev/null
    sips -z 256  256  assets/icon.png --out "$ICONSET/icon_256x256.png"  2>/dev/null
    sips -z 512  512  assets/icon.png --out "$ICONSET/icon_256x256@2x.png" 2>/dev/null
    sips -z 512  512  assets/icon.png --out "$ICONSET/icon_512x512.png"  2>/dev/null
    iconutil -c icns "$ICONSET" -o assets/icon.icns && ICON_FILE="assets/icon.icns"
    echo "  ✓ icon.icns generado"
fi

echo "Generando .app con PyInstaller..."
pyinstaller \
  --name "OQB BadStick Mac" \
  --windowed \
  --icon "$ICON_FILE" \
  --add-data "assets:assets" \
  --onefile \
  --clean \
  main.py

echo ""
echo "✅ App generada en: dist/OQB BadStick Mac"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   (Archivo .app listo para distribuir)"
fi
