#!/usr/bin/env python3
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "data" / "raw" / "126002A12.pdf"
OUT_DIR = ROOT / "assets" / "questions"

# Coordinates are in the original rendered PDF point grid, 595 x 842.
# Each crop avoids the answer marker printed at the left of the official PDF.
CROPS = {
    "12600-A12-001": (2, (110, 70, 190, 100)),
    "12600-A12-004": (2, (280, 192, 302, 218)),
    "12600-A12-005": (2, (204, 238, 386, 282)),
    "12600-A12-006": (2, (112, 320, 202, 340)),
    "12600-A12-008": (2, (392, 363, 452, 386)),
    "12600-A12-011": (2, (405, 486, 468, 502)),
    "12600-A12-012": (2, (417, 520, 462, 565)),
    "12600-A12-013": (2, (430, 580, 482, 598)),
    "12600-A12-014": (2, (392, 617, 452, 646)),
    "12600-A12-015": (2, (421, 662, 454, 692)),
    "12600-A12-017": (2, (378, 747, 452, 768)),
    "12600-A12-018": (3, (404, 45, 468, 68)),
    "12600-A12-019": (3, (112, 116, 206, 158)),
    "12600-A12-020": (3, (454, 158, 494, 190)),
    "12600-A12-022": (3, (112, 278, 190, 308)),
    "12600-A12-030": (3, (112, 634, 208, 670)),
    "12600-A12-031": (3, (300, 672, 326, 710)),
    "12600-A12-032": (4, (300, 42, 328, 86)),
    "12600-A12-033": (4, (112, 160, 160, 208)),
    "12600-A12-043": (4, (112, 576, 522, 665)),
    "12600-A12-044": (4, (112, 684, 488, 776)),
    "12600-A12-045": (5, (112, 42, 302, 116)),
    "12600-A12-048": (5, (112, 196, 270, 232)),
    "12600-A12-051": (5, (306, 322, 368, 350)),
    "12600-A12-052": (5, (180, 378, 438, 398)),
    "12600-A12-053": (5, (180, 402, 535, 442)),
    "12600-A12-054": (5, (168, 462, 336, 514)),
    "12600-A12-055": (5, (112, 530, 492, 586)),
    "12600-A12-056": (5, (198, 622, 488, 684)),
    "12600-A12-057": (5, (286, 724, 522, 774)),
    "12600-A12-058": (6, (112, 64, 484, 118)),
    "12600-A12-059": (6, (182, 162, 470, 198)),
    "12600-A12-060": (6, (350, 224, 540, 294)),
    "12600-A12-061": (6, (300, 322, 520, 356)),
    "12600-A12-062": (6, (160, 394, 462, 452)),
    "12600-A12-063": (6, (170, 462, 370, 500)),
    "12600-A12-064": (6, (145, 518, 390, 543)),
    "12600-A12-065": (6, (155, 566, 370, 602)),
    "12600-A12-067": (6, (140, 676, 405, 718)),
    "12600-A12-068": (6, (112, 710, 548, 770)),
    "12600-A12-069": (7, (145, 58, 330, 90)),
    "12600-A12-070": (7, (112, 108, 330, 142)),
    "12600-A12-079": (7, (178, 576, 424, 610)),
    "12600-A12-095": (8, (128, 470, 190, 505)),
    "12600-A12-305": (22, (112, 475, 150, 502)),
}


def render_page(reader: PdfReader, page_number: int, temp_dir: Path) -> Image.Image:
    single_page_pdf = temp_dir / f"page-{page_number:02d}.pdf"
    single_page_png = temp_dir / f"page-{page_number:02d}.png"
    writer = PdfWriter()
    writer.add_page(reader.pages[page_number - 1])
    with single_page_pdf.open("wb") as handle:
        writer.write(handle)

    subprocess.run(
        ["sips", "-s", "format", "png", "-z", "1684", "1190", str(single_page_pdf), "--out", str(single_page_png)],
        check=True,
        capture_output=True,
    )
    image = Image.open(single_page_png).convert("RGBA")
    white = Image.new("RGBA", image.size, "white")
    white.alpha_composite(image)
    return white.convert("RGB")


def crop_box(box: tuple[int, int, int, int], scale: int = 2) -> tuple[int, int, int, int]:
    return tuple(value * scale for value in box)


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(f"Missing {PDF_PATH}")
    if shutil.which("sips") is None:
        raise SystemExit("This script uses macOS sips to render single-page PDF crops.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(PDF_PATH))
    rendered: dict[int, Image.Image] = {}

    with tempfile.TemporaryDirectory() as dirname:
        temp_dir = Path(dirname)
        for question_id, (page_number, box) in CROPS.items():
            if page_number not in rendered:
                rendered[page_number] = render_page(reader, page_number, temp_dir)
            crop = rendered[page_number].crop(crop_box(box))
            crop.save(OUT_DIR / f"{question_id}.png", optimize=True)

    print(f"Wrote {len(CROPS)} question images to {OUT_DIR}")


if __name__ == "__main__":
    main()
