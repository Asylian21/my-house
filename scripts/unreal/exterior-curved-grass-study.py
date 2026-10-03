"""One immutable original-curved-grass source pilot; no Unreal/GPU launch."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-study.py'
OUTPUT = ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('r20_study_native_guards', ROOT/'scripts/unreal/exterior-curved-grass-native.py')
n = importlib.util.module_from_spec(spec); spec.loader.exec_module(n)
g, maps = n.guard, n.maps


def main():
    g.require(not OUTPUT.exists(), 'R20 source outputs are immutable; select a new named revision for any repair')
    OUTPUT.mkdir(parents=True)
    evidence = g.read(g.EVIDENCE_PLAN)
    report, _, _ = g.common.validate_plan(evidence, g.EVIDENCE_PLAN)
    originals = g.original_meshes()
    rows = g.converted_geometry(originals)
    source_geometry_proof = g.validate_geometry(rows, originals)
    geometry_file = OUTPUT/'geometry-manifest.json'
    g.write(geometry_file, {'schema': 'brezi-original-curved-grass-geometry-r1', 'owner': OWNER,
        'meshes': rows, 'audit': source_geometry_proof, 'nativeExecuted': False})
    glb = OUTPUT/'original-curved-grass-r20.glb'
    g.write_glb(glb, rows)
    decoded = g.decode_glb(glb, rows)
    placements, prototypes, camera = n.load_selection_inputs()
    candidates = g.source_candidates(placements, prototypes, camera)
    selected = g.select_roots(candidates, rows)
    selection_proof = g.validate_selection(selected, placements, prototypes, camera, rows)
    g.write(OUTPUT/'root-selection.json', selected)
    g.write(OUTPUT/'material-recipe.json', maps.canonical_recipe())
    maps.validate_recipe(maps.canonical_recipe())
    reference_receipt = ROOT/'output/unreal/exterior-ph-vegetation-reference-20261001-r1/source-download-receipt.json'
    reference_review = ROOT/'output/unreal/exterior-ph-vegetation-reference-review-20261001-r1/reference-review.json'
    g.require(g.sha(reference_receipt) == '5a461a4b1f9198f7622c373bb041327969665c8ad5f62525d1df708cea6fd466',
              'Original provider download receipt changed')
    sources = {'generator': ROOT/OWNER, 'nativeHelper': ROOT/n.OWNER,
        'geometryGuards': ROOT/g.OWNER, 'materials': ROOT/maps.OWNER,
        'tests': ROOT/'scripts/unreal/test_exterior_curved_grass.py', 'design': ROOT/'docs/unreal-curved-grass-r1.md'}
    start = time.monotonic()
    result = subprocess.run([sys.executable, '-B', str(sources['tests'])], cwd=ROOT, capture_output=True, text=True)
    (OUTPUT/'source-guard-tests.log').write_text(result.stdout+result.stderr)
    match = re.search(r'Ran (\d+) tests? in ', result.stdout+result.stderr)
    tests = {'owner': OWNER, 'status': 'passed' if result.returncode == 0 else 'failed', 'exitCode': result.returncode,
        'command': [sys.executable, '-B', str(sources['tests'])], 'elapsedSeconds': time.monotonic()-start,
        'testCount': int(match.group(1)) if match else None,
        'scope': 'CPU original geometry/basis/UV frames, exact source roots and RemoveAtSwap fixtures; no native execution.',
        'log': g.pin(OUTPUT/'source-guard-tests.log'), 'nativeExecuted': False, 'nativeAppearanceAccepted': False}
    g.write(OUTPUT/'source-guard-tests.json', tests)
    g.require(result.returncode == 0 and tests['testCount'] == 15, 'R20 CPU guards failed; preserve failed output and use new revision after repair')
    owned = {}
    for role, path in sources.items():
        snapshot = OUTPUT/('source-'+path.name)
        shutil.copyfile(path, snapshot)
        owned[role] = {'live': g.pin(path), 'snapshot': g.pin(snapshot)}
    engine = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    engine_paths = {
        'axisConversion': engine/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/ConversionUtilities.h',
        'originalAccessor': engine/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/GLTFAccessor.cpp',
        'originalMeshFactory': engine/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTFMeshFactory.cpp',
        'staticMeshSubsystemHeader': engine/'Source/Editor/StaticMeshEditor/Public/StaticMeshEditorSubsystem.h',
        'staticMeshSubsystemCpp': engine/'Source/Editor/StaticMeshEditor/Private/StaticMeshEditorSubsystem.cpp',
        'hismRemovalCpp': engine/'Source/Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp',
        'instanceStorageHeader': engine/'Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h'}
    engine_evidence = {**evidence['engineEvidence'], **{key: g.pin(path) for key,path in engine_paths.items()}}
    audit = n.canonical_audit(report)
    plan = {'schemaVersion': 1, 'schema': g.SCHEMA, 'owner': OWNER, 'status': g.STATUS,
        'baseNativeReport': evidence['baseNativeReport'], 'baseContentInventory': evidence['baseContentInventory'],
        'baseProjectProof': evidence['baseProjectProof'], 'activeDesign': report['activeDesign'], 'setbacksMm': report['setbacksMm'],
        'reusedBaseEvidencePlan': g.pin(g.EVIDENCE_PLAN), 'immutableGenericHelper': g.pin(g.SHARED),
        'sourceInputs': {key:g.pin(path) for key,path in n.source_inputs().items()}, 'camera': camera,
        'originalReferenceReceipt': g.pin(reference_receipt), 'originalReferenceReview': g.pin(reference_review),
        'geometry': g.pin(geometry_file), 'sourceGlb': g.pin(glb), 'rootSelection': g.pin(OUTPUT/'root-selection.json'),
        'materialRecipe': g.pin(OUTPUT/'material-recipe.json'), 'sourceGuardTests': g.pin(OUTPUT/'source-guard-tests.json'),
        'newSourceFiles': owned, 'engineEvidence': engine_evidence, 'nativeEngineBuildId': evidence['nativeEngineBuildId'],
        'audit': audit, 'nativeExecuted': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingPackageProduced': False, 'generatedAt': g.now()}
    plan_file = OUTPUT/'curved-grass-plan.json'
    g.write(plan_file, plan)
    n.validate_plan(plan, plan_file)
    summary = {'owner': OWNER, 'status': g.STATUS, 'selectedPlan': g.pin(plan_file), 'audit': audit,
        'geometryProof': source_geometry_proof, 'decodedGlb': decoded, 'selectionProof': selection_proof,
        'sourceCandidateCount': len(candidates), 'selectedByKind': dict(Counter(r['kind'] for r in selected)),
        'affectedOriginalGroupIds': sorted({r['groupId'] for r in selected}),
        'sourcePixelsEdited': False, 'originalGeometrySourceInputsChanged': False,
        'hismRetainedOrder': 'Native descending RemoveAtSwap; full retained original-index permutation recorded in native receipt.',
        'nativeExecuted': False, 'nativeAppearanceAccepted': False, 'performanceAccepted': False,
        'rootNativePending': True, 'fullPhotorealismAccepted': False}
    g.write(OUTPUT/'summary.json', summary)
    files = [p for p in sorted(OUTPUT.iterdir()) if p.is_file()]
    receipt = {'owner': OWNER, 'status': 'frozen-source-only-original-curved-grass-pilot', 'selectedPlan': g.pin(plan_file),
        'files': {p.name:g.pin(p) for p in files}, 'payloadFiles': len(files),
        'payloadBytes': sum(p.stat().st_size for p in files), 'nativeExecuted': False,
        'nativeAppearanceAccepted': False, 'performanceAccepted': False, 'generatedAt': g.now()}
    g.write(OUTPUT/'source-receipt.json', receipt)
    print(json.dumps({'output': str(OUTPUT), 'plan': g.pin(plan_file), 'receipt': g.pin(OUTPUT/'source-receipt.json'),
        'audit': audit, 'selection': selection_proof, 'nativeExecuted': False}))


if __name__ == '__main__': main()
