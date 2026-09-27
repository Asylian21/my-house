"""Isolated C/B/B stove geometry study; never edits a source project or runs UE.

The original solid body remains collision-authoritative. Only its visual proxy
and six opaque fire proxies may be hidden by a future, separately reviewed stage.
"""
import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-stove-geometry.py'
HELPER = ROOT/'scripts/unreal/stove-visuals/generate.py'
SPEC = importlib.util.spec_from_file_location('legacy_stove_mesh_primitives', HELPER)
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)
require, sha = G.require, G.sha
PREFIX = 'FIREPLACE-STOVE-B-2026-09-11 · '
IDS = [f'DOM_{n:05}' for n in (553,556,562,563,564,565,566)]
GLASS_ID = 'DOM_00557'
GUARDS = {
    'DOM_00553': ('BODY · matne čierne valcové teleso Ø510', 'real-interior-fireplace', 256, True),
    'DOM_00556': ('FIRE-GLOW · žeravé ohnisko', 'real-interior-fireplace-ember', 192, False),
    'DOM_00562': ('LOG-1 · horiace poleno', 'real-interior-fireplace-ember', 80, False),
    'DOM_00563': ('LOG-2 · horiace poleno', 'real-interior-fireplace-ember', 80, False),
    'DOM_00564': ('FLAME-1 · plameň', 'real-interior-fireplace-ember', 96, False),
    'DOM_00565': ('FLAME-2 · plameň', 'real-interior-fireplace-ember', 96, False),
    'DOM_00566': ('FLAME-3 · plameň', 'real-interior-fireplace-ember', 96, False),
    GLASS_ID: ('CURVED-GLASS · zaoblené panoramatické dvierka 118°', 'real-interior-fireplace-glass', 192, False),
}
FACING = -math.pi/4
ATLAS = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Runtime/NetworkPredictionExtras/Content/Art/Effects/Proto/Shared/Textures/Fire/T_Fire_SubUV.uasset')
ATLAS_SHA = '865a10d77419a7a5c80a89abbf2a738168cd79bfad1aab1397d3d5802ac6f33c'


def rotate(point, angle):
    x,y,z = point
    return (x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle), z)


def source(directory):
    directory = Path(directory)
    scene = json.loads((directory/'scene.json').read_text())
    require(scene['activeDesign'] == {'variant':'C','heatingLayout':'B','livingLayout':'B'}, 'Stove study requires C/B/B')
    require(scene['objSha256'] == sha(directory/'dom-mm.obj'), 'Stove source OBJ drift')
    selected = [r for r in scene['objects'] if r['id'] in GUARDS]
    records = {r['id']:r for r in selected}
    require(len(selected) == len(records) == len(GUARDS), 'Missing/duplicate stove source')
    triangles = G.obj_geometry(directory/'dom-mm.obj', set(GUARDS))
    for id_, (suffix, material, count, collision) in GUARDS.items():
        r = records[id_]
        require(r['name'] == PREFIX+suffix and r['sourceId'] == PREFIX+suffix
                and r['enabled'] and r['instances'] == 1 and r['materialNames'] == [material]
                and r['triangles'] == count and len(triangles[id_]) == count
                and r['metadata']['babylonCheckCollisions'] == collision
                and not r['metadata'].get('doorMotion'), 'Stove source semantics/geometry/collision drift: '+id_)
        points = [p for tri in triangles[id_] for p in tri]
        require(all(abs(fn(p[i] for p in points)-r['boundsMm'][key][i]) < .011
                    for key,fn in [('min',min),('max',max)] for i in range(3)), 'Source stove bounds mismatch')
    b = records['DOM_00553']['boundsMm']
    center = [(b['min'][i]+b['max'][i])/2 for i in (0,1)]
    require(all(abs((b['max'][i]-b['min'][i])-size) < .001 for i,size in enumerate((510,510,1520)))
            and abs(b['min'][2]-30)<.001 and abs(b['max'][2]-1550)<.001
            and records['DOM_00553']['metadata']['designSourceId'] == 'SRC-CLIENT-LIVING-VARIANT-B-20260911',
            'Source stove design/envelope changed')
    local = {id_:[tuple(rotate((p[0]-center[0],p[1]-center[1],p[2]),-FACING) for p in tri)
                  for tri in tris] for id_,tris in triangles.items()}
    glass = [p for tri in local[GLASS_ID] for p in tri]
    angles = [math.degrees(math.atan2(p[1],p[0])) for p in glass]
    require(max(abs(math.hypot(p[0],p[1])-264) for p in glass) < .011
            and abs(min(angles)+59)<.01 and abs(max(angles)-59)<.01,
            'Source glass no longer faces −45 degrees over its 118-degree window')
    return scene, records, local, center


