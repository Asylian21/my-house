"""Portable CPU binding negatives; no Unreal, ignored output fixtures or asset writes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import water_binding as w


class WaterBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = w.load_binding(w.RESOURCE)
        cls.old_paths = [w.PLUGIN / 'Resources' / name for name in
                         ['receiver-contract.json', 'source-binding.json',
                          'receiver-identity-policy.json', 'receiver-identity-test-fixture.json']]
        cls.old_hashes = {str(path): w.sha(path) for path in cls.old_paths}

    def fixtures(self):
        b = copy.deepcopy(self.binding); waves = b['authoredWaves']
        normal = {'status': 'native-water-normal-graph-readback-validated',
                  'normalOutputConnected': True, 'worldSpaceNormal': True, 'cosineCount': 12,
                  'reachableExpressionCount': 138, 'waves': b['savedNormalRows'],
                  'initialGradient': [0, 0, 0], 'upVector': [0, 0, 1],
                  'absoluteWorldPositionCm': True, 'sharedTime': True,
                  'timeIgnoresPause': False, 'timePeriodOverride': False,
                  'defaultChannelsVerified': True, 'internalNodeNamesUsed': False, 'renderedVerified': False}
        graph = {'waterNormalReadback': normal}
        source = {'WAVES': waves, 'ABSORPTION_PER_METRE': b['absorptionPerMetre'],
                  'SCATTERING_PER_METRE': b['scatteringPerMetre']}
        assets = {w.MATERIAL: b['material']['sha256']}
        saved = {'status': 'fresh-process-saved-water-graph-validated', 'readOnly': True, 'freshProcess': True,
                 'sourceAssetsUnchanged': True, 'renderedVerified': False, 'asset': w.ASSET,
                 'importReceiptSha256': 'a'*64, 'sourceWriterSha256': b['sourceWriter']['sha256'],
                 'declaredWaves': copy.deepcopy(waves), 'graph': copy.deepcopy(graph), 'assetHashes': assets}
        optics = {'status': 'optics-authored', 'writerSha256': b['sourceWriter']['sha256'],
                  'water': {'waves': copy.deepcopy(waves), 'absorptionPerMetre': b['absorptionPerMetre'],
                            'scatteringPerMetre': b['scatteringPerMetre'], 'ior': 1.333,
                            'waterLevelMm': -12, 'displacement': False,
                            'nativeCoefficientUnit': '1/cm; per-metre parameters multiplied by 0.01'},
                  'masters': [{'sourceFamily': 'real-pool-water', 'asset': w.ASSET, 'saved': True,
                               'shadingModel': 'SingleLayerWater', 'compileErrors': [], 'graph': graph}],
                  'generatedAssetHashes': assets}
        imported = {'status': 'import-validated', 'hostProcess': {'code': 0, 'cleanExit': True},
                    'optics': optics, 'pipelineFiles': {w.WRITER: b['sourceWriter']['sha256']},
                    'finalAssetHashes': assets}
        return source, imported, saved

    def validate(self, fixtures):
        w.validate_evidence(*fixtures, self.binding['sourceWriter']['sha256'], 'a'*64)

    def test_exact_saved_float32_source_and_json_numeric_forms(self):
        self.validate(self.fixtures())
        rows = self.binding['savedNormalRows']
        self.assertEqual(rows, w.expected_rows(self.binding['authoredWaves']))
        # JSON.parse/stringify may encode native 0.0 as 0; numeric values stay exact.
        rows = json.loads(json.dumps(rows).replace('0.0,', '0,'))
        w.validate_rows(rows, self.binding['authoredWaves'])

    def test_every_saved_numeric_field_and_last_wave_are_checked(self):
        for key in ['cosinePeriod', 'timeCyclesPerSecond', 'phaseCycles',
                    'positionCyclesPerCm', 'slopeVector']:
            for index in [0, 11]:
                with self.subTest(key=key, index=index):
                    rows = copy.deepcopy(self.binding['savedNormalRows'])
                    if isinstance(rows[index][key], list):
                        rows[index][key][0] += 1e-9
                    else:
                        rows[index][key] += 1e-9
                    with self.assertRaisesRegex(ValueError, 'exact float32'):
                        w.validate_rows(rows, self.binding['authoredWaves'])

    def test_count_order_bool_extra_and_nonfinite_rows_refuse(self):
        mutations = [lambda r: r.pop(), lambda r: r.append(copy.deepcopy(r[-1])),
                     lambda r: r.reverse(), lambda r: r[0].update(index=False),
                     lambda r: r[0].update(unreviewed=1),
                     lambda r: r[0].update(phaseCycles=float('nan')),
                     lambda r: r[11]['slopeVector'].__setitem__(2, float('inf')),
                     lambda r: r[0]['positionCyclesPerCm'].__setitem__(2, False)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                rows = copy.deepcopy(self.binding['savedNormalRows']); mutate(rows)
                with self.assertRaises(ValueError):
                    w.validate_rows(rows, self.binding['authoredWaves'])

    def test_source_units_direction_and_count_refuse(self):
        mutations = [lambda a: a.pop(), lambda a: a[0].update(wavelengthMetres=0),
                     lambda a: a[0].update(amplitudeMetres=-1),
                     lambda a: a[0].update(phaseCycles=1),
                     lambda a: a[0].update(direction=[1, 1]),
                     lambda a: a[0].update(direction=[True, 0]),
                     lambda a: a[0].update(wavelengthMetres=float('nan'))]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                waves = copy.deepcopy(self.binding['authoredWaves']); mutate(waves)
                with self.assertRaises(ValueError):
                    w.validate_waves(waves)

    def test_evidence_provenance_and_graph_negatives(self):
        mutations = [lambda s, i, r: s['WAVES'][11].update(phaseCycles=.5),
                     lambda s, i, r: r.update(importReceiptSha256='b'*64),
                     lambda s, i, r: r.update(sourceWriterSha256='b'*64),
                     lambda s, i, r: i['pipelineFiles'].update({w.WRITER: 'b'*64}),
                     lambda s, i, r: i['hostProcess'].update(code=1),
                     lambda s, i, r: i['hostProcess'].update(cleanExit=False),
                     lambda s, i, r: r.update(freshProcess=False),
                     lambda s, i, r: i['optics']['water'].update(absorptionPerMetre=[0, 0, 0]),
                     lambda s, i, r: i['optics']['water'].update(ior=1.4),
                     lambda s, i, r: i['optics']['water'].update(displacement=True),
                     lambda s, i, r: i['optics']['masters'][0].update(saved=False),
                     lambda s, i, r: i['optics']['masters'].append(copy.deepcopy(i['optics']['masters'][0])),
                     lambda s, i, r: r['graph']['waterNormalReadback'].update(cosineCount=4),
                     lambda s, i, r: r['graph']['waterNormalReadback'].update(defaultChannelsVerified=False)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                fixtures = self.fixtures(); mutate(*fixtures)
                with self.assertRaises(ValueError):
                    self.validate(fixtures)

    def test_native_policies_even_when_both_receipts_agree(self):
        for key, value in [('sharedTime', False), ('worldSpaceNormal', False), ('timeIgnoresPause', True),
                           ('timePeriodOverride', True), ('reachableExpressionCount', 137),
                           ('initialGradient', [1, 0, 0]), ('upVector', [0, 1, 0])]:
            with self.subTest(key=key):
                fixtures = self.fixtures()
                fixtures[1]['optics']['masters'][0]['graph']['waterNormalReadback'][key] = value
                fixtures[2]['graph']['waterNormalReadback'][key] = value
                with self.assertRaises(ValueError):
                    self.validate(fixtures)

    def test_ast_never_executes_and_rejects_ambiguous_or_nonliteral(self):
        source, _, _ = self.fixtures()
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'optics.py'
            literal = '\n'.join(k + ' = ' + repr(v) for k, v in source.items())
            p.write_text("import unreal\nraise RuntimeError('must never execute')\n" + literal)
            self.assertEqual(w.source_constants(p), source)
            for suffix in ['\nWAVES = []', '\nWAVES = list()']:
                p.write_text(literal + suffix)
                with self.assertRaises(ValueError):
                    w.source_constants(p)
            p.write_text(literal.replace('WAVES = ', 'WAVES = other = '))
            with self.assertRaises(ValueError):
                w.source_constants(p)

    def test_offline_capture_accepts_only_reviewed_bytes_and_header(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'active-water-binding.json'; p.write_bytes(w.RESOURCE.read_bytes())
            with patch.object(w, 'build_binding', side_effect=RuntimeError('must not access live sources')):
                self.assertEqual(w.load_binding(p), self.binding)
            changed = copy.deepcopy(self.binding); changed['savedNormalRows'][11]['phaseCycles'] += .1
            p.write_bytes(w.binding_bytes(changed))
            with self.assertRaisesRegex(ValueError, 'Unreviewed'):
                w.load_binding(p)
            p.write_bytes(w.RESOURCE.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'Unreviewed'):
                w.load_binding(p)
            p.write_bytes(w.RESOURCE.read_bytes())
            header = Path(directory) / 'header.h'; header.write_text(w.HEADER.read_text().replace('TEXT(', 'BAD('))
            with patch.object(w, 'HEADER', header), self.assertRaisesRegex(ValueError, 'Compiled active water pins'):
                w.load_binding(p)

    def test_current_source_revalidation_and_path_escape_fail_closed(self):
        changed = copy.deepcopy(self.binding); changed['material']['sha256'] = 'b'*64
        with patch.object(w, 'build_binding', return_value=changed), self.assertRaisesRegex(ValueError, 'current source'):
            w.load_binding(w.RESOURCE, verify_sources=True, root=Path.cwd())
        with tempfile.TemporaryDirectory() as directory:
            for relative in ['../escape', '/absolute']:
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    w.root_path(Path(directory), relative)

    def test_geometry_record_and_ordered_face_disagreement_refuse(self):
        contract = w.read_json(w.PLUGIN / 'Resources/receiver-contract.json')
        scene = {'objects': copy.deepcopy(contract['receiverObjects'])}
        scene['objects'][0]['materialSlots'] = ['WRONG']
        with self.assertRaisesRegex(ValueError, 'Current receiver record'):
            w.verify_receiver_geometry(contract, scene, 'must-not-open')
        scene = {'objects': copy.deepcopy(contract['receiverObjects'])}
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'empty.obj'; p.write_text('# No source faces\n')
            with self.assertRaisesRegex(ValueError, 'Current OBJ receiver triangles'):
                w.verify_receiver_geometry(contract, scene, p)

    def test_duplicate_and_nonfinite_json_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'bad.json'
            for raw in ['{"waveCount":12,"waveCount":4}', '{"phase":NaN}', '{"phase":Infinity}']:
                p.write_text(raw)
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    w.read_json(p)

    def test_historical_contract_and_identity_remain_unchanged(self):
        self.assertEqual({str(path): w.sha(path) for path in self.old_paths}, self.old_hashes)
        old = w.read_json(self.old_paths[0])
        self.assertEqual(len(old['authoredWaves']), 4)
        self.assertEqual(w.sha(self.old_paths[0]), 'c7c8011b3d7623e8780c30ea77775472a0cab7ebefa0f5cb97528f96580d404a')
        self.assertEqual(w.sha(self.old_paths[0]), self.binding['receiverContractSha256'])
        self.assertNotEqual(old['authoredWaves'], self.binding['authoredWaves'])


if __name__ == '__main__':
    unittest.main()
