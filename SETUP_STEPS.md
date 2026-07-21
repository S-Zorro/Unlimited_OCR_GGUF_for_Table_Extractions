# Unlimited-OCR GGUF Isolated Setup Steps

This is an isolated test for:

- Hugging Face repo: `sahilchachra/Unlimited-OCR-GGUF`
- Model: `Unlimited-OCR-Q8_0.gguf`
- Vision projector: `mmproj-Unlimited-OCR-F16.gguf`

This test is separate from the PaddleOCR/FastAPI repository.

## Current Local Notes

Checked locally:

- `git` is available.
- `cmake` is available.
- `g++` is available.
- `nvidia-smi` failed to communicate with the NVIDIA driver in the current session.
- `huggingface-cli` was missing initially.
- `huggingface-hub` was installed with pip, which installed the newer `hf` CLI.
- A model download was started, then manually stopped by request.

Before expecting GPU acceleration, fix/verify NVIDIA driver visibility:

```bash
nvidia-smi
```

If this still fails, build and test CPU-only first.

## Folder Layout

Use this isolated folder:

```text
unlimited_ocr_gguf_test/
  models/
    unlimited_ocr/
  runs/
  scripts/
  third_party/
```

## 1. Install Python Helper

```bash
python -m pip install --user huggingface-hub
```

Verify:

```bash
~/.local/bin/hf --help
```

## 2. Download Model Files

From inside `unlimited_ocr_gguf_test/`:

```bash
~/.local/bin/hf download sahilchachra/Unlimited-OCR-GGUF \
  Unlimited-OCR-Q8_0.gguf \
  mmproj-Unlimited-OCR-F16.gguf \
  --local-dir models/unlimited_ocr
```

Expected files:

```text
models/unlimited_ocr/Unlimited-OCR-Q8_0.gguf
models/unlimited_ocr/mmproj-Unlimited-OCR-F16.gguf
```

Check:

```bash
ls -lh models/unlimited_ocr
```

## 3. Build DeepSeek-OCR-Aware llama.cpp

The model card says stock llama.cpp may not support this model yet. Build the PR branch listed by the model card.

From inside `unlimited_ocr_gguf_test/`:

```bash
cd third_party
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
git fetch origin pull/24975/head:pr24975
git checkout pr24975
```

### GPU Build

Use this only after `nvidia-smi` works:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build build -j --target llama-mtmd-cli llama-server
```

### CPU Build

Use this if NVIDIA driver/CUDA is not visible:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j --target llama-mtmd-cli llama-server
```

Expected binary:

```text
third_party/llama.cpp/build/bin/llama-mtmd-cli
```

Check:

```bash
third_party/llama.cpp/build/bin/llama-mtmd-cli --help
```

## 4. Render A PDF Page

The isolated folder includes:

```text
scripts/render_pdf_pages.py
```

Render `ADList1.pdf`:

```bash
python scripts/render_pdf_pages.py ../pdf_data/ADList1.pdf \
  --out runs/ADList1/pages \
  --dpi 200
```

Start with 200 DPI. Try 300 DPI only if small text is missed:

```bash
python scripts/render_pdf_pages.py ../pdf_data/ADList1.pdf \
  --out runs/ADList1/pages_300dpi \
  --dpi 300
```

## 5. Run One Page

The isolated folder includes:

```text
scripts/run_page.py
```

Run page 1:

```bash
python scripts/run_page.py \
  --llama-bin third_party/llama.cpp/build/bin/llama-mtmd-cli \
  --model models/unlimited_ocr/Unlimited-OCR-Q8_0.gguf \
  --mmproj models/unlimited_ocr/mmproj-Unlimited-OCR-F16.gguf \
  --image runs/ADList1/pages/page_001_200dpi.png \
  --out runs/ADList1/ocr/page_001.md
```

The runner passes `--jinja` because this model's custom chat template is not supported by the default llama.cpp template path.

If CUDA is not visible or you see `no CUDA-capable device is detected`, force CPU:

```bash
python scripts/run_page.py \
  --llama-bin third_party/llama.cpp/build/bin/llama-mtmd-cli \
  --model models/unlimited_ocr/Unlimited-OCR-Q8_0.gguf \
  --mmproj models/unlimited_ocr/mmproj-Unlimited-OCR-F16.gguf \
  --image runs/ADList1/pages/page_001_200dpi.png \
  --out runs/ADList1/ocr/page_001_cpu.md \
  --device none \
  --gpu-layers 0
```

Output:

```text
runs/ADList1/ocr/page_001.md
runs/ADList1/ocr/page_001.md.log
```

## 6. Useful Prompts

Default table-focused prompt:

```text
<|grounding|>Extract every table from this document as Markdown tables. Preserve row order, column order, merged cells, dates, numbers, and all visible text. Do not summarize.
```

