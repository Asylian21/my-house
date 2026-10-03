// Local evidence gallery. Original native PNGs remain untouched.
// node scripts/unreal/exterior-gallery.mjs [validation-output-directory]
import { readFile, readdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = resolve(root, process.argv[2] ?? 'output/unreal/exterior-validation-20260926-r1');
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const phases = new Set(['before-exterior', 'after-exterior', 'final-exterior']);
const sceneNames = [
  ['street', 'Ulica', 'Dom a jeho uličný priestor'],
  ['terrace', 'Terasa', 'Terasa, bazén a záhrada pri dome'],
  ['garden', 'Záhrada', 'Detail priestorovej výsadby a záhonov'],
  ['lawn-detail', 'Trávnik zblízka', 'Skutočné ohnuté listy koseného trávnika'],
  ['lawn-edge', 'Hrana trávnika', 'Nadväznosť krátkeho porastu na pôvodné povrchy'],
  ['neighborhood', 'Susedstvo', 'Nadväznosť na okolité pozemky'],
  ['vineyard', 'Vinohrad', 'Riadky výsadby za pozemkom'],
  ['parcel', 'Parcely', 'Hranice a okraje pozemkov'],
  ['siteaerial', 'Nadhľad', 'Dom v širšom okolí'],
  ['canopy-close', 'Koruny zblízka', 'Detail listov, vetiev a kontaktu so zemou'],
  ['canopy-floor', 'Pod stromami', 'Koreňové nábehy, opadané listy a prirodzený podrast'],
  ['canopy-lod', 'Koruny v diaľke', 'Rovnaká skupina stromov z väčšej vzdialenosti'],
  ['canopy-grove', 'Háj pri obci', 'Existujúca skupina korún v širšom okolí'],
];

async function summaries(directory) {
  const found = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) found.push(...await summaries(path));
    else if (entry.isFile() && entry.name === 'summary.json') found.push(path);
  }
  return found.sort();
}

function localPath(path) {
  const result = relative(output, path);
  if (!result || result.startsWith(`..${sep}`) || result === '..' || isAbsolute(result)) {
    throw new Error('Evidence is outside the gallery directory');
  }
  return result.split(sep).map(encodeURIComponent).join('/');
}

function pngPixels(bytes) {
  if (bytes.length < 24 || !bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    throw new Error('Capture is not a PNG');
  }
  return [bytes.readUInt32BE(16), bytes.readUInt32BE(20)];
}

function vector(value, count) {
  return Array.isArray(value) && value.length === count && value.every(Number.isFinite) ? value : null;
}