def ember_bed():
    mesh = G.Mesh('RFIRE_EMBERS', 'embers')
    # Restrained irregular coals below the two source-sized logs, fully enclosed
    # by the existing firebox. No mesh displacement or light source is introduced.
    for j in range(17):
        angle = j*2.39996323
        radius = 24+128*math.sqrt((j+.5)/17)
        cx,cy = 15+radius*math.cos(angle), radius*math.sin(angle)
        size = 12+4*math.sin(j*1.73)
        ring = [(cx+size*math.cos(i*math.tau/7),cy+size*math.sin(i*math.tau/7),447+2*math.sin(i+j)) for i in range(7)]
        for i in range(7):
            a,b = ring[i],ring[(i+1)%7]
            mesh.triangle((cx,cy,456+3*math.sin(j)),a,b)
            mesh.triangle((cx,cy,441),b,a)
    return mesh


def geometry(local):
    # Reuse immutable mesh-building math, not its obsolete A-layout source
    # validation or editor importer. Geometry is made in the current stove frame.
    meshes, transforms, _ = G.geometry({'DOM_00522':local['DOM_00553']}, (0,0))
    for mesh in meshes:
        mesh.name = 'RFIRE_'+mesh.role.upper()
        if mesh.role == 'flames':
            # Bury card roots in the charred logs. The prior external proxy
            # offset left transparent flame tongues visibly suspended in front.
            mesh.positions = [(x-35,y,z-35) for x,y,z in mesh.positions]
    remap = {'DOM_00531':'DOM_00562','DOM_00532':'DOM_00563',
             'DOM_00533':'DOM_00564','DOM_00534':'DOM_00565','DOM_00535':'DOM_00566'}
    for row in transforms:
        row['visualOf'] = remap[row['visualOf']]
        if 'cards' in row:
            row['centerRelativeMm'][0] -= 35
            row['centerRelativeMm'][2] -= 35
    meshes.append(ember_bed())
    return meshes, transforms, validate(meshes)


def validate(meshes):
    result = G.validate_vertices(meshes)
    require({m.name for m in meshes} == {'RFIRE_SHELL','RFIRE_CHAMBER','RFIRE_LOGS','RFIRE_FLAMES','RFIRE_EMBERS'}, 'Unexpected fire study scope')
    for mesh in meshes:
        if mesh.role == 'embers':
            require(all(math.hypot(x,y) < 200 and 440 <= z <= 463 for x,y,z in mesh.positions), 'Ember bed escaped chamber floor')
    return result


