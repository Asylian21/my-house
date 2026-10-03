"""Source-only enum rejection fixtures; stand-ins are not Unreal runtime proof."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('r20_enum_test_material_r3','exterior-curved-grass-materials-r3.py')
old=load('r20_enum_test_original_maps','exterior-curved-grass-materials.py')


def standin():
    # Names below correspond to primary installed UE5.8 declarations, with
    # Python-export uppercase/word separators. These values are only fixtures.
    symbols={'TextureCompressionSettings':['TC_DEFAULT','TC_NORMALMAP','TC_MASKS'],
        'TextureSourceEncoding':['TSE_S_RGB','TSE_NONE'],'MaterialShadingModel':['MSM_TWO_SIDED_FOLIAGE'],
        'MaterialUsage':['MATUSAGE_INSTANCED_STATIC_MESHES'],
        'MaterialSamplerType':['SAMPLERTYPE_COLOR','SAMPLERTYPE_NORMAL','SAMPLERTYPE_MASKS'],
        'TextureAddress':['TA_WRAP'],'TextureMipGenSettings':['TMGS_FROM_TEXTURE_GROUP'],
        'TexturePowerOfTwoSetting':['NONE'],'BlendMode':['BLEND_MASKED'],
        'MaterialProperty':['MP_BASE_COLOR','MP_NORMAL','MP_OPACITY_MASK','MP_AMBIENT_OCCLUSION',
            'MP_ROUGHNESS','MP_METALLIC','MP_SUBSURFACE_COLOR','MP_SPECULAR']}
    return SimpleNamespace(**{group:type(group,(),{name:group+'.'+name for name in names})for group,names in symbols.items()})


class EnumRepair(unittest.TestCase):
    def setUp(self): m._ENUM_CACHE.clear()

    def test_primary_prefixes_resolve_and_preflight_complete(self):
        u=standin();proof=m.native_enum_preflight(u)
        self.assertEqual(proof['MaterialShadingModel']['TWOSIDEDFOLIAGE'],'MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE')
        self.assertEqual(proof['MaterialUsage']['INSTANCEDSTATICMESHES'],'MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES')
        self.assertEqual(sum(len(v)for v in proof.values()),22)
        self.assertEqual(len(m._ENUM_CACHE),10)

    def test_unrelated_prefix_or_suffix_not_accepted(self):
        u=SimpleNamespace(MaterialShadingModel=type('wrong',(),{'OTHER_TWO_SIDED_FOLIAGE':1,'MSM_TWO_SIDED_FOLIAGE_WRONG':2}))
        with self.assertRaises(RuntimeError):m.enum(u,'MaterialShadingModel','TWOSIDEDFOLIAGE')

    def test_ambiguous_native_names_rejected(self):
        u=SimpleNamespace(MaterialShadingModel=type('ambiguous',(),{'MSM_TWO_SIDED_FOLIAGE':1,'TWOSIDEDFOLIAGE':2}))
        with self.assertRaises(RuntimeError):m.enum(u,'MaterialShadingModel','TWOSIDEDFOLIAGE')

    def test_missing_enum_fails_before_asset_creation(self):
        u=standin();u.MaterialUsage=type('missing',(),{})
        with self.assertRaises(RuntimeError):m.build_materials(u,m.canonical_recipe(),None)
        self.assertFalse(hasattr(u,'EditorAssetLibrary'))

    def test_original_recipe_photos_routes_constants_unchanged(self):
        self.assertEqual(m.canonical_recipe(),old.canonical_recipe())
        self.assertEqual(m.FILES,old.FILES);self.assertEqual(m.TAG,old.TAG);self.assertEqual(m.PREFIX,old.PREFIX)
        self.assertTrue(m.validate_recipe(m.canonical_recipe())['explicitSeparateAlphaPngRequired'])

    def test_native_source_plan_stays_original_64_roots(self):
        n=load('r20_enum_test_native_r3','exterior-curved-grass-native-r3.py')
        path=ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json'
        result=n.validate_plan(n.read(path),path)
        self.assertEqual(len(result[5]),64);self.assertEqual(result[6],old.canonical_recipe())


if __name__=='__main__':unittest.main(verbosity=2)
