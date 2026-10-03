"""CPU-only geometry/usage safeguards for frozen R28 local-yard layout.

No UE imports, native receipt invention, historical writes or shader changes.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-source-guards-r28.py'
PLAN=ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-source-plan.json'
PLAN_SHA='f9b61cb39598c46546a7d141b98da0188366256a75ac6fd9e604e77e39fae263'
s=importlib.util.spec_from_file_location('r28_frozen_layout_source',ROOT/'scripts/unreal/exterior-context-yard-study-r28.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
require,read,sha,pin,digest=p.require,p.read,p.sha,p.pin,p.digest
from shapely.geometry import Point,shape,Polygon
from shapely.ops import unary_union


def validate_geometry(layout,masks,buildings,models):
 require(len(layout['yards'])==3 and {r['buildingSourceId']for r in layout['yards']}==set(p.TARGETS),'Exact three target yards required')
 require(len(layout['surfaces'])==12 and len({r['id']for r in layout['surfaces']})==12,'Exact twelve declared layout surfaces required')
 blocked=unary_union([m.buffer(20)for m in masks.values()])
 floors={};plant_ids=set();by_building={b['id']:b for b in buildings['buildings']}
 for yard in layout['yards']:
  identity=yard['buildingSourceId'];original=by_building[identity]
  require(yard['sourceBuildingSha256']==digest(original)and yard['entrance']==p.entrance(original),'Frozen original volume/entrance identity differs')
  require(yard['perimeterIsLegalParcelBoundary']is False and yard['streetConnectionProposed']is False
   and yard['drivewayOrVehicleAccessVerified']is False and yard['authoredLocalEnvelopeCm']==700,'Artist local envelope widened into legal/access claim')
  footprint=unary_union([Polygon(r[0],r[1:])for r in original['polygonsCm']]);domain=footprint.buffer(700).difference(blocked)
  rows=[r for r in layout['surfaces']if r['buildingSourceId']==identity]
  require({r['role']for r in rows}=={'entry_walk','service_court','soil_bed','worn_edge'},'Functional surface roles changed')
  shapes={r['role']:shape(r['domainCm'])for r in rows};floors[identity]=shapes
  for row in rows:
   geometry=shapes[row['role']]
   require(geometry.is_valid and geometry.area>0 and geometry.difference(domain).area<1e-5,'Source floor crosses source-building/road/private/cultivated domain')
   require(abs(row['sourceAreaM2']-geometry.area/10000)<1e-10 and row['materialKey']=={'entry_walk':'context_track','service_court':'context_track','soil_bed':'context_garden_soil','worn_edge':'context_soil_exposure'}[row['role']],
    'Surface area/material usage differs')
   require(row['nativeApplied']is False and row['sourceVerticesMustUseHighestExistingGround']is True,'Source layout cannot claim native result or fabricated ground')
  require(all(a.intersection(b).area<1e-5 for i,a in enumerate(shapes.values())for b in list(shapes.values())[i+1:]),'Functional floor regions overlap')
  door=Point(yard['entrance']['doorCenterCm'][:2]);require(door.distance(shapes['entry_walk'])<40,'Entry walk is disconnected from original modeled door')
  require(shapes['service_court'].distance(shapes['entry_walk'])<1e-5,'Court is disconnected from purposeful entry walk')
  expected_roots=[r['id']for r in layout['planting']if r['buildingSourceId']==identity]
  require(yard['plantIds']==expected_roots,'Planting is not assigned to its exact yard')
  plant_ids.update(expected_roots)
 require(len(layout['planting'])==13 and len(plant_ids)==13,'Exact selected thirteen shrub roots required')
 minimum=math.inf
 for root in layout['planting']:
  require(root['modelId']in('shrub_broadleaf_a','shrub_broadleaf_b','shrub_broadleaf_c')and root['nativeApplied']is False,
   'Unselected master or native claim introduced')
  model=models[root['modelId']];scale=root['uniformScale']
  require(type(scale)in(float,int)and math.isfinite(scale)and scale>0
   and len(root['positionCm'])==3 and all(type(v)in(float,int)and math.isfinite(v)for v in root['positionCm'])
   and type(root['yawDegrees'])in(float,int)and math.isfinite(root['yawDegrees']),'Nonfinite or inverted planting transform')
  radius=max(math.hypot(max(abs(l['expectedBoundsCm']['min'][0]),abs(l['expectedBoundsCm']['max'][0])),max(abs(l['expectedBoundsCm']['min'][1]),abs(l['expectedBoundsCm']['max'][1])))for l in model['lods'])*scale
  require(radius==root['radialEnvelopeCm']and scale==root['heightCm']/model['heightCm'],'Source full-LOD conservative crown/height fit differs')
  crown=Point(root['positionCm'][:2]).buffer(radius/math.cos(math.pi/128),quad_segs=32)
  require(floors[root['buildingSourceId']]['soil_bed'].covers(crown)and crown.intersection(blocked).area<1e-5,
   'Whole shrub envelope crosses soil-bed or exact source exclusion')
  for mask in masks.values():minimum=min(minimum,Point(root['positionCm'][:2]).distance(mask)-radius)
  require(root['wholeCrownInsideAuthoredBedAndAllExclusions']is True and root['sourceGround']['measuredElevation']is False,'Source planting scope/elevation claim differs')
  require(root['positionCm'][2]==root['sourceGround']['zCm']-min(l['expectedBoundsCm']['min'][2]for l in model['lods'])*scale+.6,
   'Source all-LOD basal ground contact differs')
 for i,a in enumerate(layout['planting']):
  for b in layout['planting'][i+1:]:
   require(math.dist(a['positionCm'][:2],b['positionCm'][:2])>=a['radialEnvelopeCm']+b['radialEnvelopeCm']+12,
    'Authored shrubs overlap their conservative full-LOD envelopes')
 return {'surfaces':12,'surfaceAreaM2':sum(r['sourceAreaM2']for r in layout['surfaces']),'shrubs':13,
  'minimumConservativeCrownClearanceToUnbufferedExclusionsCm':minimum,'buildingFootprintChanges':0,'originalRootChanges':0,
  'roadConnectionsOrLegalYardBoundariesClaimed':False,'nativeApplied':False,'nativeAppearanceAccepted':False,'performanceAccepted':False}


def load_source():
 require(sha(PLAN)==PLAN_SHA,'Frozen root-reviewed layout plan changed')
 plan=read(PLAN);require(plan['schema']=='brezi-context-yard-artistic-source-layout-r28'and plan['owner']==p.OWNER
  and plan['status']=='source-only-layout-review-native-pending','Typed source layout differs')
 for row in plan['inputFiles'].values():require(sha(row['path'])==row['sha256']and Path(row['path']).stat().st_size==row['bytes'],'Original source/photographic input changed')
 require(plan['generator']==pin(ROOT/p.OWNER)and Path(plan['snapshot']['path']).read_bytes()==(ROOT/p.OWNER).read_bytes(),'Frozen producer snapshot differs')
 for key in ('layout','masks'):require(pin(plan[key]['path'])==plan[key],'Source payload changed')
 data={k:read(row['path'])for k,row in plan['inputFiles'].items()if k in p.SOURCES and k!='doorProducer'}
 layout=read(plan['layout']['path']);masks={k:shape(v)for k,v in read(plan['masks']['path']).items()}
 require({k:json.loads(v)for k,v in data['ecology']['exclusionDomainsCm'].items()}==read(plan['masks']['path']),'Source exclusions are not the exact retained domains')
 models={m['id']:m for m in data['plantGeometry']['meshes']};audit=validate_geometry(layout,masks,data['buildings'],models)
 require(plan['audit']['shrubs']==audit['shrubs']and plan['audit']['surfaceCount']==audit['surfaces']
  and plan['audit']['surfaceAreaM2']==audit['surfaceAreaM2'],'Root-reviewed source census differs')
 require(layout['existingMaterialReferences']=={k:data['nativeR16']['materials']['materials'][k]for k in layout['existingMaterialReferences']},'Existing source PBR graph/texture recipe altered')
 return plan,layout,masks,data,models,audit


if __name__=='__main__':
 plan,layout,masks,data,models,audit=load_source();print(json.dumps({'selectedSourcePlan':pin(PLAN),'sourceMaskAudit':audit}))
