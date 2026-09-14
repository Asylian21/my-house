# Private C/B/B document library

Run `node scripts/document-library/generate.mjs` after regenerating the construction drawing set. The same command is suitable before dev/build: unchanged inputs and complete assets take the checked cache path. `--force` rebuilds; `--check` validates freshness without writing. Missing private source PDFs or assets never silently become an empty or stale library.

The generator reads the existing 25-page color/mono PDFs, matching HTML, register, snapshot and verification results from `output/pdf/construction-cbb/`. It copies the curated Markdown reports without rewriting their content. It writes a trackable `lib/document-library.generated.json` and local assets below `public/documents/`. No source PDF is overwritten. Generation itself does not upload or publish.

For source-only hosting builds, `npm run docs:publish-snapshot` verifies the local export and writes `lib/document-library.snapshot.json`. Commit that snapshot, the generated manifest and exactly the `public/documents` assets listed in its `assets` map (the directory remains ignored for unrelated cache/QA files). `npm run docs:library` uses the full local generator when source PDFs are available. In a clean remote checkout it instead verifies the committed snapshot, source hashes and every linked asset using Node alone. Missing files or changed sources fail the build; `--force` requires the original local sources. Refresh the snapshot and stage the new asset list after regenerating documents.

The current library has 75 records, including the existing seven-page A4 H200 PDF as a reference export linked to the current Markdown reports. Its `pagePreviewUrls` contains all seven SVG pages in PDF order; `previewUrl` is the first page. Poppler converts the PDF vectors directly, retaining each source page box and embedded glyph outlines. A Markdown-only update reuses the verified drawing/image assets and refreshes report content and source metadata.

Each of the 50 sheet records is a separate one-page PDF, with `sheetIndex` 1–25 and `bundleId`. Both bundle records retain all 25 A1 pages. SVG previews preserve the exact source SVG plus the entire original HTML style block; JPEG thumbnails are rendered from the actual PDFs with Poppler. The UI can page through the full bundles using lightweight sheet previews.

Pikepdf optimizes PDF streams and object storage losslessly; pypdf additionally merges identical resource objects without rasterizing. Twenty-four sheets in each color retain the source decoded content-stream SHA-256 values, MediaBox, CropBox and rotation, including their standalone exports.

ZA-03 needs a separate vector optimization: the original Chromium PDF repeats the concrete pattern for every grid face and alone exceeds 100 MB. `optimize_svg.py` preserves every original non-pattern geometry/text attribute and paints the same pattern once through the union clip of each continuous face group. `compile-svg-pdf.mjs` prints this vector SVG with the project's Playwright/Chromium. The original SVG remains the library preview. The online PDF is a derivative with unchanged geometry, dimensions and text; tiny transparent-pattern compositing/antialiasing differences mean its raster is not bit-identical. Every export compares all PDF word positions within 0.002 points and 60 dpi renders, with bounded raster differences recorded in `.build-state.json`. The optimized ZA-03 replaces only its corresponding page in each online bundle. The original source PDFs are never modified.

All linked assets must be smaller than 25,000,000 bytes. A complete new generation is built separately, checked, then exposed under its own versioned directory; only afterwards is the manifest atomically replaced. Former generated files are removed by the previous cache's explicit ownership list. Timestamps for source documents come from their original file mtimes, never the time they were copied. The visible revision and searchable load values come from the source client brief and the verified R7/SA30 data.

## Runtime

The Node wrapper discovers the Codex bundled Python and Poppler runtime when available. Overrides: `DOCUMENT_LIBRARY_PYTHON` for Python and `DOCUMENT_LIBRARY_PYTHON_PACKAGES` for a dependency directory. Otherwise it uses `python3` and tools on `PATH`. Python 3.11 or newer is required.

Prepare the small isolated dependency directory once (the generator does not install packages automatically):

```sh
uv pip install --python /path/to/python3 --target "$HOME/.cache/dom-document-library/python" -r scripts/document-library/requirements.txt
```

The required Python packages are pinned in `requirements.txt`. Poppler provides `pdftoppm`, `pdftotext` and `pdftocairo`. The existing project Playwright/Chromium installation prints the optimized vector page. No PyMuPDF dependency is required.

## Content and evidence

- `drawings`: complete sets and all individual sheets, always `coordination`.
- `reports`: all current construction reports, active design, current H200/SA30, kitchen and office decisions.
- `images`: four standalone foundation axonometry PNG/SVG files, color and mono.
- `model`: source snapshot, drawing register, verified nominal partition mass calculation, and client brief.
- `archive`: only the explicitly superseded 274 mm acoustic-wall study.

The source claims remain bounded: no drawing is promoted to approved construction, a verified mass calculation is not a slab-capacity check, and the reported cast extent is not a survey. The current assembly choice is H200; the active thinner-options report remains under current acoustics.

The cache hashes all source inputs, the generated manifest and every linked asset. A stale checked-in manifest with missing ignored assets fails `--check`; the normal command rebuilds from available private inputs. A source change during a long export fails rather than committing mixed manifest metadata.
