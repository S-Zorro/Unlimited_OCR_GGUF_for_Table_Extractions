from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from render_pdf_pages import main as _render_main  # noqa: F401
from run_page import PROMPT


def render_pages(pdf: Path, out: Path, dpi: int) -> list[Path]:
    import fitz

    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    pages: list[Path] = []
    for index in range(doc.page_count):
        page = doc.load_page(index)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        path = out / f"page_{index + 1:03d}_{dpi}dpi.png"
        pix.save(path)
        pages.append(path)
    doc.close()
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a PDF and run Unlimited-OCR per page.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--llama-bin", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--mmproj", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--tokens", type=int, default=2048)
    parser.add_argument("--device", default=None)
    parser.add_argument("--gpu-layers", default="5")
    args = parser.parse_args()

    pages_dir = args.out / "pages"
    ocr_dir = args.out / "ocr"
    ocr_dir.mkdir(parents=True, exist_ok=True)
    pages = render_pages(args.pdf, pages_dir, args.dpi)

    for page in pages:
        out_path = ocr_dir / f"{page.stem}.md"
        command = [
            "python",
            "scripts/run_page.py",
            "--llama-bin",
            str(args.llama_bin),
            "--model",
            str(args.model),
            "--mmproj",
            str(args.mmproj),
            "--image",
            str(page),
            "--out",
            str(out_path),
            "--prompt",
            args.prompt,
            "--tokens",
            str(args.tokens),
        ]
        if args.device:
            command.extend(["--device", args.device])
        if args.gpu_layers:
            command.extend(["--gpu-layers", args.gpu_layers])
        print(f"Running {page.name}")
        subprocess.run(command, check=True)

    combined = args.out / "combined.md"
    combined.write_text(
        "\n\n".join(
            f"<!-- {path.name} -->\n\n{path.read_text(encoding='utf-8')}"
            for path in sorted(ocr_dir.glob("*.md"))
        ),
        encoding="utf-8",
    )
    print(combined)


if __name__ == "__main__":
    main()
