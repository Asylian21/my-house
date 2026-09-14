import { readFileSync, writeFileSync } from 'node:fs';
const detail = JSON.parse(readFileSync(new URL('../../lib/h200-junction.json', import.meta.url), 'utf8'));
const lines = [`# ${detail.title}`, '', `${detail.code} · ${detail.date} · hlavný návrh C/B/B`, '', '> Generované z lib/h200-junction.json. Webový výkres: /docs/akustika-h200/napojenie.', '', detail.summary, '', '## Rozhodnutie', '', detail.decision, '', '## Vyhotovenie', ''];
for (const step of detail.steps) lines.push(`### ${step.title}`, '', `${step.text}${step.sources?.map(id => `[^${id}]`).join('') ?? ''}`, '');
lines.push('## Návrhové rozmery', '', '| Miesto | Rozmer |', '| --- | --- |', ...detail.geometry.map(row => `| ${row.join(' | ')} |`), '', detail.modelNote, '', '## Hranice detailu', '', detail.limit, '', '## Technické zdroje', '');
for (const source of detail.references) lines.push(`[^${source.id}]: [${source.title}](${source.url}). ${source.note}`, '');
writeFileSync(new URL('../../docs/office-acoustic-wall-junction.md', import.meta.url), lines.join('\n'));
