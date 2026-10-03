"""One unbound source proposal: 23 existing front roots -> whole original ferns.

No Unreal calls, source pixels, mesh exports, materials or saved scene changes.
The actual R38 membership is a historical reference, not the future selected
native base. All three reused masters have exactly one available native LOD0.
"""
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-foreground-fern-study-r40.py'
SCHEMA='brezi-source-only-23-front-garden-whole-original-fern-proposal-r40'
OUTPUT=ROOT/'output/unreal/exterior-garden-foreground-fern-20261002-r40-source-study'
FRONT=[[-1160.,-420.],[-980.,-520.],[-760.,-610.],[-685.,-560.]]
IDS=tuple('garden_drift_'+v for v in ('021','033','036','039','041','046','047','050','058','062','070','078','083','091','095','097','099','103','110','112','119','148','163'))
MODEL_IDS=('fern_02_a','fern_02_c','fern_02_d')
INPUTS={
 'periwinklePlan':('output/unreal/exterior-garden-periwinkle-20261002-r36-source-study/periwinkle-source-plan.json','93b4bc17203f10b5c14acd036dd942f8d2bf0b99ec1744e6638e7a29502a8b96'),
 'periwinkleNativeReport':('output/unreal/exterior-20261002-r36b/garden-periwinkle-native-report-r2.json','d2057c860c0b5135cd19beaee776145d89c3377a07ff08abee9537f6a15c765e'),
 'gardenPlan':('output/unreal/exterior-garden-organic-20261001-r1c-study/garden-plan.json','e599442a7ec887d16ee6e58c7466f4a34bf9a7880ef538bd2861c80ad39523e6'),
 'fernPlan':('output/unreal/exterior-garden-fern-only-20261002-r34-study/fern-only-source-plan.json','93839661f6b28054521ddf550388b8f2e5daa380fe93406e0c399a6ec807ceb2'),
 'fernDescriptor':('output/unreal/exterior-garden-fern-only-20261002-r34-study/geometry-descriptor.json','4b01fbcaf9d6fade4ea7ba2f3bd3285d0595efd9a3e56fdd1490d3bf6c955de4'),
 'fernNativeReport':('output/unreal/exterior-20261002-r34a/garden-fern-only-native-report.json','d233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8'),
 'currentMembershipReport':('output/unreal/exterior-20261002-r38b/soft-ground-native-report-r2.json','077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9'),
 'stepGuard':('scripts/unreal/exterior-garden-composition-step-guards-r3.py','09c628eecf5c8cfd766028243c1bc794c92098cec397d6eec12e675484338727')}

def require(ok,message):
 if not ok:raise RuntimeError(message)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def checked(row):
 p=Path(row['path']);require(p.is_absolute() and p.resolve()==p and not p.is_symlink() and pin(p)==row,'Immutable source reference differs: '+str(p));return p
def read(p):return json.loads(Path(p).read_text())
def binary_matrix_sha(matrices):
 h=hashlib.sha256()
 for matrix in matrices:
  require(len(matrix)==4 and all(len(plane)==4 for plane in matrix),'Recorded 4x4 matrices required')
  for plane in matrix:
   for value in plane:h.update(struct.pack('<d',value))
 return h.hexdigest()
def load_inputs():
 data={};pins={}
 for key,(rel,wanted)in INPUTS.items():
  p=ROOT/rel;require(sha(p)==wanted,'Frozen source basis changed: '+key);pins[key]=pin(p)
  if key!='stepGuard':data[key]=read(p)
 r36=data['periwinkleNativeReport'];r38=data['currentMembershipReport']
 for key,row in [('measurements',r36['newSourceNativeMeasurements']),('currentWitness',r38['savedActorWitness']),('currentRaw',r38['rawInstanceControlsSaved']),('contentInventory',r38['afterContentInventory'])]:
  data[key]=read(checked(row));pins[key]=row
 spec=importlib.util.spec_from_file_location('_r40_original_step_projection',checked(pins['stepGuard']));steps=importlib.util.module_from_spec(spec);spec.loader.exec_module(steps)
 data['stepGuard']=steps
 return data,pins

def inside_triangle(p,t):
 values=[(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])for a,b in zip(t,t[1:]+t[:1])]
 return all(v>=0 for v in values)or all(v<=0 for v in values)
def bed_edges(triangles):
 counts=Counter(tuple(sorted((tuple(a[:2]),tuple(b[:2]))))for t in triangles for a,b in zip(t,t[1:]+t[:1]))
 require(set(counts.values())<={1,2},'Original bed triangle union is nonmanifold')
 return [edge for edge,count in counts.items()if count==1]
