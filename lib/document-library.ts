export type DocumentFormat = 'PDF' | 'SVG' | 'PNG' | 'MD' | 'JSON';
export type DocumentStatus = 'coordination' | 'reference' | 'archive';

export interface DocumentFolder {
  id: string;
  title: string;
  parentId: string | null;
  description: string;
}

export interface LibraryDocument {
  id: string;
  title: string;
  description: string;
  folderId: string;
  code?: string;
  format: DocumentFormat;
  status: DocumentStatus;
  statusNote: string;
  filename: string;
  url: string;
  previewUrl?: string;
  pagePreviewUrls?: string[];
  thumbnailUrl?: string;
  bytes: number;
  updatedAt: string;
  pageCount?: number;
  sheetIndex?: number;
  bundleId?: string;
  scale?: string;
  paper?: string;
  color?: 'color' | 'mono';
  searchText: string;
  relatedIds?: string[];
  webUrl?: string;
}

export interface DocumentLibrary {
  version: number;
  generatedAt: string;
  design: string;
  revision: string;
  sourceUpdatedAt: string;
  folders: DocumentFolder[];
  documents: LibraryDocument[];
  featuredIds: string[];
  bundleIds: { color: string; mono: string };
}

export const DOCUMENT_STATUS: Record<DocumentStatus, string> = {
  coordination: 'Na koordináciu',
  reference: 'Podklad',
  archive: 'Archív',
};

export function normalizeDocumentSearch(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('sk').replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
}

export function documentFolderIds(folders: DocumentFolder[], selected: string): Set<string> {
  const ids = new Set([selected]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const folder of folders) if (folder.parentId && ids.has(folder.parentId) && !ids.has(folder.id)) {
      ids.add(folder.id); changed = true;
    }
  }
  return ids;
}

export function searchLibraryDocuments(library: DocumentLibrary, options: {
  folderId?: string; query?: string; format?: string; status?: string;
  sort?: 'name' | 'updated' | 'code';
}) {
  const scope = options.folderId && options.folderId !== 'all' ? documentFolderIds(library.folders, options.folderId) : null;
  const tokens = normalizeDocumentSearch(options.query ?? '').split(' ').filter(Boolean);
  const docs = library.documents.filter(doc => {
    if (scope && !scope.has(doc.folderId)) return false;
    if (options.format && options.format !== 'all' && doc.format !== options.format) return false;
    if (options.status && options.status !== 'all' && doc.status !== options.status) return false;
    const haystack = normalizeDocumentSearch([doc.title, doc.description, doc.code, doc.filename, doc.searchText].join(' '));
    return tokens.every(token => haystack.includes(token));
  });
  return docs.sort((a, b) => options.sort === 'updated'
    ? b.updatedAt.localeCompare(a.updatedAt) || a.title.localeCompare(b.title, 'sk')
    : options.sort === 'code'
      ? (a.code ?? 'ZZZ').localeCompare(b.code ?? 'ZZZ', 'sk', { numeric: true }) || a.title.localeCompare(b.title, 'sk')
      : a.title.localeCompare(b.title, 'sk', { numeric: true }));
}

export function formatDocumentBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  const unit = bytes < 1024 * 1024 ? 'kB' : 'MB';
  const amount = bytes / (unit === 'kB' ? 1024 : 1024 * 1024);
  return `${amount.toLocaleString('sk-SK', { maximumFractionDigits: 1 })} ${unit}`;
}

export function formatDocumentDate(date: string) {
  return new Intl.DateTimeFormat('sk-SK', { day: 'numeric', month: 'numeric', year: 'numeric', timeZone: 'Europe/Bratislava' }).format(new Date(date));
}
