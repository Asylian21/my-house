/* Direct images preserve generated SVG dimensions and avoid unnecessary image proxies for local document previews. */
/* eslint-disable @next/next/no-img-element */
'use client';

import { useCallback, useEffect, useMemo, useRef, useState, type RefObject, type CSSProperties } from 'react';
import Link from 'next/link';
import { Archive, ArrowDownToLine, ArrowUpRight, BookOpen, Box, Check, ChevronDown, ChevronLeft, ChevronRight, ChevronsUpDown, CircleHelp, Copy, Download, File, FileCode2, FileImage, FileText, Folder, FolderClosed, FolderOpen, LayoutGrid, List, LoaderCircle, Maximize2, Menu, PanelLeftClose, Search, X, ZoomIn, ZoomOut } from 'lucide-react';
import { ProjectNav } from '../project-nav';
import { designHref } from '@/lib/twin-design-selection';
import { DOCUMENT_STATUS, documentFolderIds, formatDocumentBytes, formatDocumentDate, searchLibraryDocuments, type DocumentFolder, type DocumentLibrary as Library, type LibraryDocument } from '@/lib/document-library';
import { DocumentMarkdown } from './document-markdown';
import './document-library.css';

type BrowserState = { folder: string; query: string; format: string; status: string; sort: 'name' | 'updated' | 'code'; view: 'list' | 'grid'; file: string | null };
export function readLibraryState(params: URLSearchParams, library: Library): BrowserState {
  const folder = params.get('folder') ?? 'all', file = params.get('file');
  const sort = params.get('sort'), format = params.get('format'), status = params.get('status');
  return { folder: library.folders.some(f => f.id === folder) ? folder : 'all', query: params.get('q') ?? '',
    format: ['PDF', 'SVG', 'PNG', 'MD', 'JSON'].includes(format ?? '') ? format! : 'all',
    status: ['coordination', 'reference', 'archive'].includes(status ?? '') ? status! : 'all',
    sort: sort === 'name' || sort === 'updated' ? sort : 'code', view: params.get('view') === 'grid' ? 'grid' : 'list',
    file: file && library.documents.some(d => d.id === file) ? file : null };
}
function FileIcon({ format, size = 21 }: { format: string; size?: number }) {
  const Icon = format === 'PNG' || format === 'SVG' ? FileImage : format === 'JSON' ? FileCode2 : FileText;
  return <Icon size={size} strokeWidth={1.6} aria-hidden="true"/>;
}
function Status({ document: doc }: { document: LibraryDocument }) {
  return <span className={`dl-status dl-status-${doc.status}`} title={doc.statusNote}><i/>{DOCUMENT_STATUS[doc.status]}</span>;
}
function colorName(doc: LibraryDocument) { return doc.color === 'color' ? 'Farebné' : doc.color === 'mono' ? 'Čiernobiele' : null; }

