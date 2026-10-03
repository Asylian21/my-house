"""R24 single original provider tree: source only, no Unreal or old writes.

All published binary attributes remain byte exact. The NEW glTF references the
old immutable buffers/images and adds one common root shift and uniform node
scale. The proposed native base must later be the actually saved R22 composition.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-original-tree-study.py'
OUTPUT = ROOT/'output/unreal/exterior-original-tree-20261002-r24-study'
REFERENCE = ROOT/'output/unreal/exterior-ph-tree-reference-20261001-r1'
TARGET = 'village_nearest_grove_3'
GROUP = 'EX_regional_1_4_canopy_fullness_broadleaf_r1_c_125000'
PREFIX = '/Game/Brezi/OriginalTree20261002R24'
SOURCES = {
    'providerReceipt': ('output/unreal/exterior-ph-tree-reference-20261001-r1/source-download-receipt.json', None),
    'context': ('output/unreal/exterior-context-20260927-r8/context-plan.json', '4b0b72a5f39d5bec3915846abb159147a4cf73b65cbf920884ffe7dd762a4176'),
    'fullnessPlan': ('output/unreal/exterior-canopy-fullness-20261001-r1-study/canopy-plan.json', '9b6dc59420986b5d56b39ed68ea092b7e11c11e3b82f8f0866b47d515a834e77'),
    'ecology': ('output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json', '27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576'),
    'managedLawn': ('output/unreal/exterior-lawn-photo-integration-20261001-r1/lawn-natural-plan.json', '5226c3d437decb065d4b792be16a7f8182f8c03a583bfb06cc0384bcd7bb3621'),
    'nativeR16': ('output/unreal/exterior-20261001-r16a/exterior-import-report.json', '1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'),
    'nativeBeforeActors': ('output/unreal/exterior-20261002-r21b/foreground-native-checkpoint/before-actor-witness.json', 'a61d435bb064d984567c8757816d0ed3d5d6747f9101bcc2861c669711d3152b'),
    'views': ('output/unreal/exterior-20261001-r16a/Project/BreziTwin/Content/Data/viewpoints.json', '06127e9b9d8d4c3798e4a08601b909e81d992fc2b2f8ca1f761dd7df36d7bff7'),
    'polygonHelper': ('scripts/unreal/exterior-grove-substrate-native.py', 'c27e3b935d4486e6150e262a8309223e9f72e0ef6abb9f648af5c897283f692e'),
}


def require(value, message):
    if not value: raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def pin(path): return dict(path=str(Path(path).resolve()), sha256=sha(path), bytes=Path(path).stat().st_size)
def write(path, value):
    with Path(path).open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def accessor(document, binary, index):
    a = document['accessors'][index]; v = document['bufferViews'][a['bufferView']]
    require(not a.get('sparse') and v.get('buffer', 0) == 0 and isinstance(a['count'], int) and a['count'] > 0, 'Unsupported original accessor')
    n = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]
    size, fmt = {5126:(4, 'f'), 5125:(4, 'I'), 5123:(2, 'H')}[a['componentType']]
    width = n*size; start = v.get('byteOffset', 0)+a.get('byteOffset', 0); stride = v.get('byteStride', width)
    require(stride >= width and start >= 0 and start+(a['count']-1)*stride+width <= len(binary), 'Original accessor extent invalid')
    return a, (struct.unpack_from('<'+fmt*n, binary, start+i*stride) for i in range(a['count']))


def attribute_proof(document, binary, index):
    a, rows = accessor(document, binary, index); packed = hashlib.sha256(); maximum = -math.inf; minimum = math.inf
    n = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]; fmt = {5126:'f', 5125:'I', 5123:'H'}[a['componentType']]
    for values in rows:
        require(all(math.isfinite(v) for v in values), 'Nonfinite original attribute')
        packed.update(struct.pack('<'+fmt*n, *values)); maximum = max(maximum, *values); minimum = min(minimum, *values)
    return dict(accessor=index, count=a['count'], type=a['type'], componentType=a['componentType'], orderedAttributeBytesSha256=packed.hexdigest(), scalarMinimum=minimum, scalarMaximum=maximum)


def validate_document(candidate, original, output, scale, bottom):
    expected = deepcopy(original)
    expected['nodes'][0]['translation'] = [0., -bottom*scale, 0.]
    expected['nodes'][0]['scale'] = [scale]*3
    expected['buffers'][0]['uri'] = os.path.relpath(REFERENCE/'tree_small_02'/original['buffers'][0]['uri'], output)
    for row, old in zip(expected['images'], original['images']): row['uri'] = os.path.relpath(REFERENCE/'tree_small_02'/old['uri'], output)
    require(candidate == expected, 'Candidate changed published attributes, indices, KHR material mapping or node scope')
    require(len(original['nodes']) == len(original['meshes']) == 1 and original['nodes'] == [{'mesh':0, 'name':'tree_small_02_LOD0'}], 'Only the exact original single provider LOD is allowed')
    require(original['extensionsRequired'] == original['extensionsUsed'] == ['KHR_texture_transform'], 'Unexpected provider extension')


def source_materials(document, published):
    lookup = {Path(row['path']).name:row for row in published}; materials = []
    alpha = lookup['tree_small_02_leaves_alpha_2k.png']
    for i, row in enumerate(document['materials']):
        pbr = row['pbrMetallicRoughness']; basis = pbr['baseColorTexture']; normal = row['normalTexture']; arm = pbr['metallicRoughnessTexture']
        require(row['doubleSided'] is True and pbr['metallicFactor'] == 0 and not row.get('occlusionTexture'), 'Original tree material defaults differ')
        coords = [t.get('texCoord', 0) for t in (basis, normal, arm)]
        transforms = [t.get('extensions', {}).get('KHR_texture_transform', {'offset':[0.,0.], 'scale':[1.,1.]}) for t in (basis, normal, arm)]
        require(len(set(coords)) == 1 and transforms[0] == transforms[1] == transforms[2], 'Original map UV sets/transform differ')
        maps = {}
        for role, texture in [('albedo', basis), ('normalGL', normal), ('ARM', arm)]:
            image = document['images'][document['textures'][texture['index']]['source']]
            maps[role] = lookup[Path(image['uri']).name]
        leaves = i == 1
        require(row['name'] == ('tree_small_02_branches','tree_small_02_leaves','tree_small_02_trunk')[i], 'Original three section/material order differs')
        materials.append(dict(id='ph_original_'+row['name']+'_r24', providerMaterial=row, sourceMaps=maps,
            uvSet=coords[0], KHRTextureTransform=transforms[0], alphaSource=alpha if leaves else None,
            nativeProposal=dict(blendMode='MASKED' if leaves else 'OPAQUE', twoSided=True,
                shadingModel='TwoSidedFoliage' if leaves else 'DefaultLit', baseColorFactor=[1.,1.,1.,1.],
                metallicFactor=0., roughnessFactor=1., normalScale=1., specular=.5,
                opacityMask='Original published leaf alpha PNG.R' if leaves else None, opacityMaskClipValue=.5 if leaves else None,
                subsurfaceScale=.08 if leaves else None, albedoSRGB=True, normalGLGreenFlip=True, ARMLinear=True,
                roughnessChannel='G', metallicChannel='B * original metallicFactor0', occlusionRoot=None,
                normalTangentBasis='Must use selected normalTexture UV set; branch UV1 differs from UV0. Native UV1 derivative basis or explicitly derived UV1 mesh tangents required; not implemented by this source study.',
                worldPositionOffset=None, pixelSourceEdits=False, nativeGraphBuilt=False),
            nativeShaderMatchesOriginalGlTFExactly=False,
            conversionLimit='Leaf source alphaMode BLEND is explicitly proposed as UE MASKED for alpha leaves/Nanite. Source JPG has no alpha; the unchanged published PNG sidecar must supply it.' if leaves else 'UE specular/basis realization is proposed; original graph pixels/UV mapping stay pinned.'))
    return materials


def plot(output, target, source_samples, proof, other_roots, camera):
    # Diagram, not a raster edit or a rendered/native appearance claim.
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (1440,900), '#f1f0e6'); draw = ImageDraw.Draw(image)
    draw.text((35,25), 'SOURCE ONLY / R24: ONE published original tree, unchanged geometry; native appearance pending.', fill='#23382d')
    def plan(p): return (360+(p[0]-target['positionCm'][0])*.43, 430-(p[1]-target['positionCm'][1])*.43)
    for row in other_roots:
        p = plan(row['positionCm']); radius = row['radiusCm']*.43
        draw.ellipse((p[0]-radius,p[1]-radius,p[0]+radius,p[1]+radius), outline='#bdc6b6')
    center = plan(target['positionCm']); old = target['radiusCm']*.43
    draw.ellipse((center[0]-old,center[1]-old,center[0]+old,center[1]+old), outline='#8d6959', width=3)
    for p in source_samples:
        x,y = plan(p); draw.point((int(x),int(y)), fill='#376847')
    draw.ellipse((center[0]-5,center[1]-5,center[0]+5,center[1]+5), fill='#192a25')
    draw.text((55,790), 'Plan: brown = previous inferred crown envelope; green = sampled full-source vertices.', fill='#253a2d')
    draw.text((55,812), 'All vertices/triangles are checked by the containing-circle mask proof; samples are diagram-only.', fill='#253a2d')
    yaw=math.radians(target['yawDeg']);c,s=math.cos(yaw),math.sin(yaw)
    for p in source_samples:
        dx,dy=p[0]-target['positionCm'][0],p[1]-target['positionCm'][1]; localx=c*dx+s*dy
        x=1060+localx*.52;y=735-(p[2]-target['positionCm'][2])*.72
        draw.point((int(x),int(y)),fill='#385b3a')
    draw.line((790,735,1335,735),fill='#c7aa87',width=2)
    draw.text((800,790), 'Original modeled tree / uniform height fit / no procedural crown fill.', fill='#253a2d')
    draw.text((800,812), 'No texture/alpha raster rendering shown. Burkea africana ecological fit unverified.', fill='#253a2d')
    image.save(output/'source-one-tree-layout.png')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output', type=Path, default=OUTPUT);args=parser.parse_args();output=args.output.resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Fresh isolated R24 output required')
    inputs={};data={}
    for key,(relative,expected) in SOURCES.items():
        p=ROOT/relative;require(expected is None or sha(p)==expected, 'Frozen source differs: '+key);inputs[key]=pin(p)
        if p.suffix=='.json': data[key]=read(p)
    receipt=data['providerReceipt'];require(receipt['status']=='VERIFIED_ORIGINAL_3D_TREE_REFERENCE_DOWNLOAD_NATIVE_PENDING' and receipt['nativeImported'] is False and receipt['ecologicalFitVerified'] is False, 'Exact original source reference state required')
    require(len(receipt['files'])==12 and receipt['sourceMeshes']==[{'name':'BezierCurve.002','primitives':3,'triangles':2062487}], 'Exact original12files/2M single source model required')
    for row in receipt['files']:
        p=Path(row['path']);b=p.read_bytes();require(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'] and hashlib.md5(b).hexdigest()==row['publishedMd5'], 'Published original file identity differs')
        inputs['provider:'+p.name]=pin(p)
    original=read(REFERENCE/'tree_small_02/tree_small_02_2k.gltf');binary=(REFERENCE/'tree_small_02/tree_small_02.bin').read_bytes()
    require(len(binary)==original['buffers'][0]['byteLength'] and len(original['meshes'][0]['primitives'])==3, 'Original primitive/buffer count differs')
    context=data['context'];full=data['fullnessPlan'];require(context['activeDesign']==full['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'} and context['housePlacement']==full['housePlacement'] and full['housePlacement']['streetSetbackMm']==full['housePlacement']['eastSetbackMm']==3000, 'C/B/B3000 source changed')
    target=next(row for row in full['canopyPlacements'] if row['id']==TARGET)
    group=[row for row in full['canopyPlacements'] if f'EX_regional_{math.floor(row["positionCm"][0]/5000)}_{math.floor(row["positionCm"][1]/5000)}_{row["meshId"]}_{row["cullEndCm"]}'==GROUP]
    require([r['id'] for r in group]==[TARGET,'village_nearest_grove_11','village_nearest_grove_27','village_nearest_grove_30'], 'Exact original4 tree group differs')
    actors=[(k,r)for k,r in data['nativeBeforeActors'].items() if r['label']==GROUP]
    require(len(actors)==1 and actors[0][1]['components'][0]['instanceCount']==4, 'Actual original native group witness differs')
    parts=[];minimum=math.inf;maximum=-math.inf;radius=0.;vertex_count=0
    for primitive in original['meshes'][0]['primitives']:
        require(primitive.get('mode',4)==4 and set(primitive['attributes'])=={'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1'}, 'Original attributes changed/morph/skin refused')
        proof={k:attribute_proof(original,binary,i)for k,i in primitive['attributes'].items()};ind=attribute_proof(original,binary,primitive['indices']);count=proof['POSITION']['count']
        require(all(v['count']==count for v in proof.values()) and ind['count']%3==0 and 0<=ind['scalarMinimum']<=ind['scalarMaximum']<count, 'Original attribute/index pairing invalid')
        _,positions=accessor(original,binary,primitive['attributes']['POSITION']);lo=[math.inf]*3;hi=[-math.inf]*3;part_radius=0.
        for point in positions:
            minimum=min(minimum,point[1]);maximum=max(maximum,point[1]);part_radius=max(part_radius,math.hypot(point[0],point[2]))
            lo=[min(lo[i],point[i])for i in range(3)];hi=[max(hi[i],point[i])for i in range(3)]
        radius=max(radius,part_radius);vertex_count+=count
        parts.append(dict(material=original['materials'][primitive['material']]['name'],materialIndex=primitive['material'],vertices=count,triangles=ind['count']//3,attributes=proof,indices=ind,boundsM=[lo,hi],rootCenteredRadiusM=part_radius))
    require(sum(p['triangles']for p in parts)==2062487 and vertex_count==1777278, 'Full original decoded count differs')
    height=maximum-minimum;scale=target['heightCm']/100/height
    candidate=deepcopy(original);candidate['nodes'][0].update(translation=[0.,-minimum*scale,0.],scale=[scale]*3)
    candidate['buffers'][0]['uri']=os.path.relpath(REFERENCE/'tree_small_02'/original['buffers'][0]['uri'],output)
    for row,old in zip(candidate['images'],original['images']):row['uri']=os.path.relpath(REFERENCE/'tree_small_02'/old['uri'],output)
    validate_document(candidate,original,output,scale,minimum)
    spec=importlib.util.spec_from_file_location('r24_frozen_source_polygons',ROOT/SOURCES['polygonHelper'][0]);poly=importlib.util.module_from_spec(spec);spec.loader.exec_module(poly)
    masks={k:poly._PolygonIndex(v)for k,v in data['ecology']['exclusionDomainsCm'].items()};rings=data['managedLawn']['managedLawnKeepPolygonsCm']
    masks['managedLawn']=poly._PolygonIndex({'type':'MultiPolygon','coordinates':[[r+[r[0]]if r[0]!=r[-1]else r]for r in rings]})
    ring=data['ecology']['sourceRegion']['polygonCm'];domain=poly._PolygonIndex({'type':'Polygon','coordinates':[ring+[ring[0]]]})
    require(set(masks)=={'protected','subject','roads','buildings','cultivatedGround','managedLawn'}, 'Full original exclusion inventory required')
    world_hash=hashlib.sha256();world_min=[math.inf]*3;world_max=[-math.inf]*3;actual_radius=0.;samples=[];count=0
    angle=math.radians(target['yawDeg']);c,s=math.cos(angle),math.sin(angle);root=target['positionCm']
    for primitive in original['meshes'][0]['primitives']:
        _,positions=accessor(original,binary,primitive['attributes']['POSITION'])
        for point in positions:
            x,y=point[0]*scale*100,point[2]*scale*100;dx,dy=c*x-s*y,s*x+c*y;z=(point[1]-minimum)*scale*100
            world=[root[0]+dx,root[1]+dy,root[2]+z];world_hash.update(struct.pack('<ddd',*world));actual_radius=max(actual_radius,math.hypot(dx,dy))
            world_min=[min(world_min[i],world[i])for i in range(3)];world_max=[max(world_max[i],world[i])for i in range(3)]
            if count%256==0:samples.append(world)
            count+=1
    require(count==vertex_count and actual_radius<target['radiusCm'] and abs(world_max[2]-world_min[2]-target['heightCm'])<1e-9, 'Uniform whole-tree morphology fit exceeds previous inferred envelope')
    mask_proofs={}
    for key,mask in masks.items():
        distance=min(poly.base._distance(root[:2],a,b)for a,b in mask.edges)
        require(not mask.contains(root[:2]) and distance>actual_radius+75., 'Complete transformed tree circle intersects source exclusion: '+key)
        mask_proofs[key]=dict(rootOutsideSourcePolygon=True,sourcePolygonBoundaryDistanceCm=distance,allVertexContainingCircleRadiusCm=actual_radius,completeTriangleClearanceLowerBoundCm=distance-actual_radius,minimumRequiredClearanceCm=75.,allVerticesAndTriangleEdgesProvenOutside=True)
    edge_distance=min(poly.base._distance(root[:2],a,b)for a,b in domain.edges)
    require(domain.contains(root[:2]) and edge_distance>actual_radius, 'Full original-tree geometry leaves original authored grove')
    require(not any('flare' in g['meshId']for g in data['ecology']['groups']), 'Unexpected old root flare needs separate proposal')
    old_component=actors[0][1]['components'][0]
    selection=dict(id=TARGET,originalSourceRow=target,originalNativeActor=actors[0][0],originalNativeActorWitness=actors[0][1],groupId=GROUP,originalGroupRootIds=[r['id']for r in group],retiredOriginalIndex=0,retainedSourceRootIds=[r['id']for r in group[1:]],retainedSourceRootRows=group[1:],originalNativeMembers=4,remainingNativeMembers=3,
        proposal='Rebuild only this4-member HISM minus selected index0 with original remaining native transforms/order. Preserve all original actor/component policies/assets. Add exactly one owned full-original-tree actor.',
        newActorProposal=dict(ownerTag='BreziOriginalTree20261002R24',positionCm=deepcopy(root),yawDeg=target['yawDeg'],actorScale=[1.,1.,1.],sourceNodeUniformScale=scale,sourceNodeTranslationM=[0.,-minimum*scale,0.],authoredHeightCm=target['heightCm'],collision='NoCollision',navigation=False,windWPO=False,castShadow=True),
        associatedOldFlareRoots=0,originalNativeRootTransformsCopiedLater=True,nativeApplied=False)
    material=source_materials(original,receipt['files'])
    masks_audit=dict(method='Decode every original/transformed vertex, derive its exact conservative horizontal containing circle, then prove this complete convex circle outside all6 authentic source exclusions and inside the original grove. This also bounds every original triangle edge/interior.',decodedTransformedVertices=count,triangles=2062487,originalOrderedSourceAttributesUnchanged=True,originalTriangleIndicesAndOrderUnchanged=True,originalNormalsPreserved=True,sourceTangentsPresent=False,normalTangentNativeReadbackAvailable=False,allOrderedWorldVertexBinary64Sha256=world_hash.hexdigest(),worldBoundsCm=[world_min,world_max],circleRadiusCm=actual_radius,previousInferredRadiusCm=target['radiusCm'],groveBoundaryDistanceCm=edge_distance,wholeTreeGroveBoundaryClearanceLowerBoundCm=edge_distance-actual_radius,exclusions=mask_proofs,ground='context_unresolved_flat_backdrop',originalRootZpreserved=True,measuredGroundElevation=False,libmAnnotationExactCrossRuntimeComparisonRequired=False)
    engine_paths=['Config/Mac/DataDrivenPlatformInfo.ini','Source/Runtime/Apple/MetalRHI/Private/MetalRHI.cpp','Source/Runtime/RenderCore/Private/RenderUtils.cpp','Source/Runtime/Engine/Private/Rendering/NaniteResources.cpp']
    engine=Path('/Users/Shared/Epic Games/UE_5.8/Engine');nanite=dict(platformSourceEligibility=True,materialProposalEligibility='Opaque trunk/branches and explicitly proposed Masked leaf material accepted by installed IsSupportedBlendMode; preserve original input geometry and UV attributes.',evidence={p:pin(engine/p)for p in engine_paths},actualNewNaniteBuild=False,actualNewNaniteResourcesVerified=False,actualNaniteRenderPassVerified=False,performanceAccepted=False,sourceLODCount=1,sourceTriangleBudget=2062487,sourceMaterialSections=3,limitation='Single full-original 2Mtri candidate only;1.939Mleaf triangles/alpha overdraw remain expensive. Platform eligibility does not prove native assets, render execution, budget or Shipping performance.')
    output.mkdir();write(output/'candidate-original-tree.gltf',candidate);write(output/'original-geometry-decoder-proof.json',dict(sourceOnly=True,sourceGLTF=inputs['provider:tree_small_02_2k.gltf'],sourceBinary=inputs['provider:tree_small_02.bin'],parts=parts,sourceNodes=original['nodes'],sourceLODCount=1,sourceVertices=vertex_count,sourceTriangles=2062487,sourceModeling='Original published provider modeling, unchanged attributes/order; one whole-tree shift/scale only.'))
    write(output/'single-tree-selection.json',selection);write(output/'original-tree-material-proposal.json',material);write(output/'whole-tree-mask-review.json',masks_audit)
    camera=next(v for v in data['views']['views']if v['id']=='exterior-canopy-close');plot(output,target,samples,masks_audit,full['canopyPlacements'],camera)
    plan=dict(schemaVersion=1,owner=OWNER,status='source-only-single-original-tree-native-R22-base-pending',generatorSha256=sha(ROOT/OWNER),generatedAt=datetime.now(timezone.utc).isoformat(),inputFiles=inputs,
        provider='Poly Haven',sourcePage='https://polyhaven.com/a/tree_small_02',license='CC0-1.0',originalProviderFiles=receipt['files'],publishedOriginalFileCount=12,publishedOriginalBytes=115965151,activeDesign=context['activeDesign'],housePlacement=context['housePlacement'],sourceSceneSha256=context['sourceSceneSha256'],sourceObjSha256=context['sourceObjSha256'],regionId='village_nearest_grove',targetRootId=TARGET,nativeNamespaceProposal=PREFIX,
        candidateGLTF=pin(output/'candidate-original-tree.gltf'),decoderProof=pin(output/'original-geometry-decoder-proof.json'),selection=pin(output/'single-tree-selection.json'),materialProposal=pin(output/'original-tree-material-proposal.json'),maskReview=pin(output/'whole-tree-mask-review.json'),sourcePlot=pin(output/'source-one-tree-layout.png'),sourceCamera=camera,
        preservedSourceArrays={k:digest(context[k])for k in ['meshes','treePlacements','regionalVegetationPlacements','groundCoverPlacements','meadowBladePlacements','meadowUnderstoryPlacements']},unchangedOriginalRegionalRows=1099,unchangedOtherGroveRoots=77,
        pendingNativeBase=dict(required='Actual validated saved R22 combined composition after integration; no future report invented.',selectedNativeReport=None,selectionComplete=False,currentNativeGroupSourceEvidence='Actual original R16 /R21before witness only, not an R22 native report.'),
        budget=dict(newTreeActors=1,oldNativeTreeInstanceRetired=1,sourceLODCount=1,sourceTriangles=2062487,sourceVertices=vertex_count,sourceSections=3,newMeshAssets=1,newMaterialAssets=3,newTextureObjects=10,interchangePipelinesIfNeeded=3,maximumProposedNewPackages=17,sourceCandidateReferencesOriginalBuffer=True),nanite=nanite,
        sourceEvidenceLimit='2024 ortho-derived root/height/previous crown envelope are authored/inferred. Burkea africana is an artistic original-model pilot, ecological fit/local species and surveyed site elevation not verified.',nativeApplied=False,nativeAppearanceAccepted=False,fullPhotorealismAccepted=False,ecologicalFitVerified=False,performanceAccepted=False,shippingVerified=False,packageVerified=False)
    write(output/'original-tree-source-plan.json',plan)
    # Re-read the actual NEW descriptor and all12 untouched published files.
    validate_document(read(output/'candidate-original-tree.gltf'),original,output,scale,minimum)
    for row in receipt['files']:require(sha(row['path'])==row['sha256'], 'Published original changed during study')
    write(output/'source-validation-receipt.json',dict(schemaVersion=1,owner=OWNER,status='PASS_SOURCE_SINGLE_ORIGINAL_TREE_ALL_VERTEX_MASKS_NATIVE_PENDING',plan=pin(output/'original-tree-source-plan.json'),generator=pin(ROOT/OWNER),originalPublishedFilesVerifiedUnchanged=12,allSourceAttributeBytesAndIndexOrderPreserved=True,allTransformedVerticesChecked=count,allOriginalTrianglesConservativelyMaskProven=2062487,sourceSections=3,sourceLods=1,newTreeRoots=1,oldSourceOtherRootsUnchanged=77,CBB3000Preserved=True,sourceMasks=masks_audit['exclusions'],nativeBaseSelectionComplete=False,nativeApplied=False,nativeAppearanceAccepted=False,performanceAccepted=False,shippingVerified=False,packageVerified=False,fullPhotorealismAccepted=False))
    print(json.dumps(dict(plan=pin(output/'original-tree-source-plan.json'),receipt=pin(output/'source-validation-receipt.json'),scale=scale,sourceHeightM=height,worldHeightCm=target['heightCm'],radiusCm=actual_radius,sourceVertices=vertex_count,sourceTriangles=2062487),indent=2))


if __name__=='__main__':main()