def circle_guard(point,radius,triangles,steps,step_guard):
 require(radius>0 and all(math.isfinite(v)for v in [*point,radius]),'Finite positive source crown required')
 require(any(inside_triangle(point,t)for t in triangles),'Source root outside original unchanged bed')
 distance=min(step_guard.edge_distance(point,a,b)for a,b in bed_edges(triangles))
 require(radius<distance,'Complete source crown intersects original bed boundary')
 s=step_guard.circle_clearance(steps,point,radius)
 return {'bedBoundaryDistanceCm':distance,'bedCircleClearanceCm':distance-radius,'stepCircleClearanceCm':s['circleClearanceCm']}
def select_roots(rows,step_guard):
 selected=[v for v in rows if v['sourceBedId']=='DOM_01965' and v['sourceCameraProjection']['verticesInsideFrustum']>0 and
  min(step_guard.edge_distance(v['positionCm'][:2],a,b)for a,b in zip(FRONT,FRONT[1:]))<=60.]
 require(tuple(sorted(v['rootId']for v in selected))==IDS,'Exact source-visible original front-chain 23-root selection differs')
 return sorted(selected,key=lambda v:v['rootId'])

def membership_reference(data):
 r36=data['periwinkleNativeReport'];w=data['currentWitness'];raw=data['currentRaw'];measurements=data['measurements'];groups={}
 require(len(r36['newOwnedGroups'])==6 and sum(v['instances']for v in r36['newOwnedGroups'].values())==384,'Six actual original periwinkle groups/384 required')
 for model,row in r36['newOwnedGroups'].items():
  actor=row['actor'];require(actor in w and len(w[actor]['components'])==1,'Actual source group actor/component unavailable')
  component=w[actor]['components'][0];path=actor+'.Instances';measured=measurements[model]
  require(component['path']==path and component['mesh']==row['mesh'] and component['materials']==[row['material']]and component['instanceCount']==row['instances'],
   'Historical current mesh/material/group binding differs')
  require(measured['rootIds']==row['rootIds'] and digest(measured['recoveredValues'])==component['orderedInstanceTransformsSha256'],
   'Recorded root order/recovered values must bind actual current membership')
  require(binary_matrix_sha(measured['storedMatrices'])==raw[path]['rawMatrixBinary64Sha256'] and raw[path]['instances']==row['instances'] and raw[path]['numCustomDataFloats']==0,
   'Recorded original matrices/custom data must bind actual current group')
  require(len({len(measured[k])for k in ('rootIds','originalValues','inputValues','recoveredValues','storedMatrices')})==1,'Whole recorded constructor/recovered/matrix arrays required')
  groups[model]={'actor':actor,'componentPath':path,'rootIds':row['rootIds'],'mesh':row['mesh'],'material':row['material'],
   'actorWitness':w[actor],'actorWitnessSha256':digest(w[actor]),'rawControl':raw[path],'rawControlSha256':digest(raw[path]),
   'recordedConstructorArraysPin':data['periwinkleNativeReport']['newSourceNativeMeasurements']}
 return groups

def validate_future_membership(proposal,witness,raw):
 """A future saved base must authenticate fresh full groups before mutation.

 Passing recorded dictionaries here is source comparison, not a native read.
 """
 for row in proposal['historicalCurrentMembership']['groups'].values():
  require(row['actor']in witness and row['componentPath']in raw,'Fresh saved target group missing')
  require(witness[row['actor']]==row['actorWitness'] and digest(witness[row['actor']])==row['actorWitnessSha256'],
   'Future current group membership/mesh/material/policy changed')
  require(raw[row['componentPath']]==row['rawControl'] and digest(raw[row['componentPath']])==row['rawControlSha256'],
   'Future current raw matrices/order/main seed/custom data changed')
 return True

