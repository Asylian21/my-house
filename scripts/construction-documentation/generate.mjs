import { createServer } from 'vite';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';
import { renderDrawingSet } from './render.mjs';
import { deriveFoundationIllustration, foundationAxonSvg } from './foundation-axon.mjs';
import { derivePartitionLoads } from './partition-loads.mjs';

const root=resolve(import.meta.dirname,'../..');
const out=resolve(root,'output/pdf/construction-cbb');
await mkdir(out,{recursive:true});
const server=await createServer({root,configFile:false,cacheDir:'node_modules/.vite-construction-documentation',resolve:{alias:{'@':root}},server:{middlewareMode:true},appType:'custom'});
let data,plans;
try {
  const source=await server.ssrLoadModule('/scripts/construction-documentation/source.tsx');
  data=source.drawingSource();
  plans={color:source.originalPlanSvg(true),mono:source.originalPlanSvg(false)};
}finally{await server.close();}
data.partitionLoads=derivePartitionLoads(data);
data.foundationIllustration=deriveFoundationIllustration(data);
const modelFiles=['lib/plan-geometry.generated.json','lib/twin-active-house.ts','lib/twin-site.ts','lib/twin-roof.ts','lib/twin-interior.ts','lib/floor-plan-concept.ts','lib/plan-export.ts','lib/acoustic-walls.ts','lib/h200-acoustic-calculation.ts','lib/twin-house-placement.ts','lib/technical-design.ts','lib/twin-living-layouts.ts','lib/h200-junction.json'];
modelFiles.push('app/koncept-2d/acoustic-wall-detail.tsx','app/koncept-2d/documentation-plan.tsx','app/koncept-2d/export-sheet.tsx','app/koncept-2d/plan-svg.tsx','lib/deck-boards.ts','lib/floor-plan-garage.ts','lib/plan-documentation.ts','lib/twin-active-site.ts','lib/twin-children-design.ts','lib/twin-design-selection.ts','lib/twin-domain.ts','lib/twin-garage.ts','lib/twin-interior-baseline.ts','lib/twin-office-desk.ts','lib/twin-superb-combi.ts','lib/twin-viewport-contract.ts','lib/babylon-scene.ts','scripts/construction-documentation/source.tsx','scripts/construction-documentation/render.mjs','scripts/construction-documentation/generate.mjs','package.json','package-lock.json');
modelFiles.push('scripts/construction-documentation/porch-envelope.ts');
modelFiles.push('scripts/construction-documentation/client-brief.ts','scripts/construction-documentation/client-sheets.mjs',...data.clientBrief.foundations.photos);
modelFiles.push('scripts/construction-documentation/foundation-axon.mjs','scripts/construction-documentation/partition-loads.mjs','lib/babylon-interior.ts');
data.provenance={date:'2026-09-16',gitHead:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),files:{}};
for(const f of modelFiles)data.provenance.files[f]=createHash('sha256').update(await readFile(resolve(root,f))).digest('hex');
await writeFile(resolve(out,'model-snapshot.json'),JSON.stringify(data,null,2));
const browser=await chromium.launch({headless:true});
try {
  for(const color of [true,false]) {
    const result=renderDrawingSet(data,plans[color?'color':'mono'],color);
    const suffix=color?'color':'mono';
    await writeFile(resolve(out,`foundation-axon-${suffix}.svg`),foundationAxonSvg(data,color));
    await writeFile(resolve(out,`drawing-set-${suffix}.html`),result.html);
    if(color)await writeFile(resolve(out,'drawing-register.json'),JSON.stringify(result.register,null,2));
    const page=await browser.newPage({viewport:{width:1682,height:1188}});
    await page.goto(new URL(`file://${resolve(out,`drawing-set-${suffix}.html`)}`).href);
    await page.evaluate(()=>document.fonts.ready);
    await page.pdf({path:resolve(out,`DOM-CBB-A1-${suffix}.pdf`),width:'841mm',height:'594mm',printBackground:true,preferCSSPageSize:true,displayHeaderFooter:false,margin:{top:0,right:0,bottom:0,left:0},tagged:true});
    console.log(`${suffix}: ${result.register.length} A1 sheets`);
    await page.close();
    const illustration=await browser.newPage({viewport:{width:1640,height:1030},deviceScaleFactor:2});
    await illustration.goto(new URL(`file://${resolve(out,`foundation-axon-${suffix}.svg`)}`).href);
    await illustration.evaluate(()=>document.fonts.ready);
    await illustration.screenshot({path:resolve(out,`foundation-axon-${suffix}.png`)});
    await illustration.close();
  }
}finally{await browser.close();}
console.log(out);
