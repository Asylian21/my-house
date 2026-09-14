import { readFileSync, writeFileSync } from 'node:fs';
const report = JSON.parse(readFileSync(new URL('../../lib/h200-research.json', import.meta.url), 'utf8'));
const cite = text => text.replace(/\[(\d+)\]/g, '[^$1]');
const lines = [`# ${report.title}`, '', `**${report.status}**`, '', `${report.code} · ${report.date} · hlavný návrh C/B/B`, '', '> Generované z lib/h200-research.json. Úpravy článku robiť v tomto spoločnom zdroji; obnoviť cez node scripts/plan-documentation/generate-h200-research.mjs. Webová verzia: /docs/akustika-h200.', '', '## Abstrakt', '', report.abstract, '', `Kľúčové slová: ${report.keywords.join('; ')}.`, ''];
for (const section of report.sections) {
  lines.push(`## ${section.title}`, '', ...section.paragraphs.flatMap(text => [cite(text), '']));
  if (section.table) {
    lines.push(`| ${section.table.headers.join(' | ')} |`, `| ${section.table.headers.map(() => '---').join(' | ')} |`, ...section.table.rows.map(row => `| ${row.map(cite).join(' | ')} |`), '');
  }
  if (section.equations) lines.push('```text', ...section.equations, '```', '');
  if (section.note) lines.push(`> ${cite(section.note)}`, '');
  if (section.id === 'realizacia') lines.push(`[${report.junctionDetail.title}](office-acoustic-wall-junction.md). ${report.junctionDetail.summary} Webový výkres: ${report.junctionDetail.url}.`, '');
}
lines.push('## Použitá literatúra', '', 'Odkazy overené pri spracovaní 13.–14. 9. 2026.', '');
for (const source of report.references) lines.push(`[^${source.id}]: ${source.authors} ${source.publication} [${source.title}](${source.url}). ${source.publisherUrl ? `[Záznam u vydavateľa](${source.publisherUrl}). ` : ''}${cite(source.note)}`);
writeFileSync(new URL('../../docs/office-acoustic-wall-scientific-rationale.md', import.meta.url), lines.join('\n') + '\n');
