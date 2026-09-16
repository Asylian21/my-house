#!/usr/bin/env python3
"""Build the private C/B/B document library; source PDFs are never modified."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'output/pdf/construction-cbb'
PUBLIC_BASE = ROOT / 'public/documents'
PUBLIC = PUBLIC_BASE
URL_PREFIX = '/documents'
MANIFEST = ROOT / 'lib/document-library.generated.json'
STATE = PUBLIC_BASE / '.build-state.json'
VERSION = 1
# This verified predecessor differs only in H200 previews/cache URL handling.
# Permit its drawing assets to migrate once without rerendering 50 A1 sheets.
# Any other renderer-source change still invalidates the rendering cache.
H200_PREVIEW_COMPATIBLE_BUILD_SHA256 = 'c496f9ed8b6f690c583a5d2574145c5962112861a3f246e064cfcf9af7e3fb5f'
COORDINATION = 'Koordinačný podklad. Nie je vydaný na realizáciu; chýbajúce statické a konštrukčné údaje ostávajú otvorené.'
REFERENCE = 'Aktuálny podklad alebo rozhodnutie C/B/B; nepredstavuje schválenie nosnej konštrukcie.'
ARCHIVE = 'Historická alternatíva 274 mm. Nie je aktívnou skladbou H200 ani realizačným podkladom C/B/B.'

FOLDERS = [
    ('drawings', 'Výkresy', None, 'Výkresová sada C/B/B: 25 listov vo farebnej a čiernobielej verzii.'),
    ('plan', 'Pôdorys', 'drawings', 'Pôvodný pôdorys so stopami rezov.'),
    ('elevations', 'Pohľady', 'drawings', 'Všetky fasády a zalomené časti domu.'),
    ('sections', 'Rezy', 'drawings', 'Pozdĺžny a priečne rezy A-A, B-B, C-C.'),
    ('foundations', 'Základy', 'drawings', 'Nosné línie, monolitické založenie a priestorové zobrazenie.'),
    ('roof', 'Strecha', 'drawings', 'Pôdorys strechy.'),
    ('site', 'Osadenie', 'drawings', 'Situácia a územný plán.'),
    ('openings', 'Okná a dvere', 'drawings', 'Výpisy otvorov a ich pôvodné kódy.'),
    ('assemblies', 'Skladby a detaily', 'drawings', 'Konštrukčné skladby, H200 a SM30.'),
    ('services', 'Technické zariadenia', 'drawings', 'Vykurovanie a rozsah povaly.'),
    ('reports', 'Správy a rozhodnutia', None, 'Aktuálne textové podklady projektu.'),
    ('construction-reports', 'Konštrukčné podklady', 'reports', 'Otvorené stavebné, výškové a statické súvislosti.'),
    ('acoustics', 'Akustika', 'reports', 'Aktívne SM30 a H200 vrátane napojení.'),
    ('decisions', 'Rozhodnutia C/B/B', 'reports', 'Aktívny návrh, kuchyňa a pracovňa.'),
    ('images', 'Obrázky', None, 'Samostatná farebná a čiernobiela axonometria.'),
    ('model', 'Model a registre', None, 'Strojovo čitateľné údaje, zadanie a výpočtové podklady.'),
    ('archive', 'Archív', None, 'Výslovne nahradené alternatívy; nie hlavný návrh.'),
]
REPORTS = {
    'active-design.md': ('Hlavný návrh C/B/B', 'decisions', 'reference', '/docs'),
    'acoustic-walls.md': ('Steny SM30 a H200 · odhlučnenie', 'acoustics', 'reference', None),
    'office-acoustic-wall-thinner-options.md': ('H200 · aktuálna skladba a podklady', 'acoustics', 'reference', '/docs/akustika-h200'),
    'office-acoustic-wall-junction.md': ('H200 · napojenie pri dverách D1 / J1 / J2', 'acoustics', 'reference', '/docs/akustika-h200/napojenie'),
    'office-acoustic-wall-scientific-rationale.md': ('H200 · odborné zdôvodnenie', 'acoustics', 'reference', '/docs/akustika-h200'),
    'kitchen-island.md': ('Kuchyňa · ostrovček a zostava', 'decisions', 'reference', None),
    'office-desk.md': ('Pracovňa · pracovný stôl', 'decisions', 'reference', None),
    'sa30-acoustic-wall-study.md': ('Archív · nahradená dvojplášťová SA30', 'archive', 'archive', None),
    'office-acoustic-wall-study.md': ('Archív · akustická stena 274 mm', 'archive', 'archive', None),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def iso_mtime(path):
    return datetime.fromtimestamp(Path(path).stat().st_mtime, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + f'.tmp-{os.getpid()}')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def slug(code):
    return re.sub(r'[^a-z0-9-]+', '-', code.lower()).strip('-')


def sheet_folder(code):
    for token, folder in [('002', 'plan'), ('.PO-', 'elevations'), ('.RE-', 'sections'), ('.ZA-', 'foundations'),
                          ('.ST-', 'roof'), ('.SI-', 'site'), ('.UP-', 'site'), ('.OT-', 'openings'),
                          ('.SK-', 'assemblies'), ('.DT-', 'assemblies'), ('.TZ-', 'services')]:
        if token in code:
            return folder
    return 'drawings'


def inputs():
    required = [SOURCE / name for name in [
        'DOM-CBB-A1-color.pdf', 'DOM-CBB-A1-mono.pdf', 'drawing-set-color.html', 'drawing-set-mono.html',
        'drawing-register.json', 'model-snapshot.json', 'verification.json', 'pdf-verification.json',
        'foundation-axon-color.svg', 'foundation-axon-color.png', 'foundation-axon-mono.svg', 'foundation-axon-mono.png',
    ]]
    required += [ROOT / 'docs' / name for name in REPORTS]
    required += [ROOT / 'output/pdf/h200-odborne-zdovodnenie.pdf']
    construction = sorted((ROOT / 'docs').glob('construction*.md'))
    require(construction, 'Missing docs/construction*.md reports')
    required += construction
    required += [ROOT / 'lib/document-library.ts', *sorted(Path(__file__).parent.glob('*.py')),
                 *sorted(Path(__file__).parent.glob('*.mjs')), Path(__file__).parent / 'requirements.txt']
    for path in required:
        require(path.is_file(), f'Missing document-library source: {path.relative_to(ROOT)}. Regenerate the construction set before exporting the library.')
    return sorted(set(required)), construction


def source_signature(paths):
    facts = {str(path.relative_to(ROOT)): {'sha256': sha(path), 'mtimeNs': path.stat().st_mtime_ns} for path in paths}
    return hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest(), facts


def render_facts(facts):
    return {name: metadata['sha256'] for name, metadata in facts.items()
            if name.startswith(('output/pdf/construction-cbb/', 'scripts/document-library/'))}


def h200_only_cache_migration(cached, facts):
    if not cached:
        return False
    previous = render_facts(cached.get('inputs', {}))
    current = render_facts(facts)
    build_name = 'scripts/document-library/build.py'
    if previous.pop(build_name, None) != H200_PREVIEW_COMPATIBLE_BUILD_SHA256:
        return False
    current.pop(build_name, None)
    return previous == current


def validate_assets(manifest, expected=None, staging=None):
    require(manifest.get('version') == VERSION, 'Unsupported library manifest version')
    ids = [doc['id'] for doc in manifest['documents']]
    require(len(ids) == len(set(ids)), 'Duplicate document ids')
    folders = {folder['id'] for folder in manifest['folders']}
    assets = {}
    for doc in manifest['documents']:
        require(doc['folderId'] in folders, f"Unknown folder: {doc['id']}")
        urls = [(key, doc[key]) for key in ['url', 'previewUrl', 'thumbnailUrl'] if doc.get(key)]
        if 'pagePreviewUrls' in doc:
            previews = doc['pagePreviewUrls']
            require(isinstance(previews, list) and len(previews) == doc.get('pageCount') and previews,
                    f"Incomplete page previews: {doc['id']}")
            require(len(set(previews)) == len(previews), f"Duplicate page previews: {doc['id']}")
            require(doc.get('previewUrl') == previews[0], f"First page preview differs: {doc['id']}")
            urls.extend((f'pagePreviewUrls[{index}]', url) for index, url in enumerate(previews))
        for key, url in urls:
            require(url.startswith('/documents/') and '..' not in Path(url).parts and '\\' not in url,
                    f"Unsafe {key}: {doc['id']}")
            path = ROOT / 'public' / url.lstrip('/')
            if staging is not None and url.startswith(URL_PREFIX + '/'):
                path = staging / url[len(URL_PREFIX) + 1:]
            require(path.is_file(), f'Missing generated asset: {url}. Run node scripts/document-library/generate.mjs')
            size = path.stat().st_size
            require(size > 0, f'Empty generated asset: {url}')
            require(size < 25_000_000, f'Generated asset exceeds the static-file limit: {url} ({size} bytes)')
            if key == 'url':
                require(size == doc['bytes'], f"Stale byte count: {doc['id']}")
            if url not in assets:
                assets[url] = {'bytes': size, 'sha256': sha(path)}
            if expected is not None:
                require(assets[url] == expected.get(url), f'Stale or altered generated asset: {url}')
    for color in ['color', 'mono']:
        bundle = next(doc for doc in manifest['documents'] if doc['id'] == manifest['bundleIds'][color])
        require(bundle['pageCount'] == 25 and bundle['format'] == 'PDF', 'The complete bundle must retain all 25 pages')
        sheets = [doc for doc in manifest['documents'] if doc.get('bundleId') == bundle['id']]
        require(sorted(doc['sheetIndex'] for doc in sheets) == list(range(1, 26)), f'Incomplete {color} sheet set')
        require(all(doc['pageCount'] == 1 and doc['format'] == 'PDF' and doc['color'] == color for doc in sheets), 'Invalid standalone sheet')
    require(all(value in ids for value in manifest['featuredIds']), 'Unknown featured document')
    return assets


def signatures(pdf):
    values = []
    for page in pdf.pages:
        contents = page.obj.get('/Contents', [])
        streams = list(contents) if isinstance(contents, pikepdf.Array) else [contents]
        values.append({
            'mediaBox': [float(n) for n in page.mediabox],
            'cropBox': [float(n) for n in page.cropbox],
            'rotate': int(page.obj.get('/Rotate', 0)),
            'contents': [hashlib.sha256(stream.read_bytes()).hexdigest() for stream in streams],
        })
    return values


def save_pdf(pdf, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # A fresh page catalog excludes the replaced ZA03 page still retained by
    # Chromium's old tagged-structure references. Visible page streams stay intact.
    with pikepdf.Pdf.new() as clean:
        clean.pages.extend(pdf.pages)
        for key, value in pdf.docinfo.items():
            clean.docinfo[key] = pikepdf.String(str(value))
        clean.save(path, compress_streams=True, recompress_flate=True,
                   object_stream_mode=pikepdf.ObjectStreamMode.generate, deterministic_id=True)
    # QPDF does not merge identical resource objects. Chromium's axonometry
    # contains duplicates; merge them without rasterization or stream rewriting.
    candidate = path.with_suffix('.deduplicated.pdf')
    with PdfReader(path) as reader:
        writer = PdfWriter(clone_from=reader)
        writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
        writer.write(candidate)
    if candidate.stat().st_size < path.stat().st_size:
        candidate.replace(path)
    else:
        candidate.unlink()


def record(path, *, ident, title, description, folder, fmt, status, updated, **kwargs):
    return dict(id=ident, title=title, description=description, folderId=folder, format=fmt, status=status,
                statusNote={'coordination': COORDINATION, 'reference': REFERENCE, 'archive': ARCHIVE}[status],
                filename=path.name, url=URL_PREFIX + '/' + str(path.relative_to(PUBLIC)), bytes=path.stat().st_size,
                updatedAt=updated, **kwargs)


def build(construction, reuse=None):
    from optimize_svg import optimize_aggregate, compare_pdf_renders
    register = json.loads((SOURCE / 'drawing-register.json').read_text())
    snapshot = json.loads((SOURCE / 'model-snapshot.json').read_text())
    verification = json.loads((SOURCE / 'verification.json').read_text())
    require(len(register) == 25 and len({r['id'] for r in register}) == 25, 'Expected exactly 25 uniquely coded source sheets')
    require(all(r['status'] == 'NOT_FOR_CONSTRUCTION' for r in register), 'Unexpected approval state in source register')
    require(any(r['id'] == 'R7' for r in snapshot['foundationIllustration']['ribs']), 'Source is stale: current R7 must be present')
    loads = snapshot['partitionLoads']
    require(loads['finalDesignApproved'] is False, 'Unexpected partition design approval')
    require(verification['partitionSelfWeight']['unplasteredKg'] == loads['totals']['unplasteredKg'], 'Load verification and snapshot disagree')
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for folder in ['bundles', 'sheets', 'previews', 'thumbnails', 'images', 'reports', 'model', 'archive']:
        (PUBLIC / folder).mkdir(exist_ok=True)
    documents = [] if reuse is None else [doc for doc in reuse['manifest']['documents']
        if doc['id'].startswith(('sheet-', 'bundle-', 'image-'))]
    for doc in documents:
        if doc['id'].startswith(('sheet-', 'bundle-')):
            doc['updatedAt'] = iso_mtime(SOURCE / f'DOM-CBB-A1-{doc["color"]}.pdf')
        else:
            doc['updatedAt'] = iso_mtime(SOURCE / doc['filename'])
    pdf_times = [iso_mtime(SOURCE / f'DOM-CBB-A1-{color}.pdf') for color in ['color', 'mono']]
    source_updated = max(pdf_times)
    number = lambda value: f'{value:.2f}'.replace('.', ',')
    grouped = lambda value: f'{value:,.2f}'.replace(',', ' ').replace('.', ',')
    load_search = 'R7 SM30 AK-01 AK-02 H200 vlastná tiaž nenosná priečka 300 mm tehla hmotnosť neurčená výber výrobku odhlučnenie'
    vector_checks = {} if reuse is None else reuse['state']['vectorOptimization']
    if reuse is not None:
        print('Reusing verified drawing/image assets; refreshing reports and source metadata.', flush=True)
    for color in ([] if reuse is not None else ['color', 'mono']):
        print(f'Exporting {color}: lossless bundle and 25 standalone sheets…', flush=True)
        source_pdf = SOURCE / f'DOM-CBB-A1-{color}.pdf'
        updated = iso_mtime(source_pdf)
        html = (SOURCE / f'drawing-set-{color}.html').read_text()
        styles = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', html, flags=re.S))
        sections = re.findall(r'<section\b[^>]*data-sheet="([^"]+)"[^>]*>(.*?)</section>', html, flags=re.S)
        require([code for code, _ in sections] == [row['id'] for row in register], f'{color} HTML/register order mismatch')
        original_svgs = []
        for code, section in sections:
            svg_match = re.search(r'(<svg\b.*</svg>)', section, flags=re.S)
            require(svg_match is not None, f'{code}: missing SVG preview')
            svg = svg_match.group(1)
            cut = svg.index('>') + 1
            original_svgs.append(svg[:cut] + '<style><![CDATA[' + styles + ']]></style>' + svg[cut:])
        za_index = next(index for index, row in enumerate(register) if row['id'] == 'D1.1.ZA-03')
        optimized_svg, vector_info = optimize_aggregate(original_svgs[za_index])
        qa_dir = PUBLIC / '.qa' / color
        qa_dir.mkdir(parents=True, exist_ok=True)
        optimized_svg_path, optimized_pdf_path = qa_dir / 'optimized.svg', qa_dir / 'optimized.pdf'
        optimized_svg_path.write_text(optimized_svg)
        subprocess.run(['node', str(ROOT / 'scripts/document-library/compile-svg-pdf.mjs'), str(optimized_svg_path), str(optimized_pdf_path)], check=True)
        vector_checks[color] = {**vector_info, **compare_pdf_renders(source_pdf, za_index + 1, optimized_pdf_path, qa_dir)}
        print(f'  ZA03 vector pattern grouping: {vector_info["faces"]} faces → {vector_info["groups"]} fills; {optimized_pdf_path.stat().st_size:,} bytes', flush=True)
        text = subprocess.check_output(['pdftotext', '-layout', str(source_pdf), '-'], text=True)
        page_texts = text.split('\f')
        if not page_texts[-1].strip():
            page_texts.pop()
        require(len(page_texts) == 25, f'{color} PDF text page count differs')
        label = 'Farebná' if color == 'color' else 'Čiernobiela'
        with pikepdf.open(source_pdf) as pdf:
            original = signatures(pdf)
            require(len(original) == 25, f'{color} source PDF does not have 25 pages')
            for signature in original:
                box = signature['mediaBox']
                require(abs((box[2]-box[0])*25.4/72 - 841) < .3 and abs((box[3]-box[1])*25.4/72 - 594) < .3,
                        'Source sheet is not landscape A1')
            with pikepdf.open(optimized_pdf_path) as replacement:
                replacement_signature = signatures(replacement)[0]
                require(replacement_signature['mediaBox'] == original[za_index]['mediaBox'], 'ZA03 replacement changed its A1 page box')
                pdf.pages[za_index] = replacement.pages[0]
                original[za_index] = replacement_signature
            bundle_path = PUBLIC / 'bundles' / source_pdf.name
            save_pdf(pdf, bundle_path)
            with pikepdf.open(bundle_path) as exported:
                require(signatures(exported) == original, f'{color}: lossless optimization changed page content or page boxes')
            print(f'  bundle {source_pdf.stat().st_size:,} → {bundle_path.stat().st_size:,} bytes', flush=True)
            with tempfile.TemporaryDirectory(prefix='.thumbs-', dir=PUBLIC) as temporary:
                thumb_prefix = Path(temporary) / color
                subprocess.run(['pdftoppm', '-jpeg', '-scale-to', '900', '-jpegopt', 'quality=84,optimize=y',
                                str(bundle_path), str(thumb_prefix)], check=True)
                thumbnails = sorted(Path(temporary).glob(f'{color}-*.jpg'), key=lambda path: int(path.stem.rsplit('-', 1)[1]))
                require(len(thumbnails) == 25, 'Thumbnail export incomplete')
                for index, ((code, section), row, thumbnail) in enumerate(zip(sections, register, thumbnails), start=1):
                    stem = f'{slug(code)}-{color}'
                    pdf_path = PUBLIC / 'sheets' / f'{stem}.pdf'
                    with pikepdf.Pdf.new() as leaf:
                        leaf.pages.append(pdf.pages[index - 1])
                        save_pdf(leaf, pdf_path)
                    with pikepdf.open(pdf_path) as leaf:
                        require(signatures(leaf) == [original[index - 1]], f'{code}: standalone export changed content or paper')
                    svg = original_svgs[index - 1]
                    require('http://www.w3.org/2000/svg' in svg, f'{code}: missing SVG namespace')
                    svg_path = PUBLIC / 'previews' / f'{stem}.svg'
                    svg_path.write_text(svg)
                    thumb_path = PUBLIC / 'thumbnails' / f'{stem}.jpg'
                    shutil.copyfile(thumbnail, thumb_path)
                    other_color = 'mono' if color == 'color' else 'color'
                    search = ' '.join(page_texts[index - 1].split())
                    if code in ['D1.1.ZA-01', 'D1.1.ZA-03']:
                        search += ' ' + load_search
                    documents.append(record(pdf_path, ident=f'sheet-{stem}', title=f'{row["title"]} · {label.lower()}',
                        description=f'{code} · {row["title"]}. Samostatný list z aktuálnej sady C/B/B.',
                        folder=sheet_folder(code), fmt='PDF', status='coordination', updated=updated,
                        code=code, pageCount=1, sheetIndex=index, bundleId=f'bundle-{color}', paper='A1',
                        scale=row['scale'], color=color, previewUrl=URL_PREFIX + '/' + str(svg_path.relative_to(PUBLIC)),
                        thumbnailUrl=URL_PREFIX + '/' + str(thumb_path.relative_to(PUBLIC)), searchText=search,
                        relatedIds=[f'sheet-{slug(code)}-{other_color}', f'bundle-{color}']))
        documents.append(record(bundle_path, ident=f'bundle-{color}', title=f'Kompletná sada A1 · {label.lower()}',
            description='Všetkých 25 listov: pôdorys, pohľady, rezy, základy, strecha, osadenie, otvory, skladby a technické zariadenia.',
            folder='drawings', fmt='PDF', status='coordination', updated=updated, pageCount=25,
            paper='A1', color=color, searchText=' '.join(text.split()) + ' ' + load_search,
            previewUrl=f'{URL_PREFIX}/previews/{slug(register[0]["id"])}-{color}.svg',
            thumbnailUrl=f'{URL_PREFIX}/thumbnails/{slug(register[0]["id"])}-{color}.jpg'))
    for color in ([] if reuse is not None else ['color', 'mono']):
        png_source = SOURCE / f'foundation-axon-{color}.png'
        thumb = PUBLIC / 'thumbnails' / f'foundation-axon-{color}.jpg'
        with Image.open(png_source) as image:
            image = image.convert('RGB')
            image.thumbnail((900, 900))
            image.save(thumb, 'JPEG', quality=86, optimize=True)
        for extension in ['png', 'svg']:
            source = SOURCE / f'foundation-axon-{color}.{extension}'
            target = PUBLIC / 'images' / source.name
            shutil.copyfile(source, target)
            documents.append(record(target, ident=f'image-foundation-axon-{color}-{extension}',
                title=f'Základy · priestorový pohľad · {"farebný" if color == "color" else "čiernobiely"} {extension.upper()}',
                description='Celý L-obrys vrátane lodžie a krytej terasy; R1–R7. Označené návrhové trasy, nie schválená výstuž.',
                folder='images', fmt=extension.upper(), status='coordination', updated=iso_mtime(source), color=color,
                previewUrl=f'{URL_PREFIX}/images/foundation-axon-{color}.png',
                thumbnailUrl=f'{URL_PREFIX}/thumbnails/foundation-axon-{color}.jpg', searchText=load_search,
                relatedIds=[f'sheet-d1-1-za-03-{color}']))
    report_sources = {path.name: path for path in construction}
    report_sources.update({name: ROOT / 'docs' / name for name in REPORTS})
    for name, source in sorted(report_sources.items()):
        text = source.read_text()
        if name in REPORTS:
            title, folder, status, web_url = REPORTS[name]
        else:
            heading = re.search(r'^#\s+(.+)$', text, flags=re.M)
            title, folder, status, web_url = heading.group(1) if heading else source.stem, 'construction-reports', 'coordination', None
        target = PUBLIC / ('archive' if status == 'archive' else 'reports') / name
        shutil.copyfile(source, target)
        extra = {'webUrl': web_url} if web_url else {}
        documents.append(record(target, ident=f'report-{source.stem}', title=title,
            description=('Historická skladba nahradená aktuálnym riešením; nepoužiť pre realizáciu.' if status == 'archive' else 'Úplný text aktuálneho projektového podkladu.'),
            folder=folder, fmt='MD', status=status, updated=iso_mtime(source), searchText=text,
            previewUrl=URL_PREFIX + '/' + str(target.relative_to(PUBLIC)), **extra))
    h200_source = ROOT / 'output/pdf/h200-odborne-zdovodnenie.pdf'
    h200_target = PUBLIC / 'reports' / h200_source.name
    shutil.copyfile(h200_source, h200_target)
    with pikepdf.open(h200_source) as report_pdf:
        report_pages = len(report_pdf.pages)
        paper_sizes = [[float(n) for n in page.mediabox] for page in report_pdf.pages]
        paper = 'A4' if all(abs((box[2]-box[0])*25.4/72-210) < .5 and abs((box[3]-box[1])*25.4/72-297) < .5 for box in paper_sizes) else 'Podľa zdrojového PDF'
    h200_text = subprocess.check_output(['pdftotext', '-layout', str(h200_source), '-'], text=True)
    h200_previews = []
    for page_index, box in enumerate(paper_sizes, start=1):
        preview = PUBLIC / 'previews' / f'h200-odborne-zdovodnenie-{page_index:02d}.svg'
        subprocess.run(['pdftocairo', '-svg', '-f', str(page_index), '-l', str(page_index),
                        str(h200_source), str(preview)], check=True)
        svg = ET.parse(preview).getroot()
        require(svg.tag == '{http://www.w3.org/2000/svg}svg', f'H200 page {page_index}: invalid SVG')
        view_box = [float(value) for value in svg.attrib['viewBox'].split()]
        require(abs(view_box[2] - (box[2]-box[0])) < .01 and abs(view_box[3] - (box[3]-box[1])) < .01,
                f'H200 page {page_index}: SVG changed the source page size')
        h200_previews.append(URL_PREFIX + '/' + str(preview.relative_to(PUBLIC)))
    h200_thumb = PUBLIC / 'thumbnails' / 'h200-odborne-zdovodnenie'
    subprocess.run(['pdftoppm', '-f', '1', '-l', '1', '-singlefile', '-jpeg', '-scale-to', '900',
                    '-jpegopt', 'quality=84,optimize=y', str(h200_source), str(h200_thumb)], check=True)
    documents.append(record(h200_target, ident='report-h200-scientific-pdf', title='H200 · odborné zdôvodnenie · PDF',
        description='Existujúci PDF export odbornej správy. Aktuálny text a napojenie sú dostupné v súvisiacich dokumentoch; PDF nie je statické ani realizačné schválenie.',
        folder='acoustics', fmt='PDF', status='reference', updated=iso_mtime(h200_source), paper=paper, pageCount=report_pages,
        previewUrl=h200_previews[0], pagePreviewUrls=h200_previews,
        thumbnailUrl=URL_PREFIX + '/thumbnails/h200-odborne-zdovodnenie.jpg', searchText=' '.join(h200_text.split()),
        webUrl='/docs/akustika-h200', relatedIds=['report-office-acoustic-wall-scientific-rationale', 'report-office-acoustic-wall-junction']))
    technical = [
        ('model-snapshot', 'Model C/B/B · zdrojové údaje', snapshot, 'coordination', 'C/B/B model súradnice rozmery otvory skladby osi ' + load_search),
        ('drawing-register', 'Register 25 výkresov', register, 'coordination', ' '.join(row['id'] + ' ' + row['title'] for row in register)),
        ('partition-loads', 'SM30 · geometria a podklady zaťaženia', loads, 'coordination', json.dumps(loads, ensure_ascii=False) + ' ' + load_search),
        ('client-brief', 'Zadanie stavebníka · aktuálne požiadavky', snapshot['clientBrief'], 'reference', json.dumps(snapshot['clientBrief'], ensure_ascii=False)),
    ]
    for stem, title, payload, status, search in technical:
        target = PUBLIC / 'model' / f'{stem}.json'
        write_json(target, payload)
        documents.append(record(target, ident=f'model-{stem}', title=title,
            description='Strojovo čitateľný podklad zo zdrojového exportu. Overenie prepočtu nie je statickým schválením.',
            folder='model', fmt='JSON', status=status, updated=iso_mtime(SOURCE / ('drawing-register.json' if stem == 'drawing-register' else 'model-snapshot.json')),
            previewUrl=URL_PREFIX + '/' + str(target.relative_to(PUBLIC)), searchText=search))
    manifest = dict(version=VERSION, generatedAt=datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
                    design='C / B / B', revision=snapshot['clientBrief']['revision'] + ' · R7 / SM30', sourceUpdatedAt=source_updated,
                    folders=[dict(id=ident, title=title, parentId=parent, description=description) for ident, title, parent, description in FOLDERS],
                    documents=documents, featuredIds=['bundle-color', 'sheet-d1-1-za-03-color', 'sheet-d1-1-po-01-color', 'sheet-d1-1-re-02-color'],
                    bundleIds={'color': 'bundle-color', 'mono': 'bundle-mono'})
    assets = validate_assets(manifest, staging=PUBLIC)
    return manifest, assets, vector_checks


def main():
    global PUBLIC, URL_PREFIX
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Rebuild all generated library assets')
    parser.add_argument('--check', action='store_true', help='Validate source freshness and all generated assets; do not generate')
    args = parser.parse_args()
    paths, construction = inputs()
    signature, facts = source_signature(paths)
    render_signature = hashlib.sha256(json.dumps(render_facts(facts), sort_keys=True).encode()).hexdigest()
    cached = json.loads(STATE.read_text()) if STATE.is_file() else None
    reuse = None
    if not args.force and cached and MANIFEST.is_file() and cached.get('inputSignature') == signature:
        try:
            require(sha(MANIFEST) == cached.get('manifestSha256'), 'Generated manifest changed since export')
            manifest = json.loads(MANIFEST.read_text())
            validate_assets(manifest, cached['assets'])
            print(f'Document library current: {len(manifest["documents"])} records; all source hashes and assets verified.', flush=True)
            return
        except RuntimeError as error:
            if args.check:
                raise
            print(f'Rebuilding document library: {error}', flush=True)
    if not args.force and cached and MANIFEST.is_file() and (
            cached.get('renderSignature') == render_signature or h200_only_cache_migration(cached, facts)):
        try:
            require(sha(MANIFEST) == cached.get('manifestSha256'), 'Generated manifest changed since export')
            previous = json.loads(MANIFEST.read_text())
            validate_assets(previous, cached['assets'])
            reuse = {'manifest': previous, 'state': cached}
        except RuntimeError:
            reuse = None
    require(not args.check, 'Document library is missing or stale. Run node scripts/document-library/generate.mjs')
    for executable in ['pdftoppm', 'pdftotext', 'pdftocairo']:
        require(shutil.which(executable), f'{executable} is required; use the bundled Poppler runtime or add it to PATH')
    global pikepdf, Image, PdfReader, PdfWriter
    try:
        import pikepdf
        from PIL import Image
        from pypdf import PdfReader, PdfWriter
    except ImportError as error:
        raise RuntimeError('Missing document-library Python dependencies. Install scripts/document-library/requirements.txt into DOCUMENT_LIBRARY_PYTHON_PACKAGES; see scripts/document-library/README.md') from error
    PUBLIC_BASE.mkdir(parents=True, exist_ok=True)
    PUBLIC = Path(tempfile.mkdtemp(prefix='.staging-', dir=PUBLIC_BASE))
    URL_PREFIX = '/documents/pending'
    manifest, assets, vector_checks = build(construction, reuse)
    final_signature, _ = source_signature(paths)
    require(final_signature == signature, 'Sources changed during export; rerun to avoid a mixed library revision')
    content_signature = hashlib.sha256(json.dumps(assets, sort_keys=True).encode()).hexdigest()[:12]
    final_name = f'g-{signature[:12]}-{content_signature}'
    final_prefix = '/documents/' + final_name
    for document in manifest['documents']:
        for key in ['url', 'previewUrl', 'thumbnailUrl']:
            if document.get(key):
                document[key] = document[key].replace(URL_PREFIX + '/', final_prefix + '/', 1)
        if document.get('pagePreviewUrls'):
            document['pagePreviewUrls'] = [url.replace(URL_PREFIX + '/', final_prefix + '/', 1)
                                           for url in document['pagePreviewUrls']]
    assets = {url.replace(URL_PREFIX + '/', final_prefix + '/', 1): metadata for url, metadata in assets.items()}
    final_dir = PUBLIC_BASE / final_name
    if final_dir.exists():
        # A same-input rerun can reuse identical bytes; repair a corrupted prior
        # generation by swapping directories before publishing the manifest.
        backup = PUBLIC_BASE / f'.old-{final_name}-{os.getpid()}'
        final_dir.rename(backup)
        PUBLIC.rename(final_dir)
        shutil.rmtree(backup)
    else:
        PUBLIC.rename(final_dir)
    validate_assets(manifest, assets)
    write_json(MANIFEST, manifest)
    write_json(STATE, {'inputSignature': signature, 'renderSignature': render_signature, 'inputs': facts, 'manifestSha256': sha(MANIFEST), 'assets': assets,
                       'optimizer': f'pikepdf {pikepdf.__version__} + pypdf resource deduplication; 24 original content streams/page boxes verified; ZA03 vector pattern grouping',
                       'vectorOptimization': vector_checks})
    # Remove only files owned by the previous generated manifest. This also
    # removes the former oversized flat assets from the static build input.
    if cached:
        for url in cached.get('assets', {}):
            if url not in assets:
                old = ROOT / 'public' / url.lstrip('/')
                if old.is_file() and old.is_relative_to(PUBLIC_BASE):
                    old.unlink()
    for stale in PUBLIC_BASE.glob('.staging-*'):
        if stale.is_dir():
            shutil.rmtree(stale)
    print(f'Document library generated: {len(manifest["documents"])} records; 50 standalone A1 PDFs, 2 complete bundles.', flush=True)


if __name__ == '__main__':
    try:
        PUBLIC_BASE.mkdir(parents=True, exist_ok=True)
        with (PUBLIC_BASE / '.build.lock').open('a') as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError('Another document-library export is running; retry after it finishes') from error
            main()
    except Exception as error:
        print(f'Document library failed: {error}', file=sys.stderr)
        sys.exit(1)
