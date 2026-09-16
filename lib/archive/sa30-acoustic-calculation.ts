// Archived comparison only; never use for current AK-01 or AK-02.
import { ARCHIVED_SA30_ASSEMBLY as ACOUSTIC_ASSEMBLY } from './sa30-assembly';

/** Ideal mass–air–mass resonance only; this does not predict a whole-wall Rw. */
export function massAirMassResonanceHz(leafOneKgM2: number, leafTwoKgM2: number, cavityM: number) {
  if (![leafOneKgM2, leafTwoKgM2, cavityM].every(value => Number.isFinite(value) && value > 0)) {
    throw new RangeError('Masses and cavity depth must be finite and positive.');
  }
  return 160 * Math.sqrt(0.111 / cavityM * (1 / leafOneKgM2 + 1 / leafTwoKgM2));
}

/** Ziegel 2022, p. 36, equations 4.10/4.11: a comparison scenario, not a tested Rw. */
export function separatedMasonryScenarioDb(leafOneKgM2: number, leafTwoKgM2: number, cavityMm: number) {
  if (![leafOneKgM2, leafTwoKgM2, cavityMm].every(Number.isFinite)
    || leafOneKgM2 < 100 || leafTwoKgM2 < 100 || cavityMm < 50) {
    throw new RangeError('This scenario requires each plastered leaf ≥ 100 kg/m² and a filled cavity ≥ 50 mm.');
  }
  const equivalentMassDb = 28 * Math.log10(leafOneKgM2 + leafTwoKgM2) - 18;
  const separationBonusDb = 12;
  const flankingCorrectionDb = 0;
  // Retain the basic 12 dB scenario; do not take the additional 2 dB cavity bonus.
  return { equivalentMassDb, separationBonusDb, flankingCorrectionDb,
    apparentRatingDb: equivalentMassDb + separationBonusDb - flankingCorrectionDb };
}

const masonryMassKgM2 = 73;
const plaster = ACOUSTIC_ASSEMBLY.roomPlaster;
const plasterMassKgM2 = plaster.thicknessMm / 1000 * plaster.densityKgM3;
const leafMassKgM2 = masonryMassKgM2 + plasterMassKgM2;
const cavityMm = ACOUSTIC_ASSEMBLY.layers.find(layer => layer.material === 'mineral-wool')!.thicknessMm;
const scenario = separatedMasonryScenarioDb(leafMassKgM2, leafMassKgM2, cavityMm);
const finishedLayers = [
  { id: 'PLASTER-W', material: plaster.material, name: `${plaster.name} · spálňa / kúpeľňa`, thicknessMm: plaster.thicknessMm },
  ...ACOUSTIC_ASSEMBLY.layers,
  { id: 'PLASTER-E', material: plaster.material, name: `${plaster.name} · detská izba`, thicknessMm: plaster.thicknessMm },
] as const;

export const SA30_ACOUSTIC_CALCULATION = {
  status: 'ARCHIVED_SUPERSEDED_20260916',
  masonryMassKgM2,
  plaster,
  plasterMassKgM2,
  leafMassKgM2,
  totalMassKgM2: leafMassKgM2 * 2,
  cavityMm,
  finishedLayers,
  finishedTotalMm: finishedLayers.reduce((sum,layer)=>sum+layer.thicknessMm,0),
  scenario,
  // Keep the source's R′w notation. This is not a laboratory Rw declaration.
  ratingLabel: `R′w,model ≈ ${Math.round(scenario.apparentRatingDb)} dB · výpočet`,
  resonanceHz: massAirMassResonanceHz(leafMassKgM2, leafMassKgM2, cavityMm / 1000),
  productSheetUrl: 'https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf',
  methodUrl: 'https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf',
  scope: 'AK-01 aj AK-02: omietka 15 + tehla 100 + vata 100 + tehla 100 + omietka 15 = 330 mm. Každý tehlový plášť má jednu omietku do izby. Jej hrúbka 15 mm a hustota 1 800 kg/m³ sú predpoklady výpočtu.',
  methodNote: 'Porovnávací hmotnostný scenár podľa Ziegel 2022, s. 34–38 a 57. Zdroj používa R′w pre domové deliace steny; preto výsledok označujeme R′w,model. Základný prírastok za oddelenie je 12 dB. Prídavné 2 dB za širšiu dutinu nezapočítavame. K = 0 je predpoklad bez odpočtu za bočný prenos, nie overenie napojení C/B/B.',
  resonanceNote: 'Rezonancia je pomocná kontrola oddelených plášťov a vzduchu v dutine. Je pod 100 Hz; samotná táto frekvencia neurčuje nepriezvučnosť v dB.',
  rwNote: 'Odhad platí pre idealizované akustické oddelenie plášťov, súvislé vzduchotesné omietky a celoplošnú mäkkú minerálnu výplň vhodnú pre deliace steny (typ WTH podľa zdroja). Použiteľnosť hmotnostného modelu na konkrétny LeierPLAN 10 a jeho napojenia treba potvrdiť. Hodnota 100 kg/m² na plášť je dolná hmotnostná hranica tohto scenára; ľahšia alebo tenšia omietka vyžaduje nový výpočet.',
  siteNote: 'Predikcia skutočného R′w medzi izbami musí zahrnúť spoločnú dosku, strop, bočné steny, kotvy a prestupy; pri AK-01 a AK-02 môže byť odlišná. Uvedený scenár nie je meraním presnej SA30 ani potvrdením výsledku na stavbe.',
  productNote: 'Výrobcom uvedených Rw 35 dB patrí jednej 100 mm priečke s omietkou z oboch strán. Túto hodnotu tu nesčítavame ani nepreberáme: používame hmotnosť muriva 73 kg/m² a jednu izbovú omietku na každý plášť.',
} as const;
