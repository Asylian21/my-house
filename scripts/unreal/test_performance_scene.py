"""Conservative migration boundaries; no Unreal process is started."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from performance_scene_policy import DETAIL_FLAGS, LUMEN_DEFAULTS, apply_detail, detail_policy, read_detail_flag, set_detail_flag, verify_detail

SPEC = importlib.util.spec_from_file_location('performance_optimize', Path(__file__).with_name('performance-optimize.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Component:
    def __init__(self):
        self.properties = {}
        self.owner = VegetationActor(self)

    def set_editor_property(self, name, value):
        if name == 'enable_density_scaling':
            raise RuntimeError('UE 5.8 does not expose this property to Python')
        self.properties[name] = value

    def get_editor_property(self, name):
        if name == 'enable_density_scaling':
            raise RuntimeError('UE 5.8 does not expose this property to Python')
        return self.properties[name]

    def get_owner(self):
        return self.owner

    def set_cull_distances(self, start, end):
        self.properties.update(instance_start_cull_distance=start, instance_end_cull_distance=end)


class VegetationActor:
    def __init__(self, component):
        self.instances = component
        self.density_enabled = False
        self.accept_density_change = True

    def get_editor_property(self, name):
        assert name == 'instances'
        return self.instances

    def set_detail_density_scaling(self, enabled):
        if not self.accept_density_change:
            return False
        self.density_enabled = enabled
        return True

    def get_detail_density_scaling(self):
        return self.density_enabled


class PerformanceSceneTests(unittest.TestCase):
    def test_only_tagged_small_detail_can_scale(self):
        for tags, label in [(['DOM_00001'], 'plants_lawn'), ([], 'plants_grass'),
                            (['BreziRural20260923'], 'windbreak_natural_understorey'),
                            (['BreziRural20260923'], 'windbreak_0_1'),
                            (['BreziGenerated'], 'lawn'), (['BreziVegetation'], 'plants_hedge')]:
            with self.subTest(tags=tags, label=label):
                self.assertIsNone(detail_policy(tags, label))
        for tags, label, distances in [(['BreziPhotorealLawn'], 'lawn', (1500, 2500)),
                                      (['BreziLawnDetail'], 'legacy', (600, 1200)),
                                      (['BreziRural20260923'], 'plants_1_2_ragweed', (6000, 8000))]:
            c = Component()
            policy = detail_policy(tags, label)
            apply_detail(c, policy)
            verify_detail(c, policy)
            self.assertEqual(policy['cullCm'], distances)
            self.assertFalse(c.properties['visible_in_ray_tracing'])
            self.assertFalse(c.properties['cast_shadow'])
            self.assertTrue(read_detail_flag(c, 'enable_density_scaling'))
            self.assertEqual(set(c.properties), (set(DETAIL_FLAGS) - {'enable_density_scaling'})
                             | {'instance_start_cull_distance', 'instance_end_cull_distance'})

    def test_readback_refuses_shadow_raytracing_density_or_cull_drift(self):
        policy = detail_policy(['BreziPhotorealLawn'], 'lawn')
        for name in [*DETAIL_FLAGS, 'instance_end_cull_distance']:
            c = Component()
            apply_detail(c, policy)
            if name == 'enable_density_scaling':
                c.owner.density_enabled = False
            else:
                c.properties[name] = 0 if name == 'instance_end_cull_distance' else not c.properties[name]
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                verify_detail(c, policy)

    def test_density_bridge_refuses_foreign_component_and_native_rejection(self):
        c = Component()
        c.owner.instances = Component()
        with self.assertRaisesRegex(RuntimeError, 'owned vegetation HISM'):
            set_detail_flag(c, 'enable_density_scaling', True)
        with self.assertRaisesRegex(RuntimeError, 'owned vegetation HISM'):
            read_detail_flag(c, 'enable_density_scaling')
        c.owner.instances = c
        c.owner.accept_density_change = False
        with self.assertRaisesRegex(RuntimeError, 'Native density scaling rejected'):
            set_detail_flag(c, 'enable_density_scaling', True)
        self.assertFalse(read_detail_flag(c, 'enable_density_scaling'))
        c.owner.accept_density_change = True
        set_detail_flag(c, 'enable_density_scaling', True)
        self.assertTrue(read_detail_flag(c, 'enable_density_scaling'))
        set_detail_flag(c, 'enable_density_scaling', False)
        self.assertFalse(read_detail_flag(c, 'enable_density_scaling'))

    def test_only_six_lumen_cost_defaults_are_changed(self):
        self.assertEqual(len(LUMEN_DEFAULTS), 6)
        self.assertEqual({v for k, v in LUMEN_DEFAULTS.items() if 'distance' not in k}, {1.0})
        self.assertEqual({v for k, v in LUMEN_DEFAULTS.items() if 'distance' in k}, {10000.0})

    def test_light_witness_ignores_struct_identity_but_preserves_every_light_value(self):
        class Color:
            def __init__(self):
                self.r, self.g, self.b, self.a = 255, 240, 230, 255

        def light():
            c = Component()
            c.properties.update(intensity=1250.0, light_color=Color(), temperature=2700.0,
                                cast_shadows=True, mobility='Movable')
            return c

        first, reloaded = light(), light()
        self.assertNotEqual(str(first.properties['light_color']), str(reloaded.properties['light_color']))
        self.assertEqual(M.light_witness(first), M.light_witness(reloaded))
        for channel in 'rgba':
            changed = light()
            setattr(changed.properties['light_color'], channel, 0)
            with self.subTest(channel=channel):
                self.assertNotEqual(M.light_witness(first), M.light_witness(changed))
        for name, value in [('intensity', 1), ('temperature', 5000), ('cast_shadows', False), ('mobility', 'Static')]:
            changed = light()
            changed.properties[name] = value
            with self.subTest(property=name):
                self.assertNotEqual(M.light_witness(first), M.light_witness(changed))

    def test_only_map_bytes_may_change(self):
        before = {M.MAP_FILE: 'map', 'Brezi/Geometry/Wall.uasset': 'mesh',
                  'Data/walking.json': 'walking', 'Data/viewpoints.json': 'camera',
                  'Brezi/Materials/Glass.uasset': 'material'}
        M.validate_changes(before, {**before, M.MAP_FILE: 'new-map'})
        for path in before:
            if path == M.MAP_FILE:
                continue
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'Protected content'):
                M.validate_changes(before, {**before, path: 'changed'})
        for changed in [dict(list(before.items())[1:]), {**before, 'Brezi/New.uasset': 'new'}]:
            with self.assertRaisesRegex(RuntimeError, 'inventory'):
                M.validate_changes(before, changed)

    def test_existing_active_nested_and_external_targets_refused(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(M, 'ROOT', Path(tmp).resolve()):
            parent = Path(tmp).resolve()/'output/unreal'
            parent.mkdir(parents=True)
            source, output = parent/'baseline', parent/'fresh'
            self.assertEqual(M.checked_paths(source, output), (source, output))
            for target in [source, source/'nested', parent, Path(tmp)/'other']:
                with self.subTest(target=str(target)), self.assertRaises(RuntimeError):
                    M.checked_paths(source, target)
            (parent/'model-refresh-current.json').write_text(json.dumps({'output': str(output)}))
            with self.assertRaisesRegex(RuntimeError, 'active package'):
                M.checked_paths(source, output)
            (parent/'model-refresh-current.json').unlink()
            output.mkdir()
            (output/'model-package.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'historical output'):
                M.checked_paths(source, output)


if __name__ == '__main__':
    unittest.main()
