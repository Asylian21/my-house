"""Isolated R14 geometry experiment; no Unreal, density, shader or scene writes.

Compare a bounded, widest-leaf V fold with an all-leaf close-LOD alternative.
The actual current photographer UV interpolation and XY silhouette are retained.
Seeded tip droop changes real Z geometry; ridge vertices subdivide the existing
shoulder edge, so the protected source crown does not grow. Coverage is measured
again from the exported float32 geometry against the unchanged four source ROIs.
This deliberately discloses the remaining two longitudinal segments and straight
outer segments: neither version is a smooth botanical reconstruction.
"""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-folded-study.py'
PHOTO = ROOT/'output/unreal/exterior-lawn-photo-variants-20261001-r3-study'
DONOR = ROOT/'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'
MATERIAL = 'lawn_photographic_blade'
PINS = {
    PHOTO/'lawn-photographic-variants.glb': 'ddb4402577e844ec5e70ca4417c0c686778cca4f35f6c766155313a6aae9aebd',
    PHOTO/'geometry-manifest.json': '4f671b902732999f542e301ab11cab3ca29e6718cdad1d5d8bd0da6b81781730',
    PHOTO/'material-manifest.json': '9a0275363882594afb4b656ffbd7528866ad63366d03cf938bf562ac6ec5c88e',
    PHOTO/'photographic-alpha-coverage-receipt.json': '0b6e9e163fb48182e2669c1111a851d5b8cff7fa5f48ff3a5ebb2b8637a16118',
    DONOR/'lawn-natural-plan.json': '0c13741cf2344ef809ac4427b4102a4917eefd508bc0b3c3746312029800c319',
    DONOR/'lawn-natural-prototypes.json': 'f356a5a2ff014d5faa4647ac16e610e9b8c751ed3057ba48d95369b99b88c7fd',
    ROOT/'scripts/unreal/exterior-lawn-photo-variants.py': '7d57758086df5a4305282cbe18e913364566c7b7c4ebc5242146418cb78b9a85',
    ROOT/'scripts/unreal/exterior-lawn-tapered-photo-uv-study.py': 'cc9e19d66d661160707b63a8f256a412351d3a025185f96be5d9e89050510dd2',
    ROOT/'scripts/unreal/exterior-lawn-photo-uv-study.py': 'e313373d21c8a49b80a878dade66649c6c6809f1d543b9128ca69e1ba9053850',
}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def pin(path): return {'path': str(Path(path).resolve()), 'sha256': sha(path)}
def require(value, message):
    if not value: raise RuntimeError(message)
def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def native_record(raw):
    return {'positionsCm': raw['POSITION'][:, [0, 2, 1]].astype(float)*100,
            'normals': raw['NORMAL'][:, [0, 2, 1]].astype(float),
            'uv0': raw['TEXCOORD_0'].astype(float), 'uv1': raw['TEXCOORD_1'].astype(float),
            'colors': raw['COLOR_0'].astype(float), 'triangles': raw['indices'][:, [0, 2, 1]].astype(int)}


def selection(record, meta):
    scores = []
    for blade in meta['bladeRanges']:
        p = record['positionsCm'][blade['vertexOffset']:blade['vertexOffset']+5]
        width = np.linalg.norm(p[3]-p[2])
        tip_area = np.linalg.norm(np.cross(p[3]-p[2], p[4]-p[2]))/2
        # Real widest, most exposed terminal faces; no new random placement.
        scores.append((float(width*tip_area), blade['bladeIndex']))
    count = 5 if meta['edgeMaster'] else 7
    return sorted(index for _, index in sorted(scores, reverse=True)[:count])