export function DocumentLibrary({ library, initialParams }: { library: Library; initialParams: string }) {
  const [state, setState] = useState(() => readLibraryState(new URLSearchParams(initialParams), library));
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(['drawings']));
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const search = useRef<HTMLInputElement>(null), menu = useRef<HTMLDetailsElement>(null), sidebar = useRef<HTMLElement>(null);
  const lastTrigger = useRef<HTMLElement | null>(null), folderTrigger = useRef<HTMLElement | null>(null);
  const current = library.documents.find(d => d.id === state.file) ?? null;
  const folder = library.folders.find(f => f.id === state.folder);
  const count = (id: string) => { const ids = documentFolderIds(library.folders, id); return library.documents.filter(d => ids.has(d.folderId)).length; };
  const results = useMemo(() => searchLibraryDocuments(library, { folderId: state.query.trim() ? 'all' : state.folder, query: state.query, format: state.format, status: state.status, sort: state.sort }), [library, state.folder, state.query, state.format, state.status, state.sort]);
  const childFolders = state.query || state.format !== 'all' || state.status !== 'all' ? [] : library.folders.filter(f => f.parentId === (state.folder === 'all' ? null : state.folder));
  const sheetCount = new Set(library.documents.filter(d => d.sheetIndex).map(d => d.code)).size;
  const bundles = [library.bundleIds.color, library.bundleIds.mono].map(id => library.documents.find(d => d.id === id)).filter((d): d is LibraryDocument => !!d);
  const update = (patch: Partial<BrowserState>, replace = false) => {
    const next = { ...state, ...patch };
    setState(next);
    const url = new URL(window.location.href);
    const pairs = { folder: next.folder === 'all' ? null : next.folder, q: next.query || null, format: next.format === 'all' ? null : next.format, status: next.status === 'all' ? null : next.status, sort: next.sort === 'code' ? null : next.sort, view: next.view === 'list' ? null : next.view, file: next.file };
    for (const [key, value] of Object.entries(pairs)) { if (value) url.searchParams.set(key, value); else url.searchParams.delete(key); }
    window.history[replace ? 'replaceState' : 'pushState'](window.history.state, '', url);
  };
  useEffect(() => {
    const pop = () => setState(readLibraryState(new URLSearchParams(window.location.search), library));
    const key = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); search.current?.focus(); search.current?.select(); }
      if (event.key === 'Escape') { setSidebarOpen(false); if (menu.current) menu.current.open = false; }
    };
    window.addEventListener('popstate', pop); window.addEventListener('keydown', key);
    return () => { window.removeEventListener('popstate', pop); window.removeEventListener('keydown', key); };
  }, [library]);
  useEffect(() => {
    if (!sidebarOpen) return;
    const trigger = folderTrigger.current;
    const region = sidebar.current;
    const focusable = () => Array.from(region?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href]') ?? []).filter(element => element.getClientRects().length > 0 && getComputedStyle(element).visibility === 'visible');
    // Inherited visibility can settle after the opening frame; hidden controls reject focus.
    let focusFrame: number;
    const focusInitial = () => {
      const first = focusable()[0];
      if (first) first.focus();
      else focusFrame = requestAnimationFrame(focusInitial);
    };
    focusFrame = requestAnimationFrame(focusInitial);
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); setSidebarOpen(false); }
      if (event.key !== 'Tab') return;
      const targets = focusable(), first = targets[0], last = targets.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    const resize = () => { if (window.innerWidth > 800) setSidebarOpen(false); };
    region?.addEventListener('keydown', key); window.addEventListener('resize', resize);
    return () => { cancelAnimationFrame(focusFrame); region?.removeEventListener('keydown', key); window.removeEventListener('resize', resize); requestAnimationFrame(() => { if (!region?.classList.contains('is-open')) trigger?.focus(); }); };
  }, [sidebarOpen]);
  const chooseFolder = (id: string) => {
    update({ folder: id, query: '', file: null }); setSidebarOpen(false);
    setExpanded(previous => new Set([...previous, id]));
  };
  const open = (doc: LibraryDocument, trigger?: HTMLElement) => { if (trigger) lastTrigger.current = trigger; update({ file: doc.id }); };
  const close = () => { update({ file: null }); requestAnimationFrame(() => lastTrigger.current?.focus()); };
  const renderFolder = (item: DocumentFolder, depth = 0) => {
    const children = library.folders.filter(f => f.parentId === item.id), isExpanded = expanded.has(item.id);
    return <li key={item.id}>
      <div className={`dl-folder-row${state.folder === item.id ? ' is-active' : ''}`} style={{ '--folder-depth': depth } as CSSProperties}>
        {children.length > 0 ? <button className="dl-folder-toggle" aria-label={`${isExpanded ? 'Zbaliť' : 'Rozbaliť'} ${item.title}`} aria-expanded={isExpanded} onClick={() => setExpanded(previous => { const next = new Set(previous); if (next.has(item.id)) next.delete(item.id); else next.add(item.id); return next; })}>{isExpanded ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}</button> : <span className="dl-folder-spacer"/>}
        <button className="dl-folder-choice" aria-current={state.folder === item.id ? 'page' : undefined} onClick={() => chooseFolder(item.id)}>{state.folder === item.id ? <FolderOpen size={18}/> : item.id === 'archive' ? <Archive size={18}/> : <Folder size={18}/>}<span>{item.title}</span><small>{count(item.id)}</small></button>
      </div>
      {children.length > 0 && isExpanded && <ul>{children.map(child => renderFolder(child, depth + 1))}</ul>}
    </li>;
  };
  const ancestors: DocumentFolder[] = [];
  let ancestor = folder;
  while (ancestor) { ancestors.unshift(ancestor); ancestor = library.folders.find(f => f.id === ancestor?.parentId); }
  return <div className="dl-app">
    <div className="dl-global-nav" inert={sidebarOpen}><ProjectNav active="docs"/></div>
    <a className="dl-skip" href="#dl-main">Preskočiť na súbory</a>
    <div className="dl-shell">
      {sidebarOpen && <button className="dl-sidebar-scrim" aria-label="Zavrieť zložky" onClick={() => setSidebarOpen(false)}/>}
      <aside ref={sidebar} className={`dl-sidebar${sidebarOpen ? ' is-open' : ''}`} role={sidebarOpen ? 'dialog' : undefined} aria-modal={sidebarOpen || undefined} aria-label="Zložky dokumentácie">
        <div className="dl-sidebar-heading"><span><FolderClosed size={19}/> Dokumenty projektu</span><button className="dl-icon dl-sidebar-close" onClick={() => setSidebarOpen(false)} aria-label="Zavrieť zložky"><PanelLeftClose size={18}/></button></div>
        <nav aria-label="Priečinky"><button className={`dl-all${state.folder === 'all' ? ' is-active' : ''}`} aria-current={state.folder === 'all' ? 'page' : undefined} onClick={() => chooseFolder('all')}><LayoutGrid size={18}/><span>Všetky súbory</span><small>{library.documents.length}</small></button><div className="dl-sidebar-label">ZLOŽKY</div><ul className="dl-folder-tree">{library.folders.filter(f => !f.parentId).map(f => renderFolder(f))}</ul></nav>
        <div className="dl-sidebar-links"><span className="dl-sidebar-label">SÚVISIACE ZOBRAZENIA</span><Link href={designHref('/docs/manual')}><BookOpen size={17}/>Manuál domu<ArrowUpRight size={14}/></Link><Link href="/docs/model"><Box size={17}/>Technický model<ArrowUpRight size={14}/></Link><Link href="/docs/akustika-h200"><FileText size={17}/>Odborná správa H200<ArrowUpRight size={14}/></Link><Link href="/archiv"><Archive size={17}/>Archív návrhov<ArrowUpRight size={14}/></Link></div>
        <div className="dl-sidebar-foot"><span className="dl-project-dot"/><div><strong>Rodinný dom · Březí</strong><small>Parcela 6012/26 · hlavný návrh C/B/B</small></div></div>
      </aside>
      <main className="dl-main" id="dl-main" inert={sidebarOpen}>
        <header className="dl-heading">
          <div><nav className="dl-breadcrumb" aria-label="Umiestnenie"><button className="dl-mobile-folders dl-icon" onClick={event => { folderTrigger.current = event.currentTarget; setSidebarOpen(true); }} aria-label="Otvoriť zložky"><Menu size={18}/></button><button onClick={() => chooseFolder('all')}>Dokumenty projektu</button>{ancestors.map(a => <span key={a.id}><ChevronRight size={13}/><button onClick={() => chooseFolder(a.id)}>{a.title}</button></span>)}</nav><h1>{state.query.trim() ? 'Vyhľadávanie' : folder?.title ?? 'Dokumentácia'}</h1><p>{state.query.trim() ? 'Hľadanie podľa názvu, kódu aj obsahu v celej dokumentácii.' : folder?.description ?? 'Výkresy, technické správy a podklady. Všetko na jednom mieste.'}</p></div>
          <details className="dl-download-menu" ref={menu}><summary aria-label="Stiahnuť výkresovú sadu"><Download size={17}/><span>Stiahnuť sadu</span><ChevronDown size={15}/></summary><div>{bundles.map(doc => <a key={doc.id} href={doc.url} download={doc.filename} onClick={() => { if (menu.current) menu.current.open = false; }}><FileText size={21}/><span><strong>{colorName(doc)} PDF</strong><small>{doc.pageCount} listov · A1 · {formatDocumentBytes(doc.bytes)}</small></span><ArrowDownToLine size={16}/></a>)}</div></details>
        </header>
        {state.folder === 'all' && !state.query && <section className="dl-current-set" aria-label="Aktuálna výkresová sada"><div className="dl-set-icon"><FileText size={23}/></div><div><strong>Výkresová sada C / B / B <span>{sheetCount} listov A1</span></strong><p>Posledný export {formatDocumentDate(library.sourceUpdatedAt)} · vrátane základov s R7 a zaťaženia SA30</p></div><span className="dl-status dl-status-coordination"><i/>Nevydané na realizáciu</span>{bundles[0] && <button onClick={e => open(bundles[0], e.currentTarget)} aria-label="Prezrieť celú výkresovú sadu">Prezrieť sadu<ArrowUpRight size={17}/></button>}</section>}
        <div className="dl-toolbar"><label className="dl-search"><Search size={19}/><span className="dl-sr-only">Vyhľadať dokumenty</span><input ref={search} type="search" value={state.query} placeholder="Hľadať názov, kód alebo obsah…" onChange={e => update({ query: e.target.value }, true)}/>{!state.query && <kbd>⌘ K</kbd>}</label><label className="dl-select"><span className="dl-sr-only">Typ súboru</span><select value={state.format} onChange={e => update({ format: e.target.value })}><option value="all">Všetky typy</option>{['PDF', 'SVG', 'PNG', 'MD', 'JSON'].map(f => <option key={f}>{f}</option>)}</select><ChevronDown size={14}/></label><label className="dl-select dl-status-select"><span className="dl-sr-only">Stav dokumentu</span><select value={state.status} onChange={e => update({ status: e.target.value })}><option value="all">Všetky stavy</option>{Object.entries(DOCUMENT_STATUS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><ChevronDown size={14}/></label></div>
        <div className="dl-files-scroll">
          {childFolders.length > 0 && <section className="dl-folder-section" aria-label="Podpriečinky"><div className="dl-section-label">{state.folder === 'all' ? 'ZLOŽKY DOKUMENTÁCIE' : 'PODZLOŽKY'}</div><div className="dl-folder-cards">{childFolders.map(f => <button key={f.id} onClick={() => chooseFolder(f.id)}><Folder size={25} strokeWidth={1.4}/><strong>{f.title}</strong><span>{count(f.id)} súborov<ChevronRight size={14}/></span></button>)}</div></section>}
          <div className="dl-list-heading"><div><h2>{state.query ? 'Výsledky v celej dokumentácii' : state.folder === 'all' ? 'Všetky súbory' : 'Súbory v zložke'}</h2><span role="status" aria-live="polite">{results.length} súborov</span></div><div className="dl-list-controls"><label className="dl-sort"><ChevronsUpDown size={15}/><span className="dl-sr-only">Zoradiť súbory</span><select value={state.sort} onChange={e => update({ sort: e.target.value as BrowserState['sort'] })}><option value="code">Podľa kódu</option><option value="name">Podľa názvu</option><option value="updated">Naposledy upravené</option></select></label><div className="dl-view-toggle" role="group" aria-label="Zobrazenie súborov"><button className="dl-icon" aria-label="Zoznam" aria-pressed={state.view === 'list'} onClick={() => update({ view: 'list' })}><List size={17}/></button><button className="dl-icon" aria-label="Mriežka" aria-pressed={state.view === 'grid'} onClick={() => update({ view: 'grid' })}><LayoutGrid size={16}/></button></div></div></div>
          {results.length ? <div className={state.view === 'grid' ? 'dl-file-grid' : 'dl-file-table'}>
            {state.view === 'list' && <div className="dl-table-head" aria-hidden="true"><span>NÁZOV SÚBORU</span><span>STAV</span><span>UPRAVENÉ</span><span>VEĽKOSŤ</span><span/></div>}
            {results.map(doc => <article key={doc.id} className={`dl-file-row${current?.id === doc.id ? ' is-selected' : ''}`}>
              <button className="dl-file-open" onClick={e => open(doc, e.currentTarget)} aria-label={`Zobraziť ${doc.title}${colorName(doc) ? ` · ${colorName(doc)}` : ''}`}>
                {state.view === 'grid' && <div className="dl-card-preview">{doc.thumbnailUrl ? <img src={doc.thumbnailUrl} alt="" loading="lazy"/> : <FileIcon format={doc.format} size={42}/>}<span>{doc.format}</span></div>}
                <span className={`dl-file-type dl-type-${doc.format.toLowerCase()}`}><FileIcon format={doc.format}/></span><span className="dl-file-name"><strong>{doc.title}</strong><small>{doc.code && <b>{doc.code}</b>}{colorName(doc) && <span>{colorName(doc)}</span>}<span>{doc.format}</span>{!doc.code && <span>{library.folders.find(f => f.id === doc.folderId)?.title}</span>}</small></span>
              </button>
              <div className="dl-row-status"><Status document={doc}/></div><time dateTime={doc.updatedAt} className="dl-row-date">{formatDocumentDate(doc.updatedAt)}</time><span className="dl-row-size">{formatDocumentBytes(doc.bytes)}</span><a className="dl-icon dl-row-download" href={doc.url} download={doc.filename} aria-label={`Stiahnuť ${doc.title}${colorName(doc) ? ` · ${colorName(doc)}` : ''}`}><ArrowDownToLine size={17}/></a>
            </article>)}
          </div> : <div className="dl-empty"><Search size={34} strokeWidth={1.3}/><h3>Nenašli sa žiadne súbory</h3><p>{state.query ? `Skús kratší výraz alebo kód výkresu. Hľadáš „${state.query}“ v celej dokumentácii.` : 'Pre túto kombináciu zložky a filtrov tu zatiaľ nie je dokument.'}</p><button onClick={() => update({ query: '', format: 'all', status: 'all' })}>Vymazať vyhľadávanie a filtre</button></div>}
          <footer className="dl-content-footer"><span>{sheetCount} výkresových listov · farebné aj čiernobiele PDF</span><span>Hlavný návrh C / B / B</span></footer>
        </div>
      </main>
    </div>
    {current && <DocumentViewer key={current.id} doc={current} library={library} onClose={close} onOpen={id => { const doc = library.documents.find(d => d.id === id); if (doc) open(doc); }} returnFocus={lastTrigger}/>}
  </div>;
}

function DocumentViewer({ doc, library, onClose, onOpen, returnFocus }: { doc: LibraryDocument; library: Library; onClose: () => void; onOpen: (id: string) => void; returnFocus: RefObject<HTMLElement | null> }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [content, setContent] = useState<string | null>(null), [error, setError] = useState(false), [attempt, setAttempt] = useState(0);
  const [page, setPage] = useState(0), [zoom, setZoom] = useState(100), [imageLoaded, setImageLoaded] = useState(false), [detailsOpen, setDetailsOpen] = useState(false);
  const [copied, setCopied] = useState(false), [copyError, setCopyError] = useState(false);
  // A cached server-rendered image can finish before React attaches its load handler.
  const previewImage = useCallback((element: HTMLImageElement | null) => {
    if (element?.complete) {
      if (element.naturalWidth > 0) setImageLoaded(true);
      else setError(true);
    }
  }, []);
  const sheets = library.documents.filter(d => d.bundleId === doc.id).sort((a, b) => (a.sheetIndex ?? 0) - (b.sheetIndex ?? 0));
  const isBundle = sheets.length > 0;
  const pages = isBundle ? sheets : (doc.pagePreviewUrls ?? []).map((previewUrl, index) => ({ ...doc, id: `${doc.id}-page-${index + 1}`, previewUrl, url: `${doc.url}#page=${index + 1}` }));
  const displayed = pages[page] ?? doc;
  const imageUrl = displayed.previewUrl ?? (['PNG', 'SVG'].includes(displayed.format) ? displayed.url : undefined);
  const isText = doc.format === 'MD' || doc.format === 'JSON';
  const alternatives = library.documents.filter(d => d.id !== doc.id && ((doc.code && d.code === doc.code && d.format === doc.format) || doc.relatedIds?.includes(d.id)));
  useEffect(() => {
    const trigger = returnFocus.current;
    dialog.current?.showModal();
    dialog.current?.querySelector<HTMLButtonElement>('[aria-label="Zavrieť náhľad"]')?.focus();
    return () => { requestAnimationFrame(() => trigger?.focus()); };
  }, [returnFocus]);
  useEffect(() => {
    if (!isText) return;
    const controller = new AbortController();
    fetch(doc.url, { signal: controller.signal }).then(response => { if (!response.ok) throw new Error('Preview unavailable'); return response.text(); }).then(text => { setContent(text); setError(false); }).catch(error => { if (error.name !== 'AbortError') setError(true); });
    return () => controller.abort();
  }, [doc.url, isText, attempt]);
  const changePage = (value: number) => {
    const next = Math.max(0, Math.min(pages.length - 1, value));
    if (next === page) return;
    setPage(next); setImageLoaded(false); setError(false); setZoom(100);
  };
  const copy = async () => { try { await navigator.clipboard.writeText(window.location.href); setCopied(true); setCopyError(false); } catch { setCopied(false); setCopyError(true); } };
  const retry = () => { setError(false); setContent(null); setImageLoaded(false); setAttempt(n => n + 1); };
  return <dialog ref={dialog} className={`dl-viewer${detailsOpen ? ' details-open' : ''}`} aria-labelledby="dl-viewer-title" onCancel={e => { e.preventDefault(); onClose(); }}>
    <header className="dl-viewer-header"><span className={`dl-file-type dl-type-${doc.format.toLowerCase()}`}><FileIcon format={doc.format}/></span><div><h2 id="dl-viewer-title">{doc.title}</h2><p>{doc.code && `${doc.code} · `}{colorName(doc) && `${colorName(doc)} · `}{doc.filename}</p></div><button className="dl-icon dl-mobile-info" aria-label="Informácie o dokumente" aria-expanded={detailsOpen} onClick={() => setDetailsOpen(v => !v)}><CircleHelp size={19}/></button><button className="dl-icon" onClick={onClose} aria-label="Zavrieť náhľad"><X size={21}/></button></header>
    <div className="dl-viewer-layout"><section className="dl-viewer-content" aria-label="Náhľad dokumentu">
      <div className="dl-preview-tools"><div>{pages.length > 0 ? <div className="dl-pages"><button className="dl-icon" disabled={page === 0} onClick={() => changePage(page - 1)} aria-label={isBundle ? "Predchádzajúci list" : "Predchádzajúca strana"}><ChevronLeft size={18}/></button><label><span className="dl-sr-only">{isBundle ? "List výkresovej sady" : "Strana dokumentu"}</span><select value={page} onChange={e => changePage(Number(e.target.value))}>{pages.map((p, i) => <option value={i} key={p.id}>{i + 1}. {p.code ? `${p.code} · ` : ""}{p.title}</option>)}</select></label><span>/ {pages.length}</span><button className="dl-icon" disabled={page === pages.length - 1} onClick={() => changePage(page + 1)} aria-label={isBundle ? "Nasledujúci list" : "Nasledujúca strana"}><ChevronRight size={18}/></button></div> : <span className="dl-preview-label">{doc.format === 'MD' ? 'Technická správa' : doc.format === 'JSON' ? 'Štruktúrované údaje' : `${doc.paper ?? 'Náhľad'}${doc.scale ? ` · ${doc.scale}` : ''}`}</span>}</div>{imageUrl && !isText && <div className="dl-zoom"><button className="dl-icon" disabled={zoom <= 50} onClick={() => setZoom(v => Math.max(50, v - 25))} aria-label="Zmenšiť náhľad"><ZoomOut size={17}/></button><button onClick={() => setZoom(100)} title="Prispôsobiť šírke">{zoom}%</button><button className="dl-icon" disabled={zoom >= 250} onClick={() => setZoom(v => Math.min(250, v + 25))} aria-label="Zväčšiť náhľad"><ZoomIn size={17}/></button><button className="dl-icon dl-fit" onClick={() => setZoom(100)} aria-label="Prispôsobiť šírke"><Maximize2 size={16}/></button></div>}</div>
      <div className={`dl-preview-canvas${isText ? ' is-text' : ''}`}>
        {error ? <div className="dl-preview-message" role="alert"><File size={32}/><h3>Náhľad sa nepodarilo načítať</h3><p>Skús ho načítať znova alebo otvor pôvodný súbor.</p><button onClick={retry}>Skúsiť znova</button><a href={doc.url} target="_blank" rel="noreferrer">Otvoriť súbor<ArrowUpRight size={15}/></a></div> : isText ? content === null ? <div className="dl-preview-message" role="status"><LoaderCircle className="dl-spinner"/>Načítavam dokument…</div> : doc.format === 'MD' ? <DocumentMarkdown content={content} documents={library.documents} onOpenDocument={onOpen}/> : <pre className="dl-json"><code>{content}</code></pre> : imageUrl ? <><div className="dl-preview-paper" style={{ width: `${zoom}%` }}>{!imageLoaded && <div className="dl-preview-loading" role="status"><LoaderCircle className="dl-spinner"/> Načítavam náhľad…</div>}<img ref={previewImage} key={`${imageUrl}-${attempt}`} src={imageUrl} alt={`${displayed.title}${displayed.code ? ` · ${displayed.code}` : ''}`} onLoad={() => setImageLoaded(true)} onError={() => setError(true)}/></div></> : <div className="dl-preview-message"><FileIcon format={doc.format} size={42}/><h3>{doc.format} dokument</h3><p>Tento súbor otvoríš v samostatnej karte.</p><a href={doc.url} target="_blank" rel="noreferrer">Otvoriť {doc.format}<ArrowUpRight size={17}/></a></div>}
      </div>
      <div className="dl-preview-footer"><span>{displayed.code ?? doc.format}{pages.length ? ` · ${isBundle ? "list" : "strana"} ${page + 1} z ${pages.length}` : ''}</span><div className="dl-preview-footer-actions"><a className="dl-preview-download" href={doc.url} download={doc.filename}><Download size={15}/>{isBundle ? 'Stiahnuť sadu' : 'Stiahnuť'}</a><a href={displayed.url} target="_blank" rel="noreferrer">Otvoriť {displayed.format}<ArrowUpRight size={14}/></a></div></div>
    </section>
    <aside className="dl-file-details" aria-label="Informácie o dokumente"><h3>Informácie o súbore</h3><Status document={doc}/><p className="dl-file-description">{doc.description}</p><div className={`dl-evidence dl-evidence-${doc.status}`}><CircleHelp size={17}/><p>{doc.statusNote}</p></div><dl><div><dt>Zložka</dt><dd>{library.folders.find(f => f.id === doc.folderId)?.title}</dd></div><div><dt>Upravené</dt><dd>{formatDocumentDate(doc.updatedAt)}</dd></div><div><dt>Formát</dt><dd>{doc.format}{doc.paper ? ` · ${doc.paper}` : ''}</dd></div><div><dt>Veľkosť</dt><dd>{formatDocumentBytes(doc.bytes)}</dd></div>{doc.pageCount && <div><dt>Počet listov</dt><dd>{doc.pageCount}</dd></div>}{doc.scale && <div><dt>Mierka</dt><dd>{doc.scale}</dd></div>}</dl><a className="dl-primary-download" href={doc.url} download={doc.filename}><Download size={17}/>Stiahnuť {doc.format}</a><button className="dl-copy" onClick={copy}>{copied ? <Check size={16}/> : <Copy size={16}/>}<span role="status">{copied ? 'Odkaz skopírovaný' : 'Kopírovať odkaz'}</span></button>{copyError && <label className="dl-copy-fallback">Skopíruj odkaz z tohto poľa<input readOnly aria-label="Odkaz na dokument" value={typeof window === 'undefined' ? '' : window.location.href} onFocus={event => event.target.select()}/></label>}{doc.webUrl && <Link className="dl-related-link" href={doc.webUrl}>Otvoriť v aplikácii<ArrowUpRight size={15}/></Link>}{alternatives.length > 0 && <div className="dl-alternatives"><h3>Súvisiace súbory</h3>{alternatives.slice(0, 6).map(other => <button key={other.id} onClick={() => onOpen(other.id)}><FileIcon format={other.format} size={18}/><span>{colorName(other) ? `${(other.pageCount ?? 0) > 1 ? 'Celá sada · ' : ''}${colorName(other)} ${other.format}` : other.title}</span><ChevronRight size={14}/></button>)}</div>}</aside>
    </div>
  </dialog>;
}
