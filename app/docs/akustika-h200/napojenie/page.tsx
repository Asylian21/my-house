import Link from 'next/link';
import junction from '@/lib/h200-junction.json';
import { designHref } from '@/lib/twin-design-selection';
import { ProjectNav } from '../../../project-nav';
import { H200JunctionFigure } from '../junction-figure';
import '../../../globals.css';
import '../research.css';

export const metadata = { title: 'H200 · Detail napojenia pri dverách', description: junction.summary };

export default function H200JunctionPage() {
  return <div className="project-app h200-page"><ProjectNav active="docs"/>
    <main className="h200-report h200-junction-report" id="project-content">
      <header><p className="h200-kicker">DOM · C/B/B · DETAIL D1</p><h1>{junction.title}</h1><p className="h200-subtitle">{junction.summary}</p>
        <dl className="h200-meta"><div><dt>Detail / revízia</dt><dd>{junction.code}</dd></div><div><dt>Spracované</dt><dd>{junction.date}</dd></div></dl>
        <div className="h200-actions"><Link href="/docs/akustika-h200">Odborná správa H200</Link><Link href={designHref('/docs/manual')}>Výkres a manuál</Link><a href="#zdroje">Technické zdroje</a></div>
      </header>
      <p className="h200-note">{junction.decision}</p>
      <H200JunctionFigure/>
      <section className="h200-section" aria-labelledby="realizacia"><h2 id="realizacia">Ako spoj vyhotoviť</h2>
        <div className="h200-junction-steps">{junction.steps.map(step => <section key={step.title}><h3>{step.title}</h3><p>{step.text}{'sources' in step && step.sources?.map(id => <sup key={id}><a href={`#zdroj-${id}`} aria-label={`Zdroj ${id}`}>[{id}]</a></sup>)}</p></section>)}</div>
      </section>
      <section className="h200-section" aria-labelledby="rozmery"><h2 id="rozmery">Zmestí sa to do súčasného návrhu</h2>
        <table><tbody>{junction.geometry.map(([label,value]) => <tr key={label}><th scope="row">{label}</th><td>{value}</td></tr>)}</tbody></table>
        <p>{junction.modelNote}</p>
      </section>
      <aside className="h200-note">{junction.limit}</aside>
      <section className="h200-section h200-references" aria-labelledby="zdroje"><h2 id="zdroje">Technické zdroje</h2><ol>{junction.references.map(source => <li key={source.id} id={`zdroj-${source.id}`}><a href={source.url}>{source.title}</a><p>{source.note}</p></li>)}</ol></section>
      <footer className="h200-report-footer">{junction.code} · Zväčšený projektový detail napojenia H200. Rozmery v mm; nejde o nový akustický skúšobný protokol.</footer>
    </main>
  </div>;
}
