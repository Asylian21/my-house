"""Host boundaries for the isolated texture probe; never launches Unreal."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('fire_probe', Path(__file__).with_name('realism-fire-texture-probe.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class FireProbeTests(unittest.TestCase):
    def test_project_has_no_runtime_modules_or_network_plugin(self):
        result = M.descriptor()
        self.assertNotIn('Modules', result)
        self.assertTrue(result['DisableEnginePluginsByDefault'])
        enabled = [row for row in result['Plugins'] if row['Enabled']]
        self.assertEqual([row['Name'] for row in enabled], ['PythonScriptPlugin', 'EditorScriptingUtilities'])
        self.assertTrue(all(row['TargetAllowList'] == ['Editor'] for row in enabled))
        self.assertEqual([row['Name'] for row in result['Plugins'] if not row['Enabled']], ['NetworkPredictionExtras', 'NetworkPrediction'])

    def test_dependencies_are_only_core_classes_or_the_owned_package(self):
        package = M.PREFIX + '/T_Fire_SubUV'
        M.validate_dependencies([package, '/Script/Engine', '/Script/CoreUObject'], package)
        for path in ['/Script/NetworkPredictionExtras', '/NetworkPredictionExtras/Texture', '/Game/Other', '/Script/UnrealEd']:
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                M.validate_dependencies([path], package)

    def test_probe_cannot_target_existing_model_or_outside_directory(self):
        accepted = M.ROOT / 'output/unreal/realism-fire-texture-probe-test'
        self.assertEqual(M.checked_output(str(accepted)), accepted)
        for path in ['output/unreal/realism-20260926-r5', 'output/unreal/realism-fire-texture-probe-test/nested', '../realism-fire-texture-probe-test']:
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                M.checked_output(path)

    def test_png_header_checks_full_resolution_and_records_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'export.png'
            path.write_bytes(b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>IIBBBBB', 1024, 1024, 8, 6, 0, 0, 0) + b'\0' * 4)
            result = M.png_info(path)
            self.assertEqual((result['width'], result['height'], result['colorType']), (1024, 1024, 6))
            self.assertEqual(result['sha256'], M.sha(path))
            path.write_bytes(b'thumbnail is not source png')
            with self.assertRaises(RuntimeError): M.png_info(path)

    def test_prepared_input_pins_fail_on_asset_and_descriptor_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'Probe.uproject'
            asset = Path(tmp) / 'Texture.uasset'
            M.write(project, M.descriptor()); asset.write_bytes(b'original')
            report = {'project': str(project), 'inputPins': {str(asset): M.sha(asset), str(project): M.sha(project)}}
            M.check_pins(report)
            asset.write_bytes(b'changed')
            with self.assertRaises(RuntimeError): M.check_pins(report)
            asset.write_bytes(b'original')
            changed = M.descriptor(); changed['Modules'] = [{'Name': 'NetworkPredictionExtras'}]
            M.write(project, changed)
            report['inputPins'][str(project)] = M.sha(project)
            with self.assertRaises(RuntimeError): M.check_pins(report)


if __name__ == '__main__': unittest.main()