Layout Markdown prompt from model card:

```text
<|grounding|>Convert the document to markdown.
```

Raw OCR prompt:

```text
Free OCR.
```

To override the prompt:

```bash
python scripts/run_page.py \
  --llama-bin third_party/llama.cpp/build/bin/llama-mtmd-cli \
  --model models/unlimited_ocr/Unlimited-OCR-Q8_0.gguf \
  --mmproj models/unlimited_ocr/mmproj-Unlimited-OCR-F16.gguf \
  --image runs/ADList1/pages/page_001_200dpi.png \
  --out runs/ADList1/ocr/page_001_layout.md \
  --prompt "<|grounding|>Convert the document to markdown."
```

## 7. Batch Run A Full PDF

The previous batch script exists here:

```text
scripts/batch_unlimited_ocr_pdf.py
```

Run:

```bash
python scripts/batch_unlimited_ocr_pdf.py \
  --pdf ../pdf_data/ADList1.pdf \
  --llama-bin third_party/llama.cpp/build/bin/llama-mtmd-cli \
  --model models/unlimited_ocr/Unlimited-OCR-Q8_0.gguf \
  --mmproj models/unlimited_ocr/mmproj-Unlimited-OCR-F16.gguf \
  --out runs/ADList1 \
  --dpi 200
```

Combined output:

```text
runs/ADList1/combined.md
```

## 8. Evaluation Checklist

For each output page, check:

- Are all tables present?
- Is row order preserved?
- Is column order preserved?
- Are dates exact?
- Are IDs exact?
- Are numeric values exact?
- Are merged cells handled acceptably?
- Did the output hallucinate headings or missing cells?
- Did it truncate before the table ended?
- Did it repeat content?

If it truncates:

```bash
python scripts/run_page.py ... --tokens 12000
```

If it repeats, edit `scripts/run_page.py` and raise:

```text
--repeat-penalty 1.10
```

## 9. If GPU Memory Is Tight

Try:

- CPU build first.
- 200 DPI instead of 300 DPI.
- One page at a time.
- Crop table regions manually and run the cropped images.
- Reduce image resolution.

If GPU support is available in `llama-mtmd-cli`, check its `--help` output for GPU layer flags and tune conservatively for 6GB VRAM.

## 10. Runtime Error: `this custom template is not supported, try using --jinja`

If the log contains:

```text
terminate called after throwing an instance of 'std::runtime_error'
what(): this custom template is not supported, try using --jinja
```

Rerun with `--jinja`. The local `scripts/run_page.py` now adds this automatically.

Manual command shape:

```bash
third_party/llama.cpp/build/bin/llama-mtmd-cli \
  -m models/unlimited_ocr/Unlimited-OCR-Q8_0.gguf \
  --mmproj models/unlimited_ocr/mmproj-Unlimited-OCR-F16.gguf \
  --image runs/ADList1/pages/page_001_200dpi.png \
  --jinja \
  --temp 0 \
  --repeat-penalty 1.05 \
  -n 8192 \
  -p "<|grounding|>Extract every table from this document as Markdown tables. Preserve row order, column order, merged cells, dates, numbers, and all visible text. Do not summarize."
```

## 11. Build Error: `std_function.h parameter packs not expanded`

If CUDA build fails with an error like:

```text
/usr/include/c++/11/bits/std_function.h:435:145: error: parameter packs not expanded with ‘...’
```

This is usually a CUDA `nvcc` plus GCC/libstdc++ compatibility problem, not a llama.cpp source problem.

First check:

```bash
nvcc --version
gcc --version
g++ --version
```

On Ubuntu 22.04, GCC/G++ 11 is common. Some CUDA toolkit versions fail with GCC 11. Use GCC/G++ 10 as the CUDA host compiler:

```bash
sudo apt update
sudo apt install gcc-10 g++-10
```

Then rebuild from a clean CMake directory:

```bash
cd unlimited_ocr_gguf_test/third_party/llama.cpp
rm -rf build
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-10 \
  -DCMAKE_CUDA_ARCHITECTURES=89
cmake --build build -j 1 --target llama-mtmd-cli
```

Why `89`: RTX 4050 is Ada Lovelace, compute capability 8.9. This avoids compiling many unnecessary older CUDA architectures and reduces build time/memory.

If CMake or nvcc says architecture `89` is unsupported, your CUDA toolkit is too old for RTX 4050. Install a newer CUDA toolkit, preferably CUDA 12.x, then rebuild.

CPU fallback:

```bash
cd unlimited_ocr_gguf_test/third_party/llama.cpp
rm -rf build
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 2 --target llama-mtmd-cli
```

## 12. Source

Model card:

https://huggingface.co/sahilchachra/Unlimited-OCR-GGUF

Files:

https://huggingface.co/sahilchachra/Unlimited-OCR-GGUF/tree/main
