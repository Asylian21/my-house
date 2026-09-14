import { readFileSync, realpathSync, statSync } from 'node:fs';
import { basename, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { documentFolderIds, searchLibraryDocuments, type DocumentFolder, type DocumentLibrary, type LibraryDocument } from '../lib/document-library';

const folders: DocumentFolder[] = [
  { id: 'details', parentId: 'foundations', title: 'Detaily', description: '' },
  { id: 'foundations', parentId: 'drawings', title: 'Základy', description: '' },
  { id: 'roof', parentId: 'drawings', title: 'Strecha', description: '' },
  { id: 'drawings', parentId: null, title: 'Výkresy', description: '' },
  { id: 'archive-foundations', parentId: 'archive', title: 'Staré základy', description: '' },
  { id: 'archive', parentId: null, title: 'Archív', description: '' },
];

function document(id: string, overrides: Partial<LibraryDocument> = {}): LibraryDocument {
  return {
    id, title: id, description: '', folderId: 'foundations', format: 'PDF',
    status: 'coordination', statusNote: 'Na koordináciu, nevydané na realizáciu.',
    filename: `${id}.pdf`, url: `/documents/${id}.pdf`, bytes: 2048,
    updatedAt: '2026-09-14T12:00:00Z', searchText: '', ...overrides,
  };
}

function library(documents: LibraryDocument[]): DocumentLibrary {
  return {
    version: 1, generatedAt: '2026-09-14T12:00:00Z', sourceUpdatedAt: '2026-09-14T12:00:00Z',
    design: 'C/B/B', revision: 'TEST', folders, documents,
    featuredIds: [], bundleIds: { color: '', mono: '' },
  };
}

const examples = library([
  document('foundation-color', {
    title: 'Základy domu', code: 'D1.1.ZA-03', filename: 'CBB-zaklady-color.pdf', color: 'color',
    description: 'Priestorový pohľad.', searchText: 'R7: vlastná hmotnosť SA30, zaťaženie 456,25 kg/m.',
  }),
  document('foundation-mono', {
    title: 'Základy domu', code: 'D1.1.ZA-03', filename: 'CBB-zaklady-mono.pdf', color: 'mono',
    searchText: 'R7: vlastná hmotnosť SA30, zaťaženie 456,25 kg/m.',
  }),
  document('cornice-detail', {
    title: 'Detail rímsy', folderId: 'details', format: 'SVG', code: 'D1.1.DT-01',
    filename: 'rimsa.svg', description: 'Spodná úroveň rímsy, štúdia výšok.',
  }),
  document('roof-survey', {
    title: 'Výškový podklad', folderId: 'roof', status: 'reference',
    statusNote: 'Merací podklad.', searchText: 'Geodetické zameranie.',
  }),
  document('historic-foundation', {
    title: 'Historické základy', folderId: 'archive-foundations', status: 'archive',
    statusNote: 'Nahradený návrh, nepoužiť pre hlavné C/B/B.', code: 'D1.1.ZA-03',
    searchText: 'Staršie základy.',
  }),
]);

const ids = (documents: LibraryDocument[]) => documents.map(doc => doc.id);

describe('document library search and navigation', () => {
  it('finds Slovak titles and contents without diacritics, regardless of case', () => {
    expect(ids(searchLibraryDocuments(examples, { query: 'ZAKLADY HMOTNOST' })))
      .toEqual(['foundation-color', 'foundation-mono']);
    expect(ids(searchLibraryDocuments(examples, { query: 'rimsy STUDIA' })))
      .toEqual(['cornice-detail']);
  });

  it('requires all search terms while allowing them to come from filename, code and content', () => {
    expect(ids(searchLibraryDocuments(examples, { query: 'color ZA-03 zaťaženie' })))
      .toEqual(['foundation-color']);
    expect(searchLibraryDocuments(examples, { query: 'color ZA-03 komín' })).toEqual([]);
  });

  it('treats a blank query as browsing and an unknown term as no results', () => {
    expect(searchLibraryDocuments(examples, { query: '  \n\t ' })).toHaveLength(examples.documents.length);
    expect(searchLibraryDocuments(examples, { query: 'neexistujucipodklad' })).toEqual([]);
  });

  it('includes nested folders even when parents are listed after their children', () => {
    expect([...documentFolderIds(folders, 'drawings')].sort())
      .toEqual(['details', 'drawings', 'foundations', 'roof']);
    expect(ids(searchLibraryDocuments(examples, { folderId: 'foundations' })).sort())
      .toEqual(['cornice-detail', 'foundation-color', 'foundation-mono']);
    expect(searchLibraryDocuments(examples, { folderId: 'missing-folder' })).toEqual([]);
  });

  it('combines folder, format, status and text filters instead of broadening one another', () => {
    expect(ids(searchLibraryDocuments(examples, {
      folderId: 'drawings', format: 'PDF', status: 'coordination', query: 'SA30',
    }))).toEqual(['foundation-color', 'foundation-mono']);
    expect(ids(searchLibraryDocuments(examples, {
      folderId: 'drawings', format: 'PDF', status: 'reference',
    }))).toEqual(['roof-survey']);
    expect(searchLibraryDocuments(examples, {
      folderId: 'foundations', format: 'SVG', status: 'archive',
    })).toEqual([]);
    expect(searchLibraryDocuments(examples, {
      folderId: 'all', format: 'all', status: 'all',
    })).toHaveLength(examples.documents.length);
  });

  it('uses explicit archive status rather than inferring it from a filename or historical text', () => {
    const docs = library([
      document('active', { filename: 'office-acoustic-wall-thinner-options.md', format: 'MD', searchText: 'Aktuálne H200. Historická záloha SA25-AKU 274 mm je v archíve.' }),
      document('replaced', { filename: 'office-acoustic-wall-study.md', format: 'MD', status: 'archive', statusNote: 'Nahradená záloha SA25-AKU 274 mm.', searchText: 'SA25-AKU, hrúbka 274 mm.' }),
    ]);
    expect(ids(searchLibraryDocuments(docs, { query: '274', status: 'archive' }))).toEqual(['replaced']);
    expect(ids(searchLibraryDocuments(docs, { query: '274', status: 'coordination' }))).toEqual(['active']);
  });

  it('sorts drawing names and codes naturally and places the newest revision first', () => {
    const docs = library([
      document('ten', { title: 'Rez 10', code: 'RE-10', updatedAt: '2026-09-12T12:00:00Z' }),
      document('two', { title: 'Rez 2', code: 'RE-2', updatedAt: '2026-09-14T12:00:00Z' }),
      document('uncoded', { title: 'Správa', updatedAt: '2026-09-13T12:00:00Z' }),
    ]);
    expect(ids(searchLibraryDocuments(docs, { sort: 'name' }))).toEqual(['two', 'ten', 'uncoded']);
    expect(ids(searchLibraryDocuments(docs, { sort: 'code' }))).toEqual(['two', 'ten', 'uncoded']);
    expect(ids(searchLibraryDocuments(docs, { sort: 'updated' }))).toEqual(['two', 'uncoded', 'ten']);
    expect(ids(docs.documents)).toEqual(['ten', 'two', 'uncoded']);
  });

  it('keeps equal-key color and monochrome entries stable when changing sort modes', () => {
    const docs = library([
      document('color', { title: 'Detail', code: 'DT-01', color: 'color' }),
      document('mono', { title: 'Detail', code: 'DT-01', color: 'mono' }),
    ]);
    for (const sort of ['name', 'code', 'updated'] as const) {
      expect(ids(searchLibraryDocuments(docs, { sort }))).toEqual(['color', 'mono']);
    }
  });
});

const expectedSheetCodes = [
  'D1.1.000-C', 'D1.1.002-C-RE',
  'D1.1.PO-01', 'D1.1.PO-02', 'D1.1.PO-03', 'D1.1.PO-04',
  'D1.1.PO-05', 'D1.1.PO-06', 'D1.1.PO-07', 'D1.1.PO-08',
  'D1.1.RE-01', 'D1.1.RE-02', 'D1.1.RE-03',
  'D1.1.ZA-01', 'D1.1.ZA-02', 'D1.1.ZA-03', 'D1.1.ST-01',
  'C.SI-01', 'C.SI-02', 'C.UP-01', 'D1.1.OT-01', 'D1.1.OT-02',
  'D1.1.SK-01', 'D1.1.DT-01', 'D1.1.TZ-01',
];
const publicRoot = fileURLToPath(new URL('../public/', import.meta.url));

function publicFile(url: string) {
  expect(url, 'downloads and previews must be deployable public assets').toMatch(/^\/documents\/[^?#]+$/);
  const decoded = decodeURIComponent(url);
  expect(decoded).not.toMatch(/\\|(?:^|\/)\.{1,2}(?:\/|$)|\/(?:Users|home|Volumes|private|tmp)\//i);
  const path = realpathSync(resolve(publicRoot, `.${decoded}`));
  const relativePath = relative(realpathSync(publicRoot), path);
  expect(relativePath.startsWith('..'), url).toBe(false);
  expect(statSync(path).isFile(), url).toBe(true);
  expect(statSync(path).size, url).toBeGreaterThan(0);
  return path;
}

describe('generated document library and downloadable files', () => {
  let catalog: DocumentLibrary;
  beforeAll(() => {
    // A missing generated manifest is a release failure, not a reason to skip this suite.
    catalog = JSON.parse(readFileSync(new URL('../lib/document-library.generated.json', import.meta.url), 'utf8'));
  });

  it('has unique document and folder IDs and a valid acyclic folder tree', () => {
    expect(catalog.design.replaceAll(' ', '')).toBe('C/B/B');
    expect(catalog.revision.trim()).not.toBe('');
    expect(Number.isNaN(Date.parse(catalog.generatedAt))).toBe(false);
    const folderById = new Map(catalog.folders.map(folder => [folder.id, folder]));
    expect(folderById.size).toBe(catalog.folders.length);
    expect(new Set(catalog.documents.map(doc => doc.id)).size).toBe(catalog.documents.length);
    for (const folder of catalog.folders) {
      const ancestors = new Set([folder.id]);
      let parentId = folder.parentId;
      while (parentId !== null) {
        expect(folderById.has(parentId), `${folder.id}: missing parent ${parentId}`).toBe(true);
        expect(ancestors.has(parentId), `${folder.id}: folder cycle`).toBe(false);
        ancestors.add(parentId);
        parentId = folderById.get(parentId)!.parentId;
      }
    }
    for (const doc of catalog.documents) {
      expect(folderById.has(doc.folderId), `${doc.id}: missing folder`).toBe(true);
      expect(['coordination', 'reference', 'archive']).toContain(doc.status);
      expect(doc.statusNote.trim(), `${doc.id}: unexplained status`).not.toBe('');
      expect(Number.isNaN(Date.parse(doc.updatedAt)), `${doc.id}: invalid revision date`).toBe(false);
    }
  });

  it('provides every one of the 25 sheets separately in color and monochrome', () => {
    for (const color of ['color', 'mono'] as const) {
      const sheets = catalog.documents.filter(doc => doc.format === 'PDF' && doc.color === color && expectedSheetCodes.includes(doc.code ?? ''));
      expect(sheets.map(doc => doc.code).sort()).toEqual([...expectedSheetCodes].sort());
      for (const sheet of sheets) {
        expect(sheet.pageCount, sheet.id).toBe(1);
        expect(sheet.paper, sheet.id).toBe('A1');
        expect(sheet.status, sheet.id).toBe('coordination');
      }
      const bundle = catalog.documents.find(doc => doc.id === catalog.bundleIds[color]);
      expect(bundle, `${color} bundle`).toMatchObject({ format: 'PDF', pageCount: 25, paper: 'A1', color, status: 'coordination' });
    }
  });

  it('links featured and related items to documents that actually exist', () => {
    const known = new Set(catalog.documents.map(doc => doc.id));
    expect(catalog.featuredIds.length).toBeGreaterThan(0);
    for (const id of [...catalog.featuredIds, ...Object.values(catalog.bundleIds)]) expect(known.has(id), id).toBe(true);
    for (const doc of catalog.documents) {
      for (const id of doc.relatedIds ?? []) {
        expect(known.has(id), `${doc.id} -> ${id}`).toBe(true);
        expect(id, `${doc.id}: related item should not point to itself`).not.toBe(doc.id);
      }
    }
  });

  it('serves real nonempty files with accurate sizes and no host paths or directory escapes', () => {
    for (const doc of catalog.documents) {
      expect(doc.filename, doc.id).toBe(basename(doc.filename));
      expect(doc.filename.toLowerCase(), doc.id).toMatch(new RegExp(`\\.${doc.format.toLowerCase()}$`));
      expect(Number.isSafeInteger(doc.bytes), doc.id).toBe(true);
      const path = publicFile(doc.url);
      expect(doc.bytes, doc.id).toBe(statSync(path).size);
      if (doc.format === 'PDF') expect(readFileSync(path).subarray(0, 5).toString(), doc.id).toBe('%PDF-');
      for (const preview of [doc.previewUrl, doc.thumbnailUrl, ...doc.pagePreviewUrls ?? []]) if (preview) publicFile(preview);
      if (doc.pagePreviewUrls) {
        expect(doc.pagePreviewUrls, doc.id).toHaveLength(doc.pageCount!);
        expect(new Set(doc.pagePreviewUrls).size, doc.id).toBe(doc.pageCount);
      }
    }
    expect(catalog.documents.find(doc => doc.id === 'report-h200-scientific-pdf')?.pagePreviewUrls).toHaveLength(7);
  });

  it('finds current R7 and both verified SA30 mass values inside each ZA-03 PDF', () => {
    const found = searchLibraryDocuments(catalog, {
      query: 'R7 SA30 456,25 2781,30', format: 'PDF', status: 'coordination',
    });
    const axons = found.filter(doc => doc.code === 'D1.1.ZA-03');
    expect(axons.map(doc => doc.color).sort()).toEqual(['color', 'mono']);
  });

  it('keeps current construction reports available and the rejected 274 mm study explicitly archived', () => {
    for (const filename of [
      'construction-drawings.md', 'construction-entry-basis.md', 'construction-foundation-axon.md',
      'construction-height-basis.md', 'construction-roof-heating-basis.md', 'construction-structural-basis.md',
    ]) {
      const reports = catalog.documents.filter(doc => doc.filename === filename);
      expect(reports, filename).toHaveLength(1);
      expect(reports[0].status, filename).not.toBe('archive');
    }
    const archived = catalog.documents.filter(doc => doc.filename === 'office-acoustic-wall-study.md');
    expect(archived).toHaveLength(1);
    expect(archived[0].status).toBe('archive');
    expect(archived[0].statusNote.trim()).not.toBe('');
    const current = catalog.documents.find(doc => doc.filename === 'office-acoustic-wall-thinner-options.md');
    expect(current).toBeDefined();
    expect(current!.status).not.toBe('archive');
    const archiveFolders = documentFolderIds(catalog.folders, 'archive');
    for (const doc of catalog.documents.filter(doc => archiveFolders.has(doc.folderId))) expect(doc.status, doc.id).toBe('archive');
  });
});
