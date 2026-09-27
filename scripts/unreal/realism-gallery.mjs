// Direct native images and their paired runtime receipts; never retouch renders.
import {readFile, writeFile, readdir} from 'node:fs/promises';
import {resolve, relative} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

const root = resolve(import.meta.dirname, '../..');
const output = resolve(root, process.argv[2] ?? 'output/unreal/realism-validation-20260926-r1');
const qa = resolve(output, 'qa');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const cases = [];
const excludedMeasurements = [];
for (const session of await readdir(qa, {withFileTypes: true})) {
  if (!session.isDirectory()) continue;
  for (const item of await readdir(resolve(qa, session.name), {withFileTypes: true})) {
    if (!item.isDirectory()) continue;
    const directory = resolve(qa, session.name, item.name);
    try {
      const receipt = JSON.parse(await readFile(resolve(directory, 'qa.json')));
      if (receipt.status !== 'measured' || receipt.motion !== 'static') continue;
      const runtime = JSON.parse(await readFile(resolve(directory, 'runtime.json')));
      const image = await readFile(resolve(directory, 'capture.png'));
      assert.equal(sha(image), receipt.screenshotSha256);
      assert.equal(runtime.rhi, 'Metal');
      if (runtime.focusDuringBenchmark.applicationForegroundSamples !== runtime.frameInterval.sampleCount
        || runtime.focusDuringBenchmark.gameWindowActiveSamples !== runtime.frameInterval.sampleCount) {
        excludedMeasurements.push({receipt: relative(output,resolve(directory,'qa.json')), reason: 'Window or application was not foreground throughout the benchmark'});
        continue;
      }
      cases.push({...receipt, camera: runtime.walking.presentationCamera,
        image: relative(output, resolve(directory, 'capture.png')), runtime: relative(output, resolve(directory, 'runtime.json'))});
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
}
const scenes = [['street-day', 'Ulica', 'Fasáda a obloha'], ['terrace-day', 'Terasa', 'Trávnik, svetlo a materiály'],
  ['interior-day', 'Kuchyňa', 'Dub a čierne sklo']];
const pairs = scenes.map(([scene, name, detail]) => {
  const select = (phases, profile) => cases.filter(row => phases.includes(row.phase) && row.scene === scene && row.profile === profile && row.mode === '4k')
    .sort((a,b) => b.endedAt.localeCompare(a.endedAt))[0];
  const afterPhases = ['after-realism', 'after-details', 'after-room-details', 'after-furniture'];
  const before = select(['before'], 'native'), native = select(afterPhases, 'native'), cinematic = select(afterPhases, 'cinematic');
  assert(before && native && cinematic, 'Missing complete native comparison for ' + scene);
  for (const after of [native, cinematic]) {
    assert.deepEqual(before.camera.eyeCm, after.camera.eyeCm, 'Comparison cameras differ');
    assert.deepEqual(before.camera.forward, after.camera.forward, 'Comparison directions differ');
  }
  return {scene, name, detail, before, native, cinematic};
});
const roomDetails = [
  ['room-1-05-day','Kúpeľňa a práčovňa','coverage-realism','after-room-details'],
  ['room-1-09-day','Detská izba','coverage-realism','after-room-details'],
  ['room-1-03-day','Obývačka a jedáleň','before-furniture','after-furniture'],
].flatMap(([scene,name,beforePhase,afterPhase]) => {
  const select = phase => cases.filter(row => row.phase === phase && row.scene === scene && row.profile === 'cinematic' && row.mode === 'retina')
    .sort((a,b) => b.endedAt.localeCompare(a.endedAt))[0];
  const before=select(beforePhase), after=select(afterPhase);
  if (!before || !after) return [];
  assert.deepEqual(before.camera.eyeCm,after.camera.eyeCm,'Room comparison cameras differ');
  assert.deepEqual(before.camera.forward,after.camera.forward,'Room comparison directions differ');
  assert.deepEqual(before.pixels,after.pixels,'Room comparison resolution differs');
  return [{scene,name,before,after}];
});
let stoveAcceptance;
try { stoveAcceptance = JSON.parse(await readFile(resolve(output,'stove-native-acceptance.json'))); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const stoveDetails = [
  ['room-1-03-day','Ohnisko cez deň','after-furniture'],
  ['room-1-03-night','Ohnisko v noci','before-stove'],
].flatMap(([scene,name,beforePhase]) => {
  const select = phase => cases.filter(row => row.phase === phase && row.scene === scene && row.profile === 'cinematic' && row.mode === '4k'
    && (phase !== 'after-stove' || (stoveAcceptance?.status === 'native-visually-accepted' && row.packageReportSha256 === stoveAcceptance.packageReportSha256)))
    .sort((a,b) => b.endedAt.localeCompare(a.endedAt))[0];
  const before=select(beforePhase), after=select('after-stove');
  if (!before || !after) return [];
  assert.deepEqual(before.camera.eyeCm,after.camera.eyeCm,'Stove comparison cameras differ');
  assert.deepEqual(before.camera.forward,after.camera.forward,'Stove comparison directions differ');
  assert.deepEqual(before.pixels,after.pixels,'Stove comparison resolution differs');
  return [{scene,name,before,after}];
});
const manifest = {generatedAt: new Date().toISOString(), status: 'native-image-pairs-validated',
  caveat: 'Fotoreal is a higher quality and cost profile. Compare Native against Native to isolate the material/environment revision. Room detail pairs isolate the later geometry revision at equal cinematic quality and 1920x1080; stove pairs use 3840x2160. Static images do not prove animation continuity.', pairs,roomDetails,stoveDetails,excludedMeasurements};
await writeFile(resolve(output, 'gallery-data.json'), JSON.stringify(manifest, null, 2) + '\n');
const data = JSON.stringify(pairs).replaceAll('<', '\\u003c');
const roomHtml = roomDetails.length ? '<section style="margin-top:32px"><h2>Detaily v miestnostiach</h2><p class="small">Rovnaká kamera a kvalita Fotoreal, 1 920 × 1 080. Porovnanie pred a po dopracovaní detailov jednotlivých miestností.</p>' + roomDetails.map(p => '<h3>'+p.name+'</h3><div class="meta">'+[['before','Pred dopracovaním'],['after','Po dopracovaní']].map(([key,label]) => '<a href="'+p[key].image+'"><img style="width:100%;display:block;border-radius:5px" src="'+p[key].image+'" alt="'+p.name+' — '+label+'">'+label+'</a>').join('')+'</div>').join('')+'</section>' : '';
const stoveHtml = stoveDetails.length ? '<section style="margin-top:32px"><h2>Oheň v obývačke</h2><p class="small">Priame 4K zábery pri rovnakej kamere a kvalite Fotoreal. Dutá komora, zuhoľnatené polená a textúrované plamene nahrádzajú pôvodné kužele. Statické snímky zachytávajú rozdielne fázy animácie.</p>' + stoveDetails.map(p => '<h3>'+p.name+'</h3><div class="meta">'+[['before','Pred úpravou ohniska'],['after','Po úprave ohniska']].map(([key,label]) => '<a href="'+p[key].image+'"><img style="width:100%;display:block;border-radius:5px" src="'+p[key].image+'" alt="'+p.name+' — '+label+'">'+label+'</a>').join('')+'</div>').join('')+'</section>' : '';
const html = `<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Březí — realizmus pred / po</title><style>
*{box-sizing:border-box}body{margin:0;background:#edece6;color:#202922;font:16px/1.5 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:32px 24px 60px}.eyebrow{letter-spacing:.18em;font-size:12px;font-weight:700;color:#5b6c5d}h1{font-size:clamp(27px,4vw,48px);font-weight:550;letter-spacing:-.045em;margin:8px 0}.intro{max-width:820px;color:#4f5b53}nav{display:flex;gap:8px;flex-wrap:wrap;margin:25px 0 15px}button,select{font:inherit;border:1px solid #bbc5b9;background:#f8f8f4;color:#273b2a;border-radius:7px;padding:10px 17px;cursor:pointer}button[aria-selected=true]{background:#294632;color:#fff;border-color:#294632}button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid #c6832a;outline-offset:3px}.controls{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:15px;flex-wrap:wrap}.stage{aspect-ratio:16/9;position:relative;background:#18231c;overflow:hidden;border-radius:9px;box-shadow:0 12px 28px #18351c20}.stage img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.stage .after{clip-path:inset(0 0 0 var(--split,50%))}.divider{position:absolute;left:var(--split,50%);top:0;bottom:0;width:2px;background:#fff;box-shadow:0 0 0 1px #0003}.badge{position:absolute;top:16px;background:#17241cca;color:white;border-radius:4px;padding:6px 10px;font-size:12px;letter-spacing:.06em}.left{left:16px}.right{right:16px}.range{display:flex;align-items:center;gap:15px;margin:16px 0}input{flex:1;accent-color:#294632}.meta{display:grid;grid-template-columns:1fr 1fr;gap:20px;background:#f8f8f4;border:1px solid #cbd2c8;border-radius:9px;padding:20px}.metric{font-size:26px;font-weight:600;margin:5px 0}a{color:#365d3e;text-underline-offset:3px}.small{font-size:13px;color:#5b695e}footer{margin-top:28px;max-width:950px}.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;margin-top:20px;font-size:14px}th,td{padding:12px 16px;text-align:left;border-bottom:1px solid #cbd2c8}th{font-weight:600}p{margin:8px 0}@media(max-width:640px){main{padding:22px 13px}.meta{gap:12px;padding:14px}.metric{font-size:21px}.badge{top:8px;padding:3px 6px;font-size:10px}.left{left:8px}.right{right:8px}}
</style><main><div class="eyebrow">BŘEZÍ · HLAVNÝ NÁVRH C / B / B</div><h1>Realizmus, ktorý vidno v aplikácii.</h1>
<p class="intro">Priame snímky z Unreal Engine na Metal, 3 840 × 2 160. Rovnaká poloha a smer kamery. Posuvníkom porovnajte pôvodný obraz s novou verziou.</p>
<nav role="tablist" aria-label="Porovnávaný pohľad" id="tabs"></nav><div class="controls"><strong id="detail"></strong><label>Kvalita novej verzie <select id="profile"><option value="cinematic">Fotoreal</option><option value="native">Natívny detail — rovnaký profil ako predtým</option></select></label></div>
<div class="stage" id="stage"><img id="before" alt="Pôvodný natívny render"><img class="after" id="after" alt="Nový natívny render"><div class="divider"></div><span class="badge left">PRED · NATIVE</span><span class="badge right" id="after-label">PO · FOTOREAL</span></div>
<label class="range">Pred <input id="split" type="range" min="0" max="100" value="50" aria-label="Hranica porovnania pred a po"> Po</label>
<section class="meta"><div><span class="small">PÔVODNÁ VERZIA</span><div class="metric" id="before-fps"></div><a id="before-link">Otvoriť pôvodný 4K obraz</a></div><div><span class="small">NOVÁ VERZIA</span><div class="metric" id="after-fps"></div><a id="after-link">Otvoriť nový 4K obraz</a></div></section>
<p class="small">FPS je priemer 300 meraných snímok po zahriatí, aktívne okno a aplikácia. Vyššia kvalita má vyššiu cenu. Pre porovnanie samotných materiálov a atmosféry vyberte „Natívny detail“.</p>
<div class="tablewrap"><table><thead><tr><th>Záber</th><th>Pred · Native</th><th>Po · Native</th><th>Po · Fotoreal</th></tr></thead><tbody id="table"></tbody></table></div>
${roomHtml}
${stoveHtml}
<footer><p>Nová atmosféra, pokojnejšia omietka a dub, správna lineárna odrazivosť čierneho skla a vybraných povrchov. Fotoreal obnovuje detailné tiene vegetácie a zvyšuje kvalitu Lumen aj TSR.</p><p class="small">Ide o lokálne overenú vizualizáciu. Zábery nie sú retušované. Výsledok ešte nie je nerozoznateľný od fotografie; medzi zostávajúce obmedzenia patria zjednodušené rastliny a niektoré modelové detaily. <a href="gallery-data.json">Merania a väzby na pôvodné dôkazy</a>.</p></footer>
</main><script>const pairs=${data};let selected=0;const $=id=>document.getElementById(id);const metric=r=>(1000/r.frame.meanMs).toFixed(1)+' FPS · '+r.frame.meanMs.toFixed(1)+' ms';function show(index){selected=index;const p=pairs[index],a=p[$('profile').value];$('before').src=p.before.image;$('after').src=a.image;$('detail').textContent=p.detail;$('before-fps').textContent=metric(p.before);$('after-fps').textContent=metric(a);$('before-link').href=p.before.image;$('after-link').href=a.image;$('after-label').textContent='PO · '+($('profile').value==='cinematic'?'FOTOREAL':'NATIVE');[...$('tabs').children].forEach((el,i)=>el.setAttribute('aria-selected',String(i===index)));}pairs.forEach((p,i)=>{const b=document.createElement('button');b.textContent=p.name;b.setAttribute('role','tab');b.onclick=()=>show(i);$('tabs').append(b);const tr=document.createElement('tr');[p.name,...['before','native','cinematic'].map(k=>metric(p[k]))].forEach(text=>{const td=document.createElement('td');td.textContent=text;tr.append(td)});$('table').append(tr)});$('profile').onchange=()=>show(selected);$('split').oninput=()=>{$('stage').style.setProperty('--split',$('split').value+'%')};show(0);</script></html>`;
await writeFile(resolve(output, 'porovnanie.html'), html);
console.log(JSON.stringify({status: manifest.status, pairs:pairs.length, gallery:resolve(output,'porovnanie.html')}));