def build(directory, output):
    directory, output = Path(directory).resolve(), Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a new isolated fire output')
    scene, records, local, center = source(directory)
    meshes, transforms, validation = geometry(local)
    require(sha(ATLAS) == ATLAS_SHA, 'Installed Epic flame atlas changed')
    output.mkdir(parents=True)
    world_meshes = copy.deepcopy(meshes)
    for mesh in world_meshes:
        mesh.positions = [rotate(p,FACING) for p in mesh.positions]
        mesh.normals = [rotate(p,FACING) for p in mesh.normals]
    glb = output/'realism-stove-study.glb'
    objects = G.write_glb(world_meshes, center, glb)
    role_sources = {'shell':['DOM_00553'], 'chamber':['DOM_00553'],
                    'logs':['DOM_00562','DOM_00563'], 'flames':['DOM_00564','DOM_00565','DOM_00566'], 'embers':['DOM_00556']}
    for row in objects:
        row['sourceIds'] = role_sources[row['role']]
        row['materialRole'] = row['role']
        row['expectedWorldBoundsCm'] = copy.deepcopy(row['nativeBoundsCm'])
        points = [(p[0]+center[0],p[1]+center[1],p[2]) for p in row['sourceRelativeVerticesMm']]
        row['visualBoundsMm'] = {'min':[min(p[i] for p in points) for i in range(3)],
                                'max':[max(p[i] for p in points) for i in range(3)]}
    decoded = G.read_glb_positions(glb,center)
    error = max(abs(a-b) for mesh in world_meshes for p,q in zip(mesh.positions,decoded[mesh.name]) for a,b in zip(p,q))
    require(error < .002, 'Fire GLB exceeds 0.002mm quantization tolerance')
    roundtrip = copy.deepcopy(meshes)
    for mesh in roundtrip:
        mesh.positions = [rotate(p,-FACING) for p in decoded[mesh.name]]
    validate(roundtrip)
    script = "import{readFile}from'node:fs/promises';import{validateBytes}from'gltf-validator';const r=await validateBytes(new Uint8Array(await readFile(process.argv[1])),{maxIssues:0});process.stdout.write(JSON.stringify(r.issues));"
    issues = json.loads(subprocess.check_output(['node','--input-type=module','-e',script,str(glb)],cwd=ROOT,text=True))
    require(not issues['numErrors'] and not issues['numWarnings'], 'Fire study GLB validation failed')
    # The embedded editor thumbnail is a preview aid only. It is not promoted
    # as the production texture or evidence of the full-resolution atlas grid.
    raw = ATLAS.read_bytes(); start = raw.index(b'\xff\xd8\xff'); end = raw.index(b'\xff\xd9',start)+2
    (output/'epic-fire-atlas-thumbnail.jpg').write_bytes(raw[start:end])
    report = {'schemaVersion':1,'owner':OWNER,'status':'offline-study-geometry-validated','generatedAt':datetime.now(timezone.utc).isoformat(),
              'sourceGeometry':str(directory),'sourceSceneSha256':sha(directory/'scene.json'),'sourceObjSha256':sha(directory/'dom-mm.obj'),
              'generatorSha256':sha(__file__),'generatorDependencies':{str(HELPER.relative_to(ROOT)):sha(HELPER)},
              'glb':glb.name,'glbSha256':sha(glb),'objects':objects,'triangles':sum(len(m.indices)//3 for m in meshes),
              'roundtripErrorMm':error,'khronosValidation':issues,'sourceRecords':records,'sourceIds':IDS,'hiddenSourceIds':IDS,
              'preservedSourceIds':[f'DOM_{n:05}' for n in range(553,572) if f'DOM_{n:05}' not in IDS],
              'sourceBodyCollisionPreserved':True,'originalLightingUnchanged':True,
              'sourceAxisMm':center,'facingDegrees':-45,'vertexValidation':validation,'localTransforms':transforms,
              'envelope':{'bodyRadiusMm':255,'bodyBottomMm':30,'bodyTopMm':1550,'chamberRadiusMm':245,
                          'chamberBottomMm':440,'chamberTopMm':1020,'glassRadiusMm':264,'windowArcDegrees':118},
              'builtinAsset':{'path':str(ATLAS),'sha256':ATLAS_SHA,'sizeBytes':ATLAS.stat().st_size,
                              'registryDimensions':[1024,1024],'thumbnailObservedGrid':[6,6],'fullAtlasNativeInspected':False},
              'nativeImported':False,'nativeRenderedVerified':False,
              'limitations':['Geometry study only; importer and materials are not implemented.',
                             'All original source mesh/collision/transform/door/glass/light records remain unchanged.',
                             'Inner firebox and char are illustrative construction cues, not measured stove internals.',
                             'Flame cards require a full native atlas inspection and day/night moving-view verification.',
                             'Builtin Epic texture reuse must be owned asset-only content with no sample runtime plugin dependency.']}
    (output/'geometry-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--geometry',required=True); parser.add_argument('--output',required=True)
    args = parser.parse_args(); report = build(args.geometry,args.output)
    print(json.dumps({key:report[key] for key in ('status','triangles','roundtripErrorMm')}))
