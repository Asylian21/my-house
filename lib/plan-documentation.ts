import generated from './plan-geometry.generated.json';
import { ACOUSTIC_WALL_SPECS, acousticMeshInfo } from './acoustic-walls';
import { BEDROOM_FITOUT, CHILDRENS_BEDROOM_FITOUTS, HALLWAY_BUILT_IN_WARDROBES, INTERIOR_DOORS, INTERIOR_ROOMS, KITCHEN_DESIGN, KITCHEN_ISLAND, KITCHEN_RUN, OFFICE_FITOUT, roomAreaM2, roomBoundsMm, type RectMm } from './twin-interior';
import { DEFAULT_LIVING_LAYOUT_ID, LIVING_LAYOUTS, LIVING_LAYOUT_IDS, diningTableRectMm, type LivingLayoutId } from './twin-living-layouts';
import { HOUSE } from './twin-active-house';
import { CHILDREN_WINDOW_DESIGN } from './twin-children-design';
import { HEATING_SOURCES, HEATING_LAYOUTS, DEFAULT_HEATING_LAYOUT_ID, heatingRoomNotes, heatingTransportNote, type HeatingLayoutId } from './technical-design';

export type PlanCategory = 'furniture'|'equipment'|'lighting'|'walls'|'openings'|'finishes';
export const PLAN_CATEGORIES:Record<PlanCategory,string>={furniture:'Nábytok',equipment:'Vybavenie',lighting:'Svetlá',walls:'Steny',openings:'Okná a dvere',finishes:'Povrchy a detaily'};
export type PlanMesh=typeof generated.meshes[number];
/** Layer suffix of an exterior wall mesh: 300 mm masonry, 200 mm contact insulation or a solid uninsulated pier. */
const WALL_LAYER_SUFFIX=/ · (murivo|izolácia|plné murivo)$/;
export type ExteriorWallLayer='masonry'|'insulation'|'solid';
/** Which layer of the exterior wall build-up a shell wall mesh is; interior walls and unlayered pieces read as masonry. */
export const exteriorWallLayer=(mesh:Pick<PlanMesh,'name'>):ExteriorWallLayer=>/ · izolácia$/.test(mesh.name)?'insulation':/ · plné murivo$/.test(mesh.name)?'solid':'masonry';
export interface PlanItem {
  id:string; name:string; category:PlanCategory; roomId:string; meshes:PlanMesh[];
  rect:RectMm; z0:number; z1:number; nominal?:RectMm; note?:string;
  /** Living-room pieces exist once per layout; shared items carry no layout. */
  layout?:LivingLayoutId;
  heatingLayout?:HeatingLayoutId;
  opening?:{width:number;height:number;sill:number;clearWidth?:number};
  product?:{label:string;dimensions:string;source:string};
}
export const PLAN_ROOM_NOTES:Record<string,string[]>={
  'ROOM-1-04':['AK-03 / H200 je finálne zvolená skladba: od sprchy 15 mm VC omietka + 100 mm LeierPLAN 10 + 15 mm omietka + 45 mm dutina W623 na pružných závesoch s vatou 40 mm + 1 × 12,5 mm Silentboard. Spolu 187,5 mm, hydroizolácia a obklad navyše. Požiadavka Rw ≥ 51 dB; predbežný výpočet ≈ 56 dB, presnú zostavu a napojenia treba potvrdiť.','Líce kúpeľne je zarovnané s chodbovou priečkou na Y 6 552 mm, líce pracovne je na Y 6 364,5 mm. Dvere aj vstupný roh pracovne sú posunuté o 30 mm k ulici; ostenie má 42,5 mm. Pracovňa má 12,14 m². Otvor kúpeľne aj zatvorené krídlo sú na osi X chodby, Y 7 101,5 mm.'],
  'ROOM-1-02':['Chodba medzi detskými izbami je vystredená medzi fasádami: južná priečka 140 mm leží na 6 412–6 552 mm, severná na 7 651–7 791 mm, medzi nimi je 1 099 mm. Obe detské izby sú tak rovnako hlboké (2 908 mm). Severná stena je jedna rovina od šatníka cez dvere spálne po východnú nosnú stenu chlapčenskej izby; južná priečka pokračuje pri zádverí až k rohu pracovne.','Stena k dievčenskej izbe a zádveriu je priečka 140 mm namiesto 199 mm. Plocha chodby je 16,28 m² (predtým 17,46 m²): stena kúpeľne s dverami z chodby leží na tej istej rovine 6 412–6 552 mm, takže bývalý koniec chodby pred kúpeľňou patrí kúpeľni. Puzdro posuvných dverí zo zádveria je v tejto priečke; jeho hrúbku potvrdí dodávateľ. Skriňa na konci chodby má 1 099 × 460 mm medzi stenou kúpeľne a rovinou 7 651 mm (predtým 1 907 mm), skriňa pri dvore 2 768 × 701 mm za priečkou 140 mm.'],
  'ROOM-1-08':['Jedno dvojkrídlové okno 1 800 × 1 500 mm s parapetom 900 mm, presne v osi dverí a v strede izby. Dve rovnaké otváravé krídla v štíhlom antracitovom ráme 45 mm; zhodné s oknom chlapčenskej izby.','Západná murovaná stena AK-02 / SM30 má 300 mm (jedna vrstva klasickej obvodovej tehly; dôvod odhlučnenia zostáva); východná stena je nosná 300 mm. Západná priečka (líce 15 243 mm) je o 100 mm bližšie než predtým v prospech spálne a kúpeľne, východná k zádveriu je v jednej línii so stenou chlapčenskej izby. Izba má 5 298 × 2 908 mm (15,41 m²), presne ako chlapčenská: chodba je vystredená a stena k nej leží na 6 412 mm. Okno je uprostred medzi posteľou a pracovným stolom; oba bočné pásy muriva majú 1 749 mm.','Dvere 900 mm sú vystredené na dĺžku izby (17 442–18 342 mm) a ležia presne oproti dverám chlapčenskej izby. Kľučka je na ľavej strane otvoru v pôdoryse, pánty vpravo; krídlo sa otvára dovnútra izby. Zariadenie je zrkadlovým obrazom chlapčenskej izby: skriňa 2 150 × 600 mm stojí pri stene chodby v rohu pri zádverí, 49 mm za hranou dverného otvoru, tesne vedľa krídla otvoreného na 90°; regál na hračky je zrušený.'],
  'ROOM-1-09':['Jedno dvojkrídlové okno 1 800 × 1 500 mm s parapetom 900 mm, presne v osi dverí a v strede izby. Zhodný antracitový rám 45 mm aj dve otváravé krídla ako v dievčenskej izbe. Pôvodný pevný pás aj samostatné okno sú odstránené. Nástenka zostáva na bočnej stene.','Izba má 5 298 × 2 908 mm (15,41 m²), presne ako dievčenská: západná murovaná stena AK-01 / SM30 (jedna 300 mm obvodová tehla, účel odhlučnenia zostáva) je o 100 mm bližšie v prospech spálne a kúpeľne a stena k chodbe leží na 7 791 mm, v jednej rovine so stenou spálne a šatníka. Okno začína 209 mm za bočnou hranou postele a končí 449 mm pred stolom.','Dvere 900 mm sú vystredené (17 442–18 342 mm) presne oproti dverám dievčenskej izby. Kľučka je na ľavej strane otvoru v pôdoryse, pánty vpravo; krídlo sa naďalej otvára dovnútra izby. Skriňa 2 150 × 600 mm stojí pri stene chodby v rohu pri zádverí, 49 mm za hranou dverného otvoru, tesne vedľa krídla otvoreného na 90°; regál na hračky je zrušený.'],
  'ROOM-1-10':['Murovaná stena AK-01 / SM30 k chlapčenskej izbe má jednu vrstvu klasickej obvodovej tehly 300 mm s ponechaným dôvodom odhlučnenia; jej poloha je o 100 mm ďalej a južná stena spálne leží na rovine chodby 7 651–7 791 mm: spálňa má 3 800 × 2 908 mm (11,05 m²), po bokoch postele zostáva 554 mm a pred nohami 1 600 mm. Šatník za posuvnými dverami má 2 200 × 1 907 mm (4,20 m²).'],
  'ROOM-1-11':['Kúpeľňa má po posune priečky ku garáži o 50 cm tvar L: 1 961 × 2 100 mm pri ulici a rozšírenie 1 460 × 808 mm pri chodbe, spolu 5,30 m². Garáž získala 1,05 m² a jej bočný výklenok má 2 000 × 2 100 mm. Dvere 800 mm oproti spálni zostávajú na mieste. Vysoké okno je vystredené na šírku kúpeľne nad vaňou; garážové okno zostáva na mieste. Úprava je spoločná pre varianty obývačky A aj B.','Podľa dodaného obrázka leží vaňa 1 961 × 750 mm pod vysokým oknom cez celú šírku kúpeľne, od steny pri garáži po protiľahlú murovanú stenu AK-02 / SM30, bez bočnej medzery. Závesné WC je vpravo pri murovanej stene AK-02 a smeruje doľava. Kotvenie rámu a rozvody vyžadujú detail pre vybranú 300 mm obvodovú tehlu; požiadavka odhlučnenia zostáva. Umývadlová skrinka 900 × 500 mm je vľavo pri priečke ku garáži, so zrkadlom na tejto stene. Medzi čelom umývadlovej skrinky a obrysom WC je 761 mm; pred umývadlom je vyhradený priestor 750 × 900 mm. Namiesto vysokej skrine je pri dverách na stene šatníka matný čierny rebríkový radiátor 600 × 1 500 mm s hĺbkou 100 mm, spodnou hranou 200 mm nad podlahou a 15 priečkami na uteráky.'],
  'ROOM-1-06':['WC získalo ďalších 370 mm oproti predchádzajúcej verzii. Medzi priečkami má 1 899 × 1 800 mm a plochu 3,42 m² (predtým 2,75 m²). Po 10 mm obklade je šírka približne 1 879 mm.','Misa je vystredená na novej osi miestnosti. Umývadlo má 550 × 350 mm. Klasické dvere s krídlom 700 mm sa otvárajú dovnútra k severnej stene; vstupný otvor zostáva na mieste. Celý oblúk vrátane kľučiek je bez kolízie so sanitou.','Severná stena k obývačke je od 12. 9. 2026 nosné murivo 300 mm (10 712–11 012 mm) namiesto priečky 140 mm: stojí nad priečnym základovým pásom a nesie veniec s oceľovými rámami krovu katedrálového stropu obývačky. Zhrubla smerom do kuchyne, takže južné líce na 10 712 mm, plocha WC aj dvere zostávajú.'],
  'ROOM-1-05':['Priečka pri práčovni pokračuje v rovine steny WC bez zuba: líce technickej sa posunulo o 422 mm, kúpeľňové líce o 417 mm. Kúpeľňa a práčovňa má po zarovnaní H200 s chodbou 7,21 m². Zostava má 1 899 mm: umývadlová skrinka 1 213 mm s umývadlom 800 mm a vetraná veža pre práčku a sušičku, obe 600 × 600 mm. Pred spotrebičmi je vyhradený pás 900 mm. Sprcha zostáva na pôvodnom mieste.'],
  'ROOM-1-07':heatingRoomNotes(DEFAULT_HEATING_LAYOUT_ID),
};
export const unionBounds=(rects:readonly RectMm[]):RectMm=>({x0:Math.min(...rects.map(r=>r.x0)),y0:Math.min(...rects.map(r=>r.y0)),x1:Math.max(...rects.map(r=>r.x1)),y1:Math.max(...rects.map(r=>r.y1))});
export const rectSize=(r:RectMm)=>[r.x1-r.x0,r.y1-r.y0] as const;
export const numberSk=(n:number,digits=0)=>n.toLocaleString('sk-SK',{maximumFractionDigits:digits});
export const formatMm=(n:number,unit:'mm'|'cm'|'m'='mm')=>`${numberSk(n/(unit==='m'?1000:unit==='cm'?10:1),unit==='m'?3:unit==='cm'?1:0)} ${unit}`;
export const normalizeSearch=(value:string)=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const names:Record<string,string>={BED:'Posteľ',WARDROBE:'Šatníková skriňa',DESK:'Pracovný stôl',CHAIR:'Stolička',FEATURE:'Nástenný panel',ART:'Obraz',LIGHT:'Svietidlo',BOOKS:'Knižnica',READING:'Čitateľský puf',PLAY:'Hrací koberec',DRAWING:'Kreslenie a pastelky',BENCH:'Lavička s botníkom',HOOKS:'Vešiakový panel',OVERHEAD:'Horná skriňa',MIRROR:'Zrkadlo',CABINET:'Skriňová zostava',PRINTER:'Tlačiareň','MONITOR-40-21:9':'Monitor',WHITEBOARD:'Magnetická tabuľa','UTILITY-SINK':'Pracovný drez','GARAGE-RACK':'Úložný regál','GARAGE-SHELF':'Nástenné police',PEGBOARD:'Náradie na stene','LONG-TOOL':'Záhradné náradie',MOWER:'Kosačka','GARAGE-CLUTTER':'Uložené predmety','WOOD-PELLET-BOILER':'Kotol na drevo a pelety','PELLET-HOPPER':'Zásobník peliet','PELLET-AUGER':'Podávač peliet','PELLET-BURNER':'Horák','PELLET-FEED-HOSE':'Hadica podávača','BUFFER-TANK-1000L':'Akumulačná nádrž','BUFFER-TANK-800L':'Akumulačná nádrž','WALL-HUNG-WC':'Závesné WC','COMPACT-BASIN':'Umývadlo so zrkadlom','BATH-1700':'Vaňa','BATH-WALL':'Vaňa',WC:'WC',WINDOW:'Obklad pri okne','VANITY-900':'Umývadlová skrinka so zrkadlom','WALK-IN-1250':'Sprchovací kút','BUILT-IN-2616':'Kúpeľňová zostava','LAUNDRY-TOWER':'Práčovňová skriňa','TOWEL-RADIATOR-600':'Rebríkový radiátor','BATH-105-WASHER':'Práčka','BATH-105-DRYER':'Sušička'};
function semantic(mesh:PlanMesh):[string,string,PlanCategory] {
  const n=mesh.name, [prefix,tag='',part='']=n.split(' · ');
  const acoustic=acousticMeshInfo(n);
  if(acoustic)return [acoustic.mark,`${acoustic.mark} · ${acoustic.assembly.name} (${acoustic.assembly.code})`,'walls'];
  if(/^(Lounge pohovka|Lounge ležadlo|Nízky stolík|Terasový stôl|Terasová stolička)/.test(prefix))return [prefix,prefix.replace(' z 3D','').replace('Lounge pohovka','Terasová pohovka').replace('Lounge ležadlo','Terasové ležadlo'),'furniture'];
  if(prefix==='GARAGE-DOOR')return [prefix,'Sekčná garážová brána','openings'];
  if(prefix.startsWith('FLUE-'))return [prefix,'Zvislý dymovod','equipment'];
  if (/Škoda Superb|Superb Combi/.test(n)) return ['vehicle','Škoda Superb Combi','equipment'];
  if (n.startsWith('Vnútorná stena')) return [prefix, n.includes('nosná')?'Nosná vnútorná stena':'Vnútorná priečka','walls'];
  const interiorDoor=INTERIOR_DOORS.find(door=>n.startsWith(`${door.label} · `));
  if(interiorDoor)return [interiorDoor.label.split(' · ')[0],interiorDoor.label.split(' · ')[0],'openings'];
  if (/^Podkladová|^1\.\d/.test(n)) {
    const room=n.match(/^1\.\d+/)?.[0]??'dom';
    const kind=/podhľad|štít/.test(n)?'Podhľad':/podlaha/.test(n)?'Podlaha':/obklad/.test(n)?'Obklad stien':/soklová/.test(n)?'Soklové lišty':'Podkladová doska';
    return [`${room}-${kind}`,kind,'finishes'];
  }
  if(mesh.source==='shell') {
    if(n.includes('Lodžia')&&n.includes('presklené dvere'))return ['LOGGIA-DOOR','Garáž → krytý zárez','openings'];
    // Facade segments come as masonry + insulation layers (or one solid pier); both layers form one documented segment.
    const segment=n.match(/^(.*) · (úsek \d+) · (murivo|izolácia|plné murivo)$/);
    if(segment) return [`${segment[1]} · ${segment[2]}`,`${segment[1]} · ${segment[2]}`,'walls'];
    if(/Výplň|výplň|presklenie|garážové okno|svetlík/.test(n)) return [prefix.startsWith('Krytá')?`${prefix}-glazing`:prefix,prefix.includes('FRONT-ENTRY')?'Hlavné vstupné dvere':prefix.includes('EAST-03')?'Dvere technickej miestnosti':prefix.startsWith('Krytá')?'Pevné presklenie terasy':prefix.replace('Výplň otvoru','Okno').replace('Bočná výplň otvoru','Bočné okno'),'openings'];
    const base=n.replace(WALL_LAYER_SUFFIX,'');
    return [base,base.replace(/modřínový/gi,'smrekovcový').replace(/modřínové/gi,'Smrekovcové'),WALL_LAYER_SUFFIX.test(n)||/stena|pilier|podpor/.test(n)?'walls':'finishes'];
  }
  if(/FIREPLACE/.test(prefix))return [prefix,'Krbové kachle','equipment'];
  const wardrobe=HALLWAY_BUILT_IN_WARDROBES.find(w=>w.id===prefix);
  if(wardrobe)return [prefix,wardrobe.label.replace(/ · (posuvné|otváravé) dubové čelá$/,'')+(prefix==='C-DRESSING-0'?' · ľavá':prefix==='C-DRESSING-1'?' · pravá':''),'furniture'];
  if(/koberec|koberca/.test(n)||tag==='PLAY')return [`${prefix}-rug-${tag==='PLAY'?'play':'bed'}`,tag==='PLAY'?'Hrací koberec':'Koberec','finishes'];
  if(prefix==='LIVING-103-SOFA-L') {
    if(/stolíka|stolík/.test(n))return [`coffee-${n.match(/\d+$/)?.[0]}`,`Konferenčný stolík ${n.match(/\d+$/)?.[0]}`,'furniture'];
    return ['sofa','Rohová sedačka','furniture'];
  }
  if(prefix==='LIVING-103-TV-WALL')return [prefix,/TV/.test(prefix)?'TV stena':'Skrinka','furniture'];
  if(prefix==='LIVING-103-DINING') {
    // Chairs are numbered 1–3 on the kitchen-side / wall-side row (S or W) and 4–6 on the other (N or E).
    if(tag.startsWith('DINING-CHAIR')) return [tag,`Jedálenská stolička ${(/[SW]\d$/.test(tag)?0:3)+Number(tag.slice(-1))}`,'furniture'];
    if(n.includes('svietidlo'))return ['dining-light','Závesné svietidlo nad stolom','lighting'];
    return ['dining-table','Jedálenský stôl','furniture'];
  }
  if(prefix==='KITCHEN-RUN') {
    if(tag==='FRIDGE-600')return ['kitchen-fridge','Chladnička s mrazničkou','equipment'];
    if(tag==='OVEN-ELEVATED')return ['kitchen-oven','Rúra vo výške · zasúvacie dvierka','equipment'];
    if(tag==='OVEN-TOWER')return ['kitchen-oven-tower','Vysoká skriňa pre rúru','furniture'];
    if(tag==='DISHWASHER')return ['kitchen-dishwasher','Integrovaná umývačka','equipment'];
    if(tag==='ISLAND-LIGHT')return ['kitchen-island-light','Lineárne svetlo nad ostrovčekom','lighting'];
    if(tag==='ostrovček')return ['kitchen-island','Kuchynský ostrovček','furniture'];
    if(/odsávač/.test(n))return ['kitchen-extractor','Odsávač pár','equipment'];
    if(/varná/.test(n))return ['kitchen-hob','Varná doska','equipment'];
    if(/drez|batéri/.test(n)&&!n.includes('úchytka'))return ['kitchen-sink','Drez a batéria','equipment'];
    if(/horn[éý]|horných|LED/.test(n))return ['kitchen-upper','Horné kuchynské skrinky','furniture'];
    if(tag==='L-RETURN-EAST')return ['kitchen-return','Bočné rameno kuchyne','furniture'];
    if(/polostrov|ostrovč/.test(n))return ['kitchen-island','Kuchynský ostrovček','furniture'];
    return ['kitchen-back','Zadná kuchynská linka','furniture'];
  }
  let key=tag, label=names[tag]??tag;
  if(tag==='LAUNDRY-TOWER'&&/ · (WASHER|DRYER) · /.test(n)){key=n.includes(' · WASHER · ')?'WASHER':'DRYER';label=key==='WASHER'?'Práčka':'Sušička';}
  if(tag==='DESK'&&/moodboard|korkov/.test(n)){key='board';label='Nástenka';}
  if(tag==='DESK'&&/lampa|lampy/.test(n)){key='lamp';label='Stolová lampa';}
  if(tag.startsWith('PELLET-BAG-'))label=`Vrece peliet 15 kg · ${tag.slice(-1)}`;
  if(tag==='VACUUM')label='Tyčový vysávač na stene · rezerva';
  if(tag==='STORAGE-CABINET')label='Plytká servisná skriňa pri práčovni';
  if(tag==='HYDRAULIC-RESERVE')label='Rezerva pre hydrauliku';
  if(tag==='SAFETY-GROUP')label='Pojistná skupina KSG mini';
  if(tag==='BOILER-BASE')label='Nehorľavý podstavec kotla';
  if(tag==='BOILER-FLUE')label='Dymovod nahor · montážny návrh';
  if(tag==='OPEN-SHELVING')label='Oceľový regál pri vonkajších dverách';
  if(tag==='NIGHTSTAND'){key+=n.match(/\d+$/)?.[0]??'';label=`Nočný stolík ${n.match(/\d+$/)?.[0]??''}`;}
  if(tag==='GARAGE-CLUTTER'){key=part.replace('páska krabice','kartónová krabica');label=key;}
  if(prefix===BEDROOM_FITOUT.id&&tag==='LIGHT'){key+=part.match(/\d+$/)?.[0]??'-ceiling';label=/\d+$/.test(part)?`Čítacie svietidlo ${part.match(/\d+$/)?.[0]}`:'Stropné svietidlo';}
  const category:PlanCategory=/LIGHT|lamp/.test(key)?'lighting':/FEATURE|ART|WINDOW|DRAWING/.test(tag)?'finishes':/TECHNICAL|BATHROOM|^WC-|GARAGE/.test(prefix)?'equipment':'furniture';
  return [`${prefix}-${key}`,label||prefix,category];
}
function closestRoom(r:RectMm) {
  const cx=(r.x0+r.x1)/2,cy=(r.y0+r.y1)/2;
  return [...INTERIOR_ROOMS].sort((a,b)=>{
    const dist=(room:typeof a)=>Math.min(...room.rectsMm.map(p=>Math.hypot(Math.max(p.x0-cx,0,cx-p.x1),Math.max(p.y0-cy,0,cy-p.y1))));
    return dist(a)-dist(b);
  })[0].id;
}
/** Item id suffix of a living-room layout; the default layout keeps the plain ids. */
export const layoutSuffix=(layout:LivingLayoutId)=>layout===DEFAULT_LIVING_LAYOUT_ID?'':`-${layout}`;
/** Variant pieces get their own item ids unless the id already names the variant (stove, flue). */
function layoutItemId(base:string,layout:LivingLayoutId|undefined) {
  if(!layout)return base;
  const spec=LIVING_LAYOUTS[layout];
  return base===spec.stove.id||base===spec.stove.flue.id?base:`${base}${layoutSuffix(layout)}`;
}
const grouped=new Map<string,PlanItem>();
for(const mesh of generated.meshes) {
  const [base,name,category]=semantic(mesh);
  const layout=mesh.layout as LivingLayoutId|undefined;
  const heatingLayout=mesh.heatingLayout as HeatingLayoutId|undefined;
  const id=layoutItemId(base,layout);
  const item=grouped.get(id)??{id,name,category,roomId:'',meshes:[],rect:mesh.rect,z0:mesh.z0,z1:mesh.z1,...(layout?{layout}:{}),...(heatingLayout?{heatingLayout}:{})};
  item.meshes.push(mesh);grouped.set(id,item);
}
const openingSpecs=[...HOUSE.facades.front.openings,...HOUSE.facades.east.openings,...HOUSE.facades.garden.openings,HOUSE.facades.west.garageWindow];
/** Every documented item of the model, including both living-room layouts. */
export const PLAN_ITEMS_ALL:PlanItem[]=[...grouped.values()].map(item=>{
  item.rect=unionBounds(item.meshes.map(m=>m.rect));item.z0=Math.min(...item.meshes.map(m=>m.z0));item.z1=Math.max(...item.meshes.map(m=>m.z1));item.roomId=closestRoom(item.rect);
  const acoustic=ACOUSTIC_WALL_SPECS.find(w=>w.mark===item.id);
  if(acoustic){item.roomId=acoustic.rooms[0];item.nominal=item.rect;item.note=`${acoustic.location}. ${acoustic.assembly.finishNote}`;}
  if(item.id==='Vnútorná stena C-GARAGE-PARTITION'){
    item.name='Garáž / spálňa a šatník · priečka 140 mm';
    item.roomId='ROOM-1-12';item.nominal=item.rect;
    item.note='SP14 · bežná murovaná priečka 140 mm podľa zadania zo 16. 9. 2026. Líce pri izbách X 11 143 mm zostáva; garáž získava 161 mm. Úsek Y 5 744–8 749 mm končí pri zadnej stene garáže. Vonkajšie pokračovanie pri lodžii a jeho zateplenie zostávajú v pôvodnej hrúbke.';
  }
  if(item.id==='C-GARAGE-FITOUT-MOWER')item.note='Kosačka posunutá o 161 mm k novej priečke podľa zadania zo 16. 9. 2026. Medzi pravým okrajom jej pôdorysného obalu a stenou zostáva 20 mm.';
  if(item.id==='C-GARAGE-FITOUT-GARAGE-RACK')item.note='Regál skrátený na 1 839 × 500 mm, výška 2 100 mm. Ľavá hrana X 11 003 mm lícuje s priečkou aj zarovnaným návratom steny; pôvodný 161 mm zub je odstránený.';
  const numberedRoom=item.id.match(/^1\.\d+/)?.[0];
  if(numberedRoom)item.roomId=INTERIOR_ROOMS.find(r=>r.number===numberedRoom)?.id??item.roomId;
  if(/^(Lounge|Nízky stolík|Terasový stôl|Terasová stolička)/.test(item.id))item.roomId='EXTERIOR';
  const wardrobe=HALLWAY_BUILT_IN_WARDROBES.find(w=>w.id===item.id);
  if(wardrobe){item.nominal=wardrobe.footprintMm;item.roomId=wardrobe.roomId;}
  for(const fit of CHILDRENS_BEDROOM_FITOUTS) {
    if(item.id.startsWith(fit.id))item.roomId=fit.roomId;
    for(const [tag,value] of Object.entries({BED:fit.bed.footprintMm,DESK:fit.desk.footprintMm,WARDROBE:fit.wardrobe.footprintMm}))if(item.id===`${fit.id}-${tag}`)item.nominal=value;
    if(item.id===`${fit.id}-BED`)item.note=`Matrac ${formatMm(fit.bed.mattressWidthMm)} × ${formatMm(fit.bed.mattressLengthMm)}. Rám je väčší než matrac.`;
  }
  if(item.id===`${BEDROOM_FITOUT.id}-BED`)item.nominal=BEDROOM_FITOUT.bed.footprintMm;
  if(item.id===`${OFFICE_FITOUT.id}-DESK`){
    const desk=OFFICE_FITOUT.desk,p=desk.product;
    item.nominal=desk.footprintMm;
    item.name='Pracovný stôl · AlzaErgo ET1 NewGen';
    item.product={label:p.label,dimensions:`${formatMm(p.widthMm)} × ${formatMm(p.depthMm)} × ${formatMm(p.topThicknessMm)} · doska`,source:p.source};
    item.note=`Čierna laminovaná doska a čierna oceľová podnož, dva motory, trojsegmentové stĺpy. Horná plocha je v modeli ${formatMm(desk.topElevationMm)} nad podlahou; Alza uvádza rozsah nastavenia ${formatMm(p.listedHeightRangeMm[0])}–${formatMm(p.listedHeightRangeMm[1])}. Rozmery dosky sú podľa vybraného výrobku; drobné diely podnože sú modelované podľa produktovej fotografie.`;
  }
  for(const layoutId of LIVING_LAYOUT_IDS){
    const spec=LIVING_LAYOUTS[layoutId],suffix=layoutSuffix(layoutId);
    if(item.id===`sofa${suffix}`)item.nominal=unionBounds([spec.fitout.sofa.mainRectMm,spec.fitout.sofa.chaiseRectMm]);
    if(item.id===`LIVING-103-TV-WALL${suffix}`)item.nominal=spec.fitout.tvWall.rectMm;
    if(item.id===`dining-table${suffix}`)item.nominal=diningTableRectMm(spec.fitout.dining);
    if(item.id===spec.stove.id)item.nominal=spec.stove.footprintMm;
    if(item.layout===layoutId)item.roomId='ROOM-1-03';
  }
  if(item.id==='kitchen-back'){
    item.nominal=KITCHEN_DESIGN.backWorktopRectMm;
    item.note='Varná nika medzi dvojicou vysokých skríň a dverami technickej miestnosti. Indukcia 800 mm, po stranách 605 a 625 mm odkladacej plochy; odsávač 880 mm je integrovaný do horných skriniek. Prírodný dub na všetkých čelách, čierna pracovná doska a súvislý čierny obklad.';
  }
  if(item.id==='kitchen-oven-tower')item.nominal=KITCHEN_DESIGN.ovenTowerRectMm;
  if(item.id==='kitchen-oven')item.note='Rúra vo výške 850–1 445 mm; dvierka sa úplne zasúvajú pod dutinu. Umývačka je na opačnom konci ostrovčeka a už neleží oproti rúre; zasúvacie dvierka ponechávajú pohodlný prístup k plechom. Geometrická referencia NEFF B64CS71G0B: 596 × 595 × 548 mm; finálnu montáž a vetranie určí zvolený spotrebič.';
  if(item.id==='kitchen-dishwasher'){
    item.nominal=KITCHEN_DESIGN.dishwasherRectMm;
    item.note='Integrovaná umývačka 600 mm v krajnom východnom module ostrovčeka smerom k malému oknu EAST-04. Od drezovej skrinky ju oddeľuje zásuvkový modul 600 mm. Dvierka sa otvárajú do pracovnej uličky, pri plnom otvorení zostáva po protiľahlú dosku 560 mm na obsluhu; bočný priechod 900 mm je voľný.';
  }
  if(item.id==='kitchen-sink')item.note='Podvesený nerezový drez 600 × 400 × 200 mm v skrinke 800 mm. Pod drezom je triedený odpad; umývačka je na konci ostrovčeka smerom k malému oknu, za jednou zásuvkovou skrinkou. Napravo zostáva 1 330 mm súvislej prípravnej plochy. Prívod vody, odpad a elektrinu viesť koordinovanou podlahovou trasou.';
  if(item.id==='kitchen-upper')item.note='Dubová nadstavba široká 3 210 mm vo výške 2 258–2 700 mm končí zarovno s varnou nikou pred dverami. Päť čiel hrubých 22 mm má skutočné 4 mm škáry. Nad dverami do technickej miestnosti a nízkou bočnou linkou zostáva voľná svetlá stena; bez premostenia a vysokej skrine pri okne.';
  if(item.id==='kitchen-extractor')item.note='Odsávač 880 mm v strednom module 990 mm má viditeľnú 80 mm kazetu s grafitovým čelom, oceľovým rámom a lamelovými filtrami. Spodná hrana je 1 520 mm, nominálne 620 mm nad pracovnou doskou. Recirkulačná trasa Ø150 mm prechádza nadstavbou k vratnej mriežke vo výške 2 700 mm. Odvádzanie vlhkosti rieši vetranie miestnosti; presnú montážnu vzdialenosť potvrdí vybraný spotrebič.';
  if(item.id==='kitchen-island'){
    item.nominal=KITCHEN_ISLAND.worktopRectMm;
    const top=item.nominal;
    item.note=`Samostatný ostrovček s pracovnou doskou ${numberSk(top.x1-top.x0)} × ${numberSk(top.y1-top.y0)} mm, výška ${KITCHEN_RUN.counterHeightMm} mm. Pravá hotová hrana lícuje s koncom pracovnej dosky linky oproti. Drez je na ostrovčeku, umývačka v krajnom module pri malom okne a varenie pri stene. Napravo od drezu ${numberSk(KITCHEN_ISLAND.preparationWidthMm)} mm prípravnej plochy. Zo strany obývačky uzavreté úložisko hlboké 260 mm. Prírodný dub, zapustené úchopy a čierna saténová doska hrubá 20 mm; štíhle svetlo nad ostrovčekom. Plná pravá linka pri stene zostáva, priechod ${numberSk(KITCHEN_ISLAND.sidePassageMm)} mm a pracovná ulička ${numberSk(KITCHEN_ISLAND.workAisleMm)} mm medzi doskami.`;
  }
  if(item.id==='kitchen-return'){
    item.nominal=KITCHEN_DESIGN.eastStorageRectMm;
    const top=KITCHEN_ISLAND.eastReturnWorktopRectMm;
    item.note=`Linka pri pravej stene v pôvodnej plnej dĺžke, vrátane koncového úseku bývalého polostrova. Hotová doska ${numberSk(top.y1-top.y0)} × ${numberSk(top.x1-top.x0)} mm končí na rovnakej úrovni smerom k obývačke ako ostrovček. Medzi doskami zostáva ${KITCHEN_ISLAND.sidePassageMm} mm voľný priechod.`;
  }
  const opening=openingSpecs.find(o=>item.id.includes(o.id));
  if(opening)item.opening={width:opening.widthMm,height:opening.heightMm,sill:opening.sillMm};
  if(opening&&CHILDREN_WINDOW_DESIGN[opening.id])Object.assign(item,CHILDREN_WINDOW_DESIGN[opening.id]);
  if(opening?.id==='EAST-03'){
    item.opening!.clearWidth=HEATING_LAYOUTS.A.accumulator.transport.clearWidthMm;
    item.note='Otvor 900 mm, posunutý o 300 mm k sprche, krídlo otvárané von. Pri kuchyni zostáva 812 mm muriva pre regál 750 × 300 mm. Čistý pás súčasného modelu rámu a otvoreného krídla je 648 mm. Pre nádrž s demontovanou izoláciou treba overiť skutočný voľný otvor: Ø897 mm pri 1 000 l, Ø745 mm pri 800 l. Nominálne dvere „90“ nie sú zárukou 900 mm čistého priechodu.';
  }
  if(item.heatingLayout){
    const h=HEATING_LAYOUTS[item.heatingLayout],b=h.boiler,t=h.accumulator;
    item.roomId='ROOM-1-07';
    if(item.id===`${h.id}-WOOD-PELLET-BOILER`){
      item.name=`DEFRO Firewood Duo Plus ${b.referenceOutputKw} kW`;
      item.nominal=b.body.footprintMm;
      item.product={label:'Celá zostava kotla a násypky · š × h × v',dimensions:`${numberSk(b.catalogueSizeMm.width)} × ${numberSk(b.catalogueSizeMm.depth)} × 1 391 mm`,source:HEATING_SOURCES.boiler};
      item.note=`Čelo smeruje doprava, dvierka sú zatvorené a násypka je pod kotlom v pôdoryse. Modulácia na pelety ${b.pelletOutputRangeKw.join('–')} kW. Podstavec +50 mm. ${heatingRoomNotes(item.heatingLayout)[3]}`;
    }
    if(item.id===`${h.id}-BUFFER-TANK-${t.nominalVolumeL}L`){
      item.name=`DEFRO DBO-S ${numberSk(t.nominalVolumeL)} l`;
      item.product={label:'Nádrž s izoláciou · priemer × výška',dimensions:`Ø${numberSk(t.outerDiameterMm)} × ${numberSk(t.heightMm)} mm`,source:HEATING_SOURCES.accumulator};
      item.note=`Vľavo hore nad kotlom, 100 mm od hotových stien. Prípojky smerujú šikmo doprava dolu, mimo vstupu z kuchyne. ${heatingTransportNote(item.heatingLayout)}`;
    }
    if(item.id.endsWith('-PELLET-HOPPER'))item.note='Násypka 180 kg pod kotlom v pôdoryse, 100 mm od spodnej steny; výrobca umožňuje montáž na oboch stranách. Šírka 614 mm; štvorcová hĺbka je odvodená z výrobného pôdorysu. Poloha, dĺžka a sklon podávača aj hadica sú montážny návrh na potvrdenie dodávateľom.';
    if(item.id.endsWith('-PELLET-BURNER'))item.note='Úzky horák na zatvorených dvierkach. Celkový predný presah J = 429 mm je z výrobného výkresu. Šírka 220 mm, výška 260 mm a delenie na teleso 350 mm + krčok 79 mm sú zaokrúhlené proporcie odvodené z výkresu; detailné montážne rozmery treba potvrdiť.';
    if(item.id.endsWith('-BOILER-FLUE'))item.note=`Pevné hrdlo kotla 139 mm zostáva. Návrh kolena Ø159 mm s polomerom osi 100 mm a zvislej rúry do výšky 2 600 mm; odstup povrchu rúry od ľavej steny ${numberSk(h.flue.wallClearanceMm)} mm. Konkrétny diel, servis a pokračovanie nad strop nie sú potvrdené.`;
    if(item.id.endsWith('-OPEN-SHELVING')){
      item.nominal=h.shelving.footprintMm;
      item.note='Oceľový regál 750 × 300 × 2 000 mm s piatimi policami. Otvorený smerom doľava, prístup 600 mm; stojí na stene uvoľnenej posunom vonkajších dverí. Bez výklopných dvierok v priechode.';
    }
    if(item.id.endsWith('-STORAGE-CABINET'))item.note='Servisná skriňa 720 × 261 × 1 750 mm vpravo dole pri východnej stene, čelom doľava do miestnosti. Priestor pre tri vrecia a vysávač; požiarne oddelenie ešte nie je navrhnuté.';
    if(item.id.endsWith('-VACUUM'))item.product={label:'Rozmerový príklad · Electrolux WQ61-40OG',dimensions:'255 × 140 × 1 105 mm pri otočenom uložení',source:HEATING_SOURCES.vacuum};
    if(item.id.endsWith('-HYDRAULIC-RESERVE'))item.note='Priestor pre montážny návrh hydrauliky. Rozvody ani expanzná nádoba nemajú potvrdené výrobné rozmery.';
  }
  const door=INTERIOR_DOORS.find(d=>d.label.split(' · ')[0]===item.id);
  if(door)item.opening={width:door.widthMm,height:door.heightMm,sill:0};
  if(item.id==='GARAGE-DOOR')item.opening={width:HOUSE.facades.front.garageDoor.widthMm,height:HOUSE.facades.front.garageDoor.heightMm,sill:0};
  const garden=HOUSE.facades.garden.openings.find(o=>item.id===`Terasové presklenie ${o.widthMm}`);
  if(garden?.id==='GARDEN-02')item.note=`HS portál GARDEN-02 / D5 zo spálne 1.10 do dvora: ${numberSk(garden.widthMm)} × ${numberSk(garden.heightMm)} mm, parapet ${garden.sillMm} mm. Zúžený podľa označeného obrázka z 15. 9. 2026 pri zachovaní osi X ${numberSk(garden.startXmm+garden.widthMm/2)} mm; ostenia X ${numberSk(garden.startXmm)}–${numberSk(garden.startXmm+garden.widthMm)} mm. Posuvné otváranie zostáva.`;
  const otherOpening=garden??(item.id==='Terasové posuvné presklenie 2 250'?HOUSE.facades.wingWest.opening:item.id==='LOGGIA-DOOR'?HOUSE.porches.gardenLoggia.backDoor:item.id==='Krytá terasa-glazing'?HOUSE.porches.wingEnd.glazing:null);
  if(item.id==='Terasové posuvné presklenie 2 250')item.note='Posuvný portál do dvora s pohľadovou šírkou rámu aj profilov krídiel 35 mm a zapustenou koľajnicou.';
  if(otherOpening)item.opening={width:otherOpening.widthMm,height:otherOpening.heightMm,sill:otherOpening.sillMm};
  if(item.id==='vehicle')item.note='Auto je zakreslené v zaparkovanej polohe modelu.';
  return item;
});
/** Items shown for one living-room layout: everything shared plus that layout's pieces. */
export const planItemsFor=(layout:LivingLayoutId=DEFAULT_LIVING_LAYOUT_ID,heatingLayout:HeatingLayoutId=DEFAULT_HEATING_LAYOUT_ID)=>PLAN_ITEMS_ALL.filter(item=>(!item.layout||item.layout===layout)&&(!item.heatingLayout||item.heatingLayout===heatingLayout));
/** Items of the default layout; the active 3D model shows this arrangement. */
export const PLAN_ITEMS:PlanItem[]=planItemsFor(DEFAULT_LIVING_LAYOUT_ID);
export const PLAN_ITEM_BY_ID=new Map(PLAN_ITEMS_ALL.map(item=>[item.id,item]));
export const PLAN_MESH_BY_ID=new Map(PLAN_ITEMS_ALL.flatMap(item=>item.meshes.map(mesh=>[mesh.id,{mesh,item}] as const)));
/** Guidance paragraphs of a room; the living room explains the selected layout. */
export const planRoomNotes=(roomId:string,layout:LivingLayoutId=DEFAULT_LIVING_LAYOUT_ID,heatingLayout:HeatingLayoutId=DEFAULT_HEATING_LAYOUT_ID):string[]|undefined=>roomId==='ROOM-1-07'?heatingRoomNotes(heatingLayout):roomId==='ROOM-1-03'?[...LIVING_LAYOUTS[layout].notes]:PLAN_ROOM_NOTES[roomId];
export const PLAN_ROOMS=INTERIOR_ROOMS.map(room=>({...room,name:room.name.replace('Hlavný obytný priestor s kuchyňou','Obývačka a kuchyňa').replace('Zádverie, chodba, vstup','Zádverie'),area:roomAreaM2(room),bounds:roomBoundsMm(room)}));
export const PLAN_FULL_BOUNDS:RectMm={x0:5350,y0:1550,x1:29200,y1:23300};

