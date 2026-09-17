// Camera coordinates use the existing Babylon scene frame (metres, Y up).
// Only the camera and documentation overlays change; house geometry stays intact.
export const views = [
  { id: 'garden-overview', title: 'Dom zo záhrady', group: 'exterior', position: [-23, 17, -29], target: [2, 2, -1], fov: 0.62,
    description: 'Šikmý pohľad na obe krídla domu. Vidno pôdorys v tvare L, súkromný dvor, bazén a krytú terasu.' },
  { id: 'street', title: 'Uličná strana · vstup a garáž', group: 'exterior', position: [1.8, 3.4, 22], target: [1.8, 2.2, 4], fov: 0.94,
    description: 'Čelný pohľad od ulice: vľavo garáž, uprostred vstup a napravo pracovňa. Ukazuje šírku a výšku hlavného krídla.' },
  { id: 'east', title: 'Pravá bočná strana', group: 'exterior', position: [43, 8, -2], target: [7, 2.2, -2], fov: 0.56,
    description: 'Pohľad na vonkajšiu stranu dlhého krídla, od pracovne až po krytú terasu pri obývačke.' },
  { id: 'rear', title: 'Zadná strana · presklený štít', group: 'exterior', position: [1.8, 8, -39], target: [1.8, 2.4, -1], fov: 0.57,
    description: 'Pohľad zo zadnej časti pozemku. Presklený štít a krytá terasa uzatvárajú vysoký priestor obývačky.' },
  { id: 'west', title: 'Ľavá bočná strana', group: 'exterior', position: [-39, 8, -1], target: [0, 2.2, -1], fov: 0.57,
    description: 'Pohľad od ľavej hranice pozemku na štít garáže, lodžiu a vnútornú záhradnú fasádu dlhého krídla.' },
  { id: 'street-angle', title: 'Vstupný roh zo šikma', group: 'exterior', position: [28, 12, 24], target: [2, 2, -1], fov: 0.72,
    description: 'Šikmý pohľad spája uličnú a pravú fasádu. Vysvetľuje hĺbku domu a napojenie oboch strešných krídel.' },
  { id: 'terrace-angle', title: 'Terasa a záhradné krídlo', group: 'exterior', position: [29, 14, -31], target: [4, 2.3, -2], fov: 0.62,
    description: 'Šikmý pohľad od zadného rohu na krytú terasu, štít a dlhé obytné krídlo.' },
  { id: 'living-vault', title: 'Obývačka · katedrálový strop', group: 'interior', position: [7.1, 1.65, -1.5], target: [9.2, 3.15, -8.1], fov: 1.25,
    description: 'Pohľad z dennej zóny k terase. Obe šikmé plochy stropu sa stretávajú vo vysokom hrebeni nad obývačkou; priestor pokračuje k presklenému štítu.' },
  { id: 'living-kitchen', title: 'Obývačka smerom ku kuchyni', group: 'interior', position: [7.1, 1.65, -8.1], target: [9.3, 2.8, -1.1], fov: 1.25,
    description: 'Opačný pohľad ukazuje spoločný priestor obývačky, jedálne a kuchyne. Šikmý podhľad pokračuje aj nad kuchynskou časťou.' },
  { id: 'living-gable', title: 'Výška priestoru a štítové presklenie', group: 'interior', position: [11.4, 1.6, -3.5], target: [8.8, 3.5, -8.7], fov: 1.2,
    description: 'Šikmý pohľad cez obývačku zachytáva nábytok aj hornú časť presklenia. Pomáha porovnať bežnú výšku zariadenia s otvoreným katedrálovým stropom.' },
];
