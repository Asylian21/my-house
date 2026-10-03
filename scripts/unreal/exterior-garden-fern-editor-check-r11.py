"""Stdlib CPU-only saved R25 R2 single-fern proof for the Editor reader.

Validates actual receipt/source counterfactuals. Does not load Unreal or grant
pixel-format, tangent, appearance, performance or Shipping acceptance.
"""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-fern-editor-check-r11.py'
HELPER='scripts/unreal/exterior-garden-fern-native-r25-r2.py'
HELPER_SHA='010f7c38aeb0af81934c36b6bddbcd48f49b9bfc3703531833f2091c111d42a5'
GUARD_SHA='cd8bae75d24c5199385763865561abe5bfeca471e5b1431b83d66161aced90de'
MATERIAL_SHA='07de6de2e384802228b6316a15aca0fe327525084eb9141615508b1040fda34f'
REPORT_SHA='dc96a4927a0b0ec0e8abb3740e7a918e65a6ba6a0881ba77bc29275c1445e0b2'
# These two actual native report annotations differ from host libm arithmetic:
# radius by one ULP and its subtracted boundary clearance by twelve ULPs.
# No epsilon is applied. All controls stay exact and full source masks are
# independently recomputed by frozen footprint() below.
NATIVE_DERIVED_FOOTPRINT={
 'actualNativeAllVertexRadiusCm':54.48800620174227,
 'fullContainingCircleToOriginalBedBoundaryClearanceCm':14.521993798257945}
