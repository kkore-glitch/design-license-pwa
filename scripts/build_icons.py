#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/kkore/Pictures/Photos Library.photoslibrary/originals/0/068D4211-9BCA-4713-BF68-FBA30202F770.jpeg")
ASSET_DIR = ROOT / "assets"


def book_mask(size: tuple[int, int]) -> Image.Image:
    width, height = size
    # The mask follows the book mockup outline and preserves all white artwork
    # printed on the cover. It only removes the outside page background.
    points = [
        (0.012, 0.024),
        (0.086, 0.004),
        (0.558, 0.026),
        (0.510, 0.135),
        (0.560, 0.188),
        (0.710, 0.193),
        (0.708, 0.224),
        (0.922, 0.195),
        (0.962, 0.139),
        (0.922, 0.040),
        (0.999, 0.045),
        (0.999, 0.962),
        (0.078, 0.999),
        (0.000, 0.962),
        (0.000, 0.030),
    ]
    scaled = [(round(x * width), round(y * height)) for x, y in points]
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(scaled, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(0.7))


def transparent_cutout() -> Image.Image:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source image: {SOURCE}")
    source = Image.open(SOURCE).convert("RGBA")
    alpha = book_mask(source.size)
    source.putalpha(alpha)
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit("Could not isolate icon foreground")
    return source.crop(bbox)


def square_icon(cutout: Image.Image, size: int, background: tuple[int, int, int, int] | None = None) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), background or (255, 255, 255, 0))
    max_width = int(size * 0.9)
    max_height = int(size * 0.9)
    icon = cutout.copy()
    icon.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    x = (size - icon.width) // 2
    y = (size - icon.height) // 2
    canvas.alpha_composite(icon, (x, y))
    return canvas


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    cutout = transparent_cutout()
    cutout.save(ASSET_DIR / "icon-source-cutout.png", optimize=True)
    square_icon(cutout, 192).save(ASSET_DIR / "icon-192.png", optimize=True)
    square_icon(cutout, 512).save(ASSET_DIR / "icon-512.png", optimize=True)
    square_icon(cutout, 512, (247, 244, 234, 255)).save(ASSET_DIR / "icon-maskable-512.png", optimize=True)
    square_icon(cutout, 180, (247, 244, 234, 255)).save(ASSET_DIR / "apple-touch-icon.png", optimize=True)
    print("Wrote PWA icons to assets/")


if __name__ == "__main__":
    main()
