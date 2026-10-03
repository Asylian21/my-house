"""Read-only saved donor inventory; the R36 saved candidate is still pending.

No project is cloned, no package/map is written, no Unreal API is invoked.
The output is a scoped source proposal, not a native composition receipt.
"""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-yard-donor-inventory-r36-pending-r1.py'
OUTPUT = ROOT/'output/unreal/exterior-garden-yard-20261002-r36-pending-donor-inventory-r1'
REPORTS = {
 'gardenR34': ROOT/'output/unreal/exterior-20261002-r34a/garden-fern-only-native-report.json',
 'yardR32': ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json',
 'yardRepairR35': ROOT/'output/unreal/exterior-20261002-r35b/context-yard-repair-native-report-r2.json',
 'failedR36': ROOT/'output/unreal/exterior-20261002-r36a/garden-periwinkle-native-report.json',
}
INPUTS = {}


def require(condition, message):
 if not condition:
  raise RuntimeError(message)


def sha(path):
 digest = hashlib.sha256()
 with Path(path).open('rb') as handle:
  for block in iter(lambda: handle.read(1024*1024), b''):
   digest.update(block)
 return digest.hexdigest()


def pin(path):
 path = Path(path).resolve()
 row = {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}
 INPUTS[str(path)] = row
 return row


def read(path):
 pin(path)
 return json.loads(Path(path).read_text())


def read_pin(row):
 require(pin(row['path']) == row, 'Saved donor sidecar pin changed: '+row['path'])
 return json.loads(Path(row['path']).read_text())


def digest(value):
 return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                 allow_nan=False).encode()).hexdigest()


def difference_paths(a, b, path=''):
 if type(a) is not type(b):
  return [path]
 if isinstance(a, dict):
  return sum((difference_paths(a[key], b[key], path+'/'+str(key))
              if key in a and key in b else [path+'/'+str(key)]
              for key in sorted(set(a)|set(b))), [])
 if isinstance(a, list):
  if len(a) != len(b):
   return [path]
  return sum((difference_paths(x, y, path+'/'+str(i))
              for i, (x, y) in enumerate(zip(a, b))), [])
 return [] if a == b else [path]


def package_relative(asset):
 require(asset.startswith('/Game/Brezi/'), 'Only owned saved Brezi packages allowed')
 return asset.split('.', 1)[0][len('/Game/'):] + '.uasset'


