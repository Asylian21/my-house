"""R6 garden-only morphology: two CC0 source-shoot composites, immutable output.

Blender: --background --python this.py -- export --output OUTPUT
Python: this.py audit-plan --output OUTPUT
Blender: --background --python this.py -- preview --output OUTPUT
The standalone geometry manifest extends the existing library; it does not copy
or mutate its other 35 variants, source maps, material recipes or R4 garden roots.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'output/unreal/exterior-assets-20260926-r3'
LIBRARY = ROOT / 'output/unreal/exterior-assets-20260926-r5'
GARDEN = ROOT / 'output/unreal/exterior-garden-20260926-r4/garden-plan.json'
BLEND = SOURCE / 'periwinkle_plant/periwinkle_plant_2k.blend'
KEY = 'ph_periwinkle_plant'


def require(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(encode(value))


def uv_sha(mesh):
    return hashlib.sha256(b''.join(struct.pack('<2f', *x.uv) for x in mesh.uv_layers.active.data)).hexdigest()


def used(mesh):
    return {v for p in mesh.polygons for v in p.vertices}


def bounds(mesh):
    points = [mesh.vertices[i].co for i in used(mesh)]
    return [[min(p[k] for p in points) for k in range(3)],
            [max(p[k] for p in points) for k in range(3)]]


def native_bounds(mesh):
    lo, hi = bounds(mesh)
    return {'min': [lo[0]*100, -hi[1]*100, lo[2]*100],
            'max': [hi[0]*100, -lo[1]*100, hi[2]*100]}


def shoot_specs(variant):
    """Three irregular height bands, with continuous branching inherited intact."""
    rng = random.Random(601226061 + variant * 1709)
    specs = []
    # Seven upright leaders, eight outward middle shoots and eight small shoots.
    # Larger source plants supply the leaders: avoid inflating tiny source leaves.
    for index in range(23):
        band = 0 if index < 7 else 1 if index < 15 else 2
        angle = index * 2.3999632297 + variant*.43 + rng.uniform(-.26, .26)
        height = rng.uniform(*[(.44, .57), (.27, .39), (.16, .25)][band])
        radius = rng.uniform(*[(.018, .09), (.075, .15), (.13, .205)][band])
        source = ([1, 2, 3][(index+variant) % 3] if band == 0
                  else [2, 3, 4, 5][(index+variant) % 4])
        specs.append({'source': f'periwinkle_plant_{source:02}', 'band': band,
                      'heightM': height, 'rootXYm': [math.cos(angle)*radius, math.sin(angle)*radius],
                      'yaw': angle+rng.uniform(-.7,.7),
                      'tilt': math.radians(rng.uniform(*[(6,16),(13,28),(18,35)][band])),
                      'tiltDirection': angle+rng.uniform(-.65,.65),
                      'twist': math.radians(rng.uniform(-38,38)),
                      'bendXYm': [math.cos(angle)*rng.uniform(.018,.048), math.sin(angle)*rng.uniform(.018,.048)],
                      'swayXYm': [rng.uniform(-.012,.012),rng.uniform(-.012,.012)]})
    return specs


def export(output):
    import bpy
    from mathutils import Matrix, Vector
    require(not (output/'geometry-manifest.json').exists(), 'Choose a fresh output revision')
    require(sha(BLEND) == 'e9fc4300a8be05a9e7ec4423c239e9af37a2f3e4be9e6175a19ba82e1ffafd8a', 'CC0 source changed')
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    stub = bpy.data.materials.new(KEY)
    stub.use_nodes = True
    records, objects, uv_audit = [], [], []
    for variant in range(2):
        specs = shoot_specs(variant)
        variants, sources = [], []
        for level in range(3):
            parts, names = [], []
            for index, spec in enumerate(specs):
                source = bpy.data.objects[spec['source']+'_LOD'+str(level+1)]
                base = bpy.data.objects[spec['source']+'_LOD0']
                basis = Matrix.LocRotScale(Vector((0,0,0)),base.rotation_euler.to_quaternion(),base.scale)
                source_points = [basis@base.data.vertices[i].co for i in used(base.data)]
                floor = min(p.z for p in source_points)
                source_height = max(p.z for p in source_points)-floor
                scale = spec['heightM']/source_height
                data = source.data.copy()
                original_uv = uv_sha(data)
                # A continuous deformation moves every source face together;
                # branch/leaf attachment and source topology are not disconnected.
                rotation = Matrix.Rotation(spec['tiltDirection'],3,'Z') @ Matrix.Rotation(spec['tilt'],3,'Y')
                rotation = rotation @ Matrix.Rotation(spec['yaw']-spec['tiltDirection'],3,'Z')
                for vertex in data.vertices:
                    p = basis@vertex.co
                    p.z -= floor
                    t = min(1.,max(0.,p.z/source_height))
                    p *= scale
                    twist = spec['twist']*t*t
                    p.x, p.y = math.cos(twist)*p.x-math.sin(twist)*p.y, math.sin(twist)*p.x+math.cos(twist)*p.y
                    p.x += spec['bendXYm'][0]*t*t + spec['swayXYm'][0]*math.sin(math.pi*t)*t
                    p.y += spec['bendXYm'][1]*t*t + spec['swayXYm'][1]*math.sin(math.pi*t)*t
                    p = rotation@p
                    p.x += spec['rootXYm'][0]
                    p.y += spec['rootXYm'][1]
                    vertex.co = p
                data.materials.clear()
                data.materials.append(stub)
                obj = bpy.data.objects.new(f'GardenPart_{variant}_{level}_{index}',data)
                bpy.context.scene.collection.objects.link(obj)
                for selected in bpy.context.selected_objects:
                    selected.select_set(False)
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                if data.has_custom_normals:
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
                data.update()
                require(uv_sha(data) == original_uv, 'Source UVs changed during morphology')
                uv_audit.append({'variant':variant,'lod':level,'part':index,'source':source.name,
                                 'uvLoopSha256':original_uv,'uvUnchanged':True,
                                 'sourceTriangles':sum(len(p.vertices)-2 for p in source.data.polygons),
                                 'derivedTriangles':sum(len(p.vertices)-2 for p in data.polygons),
                                 'sourceUniformScale':scale})
                parts.append(obj)
                names.append(source.name)
            for selected in bpy.context.selected_objects:
                selected.select_set(False)
            for part in parts:
                part.select_set(True)
            bpy.context.view_layer.objects.active = parts[0]
            bpy.ops.object.join()
            obj = bpy.context.object
            obj.name = f'PH_garden_pink_r6_{chr(97+variant)}_LOD{level}'
            obj.data.name = obj.name
            obj.select_set(False)
            variants.append(obj)
            sources.append(names)
        # Shared isotropic normalization across all LODs preserves leaf shape.
        all_bounds = [bounds(o.data) for o in variants]
        floor = min(b[0][2] for b in all_bounds)
        top = max(b[1][2] for b in all_bounds)
        uniform = .60/(top-floor)
        normalise = Matrix.Diagonal((uniform,uniform,uniform,1)) @ Matrix.Translation((0,0,-floor))
        lods = []
        for level,obj in enumerate(variants):
            obj.data.transform(normalise)
            obj.data.update()
            obj.data.calc_loop_triangles()
            lods.append({'level':level,'nodeName':obj.name,'vertices':len(obj.data.vertices),
                         'triangles':len(obj.data.loop_triangles),'expectedBoundsCm':native_bounds(obj.data),
                         'sourceObjects':sources[level],
                         'derivation':'UV-preserving root-anchored continuous bend/twist of original connected shoots; common isotropic normalization'})
        records.append({'id':f'garden_pink_r6_{chr(97+variant)}','role':'ornamental','form':'flowering',
                        'flowerColor':'pink','placementPolicy':'explicit-only',
                        'replaces':f'ornamental_pink_{chr(97+variant)}',
                        'sourceAsset':'periwinkle_plant','sourceUrl':'https://polyhaven.com/a/periwinkle_plant',
                        'materialKeys':[KEY],'heightCm':60.,'sourceComponents':len(specs),
                        'sourceComposition':specs,'normalizationScale':uniform,'lods':lods,
                        'composition':'Illustrative cultivated flowering clump; inherited connected source branching, multi-height shoots and varied leaf-plane orientations. No species census claim.'})
        objects.extend(variants)
    for selected in bpy.context.selected_objects:
        selected.select_set(False)
    for obj in objects:
        obj.select_set(True)
    path = output/'glb/garden_pink_r6.glb'
    path.parent.mkdir(parents=True,exist_ok=True)
    require(not path.exists(),'GLB output exists')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=False,
                             export_yup=True,export_normals=True,export_tangents=True,export_materials='EXPORT',
                             export_animations=False,export_cameras=False,export_lights=False)
    repair = orthogonalize(path)
    for record in records:
        record.update(glbPath=str(path),glbSha256=sha(path),
                      tangentDerivation='Exported tangent Gram-Schmidt orthogonalization; source UV and topology unchanged')
    material = json.loads((LIBRARY/'material-manifest.json').read_text())[KEY]
    inputs = {str(p):sha(p) for p in [BLEND,LIBRARY/'material-manifest.json',SOURCE/'asset-manifest.json',
                                    SOURCE/'glb/ornamental_pink.glb',Path(__file__)]}
    inputs.update({r['path']:r['sha256'] for r in material['maps'].values()})
    manifest = {'schema':1,'units':'metres','revision':'R6 standalone garden extension',
                'axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]',
                'sourceBasis':'Blender metres Z-up -> glTF [x,z,-y] -> Unreal [100*x,-100*y,100*z]',
                'rootPolicy':'Display translations removed, each shoot rooted at source ground, common all-LOD floor zero',
                'status':'OFFLINE_GEOMETRY_NOT_NATIVE_ACCEPTED','meshes':records,'inputFiles':inputs}
    write(output/'geometry-manifest.json',manifest)
    write(output/'morphology-audit.json',{'status':'PASS_SOURCE_UV_AND_TOPOLOGY','sourceUvUnchanged':True,
          'texturePixelsChanged':False,'newMaterialKeys':[],'materialKeys':[KEY],
          'materialSource':{'path':str(LIBRARY/'material-manifest.json'),'sha256':sha(LIBRARY/'material-manifest.json')},
          'newGlbFiles':1,'newVariants':2,'sourceComponentsPerVariant':23,
          'bandCounts':{'leaders':7,'middle':8,'lower':8},'sourceParts':uv_audit,'tangentRepair':repair,
          'limits':['Source imagery includes original pink flowers and some yellowing source leaves; no recolour or emission added.',
                    'Leaf planes vary through connected shoot deformation, not independently detached leaf cards.',
                    'Source branch connectivity retained; inter-shoot leaf intersections require native visual review.']})
    print('EXPORTED',path,sha(path),flush=True)


def glb(path):
    data = Path(path).read_bytes()
    length = struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+length]),data[28+length:]


def accessor(doc,raw,index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    dim = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    kind = {5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']]
    fmt = '<'+kind*dim
    stride = view.get('byteStride',struct.calcsize(fmt))
    start = view.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from(fmt,raw,start+i*stride) for i in range(a['count'])]


def orthogonalize(path):
    data = bytearray(path.read_bytes())
    length = struct.unpack_from('<I',data,12)[0]
    doc = json.loads(data[20:20+length])
    offset = 28+length
    seen,count,max_before = set(),0,0.
    def layout(index,dim):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        return a['count'],offset+v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',dim*4)
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            attrs=primitive['attributes'];pair=(attrs['NORMAL'],attrs['TANGENT'])
            if pair in seen:continue
            seen.add(pair)
            n,np,ns=layout(pair[0],3);tc,tp,ts=layout(pair[1],4)
            require(n==tc,'Tangent count')
            for i in range(n):
                normal=struct.unpack_from('<3f',data,np+i*ns);t=struct.unpack_from('<4f',data,tp+i*ts)
                norm=math.sqrt(sum(v*v for v in normal));normal=[v/norm for v in normal]
                dot=sum(normal[k]*t[k] for k in range(3));max_before=max(max_before,abs(dot))
                tangent=[t[k]-normal[k]*dot for k in range(3)]
                size=math.sqrt(sum(v*v for v in tangent))
                require(size>1e-8,'Degenerate tangent')
                struct.pack_into('<4f',data,tp+i*ts,*(v/size for v in tangent),t[3]);count+=1
    path.write_bytes(data)
    return {'vertices':count,'maxNormalTangentDotBefore':max_before,'positionNormalUvIndicesUntouched':True}


def audit_plan(output):
    manifest=json.loads((output/'geometry-manifest.json').read_text())
    doc,raw=glb(output/'glb/garden_pink_r6.glb')
    source_doc,source_raw=glb(SOURCE/'glb/ornamental_pink.glb')
    source_uv_limits={}
    for mesh in source_doc['meshes']:
        coords=[uv for primitive in mesh['primitives']
                for uv in accessor(source_doc,source_raw,primitive['attributes']['TEXCOORD_0'])]
        source_uv_limits[int(mesh['name'][-1])]=([min(v[k]for v in coords)for k in range(2)],
                                                [max(v[k]for v in coords)for k in range(2)])
    nodes=[]
    for row in manifest['meshes']:
        require(sha(row['glbPath'])==row['glbSha256'],'GLB pin changed')
        require(row['placementPolicy']=='explicit-only','New role must not leak into random sampling')
        for lod in row['lods']:
            node=next(n for n in doc['nodes'] if n['name']==lod['nodeName'])
            require(not any(k in node for k in ['matrix','translation','rotation','scale']),'Unexpected GLB transform')
            mesh=doc['meshes'][node['mesh']]
            require([doc['materials'][p['material']]['name']for p in mesh['primitives']]==[KEY],'Material binding drift')
            points=[];total=bad=opposed=faces=0;maxdot=0.;uvmin=[1e9,1e9];uvmax=[-1e9,-1e9]
            for primitive in mesh['primitives']:
                a=primitive['attributes'];require(all(k in a for k in ['POSITION','NORMAL','TANGENT','TEXCOORD_0']),'Missing attributes')
                p=accessor(doc,raw,a['POSITION']);n=accessor(doc,raw,a['NORMAL']);t=accessor(doc,raw,a['TANGENT']);uv=accessor(doc,raw,a['TEXCOORD_0']);indices=[i[0] for i in accessor(doc,raw,primitive['indices'])]
                require(all(math.isfinite(v) for group in [p,n,t,uv] for xyz in group for v in xyz),'Nonfinite vertex attribute')
                points.extend([[x*100,z*100,y*100]for x,y,z in p]);total+=len(indices)//3
                for normal,tangent in zip(n,t):
                    nd=abs(sum(normal[k]*tangent[k]for k in range(3)));maxdot=max(maxdot,nd)
                    require(abs(math.sqrt(sum(v*v for v in normal))-1)<1e-4,'Nonunit normal')
                    require(abs(math.sqrt(sum(v*v for v in tangent[:3]))-1)<1e-4,'Nonunit tangent')
                    bad+=nd>.001
                for coord in uv:
                    for k in range(2):uvmin[k]=min(uvmin[k],coord[k]);uvmax[k]=max(uvmax[k],coord[k])
                for i in range(0,len(indices),3):
                    ia,ib,ic=indices[i:i+3];pa,pb,pc=p[ia],p[ib],p[ic]
                    u=[pb[k]-pa[k]for k in range(3)];v=[pc[k]-pa[k]for k in range(3)]
                    cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                    if sum(x*x for x in cross)<1e-18:continue
                    normal=[(n[ia][k]+n[ib][k]+n[ic][k])/3 for k in range(3)]
                    opposed+=sum(cross[k]*normal[k]for k in range(3))<0;faces+=1
            actual={'min':[min(p[k]for p in points)for k in range(3)],'max':[max(p[k]for p in points)for k in range(3)]}
            error=max(abs(actual[e][k]-lod['expectedBoundsCm'][e][k])for e in ['min','max']for k in range(3))
            require(total==lod['triangles'] and error<.001,'Native geometry contract drift')
            require(bad==0 and opposed/max(faces,1)<.001,'Invalid tangent/winding')
            # The provider intentionally tiles some source stem UVs beyond 0..1.
            # Match that source contract exactly; never clamp model UVs to ortho policy.
            source_min,source_max=source_uv_limits[lod['level']]
            require(max(abs(a-b)for a,b in zip(uvmin+uvmax,source_min+source_max))<1e-6,'Source wrapping UV bounds changed')
            nodes.append({'node':lod['nodeName'],'triangles':total,'boundErrorCm':error,'maxAbsNormalTangentDot':maxdot,
                          'opposedFaces':opposed,'faces':faces,'uvMin':uvmin,'uvMax':uvmax,'materialKeys':[KEY],
                          'uvSourceRangeExact':True,'uvAddressMode':'Wrap, inherited model atlas including tiled stems'})
    for path,pin in manifest['inputFiles'].items():require(sha(path)==pin,'Source pin changed: '+path)
    write(output/'geometry-validation.json',{'status':'PASS_OFFLINE_NOT_NATIVE','nodes':nodes,'variantCount':2,'lodCount':6,
          'checks':['source and GLB SHA256','explicit-only placement','material name and slots','untransformed nodes',
                    'UV0 inherited wrapping atlas bounds','source per-loop UV preserved','unit normals and tangents','face orientation','native bounds','LOD triangle counts']})
    garden=deepcopy(json.loads(GARDEN.read_text()));original=deepcopy(garden)
    new={r['replaces']:r for r in manifest['meshes']}
    for row in garden['ornamentalPlacements']:
        if row['meshId'] not in new:continue
        replacement=new[row['meshId']]
        lo=[min(l['expectedBoundsCm']['min'][k] for l in replacement['lods'])for k in range(3)]
        hi=[max(l['expectedBoundsCm']['max'][k] for l in replacement['lods'])for k in range(3)]
        radius=max(math.hypot(x,y)for x in [lo[0],hi[0]]for y in [lo[1],hi[1]])
        scale=min(row['actualHeightCm']/(hi[2]-lo[2]),row['radiusCm']/radius)
        previous_radius=row['radiusCm'];row.update(meshId=replacement['id'],scale=[scale]*3,uniformScale=scale,
            heightCm=(hi[2]-lo[2])*scale,actualHeightCm=(hi[2]-lo[2])*scale,radiusCm=radius*scale,
            sourceMinimumZCm=lo[2],sourceMaximumZCm=hi[2],sourceCrownRadiusCm=radius,
            morphologyRevision='R6',previousEnvelopeRadiusCm=previous_radius)
    # Every root/yaw remains exact. Changed crowns only shrink within certified R4 envelopes.
    audits=[]
    for row,old in zip(garden['ornamentalPlacements'],original['ornamentalPlacements']):
        require(row['positionCm']==old['positionCm'] and row['yawDeg']==old['yawDeg'],'Root/yaw moved')
        require(row['radiusCm']<=old['radiusCm']+1e-8 and row['actualHeightCm']<=old['actualHeightCm']+1e-8,'Old envelope exceeded')
        detail=deepcopy(next(r for r in original['audit']['individual']if r['id']==row['id']))
        delta=old['radiusCm']-row['radiusCm']
        for key in ['crownToDomainEdgeClearanceCm','crownToStepClearanceCm','crownToHardscapeClearanceCm']:detail[key]+=delta
        detail['hardscapeDistancesCm']={k:v+delta for k,v in detail['hardscapeDistancesCm'].items()}
        audits.append(detail)
    pairs=[]
    for a,b in itertools.combinations(garden['ornamentalPlacements'],2):
        distance=math.dist(a['positionCm'][:2],b['positionCm'][:2]);gap=distance-a['radiusCm']-b['radiusCm']
        require(distance>=60 and gap>=2,'Crown/root clearances changed')
        pairs.append({'a':a['id'],'b':b['id'],'rootDistanceCm':distance,'conservativeCrownGapCm':gap})
    audit=deepcopy(original['audit']);audit.update(individual=audits,pairwise=pairs,
        minimumConservativeCrownGapCm=min(p['conservativeCrownGapCm']for p in pairs),
        minimumCrownToBedEdgeClearanceCm=min(r['crownToDomainEdgeClearanceCm']for r in audits if r['sourceBedId']),
        minimumCrownToStepClearanceCm=min(r['crownToStepClearanceCm']for r in audits),
        minimumCrownToHardscapeClearanceCm=min(r['crownToHardscapeClearanceCm']for r in audits),
        exactR4RootsPreserved=12,newPinkVariants=2,unchangedOtherPlacements=10)
    garden.update(revision='R6 garden morphology',owner=str(Path(__file__).relative_to(ROOT)),
        generatedAt=datetime.now(timezone.utc).isoformat(),generatorSha256=sha(__file__),audit=audit,
        morphologyExtension={'path':str(output/'geometry-manifest.json'),'sha256':sha(output/'geometry-manifest.json')},
        limits=['Illustrative garden design, not surveyed botany.',
                'All twelve R4 roots/yaws and ten unaffected placements retained exactly.',
                'New pink crowns bounded by the old complete circular envelopes at every yaw and LOD.',
                'R5 material recipe and all source texture pixels unchanged; native R6 appearance/performance pending.'])
    garden['inputFiles'].update({str(p):sha(p)for p in [GARDEN,output/'geometry-manifest.json',output/'geometry-validation.json',Path(__file__)]})
    garden['inputFiles'].update(manifest['inputFiles'])
    garden['inputFiles'][str(output/'glb/garden_pink_r6.glb')]=sha(output/'glb/garden_pink_r6.glb')
    write(output/'garden-plan.json',garden)
    write(output/'summary.json',{'status':'PASS_OFFLINE_NOT_NATIVE','extensionManifest':str(output/'geometry-manifest.json'),
          'extensionSha256':sha(output/'geometry-manifest.json'),'gardenPlan':str(output/'garden-plan.json'),
          'gardenPlanSha256':sha(output/'garden-plan.json'),'newMaterialKeys':[],'unchangedMaterialKey':KEY,
          'lodTriangles':{r['id']:[l['triangles']for l in r['lods']]for r in manifest['meshes']},
          'gardenAudit':{k:v for k,v in audit.items()if k not in ['individual','pairwise']}})
    print((output/'summary.json').read_text())


def preview(output):
    import bpy
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # A/B morphology comparison uses the SAME unchanged source-derived material.
    bpy.ops.import_scene.gltf(filepath=str(SOURCE/'glb/ornamental_pink.glb'))
    bpy.ops.import_scene.gltf(filepath=str(output/'glb/garden_pink_r6.glb'))
    wanted=['PH_ornamental_pink_a_LOD0','PH_garden_pink_r6_a_LOD0','PH_garden_pink_r6_b_LOD0']
    kept={o.name:o for o in bpy.data.objects if o.type=='MESH' and o.name in wanted}
    for obj in list(bpy.data.objects):
        if obj.name not in kept:bpy.data.objects.remove(obj,do_unlink=True)
    material=bpy.data.materials.new('R5 source-equivalent preview');material.use_nodes=True
    nodes=material.node_tree.nodes;links=material.node_tree.links;bsdf=nodes.get('Principled BSDF')
    material.diffuse_color=(.15,.25,.08,1)
    maps=json.loads((LIBRARY/'material-manifest.json').read_text())[KEY]['maps']
    tex={}
    for channel,spec in maps.items():
        tex[channel]=nodes.new('ShaderNodeTexImage');tex[channel].image=bpy.data.images.load(spec['path'])
        if channel!='albedo':tex[channel].image.colorspace_settings.name='Non-Color'
    mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[2].default_value=(.8,.8,.8,1)
    links.new(tex['albedo'].outputs['Color'],mul.inputs[1]);links.new(mul.outputs[0],bsdf.inputs['Base Color'])
    # R5 selective calibration is native-shader-specific; no source-pixel bake.
    # Preview deliberately compares identical provider .8 colour, not UE shading.
    links.new(tex['alpha'].outputs['Color'],bsdf.inputs['Alpha']);links.new(tex['roughness'].outputs['Color'],bsdf.inputs['Roughness'])
    bsdf.inputs['Specular IOR Level'].default_value=.12
    if hasattr(material,'surface_render_method'):material.surface_render_method='DITHERED'
    for index,name in enumerate(wanted):
        obj=kept[name];obj.location.x=(index-1)*1.1
        lo,hi=bounds(obj.data);scale=.55/(hi[2]-lo[2]);obj.scale=(scale,)*3
        for slot in range(len(obj.data.materials)):obj.data.materials[slot]=material
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01))
    ground=bpy.data.materials.new('Neutral preview floor');ground.diffuse_color=(.18,.20,.16,1);bpy.context.object.data.materials.append(ground)
    world=bpy.data.worlds.new('Preview sky');bpy.context.scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.6,.68,.8,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
    bpy.ops.object.light_add(type='SUN',location=(0,0,10));sun=bpy.context.object;sun.data.energy=2;sun.data.angle=math.radians(3)
    sun.rotation_euler=(math.radians(24),math.radians(-35),math.radians(-32))
    bpy.ops.object.camera_add(location=(.9,-4.7,1.65));cam=bpy.context.object
    cam.rotation_euler=(Vector((0,0,.25))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=50;bpy.context.scene.camera=cam
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=1500;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(output/'morphology-comparison.png')
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    bpy.ops.render.render(write_still=True)
    write(output/'preview-receipt.json',{'status':'OFFLINE_BLENDER_MORPHOLOGY_ONLY','image':str(output/'morphology-comparison.png'),
          'sha256':sha(output/'morphology-comparison.png'),'left':'R3/R4 pink a','center':'R6 pink a','right':'R6 pink b',
          'sameHeightCm':55,'sourceTexturePixelsChanged':False,'nativeMaterialEquivalent':False,
          'limits':['All three use identical original atlas and .8 provider colour multiplier.',
                    'R5 selective native green calibration, two-sided foliage and Unreal lighting not simulated.',
                    'This image proves comparative geometry only; final garden camera acceptance is native.']})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['export','audit-plan','preview'])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--'in sys.argv else None)
    output=args.output.resolve()
    require(output.is_relative_to(ROOT/'output/unreal'),'Use isolated Unreal output')
    {'export':export,'audit-plan':audit_plan,'preview':preview}[args.action](output)