// Only explicit reviews bound to a native suite and package affect status.
const reviews = [], reviewWarnings = [];
function normalizeReview(receipt, path) {
  const status = receipt.status === 'not-accepted' ? 'rejected'
    : receipt.status === 'exterior-visually-reviewed' ? 'accepted' : null;
  const suites = receipt.nativeSuites ?? [{ path: receipt.nativeSuite, sha256: receipt.nativeSuiteSha256 }];
  if (!status || !/^[a-f0-9]{64}$/.test(receipt.packageSha256 ?? '') || !Array.isArray(suites) || !suites.length
      || suites.some(s => typeof s.path !== 'string' || !s.path || !/^[a-f0-9]{64}$/.test(s.sha256 ?? ''))
      || (status === 'accepted' && (typeof receipt.verdict !== 'string' || !receipt.verdict.trim()))) {
    throw new Error('Neplatný stav, verdikt alebo väzba na kontrolné súčty série a balíka.');
  }
  return { status, packageSha256: receipt.packageSha256, path: localPath(path),
    suites: suites.map(s => ({ path: resolve(isAbsolute(s.path) ? s.path : s.path.startsWith('qa/') ? output : root, s.path), sha256: s.sha256 })),
    evaluatedAt: receipt.evaluatedAt ?? receipt.reviewedAt ?? receipt.generatedAt ?? '',
    verdict: typeof receipt.verdict === 'string' ? receipt.verdict.trim() : '',
    findings: Array.isArray(receipt.visualFindings) ? receipt.visualFindings.filter(v => typeof v === 'string') : [] };
}
for (const entry of (await readdir(output, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
  if (!entry.isFile() || !/^exterior-r[0-9]+[a-z]?-(?:rejected-)?review(?:-r[0-9]+)?\.json$/.test(entry.name)) continue;
  try {
    reviews.push(normalizeReview(JSON.parse(await readFile(resolve(output, entry.name), 'utf8')), resolve(output, entry.name)));
  } catch (error) {
    reviewWarnings.push(entry.name + ': hodnotenie sa nepodarilo overiť. ' + error.message);
  }
}
function reviewFor(summaryPath, summarySha256, packageSha256) {
  const matches = reviews.filter(r => r.packageSha256 === packageSha256
    && r.suites.some(s => s.path === summaryPath && s.sha256 === summarySha256));
  // A rejection wins any conflicting receipts; no implicit acceptance upgrade.
  return matches.sort((a, b) => Number(b.status === 'rejected') - Number(a.status === 'rejected')
    || b.evaluatedAt.localeCompare(a.evaluatedAt))[0] ?? null;
}

const captures = [], omitted = [];
const seen = new Set();
for (const summaryPath of await summaries(resolve(output, 'qa'))) {
  const summaryBytes = await readFile(summaryPath);
  const summary = JSON.parse(summaryBytes.toString('utf8'));
  const review = reviewFor(summaryPath, sha256(summaryBytes), summary.packageReportSha256);
  for (const row of summary.results ?? []) {
    const series = row.phase ?? summary.phase;
    const phase = [...phases].find(value => series === value || series?.startsWith(`${value}-`));
    if (!phase || row.motion !== 'static') continue;
    try {
      if (!row.evidence) throw new Error('Evidence directory is missing');
      const directory = isAbsolute(row.evidence) ? row.evidence : resolve(output, row.evidence);
      localPath(directory);
      if (seen.has(directory)) continue;
      const imagePath = resolve(directory, 'capture.png');
      const runtimePath = resolve(directory, 'runtime.json');
      const [image, runtimeBytes] = await Promise.all([readFile(imagePath), readFile(runtimePath)]);
      const runtime = JSON.parse(runtimeBytes.toString('utf8'));
      if (runtime.rhi !== 'Metal') throw new Error('Runtime does not confirm Metal');
      if (!row.screenshotSha256 || sha256(image) !== row.screenshotSha256) throw new Error('Capture SHA256 differs or is missing');
      if (row.runtimeReportSha256 && sha256(runtimeBytes) !== row.runtimeReportSha256) throw new Error('Runtime SHA256 differs');
      const pixels = pngPixels(image);
      if (!vector(row.pixels, 2) || pixels.some((value, i) => value !== row.pixels[i])) throw new Error('PNG and receipt resolutions differ');
      const frame = row.frame ?? runtime.frameInterval;
      const samples = frame?.sampleCount;
      const focus = runtime.focusDuringBenchmark;
      const validTiming = row.status === 'measured' && Number.isFinite(frame?.meanMs) && frame.meanMs > 0
        && Number.isInteger(samples) && samples > 0
        && focus?.applicationForegroundSamples === samples && focus?.gameWindowActiveSamples === samples;
      const presentation = runtime.walking?.presentationCamera;
      captures.push({
        id: row.id ?? relative(output, directory), phase, series, scene: row.scene,
        review: review ? { status: review.status, path: review.path, evaluatedAt: review.evaluatedAt, findings: review.findings, verdict: review.verdict } : null,
        profile: row.profile ?? 'unknown', software: Boolean(row.software), pixels,
        image: localPath(imagePath), runtime: localPath(runtimePath), summary: localPath(summaryPath),
        source: row.source?.split(/[\\/]/).filter(Boolean).at(-1) ?? '',
        endedAt: row.endedAt ?? row.startedAt ?? '', sha256: row.screenshotSha256,
        camera: { eyeCm: vector(presentation?.eyeCm, 3), forward: vector(presentation?.forward, 3) },
        frame: validTiming ? { meanMs: frame.meanMs, p95Ms: Number.isFinite(frame.p95Ms) ? frame.p95Ms : null, sampleCount: samples } : null,
        warmupFrames: Number.isInteger(runtime.warmupFrames) ? runtime.warmupFrames : null,
        timingNote: validTiming ? 'Aplikácia aj herné okno boli aktívne počas všetkých meraných snímok.'
          : 'Výkon sa neporovnáva: chýba platné meranie alebo úplné potvrdenie aktívneho okna.',
      });
      seen.add(directory);
    } catch (error) {
      omitted.push({ id: row.id ?? null, phase, reason: error.message, summary: localPath(summaryPath) });
    }
  }
}
captures.sort((a, b) => a.endedAt.localeCompare(b.endedAt) || a.id.localeCompare(b.id));
for (const review of reviews) {
  if (!captures.some(r => r.review?.path === review.path)) {
    reviewWarnings.push('Hodnotenie '+review.path+' sa nezhoduje so žiadnou dostupnou sériou a balíkom. Stav sa nepreniesol na iný beh.');
  }
}

const data = JSON.stringify({ captures, omitted, reviewWarnings, sceneNames, generatedAt: new Date().toISOString() }).replaceAll('<', '\\u003c');
const html = `<!doctype html>
<html lang="sk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>Březí — exteriér v Unreal Engine</title>
<style>
:root{--ink:#233029;--muted:#647167;--paper:#f4f3ed;--line:#d8ded5;--green:#304c3a;--accent:#dbedaa;font:15px/1.5 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper)}
*{box-sizing:border-box}body{margin:0}button,select,input{font:inherit}button,select{color:inherit}button,a,select,input{-webkit-tap-highlight-color:transparent}button:focus-visible,select:focus-visible,input:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #bf7a37;outline-offset:4px}a{color:var(--green);text-underline-offset:4px}button{cursor:pointer}button:disabled{cursor:default;opacity:.38}button,select{min-height:42px}main{width:min(1600px,100%);margin:auto;padding:30px 36px 40px}header{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-bottom:22px}.eyebrow{font-size:11px;letter-spacing:.2em;font-weight:750;text-transform:uppercase;color:var(--muted)}h1{font-size:clamp(32px,4.6vw,58px);font-weight:530;line-height:1.06;letter-spacing:-.065em;margin:10px 0 12px}.intro{margin:0;color:var(--muted);max-width:690px}.stamp{font-size:11px;letter-spacing:.09em;text-transform:uppercase;background:#e7eddf;border:1px solid #d8e2cd;border-radius:99px;padding:8px 12px;white-space:nowrap}.stamp:before{content:"";display:inline-block;width:6px;height:6px;background:#66814f;border-radius:50%;margin-right:8px}.tabs{display:flex;gap:6px;border-bottom:1px solid var(--line);overflow-x:auto;padding-bottom:12px;margin:0 0 18px}.tab{border:0;border-radius:6px;padding:10px 18px;background:transparent;white-space:nowrap}.tab[aria-selected=true]{background:var(--green);color:white}.toolbar{display:flex;gap:14px;align-items:end;justify-content:space-between;margin:0 0 13px}.view-title{font-size:18px;font-weight:550;letter-spacing:-.02em}.view-detail{font-size:12px;color:var(--muted)}.selectors{display:flex;align-items:end;gap:10px;flex-wrap:wrap}.select-label{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);display:grid;gap:4px}.select-label select{font-size:13px;letter-spacing:0;text-transform:none;background:#fffdf8;border:1px solid #cbd5c8;border-radius:6px;padding:7px 30px 7px 10px;max-width:310px}.modes{display:flex;gap:2px;padding:3px;border:1px solid #cbd5c8;border-radius:7px;background:#fffdf8}.modes button{border:0;background:transparent;padding:7px 13px;font-size:12px;border-radius:4px;min-height:34px}.modes button[aria-pressed=true]{background:#e6ecdf}.stage{--split:50%;position:relative;aspect-ratio:16/9;width:100%;background:#17211b;overflow:hidden;border-radius:10px;isolation:isolate;box-shadow:0 15px 40px #23302912}.stage.compare{cursor:ew-resize;touch-action:pan-y}.stage img{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:contain;pointer-events:none;user-select:none}.stage .before{clip-path:inset(0 calc(100% - var(--split)) 0 0)}.stage .divider{position:absolute;left:var(--split);top:0;bottom:0;width:1px;background:#fff;box-shadow:0 0 0 1px #0003;pointer-events:none}.handle{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:42px;height:42px;display:grid;place-items:center;border:1px solid #ffffffa6;border-radius:50%;background:#20302799;backdrop-filter:blur(8px);color:white;font-size:20px;letter-spacing:3px;padding-left:3px}.badge{position:absolute;top:18px;padding:6px 10px;border:1px solid #ffffff2c;border-radius:4px;background:#142219b8;backdrop-filter:blur(10px);color:#fff;font-size:10px;font-weight:650;letter-spacing:.11em;text-transform:uppercase;pointer-events:none}.badge.left{left:18px}.badge.right{right:18px}.image-caption{position:absolute;left:18px;bottom:16px;color:#fff;font-size:11px;text-shadow:0 1px 5px #000;background:#14221980;border-radius:4px;padding:4px 8px}.empty{position:absolute;inset:0;display:grid;place-content:center;text-align:center;color:#dfe8dd;padding:30px}.empty strong{font-size:21px;font-weight:500}.empty span{font-size:13px;color:#aebfb1;margin-top:8px;max-width:440px}.stage.loading:after{content:'Načítavam pôvodný PNG…';position:absolute;right:18px;bottom:16px;color:white;background:#142219b8;padding:5px 10px;border-radius:4px;font-size:11px}.slider{display:flex;gap:14px;align-items:center;font-size:11px;color:var(--muted);margin:12px 0 0}.slider input{width:100%;min-width:80px;accent-color:var(--green);height:24px;margin:0}.pair-note{font-size:12px;color:var(--muted);margin:10px 0 17px;min-height:18px}.metrics{display:grid;grid-template-columns:1fr 1fr;border:1px solid var(--line);border-radius:9px;background:#fffdf7;margin-top:15px}.metric-card{padding:19px 24px;min-width:0}.metric-card+.metric-card{border-left:1px solid var(--line)}.metric-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline}.metric-head strong{font-size:12px;font-weight:650}.version{font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:65%}.measurement{font-size:clamp(23px,2.8vw,34px);letter-spacing:-.04em;font-weight:550;margin:6px 0 1px;line-height:1.2}.measurement small{font-size:13px;font-weight:400;letter-spacing:0;color:var(--muted)}.measurement.unavailable{font-size:18px;margin:12px 0}.metric-detail{font-size:11px;color:var(--muted)}.links{display:flex;gap:14px;flex-wrap:wrap;font-size:11px;margin-top:10px}.thumbnails{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:12px;margin:25px 0}.thumbnail{text-align:left;padding:0;background:transparent;border:0;min-width:0}.thumbnail img{display:block;aspect-ratio:16/9;width:100%;object-fit:cover;border-radius:6px;background:#dce2d8;filter:saturate(.8);outline:1px solid #0000000a}.thumbnail[aria-pressed=true] img{outline:2px solid var(--green);outline-offset:3px;filter:none}.thumbnail span{display:block;font-size:12px;margin-top:9px}.thumbnail small{display:block;font-size:10px;color:var(--muted)}footer{border-top:1px solid var(--line);padding-top:19px;display:flex;justify-content:space-between;gap:25px;font-size:11px;color:var(--muted)}footer p{margin:0;max-width:820px}.receipts{margin-top:16px;font-size:12px;color:var(--muted)}.receipts summary{cursor:pointer}.receipt-body{padding:12px 0;max-width:920px}.receipt-body p{margin:5px 0}.receipt-body ul{padding-left:20px}code{font-size:11px;overflow-wrap:anywhere}.legend{display:flex;align-items:center;gap:7px}.legend:before{content:'';width:8px;height:8px;background:#5e7851;border-radius:50%}[hidden]{display:none!important}noscript{display:block;background:#fff9df;border:1px solid #dfcf91;padding:16px;margin:15px 0}
@media(min-width:1800px){main{padding-top:40px}}@media(max-width:1050px){main{padding:24px}.toolbar{align-items:start;flex-direction:column;gap:10px}.selectors{width:100%}.thumbnails{gap:9px}.metric-card{padding:17px}.stamp{display:none}}@media(max-width:650px){main{padding:22px 13px}.intro{font-size:13px}header{margin-bottom:20px}.tabs{margin-bottom:13px;gap:0}.tab{padding:9px 13px;font-size:13px}.view-title{font-size:16px}.selectors{gap:8px}.select-label{flex:1;min-width:140px}.select-label select{width:100%;max-width:none}.modes{width:100%;justify-content:center}.modes button{flex:1}.stage{border-radius:6px}.badge{top:10px;font-size:8px;padding:4px 6px}.badge.left{left:10px}.badge.right{right:10px}.image-caption{left:10px;bottom:10px;font-size:9px}.handle{width:32px;height:32px;font-size:16px}.metrics{grid-template-columns:1fr}.metric-card{padding:14px 16px}.metric-card+.metric-card{border-left:0;border-top:1px solid var(--line)}.metric-head strong{font-size:11px}.measurement{font-size:27px}.metric-detail{line-height:1.65}.thumbnails{grid-template-columns:repeat(3,minmax(0,1fr));gap:15px 10px;margin:22px 0}.thumbnail span{font-size:11px}footer{flex-direction:column;gap:12px}.pair-note{font-size:11px}.slider{gap:8px}.version{max-width:60%}}@media(prefers-reduced-motion:no-preference){button{transition:background .12s ease}.thumbnail img{transition:filter .15s ease}}
.review-notice{display:flex;flex-wrap:wrap;align-items:baseline;gap:5px 13px;border:1px solid #d8ded5;background:#eaf0e5;padding:11px 14px;border-radius:7px;margin:0 0 13px;font-size:12px}.review-notice strong{font-weight:650}.review-notice span{color:var(--muted)}.review-notice.rejected{background:#fff0df;border-color:#dfbc92;color:#713e18}.review-notice.rejected span{color:#81583c}.review-notice a{white-space:nowrap}.review-warning{color:#8b491d}.review-findings{flex-basis:100%;margin:2px 0;padding-left:18px}.review-findings li+li{margin-top:3px}.review-notice.accepted{background:#e4efdb;border-color:#9bb38c}@media(max-width:1050px){.thumbnails{grid-template-columns:repeat(4,minmax(0,1fr))}}@media(max-width:650px){.thumbnails{grid-template-columns:repeat(3,minmax(0,1fr))}.review-notice{font-size:11px;padding:10px 12px}}
</style></head><body><main>
<header><div><div class="eyebrow">Březí · hlavný návrh C / B / B</div><h1>Dom v krajine.</h1><p class="intro">Exteriér, záhrada a okolie v Unreal Engine. Pôvodné zábery z aplikácie, vedľa seba s ich nameraným výkonom.</p></div><div class="stamp">Lokálna obrazová dokumentácia</div></header>
<noscript>Pre prepínanie záberov a posuvník pred / po je potrebný JavaScript. Pôvodné snímky a merania zostávajú v priečinku <a href="qa/">qa/</a>.</noscript>
<nav class="tabs" id="tabs" role="tablist" aria-label="Pohľad na exteriér"></nav>
<section id="viewer" role="tabpanel" aria-label="Natívny záber">
<div class="toolbar"><div><div class="view-title" id="view-title">Natívne zábery</div><div class="view-detail" id="view-detail">Záznamy sa pripravujú.</div></div><div class="selectors"><label class="select-label">Profil a rozlíšenie<select id="quality" aria-label="Profil a skutočné rozlíšenie záberu"></select></label><label class="select-label">Záznam<select id="revision" aria-label="Séria, zdroj a čas vybraného záberu"></select></label><label class="select-label">Porovnať s<select id="reference" aria-label="Referenčný záber s rovnakým pohľadom, profilom, rozlíšením a kamerou" aria-describedby="pair-note"></select></label><div class="modes" aria-label="Spôsob zobrazenia"><button type="button" id="mode-compare" aria-pressed="true">Pred / po</button><button type="button" id="mode-after" aria-pressed="false">Vybraný záber</button><button type="button" id="mode-before" aria-pressed="false">Pôvodný</button></div></div></div>
<div class="review-notice" id="review-notice" role="status" hidden></div>
<div class="stage" id="stage" aria-busy="false"><img id="after" alt="" decoding="async" draggable="false"><img id="before" class="before" alt="" decoding="async" draggable="false"><div id="divider" class="divider"><div class="handle" aria-hidden="true">‹›</div></div><span id="left-badge" class="badge left"></span><span id="right-badge" class="badge right"></span><span id="image-caption" class="image-caption">Natívny záber · Metal · bez retuše</span><div class="empty" id="empty" hidden><strong>Záber ešte nie je dostupný.</strong><span>Galéria zobrazuje iba existujúce snímky s overeným pôvodom. Po ďalších behoch ju treba znovu vygenerovať.</span></div></div>
<label class="slider" id="slider-wrap"><span id="slider-before-label">Pred</span><input id="split" type="range" min="0" max="100" value="50" aria-label="Hranica porovnania referenčného a vybraného záberu"><span id="slider-after-label">Po</span></label>
<p class="pair-note" id="pair-note" aria-live="polite"></p><div class="metrics"><article class="metric-card" id="before-metric"></article><article class="metric-card" id="after-metric"></article></div>
</section><nav class="thumbnails" id="thumbnails" aria-label="Prehľad dostupných pohľadov"></nav>
<footer><div><p>Snímky sú pôvodné PNG z natívnej aplikácie na Metal. Galéria ich neupravuje ani neretušuje. Statický obraz nepotvrdzuje plynulosť pohybu ani vizuálne prijatie výsledku. FPS je 1 000 / priemerný čas snímky; rozlíšenie je prečítané priamo z PNG.</p><p id="orthophoto-attribution" style="margin-top:10px"><a href="https://ags.cuzk.gov.cz/arcgis1/rest/services/ORTOFOTO/MapServer" target="_blank" rel="noopener">Zdrojové ortofoto ČR od R5: ČÚZK, 2024</a> · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a>. Zdroj: ČÚZK – on-line, jednorazový export. Úpravy pre vizualizáciu: výrez, prevzorkovanie a mapovanie na DMR. Zábery R1–R4 tento podklad nepoužívajú. <a href="https://www.cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx" target="_blank" rel="noopener">Podmienky údajov</a> · <a href="https://www.cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-sitovych-sluzeb-CUZK.aspx" target="_blank" rel="noopener">Podmienky služby</a>.</p><p id="vegetation-attribution" style="margin-top:10px">Fotografie listov pre regionálnu vegetáciu R6: <a href="https://www.cgbookcase.com/textures" target="_blank" rel="noopener">CGBookcase / Dorian Zgraggen</a> · <a href="https://creativecommons.org/publicdomain/zero/1.0/" target="_blank" rel="noopener">CC0 1.0</a>. Vegetácia v novších verziách je vizualizačná interpretácia zelenej sezóny.</p></div><div class="legend" id="capture-count"></div></footer>
<details class="receipts"><summary>Podklady a rozsah merania</summary><div class="receipt-body" id="receipts"></div></details>
</main>
<script>
const DATA=${data};
const $=id=>document.getElementById(id);
const profiles={cinematic:'Fotoreal',native:'Natívny detail',balanced:'Vyvážené',performance:'Výkon'};
const phaseLabels={'before-exterior':'Pôvodný stav','after-exterior':'Natívny pokus','final-exterior':'Záverečný beh'};
const phaseRank={'before-exterior':0,'after-exterior':1,'final-exterior':2};
const number=(n,d=1)=>new Intl.NumberFormat('sk-SK',{minimumFractionDigits:d,maximumFractionDigits:d}).format(n);
const pixels=r=>r.pixels.map(n=>number(n,0)).join(' × ');
const sceneBase=s=>s.replace(/^exterior-/,'').replace(/-(day|night)$/,'').replace(/^parcels$/,'parcel').replace(/^site-aerial$/,'siteaerial').replace(/^garden-(close|detail)$/,'garden');
const preset=s=>DATA.sceneNames.find(r=>r[0]===sceneBase(s));
const sceneLabel=s=>(preset(s)?.[1]||s)+(s.endsWith('-night')?' · noc':'');
const key=r=>[r.profile,r.software?'sw':'hw',...r.pixels].join('|');
const qualityLabel=r=>(profiles[r.profile]||r.profile)+(r.software?' · softvérový Lumen':'')+' · '+pixels(r);
const rejected=r=>r?.review?.status==='rejected';
const accepted=r=>r?.review?.status==='accepted';
const revisionName=r=>{const match=r.series.match(/(?:^|-)r([0-9]+[a-z]?)(?:-|$)/i)||r.source.match(/-r([0-9]+[a-z]?)$/i);return match?'R'+match[1]:''};
const recordLabel=r=>r.phase==='before-exterior'?'Pôvodný stav':[revisionName(r),rejected(r)?'zamietnutý pokus':accepted(r)?'vizuálne posúdené':phaseLabels[r.phase].toLocaleLowerCase('sk-SK')].filter(Boolean).join(' · ');
const priority=r=>rejected(r)?0:r.phase==='before-exterior'?1:accepted(r)?5:r.frame?4:2;
const rank=(a,b)=>priority(b)-priority(a)||b.endedAt.localeCompare(a.endedAt)||(phaseRank[b.phase]-phaseRank[a.phase])||b.id.localeCompare(a.id);
const date=value=>value?new Date(value).toLocaleString('sk-SK',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'bez času';
const optionLabel=r=>[recordLabel(r),r.source||r.series,date(r.endedAt)].filter(Boolean).join(' · ');
const near=(a,b,t)=>a&&b&&a.every((v,i)=>Math.abs(v-b[i])<=t);
const sameCamera=(a,b)=>near(a.camera.eyeCm,b.camera.eyeCm,.01)&&near(a.camera.forward,b.camera.forward,1e-7);
const sceneOrder=s=>{const i=DATA.sceneNames.findIndex(r=>r[0]===sceneBase(s));return i<0?99:i};
const availableScenes=[...new Set(DATA.captures.map(r=>r.scene))].sort((a,b)=>sceneOrder(a)-sceneOrder(b)||a.localeCompare(b));
const navScenes=[...DATA.sceneNames.map(([name])=>availableScenes.find(s=>sceneBase(s)===name)||name+'-day'),...availableScenes.filter(s=>!DATA.sceneNames.some(([name])=>name===sceneBase(s))||s.endsWith('-night'))];
let scene=availableScenes[0]||'street-day',quality='',revision='',reference='',mode='compare',current=null;
function el(tag,text,className){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(className)e.className=className;return e}
function link(text,href){const a=el('a',text);a.href=href;a.target='_blank';a.rel='noopener';return a}
function metric(id,row,label){const card=$(id);card.replaceChildren();const head=el('div',undefined,'metric-head');head.append(el('strong',label),el('span',row?.source||'Záber chýba','version'));card.append(head);if(!row){card.append(el('div','Bez porovnateľného záberu','measurement unavailable'),el('div','Pre rovnaký pohľad, profil a rozlíšenie zatiaľ nie je dostupný zodpovedajúci záznam.','metric-detail'));return}const measure=el('div',undefined,'measurement');if(row.frame){measure.append(document.createTextNode(number(1000/row.frame.meanMs)+' FPS '),el('small','/ '+number(row.frame.meanMs,2)+' ms'));card.append(measure);card.append(el('div',pixels(row)+' · '+number(row.frame.sampleCount,0)+' snímok'+(row.frame.p95Ms!==null?' · P95 '+number(row.frame.p95Ms,2)+' ms':''),'metric-detail'))}else card.append(el('div','Výkon bez platného merania','measurement unavailable'),el('div',pixels(row),'metric-detail'));const links=el('div',undefined,'links');links.append(link('Pôvodný PNG ↗',row.image),link('Meranie JSON ↗',row.runtime));card.append(links)}
function options(select,items,selected){select.replaceChildren();for(const [value,label] of items)select.add(new Option(label,value));select.value=items.some(([v])=>v===selected)?selected:items[0]?.[0]||'';select.disabled=items.length<2;return select.value}
function selectScene(next){scene=next;revision='';reference='';refresh()}
function reviewNotice(row){
 const notice=$('review-notice');notice.replaceChildren();notice.hidden=!row;notice.classList.toggle('rejected',rejected(row));notice.classList.toggle('accepted',accepted(row));if(!row)return;
 const title=row.review?recordLabel(row):row.phase==='before-exterior'?'Pôvodný porovnávací stav':recordLabel(row)+' · vizuálne prijatie nepotvrdené';
 notice.append(el('strong',title));
 if(row.review){
  if(row.review.verdict)notice.append(el('span',row.review.verdict));
  if(row.review.findings.length){const list=el('ul',undefined,'review-findings');for(const finding of row.review.findings)list.append(el('li',finding));notice.append(list)}
  else if(rejected(row)&&!row.review.verdict)notice.append(el('span','Pokus bol zamietnutý podľa priloženého hodnotenia.'));
  notice.append(link(rejected(row)?'Záznam zamietnutia ↗':'Vizuálne hodnotenie ↗',row.review.path));
 }
 else notice.append(el('span',row.phase==='before-exterior'?'Východiskový záber na porovnanie.':'Označenie série ani úspešný import nepotvrdzujú kvalitu výsledku.'));
}
function refresh(){
 const rows=DATA.captures.filter(r=>r.scene===scene).sort(rank),byQuality=[...new Map(rows.map(r=>[key(r),r])).entries()];
 quality=options($('quality'),byQuality.map(([k,r])=>[k,qualityLabel(r)]),quality);
 const matching=rows.filter(r=>key(r)===quality);revision=options($('revision'),matching.map(r=>[r.id,optionLabel(r)]),revision);
 const selected=matching.find(r=>r.id===revision);
 const references=matching.filter(r=>selected&&r.id!==selected.id&&sameCamera(r,selected));
 reference=options($('reference'),[['','Automaticky · pôvodný stav'],...references.map(r=>[r.id,optionLabel(r)])],reference);
 const manual=references.find(r=>r.id===reference)||null;
 const after=selected&&(manual||selected.phase!=='before-exterior')?selected:null;
 const before=manual||(selected?.phase==='before-exterior'?selected:references.filter(r=>r.phase==='before-exterior').sort(rank)[0]||null);
 current={before,after,selected,manual:Boolean(manual),paired:Boolean(before&&after)};
 $('view-title').textContent=sceneLabel(scene);$('view-detail').textContent=preset(scene)?.[2]||'Pôvodný natívny záznam';
 [...$('tabs').children].forEach(b=>{b.setAttribute('aria-selected',String(b.dataset.scene===scene));b.tabIndex=b.dataset.scene===scene?0:-1});[...$('thumbnails').children].forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.scene===scene)));
 const referenceLabel=before?.phase==='before-exterior'?'Pôvodný stav':'Referencia';
 metric('before-metric',before,manual?'Referencia · '+recordLabel(before):'PRED · pôvodný stav');metric('after-metric',after,after?'Vybraný · '+recordLabel(after):'Vybraný záber');reviewNotice(selected);
 $('mode-compare').textContent=manual?'Porovnanie':'Pred / po';$('mode-before').textContent=referenceLabel;
 $('slider-before-label').textContent=manual?'Referencia':'Pred';$('slider-after-label').textContent=manual?'Vybraný':'Po';
 $('mode-compare').disabled=!current.paired;$('mode-after').disabled=!after;$('mode-before').disabled=!before;
 $('pair-note').textContent=current.paired?(manual?'Referencia: '+optionLabel(before)+'. Vybraný: '+optionLabel(after)+'. ':'')+'Posuňte deliacu čiaru. Zhodný pohľad, profil, rozlíšenie, poloha a smer kamery.':after?'Vybraný záber. Automatický pôvodný záznam s rovnakým profilom, rozlíšením a kamerou nie je dostupný. Referenciu môžete vybrať v „Porovnať s“.':before?'Pôvodný záber. Porovnateľnú referenciu môžete vybrať v „Porovnať s“.':'Pre tento pohľad ešte nebol uložený overený natívny záber.';
 render();receipts();
}
function render(){
 const {before,after,selected,paired,manual}=current,effective=paired?mode:after?'after':'before';
 const showCompare=paired&&effective==='compare',image=effective==='before'?before:after;
 $('stage').classList.toggle('compare',showCompare);$('stage').style.aspectRatio=selected?selected.pixels[0]+'/'+selected.pixels[1]:'16/9';
 $('empty').hidden=Boolean(selected);$('image-caption').hidden=!selected;$('divider').hidden=!showCompare;$('slider-wrap').hidden=!showCompare;
 $('before').hidden=!showCompare;$('after').hidden=!selected;$('left-badge').hidden=!selected;$('right-badge').hidden=!showCompare;
 if(selected){$('stage').classList.add('loading');$('stage').setAttribute('aria-busy','true');const complete=()=>{if($('after').complete&&(!showCompare||$('before').complete)){$('stage').classList.remove('loading');$('stage').setAttribute('aria-busy','false')}};$('after').onload=complete;$('before').onload=complete;$('after').src=(showCompare?after:image||selected).image;$('after').alt=sceneLabel(scene)+' — '+optionLabel(showCompare?after:image||selected);if(showCompare){$('before').src=before.image;$('before').alt=sceneLabel(scene)+' — referencia: '+optionLabel(before)}$('left-badge').textContent=showCompare?(manual?'Referencia · '+recordLabel(before):'Pred · pôvodný stav'):recordLabel(image||selected);$('right-badge').textContent=after?(manual?'Vybraný · ':'')+recordLabel(after):'';complete()}
 for(const name of ['compare','after','before'])$('mode-'+name).setAttribute('aria-pressed',String(effective===name));
}
function receipts(){
 const parent=$('receipts');parent.replaceChildren();
 for(const row of [current.before,current.after]){
  if(!row)continue;
  parent.append(el('p',recordLabel(row)+' · '+row.timingNote+(row.warmupFrames!==null?' Zahriatie: '+number(row.warmupFrames,0)+' snímok.':'')));
  const p=el('p');p.append(link('Súhrn pôvodnej série',row.summary),document.createTextNode(' · '+row.id));parent.append(p,el('code','PNG SHA256 '+row.sha256));
  if(row.review){const review=el('p');review.append(link((rejected(row)?'Vizuálne zamietnutie':'Vizuálne hodnotenie')+' · '+date(row.review.evaluatedAt),row.review.path));parent.append(review)}
 }
 parent.append(el('p','Galéria vygenerovaná '+date(DATA.generatedAt)+'. „Natívny pokus“ a „Záverečný beh“ pomenúvajú série; nepotvrdzujú vizuálne prijatie. Automatické porovnanie používa pôvodný stav. V „Porovnať s“ možno zvoliť inú overenú referenciu s rovnakým pohľadom, profilom, rozlíšením a kamerou; jej hodnotenie sa tým nemení.'));
 const sources=el('p');sources.append(document.createTextNode('Podklady: '),link('ČÚZK · katastrálne parcely','https://services.cuzk.gov.cz/wfs/inspire-cp-wfs.asp'),document.createTextNode(' · '),link('ČÚZK · DMR 5G','https://ags.cuzk.gov.cz/arcgis2/rest/services/dmr5g/ImageServer'),document.createTextNode(' · '),link('Podmienky ČÚZK','https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx'),document.createTextNode(' · '),link('Poly Haven · licencia CC0','https://polyhaven.com/license'));parent.append(sources);
 parent.append(el('p','© ČÚZK · parcely a DMR 5G · CC BY 4.0. Hranice, vzorkovaný výškový model a ilustračné osadenie rastlín majú odlišnú presnosť; galéria nepotvrdzuje geodetické zameranie ani botanický súpis miesta.'));
 for(const warning of DATA.reviewWarnings)parent.append(el('p',warning,'review-warning'));
 if(DATA.omitted.length){parent.append(el('p','Vynechané neúplné alebo neoverené záznamy: '+DATA.omitted.length));const list=el('ul');for(const r of DATA.omitted)list.append(el('li',(r.id||r.phase)+': '+r.reason));parent.append(list)}
}
for(const s of navScenes){const button=el('button',sceneLabel(s),'tab');button.type='button';button.dataset.scene=s;button.id='tab-'+s;button.setAttribute('role','tab');button.setAttribute('aria-controls','viewer');button.disabled=!availableScenes.includes(s);button.onclick=()=>selectScene(s);$('tabs').append(button);if(!button.disabled){const row=DATA.captures.filter(r=>r.scene===s).sort(rank)[0],thumb=el('button',undefined,'thumbnail');thumb.type='button';thumb.dataset.scene=s;thumb.setAttribute('aria-label','Zobraziť '+sceneLabel(s));const img=new Image;img.src=row.image;img.alt='';img.loading='lazy';thumb.append(img,el('span',sceneLabel(s)),el('small',recordLabel(row)));thumb.onclick=()=>selectScene(s);$('thumbnails').append(thumb)}}
$('tabs').onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;const tabs=[...$('tabs').children].filter(b=>!b.disabled),index=tabs.indexOf(document.activeElement);if(index<0)return;e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?tabs.length-1:(index+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[n].focus();tabs[n].click()};
$('quality').onchange=()=>{quality=$('quality').value;revision='';reference='';refresh()};$('revision').onchange=()=>{revision=$('revision').value;refresh()};$('reference').onchange=()=>{reference=$('reference').value;refresh()};
for(const name of ['compare','after','before'])$('mode-'+name).onclick=()=>{mode=name;render()};
function split(value){$('split').value=Math.max(0,Math.min(100,value));$('stage').style.setProperty('--split',$('split').value+'%')}
$('split').oninput=()=>split(Number($('split').value));
function drag(e){const rect=$('stage').getBoundingClientRect();split((e.clientX-rect.left)/rect.width*100)}
$('stage').onpointerdown=e=>{if(!current?.paired||mode!=='compare'||e.button!==0)return;$('stage').setPointerCapture(e.pointerId);drag(e)};
$('stage').onpointermove=e=>{if($('stage').hasPointerCapture(e.pointerId))drag(e)};
$('stage').onpointerup=e=>{if($('stage').hasPointerCapture(e.pointerId))$('stage').releasePointerCapture(e.pointerId)};
for(const id of ['after','before'])$(id).onerror=()=>{$('stage').classList.remove('loading');$('stage').setAttribute('aria-busy','false');$('pair-note').textContent='Pôvodný PNG sa nepodarilo načítať. Skontrolujte, či sa galéria otvára zo správneho priečinka spolu s qa/.'};
$('capture-count').textContent=DATA.captures.length+' overených záberov · '+availableScenes.length+' pohľadov';
refresh();
</script></body></html>`;
await writeFile(resolve(output, 'index.html'), html);
console.log(JSON.stringify({ gallery: resolve(output, 'index.html'), captures: captures.length, omitted: omitted.length,
  status: 'gallery-generated-from-native-evidence', visualAcceptanceClaimed: false }));
