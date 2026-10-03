"""R29 source proposal only: four existing grove roots, one saved original mesh.

Decode all original positions for new fits/masks. Reuse pinned R24 attribute,
material and sampled native geometry proofs without claiming a new import.
No Unreal, download, project write, asset copy or native helper is invoked.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-original-tree-group-study-r29.py'
OUTPUT = ROOT/'output/unreal/exterior-original-tree-group-20261002-r29-proposal'
GROUP = 'EX_regional_1_4_canopy_fullness_broadleaf_r1_c_125000'
IDS = ['village_nearest_grove_3', 'village_nearest_grove_11', 'village_nearest_grove_27', 'village_nearest_grove_30']
SOURCES = {
    'originalSourcePlan': ('output/unreal/exterior-original-tree-20261002-r24-study/original-tree-source-plan.json', 'c45ff265adc98c394a58b69167066f3445f53800d4c6d9aa7fdb7d0cc1eb1ba6'),
    'originalDecoderProof': ('output/unreal/exterior-original-tree-20261002-r24-study/original-geometry-decoder-proof.json', 'f32f2459b115b80995a9d9c12282b4ad1855824f0311c77d1e52897ccd9f3cd1'),
    'tangentSupplement': ('output/unreal/exterior-original-tree-20261002-r24-tangent-r2-study/original-tree-tangent-supplement-r2.json', '0e24b32ffc0f65d5888bb33c1410b0f42769e831e53523559bb884f1aeec0025'),
    'originalSourceProducer': ('scripts/unreal/exterior-original-tree-study.py', '0240c7ff60b8ae9a009a642510bd68327aa0d3ea07a06f7b07ef954b1f54fa6e'),
    'fullnessPlan': ('output/unreal/exterior-canopy-fullness-20261001-r1-study/canopy-plan.json', '9b6dc59420986b5d56b39ed68ea092b7e11c11e3b82f8f0866b47d515a834e77'),
    'ecology': ('output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json', '27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576'),
    'managedLawn': ('output/unreal/exterior-lawn-photo-integration-20261001-r1/lawn-natural-plan.json', '5226c3d437decb065d4b792be16a7f8182f8c03a583bfb06cc0384bcd7bb3621'),
    'polygonHelper': ('scripts/unreal/exterior-grove-substrate-native.py', 'c27e3b935d4486e6150e262a8309223e9f72e0ef6abb9f648af5c897283f692e'),
    'savedOriginalTreeDonor': ('output/unreal/exterior-20261002-r24b/original-tree-native-report-r2.json', '869ed396ed7946cb0ea562d3f2da77f8dbd9f3d65777250b9686171697aa10f1'),
    'actualCleanReference': ('output/unreal/exterior-20261002-r27a/realism-clean-integration-native-report.json', '5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498'),
}


def require(value, message):
    if not value: raise ValueError(message)


def read(path): return json.loads(Path(path).read_text())
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): h.update(block)
    return h.hexdigest()
def pin(path):
    p = Path(path).resolve(); return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def check_pin(row):
    p = Path(row['path']); require(sha(p) == row['sha256'] and p.stat().st_size == row['bytes'], 'Pinned input changed: '+str(p)); return p
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def write(path, value):
    with Path(path).open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


def actual_process(report, stem, inputs, role):
    folder = Path(report['output']); terminal_path = folder/(stem+'-process.json'); terminal = read(terminal_path)
    raw = Path(terminal['processFile']); process = read(raw)
    require(terminal['reportSha256'] == sha(folder/(('original-tree-native-report-r2.json') if role == 'donor' else 'realism-clean-integration-native-report.json'))
            and terminal['processFileSha256'] == sha(raw) and process['code'] == 0 and process['signal'] is None
            and process['pid'] == report['nativeProcessId'] and terminal['sourcePinsUnchangedAfterNative'] is True,
            'Actual completed source reference process required')
    require(process['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and process['args'][0] == str(Path(report['project'])/'BreziTwin.uproject')
            and '-nullrhi' in process['args'] and '-run=pythonscript' in process['args']
            and '-script='+str(ROOT/report['owner']) in process['args'], 'Actual reference command scope differs')
    inputs[role+'Process'] = pin(terminal_path); inputs[role+'RawProcess'] = pin(raw)
    return {'actualPid': process['pid'], 'exitCode': 0, 'rawProcess': pin(raw), 'terminalReceipt': pin(terminal_path),
            'sourcePinsUnchangedAtHistoricalTerminal': len(terminal['sourcePinsBeforeNative']),
            'historicalTerminalPinsRehashedHere': False}


def frame(camera):
    eye = camera['eyeCm']; forward = [b-a for a,b in zip(eye, camera['targetCm'])]
    length = math.sqrt(sum(v*v for v in forward)); forward = [v/length for v in forward]
    right = [forward[1], -forward[0], 0.]; length = math.hypot(right[0], right[1]); right = [v/length for v in right]
    up = [right[1]*forward[2], -right[0]*forward[2], right[0]*forward[1]-right[1]*forward[0]]
    tangent = math.tan(math.radians(camera['horizontalFovDegrees']/2))
    return eye, forward, right, up, tangent


def camera_review(camera, bounds, row):
    eye, forward, right, up, tangent = frame(camera)
    def project(point):
        delta = [a-b for a,b in zip(point,eye)]
        depth = sum(a*b for a,b in zip(delta,forward)); horizontal = sum(a*b for a,b in zip(delta,right)); vertical = sum(a*b for a,b in zip(delta,up))
        return depth, horizontal, vertical
    corners = [project([bounds[x][0],bounds[y][1],bounds[z][2]]) for x in (0,1) for y in (0,1) for z in (0,1)]
    # A single negative half-space for the entire containing box proves it is outside.
    planes = {'front':lambda p:p[0], 'left':lambda p:p[0]*tangent+p[1], 'right':lambda p:p[0]*tangent-p[1],
              'bottom':lambda p:p[0]*tangent*9/16+p[2], 'top':lambda p:p[0]*tangent*9/16-p[2]}
    outside = [key for key,function in planes.items() if max(function(c) for c in corners) < 0]
    contained = all(min(function(c) for c in corners)>0 for function in planes.values())
    center = row['positionCm'][:]; center[2] += row['heightCm']/2
    depth,x,y = project(center)
    normalized = [x/(depth*tangent), y/(depth*tangent*9/16)] if depth>0 else None
    return {'sourceViewId':camera['id'],'sourceCamera':camera,'sourceOnly':True,'aspectRatioAssumed':[16,9],
            'nativeFovMeasured':False,'nativeCameraReadbackPerformed':False,'occlusionEvaluated':False,
            'rootCrownMidpointDepthCm':depth,'rootCrownMidpointNormalizedXY':normalized,
            'wholeDecodedCrownBoundingBoxInsideSourceFrustum':contained,'wholeDecodedCrownBoundingBoxOutsideSourceFrustum':bool(outside),
            'outsideFrustumPlanes':outside,'boundingBoxMayIntersectSourceFrustum':not outside,
            'actualRenderedVisiblePixelsEstablished':False,
            'scope':'Source camera and decoded box only. Intersection is a possible framing opportunity, not proof of visible alpha pixels or absence of occlusion.'}


def diagram(output, selections, all_roots, camera):
    # An explanatory source layout; no image-generation or simulated Unreal output.
    minx,miny,maxx,maxy = 4200.,17700.,9400.,23300.
    def xy(point): return (50+(point[0]-minx)*.14,820-(point[1]-miny)*.14)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="940" viewBox="0 0 1400 940">',
           '<rect width="1400" height="940" fill="#f4f2e9"/>',
           '<g font-family="sans-serif" fill="#243c31"><text x="34" y="30" font-size="22">R29 / SOURCE PROPOSAL — four existing roots, one original modeled tree</text>',
           '<text x="34" y="54" font-size="14">No native render, occlusion, surveyed elevation, local species fit or performance acceptance.</text></g>']
    for row in all_roots:
        x,y=xy(row['positionCm']); radius=row['radiusCm']*.14
        if -radius<x<800+radius and -radius<y<850+radius: out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius:.3f}" fill="none" stroke="#c8ccc0"/>')
    eye,forward,right,up,tangent=frame(camera); e=xy(eye); ends=[xy([eye[0]+forward[0]*5300+sign*right[0]*5300*tangent,eye[1]+forward[1]*5300+sign*right[1]*5300*tangent])for sign in(-1,1)]
    out.append(f'<path d="M{e[0]:.2f},{e[1]:.2f} L{ends[0][0]:.2f},{ends[0][1]:.2f} L{ends[1][0]:.2f},{ends[1][1]:.2f} Z" fill="#8ebade" fill-opacity=".10" stroke="#6589a0"/>')
    for index,item in enumerate(selections):
        row=item['originalSourceRow'];x,y=xy(row['positionCm']); old=row['radiusCm']*.14;new=item['fit']['circleRadiusCm']*.14
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{old:.3f}" fill="none" stroke="#a67553" stroke-width="2"/><circle cx="{x:.3f}" cy="{y:.3f}" r="{new:.3f}" fill="#40875b" fill-opacity=".20" stroke="#306d45" stroke-width="2"/><circle cx="{x:.3f}" cy="{y:.3f}" r="4" fill="#1a3427"/><text x="{x+6:.3f}" y="{y:.3f}" font-family="sans-serif" font-size="15">{row["id"].split("_")[-1]}</text>')
        line=120+index*146; canopy=item['sourceCameraReviews']['exterior-canopy-close']; frustum='inside'if canopy['wholeDecodedCrownBoundingBoxInsideSourceFrustum']else('outside'if canopy['wholeDecodedCrownBoundingBoxOutsideSourceFrustum']else'edge / partial possible')
        out.append(f'<g font-family="sans-serif" fill="#243c31"><text x="850" y="{line}" font-size="20">Root {row["id"].split("_")[-1]}</text><text x="850" y="{line+25}">Original height {row["heightCm"]/100:.2f} m / yaw {row["yawDeg"]:.1f}°</text><text x="850" y="{line+49}">Radius {item["fit"]["circleRadiusCm"]/100:.2f} m within {row["radiusCm"]/100:.2f} m envelope</text><text x="850" y="{line+73}">Canopy camera: {frustum}</text><text x="850" y="{line+97}">Parcels camera: complete crown outside</text></g>')
    out.extend(['<g font-family="sans-serif" fill="#243c31" font-size="14"><text x="34" y="891">Brown: original inferred crown envelopes. Green: full decoded containing circles. Grey: unchanged source grove roots.</text>',
                '<text x="34" y="914">Blue: horizontal source camera framing. 74 other grove roots unchanged. Reuse17 saved packages; 4 × 2,062,487 input triangles.</text></g></svg>'])
    (output/'source-four-root-layout.svg').write_text('\n'.join(out)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUTPUT);output=parser.parse_args().output.resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(),'Fresh isolated R29 proposal required')
    inputs={};data={}
    for key,(relative,expected)in SOURCES.items():
        p=ROOT/relative;require(sha(p)==expected,'Frozen source differs: '+key);inputs[key]=pin(p)
        if p.suffix=='.json': data[key]=read(p)
    old=data['originalSourcePlan'];donor=data['savedOriginalTreeDonor'];clean=data['actualCleanReference']
    require(clean['status']=='verified-saved-four-donor-clean-exterior-realism-integration'and clean['savedMapUnloadedReloaded']is True,'Actual saved clean reference required')
    require(donor['status']=='verified-saved-single-original-tree-overlay'and donor['savedMapUnloadedReloaded']is True,'Actual saved original tree donor required')
    processes={'savedOriginalTree':actual_process(donor,'original-tree-native-r2',inputs,'donor'),'savedCleanReference':actual_process(clean,'realism-clean-integration-native',inputs,'clean')}
    for key,row in [('sourceGLTF',data['originalDecoderProof']['sourceGLTF']),('sourceBinary',data['originalDecoderProof']['sourceBinary']),
                    ('cleanSavedActors',clean['savedActorWitness']),('originalTreeSavedActors',donor['savedActorWitness']),('cleanViews',clean['diagnosticViewpoints']),('donorContentInventory',donor['afterContentInventory'])]:
        check_pin(row);inputs[key]=row
    document=read(inputs['sourceGLTF']['path']);binary=Path(inputs['sourceBinary']['path']).read_bytes();source=module('r29_readonly_original_decoder',inputs['originalSourceProducer']['path'])
    proof=data['originalDecoderProof'];require(proof['sourceOnly']is True and proof['sourceVertices']==1777278 and proof['sourceTriangles']==2062487 and proof['sourceLODCount']==1,'Exact full original source proof required')
    full=data['fullnessPlan'];rows=[r for r in full['canopyPlacements'] if f'EX_regional_{math.floor(r["positionCm"][0]/5000)}_{math.floor(r["positionCm"][1]/5000)}_{r["meshId"]}_{r["cullEndCm"]}'==GROUP]
    require([r['id']for r in rows]==IDS and len(full['canopyPlacements'])==78,'Exact whole four-member original group required')
    witness=read(inputs['cleanSavedActors']['path']);group=[(k,v)for k,v in witness.items()if v['label']==GROUP]
    require(len(group)==1 and len(group[0][1]['components'])==1 and group[0][1]['components'][0]['instanceCount']==4,'Actual clean group is not exactly four original members')
    native_geometry=donor['nativeSourceGeometry'];require(native_geometry['sourceTriangles']==2062487 and native_geometry['sampledNativeTriangles']==4096 and native_geometry['unsampledNativeTriangles']==2058391
            and native_geometry['nativeSampledPositionUV0UV1SectionOrderVerified']is True and native_geometry['nativeFullPositionUV0UV1CornerReadbackPerformed']is False,'Saved donor sampled/full-source proof distinction changed')
    require(full['activeDesign']==old['activeDesign']==clean['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'} and full['housePlacement']==old['housePlacement']
            and full['housePlacement']['streetSetbackMm']==full['housePlacement']['eastSetbackMm']==3000,'C/B/B3000 basis changed')
    minimum=math.inf;maximum=-math.inf;source_radius=0.;vertices=0;position_hash=hashlib.sha256();bounds=[]
    for primitive,part in zip(document['meshes'][0]['primitives'],proof['parts']):
        require(primitive['attributes']['POSITION']==part['attributes']['POSITION']['accessor'],'Original position mapping changed');a,positions=source.accessor(document,binary,primitive['attributes']['POSITION']);require(a['count']==part['vertices'],'Original position census differs')
        lo=[math.inf]*3;hi=[-math.inf]*3;h=hashlib.sha256()
        for point in positions:
            require(all(math.isfinite(v)for v in point),'Original nonfinite position');raw=struct.pack('<fff',*point);position_hash.update(raw);h.update(raw)
            minimum=min(minimum,point[1]);maximum=max(maximum,point[1]);source_radius=max(source_radius,math.hypot(point[0],point[2]));vertices+=1
            for i in range(3):lo[i]=min(lo[i],point[i]);hi[i]=max(hi[i],point[i])
        require(h.hexdigest()==part['attributes']['POSITION']['orderedAttributeBytesSha256']and [lo,hi]==part['boundsM'],'Decoded original ordered positions/bounds differ from frozen source proof');bounds.append([lo,hi])
    require(vertices==1777278 and len(bounds)==3,'Exact full source position census required')
    poly=module('r29_frozen_polygons',inputs['polygonHelper']['path']);masks={k:poly._PolygonIndex(v)for k,v in data['ecology']['exclusionDomainsCm'].items()}
    rings=data['managedLawn']['managedLawnKeepPolygonsCm'];masks['managedLawn']=poly._PolygonIndex({'type':'MultiPolygon','coordinates':[[r+[r[0]]if r[0]!=r[-1]else r]for r in rings]})
    require(set(masks)=={'protected','subject','roads','buildings','cultivatedGround','managedLawn'},'All six authentic exclusions required')
    ring=data['ecology']['sourceRegion']['polygonCm'];domain=poly._PolygonIndex({'type':'Polygon','coordinates':[ring+[ring[0]]]})
    cameras={v['id']:v for v in read(inputs['cleanViews']['path'])['views']if v['id']in('exterior-canopy-close','exterior-parcels')};require(len(cameras)==2,'Exact saved clean source cameras required')
    selections=[];states=[]
    for row in rows:
        scale=row['heightCm']/(100*(maximum-minimum));angle=math.radians(row['yawDeg']);states.append({'row':row,'scale':scale,'c':math.cos(angle),'s':math.sin(angle),'lo':[math.inf]*3,'hi':[-math.inf]*3,'radius':0.,'hash':hashlib.sha256(),'vertices':0})
    for primitive in document['meshes'][0]['primitives']:
        _,positions=source.accessor(document,binary,primitive['attributes']['POSITION'])
        for point in positions:
            for state in states:
                scale=state['scale'];x,y=point[0]*scale*100,point[2]*scale*100;dx=state['c']*x-state['s']*y;dy=state['s']*x+state['c']*y;row=state['row'];root=row['positionCm'];world=[root[0]+dx,root[1]+dy,root[2]+(point[1]-minimum)*scale*100]
                state['hash'].update(struct.pack('<ddd',*world));state['radius']=max(state['radius'],math.hypot(dx,dy));state['vertices']+=1
                for i in range(3):state['lo'][i]=min(state['lo'][i],world[i]);state['hi'][i]=max(state['hi'][i],world[i])
    for index,state in enumerate(states):
        row=state['row'];root=row['positionCm'];radius=state['radius'];require(state['vertices']==1777278 and radius<row['radiusCm'],'Full original geometry exceeds assigned crown envelope')
        require(abs(state['hi'][2]-state['lo'][2]-row['heightCm'])<1e-9 and state['lo'][2]==root[2],'Source whole height/root ground fit differs')
        exclusions={}
        for key,mask in masks.items():
            distance=min(poly.base._distance(root[:2],a,b)for a,b in mask.edges);require(not mask.contains(root[:2])and distance>radius+75,'Full crown intersects exclusion '+key)
            exclusions[key]={'rootOutsideSourcePolygon':True,'sourceBoundaryDistanceCm':distance,'circleRadiusCm':radius,'wholeTriangleClearanceLowerBoundCm':distance-radius,'requiredClearanceCm':75.,'fullCirclePass':True}
        distance=min(poly.base._distance(root[:2],a,b)for a,b in domain.edges);require(domain.contains(root[:2])and distance>radius,'Full tree leaves original grove')
        world_bounds=[state['lo'],state['hi']]
        selections.append({'rootId':row['id'],'originalGroupIndex':index,'originalSourceRow':deepcopy(row),
            'fit':{'sourceYupMetersToNativeCm':'[100*x,100*z,100*y]','uniformScale':state['scale'],'sourceBottomYmeters':minimum,'nativeInstanceOriginOffsetCm':[0.,0.,-minimum*state['scale']*100],
                   'sourceBasalRootCm':root,'proposedNativeInstanceOriginCm':[root[0],root[1],root[2]-minimum*state['scale']*100],'originalBasalRootAndYawPreserved':True,'instanceOriginZNumericallyEqualsOriginalRootZ':False,
                   'heightCm':state['hi'][2]-state['lo'][2],'circleRadiusCm':radius,'assignedOldRadiusCm':row['radiusCm'],'remainingEnvelopeRadiusCm':row['radiusCm']-radius,'worldBoundsCm':world_bounds,
                   'allTransformedSourceVertices':state['vertices'],'orderedBinary64WorldPositionsSha256':state['hash'].hexdigest(),'independentXYStretchApplied':False,'groundElevationSurveyed':False,'libmAnnotationExactCrossRuntimeGate':False},
            'sourceMasks':{'wholeCircleInsideOriginalGrove':True,'groveBoundaryDistanceCm':distance,'wholeTriangleGroveClearanceLowerBoundCm':distance-radius,'exclusions':exclusions,
                           'method':'All original positions decoded; convex horizontal containing circle proves every original triangle/edge inside grove and outside all six authentic source exclusions.'},
            'sourceCameraReviews':{key:camera_review(camera,world_bounds,row)for key,camera in cameras.items()}})
    packages=read(inputs['donorContentInventory']['path']);proposal_packages=[{'relativeContentPath':p,**packages[p]}for p in donor['newContentPackages']]
    require(len(proposal_packages)==17 and all(p['relativeContentPath'].startswith('Brezi/OriginalTree20261002R24/')for p in proposal_packages),'Exact saved donor17 packages required')
    current=group[0][1]['components'][0];original_positions=[r['positionCm']for r in rows];original_matrices=donor['originalRootRetirement']['storedMatricesBefore']
    require([m[3][:3]for m in original_matrices]==original_positions,'Saved original tree donor roots do not match clean source group')
    output.mkdir();snapshot=output/Path(OWNER).name;snapshot.write_bytes((ROOT/OWNER).read_bytes());inputs['producer']=pin(ROOT/OWNER);inputs['producerSnapshot']=pin(snapshot)
    write(output/'four-root-fit-and-mask-review.json',selections);write(output/'original-clean-group-witness.json',{'actor':group[0][0],'witness':group[0][1],'actualCleanReport':inputs['actualCleanReference'],'historicalNativeGroupMatched':True,'newNativeGroupMeasured':False})
    write(output/'saved-tree-package-proposal.json',{'savedDonor':inputs['savedOriginalTreeDonor'],'inventory':inputs['donorContentInventory'],'packages':proposal_packages,'filesCopiedHere':0,'actualDonorNativeGeometryProof':native_geometry,'nativeNewPlacementProofPerformed':False})
    diagram(output,selections,full['canopyPlacements'],cameras['exterior-canopy-close'])
    plan={'schema':'brezi-original-tree-four-existing-grove-roots-source-proposal-r29','owner':OWNER,'status':'source-only-four-original-tree-root-proposal-review-required',
          'generatedAt':datetime.now(timezone.utc).isoformat(),'inputFiles':inputs,'sourceOnly':True,'activeDesign':full['activeDesign'],'housePlacement':full['housePlacement'],
          'sourceSceneSha256':full['sourceSceneSha256'],'sourceObjSha256':full['sourceObjSha256'],'regionId':'village_nearest_grove','selectedGroupId':GROUP,'selectedRootIds':IDS,
          'rootSelection':pin(output/'four-root-fit-and-mask-review.json'),'originalGroupWitness':pin(output/'original-clean-group-witness.json'),'savedPackageProposal':pin(output/'saved-tree-package-proposal.json'),'sourceDiagram':pin(output/'source-four-root-layout.svg'),
          'actualHistoricalProcesses':processes,'originalSourcePositionsDecoded':vertices,'sourcePositionBytesSha256':position_hash.hexdigest(),'sourceYupBoundsMeters':bounds,'newWorldSourceVerticesChecked':vertices*4,
          'sourceGeometryAndMaterialFilesMutated':0,'sourceNormalUVIndexProofReusedFrom':inputs['originalDecoderProof'],'allOtherGroveSourceRowsPreserved':74,'allOtherGroveRowsOrderedSha256':digest([r for r in full['canopyPlacements']if r['id']not in IDS]),
          'proposal':{'operation':'Retire all4 members of the one original group; leave its actor/component/assets in place with zero members; add one uniquely owned4-member HISM using the exact saved original R24 mesh/materials.',
                      'reason':'Whole-group replacement avoids rebuilding/reordering retained members or reconstructing unavailable additional seed ranges. It does not certify unobserved seed ranges.',
                      'newRootCount':0,'retiredOldMembers':4,'newOriginalMeshMembers':4,'oldGroupRemainingMembers':0,'newOwnedHismGroups':1,'newOwnedActors':1,'allOtherActorChanges':0,
                      'collision':'NoCollision','navigation':False,'oldCullStartEndCm':current['instanceCullCm'],'requestedNewCullStartEndCm':current['instanceCullCm'],
                      'oldQualityDetailDensityScaling':group[0][1]['detailDensityScaling'],'requestedQualityDetailDensityScaling':False,
                      'rootXYZAndQuaternionNativeWrappedCopyRequiredLater':True,'originalMatricesReconstructedHere':False,'AdditionalRandomSeedsReadbackAvailable':False,
                      'architectureHardscapeLightingAndSourceCameraChanges':0,'nativeNamespaceReuse':donor['newMesh'],'newMaterialEdits':0},
          'budget':{'treeInputTrianglesPerInstance':2062487,'treeInputTrianglesAcross4Instances':8249948,'sourceVerticesPerInstance':1777278,'uniqueMeshAssetsReused':1,'sourceLods':1,'materialSections':3,
                    'savedNaniteResourceInputTriangles':donor['naniteResourceReadback']['nativeResourceInputTriangles'],'savedFallbackTrianglesPerInstance':native_geometry['renderFallbackTriangles'],
                    'savedPackagesToCopyLater':17,'newGeometryGenerated':0,'actualNewRuntimeFrameCostMeasured':False,
                    'limit':'Four instances reuse one2Mtriangle input mesh; source input census is not runtime drawn triangles. Leaf alpha overdraw remains expensive; no selected-tree pass attribution or performance acceptance.'},
          'pendingNativeBase':{'preferred':'Future actual saved R28 purposefully surfaced yards on clean R27, only after root reviews this source proposal.','selectedNativeReport':None,'selectionComplete':False,'actualSavedR27Reference':inputs['actualCleanReference'],'actualSavedR28ExistsOrValidatedHere':False},
          'appearanceLimits':['Two central crowns fit the canopy source camera; two eastern crowns intersect its edge. The parcels source camera excludes the whole selected group.',
                              'The source model is asymmetric but reused four times. Original yaw/height variation reduces identical orientation; no unique-model diversity is claimed.',
                              'Original Burkea africana model is an artistic choice; local species/ecological fit and surveyed elevation are unverified.',
                              'Native4096triangle R24 sampled proof is historical. Remaining2,058,391 native triangles, native normal/tangent readback and selected-tree Nanite pass attribution are unverified.'],
          'nativeApplied':False,'nativeNewPlacementProofPerformed':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'ecologicalFitVerified':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    write(output/'original-tree-group-source-proposal.json',plan)
    for key,row in inputs.items():check_pin(row)
    receipt={'schema':plan['schema'],'owner':OWNER,'status':'verified-source-only-four-root-original-tree-fit-masks-proposal-native-pending','plan':pin(output/'original-tree-group-source-proposal.json'),
             'sourceInputsBeforeAfterUnchanged':True,'inputPinCount':len(inputs),'CBB3000Preserved':True,'all4FullSourceVertexEnvelopeAndSixMaskProofs':True,'transformedSourceVerticesChecked':vertices*4,
             'all4CrownBoundingBoxesOutsideParcelsSourceView':all(s['sourceCameraReviews']['exterior-parcels']['wholeDecodedCrownBoundingBoxOutsideSourceFrustum']for s in selections),
             'actualNativeR29Executed':False,'nativeBaseSelectionComplete':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
    write(output/'source-validation-receipt.json',receipt)
    print(json.dumps({'plan':pin(output/'original-tree-group-source-proposal.json'),'receipt':pin(output/'source-validation-receipt.json'),'roots':[{k:s[k]for k in('rootId','fit')}for s in selections],'nativeExecuted':False},indent=2))


if __name__=='__main__':main()
