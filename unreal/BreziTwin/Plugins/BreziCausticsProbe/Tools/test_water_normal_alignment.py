"""CPU numeric checks of saved water rows against the independent authored reference.

The saved constants and elementary arithmetic are rounded to float32; Python's
cosine is then rounded to float32. This is a convention/precision regression,
not an emulation or validation of Metal transcendental instructions, FMA, LWC
pixel positions, native material evaluation, or a rendered frame.
"""
import copy
import importlib.util
import json
import math
import struct
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, BASE / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


reference = module("receiver_reference")


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def saved_normal(rows, point_metres, seconds, *, flip_y=False, cm_scale=100.0,
                 positive_frequency=False, radians_per_cycle=2 * math.pi):
    """Literal saved-row convention, independent of authoring directions/lengths."""
    position = [f32(f32(v) * cm_scale) for v in point_metres]
    if flip_y:
        position[1] = -position[1]
    total = [0.0, 0.0, 0.0]
    for row in rows:
        spatial = 0.0
        for p, k in zip(position, row["positionCyclesPerCm"]):
            spatial = f32(spatial + f32(p * k))
        frequency = row["timeCyclesPerSecond"]
        if positive_frequency:
            frequency = -frequency
        phase = f32(f32(spatial + f32(f32(seconds) * frequency)) + row["phaseCycles"])
        cosine = f32(math.cos(f32(f32(radians_per_cycle) * phase)))
        total = [f32(a + f32(s * cosine)) for a, s in zip(total, row["slopeVector"])]
    total[2] = f32(total[2] + 1.0)
    length = math.sqrt(sum(v * v for v in total))
    return tuple(f32(v / length) for v in total)


class WaterNormalAlignmentTests(unittest.TestCase):
    # Absolute normal-component error, not a hit-position or radiometric bound.
    # Covers float32 constants/arithmetic versus the independent double formula
    # at the small source pool coordinates and these explicitly bounded times.
    NORMAL_COMPONENT_TOLERANCE = 2e-5

    @classmethod
    def setUpClass(cls):
        binding = module("water_binding")
        cls.water = binding.load_binding(
            BASE.parent / "Resources/active-water-binding.json", verify_sources=False)
        cls.rows = cls.water["savedNormalRows"]
        cls.waves = cls.water["authoredWaves"]
        receiver = json.loads((BASE.parent / "Resources/receiver-contract.json").read_text())
        floor = next(v for v in receiver["receiverObjects"] if v["id"] == "DOM_01720")
        low, high = floor["boundsMm"]["min"], floor["boundsMm"]["max"]
        # Source millimetres -> absolute UE metres: reflect source Y once.
        x0, x1 = low[0] / 1000, high[0] / 1000
        y0, y1 = -high[1] / 1000, -low[1] / 1000
        cls.points = [(x0 + u * (x1 - x0), y0 + v * (y1 - y0),
                       receiver["waterMeanPlaneMetres"])
                      for u, v in ((.137, .263), (.419, .827), (.873, .391), (.631, .157))]
        cls.times = (0.0, .125, 2.0)

    def max_error(self, rows=None, **changes):
        rows = self.rows if rows is None else rows
        maximum = 0.0
        for point in self.points:
            for seconds in self.times:
                expected = reference.normal(point[0], point[1], seconds, self.waves)
                actual = saved_normal(rows, point, seconds, **changes)
                maximum = max(maximum, *(abs(a - b) for a, b in zip(actual, expected)))
        return maximum

    def test_actual_twelve_saved_float32_rows_align_with_authored_double(self):
        self.assertEqual(len(self.rows), 12)
        self.assertEqual(len(self.waves), 12)
        for index, row in enumerate(self.rows):
            self.assertEqual(row["index"], index)
            self.assertEqual(row["cosinePeriod"], 1.0)
            for value in (*row["positionCyclesPerCm"], row["timeCyclesPerSecond"],
                          *row["slopeVector"], row["phaseCycles"]):
                self.assertTrue(math.isfinite(value))
                self.assertEqual(value, f32(value))
        self.assertLessEqual(self.max_error(), self.NORMAL_COMPONENT_TOLERANCE)

    def test_second_y_reflection_is_detected(self):
        self.assertGreater(self.max_error(flip_y=True), self.NORMAL_COMPONENT_TOLERANCE * 10)

    def test_missing_metres_to_centimetres_is_detected(self):
        self.assertGreater(self.max_error(cm_scale=1.0), self.NORMAL_COMPONENT_TOLERANCE * 10)

    def test_reversed_temporal_travel_is_detected(self):
        self.assertGreater(self.max_error(positive_frequency=True), self.NORMAL_COMPONENT_TOLERANCE * 10)

    def test_missing_cycles_to_radians_is_detected(self):
        self.assertGreater(self.max_error(radians_per_cycle=1.0), self.NORMAL_COMPONENT_TOLERANCE * 10)

    def test_changed_twelfth_phase_is_detected(self):
        changed = copy.deepcopy(self.rows)
        changed[-1]["phaseCycles"] = f32(changed[-1]["phaseCycles"] + .25)
        self.assertGreater(self.max_error(changed), self.NORMAL_COMPONENT_TOLERANCE * 10)

    def test_flat_normal_and_snell_direction(self):
        flat = copy.deepcopy(self.rows)
        for row in flat:
            row["slopeVector"] = [0.0, 0.0, 0.0]
        normal = saved_normal(flat, self.points[0], .125)
        self.assertEqual(normal, (0.0, 0.0, 1.0))
        ior = self.water["iorAirToWater"]
        for incident in ((0.0, 0.0, -1.0), (.6, 0.0, -.8), (0.0, -.8, -.6)):
            transmitted, fresnel = reference.refract(incident, normal, ior)
            self.assertLess(transmitted[2], 0.0)
            self.assertAlmostEqual(sum(v * v for v in transmitted), 1.0, places=12)
            self.assertAlmostEqual(transmitted[0], incident[0] / ior, places=12)
            self.assertAlmostEqual(transmitted[1], incident[1] / ior, places=12)
            self.assertGreaterEqual(fresnel, 0.0)
            self.assertLess(fresnel, 1.0)
        _, fresnel = reference.refract((0.0, 0.0, -1.0), normal, ior)
        self.assertAlmostEqual(fresnel, ((ior - 1) / (ior + 1)) ** 2, places=12)


if __name__ == "__main__":
    unittest.main()
