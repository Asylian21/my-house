"""Check real PDF paper dimensions and vector calibration; does not rescale PDFs."""
import json
import logging
from pathlib import Path

import pdfplumber

logging.getLogger('pdfminer').setLevel(logging.ERROR)
out = Path(__file__).resolve().parents[2] / 'output/pdf/construction-cbb'
register = json.loads((out / 'drawing-register.json').read_text())
mm_to_pt = 72 / 25.4
report = {}
for variant in ('color', 'mono'):
    measurements = []
    with pdfplumber.open(out / f'DOM-CBB-A1-{variant}.pdf') as pdf:
        assert len(pdf.pages) == len(register)
        for index, page in enumerate(pdf.pages):
            # Chromium rounds paper height to a pixel; tolerance < 0.2 paper mm.
            assert abs(page.width / mm_to_pt - 841) < 0.2
            assert abs(page.height / mm_to_pt - 594) < 0.2
            content = page.extract_text() or ''
            assert len(content) > 100, f'Empty page {index + 1}'
            assert 'NEVYDANÉ NA REALIZÁCIU' in content
            if register[index]['id'] == 'D1.1.002-C-RE':
                # Existing five-metre bar: five adjacent 20 mm paper segments.
                bars = [r for r in page.rects
                        if abs(r['width'] / mm_to_pt - 20) < 0.01
                        and abs(r['height'] / mm_to_pt - 2.2) < 0.01
                        and abs(r['top'] / mm_to_pt - 495) < 0.02]
                positions = sorted({round(r['x0'] / mm_to_pt, 5) for r in bars})
                assert len(positions) == 5
                assert all(abs(b - a - 20) < 0.01
                           for a, b in zip(positions, positions[1:]))
                measurements.append({'sheet': register[index]['id'],
                                     'calibration_paper_mm': bars[0]['width'] / mm_to_pt})
                continue
            bars = [p for p in page.lines
                    if abs(p['width'] / mm_to_pt - 20) < 0.01
                    and abs(p['top'] / mm_to_pt - 498) < 0.02]
            assert bars, f'Missing / incorrect scale bar on {index + 1}'
            measurements.append({'sheet': register[index]['id'],
                                 'calibration_paper_mm': bars[0]['width'] / mm_to_pt})
    report[variant] = measurements
(out / 'pdf-verification.json').write_text(json.dumps(report, indent=2))
print(f'PASS: {len(register)} pages per PDF, A1 media boxes, text and 20 mm vector calibration.')