def model_contract(data,pins):
 r=data['fernNativeReport'];models={};packages={};project=Path(data['currentMembershipReport']['project'])
 for source in data['fernDescriptor']['models']:
  key=source['id'];require(key in MODEL_IDS,'Only three original whole fern forms allowed');record=r['nativeGeometryReadback'][key];binding=r['newOwnedGroups'][key]
  require(record['lodCount']==1 and record['triangles']==source['triangles'] and record['asset']==binding['mesh'] and record['fullOrderedNativeF32PositionUV0WindingVerified'],
   'Historical exact original available LOD0 proof required; no invented LOD chain')
  require(source['sourceOriginalWindingPreserved'] and not source['sourceTangentsPresent'],'Original fern source frame/index policy differs')
  points=source['expectedNativeVerticesCm'];require(len(points)==source['vertices'] and len(source['indices'])==source['triangles']*3,'Whole original source arrays required')
  require(min(p[2]for p in points)==0.,'Original R34 declared rooted bottom is zero')
  radius=max(math.hypot(p[0],p[1])for p in points);height=max(p[2]for p in points)
  require(radius>0 and height>0,'Whole fern source envelope required')
  models[key]={'mesh':binding['mesh'],'material':binding['material'],'availableLods':[{'index':0,'triangles':source['triangles'],'vertices':source['vertices'],
   'recordedNativeCornerSha256':record['nativeCornerSha256'],'sourceVertexArraySha256':digest(points),'sourceIndexArraySha256':digest(source['indices']),
   'sourceRadiusCm':radius,'sourceHeightCm':height}], 'originalSourceAttributeByteSha256':source['sourceAttributeByteSha256'],
   'originalSourceIndexByteSha256':source['sourceIndexByteSha256'],'sourceTangentsPresent':False,'originalProviderLodChainPresent':False,'newLodGeometryProposed':False}
  for asset in [binding['mesh'],binding['material']]:
   relative=asset.split('.')[0].removeprefix('/Game/')+'.uasset';expected=data['contentInventory'][relative];p=project/'Content'/relative
   require(sha(p)==expected['sha256'] and p.stat().st_size==expected['bytes'],'Actual current reused mesh/material package differs')
   packages[asset]=pin(p)
 require(set(models)==set(MODEL_IDS),'All and only three existing fern masters required')
 pins['reusedCurrentPackages']=packages
 return models

