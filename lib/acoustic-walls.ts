import type { InteriorWall, RectMm } from './twin-interior-baseline';

/** Client's two highlighted walls, 13 Sep 2026. Dimensions exclude finishes. */
export const ACOUSTIC_ASSEMBLY = {
  code: 'SA30',
  name: 'Dvojplášťová akustická priečka',
  totalMm: 300,
  product: 'Leier LeierPLAN 10 P10',
  productUrl: 'https://www.vastap.cz/leier-leierplan-10-p10-P/',
  technicalSheetUrl: 'https://www.vastap.cz/files/download/ZSMA4AgCN2EdFPpyhLgdnfRSjO6pOTHy',
  layers: [
    { id: 'LEAF-W', material: 'masonry', name: 'Leier LeierPLAN 10 P10', thicknessMm: 100 },
    { id: 'WOOL', material: 'mineral-wool', name: 'Minerálna vata', thicknessMm: 100 },
    { id: 'LEAF-E', material: 'masonry', name: 'Leier LeierPLAN 10 P10', thicknessMm: 100 },
  ],
  finishNote: '300 mm = 100 + 100 + 100 mm bez omietok a obkladov. Líca v pôdoryse zostávajú zachované; povrchové úpravy sa určia samostatne.',
  structuralNote: 'Návrh nenosnej priečky. Pôvodné označenie týchto úsekov bolo nosné; zmenu nosného systému a podopretie nadväzujúcich konštrukcií musí overiť statik.',
  acousticNote: 'Nepriezvučnosť Rw celej skladby nie je doložená. Typ minerálnej vaty, kotvenie, obvodové napojenia a prestupy určí akustický detail; medzi plášťami nevytvárať neoverené tuhé mosty.',
  bathroomNote: 'Pri AK-02 vyriešiť kotvenie závesného WC a rozvody v samostatnom detaile; nezasahovať nimi do izolačnej vrstvy bez posúdenia.',
} as const;

export const ACOUSTIC_WALL_SPECS = [
  { wallId: 'C-OPEN-HALL-N', mark: 'AK-01', location: 'Spálňa / chlapčenská izba', rooms: ['ROOM-1-10', 'ROOM-1-09'] },
  { wallId: 'C-OPEN-HALL-S', mark: 'AK-02', location: 'Kúpeľňa / dievčenská izba', rooms: ['ROOM-1-11', 'ROOM-1-08'] },
] as const;

export function acousticWallSpec(wall: Pick<InteriorWall, 'id' | 'rectMm' | 'role'>) {
  // Other studies keep their original 140 mm walls. Rendered corner pieces
  // retain the source id, followed by the standard PART suffix.
  if (wall.role !== 'PARTITION' || wall.rectMm.x1 - wall.rectMm.x0 !== ACOUSTIC_ASSEMBLY.totalMm) return undefined;
  return ACOUSTIC_WALL_SPECS.find(spec => wall.id === spec.wallId || wall.id.startsWith(`${spec.wallId}-PART-`));
}

export function acousticWallLayers(wall: Pick<InteriorWall, 'id' | 'rectMm' | 'role'>) {
  if (!acousticWallSpec(wall)) return [];
  let x = wall.rectMm.x0;
  return ACOUSTIC_ASSEMBLY.layers.map(layer => {
    const rectMm: RectMm = { ...wall.rectMm, x0: x, x1: x + layer.thicknessMm };
    x = rectMm.x1;
    return { ...layer, rectMm };
  });
}

/** Stable model names survive geometry extraction into every plan renderer. */
export function acousticMeshInfo(name: string) {
  const spec = ACOUSTIC_WALL_SPECS.find(w => name.startsWith(`Vnútorná stena ${w.wallId} · SA30 · `) || name.startsWith(`Vnútorná stena ${w.wallId}-PART-`) && name.includes(' · SA30 · '));
  if (!spec) return undefined;
  return { ...spec, material: name.includes(' · WOOL · ') ? 'mineral-wool' as const : 'masonry' as const };
}
