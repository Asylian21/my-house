"""CPU-only closed saved R22 R3 composition check for the Editor pilot reader."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-integration-editor-check-r10.py'
HELPER='scripts/unreal/exterior-realism-integration-native-r22-r3.py'
HELPER_SHA='f93ea98e9599ac85abd2842dc8c08d50f7977366fa1bb3ae35b5923bfd12cbae'
s=importlib.util.spec_from_file_location('r10_exact_saved_r22_native',ROOT/HELPER)
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
g=n.guard


def validate_saved(r,plan,bundle,supplement):
    require=n.require;donors=bundle['reports'];read=lambda key:n.read(n.check_pin(r[key]))
    require(r['schema']==g.SCHEMA and r['owner']==HELPER and r['status']==n.STATUS
        and r['repairSchema']==n.repair.SCHEMA and r['repairSupplement']==n.pin(n.repair.SUPPLEMENT)
        and r['selectedPlan']==n.pin(g.PLAN) and r['savedDonors']==plan['donors'], 'Only known saved R22 R3 composition required')
    require(r['output']==str(n.repair.CANDIDATE)and r['project']==str(n.repair.CANDIDATE/'Project/BreziTwin')
        and r['inputFiles']==supplement['inputFiles']and r['ownedSources']==supplement['ownedSources']
        and r['originalOwnedSources']==plan['ownedSources']and r['baseNativeReport']==plan['baseNativeReport'],
        'Own project/source scope differs')
    require(r['originalFailedTrial']==supplement['failure']and r['moduleOrderWitness']==n.read(n.check_pin(supplement['moduleOrderStudy']))['policy'],
        'Actual frozen-first repair witness differs')
    for key in ('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced',
        'nativeMaterialPackagesIndependentlyReloaded','nativeMeshPackagesIndependentlyReloaded','nativeNormalTangentReadbackAvailable','originalExteriorOwnershipSpoofed'):
        require(r[key]is False,'Unsupported native/appearance claim: '+key)
    for key in ('savedMapUnloadedReloaded','originalR16Unchanged','sourceInputsUnchanged','donorFilesNeverMutated'):
        require(r[key]is True,'Saved/source proof missing: '+key)
    require(r['activeDesign']==bundle['base']['activeDesign']and r['setbacksMm']==bundle['base']['setbacksMm']
        and r['actualAudit']==plan['audit']and r['scopeAudit']==plan['scopeAudit']
        and r['knownReviewLimits']==plan['knownReviewLimits']and r['combinedAppearanceGoNoGo']==plan['combinedAppearanceGoNoGo'],
        'Actual scope/design/review limits differ')
    before=read('beforeActorWitness');saved=read('savedActorWitness');declared=read('expectedActorWitness')
    require(before==bundle['before']and len(before)==5306,'Original complete5306 actor witness differs')
    added=r['addedActorIdentityMap'];expected=g.compose_all_expected(bundle['expectedOriginal'],bundle['templates'],added)
    require(declared==expected==saved and len(saved)==5346,'Saved full actor state differs from explicit composed counterfactual')
    require([r[k]for k in ('beforeActorWitnessSha256','expectedActorWitnessSha256','savedActorWitnessSha256')]
        ==[n.digest(v)for v in (before,expected,saved)],'Complete actor canonical digest differs')
    require(r['leafComponentBindings']==donors['leaf']['componentBindings']and r['originalMemberChanges']==donors['grass']['originalMemberChanges']
        and r['neighborChanges']==donors['neighbors']['componentChanges'],'Original field mutation scope differs')
    culls=[]
    for delta in donors['visibility']['componentCullOverrides']:
        row=copy.deepcopy(delta);row['retainedInstances']=g.component(bundle['expectedOriginal'],row['actor'],row['component'])['instanceCount'];culls.append(row)
    require(r['componentCullOverrides']==culls and sum(x['retainedInstances']for x in culls)==501826,
        '601 cull/64 grass membership overlap differs')
    neighbor=r['newNeighborActors'];foreground=r['newForegroundActors'];grass=r['newGrassGroups']
    require(set(neighbor)==set(donors['neighbors']['addedActors'])and len(neighbor)==32
        and set(foreground)==set(donors['foreground']['addedActors'])and len(foreground)==5
        and set(grass)==set(donors['grass']['newGroups'])and len(grass)==3,'Owned actor/group identities differ')
    reconstructed={**{'neighbors:'+k:v for k,v in neighbor.items()},**{'foreground:'+k:v for k,v in foreground.items()},
        **{'grass:'+k:v['actor']for k,v in grass.items()}}
    require(added==reconstructed and len(added)==40,'Exact40 added identity map differs')
    for key,row in donors['grass']['newGroups'].items():
        require(grass[key]==g.relocate_template(row,row['actor'],added['grass:'+key]),'New grass group changed beyond owned actor identity')
    require(r['newGrassRootReadback']==donors['grass']['sourceRootPlacementReadback']and len(r['newGrassRootReadback'])==64,
        'All64 exact native stored matrix/recovered Transform/footprint proofs differ from faithful saved donor')
    require(r['newGrassMeshProofs']==donors['grass']['newMasterProofs'],'All9 copied original grass LOD geometry proofs differ')
    require(r['neighborGeometryReadback']==donors['neighbors']['savedReadback']['meshProofs'],
        'All37 copied neighbor source geometry/default slot proofs differ')
    foreground_proof=copy.deepcopy(donors['foreground']['savedReadback'])
    for row in foreground_proof['groups']:
        require(row['actor']==donors['foreground']['addedActors'][row['id']],'Original foreground proof actor differs')
        row['actor']=foreground[row['id']]
    require(r['foregroundReadback']==foreground_proof,'Foreground floor/graph/4group source512 proof differs')
    roof=[]
    for delta in donors['roof']['componentMaterialOverrides']:
        row=copy.deepcopy(delta);row['sourceDonorActor']=row['actor'];row['actor']=neighbor[row['sourceMeshId']];roof.append(row)
    require(r['roofComponentOverrides']==roof and len(roof)==4,'Roof overrides widened beyond4 new neighbor targets')
    require(read('originalGeometryAfter')==bundle['originalGeometryAfter']and r['baseGeometryReadback']==donors['leaf']['baseGeometryReadback']
        and r['savedOriginalGeometryReadback']==donors['grass']['savedGeometryReadback']['originalOwnershipDelegation'],
        'Genuine original exterior ownership/geometry readback differs')
    hisms=[c for row in saved.values()for c in row['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    require(len(hisms)==r['actualFullSceneHismComponents']==2312 and sum(c['instanceCount']for c in hisms)==r['actualFullSceneHismInstances']==676944
        and r['actualRecordedExteriorHismGroups']==1987 and r['actualRecordedExteriorHismInstances']==632538,
        'Full scene versus recorded exterior census differs')
    materials=read('materialsSaved');require(materials==read('materialsBefore'),'Original/copied graph or texture changed after scene save')
    original=n.read(n.check_pin(donors['leaf']['originalMaterialsBefore']))
    material_paths={row['asset']for row in original['graphs'].values()}|{row['asset']for row in donors['leaf']['variants'].values()} \
        |{row['asset']for row in donors['neighbors']['materials']['materials'].values()} \
        |{donors['grass']['materialReport']['asset'],donors['foreground']['newMaterial']['asset'],donors['roof']['materialReport']['asset']}
    texture_paths={row['asset']for row in original['textures'].values()}|{row['asset']for row in donors['neighbors']['materials']['textures'].values()} \
        |{row['asset']for row in donors['grass']['materialReport']['textures'].values()}|{row['asset']for row in donors['roof']['materialReport']['textures'].values()}
    expected_materials={'original':original,'leaf':donors['leaf']['variants'],'neighbor':donors['neighbors']['materials'],
        'grass':donors['grass']['materialReport'],'foreground':donors['foreground']['newMaterial'],'roof':donors['roof']['materialReport'],
        'scopedMaterialGraphs':56,'scopedTextureObjects':84,'verifiedMaterialAssets':sorted(material_paths),'verifiedTextureAssets':sorted(texture_paths)}
    require(materials==expected_materials and len(material_paths)==r['scopedMaterialGraphs']==56 and len(texture_paths)==r['scopedTextureObjects']==84,
        'Exact original42/74 plus owned material/texture set differs')
    content=read('afterContentInventory');delta=g.validate_content(bundle['content'],content,bundle['packages'],plan['diagnosticViewpoints']['sha256'])
    require(delta==r['assetDelta']and len(content)==4049 and r['protectedProjectProof']==plan['baseProjectProof']
        and r['originalPlantMastersPreserved']==135 and r['originalPlantLodsPreserved']==405,'Exact Content/plant preservation delta differs')
    project=Path(r['project']);require(r['diagnosticViewpoints']==n.pin(project/'Content/Data/viewpoints.json')
        and r['diagnosticViewpoints']['sha256']==plan['diagnosticViewpoints']['sha256'],'Exact original camera prefix/R18 appended diagnostic differs')
    return {'originalActors':5306,'savedActors':5346,'copiedNewPackages':74,'contentFiles':4049,
        'fullSceneHismComponents':2312,'fullSceneHismInstances':676944,'recordedExteriorHismGroups':1987,'recordedExteriorHismInstances':632538,
        'leafGroups':23,'visibilityGroups':601,'retainedVisibilityInstances':501826,'grassReplacementRoots':64,
        'foregroundRoots':512,'foregroundFloorTriangles':1843,'neighborAddedActors':32,'roofComponentOverrides':4,
        'scopedMaterialGraphs':56,'scopedTextureObjects':84,'wholeActorCounterfactualValidated':True,
        'nativeGeometryReadbackValidated':True,'storedGrassMatrixAndRecoveredTransformExactMeasured':True,
        'normalTangentReadbackAvailable':False,'materialAndMeshPackagesIndependentlyReloaded':False,
        'inheritedPlantMasters':135,'inheritedPlantLods':405,'newNativeInheritedPlantLodMeasurementPerformed':False,
        'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,
        'combinedAppearanceGoNoGo':plan['combinedAppearanceGoNoGo'],'knownReviewLimits':plan['knownReviewLimits']}


def main():
    n.require(n.sha(ROOT/HELPER)==HELPER_SHA,'Frozen R22 R3 native helper changed')
    report_path=Path(sys.argv[1]).resolve();n.require(report_path==n.repair.CANDIDATE/n.REPORT,'Only own saved R22 R3 report eligible')
    report=n.read(report_path);plan,bundle=g.validate_plan();supplement=n.repair.validate_supplement()
    summary=validate_saved(report,plan,bundle,supplement)
    g.actual_terminal(report_path,report_path.parent/'realism-integration-native-r3-process.json',HELPER,'realism-integration-native-r3')
    print(json.dumps(summary))


if __name__=='__main__':main()
