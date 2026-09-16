import { useId } from 'react';
import { ACTIVE_ACOUSTIC_WALLS } from '@/lib/twin-interior';
import junction from '@/lib/h200-junction.json';

/** Nominal plan coordinates; the second view deliberately enlarges both 5 mm joints. */
export function H200JunctionFigure() {
  const id = `h200-junction-${useId().replace(/[^a-z0-9_-]/gi, '')}`;
  const ink = '#263747', muted = '#5b6d79', pier = '#46535f', joint = '#c75a23';
  const x = (mm: number) => 140 + (mm - 22639) * .8;
  const y = (mm: number) => 60 + (6870 - mm) * .8;
  const wallEnd = 555;
  const wall = ACTIVE_ACOUSTIC_WALLS.find(wall => wall.mark === 'AK-03')!;
  const layers = wall.layers.map(layer => ({id:layer.id,from:layer.rectMm.y0,to:layer.rectMm.y1,
    board:layer.material==='gypsum-board',fill:layer.material==='masonry'?`url(#${id}-brick)`:
      layer.material==='mineral-wool'?`url(#${id}-wool)`:layer.material==='gypsum-board'?'#436d85':'#e1e7e8'}));
  const j1 = junction.joints.J1, j2 = junction.joints.J2;
  const nibRight = x(22842), boardStart = x(22788), pierRight = x(22783);
  const dim = (at: number, a: number, b: number, label: string) => <g fill={ink} stroke={muted} strokeWidth="1.3">
    <path d={`M${at} ${a}V${b}M${at - 6} ${a + 4}l12 -8M${at - 6} ${b + 4}l12 -8`} fill="none" />
    <text x={at + 12} y={(a + b) / 2 + 6} stroke="none" fontSize="19" fontWeight="600">{label}</text>
  </g>;

  return <figure className="h200-junction-figure">
    {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- The wide drawing must be keyboard-scrollable on narrow screens. */}
    <div className="h200-junction-viewport" role="region" aria-label="Výkres D1; na úzkej obrazovke posúvateľný do strán" tabIndex={0}>
    <svg viewBox="0 0 1000 820" role="img" aria-labelledby={`${id}-title ${id}-description`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      <title id={`${id}-title`}>H200: napojenie na spoločný pilier medzi dverami</title>
      <desc id={`${id}-description`}>Pôdorysná schéma zachováva pevný spoločný pilier a polohu oboch dverí. Oddelenie má dve spojené časti: päť milimetrov pri čele jedinej dosky a päť milimetrov nad výplňou pracovňového ostenia. Z nominálnych 42,5 mm zostáva 37,5 mm pevnej výplne a 5 mm pripojovacej škáry. Zväčšenie ukazuje obe škáry po celej výške steny.</desc>
      <defs>
        <pattern id={`${id}-brick`} width="24" height="24" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="24" height="24" fill="#e7d2c0" /><path d="M0 0V24" stroke="#947159" strokeWidth="1.6" />
        </pattern>
        <pattern id={`${id}-wool`} width="32" height="36" patternUnits="userSpaceOnUse">
          <rect width="32" height="36" fill="#f4ebc7" /><path d="M16 0C0 0 0 18 16 18S32 36 16 36" fill="none" stroke="#9b8b54" strokeWidth="1.5" />
        </pattern>
      </defs>
      <rect x="1" y="1" width="998" height="818" rx="14" fill="#fff" stroke="#d3dde2" />
      <g fontFamily="Arial, sans-serif" fill={ink}>
        <text x="32" y="39" fontSize="23" fontWeight="700">D1 · Napojenie pri dverách</text>
        <text x="32" y="68" fontSize="17" fill={muted}>Pôdorysná schéma · jedna doska · spoločné líce kúpeľne a chodby</text>
        <text x="340" y="112" fontSize="20" fontWeight="700">KÚPEĽŇA</text>
        <text x="340" y="549" fontSize="20" fontWeight="700">PRACOVŇA</text>
        <text x="37" y="239" fontSize="18" fill={muted}>CHODBA</text>

        {/* X 22639–22783 / Y 6322–6701.5, including the connected hall-side T stub. */}
        <path d={`M140 ${y(6701.5)}H${pierRight}V${y(j2.y0)}H${nibRight}V${y(6322)}H140V${y(6412)}H${x(22540)}V${y(6552)}H140Z`} fill={pier} stroke={ink} strokeWidth="1.4" />
        {layers.map(layer => <rect key={layer.id} x={layer.board ? boardStart : pierRight} y={y(layer.to)} width={wallEnd - (layer.board ? boardStart : pierRight)} height={(layer.to - layer.from) * .8} fill={layer.fill} stroke="#53636b" strokeWidth="1" />)}

        {/* Both 5 mm joints follow the shared numeric D1 source. */}
        <rect x={pierRight} y={y(j1.y1)} width="4" height={(j1.y1-j1.y0)*.8} fill={joint} />
        <rect x={pierRight} y={y(j1.y0)} width={nibRight - pierRight} height="4" fill={joint} />
        <path d={`M${pierRight + 2} ${y(j1.y1) + 1}V${y(j1.y0) + 2}H${nibRight - 1}`} fill="none" stroke={joint} strokeWidth="3" />
        <rect x={pierRight - 9} y={y(j1.y1) - 8} width={nibRight - pierRight + 20} height="31" rx="5" fill="none" stroke={joint} strokeWidth="1.4" strokeDasharray="5 4" />

        {/* Short frame/leaf symbols establish the two openings without implying a frame product. */}
        <g stroke="#698698" strokeWidth="2" fill="#dce7ed">
          <path d={`M140 ${y(6701.5)}V122M${pierRight} ${y(6701.5)}V122M140 ${y(6701.5)}H${pierRight}`} fill="none" />
          <rect x={pierRight} y="145" width="66" height="5" />
          <path d={`M140 ${y(6322)}V586M${nibRight} ${y(6322)}V586M140 ${y(6322)}H${nibRight}`} fill="none" />
          <rect x={nibRight} y="574" width="68" height="5" />
        </g>
        <text x="33" y="130" fontSize="17" fill={muted}>dvere</text>
        <text x="33" y="152" fontSize="17" fill={muted}>kúpeľne</text>
        <text x="33" y="558" fontSize="17" fill={muted}>dvere</text>
        <text x="33" y="580" fontSize="17" fill={muted}>pracovne</text>

        {dim(326, y(6701.5), y(wall.rectMm.y1), '149,5 mm')}
        {dim(326, y(j1.y0), y(6322), '42,5 mm')}
        <text x="369" y="502" fontSize="17" fill={joint}>37,5 + 5 mm</text>
        <text x="370" y="358" fontSize="19" fontWeight="700">H200 · 187,5 mm</text>
        <text x="370" y="381" fontSize="16">jedna doska 12,5 mm</text>
        <path d="M555 270v18l-7 7 14 12-14 12 14 12-7 7v104" fill="none" stroke="#53636b" strokeWidth="1.5" />

        <path d="M592 99V596" stroke="#d8e0e5" />
        <text x="620" y="121" fontSize="20" fontWeight="700">Zväčšenie oboch kontaktov</text>
        <text x="620" y="148" fontSize="17" fill={muted}>Škáry sú graficky zväčšené.</text>

        {/* The uninterrupted solid outline denotes infill bonded to the common pier, not a loose sliver. */}
        <path d="M638 227H730V404H873V525H638Z" fill={pier} stroke={ink} strokeWidth="1.5" />
        <rect x="730" y="258" width="230" height="22" fill="#e1e7e8" stroke="#53636b" />
        <rect x="730" y="280" width="230" height="56" fill={`url(#${id}-wool)`} stroke="#53636b" />
        <rect x="742" y="336" width="218" height="56" fill="#436d85" stroke="#53636b" />
        <path d="M730 336H742V392H873V404H730Z" fill="#fae2d2" />
        <path d="M736 339V398H869" fill="none" stroke={joint} strokeWidth="5" />
        <path d="M730 319H742M730 313v12M742 313v12" stroke={joint} strokeWidth="1.5" />
        <rect x="703" y="288" width="68" height="26" rx="3" fill="white" />
        <text x="737" y="308" fontSize="18" fontWeight="700" textAnchor="middle" fill={joint}>5 mm</text>
        <path d="M886 392V404M880 392h12M880 404h12" stroke={joint} strokeWidth="1.5" />
        <text x="906" y="405" fontSize="18" fontWeight="700" fill={joint}>5 mm</text>

        <g fill="white" stroke={joint} strokeWidth="2">
          <path d="M699 355H731M827 398V453H897" fill="none" />
          <circle cx="683" cy="355" r="16" /><circle cx="913" cy="453" r="16" />
        </g>
        <text x="683" y="361" textAnchor="middle" fontSize="18" fontWeight="700" fill={joint}>1</text>
        <text x="913" y="459" textAnchor="middle" fontSize="18" fontWeight="700" fill={joint}>2</text>
        <text x="832" y="369" textAnchor="middle" fontSize="16" fill="#fff">1 × Silentboard</text>
        <text x="650" y="478" fontSize="16" fill="#fff">spoločný pilier +</text>
        <text x="650" y="501" fontSize="16" fill="#fff">pevne pripojená výplň</text>
        <text x="620" y="555" fontSize="17" fill={muted}>Výplň je previazaná s pilierom.</text>
        <text x="620" y="580" fontSize="17" fill={muted}>Zárubňa sa kotví do pevného ostenia.</text>

        <path d="M32 617H968" stroke="#d8e0e5" />
        <circle cx="48" cy="656" r="16" fill="#fae2d2" stroke={joint} strokeWidth="1.5" />
        <text x="48" y="662" fontSize="18" textAnchor="middle" fontWeight="700" fill={joint}>1</text>
        <text x="79" y="651" fontSize="18" fontWeight="700">Čelo jedinej dosky: škára 5 mm</text>
        <text x="79" y="678" fontSize="17" fill={muted}>Trenn-Fix + Uniflott podľa Knauf.</text>
        <circle cx="48" cy="724" r="16" fill="#fae2d2" stroke={joint} strokeWidth="1.5" />
        <text x="48" y="730" fontSize="18" textAnchor="middle" fontWeight="700" fill={joint}>2</text>
        <text x="79" y="719" fontSize="18" fontWeight="700">Nad výplňou ostenia: druhá škára 5 mm</text>
        <text x="79" y="746" fontSize="17" fill={muted}>Pružný akustický tmel; bez sadry či malty.</text>
        <text x="620" y="651" fontSize="18" fontWeight="700" fill={joint}>Spoje po celej výške steny</text>
        <text x="620" y="681" fontSize="17" fill={muted}>Obe časti napojenia spojiť súvislo.</text>
        <text x="620" y="708" fontSize="17" fill={muted}>J1: princíp W623-B2.</text>
        <text x="620" y="735" fontSize="17" fill={muted}>J2: projektové dopracovanie rohu.</text>
        <text x="32" y="793" fontSize="16" fill={muted}>Rozmery v mm. Obvodový UD, podtesnenie a kotvy podľa W623-B2 nie sú v schéme zakreslené.</text>
      </g>
    </svg>
    </div>
    <figcaption>Detail D1 — spoločný pilier zostáva pevnou oporou zárubní. Obe 5 mm škáry prebiehajú po celej výške steny. J1 pri čele dosky: Trenn-Fix a Uniflott. J2 pri líci vonkajšej dosky: mäkké oddelenie a súvislé uzavretie pružným akustickým tmelom na vhodnej podkladovej vrstve; tvar a hĺbka podľa výrobcu tmelu. J2 je projektové dopracovanie, nie skúšaný katalógový detail Knauf. Obvodový UD, podtesnenie a mechanické kotvy podľa W623-B2 nie sú v schéme zakreslené.</figcaption>
  </figure>;
}