def geometry(record, meta, selected, lod, identity):
    p, uv, uv1, colors, faces, ranges = [], [], [], [], [], []
    high = float(record['positionsCm'][:, 2].max())
    tallest = int(np.argmax(record['positionsCm'][:, 2]))//5
    for blade in meta['bladeRanges']:
        index = blade['bladeIndex']; start = blade['vertexOffset']; first = len(p); face_start = len(faces)
        xyz = record['positionsCm'][start:start+5].copy()
        seed = float(record['uv1'][start, 0])
        span = float(xyz[:, 2].max()-xyz[:, 2].min())
        # A changed real terminal direction; root and shoulder edges stay fixed.
        # Keep the original highest leaf so the complete source Z bounds persist.
        droop = 0. if index == tallest else span*(.055+.155*((seed*17.137+index*.173)%1))
        xyz[4, 2] -= droop
        p.extend(xyz); uv.extend(record['uv0'][start:start+5])
        uv1.extend(record['uv1'][start:start+5]); colors.extend(record['colors'][start:start+5])
        folded = index in selected and lod < 2
        ridge = 0.
        if folded:
            middle = (xyz[2]+xyz[3])*.5
            width = float(np.linalg.norm(xyz[3]-xyz[2]))
            ridge = width*(.12+.06*((seed*7.731+index*.097)%1))
            middle[2] += ridge
            require(middle[2] <= high, 'Fold exceeds original source height cap')
            p.append(middle)
            uv.append((record['uv0'][start+2]+record['uv0'][start+3])*.5)
            uv1.append((record['uv1'][start+2]+record['uv1'][start+3])*.5)
            colors.append((record['colors'][start+2]+record['colors'][start+3])*.5)
            # One real widthwise ridge: original body and terminal plane split.
            local = [[0, 1, 2], [1, 3, 5], [1, 5, 2], [2, 5, 4], [5, 3, 4]]
        else:
            local = [[0, 1, 2], [1, 3, 2], [2, 3, 4]]
        faces.extend([[first+i for i in face] for face in local])
        ranges.append({'bladeIndex': index, 'vertexOffset': first, 'vertexCount': 6 if folded else 5,
                       'triangleOffset': face_start, 'triangleCount': len(local), 'folded': folded,
                       'sourceRootCm': blade['rootCm'], 'tipDroopCm': droop, 'ridgeHeightCm': ridge,
                       'sourceWidthCm': float(np.linalg.norm(xyz[3]-xyz[2])),
                       'seed': seed, 'sourceLowLeaningLeaf': blade['low']})
    record = {'nodeName': identity+'_LOD'+str(lod), 'positionsCm': np.asarray(p), 'uv0': np.asarray(uv),
              'uv1': np.asarray(uv1), 'colors': np.asarray(colors), 'triangles': np.asarray(faces),
              'bladeRanges': ranges, 'sourceNode': meta['nodeName']}
    # Frames are derived from the exact float32 serialized geometry and UVs.
    encoded = (record['positionsCm'][:, [0, 2, 1]]/100).astype('<f4')
    record['positionsCm'] = encoded[:, [0, 2, 1]].astype(float)*100
    for key in ('uv0', 'uv1', 'colors'): record[key] = record[key].astype('<f4').astype(float)
    normals = np.zeros_like(record['positionsCm'])
    for face in record['triangles']:
        q = record['positionsCm'][face]; cross = np.cross(q[1]-q[0], q[2]-q[0])
        require(np.linalg.norm(cross)>1e-8, 'Degenerate exported fold triangle')
        normals[face] += cross
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    record['normals'] = normals
    return record


