"""Freeze one native-derived, source-only leaf transmission trial.

Writes only a new owned study directory. Never invokes Unreal or alters the
base project. Source evidence is distinct from an eventual native receipt.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-transmission-study.py'
NATIVE = ROOT / 'scripts/unreal/exterior-canopy-transmission-native.py'
spec = importlib.util.spec_from_file_location('transmission_source_guards', NATIVE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def produce(base, output):
    base, output = Path(base).resolve(), Path(output).resolve()
    guard.require(base == ROOT / 'output/unreal/exterior-20261001-r16a', 'Only the selected saved R16 source is supported')
    guard.require(output == ROOT / 'output/unreal/exterior-canopy-transmission-20261001-r1-study', 'Only the new owned R1 study may be written')
    guard.require(not output.exists(), 'Study already exists; frozen outputs are not overwritten')
    report_path = base / 'exterior-import-report.json'
    report_pin = guard.pin(report_path)
    report = guard.read(report_path)
    scope = guard.canonical_scope(report)
    project = base / 'Project/BreziTwin'
    content = guard.inventory(project / 'Content')
    expected = {Path(k).relative_to(project / 'Content').as_posix(): v for k, v in report['afterAssetHashes'].items()}
    guard.require(set(content) == set(expected) and all(content[k]['sha256'] == v for k, v in expected.items()),
                  'Actual original native Content differs from its saved report')
    proof = guard.project_proof(project)
    snapshot_path = base / 'source-freeze/consumed-native-r1/snapshot.json'
    snapshot = guard.read(snapshot_path)
    frozen = {}
    rows = {r['source']: r for r in snapshot['files']}
    for path, value in report['pipelineFiles'].items():
        source_pin = guard.pin(base / 'source-freeze/consumed-native-r1/workspace' / Path(path).relative_to(ROOT))
        guard.require(source_pin['sha256'] == value == rows[path]['sha256'], 'Consumed pipeline pin mismatch')
        frozen[path] = source_pin
    engine = Path(os.environ.get('UNREAL_ENGINE_ROOT', '/Users/Shared/Epic Games/UE_5.8')).resolve()
    engine_files = {key: guard.pin(engine / path) for key, path in {
        'directFoliageShader': 'Engine/Shaders/Private/ShadingModels.ush',
        'indirectFoliageShader': 'Engine/Shaders/Private/DiffuseIndirectComposite.usf',
        'editorAssetLibraryHeader': 'Engine/Plugins/Editor/EditorScriptingUtilities/Source/EditorScriptingUtilities/Public/EditorAssetLibrary.h',
        'materialEditingHeader': 'Engine/Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h',
        'primitiveComponentHeader': 'Engine/Source/Runtime/Engine/Classes/Components/PrimitiveComponent.h',
        'editorBinary': 'Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor',
        'editorModules': 'Engine/Binaries/Mac/UnrealEditor.modules'}.items()}
    direct = Path(engine_files['directFoliageShader']['path']).read_text()
    indirect = Path(engine_files['indirectFoliageShader']['path']).read_text()
    guard.require('Lighting.Transmission = AreaLight.FalloffColor * (AreaLight.Falloff * WrapNoL * Scatter) * SubsurfaceColor;' in direct,
                  'Installed foliage transmission shader evidence differs')
    guard.require('SubsurfaceColor' in indirect and 'SHADINGMODELID_TWOSIDED_FOLIAGE' in indirect,
                  'Installed indirect foliage source evidence missing')
    own_module_map = guard.read(project / 'Binaries/Mac/UnrealEditor.modules')
    engine_module_map = guard.read(Path(engine_files['editorModules']['path']))
    guard.require(own_module_map['BuildId'] == engine_module_map['BuildId'], 'Actual native module/engine BuildId differs')
    module = project / 'Binaries/Mac' / own_module_map['Modules']['BreziTwin']
    module_pin = guard.pin(module)
    guard.require(module_pin['sha256'] == '2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574',
                  'Native Editor module is not the reviewed recorder')
    # This suite tests scope failure modes; no fake Unreal module or pixel
    # output is generated. Its output belongs to this source study only.
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    tests = subprocess.run([sys.executable, str(ROOT / 'scripts/unreal/test_exterior_canopy_transmission.py'), '-v'],
                           cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
    guard.require(tests.returncode == 0, 'Source guard tests failed:\n' + tests.stdout + tests.stderr)
    output.mkdir()
    new_sources = {}
    for key, original, filename in [
        ('generator', Path(__file__).resolve(), 'generator-source.py'),
        ('nativeHelper', NATIVE, 'native-helper-source.py'),
        ('tests', ROOT / 'scripts/unreal/test_exterior_canopy_transmission.py', 'test-source.py'),
        ('design', ROOT / 'docs/unreal-canopy-transmission-r1.md', 'design.md')]:
        source = guard.pin(original)
        target = output / filename
        shutil.copy2(original, target)
        new_sources[key] = {'live': source, 'snapshot': guard.pin(target)}
    guard.write(output / 'base-content-inventory.json', content)
    guard.write(output / 'base-project-proof.json', proof)
    guard.write(output / 'source-guard-tests.json', {'status': 'passed', 'scope': 'CPU adversarial source guards only',
                'command': [sys.executable, str(ROOT / 'scripts/unreal/test_exterior_canopy_transmission.py'), '-v'],
                'exitCode': tests.returncode, 'stdout': tests.stdout, 'stderr': tests.stderr,
                'nativeExecuted': False, 'nativeAppearanceAccepted': False})
    plan = {'schema': guard.SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'status': guard.STATUS,
            'generatedAt': guard.now(), 'activeDesign': report['activeDesign'], 'setbacksMm': report['setbacksMm'],
            'baseNativeReport': report_pin, 'baseContentInventory': guard.pin(output / 'base-content-inventory.json'),
            'baseProjectProof': guard.pin(output / 'base-project-proof.json'),
            'consumedSourceSnapshot': guard.pin(snapshot_path), 'frozenPipeline': frozen, 'newSourceFiles': new_sources,
            'engineEvidence': engine_files, 'nativeModule': module_pin, 'nativeEngineBuildId': own_module_map['BuildId'],
            'baseProjectModuleMap': guard.pin(project / 'Binaries/Mac/UnrealEditor.modules'),
            'sourceGuardTests': guard.pin(output / 'source-guard-tests.json'),
            'sourceScope': 'Two full Material duplicates; one scalar 0.08 to 0.24; 23 exact grove HISM leaf overrides / 78 trees.',
            'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
            'shippingPackageProduced': False, **scope}
    plan_file = output / 'canopy-transmission-plan.json'
    guard.write(plan_file, plan)
    guard.validate_plan(plan, plan_file)
    importer, materials = guard.frozen_modules(plan)
    guard.require(importer.ROOT == materials.ROOT == base / 'source-freeze/consumed-native-r1/workspace'
                  and callable(importer.readback) and callable(importer.helper.witness)
                  and callable(materials.graph_snapshot), 'Frozen readback helper load differs')
    for record in engine_files.values(): guard.check_pin(record)
    guard.require(guard.pin(report_path) == report_pin and guard.inventory(project / 'Content') == content
                  and guard.project_proof(project) == proof, 'Read-only original native base drifted during study')
    guard.write(output / 'summary.json', {'status': guard.STATUS, 'owner': OWNER, 'selectedPlan': guard.pin(plan_file),
        'sourceGuardTestsPassed': True, 'sourceNativeInventoryVerified': True, 'frozenReadbackImportValidated': True,
        'nativeExecuted': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingPackageProduced': False, 'audit': scope['audit'],
        'baseContentFiles': len(content), 'baseContentLogicalBytes': sum(r['bytes'] for r in content.values()),
        'baseProtectedProjectFiles': len(proof), 'baseProtectedProjectLogicalBytes': sum(r['bytes'] for r in proof.values()),
        'nativeModule': module_pin, 'engineBuildId': own_module_map['BuildId'],
        'directTransmissionTermMultiplier': 3, 'pixelBrightnessMultiplierClaimed': False,
        'nextEvidence': 'Root-owned fresh R17 native overlay, then unchanged-camera fresh Editor-game PNG comparison.'})
    files = {p.name: guard.pin(p) for p in sorted(output.iterdir()) if p.is_file()}
    guard.write(output / 'source-receipt.json', {'status': 'frozen-source-only-canopy-transmission-study', 'owner': OWNER,
                'generatedAt': guard.now(), 'files': files, 'fileCount': len(files),
                'nativeExecuted': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
                'performanceAccepted': False})
    print(json.dumps({'status': guard.STATUS, 'plan': guard.pin(plan_file), 'receipt': guard.pin(output / 'source-receipt.json'),
                      'audit': scope['audit'], 'nativeExecuted': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default=str(ROOT / 'output/unreal/exterior-20261001-r16a'))
    parser.add_argument('--output', default=str(ROOT / 'output/unreal/exterior-canopy-transmission-20261001-r1-study'))
    args = parser.parse_args()
    produce(args.base, args.output)
