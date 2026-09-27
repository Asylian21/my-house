"""R7 generator identity and exact R6 geometry preservation regression."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class MeadowGeneratorRevision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_directory = ROOT / 'output/unreal/exterior-context-20260926-r6'
        cls.directory = ROOT / 'output/unreal/exterior-context-20260926-r7'
        cls.old = read(cls.old_directory / 'context-plan.json')
        cls.plan = read(cls.directory / 'context-plan.json')
        cls.environment = read(cls.directory / 'build-environment.json')

    def test_native_owner_resolves_to_exact_generator_hash(self):
        owner = ROOT / self.plan['owner']
        self.assertEqual(self.plan['owner'], 'scripts/unreal/exterior-meadow-blades.py')
        self.assertEqual(sha(owner), self.plan['generatorSha256'])
        self.assertEqual(self.environment['inputFiles'][str(owner)], self.plan['generatorSha256'])

    def test_only_owner_generator_and_derivation_changed(self):
        self.assertEqual(set(self.old), set(self.plan))
        changed = {k for k in self.old if self.old[k] != self.plan[k]}
        self.assertEqual(changed, {'owner', 'generatorSha256', 'derivedFrom'})
        self.assertEqual(len(self.plan['meadowBladePlacements']), 382678)
        self.assertEqual(self.plan['derivedFrom']['sha256'], sha(self.old_directory / 'context-plan.json'))

    def test_frozen_r6_generator_is_preserved_and_r7_inputs_all_match(self):
        snapshot = self.old_directory / 'inputs/exterior-meadow-blades-r6.py'
        self.assertEqual(sha(snapshot), self.old['generatorSha256'])
        self.assertEqual(read(self.old_directory / 'generator-source-snapshot.json')['sha256'], sha(snapshot))
        for path, expected in self.environment['inputFiles'].items():
            self.assertEqual(sha(path), expected, path)
        self.assertEqual(self.environment['inputFiles'][str(snapshot)], self.old['generatorSha256'])

    def test_historical_numpy_is_exact_official_wheel_member_without_live_replacement(self):
        archive = self.old_directory / 'inputs/runtime-snapshot'
        receipt = read(archive / 'source-receipt.json')
        metadata = read(archive / 'pypi-numpy-2.5.3.json')
        wheel = next(row for row in metadata['urls'] if row['filename'] == receipt['wheelFile'])
        self.assertEqual(wheel['digests']['sha256'], sha(archive / receipt['wheelFile']))
        self.assertEqual(receipt['metadataUrl'], 'https://pypi.org/pypi/numpy/2.5.3/json')
        self.assertEqual(receipt['wheelUrl'], wheel['url'])
        with zipfile.ZipFile(archive / receipt['wheelFile']) as package:
            recovered = package.read('numpy/__init__.py')
        self.assertEqual(recovered, Path(receipt['snapshotPath']).read_bytes())
        old_pin = read(self.old_directory / 'build-environment.json')['inputFiles'][receipt['originalRuntimePath']]
        self.assertEqual(hashlib.sha256(recovered).hexdigest(), old_pin)
        self.assertEqual(sha(receipt['originalRuntimePath']), self.environment['inputFiles'][receipt['originalRuntimePath']])


if __name__ == '__main__':
    unittest.main()