def write_glb(path, records, tangent_api):
    binary = bytearray(); document = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0,
        'scenes': [{'nodes': list(range(len(records)))}], 'nodes': [], 'meshes': [], 'accessors': [], 'bufferViews': [],
        'materials': [{'name': MATERIAL, 'doubleSided': True}], 'buffers': []}
    metrics = []
    def accessor(values, kind, dtype='<f4', target=34962):
        a = np.asarray(values, dtype=dtype); binary.extend(b'\0'*(-len(binary)%4)); offset = len(binary); binary.extend(a.tobytes())
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': a.nbytes, 'target': target})
        row = {'bufferView': len(document['bufferViews'])-1, 'componentType': 5126 if dtype=='<f4' else 5125,
               'count': len(a), 'type': kind}
        if kind=='VEC3': row.update(min=a.min(0).tolist(), max=a.max(0).tolist())
        document['accessors'].append(row); return len(document['accessors'])-1
    for row in records:
        normals = row['normals'].astype('<f4').astype(float)
        tangent, faces = tangent_api.tangent_frame(row['positionsCm'], normals, row['uv0'], row['triangles'])
        attrs = {'POSITION': accessor(row['positionsCm'][:, [0, 2, 1]]/100, 'VEC3'),
                 'NORMAL': accessor(normals[:, [0, 2, 1]], 'VEC3'),
                 'TANGENT': accessor(np.column_stack([tangent[:, :3][:, [0, 2, 1]], -tangent[:, 3]]), 'VEC4'),
                 'TEXCOORD_0': accessor(row['uv0'], 'VEC2'), 'TEXCOORD_1': accessor(row['uv1'], 'VEC2'),
                 'COLOR_0': accessor(row['colors'], 'VEC4')}
        indices = accessor(row['triangles'][:, [0, 2, 1]].reshape(-1), 'SCALAR', '<u4', 34963)
        document['meshes'].append({'name': row['nodeName'], 'primitives': [{'attributes': attrs, 'indices': indices, 'material': 0}]})
        document['nodes'].append({'name': row['nodeName'], 'mesh': len(document['meshes'])-1})
        metrics.append({'node': row['nodeName'], 'triangles': len(faces),
                        'minimumTriangleAreaCm2': min(f['areaCm2'] for f in faces),
                        'minimumUvTriangleArea': min(f['uvArea'] for f in faces)})
    binary.extend(b'\0'*(-len(binary)%4)); document['buffers'] = [{'byteLength': len(binary)}]
    raw = json.dumps(document, separators=(',', ':'), allow_nan=False).encode(); raw += b' '*(-len(raw)%4)
    with path.open('xb') as stream:
        stream.write(struct.pack('<4sII', b'glTF', 2, 28+len(raw)+len(binary)))
        stream.write(struct.pack('<II', len(raw), 0x4e4f534a)); stream.write(raw)
        stream.write(struct.pack('<II', len(binary), 0x004e4942)); stream.write(binary)
    return metrics


def preview(output, baseline, profiles, metadata, recipe, renderer):
    texture = np.asarray(Image.open(recipe['maps']['albedo']['path']), dtype=float)/255
    alpha = np.asarray(Image.open(recipe['maps']['alpha']['path']), dtype=float)/65535
    source = inspect.getsource(renderer.render)
    old = 'screen=np.column_stack([p@right*100+width/2,height*.82-p@up*100,p@camera])'
    new = 'screen=np.column_stack([(p@right-frame[0])*frame[2]+width/2,height-55-(p@up-frame[1])*frame[2],p@camera])'
    require(source.count(old)==1, 'Pinned CPU camera convention changed')
    namespace = dict(renderer.__dict__); exec(compile(source.replace(old,new), '<new-r14-source-preview>', 'exec'), namespace)
    name = 'lawn_natural_0_3_LOD0'; base = baseline[name]
    selected = selection(base, metadata[name])[:4]
    for few in (False, True):
        assembled = []
        for label, records in [('Current photographic R13 geometry', baseline), ('Budgeted widest-leaf folds + tip droop', profiles['adaptive']),
                               ('All-leaf close LOD folds + tip droop', profiles['full_close'])]:
            row = records[name]; p = []; n = []; ix = []; uv = []
            if few:
                for slot, index in enumerate(selected):
                    blade = row['bladeRanges'][index]; start = blade['vertexOffset']; count = blade['vertexCount']; offset = len(p)-start
                    q = row['positionsCm'][start:start+count].copy()
                    q[:, :2] += [(slot-1.5)*1.15, 0]-np.asarray(blade.get('sourceRootCm', blade.get('rootCm')))
                    p.extend(q); n.extend(row['normals'][start:start+count]); uv.extend(row['uv0'][start:start+count])
                    ix.extend(row['triangles'][blade['triangleOffset']:blade['triangleOffset']+blade['triangleCount']]+offset)
                item = {'p': np.asarray(p), 'n': np.asarray(n), 'ix': np.asarray(ix)}; photo_uv = np.asarray(uv)
            else:
                item = {'p': row['positionsCm'], 'n': row['normals'], 'ix': row['triangles']}; photo_uv = row['uv0']
            assembled.append((label, item, photo_uv))
        camera = np.array([.22,.92,.42]); camera /= np.linalg.norm(camera)
        right = np.array([camera[1],-camera[0],0.]); right /= np.linalg.norm(right); up = np.cross(right,camera)
        allp = np.concatenate([row['p'] for _, row, _ in assembled]); sx = allp@right; sy = allp@up
        namespace['frame'] = [(sx.min()+sx.max())/2, sy.min(), min(570/np.ptp(sx),540/np.ptp(sy))]
        plate = Image.new('RGB',(1980,740),'#eeebe3'); draw = ImageDraw.Draw(plate)
        stats = {}
        for col, (label, item, photo_uv) in enumerate(assembled):
            image, result = namespace['render'](item, photo_uv, texture, alpha, recipe, 'photo', None)
            plate.paste(image, (col*660,48)); draw.text((col*660+12,16),label,fill='#202820'); stats[label] = result
        draw.text((12,704),'Actual exported source geometry + same original PH pixels. CPU diffuse/geometric-normal display only; no normal-map, roughness, SSS, mips, native shadows or Unreal proof.',fill='#202820')
        draw.text((12,724),'Four widest-leaf examples, roots moved for display only.' if few else 'Same actual64-leaf source clump/root layout. Adaptive folds7 leaves; all-fold profile64 at close LOD. Not a whole lawn/native view.',fill='#202820')
        plate.save(output/('four-folded-leaves.png' if few else 'folded-clump-comparison.png'))
        write(output/('four-leaf-render-statistics.json' if few else 'clump-render-statistics.json'),stats)


