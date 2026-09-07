import generated from './plan-geometry.generated.json';
import { BEDROOM_FITOUT, CHILDRENS_BEDROOM_FITOUTS, HALLWAY_BUILT_IN_WARDROBES, INTERIOR_DOORS, INTERIOR_ROOMS, KITCHEN_RUN, LIVING_DINING_FITOUT, OFFICE_FITOUT, roomAreaM2, roomBoundsMm, type RectMm } from './twin-interior';
import { HOUSE } from './twin-active-house';
import { GIRL_WINDOW_DESIGN } from './twin-children-design';
import { HEATING_SOURCES, TECHNICAL_HEATING_FITOUT as heating } from './technical-design';

export type PlanCategory = 'furniture'|'equipment'|'lighting'|'walls'|'openings'|'finishes';
export const PLAN_CATEGORIES:Record<PlanCategory,string>={furniture:'Nábytok',equipment:'Vybavenie',lighting:'Svetlá',walls:'Steny',openings:'Okná a dvere',finishes:'Povrchy a detaily'};
export type PlanMesh=typeof generated.meshes[number];
export interface PlanItem {
  id:string; name:string; category:PlanCategory; roomId:string; meshes:PlanMesh[];
  rect:RectMm; z0:number; z1:number; nominal?:RectMm; note?:string;
  opening?:{width:number;height:number;sill:number;clearWidth?:number};
  product?:{label:string;dimensions:string;source:string};
}
export const PLAN_ROOM_NOTES:Record<string,string[]>={
  'ROOM-1-08':['Tri okná, tri úlohy: pokojové svetlo nad posteľou, nízky panoramatický pohľad pri hre a svetlo nad stolom. Všetky majú nadpražie 2 500 mm.','Plocha stavebných otvorov 6,05 m² (predtým 3,36 m²). Ide o plochu otvorov, nie výpočet denného osvetlenia. Vonkajšie tienenie, bezpečnostné sklo a preklady dopracuje projektant.'],
  'ROOM-1-06':['WC získalo ďalších 370 mm oproti predchádzajúcej verzii. Medzi priečkami má 1 899 × 1 800 mm a plochu 3,42 m² (predtým 2,75 m²). Po 10 mm obklade je šírka približne 1 879 mm.','Misa je vystredená na novej osi miestnosti. Umývadlo 550 × 350 mm je pri vstupe a puzdrové dvere ponechávajú voľnú podlahu.'],
  'ROOM-1-05':['Zalomený múr pri práčovni ustúpil o 300 mm, aby kotol získal servisný odstup. Zostava má 2 316 mm; práčka a sušička zostávajú plnohodnotné 600 × 600 mm. Sprcha zostáva na pôvodnom mieste.'],
  'ROOM-1-07':['Zostava podľa dohody zo 16.–17. 2. 2026: DEFRO Firewood Duo Plus 19 kW, násypka 180 kg a DBO-S 1 000 l. Pre 19 kW uvádza návod 1 000 l; objem sa neznižuje na 800 l.','Kotol: obal 1 238 × 1 298 × 1 391 mm na 50 mm podstavci. Kotol je presne vystredený medzi bočnými obkladmi: odstupy 504,5 / 504,5 mm. Vzadu zostáva 500 mm. Predný pás 2 000 mm sa meria od čela telesa; zahŕňa aj horák.','Nádrž: Ø1 106 × 1 913 mm s izoláciou, Ø897 mm bez nej. Prípojky sú natočené o 30° ku kuchynskému vstupu, aby ostal voľný prístup k násypke. Dvojkrídlové dvere s otvorom 1 700 mm majú konzervatívny čistý pás 1 352 mm a prah 20 mm. Nádrž prevážať zvislo na 100 mm podvozku podľa vyznačenej trasy, pred montážou prípojok.','Regál pri nádrži je odstránený. Hneď napravo od kuchynských dverí je plytká skriňa 720 × 261 × 1 750 mm: vľavo tri vrecia peliet vo zvislých priehradkách, vpravo tyčový vysávač na stene. Čelo sa posúva, nezasahuje do dverí ani do servisného pásu kotla. Jej požiarne oddelenie zatiaľ nie je schválené. Návod požaduje odstup od horľavých predmetov; voľné vrecia sem nepatria.','Technická má 8,67 m² namiesto 9,34 m². Zostava, nádrž aj skriňa sa obsluhujú zo spoločnej voľnej plochy; ku skrini už netreba prechádzať popri násypke. V modeli je overená súvislá trasa šírky 580 mm aj k násypke; konečné potrubia ju musia zachovať. Nad skriňou je rezerva na hydrauliku 720 × 261 × 650 mm, vo výške 1 850–2 500 mm. Presný rozmer DEFROmat, expanzia, potrubia, vetranie, komín a požiarna skladba vyžadujú dokončenie montážneho projektu. Model overuje priestor, nie povolenie na inštaláciu.'],
};
export const unionBounds=(rects:readonly RectMm[]):RectMm=>({x0:Math.min(...rects.map(r=>r.x0)),y0:Math.min(...rects.map(r=>r.y0)),x1:Math.max(...rects.map(r=>r.x1)),y1:Math.max(...rects.map(r=>r.y1))});
export const rectSize=(r:RectMm)=>[r.x1-r.x0,r.y1-r.y0] as const;
export const numberSk=(n:number,digits=0)=>n.toLocaleString('sk-SK',{maximumFractionDigits:digits});
export const formatMm=(n:number,unit:'mm'|'cm'|'m'='mm')=>`${numberSk(n/(unit==='m'?1000:unit==='cm'?10:1),unit==='m'?3:unit==='cm'?1:0)} ${unit}`;
export const normalizeSearch=(value:string)=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const names:Record<string,string>={BED:'Posteľ',WARDROBE:'Šatníková skriňa',DESK:'Pracovný stôl',CHAIR:'Stolička',FEATURE:'Nástenný panel',ART:'Obraz',LIGHT:'Svietidlo',TOYS:'Úložný regál na hračky',BOOKS:'Knižnica',READING:'Čitateľský puf',PLAY:'Hrací koberec',DRAWING:'Kreslenie a pastelky',BENCH:'Lavička s botníkom',HOOKS:'Vešiakový panel',OVERHEAD:'Horná skriňa',MIRROR:'Zrkadlo',CABINET:'Skriňová zostava',PRINTER:'Tlačiareň','MONITOR-40-21:9':'Monitor',WHITEBOARD:'Magnetická tabuľa','UTILITY-SINK':'Pracovný drez','GARAGE-RACK':'Úložný regál','GARAGE-SHELF':'Nástenné police',PEGBOARD:'Náradie na stene','LONG-TOOL':'Záhradné náradie',MOWER:'Kosačka','GARAGE-CLUTTER':'Uložené predmety','WOOD-PELLET-BOILER':'Kotol na drevo a pelety','PELLET-HOPPER':'Zásobník peliet','PELLET-AUGER':'Podávač peliet','PELLET-BURNER':'Horák','PELLET-FEED-HOSE':'Hadica podávača','BUFFER-TANK-1000L':'Akumulačná nádrž','WALL-HUNG-WC':'Závesné WC','COMPACT-BASIN':'Umývadlo so zrkadlom','BATH-1800':'Vaňa',WC:'WC',WINDOW:'Obklad pri okne','VANITY-900':'Umývadlová skrinka so zrkadlom','WALK-IN-1250':'Sprchovací kút','BUILT-IN-2616':'Kúpeľňová zostava','LAUNDRY-TOWER':'Práčovňová skriňa','TOWEL-RADIATOR-600':'Rebríkový radiátor','BATH-105-WASHER':'Práčka','BATH-105-DRYER':'Sušička'};
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
    if(/plášť/.test(n)) return [n,`${prefix} · úsek ${n.match(/\d+$/)?.[0]}`,'walls'];
    if(/Výplň|výplň|presklenie|garážové okno|svetlík/.test(n)) return [prefix.startsWith('Krytá')?`${prefix}-glazing`:prefix,prefix.includes('FRONT-ENTRY')?'Hlavné vstupné dvere':prefix.includes('EAST-03')?'Dvere technickej miestnosti':prefix.startsWith('Krytá')?'Pevné presklenie terasy':prefix.replace('Výplň otvoru','Okno').replace('Bočná výplň otvoru','Bočné okno'),'openings'];
    return [n,n.replace(/modřínový/gi,'smrekovcový').replace(/modřínové/gi,'Smrekovcové'),/stena|pilier|podpor/.test(n)?'walls':'finishes'];
  }
  if(/FIREPLACE/.test(prefix))return [prefix,'Krbové kachle','equipment'];
  const wardrobe=HALLWAY_BUILT_IN_WARDROBES.find(w=>w.id===prefix);
  if(wardrobe)return [prefix,wardrobe.label.replace(' · posuvné dubové čelá','')+(prefix==='C-DRESSING-0'?' · ľavá':prefix==='C-DRESSING-1'?' · pravá':''),'furniture'];
  if(/koberec|koberca/.test(n)||tag==='PLAY')return [`${prefix}-rug-${tag==='PLAY'?'play':'bed'}`,tag==='PLAY'?'Hrací koberec':'Koberec','finishes'];
  if(prefix==='LIVING-103-SOFA-L') {
    if(/stolíka|stolík/.test(n))return [`coffee-${n.match(/\d+$/)?.[0]}`,`Konferenčný stolík ${n.match(/\d+$/)?.[0]}`,'furniture'];
    return ['sofa','Rohová sedačka','furniture'];
  }
  if(prefix==='LIVING-103-TV-WALL')return [prefix,/TV/.test(prefix)?'TV stena':'Skrinka','furniture'];
  if(prefix==='LIVING-103-DINING') {
    if(tag.startsWith('DINING-CHAIR')) return [tag,`Jedálenská stolička ${['SW','SE','NW','NE'].indexOf(tag.slice(-2))+1}`,'furniture'];
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
  if(tag==='STORAGE-CABINET')label='Plytká servisná skriňa pri dverách';
  if(tag==='HYDRAULIC-RESERVE')label='Rezerva pre hydrauliku';
  if(tag==='SAFETY-GROUP')label='Pojistná skupina KSG mini';
  if(tag==='BOILER-BASE')label='Nehorľavý podstavec kotla';
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
const grouped=new Map<string,PlanItem>();
for(const mesh of generated.meshes) {
  const [id,name,category]=semantic(mesh);
  const item=grouped.get(id)??{id,name,category,roomId:'',meshes:[],rect:mesh.rect,z0:mesh.z0,z1:mesh.z1};
  item.meshes.push(mesh);grouped.set(id,item);
}
const openingSpecs=[...HOUSE.facades.front.openings,...HOUSE.facades.east.openings,HOUSE.facades.west.garageWindow];
export const PLAN_ITEMS:PlanItem[]=[...grouped.values()].map(item=>{
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
  if(item.id==='sofa')item.nominal=unionBounds([LIVING_DINING_FITOUT.sofa.mainRectMm,LIVING_DINING_FITOUT.sofa.chaiseRectMm]);
  if(item.id==='kitchen-back')item.nominal={...KITCHEN_RUN.rectMm,x0:KITCHEN_RUN.fridgeUnitRectMm.x1};
  if(item.id==='kitchen-island')item.nominal=KITCHEN_RUN.peninsulaRectMm;
  if(item.id==='kitchen-return')item.nominal=KITCHEN_RUN.eastReturnRectMm;
  const opening=openingSpecs.find(o=>item.id.includes(o.id));
  if(opening)item.opening={width:opening.widthMm,height:opening.heightMm,sill:opening.sillMm};
  if(opening&&GIRL_WINDOW_DESIGN[opening.id])Object.assign(item,GIRL_WINDOW_DESIGN[opening.id],{roomId:'ROOM-1-08'});
  if(opening?.id==='EAST-03'){
    item.opening!.clearWidth=1352;
    item.note='Dve krídla sa otvárajú von. Čistý pás zohľadňuje rámy aj otvorené krídla a kovanie. Prah 20 mm. Transportné hrdlá a manipuláciu potvrdí dodávateľ.';
  }
  if(item.id===`${heating.id}-WOOD-PELLET-BOILER`){item.name='DEFRO Firewood Duo Plus 19 kW';item.product={label:'Celá zostava kotla a násypky',dimensions:'1 238 × 1 298 × 1 391 mm',source:HEATING_SOURCES.boiler};item.note='Rozmer výrobku zahŕňa celú zostavu; dole sú diely samotného telesa. Podstavec pridáva 50 mm. Servisný priestor je zakreslený osobitne.';}
  if(item.id===`${heating.id}-BUFFER-TANK-1000L`){item.name='DEFRO DBO-S 1 000 l';item.product={label:'Nádrž s izoláciou',dimensions:'Ø1 106 × 1 913 mm',source:HEATING_SOURCES.accumulator};item.note='Bez izolácie Ø897 mm. Prípojky sú natočené o 30° ku kuchynskému vstupu. Rozsah modelu navyše obsahuje navrhnuté hrdlá a odvzdušnenie; ich presahy treba potvrdiť pri objednaní.';}
  if(item.id===`${heating.id}-PELLET-HOPPER`)item.note='Násypka 180 kg, šírka 614 mm; štvorcová hĺbka je odvodená z výrobného pôdorysu. Poloha zodpovedá predbežnému osadeniu v rámci celkového obalu zostavy; hĺbku a vzájomnú polohu s kotlom musí potvrdiť dodávateľ.';
  if(item.id.startsWith(heating.storage.id)){
    item.roomId='ROOM-1-07';
    if(item.id.endsWith('-STORAGE-CABINET'))item.note='Skriňa 720 × 261 × 1 750 mm stojí pri kuchynských dverách. Tri priehradky vľavo sú pre zvislo uložené vrecia, pravý stĺpec pre tyčový vysávač. Požiarne oddelenie musí schváliť projektant; nejde o vybraný certifikovaný výrobok.';
    if(item.id.endsWith('-VACUUM')){item.product={label:'Rozmerový príklad · Electrolux WQ61-40OG',dimensions:'255 × 140 × 1 105 mm pri otočenom uložení',source:HEATING_SOURCES.vacuum};item.note='Model je priestorový príklad tyčového vysávača. Držiak, napájanie a rozmery konkrétneho vybraného vysávača sa potvrdia pred výrobou skrine.';}
    if(item.id.includes('-PELLET-BAG-'))item.note='Priestorová rezerva pre 15 kg vrece uložené zvislo v samostatnej priehradke. Rozmery balenia zvoleného dodávateľa treba pred výrobou skrine potvrdiť.';
    if(item.id.endsWith('-HYDRAULIC-RESERVE'))item.note='Voľný priestor pre konečný hydraulický návrh. DEFROmat ani expanzná nádoba nemajú v tomto modeli potvrdené výrobné rozmery.';
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
export const PLAN_ITEM_BY_ID=new Map(PLAN_ITEMS.map(item=>[item.id,item]));
export const PLAN_MESH_BY_ID=new Map(PLAN_ITEMS.flatMap(item=>item.meshes.map(mesh=>[mesh.id,{mesh,item}] as const)));
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
export function searchPlanItems(query:string,roomId:string,category:PlanCategory|'all') {
  const words=normalizeSearch(query).trim().split(/\s+/).filter(Boolean);
  return PLAN_ITEMS.filter(item=>(!roomId||item.roomId===roomId)&&(category==='all'||item.category===category)&&words.every(word=>normalizeSearch(`${item.name} ${item.id} ${PLAN_ROOMS.find(r=>r.id===item.roomId)?.number} ${PLAN_ROOMS.find(r=>r.id===item.roomId)?.name} ${item.meshes.map(m=>m.name).join(' ')}`).includes(word)));
}
