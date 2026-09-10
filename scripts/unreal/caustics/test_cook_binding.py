"""Small synthetic CPU tests; no native fixture or cooked proof is emitted."""
import csv,json,tempfile,unittest
from pathlib import Path
import cook_binding as b

class Tests(unittest.TestCase):
    def test_response_exact_paths_and_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rsp';p.write_text('"/actual cook/BreziTwin/Content/A.uasset" "../../../BreziTwin/Content/A.uasset" -compress\n')
            self.assertEqual(b.parse_response(p),{'BreziTwin/Content/A.uasset':'/actual cook/BreziTwin/Content/A.uasset'})
            p.write_text(p.read_text()*2)
            with self.assertRaises(ValueError):b.parse_response(p)
    def test_response_relative_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rsp';p.write_text('"relative/A.uasset" "../../../BreziTwin/Content/A.uasset"\n')
            with self.assertRaises(ValueError):b.parse_response(p)
    def test_package_native_csv_and_rejections(self):
        row={'Filename':'../../../BreziTwin/Content/A.uasset','ChunkType':'ExportBundleData','ContainerName':'BreziTwin-Mac',
             'Size':'500','Hash':'0x'+'a'*40,'ChunkId':'b'*24,'PackageName':'/Game/A'}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'list.csv'
            def write(rows):
                with p.open('w') as f:
                    w=csv.DictWriter(f,fieldnames=row);w.writeheader();w.writerows(rows)
            write([row]);self.assertEqual(b.package_rows(p,{'/Game/A':'Content/A.uasset'})['/Game/A'],row)
            for key,value in [('ChunkType','BulkData'),('Size','0'),('ContainerName','old-container'),('Hash','x'),
                              ('ChunkId','f'),('PackageName','/Game/Other'),('Filename','../../../Other/Content/A.uasset')]:
                with self.subTest(key=key):
                    write([{**row,key:value}])
                    with self.assertRaises(ValueError):b.package_rows(p,{'/Game/A':'Content/A.uasset'})
            write([row,row])
            with self.assertRaises(ValueError):b.package_rows(p,{'/Game/A':'Content/A.uasset'})
    def test_stale_and_missing_pin(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'data';p.write_bytes(b'v1');pins={str(p):b.digest(p)};b.check(pins)
            p.write_bytes(b'v2')
            with self.assertRaises(ValueError):b.check(pins)
            p.unlink()
            with self.assertRaises(ValueError):b.check(pins)
    def test_tree_addition_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();(p/'A').write_bytes(b'A');before=b.tree(p);(p/'B').write_bytes(b'B')
            self.assertNotEqual(before,b.tree(p));(p/'L').symlink_to(p/'A')
            with self.assertRaises(ValueError):b.tree(p)
    def test_preserve_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'receipt';b.save(p,{'fixture':True});old=p.read_bytes()
            with self.assertRaises(ValueError):b.save(p,{'fixture':False})
            self.assertEqual(p.read_bytes(),old)

if __name__=='__main__':unittest.main()
