"""Paint the repeated concrete pattern once per visible face group, still vector."""
from pathlib import Path
import subprocess

from lxml import etree
from PIL import Image, ImageChops, ImageStat

SVG = 'http://www.w3.org/2000/svg'


def optimize_aggregate(svg):
    root = etree.fromstring(svg.encode(), etree.XMLParser(strip_cdata=False))
    pattern = 'url(#foundation-axon-aggregate)'
    retained = [(node, dict(node.attrib), node.text) for node in root.iter() if node.get('fill') != pattern]
    groups = 0
    faces = 0
    for parent in list(root.iter()):
        children = list(parent)
        result = []
        index = 0
        while index < len(children):
            def pair(at):
                if at + 1 >= len(children):
                    return False
                base, overlay = children[at:at + 2]
                return (base.tag == f'{{{SVG}}}polygon' and overlay.tag == base.tag
                        and overlay.get('fill') == pattern and base.get('points') == overlay.get('points')
                        and base.get('fill', '').startswith('#'))
            if not pair(index):
                result.append(children[index])
                index += 1
                continue
            bases, overlays = [], []
            while pair(index):
                bases.append(children[index])
                overlays.append(children[index + 1])
                index += 2
            groups += 1
            faces += len(bases)
            # Every solid face is opaque and carries the same user-space pattern.
            # Front faces overwrite rear faces; a union clip applies that same
            # pattern once to the visible union, without changing its phase.
            defs = etree.Element(f'{{{SVG}}}defs')
            clip_id = f'library-concrete-clip-{groups}'
            clip = etree.SubElement(defs, f'{{{SVG}}}clipPath', id=clip_id, clipPathUnits='userSpaceOnUse')
            points = []
            for overlay in overlays:
                polygon = etree.SubElement(clip, f'{{{SVG}}}polygon', points=overlay.get('points'))
                polygon.set('fill', 'black')
                points += [tuple(map(float, item.split(','))) for item in overlay.get('points').split()]
            x0, y0 = min(x for x, _ in points), min(y for _, y in points)
            x1, y1 = max(x for x, _ in points), max(y for _, y in points)
            union = etree.Element(f'{{{SVG}}}rect', x=str(x0), y=str(y0), width=str(x1-x0), height=str(y1-y0), fill=pattern)
            union.set('clip-path', f'url(#{clip_id})')
            result += bases + [defs, union]
        if len(result) != len(children):
            parent[:] = result
    if groups < 2 or faces < 10:
        raise RuntimeError('ZA03 aggregate face structure changed; review the vector optimization')
    if any(dict(node.attrib) != attributes or node.text != text for node, attributes, text in retained):
        raise RuntimeError('ZA03 optimization altered non-pattern geometry or text')
    return etree.tostring(root, encoding='unicode'), {'groups': groups, 'faces': faces, 'originalGeometryAndTextAttributesPreserved': True}


def compare_pdf_renders(source_pdf, source_page, optimized_pdf, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    word_boxes = []
    for filename, page, prefix in [(source_pdf, source_page, 'source'), (optimized_pdf, 1, 'optimized')]:
        xml = subprocess.check_output(['pdftotext', '-f', str(page), '-l', str(page), '-bbox', str(filename), '-'])
        tree = etree.fromstring(xml)
        word_boxes.append([(node.text, *[float(node.get(key)) for key in ['xMin', 'yMin', 'xMax', 'yMax']])
                           for node in tree.xpath('//*[local-name()="word"]')])
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-singlefile', '-r', '60', '-png',
                        str(filename), str(directory / prefix)], check=True)
    if len(word_boxes[0]) != len(word_boxes[1]) or any(
        left[0] != right[0] or any(abs(a-b) > 0.002 for a, b in zip(left[1:], right[1:]))
        for left, right in zip(*word_boxes)
    ):
        raise RuntimeError('ZA03 optimized PDF changed words or their positions')
    with Image.open(directory / 'source.png') as original, Image.open(directory / 'optimized.png') as optimized:
        if original.size != optimized.size:
            raise RuntimeError('ZA03 optimized PDF render dimensions differ from source')
        diff = ImageChops.difference(original.convert('RGB'), optimized.convert('RGB'))
        mean = sum(ImageStat.Stat(diff).mean) / 3
        changed = sum(1 for pixel in diff.getdata() if max(pixel) > 8) / (diff.width * diff.height)
        result = {'dpi': 60, 'meanAbsoluteChannelDifference': mean, 'fractionPixelsDifferenceAbove8': changed,
                  'width': diff.width, 'height': diff.height, 'wordsAndPositionsVerified': len(word_boxes[0]),
                  'note': 'Small differences are limited to concrete-pattern compositing/antialiasing after vector grouping; not a bit-identical raster.'}
        # Grouped transparent pattern compositing can differ slightly in PDF.
        # Geometry attributes and all word positions have separate strict gates.
        if mean > 0.1 or changed > 0.002:
            diff.save(directory / 'difference.png')
            raise RuntimeError(f'ZA03 vector optimization failed visual equivalence: {result}')
        return result
