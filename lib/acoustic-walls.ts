import type { InteriorWall, RectMm } from './twin-interior-baseline';
import { H200_ACOUSTIC_CALCULATION } from './h200-acoustic-calculation';

/** AK-01/02: ordinary 300 mm exterior-type brick, client revision 16 Sep 2026. */
export const ACOUSTIC_ASSEMBLY = {
  code: 'SM30',
  name: 'Murovaná stena z obvodovej tehly 300 mm',
  totalMm: 300,
  product: 'Klasická obvodová keramická tehla 300 mm · výrobok neurčený',
  layers: [
    { id: 'MASONRY', material: 'masonry', name: 'Klasická obvodová tehla', thicknessMm: 300 },
  ],
  finishNote: 'Jedna vrstva klasickej obvodovej tehly 300 mm, bez minerálnej vaty, dutiny a akustickej predsteny. Bežné omietky a kúpeľňové povrchy sú navyše; model kótuje samotné murivo. Poloha líc a rozmery miestností zostávajú.',
  structuralNote: 'Modelová rola PARTITION zostáva; samotná zámena za 300 mm obvodovú tehlu nepotvrdzuje nosnú funkciu. Statik overí vlastnú hmotnosť podľa vybraného výrobku, podopretie, stabilitu a nadväzujúcu nosnú sústavu.',
  acousticNote: 'Dôvod odhlučnenia medzi susednými miestnosťami zostáva. Nepriezvučnosť novej steny zatiaľ nie je doložená; závisí od konkrétnej tehly, omietok, napojení a prestupov. Výpočet pôvodnej dvojplášťovej SA30 sa na SM30 nevzťahuje.',
  bathroomNote: 'Pri AK-02 vyriešiť kotvenie závesného WC a rozvody pre vybranú 300 mm tehlu. Drážky, prestupy a kotvenie nesmú bez posúdenia oslabiť murivo a odhlučnenie; kúpeľňové povrchy sú navyše.',
} as const;

/** Client-selected H200. The whole-wall Rw is a design prediction, not a test declaration. */
export const OFFICE_ACOUSTIC_ASSEMBLY = {
  code: 'H200',
  name: 'LeierPLAN 10 + akustická predstena Silentboard',
  totalMm: 187.5,
  product: 'LeierPLAN 10 N+F · Devecser + Knauf W623',
  productUrl: 'https://www.vastap.cz/leier-leierplan-10-p10-P/',
  technicalSheetUrl: 'https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf',
  liningSystemUrl: 'https://media.knauf.com/a/EDKwYfTuyWRUkKKKihg9E7',
  calculationSourceUrl: 'https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf',
  scientificReportUrl: '/docs/akustika-h200',
  junctionDetailUrl: '/docs/akustika-h200/napojenie',
  panelOrderSourceUrl: 'https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2',
  requiredRwDb: 51,
  estimatedRwDb: Math.round(H200_ACOUSTIC_CALCULATION.estimatedRwDb),
  layerDirection: 'Od pracovne smerom ku sprche',
  // Model coordinates increase from the office face (south) to the shower (north).
  layers: [
    { id: 'SILENTBOARD-INNER', material: 'gypsum-board', name: 'Knauf Silentboard · jediná doska pracovne', thicknessMm: 12.5 },
    { id: 'LINING-CAVITY', material: 'mineral-wool', name: 'Dutina W623 · pružné závesy, CD 60/27 a vata 40 mm', thicknessMm: 45 },
    { id: 'PLASTER-CAVITY', material: 'plaster', name: 'Súvislá vápenno-cementová omietka · dutina', thicknessMm: 15 },
    { id: 'LEIERPLAN-MASONRY', material: 'masonry', name: 'LeierPLAN 10 N+F · murivo', thicknessMm: 100 },
    { id: 'PLASTER-BATH', material: 'plaster', name: 'Vápenno-cementová omietka · kúpeľňa', thicknessMm: 15 },
  ],
  finishNote: '187,5 mm = 15 + 100 + 15 + 45 + 12,5 mm od sprchy. Jedna doska Silentboard; revízia 16. 9. 2026 ponecháva identifikátor H200. Vata 40 mm aj rošt sú v 45 mm dutine. Hydroizolácia, lepidlo, obklad a prípadná celoplošná stierka sú navyše.',
  structuralNote: 'Nenosná priečka H200. Statik overí stabilitu LeierPLAN 10 pri výške 3 125 mm, založenie, napojenie a náhradu pôvodnej nosnej funkcie. Kotvy a rozstup pružných závesov zvoliť pre konkrétne dutinové murivo a hmotnosť opláštenia.',
  acousticNote: 'Požiadavka Rw ≥ 51 dB; predbežný výpočet s jednou doskou Rw ≈ 55,77 dB (zaokrúhlene 56 dB), pokles 2,15 dB oproti pôvodnému dvojitému oplášteniu. Nie je to nameraná ani výrobcom deklarovaná hodnota tejto kombinácie. W623: pružné Direktschwingabhänger, dutina 45 mm s vatou 40 mm (odpor proti prúdeniu 5–50 kPa·s/m²), jedna Silentboard 12,5 mm na strane pracovne a systémovo utesnené škáry. Potvrdiť jedno opláštenie, rozstupy a kotvy na LeierPLAN 10. Bez pevných mostov. Napojenia, prestupy a vedľajšie cesty zvuku posúdiť samostatne; R′w na stavbe nie je totožné s Rw.',
  bathroomNote: 'Sprcha zostáva na pôvodnom mieste. Súvislá 15 mm omietka zostáva na oboch stranách tehly, aj v dutine. Hydroizoláciu a obklad pridať na kúpeľňovú stranu; inštalácie, kotvenie sprchy a radiátora nesmú premostiť dutinu alebo oslabiť murivo bez detailu.',
} as const;

