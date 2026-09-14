const SVG_NAMESPACE = 'http://www.w3.org/2000/svg';
// SVG presentation styles inherited from the page must travel with the image.
const PRESENTATION_STYLES = [
  'color', 'display', 'visibility', 'opacity', 'fill', 'fill-opacity', 'fill-rule',
  'stroke', 'stroke-width', 'stroke-opacity', 'stroke-linecap', 'stroke-linejoin',
  'stroke-miterlimit', 'stroke-dasharray', 'stroke-dashoffset', 'vector-effect',
  'paint-order', 'clip-path', 'clip-rule', 'mask', 'filter', 'shape-rendering',
  'font-family', 'font-size', 'font-weight', 'font-style', 'font-stretch',
  'font-feature-settings', 'font-variation-settings', 'font-kerning',
  'text-anchor', 'text-rendering', 'text-decoration', 'letter-spacing',
  'word-spacing', 'dominant-baseline', 'alignment-baseline',
] as const;
const SCREEN_STROKE_STYLES = ['stroke-width', 'stroke-dasharray', 'stroke-dashoffset'] as const;

/** Capture the live plan before awaiting so later pan/layer changes cannot alter the export. */
export async function rasterizePlanView(source: SVGSVGElement, background: string) {
  const { width, height } = source.getBoundingClientRect();
  if (width <= 0 || height <= 0) throw new Error('Najprv zobrazte 2D pôdorys.');

  const copy = source.cloneNode(true) as SVGSVGElement;
  const originals = [source, ...source.querySelectorAll<SVGElement>('*')];
  const copies = [copy, ...copy.querySelectorAll<SVGElement>('*')];
  const screenStrokes: { element: SVGElement; styles: (readonly [string, string])[] }[] = [];
  originals.forEach((element, index) => {
    const style = getComputedStyle(element);
    for (const property of PRESENTATION_STYLES) {
      // Browsers may resolve a local hatch/clip reference against the page URL.
      const value = style.getPropertyValue(property).replace(/url\(["']?[^)"']*#([^)"']+)["']?\)/g, 'url(#$1)');
      if (value) copies[index].style.setProperty(property, value);
    }
    if (style.getPropertyValue('vector-effect') === 'non-scaling-stroke') {
      screenStrokes.push({ element: copies[index], styles: SCREEN_STROKE_STYLES.map(property => [property, style.getPropertyValue(property)] as const) });
    }
  });
  copy.setAttribute('xmlns', SVG_NAMESPACE);
  // Preserve the viewport and crop while rasterizing at a higher resolution.
  copy.setAttribute('width', String(width));
  copy.setAttribute('height', String(height));

  // A 3200 px long edge is sharp enough to share; smaller fallbacks also work
  // on browsers with tighter canvas memory limits.
  for (const edge of [3200, 2400, 1600]) {
    const scale = edge / Math.max(width, height);
    // drawImage enlarges SVG geometry but leaves non-scaling strokes in output
    // pixels. Enlarge those widths and dashes too, using the captured originals.
    for (const { element, styles } of screenStrokes) {
      for (const [property, value] of styles) {
        element.style.setProperty(property, value.replace(/-?(?:\d*\.)?\d+(?:e[-+]?\d+)?(?:px)?/gi, length => `${parseFloat(length) * scale}px`));
      }
    }
    const markup = new XMLSerializer().serializeToString(copy);
    const url = URL.createObjectURL(new Blob([markup], { type: 'image/svg+xml;charset=utf-8' }));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(width * scale));
    canvas.height = Math.max(1, Math.round(height * scale));
    try {
      const context = canvas.getContext('2d');
      if (!context) continue;
      const image = new Image();
      await new Promise<void>((resolve, reject) => {
        image.onload = () => resolve();
        image.onerror = () => reject(new Error('2D pohľad sa nepodarilo vykresliť.'));
        image.src = url;
      });
      context.fillStyle = background;
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/png'));
      if (blob) return { blob, width: canvas.width, height: canvas.height };
    } finally {
      URL.revokeObjectURL(url);
      canvas.width = 0;
      canvas.height = 0;
    }
  }
  throw new Error('Prehliadač odmietol vytvoriť PNG. Skúste export zopakovať.');
}
