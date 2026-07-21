from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


PROMPT = (
    "<|grounding|>Extract every table from this document as Markdown tables. "
    "Preserve row order, column order, merged cells, dates, numbers, and all visible text. "
    "Do not summarize."
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llama-bin", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--mmproj", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--tokens", type=int, default=8192)
    parser.add_argument("--device", default=None)
    parser.add_argument("--gpu-layers", default=None)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(args.llama_bin),
        "-m",
        str(args.model),
        "--mmproj",
        str(args.mmproj),
        "--image",
        str(args.image),
        "--jinja",
        "--temp",
        "0",
        "--repeat-penalty",
        "1.05",
        "-n",
        str(args.tokens),
        "-p",
        args.prompt,
    ]
    if args.device:
        cmd.extend(["--device", args.device])
    if args.gpu_layers:
        cmd.extend(["--gpu-layers", args.gpu_layers])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    args.out.write_text(proc.stdout, encoding="utf-8")
    args.out.with_suffix(args.out.suffix + ".log").write_text(proc.stderr, encoding="utf-8")
    print(f"returncode={proc.returncode}")
    print(args.out)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
