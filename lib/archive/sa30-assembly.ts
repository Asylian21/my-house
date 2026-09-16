// Historical SA30, superseded by single-leaf SM30 on 16 September 2026.
/** Client's two highlighted suite walls, 13 Sep 2026. Dimensions exclude finishes. */
export const ARCHIVED_SA30_ASSEMBLY = {
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
  roomPlaster: { material: 'plaster', name: 'Vápenno-cementová omietka', thicknessMm: 15, densityKgM3: 1800, basis: 'CALCULATION_ASSUMPTION' },
  finishNote: 'Jadro SA30 má 300 mm = 100 + 100 + 100 mm. Výpočet zahŕňa 15 mm vápenno-cementovej omietky na strane každej miestnosti: spolu 330 mm. Omietky do dutiny sa nepridávajú; 100 mm vaty zostáva. Model kótuje 300 mm jadro, omietky sú navyše smerom do izieb. Hydroizolácia, lepidlo a obklad sú ďalšie povrchy.',
  structuralNote: 'Návrh nenosnej priečky. Pôvodné označenie týchto úsekov bolo nosné; zmenu nosného systému a podopretie nadväzujúcich konštrukcií musí overiť statik.',
  acousticNote: 'Predbežný hmotnostný výpočet s omietkami je uvedený v detaile SA30. Ide o scenár oddelených murovaných plášťov, nie o meranie LeierPLAN ani posúdenie skutočných napojení domu. Výpočtový predpoklad: súvislé vzduchotesné omietky 15 mm, hustota 1 800 kg/m³, dutina úplne vyplnená mäkkou minerálnou vlnou vhodnou pre deliace steny. Kotvenie, obvod a prestupy nesmú vytvoriť neoverené tuhé mosty. Výsledok medzi miestnosťami potvrdí posúdenie napojení a vedľajších ciest zvuku.',
  bathroomNote: 'Pri AK-02 vyriešiť kotvenie závesného WC a rozvody v samostatnom detaile; nezasahovať nimi do izolačnej vrstvy bez posúdenia.',
} as const;
