// Display original native PNGs side by side; never synthesize or retouch evidence.
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,relative} from 'node:path';
const output=resolve(process.argv[2]??'output/unreal/performance-20260923-r1');
const {rows}=JSON.parse(await readFile(resolve(output,'measurements.json')));
const data=rows.filter(r=>r.motion==='static').map(r=>({...r,image:relative(output,resolve(r.artifacts.directory,'capture.png'))}));
// Select the same evidence as the acceptance report, including camera/focus
// rechecks. Preserve the complete raw row list and the other phase selectors.
const selection={available:false,cases:{}};
try {
  const acceptance=JSON.parse(await readFile(resolve(output,'acceptance.json')));
  if(!Array.isArray(acceptance.comparisons))throw Error('Invalid acceptance comparisons');
  for(const c of acceptance.comparisons.filter(c=>c.case.motion==='static')) {
    selection.cases[[c.case.scene,c.case.profile,c.case.output].join('/')]={
      baseline:c.baseline.selected?.artifacts?.directory??null,
      'shipping-final':c.case.selected?.artifacts?.directory??null,
    };
  }
  selection.available=true;
}catch(error){if(error.code!=='ENOENT')throw error;}
const json=JSON.stringify(data).replaceAll('<','\\u003c');
const selectedJson=JSON.stringify(selection).replaceAll('<','\\u003c');
const html=`<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Březí — natívne porovnanie výkonu</title><style>
body{margin:0;background:#111719;color:#eef3ef;font:16px system-ui}header{padding:24px 32px;border-bottom:1px solid #36413f}h1{font-size:24px;margin:0 0 8px}p{color:#bdc9c3}select{font:inherit;padding:8px;margin:8px;background:#21332c;color:white;border:1px solid #587365;border-radius:6px}main{padding:20px;display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;min-width:0}img{width:100%;display:block}figcaption{padding:14px 0;white-space:pre-line;line-height:1.6}small{color:#bfcdbe}.controls{display:flex;flex-wrap:wrap;align-items:center}@media(max-width:850px){main{grid-template-columns:1fr}}
</style><header><h1>Březí Twin · pôvodné natívne zábery</h1><p>C/B/B. PNG pochádzajú priamo z aplikácie. Čas snímky je meraný osobitne pred uložením záberu.</p><div class="controls">
<label>Záber <select id="scene"></select></label><label>Profil <select id="profile"></select></label><label>Výstup <select id="output"></select></label>
<label>Vľavo <select id="left"></select></label><label>Vpravo <select id="right"></select></label></div><p id="selection-note"></p></header><main id="pairs"></main>
<script>const rows=${json};const selection=${selectedJson};const values=k=>[...new Set(rows.map(r=>r[k]))];for(const k of ['scene','profile','output'])for(const v of values(k)){const o=new Option(v,v);document.getElementById(k).add(o)}for(const k of ['left','right'])for(const v of values('phase'))document.getElementById(k).add(new Option(v,v));for(const [id,value] of Object.entries({scene:'street-day',profile:'performance',output:'retina',left:'baseline',right:'shipping-final'})){if([...document.getElementById(id).options].some(o=>o.value===value))document.getElementById(id).value=value;}
document.getElementById('selection-note').textContent=selection.available?'Voľby baseline a shipping-final používajú presné statické zábery z acceptance.json vrátane opravných behov. Výber sa riadi platnosťou merania a zhodou kamery, nie vyšším FPS. Popis uvádza skutočnú sériu; ostatné série zostávajú dostupné.':'Upozornenie: acceptance.json chýba. Voľby baseline a shipping-final sú nedostupné; ostatné série zobrazujú surové merania.';
function selectedRow(phase,base){if(['baseline','shipping-final'].includes(phase)){const directory=selection.cases[[base.scene,base.profile,base.output].join('/')]?.[phase];return directory?rows.find(r=>r.artifacts.directory===directory):null}return rows.filter(r=>r.phase===phase&&Object.keys(base).every(k=>r[k]===base[k])).at(-1)}
function show(){const base=['scene','profile','output'].reduce((a,k)=>(a[k]=document.getElementById(k).value,a),{});const parent=document.getElementById('pairs');parent.replaceChildren();for(const side of ['left','right']){const phase=document.getElementById(side).value;const row=selectedRow(phase,base);const f=document.createElement('figure');if(row){const a=document.createElement('a');a.href=row.image;a.target='_blank';const img=new Image;img.src=row.image;img.alt=row.scene+' '+row.profile+' '+row.phase;a.append(img);f.append(a);const cap=document.createElement('figcaption');cap.textContent=row.phase+' · '+row.configuration+' · '+row.pixels.join(' × ')+'\\n'+row.fps.toFixed(1)+' FPS · p50 '+row.frame.p50Ms.toFixed(2)+' / p95 '+row.frame.p95Ms.toFixed(2)+' / p99 '+row.frame.p99Ms.toFixed(2)+' ms\\n'+(row.limitations.join(', ')||'Bez zaznamenanej výhrady merania');f.append(cap)}else f.textContent='Pre túto voľbu nie je dostupný vybraný beh.';parent.append(f)}}document.querySelectorAll('select').forEach(s=>s.onchange=show);show();</script></html>`;
await writeFile(resolve(output,'comparison.html'),html);console.log(resolve(output,'comparison.html'));