def build(output):
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a fresh isolated study output')
    inputs = {str(p): h for p,h in PINS.items()}; inputs[str(Path(__file__).resolve())] = sha(__file__)
    manifest = read(PHOTO/'geometry-manifest.json'); plan = read(DONOR/'lawn-natural-plan.json')
    prior_coverage = read(PHOTO/'photographic-alpha-coverage-receipt.json')
    recipe = read(PHOTO/'material-manifest.json')[MATERIAL]
    for value in recipe['maps'].values(): inputs[value['path']] = value['sha256']
    for path,h in inputs.items(): require(sha(path)==h, 'Pinned source changed before study: '+path)
    require(plan['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'} and
            plan['housePlacement']['streetSetbackMm']==plan['housePlacement']['eastSetbackMm']==3000, 'C/B/B/setbacks differ')
    require(len(plan['lawnPlacements'])==102011 and len(plan['groups'])==40, 'Source ordered population differs')
    api = module('r14_frozen_photo_source', ROOT/'scripts/unreal/exterior-lawn-photo-variants.py')
    tangent = module('r14_frozen_photo_tangent', ROOT/'scripts/unreal/exterior-lawn-tapered-photo-uv-study.py')
    renderer = module('r14_frozen_cpu_photo_renderer', ROOT/'scripts/unreal/exterior-lawn-photo-uv-study.py')
    _,_,_,decoded = api.glb(PHOTO/'lawn-photographic-variants.glb')
    metadata = {row['nodeName']: row for row in read(DONOR/'lawn-natural-prototypes.json')}
    baseline = {}
    for name, meta in metadata.items():
        row = native_record(decoded[name.replace('lawn_natural_','lawn_photo_',1)])
        row.update(bladeRanges=deepcopy(meta['bladeRanges']),nodeName=name); baseline[name] = row
    output.mkdir(); profiles = {}; reports = {}; alpha = np.asarray(Image.open(recipe['maps']['alpha']['path']),dtype=float)/65535
    for mode in ('adaptive','full_close'):
        folder = output/mode; folder.mkdir(); records = []; masters = []; geometric = []
        for source in manifest['meshes']:
            old_id = source['sourceMeshId']; source0 = baseline[old_id+'_LOD0']; meta = metadata[old_id+'_LOD0']
            chosen = selection(source0, meta); lods = []
            identity = old_id.replace('lawn_natural_','lawn_folded_',1)
            for lod in range(3):
                folds = list(range(len(meta['bladeRanges']))) if mode=='full_close' and lod==0 else chosen
                row = geometry(source0, meta, folds, lod, identity); records.append(row)
                old = source0['positionsCm']; new = row['positionsCm']
                # Existing XY vertices are exact; extra ridge is a convex source edge point.
                for blade in row['bladeRanges']:
                    i = blade['bladeIndex']; a = meta['bladeRanges'][i]['vertexOffset']; b = blade['vertexOffset']
                    require(np.array_equal(new[b:b+5,:2],old[a:a+5,:2]), 'Original source XY silhouette changed')
                    if blade['folded']:
                        require(np.max(abs(new[b+5,:2]-(old[a+2,:2]+old[a+3,:2])*.5))<.000001,
                                'Ridge left original shoulder edge')
                require(new[:,2].min()==old[:,2].min() and new[:,2].max()==old[:,2].max(), 'Original height envelope changed')
                require(np.linalg.norm(new[:,:2],axis=1).max()<=np.linalg.norm(old[:,:2],axis=1).max()+1e-6,
                        'Source radial crown grew')
                low,high = new.min(0).tolist(),new.max(0).tolist()
                lods.append({'level':lod,'nodeName':row['nodeName'],'vertices':len(new),'triangles':len(row['triangles']),
                             'expectedBoundsCm':{'min':low,'max':high},'foldedLeaves':sum(b['folded'] for b in row['bladeRanges']),
                             'radialEnvelopeCm':float(np.linalg.norm(new[:,:2],axis=1).max())})
                geometric.append({'node':row['nodeName'],'source':old_id+'_LOD0','selectedLeafIndices':folds if lod<2 else [],
                                  'allOriginalXYVerticesExact':True,'newVerticesOnOriginalXYShoulderEdge':True,
                                  'sourceBoundsAndCircularCrownsPreserved':True,
                                  'ridgeHeightCm':[b['ridgeHeightCm'] for b in row['bladeRanges'] if b['folded']],
                                  'tipDroopCm':[b['tipDroopCm'] for b in row['bladeRanges']]})
            masters.append({'id':identity,'sourceMeshId':old_id,'role':'grass','placementPolicy':'explicit-only',
                            'materialKeys':[MATERIAL],'lodScreenSizes':[1,.025,.007],'lods':lods,
                            'heightCm':source['heightCm'],'selectedWidestLeafIndices':chosen})
        metrics = write_glb(folder/'folded-lawn.glb', records, tangent)
        _,_,_,saved = api.glb(folder/'folded-lawn.glb'); saved_records = {}
        for row in records:
            fresh = native_record(saved[row['nodeName']]); fresh.update(bladeRanges=row['bladeRanges'],nodeName=row['nodeName'])
            require(np.array_equal(fresh['positionsCm'],row['positionsCm']) and np.array_equal(fresh['uv0'],row['uv0']), 'Actual saved float32 source differs')
            original_name = row['nodeName'].replace('lawn_folded_','lawn_natural_',1); saved_records[original_name] = fresh
        profiles[mode] = saved_records
        lookup = {m['sourceMeshId']:m for m in masters}
        budgets = [sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['triangles'] for g in plan['groups']) for lod in range(3)]
        populations = [sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['foldedLeaves'] for g in plan['groups']) for lod in range(3)]
        windows = []
        for window in prior_coverage['physicalCoverage']['windows']:
            opaque, photograph, count, stats = api.alpha_footprint(saved_records,plan['lawnPlacements'],window,alpha)
            current = api.interior_metrics(photograph); current['studyTargetsMet'] = current['projectedCoverage']>=.75 and current['tenCmBinCoverageP10']>=.55 and current['bareTenCmBins']==0
            windows.append({'centerCm':window['centerCm'],'sizeCm':100,'resolution':4000,'lod':0,
                            'instances':count,**current,'opaqueCoverage':float(opaque.mean()),'raster':stats,
                            'currentPhotoBaseline':window['lods'][0]})
            Image.fromarray(np.uint8(photograph)*255).resize((600,600),Image.Resampling.BOX).save(folder/('coverage_'+str(window['centerCm'][0])+'_'+str(window['centerCm'][1])+'.png'))
        for master in masters: master.update(glbPath=str(folder/'folded-lawn.glb'),glbSha256=sha(folder/'folded-lawn.glb'))
        write(folder/'geometry-manifest.json',{'schema':1,'owner':OWNER,'generatorSha256':sha(__file__),
            'units':'metres','axes':'glTF Y-up; Unreal native=[100*x,100*z,100*y]', 'status':'SOURCE_ONLY_NOT_NATIVE_ACCEPTED',
            'activeDesign':plan['activeDesign'],'housePlacement':plan['housePlacement'],'meshes':masters,
            'materialManifest':pin(PHOTO/'material-manifest.json'),'sourcePlacementPlan':pin(DONOR/'lawn-natural-plan.json')})
        reports[mode] = {'masters':20,'lods':60,'populationTriangleBudgetByLod':budgets,
                        'foldedLeafPopulationByLod':populations,'populationBudget20MMetByLod':[b<=20000000 for b in budgets],
                        'fourSourceWindows':windows,'allFourOriginalTargetsMet':all(w['studyTargetsMet'] for w in windows),
                        'geometry':geometric,'actualTriangleUvMetrics':metrics,'farFoldGeometryLossExplicit':True,
                        'fullCloseOnlyOver20MIsAnExplicitAlternativeNotApprovedIntegration':mode=='full_close'}
        write(folder/'study-measurements.json',reports[mode])
    preview(output,baseline,profiles,metadata,recipe,renderer)
    for path,h in inputs.items(): require(sha(path)==h, 'Pinned source changed during study: '+path)
    with (output/'study-source.py').open('x') as stream: stream.write(Path(__file__).read_text())
    summary = {'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__),'status':'SOURCE_ONLY_FOLDED_GEOMETRY_NATIVE_PENDING',
               'inputFiles':inputs,'activeDesign':plan['activeDesign'],'housePlacement':plan['housePlacement'],
               'sourceSceneSha256':plan['sourceSceneSha256'],'sourceObjSha256':plan['sourceObjSha256'],
               'sourcePopulation':{'instances':102011,'groups':40,'orderedPlacementsUnchanged':True,'sourcePlan':pin(DONOR/'lawn-natural-plan.json')},
               'profiles':{mode:{k:v for k,v in report.items() if k not in ('geometry','actualTriangleUvMetrics')}for mode,report in reports.items()},
               'opticalControl':{'materialKey':MATERIAL,'unchangedPhotographicRecipe':recipe,'photographicPixelsUnmodified':True,
                                 'uvInterpolationOnOriginalSurfaceRetained':True,'normalsAndUvTangentsRecomputedForChangedGeometry':True},
               'preservation':{'sourceXYFootprintsAndAllOriginalCircularCrownsPreserved':True,'sourceZEnvelopePreserved':True,
                               'sourcePrivateMasksArchitectureCollisionAndSetbacksUnchanged':True,'densityOrRootMoves':0,'shaderChanges':0},
               'limits':['Adaptive folds only7/64 interior and5/48 boundary leaves; remaining leaves still have three triangles.',
                         'A genuine geometric V fold, not a smooth parabolic cross-section. Two longitudinal sections remain.',
                         'Physical blade width and XY taper are unchanged; no narrower top-view silhouette is claimed.',
                         'Only four interior windows rerastered here; old boundary gates are not relabeled as new tests.',
                         'Near/mid folded and far simple geometry differ; source CPU images do not establish native LOD visibility or transition quality.',
                         'CPU diffuse uses geometric normals and original photo alpha only; original normalDX/roughness/SSS/mips are not rendered.',
                         'No forest-floor/ground/density/photographic colour adjustments. No integration or full-lawn realism acceptance.'],
               'allInputHashesUnchangedBeforeAndAfter':True,'formalUnitTestsRun':0,'nativeJobsRun':0,'gpuJobsRun':0,
               'nativeVisualAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'integrationAuthorized':False}
    write(output/'study.json',summary)
    print(json.dumps({'study':str(output/'study.json'),'sha256':sha(output/'study.json'),
                      'profiles':{k:{'budgets':v['populationTriangleBudgetByLod'],'coverage':[w['projectedCoverage']for w in v['fourSourceWindows']]}for k,v in reports.items()}}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'output/unreal/exterior-lawn-folded-20261001-r1-study')
    build(parser.parse_args().output.resolve())
