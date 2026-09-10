import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('facade_restore',Path(__file__).with_name('restore_inputs.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class RestoreTests(unittest.TestCase):
    def test_existing_real_inputs_only_read(self):
        result=r.restore()
        self.assertEqual(result['restored'],[])
        self.assertEqual(len(result['verified']),8)

    def test_outside_scope_rejected(self):
        for p in ['../foreign','/tmp/foreign','scripts/unreal/materials.py',
                  'output/unreal/facade-wood-study/hinoki_planks/../../foreign']:
            with self.assertRaises(RuntimeError):r.target(p)

    def test_bad_download_bytes_not_published(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'photo.jpg'
            with self.assertRaises(RuntimeError):r.publish(p,b'foreign','0'*64)
            self.assertFalse(p.exists())

    def test_atomic_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'photo.jpg';p.write_bytes(b'original')
            with self.assertRaises(FileExistsError):r.publish(p,b'new',r.sha(b'new'))
            self.assertEqual(p.read_bytes(),b'original')
            self.assertEqual(list(Path(d).iterdir()),[p])

    def test_missing_only_publication(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'photo.jpg';r.publish(p,b'pinned',r.sha(b'pinned'))
            self.assertEqual(p.read_bytes(),b'pinned');self.assertEqual(list(Path(d).iterdir()),[p])

    def test_symlink_parent_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            old=r.ROOT
            try:
                r.ROOT=Path(d);(r.ROOT/'output').symlink_to('/tmp',target_is_directory=True)
                with self.assertRaisesRegex(RuntimeError,'symlink'):r.target('output/unreal/facade-wood-study/source-audit.json')
            finally:r.ROOT=old


if __name__=='__main__':unittest.main()
