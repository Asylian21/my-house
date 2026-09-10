"""Relocated helper interface checks. No native process or fabricated cook acceptance."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
import cook_binding as b

class Tests(unittest.TestCase):
 def test_explicit_paths_preserve_reviewed_hashes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();binding=root/'binding.json';pair=root/'pair.json';binding.write_bytes(b'wrong');pair.write_bytes(b'wrong')
   with self.assertRaises(ValueError):b.configure_authority(binding,pair)
   with patch.object(b,'digest',side_effect=[b.BINDING_SHA,b.PAIR_SHA]):b.configure_authority(binding,pair)
   self.assertEqual(b.BINDING,binding);self.assertEqual(b.PAIR,pair)
   self.assertEqual(b.BINDING_SHA,'af9cc202a4fb4a204a47f915e457f249e4180e43b1fc55bf105c02ae1b743737')
   self.assertEqual(b.PAIR_SHA,'edc8d3d6d8113cff291d257ef76f3857ff017efd039ce6b12c6178d114577f5e')
 def test_present_null_authority_never_falls_back(self):
  with patch.object(b,'BINDING',None),patch.object(b,'PAIR',None):
   with self.assertRaisesRegex(ValueError,'explicit reviewed evidence'):b.authority(Path('/unused'))
if __name__=='__main__':unittest.main()