def derive(data,pins):
 source=data['periwinklePlan'];garden=data['gardenPlan'];require(source['activeDesign']==garden['activeDesign']=={'variant':'C','livingLayout':'B','heatingLayout':'B'},'C/B/B frame changed')
 require(garden['housePlacement']['streetSetbackMm']==garden['housePlacement']['eastSetbackMm']==3000,'Original both3000mm setbacks changed')
 groups=membership_reference(data);models=model_contract(data,pins);chosen=select_roots(source['proposedPlacements'],data['stepGuard'])
 steps=data['stepGuard'].validated_steps(garden['sourceStepTrianglesCm']);bed=garden['sourceMulchTrianglesCm']['DOM_01965'];placements=[]
 desc={m['id']:m for m in data['fernDescriptor']['models']};indices={}
 for ordinal,old in enumerate(chosen):
  root=old['rootId'];key=MODEL_IDS[ordinal%3];model=models[key];lod=model['availableLods'][0];original=old['originalRow'];radius=original['radiusCm']*.95
  scale=radius/lod['sourceRadiusCm'];ground=old['sourceContactPositionCm'][2];yaw=old['yawDeg'];center=old['sourceContactPositionCm'][:2]
  require(center==original['positionCm'][:2] and yaw==original['yawDeg'],'Original root XY/yaw source changed')
  clearance=circle_guard(center,original['radiusCm'],bed,steps,data['stepGuard']);angle=math.radians(yaw);co,si=math.cos(angle),math.sin(angle)
  points=[[center[0]+scale*(p[0]*co-p[1]*si),center[1]+scale*(p[0]*si+p[1]*co),ground+scale*p[2]]for p in desc[key]['expectedNativeVerticesCm']]
  require(all(math.hypot(p[0]-center[0],p[1]-center[1])<=original['radiusCm'] and any(inside_triangle(p,t)for t in bed)for p in points),
   'Every whole original source vertex must stay inside original circle and bed')
  require(min(p[2]for p in points)==ground,'Source ground contact differs')
  current=groups[old['model']];index=current['rootIds'].index(root);measured=data['measurements'][old['model']]
  indices.setdefault(old['model'],[]).append(index)
  placements.append({'rootId':root,'oldModel':old['model'],'oldActor':current['actor'],'oldComponentPath':current['componentPath'],'originalMemberIndex':index,
   'originalSourceRow':original,'historicalNativeInputValue':measured['inputValues'][index],'historicalNativeRecoveredValue':measured['recoveredValues'][index],
   'historicalNativeStoredMatrix':measured['storedMatrices'][index],'proposedModel':key,'mesh':model['mesh'],'material':model['material'],
   'positionCm':[center[0],center[1],ground],'yawDeg':yaw,'uniformScale':scale,'sourceGroundContactZCm':ground,
   'immutablePreR36CircleRadiusCm':original['radiusCm'],'proposedWholeFernRadiusCm':radius,'proposedWholeFernHeightCm':scale*lod['sourceHeightCm'],
   'oldPeriwinkleHeightCm':old['heightCm'],'oldPeriwinkleRadiusCm':old['radiusCm'],'allActualAvailableLodsChecked':[0],
   'fullSourceVerticesChecked':len(points),'sourceTriangles':lod['triangles'],'sourceWorldVertexArraySha256':digest(points),
   'wholeCircleInsideOriginalBedAndOutsideSteps':True,'circleClearance':clearance,'sourcePlantOcclusionVerified':False,'nativeVisibleCoverageVerified':False})
 filters={}
 for model,current in groups.items():
  remove=sorted(indices.get(model,[]));survivors=[i for i in range(len(current['rootIds']))if i not in remove];m=data['measurements'][model]
  filters[model]={'componentPath':current['componentPath'],'originalCount':len(current['rootIds']),'removeSourceIndices':remove,
   'retainedOriginalIndicesInOrder':survivors,'retainedRootIds':[current['rootIds'][i]for i in survivors],
   'retainedRecoveredValuesSha256':digest([m['recoveredValues'][i]for i in survivors]),'retainedRawMatrixBinary64Sha256':binary_matrix_sha([m['storedMatrices'][i]for i in survivors]),
   'mainRandomSeed':current['rawControl']['mainRandomSeed'],'numCustomDataFloats':0,'originalCustomDataSha256':current['rawControl']['customDataSha256'],
   'additionalRandomSeedRangesReadbackAvailable':False,'perInstanceShaderRandomIdentityPreservationClaimed':False,
   'futureRetentionRoute':'Filter/copy original wrapped PerInstanceSMData structs in original surviving order; no retained Transform/seed/custom-data setters'}
 require(sum(len(v['removeSourceIndices'])for v in filters.values())==23 and sum(len(v['retainedRootIds'])for v in filters.values())==361,'Only23 retirements/361 survivors required')
 return {'schema':SCHEMA,'schemaVersion':1,'owner':OWNER,'status':'unbound-source-only-23-whole-fern-front-proposal','activeDesign':garden['activeDesign'],
  'setbacksMm':{'street':3000,'right':3000},'sourceHousePlacement':garden['housePlacement'],'inputPins':pins,
  'futureSelectedNativeBase':None,'futureNativeProjectClone':None,'futureNativeReport':None,'futureRootImageDecision':None,
  'historicalCurrentMembership':{'report':pins['currentMembershipReport'],'witness':pins['currentWitness'],'rawControls':pins['currentRaw'],'groups':groups,'nativeFreshReadPerformedByThisProducer':False},
  'selection':{'sourceBedId':'DOM_01965','frontSourceChainCm':FRONT,'rootDistanceMaximumCm':60.,'sourceCamera':'exterior-garden','sourceVerticesInsideFrustumRequired':True,'rootIds':list(IDS)},
  'models':models,'placements':placements,'wholeOriginalGroupFiltersProposed':filters,
  'preservedSourceRootIds':{'original12Heroes':source['preservedOriginalHeroRootIds'],'original41Flowers':source['preservedOriginalFlowerRootIds'],'original36Ferns':source['preservedR34FernRootIds']},
  'preservedUnchangedScopes':['architecture','C/B/B and both3000mm setbacks','41 flowers','12 tall heroes','36 existing ferns','361 periwinkle survivors','lawn102011','both original mulch beds','yard/road/private/cultivated masks','all old light/material/pixel/mesh packages'],
  'sourceBudget':{'rootsRetired':23,'rootsAdded':23,'periwinklesRetained':361,'fernVariantCounts':dict(Counter(v['proposedModel']for v in placements)),
   'instancedOriginalFernTriangles':sum(v['sourceTriangles']for v in placements),'retiredInstancedOriginalPeriwinkleTriangles':sum(v['sourceTriangles']for v in chosen),
   'proposedFernHeightRangeCm':[min(v['proposedWholeFernHeightCm']for v in placements),max(v['proposedWholeFernHeightCm']for v in placements)],
   'oldPeriwinkleHeightRangeCm':[min(v['oldPeriwinkleHeightCm']for v in placements),max(v['oldPeriwinkleHeightCm']for v in placements)],
   'newMeshes':0,'newMaterials':0,'newTexturePixels':0,'availableLodsPerMaster':1,'sourceRadiusClearanceScaleFraction':.95},
  'selectedViewAppearanceRisk':'Smaller, lower whole fern silhouettes can further expose existing mulch. A source circle/vertex fit does not justify native replacement; root must first choose whether a matched original garden trial is worthwhile after R39 imagery, and accept only actual before/after originals.',
  'nativeExecutionRequirements':['Bind a NEW actual selected saved report/process/current-byte proof and root image decision after R39 imagery; no historical report adoption as futurebase',
   'Fresh full target actor/member/mesh/material/raw controls must match historical reference before mutation',
   'Capture current original wrapped XYZ/rotation; copy XY/rotation directly and set declared rooted-ground Z/uniform scale in unregistered meshless HISM, measuring input/recovered/stored arrays before old mutation',
   'Decode every vertex of ALL actual available LOD0 for reused3 meshes, fit original preR36 circles and original bed/step masks from actual measured matrices before/save/reload',
   'Retain 361 wrapped original structs in order with mainseed/custom unchanged; unknown AdditionalRandomSeeds ranges remain unverified',
   'Do not import/export/create meshes, materials, textures or missing LOD1/2; preserve all original assets and all other groups/policies',
   'Native full counterfactual, map-only delta, saved unloaded/reloaded proof and fixed-camera original PNG review required'],
  'limits':{'artistAuthoredUnsurveyedSourceContact':True,'sourceCircleAreaIsOpaqueLeafCoverage':False,'freshNativeGeometryDecode':False,'newNativeFrameSerializationMeasured':False,
   'sourceNormalUvIndexBytesEdited':False,'sourceOriginalR34BottomShiftUnchanged':True,'nativeNormalTangentReadbackAvailable':False,'nativeShaderRandomPreservationClaimed':False,
   'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'nativeApplied':False,'gpuExecuted':False}}

def preview(proposal,data):
 bed=data['gardenPlan']['sourceMulchTrianglesCm']['DOM_01965'];poly=bed_edges(bed);x0,x1=-1210,-635;y0,y1=-650,-295
 def xy(p):return[(p[0]-x0)*1.6,70+(p[1]-y0)*1.6]
 rows=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="750" viewBox="0 0 1000 750"><rect width="100%" height="100%" fill="#faf9f5"/>',
  '<text x="24" y="28" font-size="22" font-family="sans-serif">R40: 23 whole original ferns at existing front roots</text>',
  '<text x="24" y="51" font-size="14" font-family="sans-serif">SOURCE LAYOUT ONLY • one actual LOD0/master • no native/alpha/visible coverage claim</text>']
 for t in bed:rows.append('<polygon points="'+' '.join(','.join(map(str,xy(p)))for p in t)+'" fill="#dac9b2" stroke="none"/>')
 for a,b in poly:
  a,b=xy(a),xy(b);rows.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="#655348" stroke-width="2"/>')
 colors={'fern_02_a':'#4c7a48','fern_02_c':'#447866','fern_02_d':'#748c48'}
 for row in proposal['placements']:
  x,y=xy(row['positionCm']);r=row['proposedWholeFernRadiusCm']*1.6;hard=row['immutablePreR36CircleRadiusCm']*1.6
  rows.append(f'<circle cx="{x}" cy="{y}" r="{hard}" fill="none" stroke="#916d53" stroke-dasharray="3,3"/><circle cx="{x}" cy="{y}" r="{r}" fill="{colors[row["proposedModel"]]}" fill-opacity=".20" stroke="{colors[row["proposedModel"]]}"/><circle cx="{x}" cy="{y}" r="2.5" fill="#222"/><text x="{x+4}" y="{y-4}" font-size="9" font-family="sans-serif">{row["rootId"][-3:]}</text>')
 rows.append('<text x="24" y="684" font-size="14" font-family="sans-serif">Dashed: unchanged pre-R36 safety circles. Color: source whole-plant radial envelopes, not leaf fill.</text>')
 budget=proposal['sourceBudget'];rows.append(f'<text x="24" y="708" font-size="14" font-family="sans-serif">A/C/D={budget["fernVariantCounts"]} • unchanged ground contact/XY/yaw • 361 periwinkle roots retained</text>')
 rows.append('</svg>');return '\n'.join(rows)

def main():
 require(not OUTPUT.exists(),'Exclusive NEW source output required')
 data,pins=load_inputs();proposal=derive(data,pins);OUTPUT.mkdir()
 (OUTPUT/'source-layout.svg').write_text(preview(proposal,data))
 proposal['sourceLayout']=pin(OUTPUT/'source-layout.svg');proposal['producerSource']=pin(ROOT/OWNER)
 p=OUTPUT/'foreground-fern-source-plan.json';p.write_text(json.dumps(proposal,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'sourcePlan':pin(p),'layout':proposal['sourceLayout'],'sourceBudget':proposal['sourceBudget'],'nativeBase':None,'nativeApplied':False}))
if __name__=='__main__':main()
