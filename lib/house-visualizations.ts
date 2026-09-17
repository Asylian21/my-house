import capture from './house-visualizations.generated.json';
import { designHref } from './twin-design-selection';
import type { DocumentLibrary, LibraryDocument } from './document-library';

export const VISUALIZATIONS_FOLDER = 'visualizations';

/** Static photographs of the actual C/B/B model, independent of private PDF exports. */
export function withHouseVisualizations(library: DocumentLibrary): DocumentLibrary {
  const documents: LibraryDocument[] = capture.views.map((view, index) => ({
    id: `visualization-${view.id}`, title: view.title, description: view.description,
    folderId: VISUALIZATIONS_FOLDER, code: `VIZ-${String(index + 1).padStart(2, '0')}`,
    format: 'JPG', status: 'reference',
    statusNote: `Záber z 3D modelu hlavného návrhu ${capture.design}. Zobrazuje návrh domu, nie fotografiu hotovej stavby.`,
    filename: `dom-cbb-${view.id}.jpg`, url: view.url,
    previewUrl: `${view.url}?v=${view.sha256.slice(0, 12)}`,
    thumbnailUrl: `${view.thumbnailUrl}?v=${view.sha256.slice(0, 12)}`,
    bytes: view.bytes, updatedAt: capture.capturedAt,
    visualizationGroup: view.group as 'exterior' | 'interior',
    searchText: `vizualizácia vizualizácie foto fotky domu 3D C/B/B ${view.group === 'interior' ? 'interiér obývačka kuchyňa jedáleň katedrálový strop šikmý podhľad hrebeň' : 'exteriér fasáda pohľad dom záhrada'}`,
    webUrl: designHref('/3d'),
  }));
  return { ...library,
    folders: [{ id: VISUALIZATIONS_FOLDER, title: 'Vizualizácie domu', parentId: null,
      description: 'Dom zo všetkých strán a obývačka s katedrálovým stropom. Zábery priamo z 3D modelu C/B/B.' }, ...library.folders],
    documents: [...documents, ...library.documents],
  };
}
