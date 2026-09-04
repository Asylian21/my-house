import math
import unittest
from solar import solar_position, site_sun_direction


class SolarTest(unittest.TestCase):
    def test_equinox_noon_near_zenith_at_equator(self):
        elevation, _ = solar_position("2026-03-20T12:07:00+00:00", 0, 0)
        self.assertGreater(math.degrees(elevation), 89)

    def test_offsets_are_same_instant(self):
        self.assertEqual(
            solar_position("2026-09-04T16:30:00+02:00", 48.8176, 16.5528),
            solar_position("2026-09-04T14:30:00+00:00", 48.8176, 16.5528),
        )

    def test_true_north_rotates_into_parcel_axes(self):
        direction = site_sun_direction(0, 0, 0.9540149448)
        self.assertAlmostEqual(direction[0], 0.8157645, places=4)
        self.assertAlmostEqual(direction[1], 0.5783842, places=4)

    def test_rejects_ambiguous_time(self):
        with self.assertRaises(ValueError):
            solar_position("2026-09-04T16:30:00", 48.8, 16.5)


if __name__ == "__main__":
    unittest.main()
