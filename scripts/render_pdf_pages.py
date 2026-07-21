from __future__ import annotations

import argparse
from pathlib import Path

import fitz


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(args.pdf)
    matrix = fitz.Matrix(args.dpi / 72, args.dpi / 72)
    for index in range(doc.page_count):
        page = doc.load_page(index)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        path = args.out / f"page_{index + 1:03d}_{args.dpi}dpi.png"
        pix.save(path)
        print(path)
    doc.close()


if __name__ == "__main__":
    main()
