import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error('Usage: node compile-svg-pdf.mjs input.svg output.pdf');
const svg = await readFile(input, 'utf8');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>@page{size:841mm 594mm;margin:0}html,body{margin:0;padding:0}body>svg{display:block;width:841mm;height:594mm}*{print-color-adjust:exact;-webkit-print-color-adjust:exact}</style></head><body>${svg}</body></html>`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: output, width: '841mm', height: '594mm', printBackground: true,
    preferCSSPageSize: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
} finally {
  await browser.close();
}