s=importlib.util.spec_from_file_location('r11_exact_saved_fern_native',ROOT/HELPER)
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
g=n.guard
m=g.module('r11_exact_fern_material_guard',ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py')


def validate_recorded_footprint(root,computed):
 g.require(all(root[k]==v for k,v in NATIVE_DERIVED_FOOTPRINT.items()),'Actual native derived footprint annotations changed')
 g.require({k:v for k,v in root.items()if k not in NATIVE_DERIVED_FOOTPRINT}
  =={k:v for k,v in computed.items()if k not in NATIVE_DERIVED_FOOTPRINT},
  'Saved full1660-vertex source footprint/height controls differ')


def validate_saved(r,bundle,base,preflight):
 require=g.require;load=lambda key:g.read(g.checked(r[key]));output=g.NATIVE_OUTPUT
 require(r['schema']==g.SCHEMA and r['owner']==HELPER and r['status']==n.STATUS
  and r['output']==str(output)and r['project']==str(output/'Project/BreziTwin'),'Only actual owned R25b R2 fern result eligible')
 require(r['selectedSourcePlan']==g.pin(g.SOURCE)and r['baseNativeReport']==base['reportPin']
  and r['baseNativeProcess']==base['process']and r['projectClone']==g.pin(output/'garden-fern-project-clone.json')
  and r['inputFiles']==preflight['inputFiles']and r['windingRepair']==preflight['windingRepair']
  and r['sourceGeometry']==preflight['sourceGeometry'],'Actual source/native base/geometry repair scope differs')
 require(r['activeDesign']==bundle['plan']['activeDesign']and r['setbacksMm']=={'street':3000,'east':3000},'C/B/B3000 changed')
 for key in ('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified',
  'nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyReloaded','nativeMeshPackagesIndependentlyReloaded',
  'inheritedPlantNativeLodsRemeasuredHere'):
  require(r[key]is False,'Unsupported native acceptance/readback claim: '+key)
 for key in ('nativeApplied','savedMapUnloadedReloaded','originalSavedR22Unchanged','sourceInputsUnchanged',
  'inheritedPlantAssetsBytePreserved','sourceRootHeightChangeExplicit'):
  require(r[key]is True,'Actual saved source/scene proof missing: '+key)
 require(r['changedOriginalRoot']==1 and r['newActors']==r['newRoots']==0,'Single existing-root scope widened')
 change=r['changedComponent'];asset=g.PREFIX+'/Geometry/StaticMeshes/'+g.MODEL+'_LOD0.'+g.MODEL+'_LOD0'
 require(change=={'actor':base['targetActor'],'component':base['targetComponent'],'groupId':g.GROUP,
  'beforeMesh':base['oldMesh'],'afterMesh':asset},'Declared one-component mesh target differs')
 material=r['materialReport'];recipe=m.validate_recipe(bundle['plan'])
 require(material['schemaVersion']==1 and material['owner']==m.OWNER and material['status']=='owned-original-fern-material-created'
  and material['recipe']==recipe and material['sourceStudy']==g.pin(g.SOURCE)
  and material['asset']==g.PREFIX+'/Materials/M_'+m.KEY+'.M_'+m.KEY
  and material['materialCount']==1 and material['textureCount']==4 and set(material['textures'])==set(recipe['maps'])
  and material['compileErrors']==[] and material['instancedStaticMeshUsage']is True,'Exact one-graph/four-map fern recipe differs')
 for key in ('nativeAppearanceAccepted','nativeNormalTangentReadbackAvailable','nativeAlphaPixelsDecoded',
  'nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable','ueOpticalCalibrationAccepted'):
  require(material[key]is False,'Material/native pixel or optical claim unsupported: '+key)
 require(material['sourceAlpha16BitDoesNotProveNativePixelFormat']is True,'Source16-bit/native pixel distinction missing')
 for role,row in material['textures'].items():
  source=recipe['maps'][role];name='T_'+m.KEY+'_'+role+'_'+source['sha256'][:16]
  require(row['source']==source and row['asset']==g.PREFIX+'/Textures/'+name+'.'+name
   and row['sourceBits']==(16 if role=='alpha'else None)and row['sourceMode']==('I;16'if role=='alpha'else None)
   and all(row[k]is False for k in ('nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable','nativeImportedPixelsDecoded')),
   'Exact source-map route/pixel evidence differs')
  snapshot=row['snapshot'];tok=m.token
  require(snapshot['srgb']==(role=='albedo')and snapshot['flip_green_channel']==(role=='normalGL')
   and tok(snapshot['compression_settings'])=={'albedo':'TCDEFAULT','normalGL':'TCNORMALMAP','ARM':'TCMASKS','alpha':'TCMASKS'}[role]
   and tok(snapshot['address_x'])==tok(snapshot['address_y'])=='TAWRAP'
   and tok(snapshot['mip_gen_settings'])=='TMGSFROMTEXTUREGROUP','Saved source-map sampler/normal/mip policy differs')
 require(m.check_graph(material['graph'],{k:v['asset']for k,v in material['textures'].items()})==material['audit'],
  'Saved10-node original alpha/normal/ARM/SSS graph differs')
 measurement=load('nativeScaleMeasurement');proposal=bundle['plan']['placementProposal'];root=r['savedRootReadback']
 for key,value in {'actualNativeTransientMeasurement':True,'nativeQuaternionReconstructedFromHostFloats':False,
  'originalWrappedTranslationAndRotationCopiedDirectly':True,'transientComponentOwnedBySceneActor':False}.items():
  require(measurement[key]is value,'Faithful native transform measurement path differs')
 n.numeric_exact(measurement['preInsertionValue'],[measurement['originalValue'][0],measurement['originalValue'][1],proposal['scale']],
  'Source wrapped original XYZ/rotation or uniform scale changed before insertion')
 n.numeric_exact(root['actualStoredMatrix'],measurement['storedMatrix'],'Actual saved matrix differs from measured native binary64')
 n.numeric_exact(root['savedNativeValue'],measurement['recoveredValue'],'Actual saved Transform differs from measured native binary64')
 n.numeric_exact(root['actualNativeRootXYZ'],measurement['originalValue'][0],'Original native root XYZ changed')
 computed=n.footprint(bundle,measurement,root['savedNativeValue'],root['actualStoredMatrix'])
 validate_recorded_footprint(root,computed)
 before=load('beforeActorWitness');saved=load('savedActorWitness');declared=load('expectedActorWitness')
 require(before==base['witness'],'Actual complete R22 before witness differs')
 expected=g.expected_witness(before,base['targetActor'],base['targetComponent'],base['oldMesh'],asset,material['asset'],measurement['recoveredValue'])
 require(declared==saved==expected and len(saved)==r['actualFullActorCount']==5346
  and g.digest(saved)==r['savedActorWitnessSha256']==r['expectedActorWitnessSha256'],'Full5346 saved actor counterfactual differs')
 hisms=[c for actor in saved.values()for c in actor['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 require(len(hisms)==r['actualFullHismComponents']==2312 and sum(c['instanceCount']for c in hisms)==r['actualFullHismInstances']==676944,
  'Full native HISM census changed')
 old=g.component(before,base['targetActor'],base['targetComponent'])
 require(old['orderedInstanceTransformsSha256']==g.digest([measurement['originalValue']]),'Original measured single-root frame differs from original actor witness')
 corners=[n.cyclic([tuple(bundle['row']['expectedNativeVerticesCm'][i]+bundle['row']['uv0'][i])for i in bundle['row']['indices'][j:j+3]])for j in range(0,len(bundle['row']['indices']),3)]
 mesh=r['nativeMeshReadback'];require(mesh['mesh']==asset and mesh['lodProofs']==[{'lod':lod,'triangles':2384,
  'nativeCornerSha256':g.digest(corners),'orderedNativeFloat32PositionUvWindingVerified':True}for lod in range(3)]
  and mesh['actualLodScreenSizes']==[g.f32(v)for v in (1.,.15,.04)],'Actual all3×2384 native original corner/UV/order proofs differ')
 for key,value in {'savedBuildPolicyVerified':True,'originalFullShapeAtAllThreePilotLods':True,'originalProviderLodChainPresent':False,
  'sourceNormalsPreservedInExport':True,'originalSourceTangentsPresent':False,'nativeTangentsRequestedFromOriginalUv':True,
  'nativeTangentGenerationNumericallyVerified':False,'nativeNormalTangentReadbackAvailable':False,'nativeMeshPackageIndependentlyUnloaded':False}.items():
  require(mesh[key]is value,'Original normals/UV/tangent/pilot-LOD proof overclaimed: '+key)
 require(load('originalMaterialsBefore')==load('originalMaterialsSaved')==base['materials'],
  'Original56graphs/84textures changed')
 require([r[k]for k in ('originalScopedMaterialGraphsPreserved','originalScopedTextureObjectsPreserved','newMaterialGraphs','newTextureObjects',
  'totalScopedMaterialGraphs','totalScopedTextureObjects')]==[56,84,1,4,57,88],'Material/texture scope census differs')
 pipelines=[g.PREFIX+'/Pipeline/'+key+'.'+key for key in ('Assets','Materials','Level')]
 require(r['importPipelineAssets']==pipelines,'Exact3 owned importer pipelines differ')
 packages=[asset.split('.')[0],material['asset'].split('.')[0]]+[row['asset'].split('.')[0]for row in material['textures'].values()]+[p.split('.')[0]for p in pipelines]
 content=load('afterContentInventory');require(g.validate_content(base['content'],content,packages)==r['assetDelta']and len(content)==4058
  and r['protectedProjectProof']==base['report']['protectedProjectProof'],'Exact map-only+9packages Content4058/protected132 delta differs')
 return {'savedActors':5346,'fullSceneHismComponents':2312,'fullSceneHismInstances':676944,'changedExistingRoots':1,
  'newActors':0,'newRoots':0,'nativeLods':3,'nativeTrianglesByLod':[2384]*3,'sourceVertices':1660,
  'storedMatrixAndRecoveredTransformExactActualMeasuredBinary64':True,'rootXYZExact':True,
  'nativeRecordedDerivedRadiusAndClearanceExact':True,'hostFootprintInequalitiesIndependentlyValidated':True,
  'originalAboveRootHeightCm':root['originalSourceAbovePivotHeightCm'],'actualAboveRootHeightCm':root['actualNativeAboveRootHeightCm'],
  'heightEquivalenceClaimed':False,'wholeActorCounterfactualValidated':True,'nativeGeometryReadbackValidated':True,
  'scopedMaterialGraphs':57,'scopedTextureObjects':88,'newPackages':9,'contentFiles':4058,'protectedProjectFiles':132,
  'sourceAlphaBits':16,'nativeSourcePixelFormatReadbackAvailable':False,'nativeGpuPixelFormatReadbackAvailable':False,
  'nativeNormalTangentReadbackAvailable':False,'materialAndMeshPackagesIndependentlyReloaded':False,
  'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,'shippingAccepted':False,'nativeLaunchPerformedByChecker':False}


def main():
 g.require(g.sha(ROOT/HELPER)==HELPER_SHA and g.sha(ROOT/g.OWNER)==GUARD_SHA
  and g.sha(ROOT/m.OWNER)==MATERIAL_SHA,'Frozen consumed native/guard/material helper changed')
 path=Path(sys.argv[1]).resolve();g.require(path==g.NATIVE_OUTPUT/n.REPORT and g.sha(path)==REPORT_SHA,'Only exact saved R25b R2 report eligible')
 report=g.read(path);bundle=g.source();base=g.saved_native_base()
 preflight=n.validate_preflight(g.checked(report['sourcePreflight']),bundle,base)
 print(json.dumps(validate_saved(report,bundle,base,preflight)))


if __name__=='__main__':main()
