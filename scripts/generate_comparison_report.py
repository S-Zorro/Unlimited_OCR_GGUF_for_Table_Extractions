from __future__ import annotations

import argparse
import base64
import html
import re
from pathlib import Path


def image_to_data_uri(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else "png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def page_key(path: Path) -> str:
    match = re.search(r"page_(\d+)", path.stem)
    return match.group(1) if match else path.stem


def markdown_to_review_html(markdown: str) -> str:
    escaped = html.escape(markdown)
    # Preserve extracted HTML table snippets as rendered tables where possible while keeping
    # the raw markdown visible below. This is intentionally conservative for review.
    rendered_tables = []
    for table in re.findall(r"(<table>.*?</table>)", markdown, flags=re.S):
        rendered_tables.append(table)
    tables_html = "\n".join(rendered_tables)
    raw_html = f"<pre>{escaped}</pre>"
    if tables_html:
        return f"<div class=\"tables\">{tables_html}</div><details open><summary>Raw output</summary>{raw_html}</details>"
    return raw_html


def build_report(title: str, pages_dir: Path, ocr_dir: Path) -> str:
    images = {page_key(path): path for path in sorted(pages_dir.glob("page_*.png"))}
    markdowns = {page_key(path): path for path in sorted(ocr_dir.glob("page_*.md"))}
    keys = sorted(set(images) | set(markdowns), key=lambda value: int(value) if value.isdigit() else value)

    sections = []
    for key in keys:
        image_path = images.get(key)
        md_path = markdowns.get(key)
        image_html = (
            f"<img src=\"{image_to_data_uri(image_path)}\" alt=\"Page {key}\">"
            if image_path
            else "<p class=\"missing\">No rendered page image found.</p>"
        )
        markdown = md_path.read_text(encoding="utf-8") if md_path else "No OCR markdown found."
        sections.append(
            "\n".join(
                [
                    f"<section class=\"page\"><h2>Page {int(key) if key.isdigit() else key}</h2>",
                    "<div class=\"comparison\">",
                    f"<div class=\"pane image-pane\">{image_html}</div>",
                    f"<div class=\"pane markdown-pane\">{markdown_to_review_html(markdown)}</div>",
                    "</div></section>",
                ]
            )
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --border: #d9dee7;
      --muted: #667085;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    header {{
      padding: 20px 24px;
      border-bottom: 1px solid var(--border);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 2;
    }}
    h1 {{ margin: 0; font-size: 20px; }}
    h2 {{ margin: 24px 24px 12px; font-size: 16px; color: var(--muted); }}
    .comparison {{
      display: grid;
      grid-template-columns: minmax(360px, 1fr) minmax(360px, 1fr);
      gap: 12px;
      padding: 0 24px 24px;
      align-items: start;
    }}
    .pane {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: auto;
      max-height: 86vh;
    }}
    .image-pane {{
      padding: 12px;
      text-align: center;
    }}
    img {{
      max-width: 100%;
      height: auto;
      border: 1px solid var(--border);
    }}
    .markdown-pane {{
      padding: 12px;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 12px;
      line-height: 1.45;
      margin: 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 16px;
      font-size: 12px;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 4px 6px;
      vertical-align: top;
    }}
    details {{
      border-top: 1px solid var(--border);
      padding-top: 10px;
    }}
    summary {{
      cursor: pointer;
      color: var(--muted);
      margin-bottom: 10px;
    }}
    .missing {{
      color: #b42318;
      font-weight: 600;
    }}
    @media (max-width: 900px) {{
      .comparison {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header><h1>{html.escape(title)}</h1></header>
  {''.join(sections)}
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create side-by-side PDF image vs OCR markdown HTML.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--pages-dir", type=Path, required=True)
    parser.add_argument("--ocr-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_report(args.title, args.pages_dir, args.ocr_dir), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
