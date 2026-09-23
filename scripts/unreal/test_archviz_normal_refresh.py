import runpy
import unittest
from pathlib import Path

M=runpy.run_path(str(Path(__file__).with_name('archviz-normal-refresh.py')))


class NormalRefreshTrustTests(unittest.TestCase):
    def test_only_exact_accepted_target_material_package_can_change(self):
        before={'map.umap':'map','geometry.uasset':'mesh','avatar.uasset':'rig','mat.uasset':'old'}
        M['assert_packages'](before,{**before,'mat.uasset':'fixed'},['mat.uasset'])
        for protected in ('map.umap','geometry.uasset','avatar.uasset'):
            with self.subTest(protected=protected),self.assertRaisesRegex(RuntimeError,'protected'):
                M['assert_packages'](before,{**before,'mat.uasset':'fixed',protected:'wrong'},['mat.uasset'])

    def test_inventory_cannot_gain_or_lose_any_package(self):
        before={'mat.uasset':'old'}
        for changed in ({},{'mat.uasset':'fixed','other.uasset':'new'}):
            with self.assertRaisesRegex(RuntimeError,'inventory'):
                M['assert_packages'](before,changed,['mat.uasset'])


if __name__=='__main__':unittest.main()
