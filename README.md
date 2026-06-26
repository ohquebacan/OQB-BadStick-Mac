# OQB BadStick Mac

![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)
![macOS](https://img.shields.io/badge/macOS-compatible-brightgreen)
![Linux](https://img.shields.io/badge/Linux-compatible-brightgreen)
![MIT License](https://img.shields.io/badge/License-MIT-green)

> Primera herramienta con GUI para preparar un USB con el exploit **ABadAvatar** en macOS y Linux — sin necesidad de Windows.

[screenshot aquí]

---

## ¿Qué hace?

OQB BadStick Mac detecta tu USB, lo formatea a FAT32, descarga automáticamente el exploit [ABadAvatar](https://github.com/shutterbug2000/ABadAvatar) y el payload elegido ([XeUnshackle](https://github.com/Byrom90/XeUnshackle) o [FreeMyXe](https://github.com/FreeMyXe/FreeMyXe)), y deja el USB listo para ejecutar homebrew en Xbox 360 sin soldar ni modificar hardware permanentemente.

El exploit **no es permanente** — debe repetirse cada vez que se reinicia la consola.

---

## Requisitos

- Python 3.9+ con pip  
  _o bien: descargar el `.app` desde [Releases](https://github.com/ohquebacan/OQB-BadStick-Mac/releases) (no requiere Python)_
- macOS 11+ o Linux con `lsblk` y `udisksctl`
- Conexión a internet (para descargar los exploits)
- Un USB de al menos 256 MB formateado o sin partición

---

## Instalación

### Opción A — Ejecutar desde código fuente

```bash
git clone https://github.com/ohquebacan/OQB-BadStick-Mac.git
cd OQB-BadStick-Mac
pip install -r requirements.txt
python main.py
```

### Opción B — Descargar .app (macOS, sin Python)

1. Ve a [Releases](https://github.com/ohquebacan/OQB-BadStick-Mac/releases)
2. Descarga `OQB BadStick Mac.app.zip`
3. Descomprime y arrastra a Aplicaciones
4. En la primera apertura: clic derecho → Abrir (para omitir Gatekeeper)

---

## Qué instala automáticamente

| Componente | Fuente | Carpeta en USB |
|---|---|---|
| ABadAvatar (exploit) | shutterbug2000/ABadAvatar | `BadUpdatePayload/` + `Content/` |
| XeUnshackle _o_ FreeMyXe (payload) | Byrom90 / FreeMyXe | `BadUpdatePayload/default.xex` |
| Simple 360 NAND Flasher (opcional) | Swizzy/XDK_Projects | `Apps/NANDFlasher/` |
| launch.ini preconfigurado | — | raíz del USB |

## Qué debes instalar manualmente

| Componente | Por qué es manual | Instrucciones |
|---|---|---|
| **Aurora Dashboard** | Distribuido como RAR, sin release en GitHub | Descarga en [phoenix.xboxunity.net](https://phoenix.xboxunity.net/#/news), extrae en `USB/Apps/Aurora/` |
| **XeXMenu** | Sin release oficial | Busca en se7ensins.com, extrae en `USB/Apps/XeXMenu/` |

---

## Advertencias de seguridad

> ⚠ **Haz un backup de tu NAND antes de modificar cualquier cosa.** Usa el NAND Flasher incluido.

> ⚠ **Desconecta tu Xbox 360 de Xbox Live** antes de insertar el USB. Microsoft puede banear consolas con exploits activos.

> ⚠ El exploit NO es permanente. No modifica la NAND. Debe repetirse en cada reinicio.

---

## Estructura del USB resultante

```
USB/
├── BadUpdatePayload/     ← exploit + payload
├── Content/              ← perfil de avatar modificado
├── Apps/
│   ├── Aurora/           ← (instalación manual)
│   ├── XeXMenu/          ← (instalación manual)
│   └── NANDFlasher/      ← incluido automáticamente
├── Games/
├── Emulators/
├── Plugins/
└── launch.ini            ← arranque automático de Aurora
```

---

## Pasos después de preparar el USB

1. Copia Aurora a `USB/Apps/Aurora/`
2. **Desconecta la consola de Internet**
3. Inserta el USB en la Xbox 360
4. Enciende la consola — el exploit se ejecuta automáticamente al cargar el perfil de avatar
5. Cuando aparezca la animación de éxito → presiona **BACK**

---

## Generar .app (para distribución)

```bash
chmod +x build.sh
./build.sh
# El .app queda en dist/
```

---

## Créditos

| Proyecto | Autor |
|---|---|
| [BadStick](https://github.com/LxcyDr0p/BadStick) — inspiración y referencia de flujo (versión Windows) | LxcyDr0p |
| [ABadAvatar](https://github.com/shutterbug2000/ABadAvatar) — exploit | shutterbug2000 |
| [XeUnshackle](https://github.com/Byrom90/XeUnshackle) — payload | Byrom90 |
| [FreeMyXe](https://github.com/FreeMyXe/FreeMyXe) — payload alternativo | InvoxiPlayGames |
| Aurora Dashboard — dashboard homebrew | Phoenix Team |
| XeXMenu — administrador de archivos | Team XeDEV |
| [Simple 360 NAND Flasher](https://github.com/Swizzy/XDK_Projects) — backup de NAND | Swizzy |
| [Xbox360BadUpdate](https://github.com/grimdoomer/Xbox360BadUpdate) — exploit original | Grimdoomer |

**Para usuarios de Windows:** usa [BadStick](https://github.com/LxcyDr0p/BadStick) de LxcyDr0p.

---

---

# OQB BadStick Mac — English

> First GUI tool to prepare an ABadAvatar exploit USB on macOS and Linux — no Windows required.

## What it does

OQB BadStick Mac detects your USB drive, formats it FAT32, automatically downloads the [ABadAvatar](https://github.com/shutterbug2000/ABadAvatar) exploit and your chosen payload ([XeUnshackle](https://github.com/Byrom90/XeUnshackle) or [FreeMyXe](https://github.com/FreeMyXe/FreeMyXe)), and leaves the USB ready to run homebrew on an Xbox 360 — no soldering or permanent hardware modification required.

The exploit is **not permanent** — it must be re-run every time the console restarts.

## Requirements

- Python 3.9+ with pip  
  _or: download the `.app` from [Releases](https://github.com/ohquebacan/OQB-BadStick-Mac/releases) (no Python needed)_
- macOS 11+ or Linux with `lsblk` and `udisksctl`
- Internet connection (to download exploits)
- A USB drive of at least 256 MB

## Quick start

```bash
git clone https://github.com/ohquebacan/OQB-BadStick-Mac.git
cd OQB-BadStick-Mac
pip install -r requirements.txt
python main.py
```

## Security warnings

> ⚠ **Back up your NAND before doing anything.** Use the included NAND Flasher.  
> ⚠ **Disconnect your Xbox 360 from Xbox Live** before inserting the USB.  
> ⚠ The exploit is NOT permanent and does NOT modify the NAND.

## Credits

BadStick (Windows original) by [LxcyDr0p](https://github.com/LxcyDr0p/BadStick) · ABadAvatar by shutterbug2000 · XeUnshackle by Byrom90 · FreeMyXe by InvoxiPlayGames · Aurora by Phoenix Team · XeXMenu by Team XeDEV · NAND Flasher by Swizzy · Xbox360BadUpdate exploit by Grimdoomer

**Windows users:** use [BadStick](https://github.com/LxcyDr0p/BadStick).

---

MIT License © 2024 OQB / ohquebacan.com
