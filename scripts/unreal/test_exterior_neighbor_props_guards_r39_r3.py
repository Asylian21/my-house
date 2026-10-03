"""Four changed constructor/proof contracts only; no inherited suite replay."""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('_r39r3_exact_constructor_guard',
    ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39-r3.py')
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


class CalibrationContracts(unittest.TestCase):
    BUNDLE = None
    @classmethod
    def setUpClass(cls):
        cls.first, cls.parts, _ = g.prior_failure_and_constructors()
        cls.source = cls.BUNDLE['source'] if cls.BUNDLE is not None else {'proposal': g.read(g.SOURCE)}
        cls.probe = g.read(g.COMPOSITION_REPORT)
        cls.calibration = g.validate_composition_probe(cls.probe,cls.source,cls.first,cls.parts)

    def denial(self, function, *args):
        with self.assertRaises(RuntimeError): function(*args)

    def test_01_actual_eight_member_source_policy_and_readonly_proof(self):
        self.assertEqual(len(self.calibration['sixRootConstructors']),6)
        self.assertEqual(sum(len(v['assemblyRootIds']) for v in self.calibration['compositions'].values()),8)
        self.assertTrue(self.calibration['allOriginalDesiredValuesPreservedBinary64'])
        self.assertFalse(self.calibration['epsilonOrToleranceUsed'])
        for receipt in self.calibration['sixRootConstructors'].values():
            self.assertEqual(struct.pack('<d',receipt['actualValues'][1][1]),struct.pack('<d',0.))
        for field,value in (('newGeometryAttributeDecodePerformed',True),
                            ('historicalExactFunctionOrZeroConventionsGloballyChanged',True),
                            ('composedMembersObserved',7)):
            wrong=copy.deepcopy(self.probe);wrong[field]=value
            self.denial(g.validate_composition_probe,wrong,self.source,self.first,self.parts)

    def test_02_original_positive_zero_and_nonzero_coefficients_exact(self):
        key=next(iter(self.probe['sixRootConstructors']))
        wrong=copy.deepcopy(self.probe)
        wrong['sixRootConstructors'][key]['actualValues'][1][1]=-0.
        self.denial(g.validate_composition_probe,wrong,self.source,self.first,self.parts)
        wrong=copy.deepcopy(self.probe)
        v=wrong['sixRootConstructors'][key]['actualValues'][1][2]
        bits=struct.unpack('<Q',struct.pack('<d',v))[0]
        wrong['sixRootConstructors'][key]['actualValues'][1][2]=struct.unpack('<d',struct.pack('<Q',bits+1))[0]
        self.denial(g.validate_composition_probe,wrong,self.source,self.first,self.parts)
        wrong=copy.deepcopy(self.probe);part=next(iter(wrong['sourceNodes']))
        wrong['sourceNodes'][part]['actualImportedSourcePart']['sourcePart']='label_only_same_count'
        self.denial(g.validate_composition_probe,wrong,self.source,self.first,self.parts)

    def test_03_only_differing_new_local_zero_can_use_finite_intermediate(self):
        events=[e for r in self.probe['sixRootConstructors'].values()
                for field in r['newLocalScalarEvents'] for e in field['scalarWrites']]
        repaired=next(e for e in events if e['zeroBitMismatchIntermediateUsed'])
        self.assertTrue(g.validate_new_local_scalar_event(repaired,repaired['axis'],repaired['requested']['value'],repaired['newLocalWrapperType']))
        wrong=copy.deepcopy(repaired);wrong['finiteIntermediateObserved']=g.binary64_record(1.0000000000000002)
        self.denial(g.validate_new_local_scalar_event,wrong,wrong['axis'],wrong['requested']['value'],wrong['newLocalWrapperType'])
        ordinary=next(e for e in events if e['requested']['value'] != 0.)
        wrong=copy.deepcopy(ordinary);wrong['zeroBitMismatchIntermediateUsed']=True
        wrong['finiteIntermediateRequested']=g.binary64_record(1.);wrong['finiteIntermediateObserved']=g.binary64_record(1.)
        self.denial(g.validate_new_local_scalar_event,wrong,wrong['axis'],wrong['requested']['value'],wrong['newLocalWrapperType'])

    def test_04_all_actual_native_arrays_and_order_are_exact(self):
        fields=('assemblyRootIds','assemblyInputValues','originalImportedNodeValues','composedInputValues','recoveredValues','storedMatrices')
        measurement={key:{field:copy.deepcopy(v[field]) for field in fields}
                     for key,v in self.calibration['compositions'].items()}
        bundle={'constructorCalibration':self.calibration}
        self.assertTrue(g.validate_constructor_measurements(measurement,bundle))
        key=next(iter(measurement))
        wrong=copy.deepcopy(measurement);wrong[key]['assemblyRootIds'].reverse()
        self.denial(g.validate_constructor_measurements,wrong,bundle)
        wrong=copy.deepcopy(measurement);old=wrong[key]['storedMatrices'][0][0][0]
        bits=struct.unpack('<Q',struct.pack('<d',old))[0]
        wrong[key]['storedMatrices'][0][0][0]=struct.unpack('<d',struct.pack('<Q',bits+1))[0]
        self.denial(g.validate_constructor_measurements,wrong,bundle)
        wrong=copy.deepcopy(measurement);wrong[key]['assemblyInputValues'][0][1][1]=-0.
        self.denial(g.validate_constructor_measurements,wrong,bundle)
        wrong=copy.deepcopy(self.probe)
        target=next(v for v in wrong['compositions'].values() if any(v['recoveredMismatchPaths']))
        index=next(i for i,v in enumerate(target['recoveredMismatchPaths']) if v)
        target['recoveredMismatchPaths'][index]=[]
        self.denial(g.validate_composition_probe,wrong,self.source,self.first,self.parts)


if __name__ == '__main__': unittest.main(verbosity=2)
