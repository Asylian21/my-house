/* Captured model images are already sized for their display; no image proxy is needed. */
/* eslint-disable @next/next/no-img-element */
'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Box, Camera, ChevronLeft, ChevronRight, Download, Expand, X } from 'lucide-react';
import Link from '@/app/project-link';
import { designHref } from '@/lib/twin-design-selection';
import { formatDocumentDate, type LibraryDocument } from '@/lib/document-library';
import './house-visualizations.css';

type OpenImage = (document: LibraryDocument, trigger?: HTMLElement) => void;

function ViewCard({ doc, onOpen }: { doc: LibraryDocument; onOpen: OpenImage }) {
  return <button className="hv-card" onClick={event => onOpen(doc, event.currentTarget)} aria-label={`Zväčšiť: ${doc.title}`}>
    <span className="hv-card-image"><img src={doc.thumbnailUrl} alt="" width={800} height={500} loading="lazy"/><span className="hv-expand"><Expand size={17}/></span></span>
    <span className="hv-card-caption"><strong>{doc.title}</strong><span>{doc.description}</span></span>
  </button>;
}

export function HouseVisualizations({ documents, onOpen, onBrowse, compact = false }: {
  documents: LibraryDocument[]; onOpen: OpenImage; onBrowse: () => void; compact?: boolean;
}) {
  const exterior = documents.filter(doc => doc.visualizationGroup === 'exterior');
  const interior = documents.filter(doc => doc.visualizationGroup === 'interior');
  const featured = [exterior[0], interior[0]].filter(Boolean);
  if (!documents.length) return null;
  return <section className={`hv-gallery${compact ? ' hv-compact' : ''}`} aria-label="Vizualizácie domu">
    <header className="hv-heading"><div><span className="hv-eyebrow"><Camera size={14}/> HLAVNÝ NÁVRH C / B / B</span><h2>{compact ? 'Predstavte si svoj dom' : 'Dom zvonka aj zvnútra'}</h2><p>{compact ? 'Obíďte dom zo všetkých strán a nahliadnite pod katedrálový strop obývačky.' : 'Každý záber môžete zväčšiť. Šípky vás prevedú celým domom.'}</p></div>{compact ? <button className="hv-browse" onClick={onBrowse}>Všetkých {documents.length} záberov<ArrowRight size={17}/></button> : <Link className="hv-browse" href={designHref('/3d')}><Box size={17}/>Prejsť do 3D<ArrowRight size={17}/></Link>}</header>
    {compact ? <div className="hv-grid">{featured.map(doc => <ViewCard key={doc.id} doc={doc} onOpen={onOpen}/>)}</div> : <>
      <section className="hv-group" aria-labelledby="hv-exterior"><div className="hv-group-heading"><h3 id="hv-exterior">01 / Okolo domu</h3><span>{exterior.length} pohľadov · fasády, strecha a záhrada</span></div><div className="hv-grid">{exterior.map(doc => <ViewCard key={doc.id} doc={doc} onOpen={onOpen}/>)}</div></section>
      <section className="hv-group hv-interior" aria-labelledby="hv-interior"><div className="hv-group-heading"><h3 id="hv-interior">02 / Pod katedrálovým stropom</h3><span>Obývačka · jedáleň · kuchyňa</span></div><p className="hv-explanation">Nad dennou zónou je otvorený priestor až po hrebeň. Dve šikmé plochy podhľadu a vysoké štítové presklenie ukazujú jeho výšku; pohľad späť ku kuchyni vysvetľuje, ako spolu jednotlivé časti miestnosti súvisia.</p><div className="hv-grid">{interior.map(doc => <ViewCard key={doc.id} doc={doc} onOpen={onOpen}/>)}</div></section>
    </>}
    <p className="hv-provenance">Zábery z 3D modelu · {formatDocumentDate(documents[0].updatedAt)} · vizualizácia návrhu</p>
  </section>;
}

function FullImage({ doc }: { doc: LibraryDocument }) {
  const [failed, setFailed] = useState(false), [attempt, setAttempt] = useState(0);
  return failed ? <div className="hv-image-error" role="alert"><p>Záber sa nepodarilo načítať.</p><button onClick={() => { setFailed(false); setAttempt(value => value + 1); }}>Skúsiť znova</button><a href={doc.url} target="_blank" rel="noreferrer">Otvoriť obrázok</a></div>
    : <img key={attempt} className="hv-full-image" src={`${doc.previewUrl}&attempt=${attempt}`} alt={doc.description} width={2400} height={1500} onError={() => setFailed(true)}/>;
}

export function VisualizationViewer({ doc, documents, onOpen, onClose }: {
  doc: LibraryDocument; documents: LibraryDocument[]; onOpen: OpenImage; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const selectedThumb = useRef<HTMLButtonElement>(null);
  const index = documents.findIndex(item => item.id === doc.id);
  const previous = documents[(index - 1 + documents.length) % documents.length];
  const next = documents[(index + 1) % documents.length];
  useEffect(() => { dialog.current?.showModal(); }, []);
  useEffect(() => { selectedThumb.current?.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'instant' }); }, [doc.id]);
  return <dialog ref={dialog} className="hv-viewer" aria-labelledby="hv-viewer-title" onCancel={event => { event.preventDefault(); onClose(); }} onKeyDown={event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === 'ArrowLeft') { event.preventDefault(); onOpen(previous); }
    if (event.key === 'ArrowRight') { event.preventDefault(); onOpen(next); }
  }}>
    <header className="hv-viewer-heading"><div><span>VIZUALIZÁCIE DOMU · C / B / B</span><h2 id="hv-viewer-title">{doc.title}</h2></div><button className="hv-icon" aria-label="Zavrieť vizualizáciu" onClick={onClose}><X size={23}/></button></header>
    <div className="hv-stage"><FullImage key={doc.id} doc={doc}/></div>
    <div className="hv-viewer-controls"><div className="hv-stepper"><button className="hv-icon" aria-label="Predchádzajúci záber" onClick={() => onOpen(previous)}><ChevronLeft size={22}/></button><span aria-live="polite" aria-atomic="true">{index + 1} / {documents.length}</span><button className="hv-icon" aria-label="Nasledujúci záber" onClick={() => onOpen(next)}><ChevronRight size={22}/></button></div><a className="hv-download" href={doc.url} download={doc.filename}><Download size={17}/><span>Stiahnuť obrázok</span></a></div>
    <p className="hv-viewer-description">{doc.description}</p>
    <nav className="hv-thumbnails" aria-label="Vybrať záber">{documents.map((item, itemIndex) => <button key={item.id} ref={item.id === doc.id ? selectedThumb : undefined} className={item.id === doc.id ? 'is-selected' : ''} aria-current={item.id === doc.id ? 'true' : undefined} aria-label={`${itemIndex + 1}. ${item.title}`} onClick={() => onOpen(item)}><img src={item.thumbnailUrl} alt="" width={800} height={500} loading="lazy"/></button>)}</nav>
  </dialog>;
}
