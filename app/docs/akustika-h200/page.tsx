import Link from '@/app/project-link';
import { Fragment } from 'react';
import report from '@/lib/h200-research.json';
import { OFFICE_ACOUSTIC_ASSEMBLY } from '@/lib/acoustic-walls';
import { designHref } from '@/lib/twin-design-selection';
import { ProjectNav } from '../../project-nav';
import '../../globals.css';
import './research.css';

type Section = { id: string; title: string; paragraphs: string[]; table?: { headers: string[]; rows: string[][] }; equations?: string[]; note?: string };
const sections: Section[] = report.sections;
export const metadata = { title: 'H200 · Odborné zdôvodnenie akustickej steny', description: report.abstract };
function CitedText({ text }: { text: string }) {
  return text.split(/(\[\d+\])/g).map((part, i) => /^\[\d+\]$/.test(part)
    ? <sup key={i}><a href={`#zdroj-${part.slice(1, -1)}`} aria-label={`Zdroj ${part.slice(1, -1)}`}>{part}</a></sup>
    : <Fragment key={i}>{part}</Fragment>);
}
function AssemblyFigure() {
  const layers = [...OFFICE_ACOUSTIC_ASSEMBLY.layers].reverse();
  return <figure className="h200-figure"><svg viewBox="0 0 480 136" role="img" aria-label="H200 od sprchy: omietka 15, tehla 100, omietka 15, dutina 45 a jedna doska 12,5 mm. Spolu 187,5 mm.">
    <text x="40" y="16">SPRCHA</text><text x="440" y="16" textAnchor="end">PRACOVŇA</text>
    {layers.map((layer, index) => { const x = 40 + layers.slice(0, index).reduce((sum, item) => sum + item.thicknessMm, 0) * 2; return <g key={layer.id}>
      <rect x={x} y="34" width={layer.thicknessMm * 2} height="56" fill={layer.material === 'masonry' ? '#dfc3a9' : layer.material === 'mineral-wool' ? '#eee2ad' : layer.material === 'gypsum-board' ? '#52768a' : '#dfe4e5'} stroke="#465465" />
      <text x={x + layer.thicknessMm} y="67" textAnchor="middle" fill={layer.material === 'gypsum-board' ? '#fff' : '#263344'}>{layer.thicknessMm.toLocaleString('sk-SK')}</text>
    </g>; })}
    <path d="M40 97V117M415 97V117M40 111H415" fill="none" stroke="#465465"/><text x="240" y="131" textAnchor="middle">187,5 mm · základná skladba</text>
  </svg><figcaption>Obr. 1. Pomerný rez vybranou H200. Na strane pracovne zostáva jedna doska Silentboard 12,5 mm. Finálne mokré povrchy sú navyše.</figcaption></figure>;
}
function ResearchTable({ table, title }: { table: NonNullable<Section['table']>; title: string }) {
  return (
    // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- Keyboard users need to focus the horizontal scroll region on narrow screens.
    <div className="h200-table-wrap" tabIndex={0} role="region" aria-label={`Tabuľka: ${title}`}><table><thead><tr>{table.headers.map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{table.rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}><CitedText text={cell}/></td>)}</tr>)}</tbody></table></div>
  );
}
export default function H200ResearchPage() {
  return <div className="project-app h200-page"><ProjectNav active="docs"/>
    <main className="h200-report" id="project-content">
      <header className="h200-report-header"><p className="h200-kicker">DOM · C/B/B · AK-03</p><h1>{report.title}</h1><p className="h200-subtitle">{report.status}</p><dl className="h200-meta"><div><dt>Revízia</dt><dd>{report.code}</dd></div><div><dt>Spracované</dt><dd>{report.date}</dd></div><div><dt>Stav návrhu</dt><dd>Finálne zvolené H200</dd></div></dl>
        <div className="h200-actions"><Link href={designHref('/podorys')}>Pôdorys C/B/B</Link><Link href={designHref('/docs/manual')}>Výkres a manuál</Link><Link href="/docs/akustika-h200/napojenie">D1 · Napojenie pri dverách</Link><a href="#literatura">Použitá literatúra</a></div>
      </header>
      <section className="h200-abstract" aria-labelledby="abstrakt"><h2 id="abstrakt">Abstrakt</h2><p>{report.abstract}</p><p className="h200-keywords"><strong>Kľúčové slová:</strong> {report.keywords.join(' · ')}</p></section>
      <nav className="h200-contents" aria-label="Obsah odbornej správy"><h2>Obsah</h2><ol>{sections.map(section => <li key={section.id}><a href={`#${section.id}`}>{section.title.replace(/^\d+\. /, '')}</a></li>)}</ol></nav>
      {sections.map(section => <section key={section.id} className="h200-section" aria-labelledby={section.id}><h2 id={section.id}>{section.title}</h2>
        {section.paragraphs.map((text, i) => <p key={i}><CitedText text={text}/></p>)}
        {section.id === 'skladba' && <AssemblyFigure/>}
        {section.id === 'realizacia' && <aside className="h200-note"><Link href={report.junctionDetail.url}>{report.junctionDetail.title}</Link><p>{report.junctionDetail.summary}</p></aside>}
        {section.table && <ResearchTable table={section.table} title={section.title}/>}
        {section.equations && <div className="h200-equations" aria-label="Výpočtový postup">{section.equations.map((equation, i) => <p key={i}>{equation}</p>)}</div>}
        {section.note && <aside className="h200-note"><CitedText text={section.note}/></aside>}
      </section>)}
      <section className="h200-section h200-references" aria-labelledby="literatura"><h2 id="literatura">Použitá literatúra</h2><p>Odkazy overené pri spracovaní 16. 9. 2026. Čísla v texte odkazujú na nasledujúce zdroje.</p><ol>{report.references.map(source => <li id={`zdroj-${source.id}`} key={source.id}><strong>{source.authors}</strong> <a href={source.url}>{source.title}</a>. {source.publication}{'publisherUrl' in source && <> <a href={source.publisherUrl}>Záznam u vydavateľa</a>.</>}<p><CitedText text={source.note}/></p></li>)}</ol></section>
      <footer className="h200-report-footer">{report.code} · Projekt DOM · Technické zdôvodnenie výberu. Výpočet, výsledok cudzieho experimentu a meranie hotovej stavby majú odlišnú dôkazovú úroveň.</footer>
    </main>
  </div>;
}
