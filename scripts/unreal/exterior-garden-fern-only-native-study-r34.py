"""Bind the immutable fern-only proposal to the actual own R29 clone."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-only-native-study-r34.py'
s = importlib.util.spec_from_file_location('r34_owned_native_study_guards', ROOT/'scripts/unreal/exterior-garden-fern-only-native-guards-r34.py')
g = importlib.util.module_from_spec(s)
s.loader.exec_module(g)


def main():
    g.require(not g.STUDY.exists(), 'Fresh native binding output only')
    bundle = g.source_bundle()
    base, source = bundle['base'], bundle['source']
    clone = g.validate_clone(base)
    materials = g.material_readiness()
    names = ['exterior-garden-fern-only-native-study-r34.py', 'exterior-garden-fern-only-native-guards-r34.py',
             'exterior-garden-fern-only-native-r34.py', 'exterior-garden-fern-only-materials-r34.py',
             'test_exterior_garden_fern_only_native_r34.py']
    owned = {name: g.pin(ROOT/'scripts/unreal'/name) for name in names}
    inputs = {r['path']: r['sha256'] for r in source['proposal']['inputFiles']}
    for key in ('geometryDescriptor', 'sourceGlb', 'sourceCrownProof', 'plannedRetainedNativeControls',
                'materialRecipe', 'sourceLayout', 'producerSnapshot'):
        row = source['proposal'][key]
        g.check_pin(row)
        inputs[row['path']] = row['sha256']
    inputs.update(g.read(base['process']['receipt']['path'])['sourcePinsBeforeNative'])
    inputs.update(materials['inputFilesBefore'])
    inputs[str(g.MATERIAL_READY)] = g.sha(g.MATERIAL_READY)
    inputs[materials['tests']['log']['path']] = materials['tests']['log']['sha256']
    for row in [*owned.values(), g.pin(g.PROPOSAL), base['reportPin'], base['audit'], base['process']['receipt'],
                base['process']['raw'], base['process']['log'], base['report']['savedActorWitness'],
                base['report']['afterContentInventory'], base['report']['protectedProjectProof'], clone]:
        inputs[row['path']] = row['sha256']
    row = {'schema': g.SCHEMA, 'schemaVersion': 1, 'owner': OWNER,
           'status': 'source-ready-actual-r29-base-36-ferns-all-ornamentals-retained-native-pending',
           'createdAt': datetime.now(timezone.utc).isoformat(), 'sourceProposal': g.pin(g.PROPOSAL),
           'baseNativeReport': base['reportPin'], 'baseNativeProcess': base['process'], 'baseCurrentByteAudit': base['audit'],
           'projectClone': clone, 'candidateOutput': str(g.CANDIDATE),
           'materialReadiness': g.pin(g.MATERIAL_READY),
           'activeDesign': source['proposal']['activeDesign'], 'setbacksMm': {'street': 3000, 'east': 3000},
           'inputFiles': inputs, 'ownedSources': owned, 'expectedCounts': g.COUNTS,
           'retiredRootIds': [r['rootId'] for r in source['placements']], 'newGroupOrder': list(g.source_guard.MODELS),
           'wholeOneMemberHeroGroupRetirements': [],
           'originalGardenGroupBindings': {k: {x: v[x] for x in ('actor', 'component', 'oldMesh')} for k, v in bundle['groups'].items()},
           'nativeExecutionRequirements': source['proposal']['nativeExecutionRequirements'],
           'futureYardIntegration': source['proposal']['futureYardIntegration'],
           'nativeApplied': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
           'performanceAccepted': False, 'shippingVerified': False, 'packageVerified': False}
    g.STUDY.mkdir()
    g.write(g.PLAN, row)
    g.validate_plan()
    print({'plan': g.pin(g.PLAN), 'clone': clone, 'nativeExecuted': False})


if __name__ == '__main__':
    main()
