# Unlimited OCR GGUF Document Test

Isolated repository for testing `sahilchachra/Unlimited-OCR-GGUF` against local aviation/maintenance PDFs.

The tested model path is:

- `Unlimited-OCR-Q8_0.gguf`
- `mmproj-Unlimited-OCR-F16.gguf`
- DeepSeek-OCR-aware `llama.cpp` branch with `llama-mtmd-cli`

This is intentionally separate from the PaddleOCR FastAPI service.

## What This Repo Provides

- Single-page OCR runner.
- Full-PDF batch runner.
- PDF page renderer.
- Side-by-side comparison report generator.
- Setup and troubleshooting guide.
- Reference comparison reports for:
  - `TaskStatusReport`
  - `EngineData1`

## Quick Run

From this folder:

```bash
python scripts/batch_unlimited_ocr_pdf.py \
  --pdf ../pdf_data/TaskStatusReport.pdf \
  --llama-bin third_party/llama.cpp/build/bin/llama-mtmd-cli \
  --model models/unlimited_ocr/Unlimited-OCR-Q8_0.gguf \
  --mmproj models/unlimited_ocr/mmproj-Unlimited-OCR-F16.gguf \
  --out runs/TaskStatusReport_full \
  --dpi 200 \
  --tokens 2048 \
  --gpu-layers 5
```

Generate a visual comparison:

```bash
python scripts/generate_comparison_report.py \
  --title "Task Status Report" \
  --pages-dir runs/TaskStatusReport_full/pages \
  --ocr-dir runs/TaskStatusReport_full/ocr \
  --out comparisons/task_status_report.html
```

Open:

```text
comparisons/task_status_report.html
```

## Setup

See [SETUP_STEPS.md](SETUP_STEPS.md).