export const ACOUSTIC_ASSEMBLIES = [ACOUSTIC_ASSEMBLY, OFFICE_ACOUSTIC_ASSEMBLY] as const;

export const ACOUSTIC_WALL_SPECS = [
  { wallId: 'C-OPEN-HALL-N', mark: 'AK-01', location: 'Spálňa / chlapčenská izba', rooms: ['ROOM-1-10', 'ROOM-1-09'], axis: 'x', assembly: ACOUSTIC_ASSEMBLY },
  { wallId: 'C-OPEN-HALL-S', mark: 'AK-02', location: 'Kúpeľňa / dievčenská izba', rooms: ['ROOM-1-11', 'ROOM-1-08'], axis: 'x', assembly: ACOUSTIC_ASSEMBLY },
  { wallId: 'IW-STUDY-NORTH', mark: 'AK-03', location: 'Pracovňa / kúpeľňa so sprchou', rooms: ['ROOM-1-04', 'ROOM-1-05'], axis: 'y', assembly: OFFICE_ACOUSTIC_ASSEMBLY },
] as const;

export function acousticWallSpec(wall: Pick<InteriorWall, 'id' | 'rectMm' | 'role'>) {
  // Other studies keep their original 140 mm walls. Rendered corner pieces
  // retain the source id, followed by the standard PART suffix.
  if (wall.role !== 'PARTITION') return undefined;
  return ACOUSTIC_WALL_SPECS.find(spec =>
    (wall.id === spec.wallId || wall.id.startsWith(`${spec.wallId}-PART-`)) &&
    (spec.axis === 'x' ? wall.rectMm.x1 - wall.rectMm.x0 : wall.rectMm.y1 - wall.rectMm.y0) === spec.assembly.totalMm);
}

export function acousticWallLayers(wall: Pick<InteriorWall, 'id' | 'rectMm' | 'role'>) {
  const spec = acousticWallSpec(wall);
  if (!spec) return [];
  let offset = spec.axis === 'x' ? wall.rectMm.x0 : wall.rectMm.y0;
  return spec.assembly.layers.map(layer => {
    const rectMm: RectMm = spec.axis === 'x'
      ? { ...wall.rectMm, x0: offset, x1: offset + layer.thicknessMm }
      : { ...wall.rectMm, y0: offset, y1: offset + layer.thicknessMm };
    offset += layer.thicknessMm;
    return { ...layer, rectMm };
  });
}

/** Stable model names survive geometry extraction into every plan renderer. */
export function acousticMeshInfo(name: string) {
  const spec = ACOUSTIC_WALL_SPECS.find(w =>
    (name.startsWith(`Vnútorná stena ${w.wallId} · `) || name.startsWith(`Vnútorná stena ${w.wallId}-PART-`)) && name.includes(` · ${w.assembly.code} · `));
  if (!spec) return undefined;
  const layer = spec.assembly.layers.find(l => name.includes(` · ${l.id} · `));
  return layer ? { ...spec, material: layer.material } : undefined;
}
