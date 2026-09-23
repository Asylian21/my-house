"""Recovery trust boundaries use synthetic packages; no native content is touched."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('archviz_import', Path(__file__).with_name('archviz-import.py'))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name).resolve()
        self.root_patch = patch.object(M, 'ROOT', self.root); self.root_patch.start()
        self.output = self.root / 'output/unreal/archviz-test'; self.project = self.output / 'Project/BreziTwin'
        self.content = self.project / 'Content/Brezi'; self.content.mkdir(parents=True)
        (self.output / 'profile.json').write_text(json.dumps({'archvizGame': True, 'project': str(self.project),
            'geometry': str(self.output / 'geometry')}))
        self.map = self.file('Maps/Brezi.umap', b'closed-map')
        self.mesh = self.file('Geometry/Wall.uasset', b'immutable-source-geometry')
        self.material = self.file('ModelRefresh/Materials/M_MAT_0001.uasset', b'baseline-material')
        self.baseline_inventory = M.inventory(self.content)
        self.report = {'mapFileSha256': M.sha(self.map), 'finalAssetHashes': {k:v for k,v in self.baseline_inventory.items()
            if k != M.relative(self.map)}, 'materials': {'materials': {'MAT_0001': {'asset':
            '/Game/Brezi/ModelRefresh/Materials/M_MAT_0001.M_MAT_0001'}}}}
        (self.output / 'model-refresh-import-report.json').write_text(json.dumps(self.report))
        self.inputs = {M.relative(self.output / 'model-refresh-import-report.json'): M.sha(self.output / 'model-refresh-import-report.json')}
        class Recipes:
            def recipe(self, value): return {'kind': 'oak'}
        self.state = M.checkpoint(self.output, self.content, self.report, self.inputs, Recipes(), {'materials': {'MAT_0001': {}}})

    def tearDown(self):
        self.root_patch.stop(); self.temp.cleanup()

    def file(self, relative, data):
        path = self.content / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data); return path

    def failed(self):
        self.material.write_bytes(b'partial-enrichment'); self.map.write_bytes(b'new-lights')
        self.new = self.file('Archviz/Textures/T_Oak.uasset', b'owned-new-texture')
        self.state.update(status='failed-recoverable', failedInventory=M.inventory(self.content))
        M.write(self.output / 'archviz-checkpoint/checkpoint.json', self.state)

    def test_restores_only_checkpointed_material_and_map_preserving_geometry(self):
        self.failed()
        with patch.object(M.os, 'kill', side_effect=ProcessLookupError): M.restore(self.output)
        self.assertEqual(M.inventory(self.content), self.baseline_inventory)
        self.assertFalse(self.new.exists()); self.assertEqual(self.mesh.read_bytes(), b'immutable-source-geometry')
        self.assertEqual(M.read(self.output / 'archviz-checkpoint/checkpoint.json')['status'], 'restored-baseline')

    def test_refuses_concurrent_changes_after_caught_failure(self):
        self.failed(); self.new.write_bytes(b'unknown-later-write')
        with patch.object(M.os, 'kill', side_effect=ProcessLookupError), self.assertRaisesRegex(RuntimeError, 'changed after recorded failure'):
            M.restore(self.output)
        self.assertEqual(self.material.read_bytes(), b'partial-enrichment')

    def test_refuses_protected_geometry_mutation_even_if_failure_inventory_matches(self):
        self.mesh.write_bytes(b'wrong-wall'); self.failed()
        with patch.object(M.os, 'kill', side_effect=ProcessLookupError), self.assertRaisesRegex(RuntimeError, 'Protected native package changed'):
            M.restore(self.output)

    def test_refuses_packages_outside_reserved_namespace(self):
        self.file('Geometry/Unrelated.uasset', b'unknown-asset'); self.failed()
        with patch.object(M.os, 'kill', side_effect=ProcessLookupError), self.assertRaisesRegex(RuntimeError, 'outside its reserved namespace'):
            M.restore(self.output)

    def test_refuses_restore_while_native_process_is_alive(self):
        self.failed()
        with patch.object(M.os, 'kill', return_value=None), self.assertRaisesRegex(RuntimeError, 'still running'):
            M.restore(self.output)

    def test_requires_explicit_archviz_profile(self):
        profile = M.read(self.output / 'profile.json'); profile['archvizGame'] = False
        M.write(self.output / 'profile.json', profile)
        with self.assertRaisesRegex(RuntimeError, 'explicitly declare'): M.paths(self.output)


if __name__ == '__main__': unittest.main()
