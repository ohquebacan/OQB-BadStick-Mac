import os
import sys


def get_assets_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "assets")
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "assets",
    )


def generate_icon(output_path: str) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (512, 512), color="#107C10")
        draw = ImageDraw.Draw(img)

        font = None
        candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        for fp in candidates:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, 180)
                    break
                except Exception:
                    continue

        if font is None:
            font = ImageFont.load_default()

        text = "360"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (512 - w) // 2 - bbox[0]
        y = (512 - h) // 2 - bbox[1]
        draw.text((x, y), text, fill="white", font=font)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        return True
    except Exception:
        return False


def format_bytes(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"
