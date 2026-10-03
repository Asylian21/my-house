"""Closed source contract for a future clean garden plus saved yard overlay.

The selected garden/native project are intentionally unbound. This module
never generates geometry, clones a project, copies a package, or invokes UE.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'brezi-clean-selected-garden-and-saved-yard-integration'
OWNER = 'scripts/unreal/exterior-garden-yard-integration-source-draft.py'
TAG = 'BreziCleanGardenYardIntegration'
INVENTORY = ROOT/'output/unreal/exterior-garden-yard-20261002-r36-pending-donor-inventory-r1/donor-inventory.json'
INVENTORY_SHA = '89d97d3e8f02cd3b05be24b9273cc8310828097c5d0fad2ce6818cae043b7082'
# No candidate/selected report may be invented while the garden image is pending.
SELECTED_BASE = None
CANDIDATE = None
SELECTED_PLAN = None


def require(condition, message):
 if not condition:
  raise RuntimeError(message)


def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
 path = Path(path).resolve()
 return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def read_pin(row):
 require(pin(row['path']) == row, 'Immutable recorded source pin differs: '+row['path'])
 return json.loads(Path(row['path']).read_text())


def digest(value):
 return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                  allow_nan=False).encode()).hexdigest()


def binary(value):
 if isinstance(value, (list, tuple)):
  return b''.join(binary(v) for v in value)
 require(type(value) in (int, float), 'Only finite numeric matrix/frame coordinates allowed')
 require(value == value and abs(value) != float('inf'), 'Nonfinite native control rejected')
 return struct.pack('<d', value)


def exact(a, b, message):
 require(binary(a) == binary(b), message)


def pending_native_gate():
 require(SELECTED_BASE is not None and CANDIDATE is not None and SELECTED_PLAN is not None,
         'Selected actual garden report, independent clone and final native plan are pending')
 raise RuntimeError('Draft is not a native-launch entry point; final bound owner/preflight required')


def load_donors():
 require(sha(INVENTORY) == INVENTORY_SHA, 'Frozen saved donor inventory differs')
 inventory = json.loads(INVENTORY.read_text())
 require(inventory['futureSavedR36BaseReport'] is None and inventory['futureCombinedNativeCounts'] is None
         and inventory['packageCount'] == 14 and inventory['packageBytes'] == 1787793,
         'Exact source-only donor proposal required')
 reports = {key: read_pin(row) for key, row in inventory['actualReports'].items()}
 r32, r35 = reports['yardR32'], reports['yardRepairR35']
 source_plan = read_pin(r32['sourceStudy'])
 proposal = read_pin(source_plan['proposal'])
 measurements = read_pin(r32['nativeSourceFrameMeasurements'])
 controls = read_pin(r35['originalEcologyControls'])
 retained = read_pin(r35['retainedEcologySaved'])
 yard_controls = read_pin(r35['originalControlsSaved'])['all13YardShrubsAnd1274LowRootsRawControls']
 templates = inventory['addedYardActorTemplates']
 groups = {}
 for actor, row in templates.items():
  c = row['components'][0]
  if 'instanceCount' not in c:
   continue
  model = row['label'].removeprefix('EX_yard_ground_r32_')
  require(model in measurements and actor in yard_controls, 'Saved whole yard group/model binding differs')
  recorded = measurements[model]
  roots = [r for r in proposal['planting'] if r['modelId'] == model]
  actual = yard_controls[actor]
  require(recorded['rootIds'] == [r['id'] for r in roots]
          and c['instanceCount'] == actual['instanceCount'] == len(roots)
          and digest(recorded['recoveredValues']) == c['orderedInstanceTransformsSha256'],
          'Saved 1274 root order/full component witness binding differs')
  exact(recorded['recoveredValues'], actual['recoveredValues'], 'R32/R35 native recovered yard controls differ')
  exact(recorded['actualMatrices'], actual['storedMatrices'], 'R32/R35 native stored yard matrices differ')
  groups[model] = {'actor': actor, 'template': row, 'sourceRows': roots,
                   'measurement': recorded, 'savedControl': actual}
 require(len(groups) == 3 and sum(len(row['sourceRows']) for row in groups.values()) == 1274,
         'Only three groups and exactly1274 authored whole yard roots required')
 retirements = {row['groupId']: row for row in r35['repairA']['actualRemoveReadback']}
 require(set(retirements) == set(controls) == set(retained) and len(controls) == 8
         and sum(row['removedRoots'] for row in retirements.values()) == 34
         and sum(row['instanceCount'] for row in retained.values()) == 1919,
         'Eight exact native donor retirement/survivor scopes required')
 return {'inventory': inventory, 'reports': reports, 'r32SourcePlan': source_plan,
         'r32Proposal': proposal, 'r32Measurements': measurements, 'yardGroups': groups,
         'ecologyOriginal': controls, 'ecologyRetained': retained,
         'retirements': retirements, 'inputPins': [pin(INVENTORY), r32['sourceStudy'],
          source_plan['proposal'], r32['nativeSourceFrameMeasurements'], r35['originalEcologyControls'],
          r35['retainedEcologySaved'], r35['originalControlsSaved']]}


def selected_target_compatibility(before, donors):
 inventory = donors['inventory']
 require(all(actor in before and digest(before[actor]) == row['originalR34WitnessSha256']
             for actor, row in inventory['changedOriginalActorTargets'].items()),
         'Selected original yard/backdrop/ecology target has changed outside donor scope')
 # Only the three added HISM identities may collide with a later R36 base.
 # Every addition is relocated, including the floor, so no identity is reused.
 return True


def relocate_template(old_actor, new_actor, template):
 family = 'BreziVegetationPatch' if 'instanceCount' in template['components'][0] else 'StaticMeshActor'
 require(re.fullmatch(re.escape('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.')+family+r'_\d+', new_actor),
         'Only fresh same-map/same-native-class actor identity allowed')
 row = copy.deepcopy(template)
 for component in row['components']:
  require(component['path'].startswith(old_actor+'.'), 'Source component must belong to its source actor')
  component['path'] = new_actor+component['path'][len(old_actor):]
  parent = component.get('attachParent')
  require(parent is None or parent.startswith(old_actor+'.'), 'External attachment cannot be relocated')
  if parent is not None:
   component['attachParent'] = new_actor+parent[len(old_actor):]
 require(TAG not in row['tags'], 'Source may not already claim future integration ownership')
 row['tags'] = sorted(row['tags']+[TAG])
 return row


def expected_scene(before, donors, mapping):
 selected_target_compatibility(before, donors)
 inventory = donors['inventory']
 templates = inventory['addedYardActorTemplates']
 require(all(TAG not in row.get('tags', []) for row in before.values()),
         'Selected base may not already contain this integration ownership tag')
 require(set(mapping) == set(templates) and len(set(mapping.values())) == 4
         and not set(mapping.values()) & set(before), 'Exactly four fresh disjoint actor identities required')
 expected = copy.deepcopy(before)
 for actor, row in inventory['changedOriginalActorTargets'].items():
  expected[actor] = copy.deepcopy(row['recordedFinalYardWitness'])
 for old_actor, template in templates.items():
  expected[mapping[old_actor]] = relocate_template(old_actor, mapping[old_actor], template)
 require(len(expected) == len(before)+4, 'Source counterfactual may add only four actors')
 return expected


def validate_packages(before_content, copied_content, after_content, donors):
 require('Brezi/Maps/Brezi.umap' in before_content, 'Actual existing main map required')
 packages = {row['relativeContentPath']: {key: row['source'][key] for key in ('sha256', 'bytes')}
             for row in donors['inventory']['packages']}
 require(len(packages) == 14 and not set(packages) & set(before_content),
         'Exactly fourteen disjoint donor native packages required')
 combined = {**before_content, **packages}
 require(copied_content == combined and set(after_content) == set(combined),
         'Actual independent package copy or post-native Content membership differs')
 require(all(after_content[key] == value for key, value in combined.items()
             if key != 'Brezi/Maps/Brezi.umap'),
         'Only original main Map bytes may change; donor/old assets stay exact')
 return {'newPackages': 14, 'newPackageBytes': 1787793, 'onlyOriginalMapChanged': True}


def replay_record(model, inputs, recovered, matrices, donors):
 row = donors['yardGroups'][model]
 expected = row['measurement']
 exact(inputs, expected['preInsertionValues'], 'Original R32 native constructor input values changed')
 exact(recovered, expected['recoveredValues'], 'Replayed native recovered transforms differ from saved R32')
 exact(matrices, expected['actualMatrices'], 'Replayed native FMatrix rows differ from saved R32')
 return {'modelId': model, 'rootIds': expected['rootIds'], 'instances': len(inputs),
         'originalNativeConstructorInputsBinary64Exact': True,
         'recoveredTransformsBinary64Exact': True, 'storedMatricesBinary64Exact': True,
         'capturedMatrixCoordinateReconstructionPerformed': False,
         'wrappedRowTransferActuallyExecuted': False}


if __name__ == '__main__':
 pending_native_gate()
