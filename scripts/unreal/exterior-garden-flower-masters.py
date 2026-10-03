"""Successor pink garden flowers with actual cupped corollas and paired leaves.

The frozen R3 generator and outputs remain reproducible. This extension changes
only two pink hero meshes, preserving all twelve primary roots and every detail
placement. Photographic leaf tissue is reused without editing any texture pixels.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-flower-masters.py'
HELPER = ROOT / 'scripts/unreal/exterior-garden-masters.py'
spec = importlib.util.spec_from_file_location('frozen_garden_master_export', HELPER)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.OWNER = OWNER  # Runtime exporter credit; the frozen helper file is untouched.
add, sub, mul, unit, cross = base.add, base.sub, base.mul, base.unit, base.cross
LEAF_UV = (.28, .30, .73, .74)
PETAL_RECIPE = {'kind': 'authored-foliage', 'maps': {}, 'linearColor': [.34, .115, .205],
                'roughness': .72, 'specular': .16, 'subsurfaceScale': .06, 'twoSided': True,
                'source': 'Original project authored flower geometry',
                'artDirection': 'Muted rose corollas with bounded vertex variation and physical folds; no emission or whole-flower cards.'}
BOTANICAL_REFERENCE = 'https://www.rhs.org.uk/plants/98105/catharanthus-roseus/details'


def leaf(mesh, anchor, direction, length, width, curl, colour, lod):
    """Smooth ovate outline, midrib fold, variable tip droop; opaque photo lamina."""
    radial = unit(direction)
    side = unit(cross(radial, [0, 0, 1]))
    normal = unit(cross(radial, side))
    points, uv, triangles = [], [], []
    sections = (7, 5, 3)[lod]
    for j in range(sections + 1):
        t = j / sections
        center = add(anchor, add(mul(radial, length*t), mul(normal, curl*math.sin(math.pi*.87*t))))
        w = width*(.035 + .965*math.sin(math.pi*t)**.76)
        for col in range(3):
            x = col - 1
            fold = .10*length*math.sin(math.pi*t)*(1-abs(x))
            tip = -.06*length*t*t*abs(x)
            points.append(add(center, add(mul(side, x*w*.5), mul(normal, fold+tip))))
            uv.append([LEAF_UV[0]+(LEAF_UV[2]-LEAF_UV[0])*col/2,
                       LEAF_UV[3]-(LEAF_UV[3]-LEAF_UV[1])*t])
    for j in range(sections):
        a = j*3; b = a+3
        triangles.extend(((a,b,a+1), (a+1,b,b+1), (a+1,b+1,a+2), (a+2,b+1,b+2)))
    mesh.geometry('regional_green_leaf', points, uv, triangles, colour)


def corolla(mesh, center, axis, radius, phase, colour, lod):
    """Five overlapping salver lobes with a narrow throat and rolled petal edges."""
    n = unit(axis)
    a = unit(cross(n, [0,0,1] if abs(n[2]) < .95 else [0,1,0])); b = unit(cross(n,a))
    sections, columns = (6,4,3)[lod], (5,3,3)[lod]
    for petal in range(5):
        phi = phase + petal*math.tau/5
        r = radius*(.94+.06*math.sin(phi*3+1.3))
        points, uv, triangles, vertex_colours = [], [], [], []
        for j in range(sections+1):
            t = j/sections
            angle = phi+.18*t
            radial = add(mul(a,math.cos(angle)),mul(b,math.sin(angle)))
            side = add(mul(a,-math.sin(angle)),mul(b,math.cos(angle)))
            width = r*(.06+.56*math.sin(math.pi*(.025+.95*t))**.63)
            longitudinal = r*(.10+.90*t)
            cup = r*(-.16*(1-t)**2+.085*math.sin(math.pi*t)+.07*t*t)
            for k in range(columns):
                x = 2*k/(columns-1)-1
                wrinkle = r*.018*math.sin(t*math.pi*3+petal*.8)*abs(x)
                height = cup + r*.10*x*x*math.sin(math.pi*t) + wrinkle
                p = add(center, add(mul(radial,longitudinal), add(mul(side,x*width),mul(n,height))))
                points.append(p); uv.append([k/(columns-1),t])
                throat = .48+.52*math.sin(math.pi*.5*t)**.65
                vein = .985+.015*math.sin(t*math.pi*9+petal*.7)
                vertex_colours.append([colour*.97*throat*vein,
                    colour*(.91+.07*math.cos(phi))*throat*vein,colour*(.77+.23*throat),1])
        for j in range(sections):
            for k in range(columns-1):
                i=j*columns+k; q=i+columns
                triangles.extend(((i,q,i+1),(i+1,q,q+1)))
        mesh.geometry('garden_petal_rose',points,uv,triangles,
                      [colour*.97,colour*(.91+.07*math.cos(phi)),colour,1])
        mesh.parts['garden_petal_rose']['colors'][-len(points):] = vertex_colours
    # A physical recessed cream eye; the tiny rose opening is not a flat disc.
    mesh.tube('garden_plume_silk',[add(center,mul(n,-radius*.22)),add(center,mul(n,-radius*.085))],
              radius*.11,[.85,.79,.61,1],sides=6 if lod==0 else 4)
    mesh.tube('garden_petal_rose',[add(center,mul(n,-radius*.27)),add(center,mul(n,-radius*.21))],
              radius*.055,[.34,.14,.26,1],sides=4)


def flower_clump(variant, lod):
    rng=random.Random(6012266700+variant*917); mesh=base.Mesh(); pairs=[]; flowers=[]
    stems=[]
    for i in range(13):
        angle = i*2.39996323 + rng.uniform(-.31,.31)
        root_radius = rng.uniform(.4,4.8)
        height = rng.uniform(25,43)
        spread = rng.uniform(6,17)*(1.08 if math.cos(angle-.6)>.2 else .87)
        bend = rng.uniform(-2.8,2.8)
        stems.append((angle,root_radius,height,spread,bend,rng.uniform(.79,1)))
    for index,(angle,root_radius,height,spread,bend,c) in enumerate(stems):
        shoot_rng=random.Random(6012268800+variant*917+index*7919)
        def stem(t):
            r=root_radius+spread*t**1.35
            return [r*math.cos(angle)-bend*math.sin(angle)*t*t,
                    r*math.sin(angle)+bend*math.cos(angle)*t*t,height*t]
        mesh.tube('garden_blade_green',[stem(j/6)for j in range(7)],.17,[c*.86,c,c*.9,1],sides=(6,5,4)[lod])
        for level,nominal_t in enumerate((.17,.34,.53,.69,.85)):
            node_rng=random.Random(6012269100+variant*917+index*7919+level*1213)
            t=nominal_t+node_rng.uniform(-.04,.04)
            if lod==2 and level==0:continue
            anchor=stem(t)
            phi=angle+level*math.pi/2+.3*math.sin(index+level)+node_rng.uniform(-.23,.23)
            length=5.3-level*.43+node_rng.uniform(-.5,.5)
            width=length*node_rng.uniform(.43,.51)
            directions=[]
            for opposite in (0,1):
                az=phi+opposite*math.pi+node_rng.uniform(-.065,.065)
                direction=[math.cos(az),math.sin(az),node_rng.uniform(-.35,.31)]
                # Both petioles originate at the same node. Slight independent
                # leaf pose/size variation avoids mirrored plastic leaf pairs.
                petiole=add(anchor,mul(unit(direction),.62))
                mesh.tube('garden_blade_green',[anchor,petiole],.055,[c*.8,c*.91,c*.8,1],sides=3)
                leaf(mesh,petiole,direction,length*(1-.055*opposite),width,
                     node_rng.uniform(-.22,.73),[c,c*.99,c*.96,1],lod)
                directions.append(direction)
            pairs.append({'stem':index,'node':level,'anchor':anchor,'directions':directions})
        top=stem(1)
        inclination=shoot_rng.uniform(.28,.85)
        axis=[inclination*math.cos(angle),inclination*math.sin(angle),shoot_rng.uniform(.67,1.)]
        size=shoot_rng.uniform(1.58,1.92)
        corolla(mesh,top,axis,size,angle+.26*index,shoot_rng.uniform(.79,1),lod)
        flowers.append({'stem':index,'center':top,'axis':axis,'petals':5,'radiusCm':size})
        # Axillary growth produces a bush, rather than evenly stacked flower discs.
        for branch in range(2 if index%3 else 1):
            branch_rng=random.Random(6012271000+variant*917+index*7919+branch*1213)
            start=stem(.49+.16*branch)
            azimuth=angle+(-1 if branch==0 else 1)*(.79+.12*math.sin(index))
            reach=branch_rng.uniform(4,7); rise=branch_rng.uniform(7,12)
            end=add(start,[reach*math.cos(azimuth),reach*math.sin(azimuth),rise])
            middle=add(start,mul(sub(end,start),.46))
            middle[2]+=.8
            mesh.tube('garden_blade_green',[start,middle,end],.11,[c*.87,c*.96,c*.8,1],sides=(5,4,3)[lod])
            phi=azimuth+math.pi/2; directions=[]
            for opposite in (0,1):
                az=phi+opposite*math.pi+branch_rng.uniform(-.065,.065)
                direction=[math.cos(az),math.sin(az),branch_rng.uniform(-.26,.35)]
                petiole=add(middle,mul(unit(direction),.43))
                mesh.tube('garden_blade_green',[middle,petiole],.045,[c*.8,c*.91,c*.8,1],sides=3)
                leaf(mesh,petiole,direction,3.7,1.7,branch_rng.uniform(-.15,.52),[c*.93,c*.94,c*.94,1],lod)
                directions.append(direction)
            pairs.append({'stem':index,'node':5+branch,'anchor':middle,'directions':directions})
            inclination=branch_rng.uniform(.42,.93)
            axis=[inclination*math.cos(azimuth),inclination*math.sin(azimuth),branch_rng.uniform(.65,1.1)]
            corolla(mesh,end,axis,size*.91,azimuth+.33,branch_rng.uniform(.76,.98),lod)
            flowers.append({'stem':index,'center':end,'axis':axis,'petals':5,'radiusCm':size*.91})
    return mesh, {'pairedNodes':pairs,'flowers':flowers,'stemCount':len(stems)}


def build(output, base_garden, library):
    output,base_garden,library=map(lambda p:Path(p).resolve(),(output,base_garden,library))
    base.require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Choose a fresh isolated output')
    original=json.loads(base_garden.read_text()); garden=deepcopy(original)
    source_materials=json.loads((library/'material-manifest.json').read_text())
    materials={key:deepcopy(source_materials[key])for key in ('garden_blade_green','garden_plume_silk','regional_green_leaf')}
    materials['garden_petal_rose']=deepcopy(PETAL_RECIPE)
    base.PALETTES['garden_petal_rose']=PETAL_RECIPE['linearColor']
    meshes=[];lod_rows=[];all_meshes=[];morphology={}
    for variant in range(2):
        mesh_id='garden_pink_spatial_r1_'+chr(97+variant); lods=[]
        authored=[flower_clump(variant,lod)for lod in range(3)]
        points=[p for mesh,_ in authored for part in mesh.parts.values()for p in part['positions']]
        bottom=min(p[2]for p in points);top=max(p[2]for p in points);normalization=45/(top-bottom)
        for lod in range(3):
            mesh,proof=authored[lod]
            for part in mesh.parts.values():
                part['positions']=[[p[0]*normalization,p[1]*normalization,(p[2]-bottom)*normalization]for p in part['positions']]
            for row in proof['pairedNodes']:
                p=row['anchor'];row['anchor']=[p[0]*normalization,p[1]*normalization,(p[2]-bottom)*normalization]
            for row in proof['flowers']:
                p=row['center'];row['center']=[p[0]*normalization,p[1]*normalization,(p[2]-bottom)*normalization]
                row['radiusCm']*=normalization
            proof['normalization']={'scale':normalization,'sourceMinimumZCm':bottom}
            points=[p for part in mesh.parts.values()for p in part['positions']]
            triangles=sum(len(part['triangles'])for part in mesh.parts.values())
            base.require(triangles<=20000,'Flower LOD exceeds 20k triangles')
            row={'level':lod,'nodeName':mesh_id+'_LOD'+str(lod),'vertices':len(points),'triangles':triangles,
                 'expectedBoundsCm':{'min':[min(p[k]for p in points)for k in range(3)],'max':[max(p[k]for p in points)for k in range(3)]},
                 'derivation':'Actual five-lobed curled corollas, opposite photo-veined ovate leaves and rooted curved branch tubes'}
            lods.append(row);lod_rows.append(row);all_meshes.append(mesh);morphology[row['nodeName']]=proof
        meshes.append({'id':mesh_id,'role':'ornamental','form':'flowering','flowerColor':'pink',
                       'heightCm':45,'placementPolicy':'explicit-only','materialKeys':sorted(mesh.parts),
                       'lods':lods,'composition':'Authored rose-periwinkle-like summer bedding clump; photographic leaf tissue, no scanned geometry or measured site species claim.'})
    output.mkdir(parents=True)
    glb=output/'glb/garden_pink_spatial_r1.glb';base.write_glb(glb,lod_rows,all_meshes)
    for row in meshes:row.update(glbPath=str(glb),glbSha256=base.sha(glb))
    inputs={str(p):base.sha(p)for p in (base_garden,library/'material-manifest.json',Path(__file__),HELPER)}
    for recipe in materials.values():
        for value in recipe['maps'].values():inputs[value['path']]=value['sha256']
    geometry={'schema':1,'units':'metres','owner':OWNER,'revision':'Spatial pink flower successor R1',
              'axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]','status':'OFFLINE_NOT_NATIVE_ACCEPTED',
              'meshes':meshes,'inputFiles':inputs}
    base.write(output/'geometry-manifest.json',geometry);base.write(output/'material-manifest.json',materials)
    base.write(output/'morphology-audit.json',{'owner':OWNER,'uvRect':LEAF_UV,'nodes':morphology,
               'reference':BOTANICAL_REFERENCE,'interpretation':'Morphology inspiration only; summer-bedding visual form, not a survey or vegetation schedule.'})
    base.write(output/'asset-manifest.json',{'schema':1,'owner':OWNER,'inputFiles':inputs,
               'sources':[{'kind':'original-authored-geometry','license':'Original project asset','generator':OWNER},
                          {'kind':'photographic-individual-leaf-tissue','license':'CC0-1.0','sourceUrl':source_materials['regional_green_leaf']['sourceUrl']}],
               'botanicalReference':BOTANICAL_REFERENCE,'scanClaim':False})
    replacements=[]
    for row in garden['ornamentalPlacements']:
        if not row['meshId'].startswith('garden_pink_r6_'):continue
        new=meshes[len(replacements)]
        radius=max(math.hypot(p[0],p[1])for mesh in all_meshes[len(replacements)*3:len(replacements)*3+3]for part in mesh.parts.values()for p in part['positions'])
        height_limit=min(45.,row['actualHeightCm']);scale=min(row['radiusCm']/radius,height_limit/45.)
        previous={k:deepcopy(row[k])for k in ('meshId','uniformScale','scale','radiusCm','heightCm','actualHeightCm')}
        row.update(meshId=new['id'],role='ornamental',form='flowering',flowerColor='pink',scale=[scale]*3,
                   uniformScale=scale,radiusCm=radius*scale,heightCm=45*scale,actualHeightCm=45*scale,
                   sourceMinimumZCm=0.,sourceMaximumZCm=45.,sourceCrownRadiusCm=radius,
                   previousFlowerEnvelope=previous,authoredRevision='Spatial pink flowers R1')
        replacements.append({'id':row['id'],'previous':previous,'newMeshId':new['id']})
    base.require(len(replacements)==2,'Expected exactly two existing pink heroes')
    for new,old in zip(garden['ornamentalPlacements'],original['ornamentalPlacements']):
        base.require(new['positionCm']==old['positionCm']and new['yawDeg']==old['yawDeg'],'A primary root moved')
        base.require(new['radiusCm']<=old['radiusCm']+1e-7 and new['heightCm']<=old['heightCm']+1e-7,'A flower envelope expanded')
    base.require(garden['gardenDetailPlacements']==original['gardenDetailPlacements'],'Detail planting changed')
    garden.update(owner=OWNER,revision='Spatial pink flowers R1; frozen R3 grasses and drifts retained',
                  generatedAt=datetime.now(timezone.utc).isoformat(),generatorSha256=base.sha(__file__),
                  flowerMasters={'path':str(output/'geometry-manifest.json'),'sha256':base.sha(output/'geometry-manifest.json')})
    garden['inputFiles'].update(inputs)
    garden['inputFiles'].update({str(p):base.sha(p)for p in (glb,output/'geometry-manifest.json',output/'material-manifest.json',output/'morphology-audit.json')})
    garden['gardenDetailAudit'].update(pinkHeroReplacements=2,sourceTexturePixelsChanged=False,
        pinkLeafGeometry='Paired, cupped and folded smooth ovate leaves; opaque photographic inner lamina',
        pinkFlowerGeometry='Five actual curled petal lobes with a recessed physical throat; no whole-flower cards')
    base.write(output/'garden-plan.json',garden)
    summary={'status':'OFFLINE_GENERATED_NATIVE_PENDING','owner':OWNER,'output':str(output),
             'gardenPlan':str(output/'garden-plan.json'),'meshes':2,'lods':6,'newMaterials':['garden_petal_rose'],
             'lodTriangles':{r['id']:[l['triangles']for l in r['lods']]for r in meshes},
             'primaryRootsPreserved':12,'detailsUnchanged':len(garden['gardenDetailPlacements']),
             'replacements':replacements,'glbSha256':base.sha(glb),'leafUvRect':LEAF_UV,'sourceTexturePixelsChanged':False}
    base.write(output/'summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--base-garden',required=True);parser.add_argument('--library',required=True)
    args=parser.parse_args();print(json.dumps(build(args.output,args.base_garden,args.library)))
