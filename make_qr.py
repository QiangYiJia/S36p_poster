#!/usr/bin/env python3
from pathlib import Path

import qrcode
import qrcode.image.svg


URL = "https://qiangyijia.github.io/S36p_poster/"
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "qr"
PNG_PATH = OUT_DIR / "S36p_poster_QR.png"
SVG_PATH = OUT_DIR / "S36p_poster_QR.svg"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=24,
        border=4,
    )
    qr.add_data(URL)
    qr.make(fit=True)

    png = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    png.save(PNG_PATH)

    svg_factory = qrcode.image.svg.SvgPathImage
    svg = qr.make_image(image_factory=svg_factory)
    svg.save(SVG_PATH)

    print(URL)
    print(PNG_PATH)
    print(SVG_PATH)


if __name__ == "__main__":
    main()