export interface PlanViewBox { x:number;y:number;width:number;height:number }
export function fitPlanRect(rect:RectMm,aspect:number,padding=700):PlanViewBox {
  const w=Math.max(300,rect.x1-rect.x0)+padding*2,h=Math.max(300,rect.y1-rect.y0)+padding*2;
  const width=Math.max(w,h*Math.max(.2,aspect)),height=width/Math.max(.2,aspect);
  return {x:(rect.x0+rect.x1-width)/2,y:-(rect.y0+rect.y1+height)/2,width,height};
}
export function zoomPlanAt(view:PlanViewBox,factor:number,anchor:{x:number;y:number}):PlanViewBox {
  const width=Math.min(140000,Math.max(600,view.width*factor)),ratio=width/view.width;
  return {x:anchor.x+(view.x-anchor.x)*ratio,y:anchor.y+(view.y-anchor.y)*ratio,width,height:view.height*ratio};
}
export function searchPlanItems(query:string,roomId:string,category:PlanCategory|'all',layout:LivingLayoutId=DEFAULT_LIVING_LAYOUT_ID,heatingLayout:HeatingLayoutId=DEFAULT_HEATING_LAYOUT_ID) {
  const words=normalizeSearch(query).trim().split(/\s+/).filter(Boolean);
  return planItemsFor(layout,heatingLayout).filter(item=>(!roomId||item.roomId===roomId)&&(category==='all'||item.category===category)&&words.every(word=>normalizeSearch(`${item.name} ${item.id} ${PLAN_ROOMS.find(r=>r.id===item.roomId)?.number} ${PLAN_ROOMS.find(r=>r.id===item.roomId)?.name} ${item.meshes.map(m=>m.name).join(' ')}`).includes(word)));
}
