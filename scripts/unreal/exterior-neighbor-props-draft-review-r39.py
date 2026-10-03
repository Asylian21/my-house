"""Freeze a small unbound draft receipt; no historical producer/Unreal launch."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-props-draft-review-r39.py'
OUT=ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-unbound-native-draft'
SOURCES=['exterior-neighbor-props-contract-r39-draft.py','exterior-neighbor-props-materials-r39-draft.py',
  'exterior-neighbor-props-native-r39-draft.py','test_exterior_neighbor_props_r39_draft.py','exterior-neighbor-props-draft-review-r39.py']
def pin(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def write(p,value):
    p.write_text(json.dumps(value,indent=2)+'\n');return pin(p)
def main():
    assert not OUT.exists(),'New output must not replace history'
    spec=importlib.util.spec_from_file_location('r39_draft_review_contract',ROOT/'scripts/unreal'/SOURCES[0])
    c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);b=c.load_source()
    inputs=[ROOT/'scripts/unreal'/n for n in SOURCES]+[c.SOURCE,Path(b['proposal']['originalDownloadReceipt']['path']),
      ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py']
    for model in b['proposal']['models'].values():inputs.extend([Path(model['gltf']['path']),*[Path(v['path'])for v in model['bins']]])
    for recipe in b['recipes'].values():inputs.extend(Path(row['path'])for row in recipe['maps'].values())
    before={str(p.resolve()):pin(p)for p in inputs}
    for name in SOURCES:ast.parse((ROOT/'scripts/unreal'/name).read_text())
    final_log=Path('/private/tmp/brezi-r39-props-unbound-fixtures-r2.log');log=final_log.read_text()
    assert 'Ran 10 tests in 1.004s' in log and log.rstrip().endswith('OK')
    OUT.mkdir();(OUT/'sources').mkdir();(OUT/'logs').mkdir()
    snapshots=[]
    for name in SOURCES:
        source=ROOT/'scripts/unreal'/name;target=OUT/'sources'/name;shutil.copyfile(source,target)
        assert pin(source)['sha256']==pin(target)['sha256'];snapshots.append(pin(target))
    for name in ['brezi-r39-props-unbound-fixtures-r1.log','brezi-r39-props-unbound-fixtures-r2.log']:
        shutil.copyfile(Path('/private/tmp')/name,OUT/'logs'/name)
    recipes=write(OUT/'material-recipes-draft.json',{'schema':'brezi-original-three-neighbor-prop-recipes-unbound-r39',
      'owner':OWNER,'sourceProposal':b['proposalPin'],'recipes':b['recipes'],'selectedNativeBase':None,'projectClone':None,'nativeReport':None})
    after={str(p.resolve()):pin(p)for p in inputs};assert before==after
    result={'schema':'brezi-original-neighbor-prop-unbound-native-draft-readiness-r39','schemaVersion':1,'owner':OWNER,
      'status':'reviewable-unbound-whole-original-prop-kernels-cpu-contracts-passed','sourceProposal':b['proposalPin'],
      'selectedNativeBase':None,'projectClone':None,'nativeReport':None,'sourceFiles':[pin(ROOT/'scripts/unreal'/n)for n in SOURCES],
      'snapshots':snapshots,'inputPinsBefore':before,'inputPinsAfter':after,'materialRecipes':recipes,
      'fixtureExecution':{'toolObservedExitCode':0,'casesPassed':10,'elapsedTestSeconds':1.004,'log':pin(OUT/'logs'/final_log.name),
        'nativeApiActuallyExercised':False,'firstFixtureFailurePreserved':pin(OUT/'logs/brezi-r39-props-unbound-fixtures-r1.log')},
      'astFilesParsed':5,'wholeOriginalModels':3,'wholeSourceAssembliesProposed':6,'originalParts':4,
      'hoseOriginalParts':2,'originalMasterTriangles':26601,'sourceAssemblyTriangleInstanceBudget':44445,
      'newMaterialGraphsProposed':3,'newOriginalPngTextureObjectsProposed':11,'originalSourcePixelsEdited':False,
      'sourceNormalTangentNumericReadbackAvailable':False,'originalCoilNodePoseNativeGatePending':True,
      'publicMutationEntriesRejectBeforeUObject':True,'finalAssemblyOwnershipAndSceneApplicationImplemented':False,
      'originalReferencedJpegToPublishedPngPixelEquivalenceClaimed':False,'wateringCanSpecularZeroIsF0OnlyApproximation':True,
      'wateringCanGrazingEnergyOrIorEquivalenceClaimed':False,'nativeExecuted':False,'nativeApplied':False,
      'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False}
    print(json.dumps(write(OUT/'draft-readiness.json',result)))
if __name__=='__main__':main()
