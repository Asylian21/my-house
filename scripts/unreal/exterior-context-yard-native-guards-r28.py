"""Stdlib-only yard scope guards. Actual clean R27 is required, never guessed.

Source geometry and GPU/native receipt evidence remain distinct. This module
does not import Unreal, the source producer or its scientific dependencies.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-native-guards-r28.py'
PREFIX='/Game/Brezi/ContextYard20261002R28'
TAG='BreziContextYard20261002R28'
NODE_TAG='BreziYardR28:'
BASE=ROOT/'output/unreal/exterior-20261002-r27a'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r28a'
STUDY=ROOT/'output/unreal/exterior-context-yard-20261002-r28-geometry-study'
SOURCE=STUDY/'yard-geometry-plan.json'
SOURCE_SHA='f0f03736fc1c6d0992e2746626e35750dcacd575770b06f5f1308511a0358cb3'
BASE_SHA='5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498'
SCHEMA='brezi-context-yard-purposeful-ground-and-shrubs-r28'
ROLES=('entry_walk','service_court','soil_bed','worn_edge')
MODELS=('shrub_broadleaf_a','shrub_broadleaf_b','shrub_broadleaf_c')


def module(name,file):
 path=ROOT/'scripts/unreal'/file;spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


clean=module('yard_r28_frozen_clean_guard','exterior-realism-clean-integration-guards-r27.py')
require,read,sha,pin,check_pin,digest=(getattr(clean,k)for k in('require','read','sha','pin','check_pin','digest'))
g=clean.g
require(sha(ROOT/clean.OWNER)=='50f670f19e28753dab890577f07755699078c1025ca99b5622ac523b12e078ae','Frozen clean source guard changed')


def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def finite(v,width):return isinstance(v,list)and len(v)==width and all(type(x)in(float,int)and math.isfinite(x)for x in v)
def cyclic(face):return min(tuple(face[i:]+face[:i])for i in range(3))
def native_points(mesh):return [[f32(f32(v/100)*100)for v in p]for p in mesh['verticesCm']]
def corners(mesh):
 points=native_points(mesh);uv0=[[f32(v)for v in p]for p in mesh['uv0']];uv1=[[f32(v)for v in p]for p in mesh['uv1']]
 return [cyclic([tuple(points[i]+uv0[i]+uv1[i])for i in mesh['indices'][j:j+3]])for j in range(0,len(mesh['indices']),3)]


def index_helper():
 path=ROOT/'scripts/unreal/exterior-grove-substrate-native.py';require(sha(path)=='c27e3b935d4486e6150e262a8309223e9f72e0ef6abb9f648af5c897283f692e','Frozen exact source polygon helper changed')
 return module('yard_r28_frozen_polygons',path.name)


def ground_check(witness,xy,data):
 source=witness['sourceGround']if'sourceGround'in witness else witness
 require(source['measuredElevation']is False,'Artist ground cannot claim surveyed elevation')
 meshes=[m for group in('context','terrain')for m in data[group]['meshes']if m['id']==source['meshId']]
 require(len(meshes)==1 and meshes[0]['material']==source['material'],'Exact source ground triangle missing')
 mesh=meshes[0];ordinal=source['triangleOrdinal'];weights=source['barycentric']
 require(type(ordinal)is int and 0<=ordinal<len(mesh['indices'])//3 and finite(weights,3)
  and min(weights)>=-1e-7 and abs(sum(weights)-1)<1e-7,'Ground source barycentric witness malformed')
 tri=[mesh['verticesCm'][i]for i in mesh['indices'][ordinal*3:ordinal*3+3]]
 position=[sum(point[k]*w for point,w in zip(tri,weights))for k in range(3)]
 require(max(abs(position[k]-xy[k])for k in(0,1))<1e-6 and abs(position[2]-source['zCm'])<1e-7,'Ground source contact is not its actual triangle')
 return source['zCm']


def load_source():
 require(sha(SOURCE)==SOURCE_SHA,'Frozen one-candidate yard geometry source changed')
 plan=read(SOURCE);require(plan['schema']=='brezi-context-yard-four-source-ground-meshes-r28'
  and plan['status']=='source-geometry-ready-actual-saved-clean-base-pending','Typed source geometry plan differs')
 for key in('nativeApplied','nativeAppearanceAccepted','performanceAccepted','shippingAccepted'):require(plan[key]is False,'Source plan claims native acceptance')
 require(plan['generator']['sha256']==plan['snapshot']['sha256']and check_pin(plan['generator'])!=check_pin(plan['snapshot']),'Exact independent source generator snapshot missing')
 layout_plan=read(check_pin(plan['sourceLayout']));require(plan['sourceLayout']['sha256']=='f9b61cb39598c46546a7d141b98da0188366256a75ac6fd9e604e77e39fae263','Reviewed layout changed')
 require(layout_plan['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and layout_plan['setbacksMm']=={'street':3000,'east':3000},'C/B/B3000 changed')
 layout=read(check_pin(layout_plan['layout']));masks=read(check_pin(layout_plan['masks']))
 data={k:read(check_pin(v))for k,v in layout_plan['inputFiles'].items()if k in('context','terrain','nativeR16','plantGeometry')}
 for row in layout_plan['inputFiles'].values():check_pin(row)
 require(layout['existingMaterialReferences']=={k:data['nativeR16']['materials']['materials'][k]for k in layout['existingMaterialReferences']},'Original ground PBR recipes differ')
 geometry=read(check_pin(plan['geometry']));recipes=read(check_pin(plan['materialCopyRecipes']));meshes=geometry['meshes']
 require([m['role']for m in meshes]==list(ROLES)and len(layout['surfaces'])==12 and len(layout['planting'])==13,'Exact4 meshes/12 regions/13 shrubs required')
 polygons=index_helper();blocked={k:polygons._PolygonIndex(v)for k,v in masks.items()};sources={r['id']:r for r in layout['surfaces']}
 triangles=0
 for mesh in meshes:
  vs=mesh['verticesCm'];ids=mesh['indices'];alpha=mesh['uv1'];normals=mesh['normals']
  require(mesh['id']=='context_yard_r28_'+mesh['role']and mesh['winding']=='clockwise'and len(vs)==len(mesh['uv0'])==len(alpha)==len(normals)
   and len(vs)==len(mesh['sourceGroundVertexWitnesses'])and len(ids)%3==0,'Closed source surface attributes differ')
  require(mesh['collision']=='NoCollision'and mesh['canEverAffectNavigation']is False and mesh['castShadow']is False
   and mesh['nanite']is False and mesh['maxDrawDistanceCm']==24000 and mesh['nativeApplied']is False,'Ground surface runtime scope differs')
  require(all(type(i)is int and 0<=i<len(vs)for i in ids),'Ground surface index malformed')
  for i,(point,uv,coverage,normal)in enumerate(zip(vs,mesh['uv0'],alpha,normals)):
   require(finite(point,3)and finite(uv,2)and finite(coverage,2)and finite(normal,3)
    and normal[2]>0 and abs(sum(v*v for v in normal)-1)<1e-12,'Nonfinite/inverted surface normal or attribute')
   require(uv==[point[0]/100,point[1]/100]and 0<=coverage[0]<=1 and coverage[1]==0,'Ground UV/feather channel differs')
   w=mesh['sourceGroundVertexWitnesses'][str(i)];row=sources[w['surfaceId']]
   require(row['role']==mesh['role']and point[2]==ground_check(w,point,data)+w['reliefCm']
    and 0<=w['reliefCm']<=row['maximumAddedReliefCm'],'Actual source triangle/microrelief differs')
   # The reviewed source uses GEOS polygonal20cm buffers; their round-corner
   # chords have a measured minimum19.976cm Euclidean clearance. Exact region
   # containment is checked per whole triangle below, rather than substituting
   # an ideal circular-distance threshold for those frozen polygons.
   require(all(not mask.contains(point[:2])for mask in blocked.values()),'Source surface intersects retained exclusions')
  require(len(mesh['sourceSurfaceRanges'])==3,'Exact three original yard regions per surface role required')
  for span in mesh['sourceSurfaceRanges']:
   row=sources[span['surfaceId']];require(span['sourceDomain']==row['domainCm']and row['role']==mesh['role'],'Source surface range points at another region')
   domain=polygons._PolygonIndex(row['domainCm'])
   for j in range(span['firstTriangle']*3,(span['firstTriangle']+span['triangles'])*3,3):
    tri=[vs[i][:2]for i in ids[j:j+3]];require(polygons._cross(*tri)<-1e-8,'Source ground topology became degenerate or inverted');domain.triangle_inside(tri)
  triangles+=len(ids)//3
 require(triangles==2969 and sum(len(m['verticesCm'])for m in meshes)==2191,'Selected source surface topology census changed')
 models={m['id']:m for m in data['plantGeometry']['meshes']};native={m['id']:m for m in data['nativeR16']['savedPlantReadback']}
 soil={r['buildingSourceId']:polygons._PolygonIndex(r['domainCm'])for r in layout['surfaces']if r['role']=='soil_bed'}
 for root in layout['planting']:
  require(root['modelId']in MODELS and root['nativeMesh']==native[root['modelId']]['mesh']and root['nativeMaterials']==native[root['modelId']]['materials']
   and root['sourceTrianglesByLOD']==native[root['modelId']]['lodTriangles'],'Existing shrub native master/material route differs')
  require(finite(root['positionCm'],3)and math.isfinite(root['yawDegrees'])and root['uniformScale']>0,'Planting transform malformed')
  model=models[root['modelId']];scale=root['uniformScale'];radius=root['radialEnvelopeCm'];center=root['positionCm'][:2]
  require(scale==root['heightCm']/model['heightCm']and radius>=max(math.hypot(*[max(abs(l['expectedBoundsCm'][side][k])for side in('min','max'))for k in(0,1)])for l in model['lods'])*scale-1e-12,'Whole-LOD shrub envelope differs')
  require(soil[root['buildingSourceId']].contains(center)and soil[root['buildingSourceId']].distance(center,radius+1)>=radius,'Planting crown leaves source bed')
  require(all(not mask.contains(center)and mask.distance(center,radius+21)>radius+20 for mask in blocked.values()),'Whole shrub crown crosses original exclusions')
  ground_check(root['sourceGround'],root['positionCm'],data)
  require(root['positionCm'][2]==root['sourceGround']['zCm']-min(l['expectedBoundsCm']['min'][2]for l in model['lods'])*scale+.6,'All-LOD source basal placement differs')
 require([r['id']for r in recipes]==['context_yard_r28_soil_bed','context_yard_r28_worn_edge'],'Exact two copied feather recipes required')
 for row,key in zip(recipes,('context_garden_soil','context_soil_exposure')):
  original=layout['existingMaterialReferences'][key];require(row['sourceNativeMaterial']==original['asset']and row['sourceGraphSha256']==original['graphSha256']
   and row['originalGraph']==original['graph']and row['baseRecipe']==original['recipe']and row['newNodes']==3 and row['newTextureObjects']==0,'Original photo/world-ground roots changed')
  check_pin(row['installedDitherFunction'])
 return {'plan':plan,'layoutPlan':layout_plan,'layout':layout,'data':data,'geometry':geometry,'recipes':recipes,'models':models,'nativeMasters':native,'polygons':polygons,'masks':blocked,'soil':soil}


def saved_base():
 path=BASE/'realism-clean-integration-native-report.json';require(path.exists()and sha(path)==BASE_SHA,'Exact actual saved clean R27 is required')
 report=read(path);plan,bundle=clean.validate_plan()
 owner='scripts/unreal/exterior-realism-clean-integration-native-r27.py'
 require(report['schema']==clean.SCHEMA and report['owner']==owner and report['status']=='verified-saved-four-donor-clean-exterior-realism-integration'
  and report['output']==str(BASE)and report['project']==str(BASE/'Project/BreziTwin')and report['selectedPlan']==pin(clean.PLAN)
  and report['savedMapUnloadedReloaded']is True and report['originalR16Unchanged']is True,'Only actual saved clean R27 may supply the yard base')
 process=clean.actual_terminal(path,BASE/'realism-clean-integration-native-process.json',owner,'realism-clean-integration-native')
 before=read(check_pin(report['beforeActorWitness']));saved=read(check_pin(report['savedActorWitness']))
 expected=clean.compose_all_expected(bundle['expectedOriginal'],bundle['templates'],report['addedActorIdentityMap'])
 require(before==bundle['before']and saved==expected and digest(saved)==report['expectedActorWitnessSha256']==report['savedActorWitnessSha256']
  and len(saved)==5343,'Saved clean original actor counterfactual differs')
 require(report['actualFullSceneHismComponents']==2309 and report['actualFullSceneHismInstances']==676944
  and report['scopedMaterialGraphs']==54 and report['scopedTextureObjects']==77,'Actual clean base census differs')
 materials=read(check_pin(report['materialsSaved']));require(materials==read(check_pin(report['materialsBefore']))
  and len(materials['verifiedMaterialAssets'])==materials['scopedMaterialGraphs']==54
  and len(materials['verifiedTextureAssets'])==materials['scopedTextureObjects']==77,'Saved54/77 original/copied material proof differs')
 old=bundle['base']['materials'];require(set(materials['original']['graphs'])==set(old['materials'])
  and all(v['asset']==old['materials'][k]['asset']and v['graphSha256']==old['materials'][k]['graphSha256']for k,v in materials['original']['graphs'].items())
  and materials['leaf']==bundle['reports']['leaf']['variants']and materials['neighbor']==bundle['reports']['neighbors']['materials']
  and materials['foreground']==bundle['reports']['foreground']['newMaterial'],'Saved material bindings differ from exact four donor/original graphs')
 grass_before=read(check_pin(report['originalGrassControlsBefore']));require(grass_before==read(check_pin(report['originalGrassControlsSaved']))
  and len(grass_before)==4 and sum(r['instances']for r in grass_before.values())==8949
  and report['originalGrassMemberMutationApisCalled']is False and report['seedRangeMutationApisCalled']is False,'Original grass matrix/control protection differs')
 content=read(check_pin(report['afterContentInventory']));protected=read(check_pin(report['protectedProjectProof']));require(len(content)==4034 and len(protected)==132,'Actual clean project inventory differs')
 require(clean.validate_content(bundle['content'],content,bundle['packages'],report['diagnosticViewpoints']['sha256'])==report['assetDelta'],'Saved59 packages/map/viewpoint delta differs')
 helper=module('yard_r28_actual_clean_native',Path(owner).name);require(pin(ROOT/owner)==plan['ownedSources']['native']['live'],'Actual clean native helper changed')
 return {'report':report,'reportPin':pin(path),'process':process,'cleanPlan':plan,'cleanBundle':bundle,'native':helper,
  'witness':saved,'content':content,'protected':protected,'materials':materials}


def validate_graph_copy(original,variant):
 additions=[n for n in variant['nodes']if n['role'].startswith(NODE_TAG)];by={n['role'][len(NODE_TAG):]:n for n in additions}
 require(len(additions)==3 and len(variant['nodes'])==len(original['nodes'])+3
  and [n for n in variant['nodes']if not n['role'].startswith(NODE_TAG)]==original['nodes'],'Only three new opacity feather nodes allowed')
 require(set(by)=={'uv1','coverage-r','temporal-dither'}and by['uv1']['class']=='MaterialExpressionTextureCoordinate'
  and by['uv1']['values']=={'coordinate_index':1,'u_tiling':1.,'v_tiling':1.}
  and by['coverage-r']['class']=='MaterialExpressionComponentMask'and by['coverage-r']['values']=={'r':True,'g':False,'b':False,'a':False}
  and by['coverage-r']['inputs']==[['None',NODE_TAG+'uv1','']],'UV1 edge alpha routing differs')
 dither=by['temporal-dither'];alpha=[v for v in dither['inputs']if'alpha'in v[0].lower()]
 require(dither['class']=='MaterialExpressionMaterialFunctionCall'and dither['values']['material_function']=='/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA'
  and len(alpha)==1 and alpha[0][1:]==[NODE_TAG+'coverage-r','']and all(v[1]is None for v in dither['inputs']if v not in alpha),'Native temporal dither route differs')
 require(variant['roots']['OPACITY_MASK']==[NODE_TAG+'temporal-dither','Result']and all(v==variant['roots'][k]for k,v in original['roots'].items()if k!='OPACITY_MASK'),'Existing PBR roots changed')
 require(variant['flags']['blend_mode']=='<BlendMode.BLEND_MASKED: 1>'and variant['flags']['opacity_mask_clip_value']==.5
  and all(v==variant['flags'][k]for k,v in original['flags'].items()if k not in('blend_mode','opacity_mask_clip_value')),'Original graph flags changed outside new opacity mask')


def validate_content(before,after,packages):
 require(len(before)==4034 and len(after)==4043 and len(packages)==len(set(packages))==9,'Only9 new yard packages allowed')
 require(set(after)==set(before)|set(packages)and all(v.startswith('Brezi/ContextYard20261002R28/')and v.endswith('.uasset')for v in packages),'Yard package namespace widened')
 require([k for k in before if before[k]!=after[k]]==['Brezi/Maps/Brezi.umap'],'Original Content changed outside own candidate map')
 return {'changedOriginalFiles':['Brezi/Maps/Brezi.umap'],'newPackageFiles':sorted(packages),'originalContentFiles':4034,'savedContentFiles':4043,'newPackages':9}
