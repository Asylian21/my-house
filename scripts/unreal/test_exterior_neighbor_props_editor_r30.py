"""Five saved-consumer contracts; no native or inherited test/source replay."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('_r30_actual_saved_consumer',
    ROOT/'scripts/unreal/exterior-neighbor-props-editor-check-r30.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class SavedConsumerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = c.read(c.REPORT)
        cls.plan = c.read(cls.report['selectedPlan']['path'])
        cls.pf = c.read(cls.report['sourcePreflight']['path'])
        cls.terminal = c.read(c.PROCESS_PATH)
        cls.raw = c.read(c.RAW_PATH)
        cls.audit = c.read(c.ROOT_AUDIT_PATH)
        cls.bundle = {'binding': cls.report['binding'],
            'source': {'proposalPin': cls.report['sourceProposal']},
            'base': {'reportPin': cls.report['baseNativeReport']},
            'nodePoseCalibration': cls.report['nodePoseCalibration'],
            'constructorCalibration': cls.report['constructorCalibration']}

    def denial(self, function, *args):
        with self.assertRaises(RuntimeError):
            function(*args)

    def test_01_closed_r3_header_rejects_failed_legacy_or_foreign(self):
        c.report_header(self.report, self.plan, self.pf, self.bundle)
        for field, value in (('status', 'failed'), ('schemaVersion', 2),
                             ('nativeProcessId', 47288), ('nativeApplied', False)):
            wrong = copy.deepcopy(self.report); wrong[field] = value
            self.denial(c.report_header, wrong, self.plan, self.pf, self.bundle)

    def test_02_closed_root_terminal_census_and_command_are_exact(self):
        self.assertTrue(c.validate_terminal(self.report, self.terminal, self.raw))
        for field, value in (('code', 255), ('signal', 'SIGTERM'), ('pid', 47288)):
            wrong = copy.deepcopy(self.raw); wrong[field] = value
            self.denial(c.validate_terminal, self.report, self.terminal, wrong)
        wrong = copy.deepcopy(self.terminal)
        wrong['sourcePinsBeforeNative'].pop(next(iter(wrong['sourcePinsBeforeNative'])))
        self.denial(c.validate_terminal, self.report, wrong, self.raw)

    def test_03_current_byte_audit_is_distinct_from_fresh_native_decode(self):
        self.assertTrue(c.validate_root_audit(self.audit, self.report))
        for field, value in (('currentProjectFiles', 4235), ('onlyOriginalMapChanged', False),
                             ('newNativeActorOrAttributeDecodeByAudit', True)):
            wrong = copy.deepcopy(self.audit); wrong[field] = value
            self.denial(c.validate_root_audit, wrong, self.report)
        wrong = copy.deepcopy(self.audit); wrong['newOwnedPackageTypes']['meshes'] = 3
        self.denial(c.validate_root_audit, wrong, self.report)

    def test_04_actual_material_readbacks_reject_policy_and_ownership_changes(self):
        maps = c.module('_r30_pure_saved_material_fields',
            ROOT/'scripts/unreal/exterior-neighbor-props-materials-r39.py')
        built = self.report['materialReport']
        model = 'garden_hose_wall_mounted_01'; row = built['materials'][model]
        c.validate_material_record(maps, built, model, row)
        wrong = copy.deepcopy(row); wrong['textures']['normalGL']['snapshot']['srgb'] = True
        self.denial(c.validate_material_record, maps, built, model, wrong)
        wrong = copy.deepcopy(row); wrong['metadata']['BreziGeneratedBy'] = 'foreign-writer'
        self.denial(c.validate_material_record, maps, built, model, wrong)
        wrong = copy.deepcopy(row); wrong['policy']['two_sided'] = False
        self.denial(c.validate_material_record, maps, built, model, wrong)

    def test_05_source_positive_zero_and_measured_serialization_cannot_be_rewritten(self):
        wrong_report, wrong_plan, wrong_pf = (copy.deepcopy(v) for v in (self.report, self.plan, self.pf))
        root = next(iter(wrong_report['constructorCalibration']['sixRootConstructors']))
        for value in (wrong_report, wrong_plan, wrong_pf):
            value['constructorCalibration']['sixRootConstructors'][root]['actualValues'][1][1] = -0.
        self.denial(c.report_header, wrong_report, wrong_plan, wrong_pf, self.bundle)
        wrong = copy.deepcopy(self.report)
        part = next(iter(wrong['constructorCalibration']['compositions']))
        wrong['constructorCalibration']['compositions'][part]['recoveredValues'][0][2][0] += .01
        self.denial(c.report_header, wrong, self.plan, self.pf, self.bundle)


if __name__ == '__main__':
    unittest.main(verbosity=2)
