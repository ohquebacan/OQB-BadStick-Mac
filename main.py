import os
import sys

# Locate assets whether running from source or PyInstaller bundle
if getattr(sys, "frozen", False):
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

_ICON_PATH = os.path.join(_BASE, "assets", "icon.png")

# Generate placeholder icon if missing (first run from source)
if not os.path.exists(_ICON_PATH):
    from app.utils.helpers import generate_icon
    generate_icon(_ICON_PATH)

from app.ui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
