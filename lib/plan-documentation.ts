import generated from './plan-geometry.generated.json';
import { BEDROOM_FITOUT, CHILDRENS_BEDROOM_FITOUTS, HALLWAY_BUILT_IN_WARDROBES, INTERIOR_DOORS, INTERIOR_ROOMS, KITCHEN_RUN, OFFICE_FITOUT, roomAreaM2, roomBoundsMm, type RectMm } from './twin-interior';
import { DEFAULT_LIVING_LAYOUT_ID, LIVING_LAYOUTS, LIVING_LAYOUT_IDS, diningTableRectMm, type LivingLayoutId } from './twin-living-layouts';
import { HOUSE } from './twin-active-house';
import { GIRL_WINDOW_DESIGN } from './twin-children-design';
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
  'ROOM-1-02':['Chodba medzi detskými izbami je vystredená medzi fasádami: južná priečka 140 mm leží na 6 412–6 552 mm, severná na 7 651–7 791 mm, medzi nimi je 1 099 mm. Obe detské izby sú tak rovnako hlboké (2 908 mm). Severná stena je jedna rovina od šatníka cez dvere spálne po východnú nosnú stenu chlapčenskej izby; južná priečka pokračuje pri zádverí až k rohu pracovne.','Stena k dievčenskej izbe a zádveriu je priečka 140 mm namiesto 199 mm. Plocha chodby je 16,28 m² (predtým 17,46 m²): stena kúpeľne s dverami z chodby leží na tej istej rovine 6 412–6 552 mm, takže bývalý koniec chodby pred kúpeľňou patrí kúpeľni. Puzdro posuvných dverí zo zádveria je v tejto priečke; jeho hrúbku potvrdí dodávateľ. Skriňa na konci chodby má 1 099 × 460 mm medzi stenou kúpeľne a rovinou 7 651 mm (predtým 1 907 mm), skriňa pri dvore 2 768 × 701 mm za priečkou 140 mm.'],
  'ROOM-1-08':['Tri okná, tri úlohy: pokojové svetlo nad posteľou, nízky panoramatický pohľad pri hre a svetlo nad stolom. Všetky majú nadpražie 2 500 mm.','Plocha stavebných otvorov 6,05 m² (predtým 3,36 m²). Ide o plochu otvorov, nie výpočet denného osvetlenia. Vonkajšie tienenie, bezpečnostné sklo a preklady dopracuje projektant.','Izba je medzi dvoma nosnými stenami 300 mm: západná (líce 15 243 mm) je o 100 mm bližšie než predtým v prospech spálne a kúpeľne, východná k zádveriu je v jednej línii so stenou chlapčenskej izby. Izba má 5 298 × 2 908 mm (15,41 m²), presne ako chlapčenská: chodba je vystredená a stena k nej leží na 6 412 mm. Okná si držia rozmery; medzi nimi zostávajú piliere 600 mm a pri oboch nosných stenách 224 mm.','Dvere 900 mm sú vystredené na dĺžku izby (17 442–18 342 mm) a ležia presne oproti dverám chlapčenskej izby. Zariadenie je zrkadlovým obrazom chlapčenskej izby: skriňa 1 600 × 600 mm stojí pri stene chodby v rohu pri zádverí, 599 mm od zárubne; regál na hračky je zrušený.'],
  'ROOM-1-09':['Izba má 5 298 × 2 908 mm (15,41 m²), presne ako dievčenská: západná nosná stena je o 100 mm bližšie v prospech spálne a kúpeľne a stena k chodbe leží na 7 791 mm, v jednej rovine so stenou spálne a šatníka. Presklenie do dvora sa posunulo o 100 mm s posteľou, pred ktorou zostáva 217 mm k sklu.','Dvere 900 mm sú vystredené (17 442–18 342 mm) presne oproti dverám dievčenskej izby. Skriňa 1 600 × 600 mm stojí pri stene chodby v rohu pri zádverí, 599 mm od zárubne; regál na hračky je zrušený.'],
  'ROOM-1-10':['Nosná stena k detským izbám je o 100 mm ďalej a južná stena spálne leží na rovine chodby 7 651–7 791 mm: spálňa má 3 800 × 2 908 mm (11,05 m²), po bokoch postele zostáva 554 mm a pred nohami 1 600 mm. Šatník za posuvnými dverami má 2 200 × 1 907 mm (4,20 m²).'],
  'ROOM-1-11':['Kúpeľňa má po posune priečky ku garáži o 50 cm tvar L: 1 961 × 2 100 mm pri ulici a rozšírenie 1 460 × 808 mm pri chodbe, spolu 5,30 m². Garáž získala 1,05 m² a jej bočný výklenok má 2 000 × 2 100 mm. Dvere 800 mm oproti spálni aj obe malé okná zostávajú na svojich miestach. Úprava je spoločná pre varianty obývačky A aj B.','Podľa dodaného obrázka leží vaňa 1 961 × 750 mm pod vysokým oknom cez celú šírku kúpeľne, od steny pri garáži po protiľahlú nosnú stenu, bez bočnej medzery. Závesné WC je vpravo pri nosnej stene a smeruje doľava. Umývadlová skrinka 900 × 500 mm je vľavo pri priečke ku garáži, so zrkadlom na tejto stene. Medzi čelom umývadlovej skrinky a obrysom WC je 761 mm; pred umývadlom je vyhradený priestor 750 × 900 mm. Namiesto vysokej skrine je pri dverách na stene šatníka matný čierny rebríkový radiátor 600 × 1 500 mm s hĺbkou 100 mm, spodnou hranou 200 mm nad podlahou a 15 priečkami na uteráky.'],
  'ROOM-1-06':['WC získalo ďalších 370 mm oproti predchádzajúcej verzii. Medzi priečkami má 1 899 × 1 800 mm a plochu 3,42 m² (predtým 2,75 m²). Po 10 mm obklade je šírka približne 1 879 mm.','Misa je vystredená na novej osi miestnosti. Umývadlo má 550 × 350 mm. Klasické dvere s krídlom 700 mm sa otvárajú dovnútra k severnej stene; vstupný otvor zostáva na mieste. Celý oblúk vrátane kľučiek je bez kolízie so sanitou.','Severná stena k obývačke je od 12. 9. 2026 nosné murivo 300 mm (10 712–11 012 mm) namiesto priečky 140 mm: stojí nad priečnym základovým pásom a nesie veniec s oceľovými rámami krovu katedrálového stropu obývačky. Zhrubla smerom do kuchyne, takže južné líce na 10 712 mm, plocha WC aj dvere zostávajú.'],
  'ROOM-1-05':['Priečka pri práčovni pokračuje v rovine steny WC bez zuba: líce technickej sa posunulo o 422 mm, kúpeľňové líce o 417 mm. Kúpeľňa a práčovňa má 6,98 m² namiesto 7,47 m². Zostava má 1 899 mm: umývadlová skrinka 1 213 mm s umývadlom 800 mm a vetraná veža pre práčku a sušičku, obe 600 × 600 mm. Pred spotrebičmi je vyhradený pás 900 mm. Sprcha zostáva na pôvodnom mieste.'],
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
    return [base,base.replace(/modřínový/gi,'smrekovcový').replace(/modřínové/gi,'Smrekovcové'),/stena|pilier|podpor/.test(n)?'walls':'finishes'];
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
    if(tag==='OVEN-UNDER-HOB')return ['kitchen-oven','Vstavaná rúra','equipment'];
    if(/odsávač/.test(n))return ['kitchen-extractor','Odsávač pár','equipment'];
    if(/varná/.test(n))return ['kitchen-hob','Varná doska','equipment'];
    if(/drez|batéri/.test(n)&&!n.includes('úchytka'))return ['kitchen-sink','Drez a batéria','equipment'];
    if(/horn[éý]|horných|LED/.test(n))return ['kitchen-upper','Horné kuchynské skrinky','furniture'];
    if(tag==='L-RETURN-EAST')return ['kitchen-return','Bočné rameno kuchyne','furniture'];
    if(/polostrov/.test(n))return ['kitchen-island','Kuchynský polostrov','furniture'];
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
const openingSpecs=[...HOUSE.facades.front.openings,...HOUSE.facades.east.openings,HOUSE.facades.west.garageWindow];
/** Every documented item of the model, including both living-room layouts. */
export const PLAN_ITEMS_ALL:PlanItem[]=[...grouped.values()].map(item=>{
  item.rect=unionBounds(item.meshes.map(m=>m.rect));item.z0=Math.min(...item.meshes.map(m=>m.z0));item.z1=Math.max(...item.meshes.map(m=>m.z1));item.roomId=closestRoom(item.rect);
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
  if(item.id===`${OFFICE_FITOUT.id}-DESK`)item.nominal=OFFICE_FITOUT.desk.footprintMm;
  for(const layoutId of LIVING_LAYOUT_IDS){
    const spec=LIVING_LAYOUTS[layoutId],suffix=layoutSuffix(layoutId);
    if(item.id===`sofa${suffix}`)item.nominal=unionBounds([spec.fitout.sofa.mainRectMm,spec.fitout.sofa.chaiseRectMm]);
    if(item.id===`LIVING-103-TV-WALL${suffix}`)item.nominal=spec.fitout.tvWall.rectMm;
    if(item.id===`dining-table${suffix}`)item.nominal=diningTableRectMm(spec.fitout.dining);
    if(item.id===spec.stove.id)item.nominal=spec.stove.footprintMm;
    if(item.layout===layoutId)item.roomId='ROOM-1-03';
  }
  if(item.id==='kitchen-back')item.nominal={...KITCHEN_RUN.rectMm,x0:KITCHEN_RUN.fridgeUnitRectMm.x1};
  if(item.id==='kitchen-island')item.nominal=KITCHEN_RUN.peninsulaRectMm;
  if(item.id==='kitchen-return')item.nominal=KITCHEN_RUN.eastReturnRectMm;
  const opening=openingSpecs.find(o=>item.id.includes(o.id));
  if(opening)item.opening={width:opening.widthMm,height:opening.heightMm,sill:opening.sillMm};
  if(opening&&GIRL_WINDOW_DESIGN[opening.id])Object.assign(item,GIRL_WINDOW_DESIGN[opening.id],{roomId:'ROOM-1-08'});
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
  const otherOpening=garden??(item.id==='Terasové posuvné presklenie 2 250'?HOUSE.facades.wingWest.opening:item.id==='LOGGIA-DOOR'?HOUSE.porches.gardenLoggia.backDoor:item.id==='Krytá terasa-glazing'?HOUSE.porches.wingEnd.glazing:null);
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