def main():
 require(not OUTPUT.exists(), 'Exclusive new inventory output already exists')
 reports = {key: read(path) for key, path in REPORTS.items()}
 garden, yard, repair, failed = (reports[k] for k in REPORTS)
 for row, pid in ((garden, 21209), (yard, 5443), (repair, 37031)):
  require(row['nativeProcessId'] == pid and row['nativeApplied'] is True
          and row['savedMapUnloadedReloaded'] is True and row['sourceInputsUnchanged'] is True,
          'Actual saved donor process/reload/source boundary differs')
 require(garden['status'] == 'verified-saved-36-original-fern-garden-all-ornamentals-retained'
         and yard['status'] == 'verified-saved-resolved-context-yard-ground-and-low-detail'
         and repair['status'] == 'verified-saved-scoped-hardcourt-ecology-coverage-near-pbr-repair',
         'Exact saved donor status required')
 require(failed['status'] == 'failed' and failed['nativeProcessId'] == 42780
         and failed['error'] == 'Exact six original source-node actor labels required'
         and failed['nativeApplied'] is False,
         'R36 failure must remain explicit; no saved R36 donor exists here')
 require(all(row['activeDesign'] == garden['activeDesign']
             and row['setbacksMm'] == {'street': 3000, 'east': 3000}
             for row in (garden, yard, repair)), 'Design/setback boundary differs')

 inventories = {key: read_pin(reports[key]['afterContentInventory'])
                for key in ('gardenR34', 'yardR32', 'yardRepairR35')}
 garden_saved = read_pin(garden['savedActorWitness'])
 before32, saved32 = map(read_pin, (yard['beforeActorWitness'], yard['savedActorWitness']))
 before35, saved35 = map(read_pin, (repair['beforeActorWitness'], repair['savedActorWitness']))
 require(before35 == saved32, 'Actual R35 original witness differs from saved R32')
 require(set(before32) <= set(saved32) and set(before35) == set(saved35),
         'Donor actor creation/removal outside declared scope')
 changed32 = {key for key in before32 if before32[key] != saved32[key]}
 changed35 = {key for key in before35 if before35[key] != saved35[key]}
 added32 = set(saved32)-set(before32)
 require(changed32 == {row['actor'] for row in yard['targets'].values()}
         and added32 == set(yard['addedActors'].values()) and len(added32) == 4,
         'R32 exact three changes/four owned additions required')
 ecology = {row['actor']: row for row in repair['repairA']['actualRemoveReadback']}
 hard = {yard['targets'][key]['actor'] for key in ('entry_walk', 'service_court')}
 backdrop = repair['repairC']['target']['actualActor']
 require(len(ecology) == 8 and changed35 == set(ecology)|hard|{backdrop},
         'R35 exact eleven changed actors required')
 require(all(key in garden_saved and garden_saved[key] == before32[key]
             for key in changed32)
         and all(key in garden_saved and garden_saved[key] == before35[key]
                 for key in set(ecology)|{backdrop})
         and not added32 & set(garden_saved),
         'Actual R34 original target compatibility or owned identity disjointness differs')
 for key in changed32:
  expected = (['/components/0/hiddenInGame', '/components/0/visible']
              if key == yard['targets']['worn_edge']['actor'] else
              ['/components/0/materials/0', '/components/0/mesh', '/components/0/overrideMaterials'])
  require(difference_paths(before32[key], saved32[key]) == expected,
          'R32 changed an undeclared actor/component field')
 for key in changed35:
  expected = (['/components/0/instanceCount', '/components/0/orderedInstanceTransformsSha256']
              if key in ecology else ['/components/0/mesh'] if key in hard else
              ['/components/0/materials/0', '/components/0/overrideMaterials'])
  require(difference_paths(before35[key], saved35[key]) == expected,
          'R35 changed an undeclared actor/component field')

 packages, relative_seen = [], set()
 for donor in ('yardR32', 'yardRepairR35'):
  report = reports[donor]
  for asset in report['newPackages']:
   relative = package_relative(asset)
   require(relative not in relative_seen and relative not in inventories['gardenR34'],
           'Saved donor package collision in actual R34')
   path = Path(report['project'])/'Content'/relative
   proof = pin(path)
   require({key: proof[key] for key in ('sha256', 'bytes')} == inventories[donor][relative],
           'Actual saved donor package bytes differ: '+relative)
   packages.append({'donor': donor, 'asset': asset, 'relativeContentPath': relative,
                    'source': proof, 'donorReport': INPUTS[str(REPORTS[donor])]})
   relative_seen.add(relative)
 require(len(packages) == 14 and sum(row['source']['bytes'] for row in packages) == 1787793,
         'Exact fourteen saved yard packages/byte census differs')

 shared = {}
 for actor in sorted(added32):
  for component in saved32[actor]['components']:
   if 'instanceCount' not in component:
    continue
   for asset in [component['mesh']] + component['materials']:
    relative = package_relative(asset)
    require(inventories['yardR32'][relative] == inventories['gardenR34'][relative],
            'Shared native yard plant master/material package differs')
    observed = {}
    for donor in ('gardenR34', 'yardR32'):
     row = pin(Path(reports[donor]['project'])/'Content'/relative)
     require({key: row[key] for key in ('sha256', 'bytes')} == inventories[donor][relative],
             'Current shared native bytes differ')
     observed[donor] = row
    shared[asset] = {'relativeContentPath': relative, 'actualByteProofs': observed}
 require(len(shared) == 6, 'Exact three shared native masters and three materials required')

 targets = {}
 for actor in sorted(changed32|changed35):
  final = saved35[actor]
  original = garden_saved[actor]
  targets[actor] = {'originalR34WitnessSha256': digest(original),
    'recordedFinalYardWitness': final,
    'allowedChangesFromOriginalR34': difference_paths(original, final),
    'recordedRetirement': ecology.get(actor)}
 templates = {actor: saved32[actor] for actor in sorted(added32)}
 require(sum(c.get('instanceCount', 0) for row in templates.values()
             for c in row['components']) == 1274,
         'Actual yard native 1274 ordered roots required')
 require(sum(row['removedRoots'] for row in ecology.values()) == 34,
         'Actual scoped thirty-four whole ecology removals required')
 result = {
  'schema': 'brezi-garden-yard-saved-donor-inventory-r36-pending-r1',
  'owner': OWNER, 'status': 'source-only-saved-yard-donors-compatible-with-actual-r34-r36-saved-base-pending',
  'producer': pin(ROOT/OWNER), 'actualReports': {key: INPUTS[str(path)] for key, path in REPORTS.items()},
  'actualGardenR34Counts': garden['actualCounts'], 'futureSavedR36BaseReport': None,
  'futureCombinedNativeCounts': None, 'failedR36Preserved': True,
  'packages': packages, 'packageCount': 14, 'packageBytes': 1787793,
  'currentSharedNativeBindings': shared, 'originalTargetWitnessCompatibilityExact': True,
  'changedOriginalActorTargets': targets, 'addedYardActorTemplates': templates,
  'donorNewActorIdentitiesMustBeRelocatedAgainstActualFutureBase': True,
  'knownPlannedIdentityCollision': {
    'r32YardHismSourceIds': [2318, 2319, 2320],
    'r36ProposedHismIdsNotActualSaved': [2316, 2317, 2318, 2319, 2320, 2321],
    'policy': 'Allocate only after actual R36 saved witness; change actor/component identity paths only; retain every recorded member and policy.'},
  'scopeArithmeticOnly': {'addedFloorActors': 1, 'addedHismActors': 3, 'addedRoots': 1274,
                          'retiredOriginalEcologyRoots': 34, 'netAdditionalRoots': 1240},
  'wholeR35MapOrR30GardenMustNotBeCopied': True,
  'existing12TallHeroes41Flowers36R34FernsMustRemainUntouched': True,
  'additionalRandomSeedRangesReadbackAvailable': False,
  'nativeRawMemberSetterOrSeedMutationPerformed': False,
  'activeDesign': garden['activeDesign'], 'setbacksMm': garden['setbacksMm'],
  'inputFiles': dict(sorted(INPUTS.items())),
  'nativeExecuted': False, 'gpuExecuted': False, 'projectCloned': False, 'packagesCopied': False,
  'freshNativeActorOrGeometryDecodePerformed': False, 'combinedGeometryOrMaterialReadbackVerified': False,
  'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
  'performanceAccepted': False, 'shippingVerified': False,
 }
 for row in INPUTS.values():
  require(sha(row['path']) == row['sha256'] and Path(row['path']).stat().st_size == row['bytes'],
          'Read-only donor source changed during inventory')
 OUTPUT.mkdir()
 (OUTPUT/'producer-source.py').write_bytes((ROOT/OWNER).read_bytes())
 (OUTPUT/'donor-inventory.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
 print(json.dumps({'status': result['status'], 'output': str(OUTPUT/'donor-inventory.json'),
                   'sha256': sha(OUTPUT/'donor-inventory.json'), 'packageCount': 14,
                   'packageBytes': 1787793, 'inputCount': len(INPUTS),
                   'futureCombinedNativeCounts': None}))


if __name__ == '__main__':
 main()
