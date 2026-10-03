"""One exact backdrop-only Material copy; current saved graph defines the delta."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-repair-materials-r35.py'
PREFIX='/Game/Brezi/ContextYardRepair20261002R35'
ASSET=PREFIX+'/Materials/M_backdrop_near_pbr_r35.M_backdrop_near_pbr_r35'
SCHEMA='brezi-single-backdrop-near-pbr-material-copy-r35'
ROLE_CODES={'BreziExterior:near-terrain-pbr-color':('return lerp(Terrain,Scan,.30*Near);','return lerp(Terrain,Scan,.65*Near);'),
 'BreziExterior:near-terrain-normal-strength':('return .30*Near;','return .65*Near;')}

def require(ok,message):
 if not ok:raise RuntimeError(message)
def digest(row):return hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate_variant(original,actual):
 require(len(original['nodes'])==len(actual['nodes'])==58,'Exact58 node graph required')
 restored=copy.deepcopy(actual);found=set()
 for n in restored['nodes']:
  if n['role']in ROLE_CODES:
   old,new=ROLE_CODES[n['role']];require(n['class']=='MaterialExpressionCustom'and n['values']['code']==new,'Only exact two near-PBR coefficient expressions allowed')
   n['values']['code']=old;found.add(n['role'])
 require(found==set(ROLE_CODES)and restored==original,'Any undeclared node/input/root/flag/texture/UV/orthophoto change rejected')
 return {'unchangedOriginalNodesExceptTwoCustomCodes':True,'nodeCount':58,'changedCustomRoles':sorted(found),
  'originalNearCoefficient':.30,'newNearCoefficient':.65,'worldUvAndOriginalOrthophotoRoutesPreserved':True,
  'sourceRecipeNormalStrengthZeroIsNotActualSavedGraphCoefficient':True,'newTextureObjects':0,
  'nativeAppearanceAccepted':False,'sourcePixelsEdited':False}

def usage(u,h,m):
 return {k:bool(u.MaterialEditingLibrary.has_material_usage(m,e))for k,e in {
  'instancedStaticMeshes':h['existing'].native_enum(u.MaterialUsage,'INSTANCEDSTATICMESHES'),'nanite':u.MaterialUsage.MATUSAGE_NANITE}.items()}
def preflight_enums(u,h):
 require(all(hasattr(u.MaterialEditingLibrary,k)for k in ('get_material_expressions','recompile_material','has_material_usage')),'Required actual MaterialEditingLibrary functions unavailable')
 return {'instancedStaticMeshes':h['existing'].native_enum(u.MaterialUsage,'INSTANCEDSTATICMESHES'),'nanite':u.MaterialUsage.MATUSAGE_NANITE}

def prepare(u,h,bundle):
 row=bundle['materialVariant'];old=u.EditorAssetLibrary.load_asset(row['originalAsset']);require(isinstance(old,u.Material),'Actual original Material required')
 original=h['existing'].graph_snapshot(u,old);require(original==row['originalFullGraph'] and digest(original)==row['originalGraphSha256'],'Current actual58-node graph differs')
 require(not u.EditorAssetLibrary.does_asset_exist(ASSET.split('.')[0]),'Fresh material namespace only')
 offsets=h['r21'].world_position_offsets(u,old);old_usage=usage(u,h,old)
 texture_helper=bundle['base']['native'].guard.module('r35_exact_shared_texture_snapshot','exterior-context-yard-ground-materials-r32.py')
 textures=texture_helper.texture_snapshot(u,bundle['materialSharedTextures'])
 material=u.EditorAssetLibrary.duplicate_asset(old.get_path_name(),ASSET.split('.')[0]);require(material and h['existing'].graph_snapshot(u,material)==original,'Initial exact copy failed')
 nodes={str(n.get_editor_property('desc')):n for n in u.MaterialEditingLibrary.get_material_expressions(material)}
 require(len(nodes)==58 and set(ROLE_CODES)<=set(nodes),'Unambiguous original tagged node roles required')
 for role,(_,code)in ROLE_CODES.items():nodes[role].set_editor_property('code',code)
 u.EditorAssetLibrary.set_metadata_tag(material,'BreziGeneratedBy',OWNER)
 u.EditorAssetLibrary.set_metadata_tag(material,'BreziSourceOriginalMaterial',old.get_path_name())
 u.EditorAssetLibrary.set_metadata_tag(material,'BreziSourceOriginalGraphSha256',row['originalGraphSha256'])
 errors=list(u.MaterialEditingLibrary.recompile_material(material));require(errors==[],'New isolated material compile errors')
 graph=h['existing'].graph_snapshot(u,material);proof=validate_variant(original,graph)
 require(graph==row['proposedGraph']and h['r21'].world_position_offsets(u,material)==offsets and usage(u,h,material)==old_usage,'Exact proposed graph/offset/usage differs')
 require(u.EditorAssetLibrary.save_loaded_asset(material,False),'Cannot save isolated material')
 report={'schema':SCHEMA,'owner':OWNER,'asset':material.get_path_name(),'originalAsset':old.get_path_name(),'originalGraphSha256':row['originalGraphSha256'],
  'graph':graph,'graphSha256':digest(graph),'graphDelta':proof,'usage':old_usage,'worldPositionShaderOffsets':offsets,'compileErrors':errors,
  'sharedTextureWitness':textures,'newPackageAssets':[material.get_path_name()],'newTextureObjects':0,'sourcePixelsEdited':False,
  'materialPackagesIndependentlyUnloaded':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False}
 verify_saved(u,h,bundle,report);return material,report

def verify_saved(u,h,bundle,report):
 row=bundle['materialVariant'];require(report['schema']==SCHEMA and report['owner']==OWNER and report['asset']==ASSET and report['originalAsset']==row['originalAsset']and report['newPackageAssets']==[ASSET]and report['newTextureObjects']==0,'Exact owned material report required')
 old=u.EditorAssetLibrary.load_asset(row['originalAsset']);material=u.EditorAssetLibrary.load_asset(ASSET)
 require(isinstance(old,u.Material)and isinstance(material,u.Material),'Saved materials required')
 original=h['existing'].graph_snapshot(u,old);graph=h['existing'].graph_snapshot(u,material)
 require(original==row['originalFullGraph']and graph==row['proposedGraph']==report['graph']and digest(graph)==report['graphSha256'],'Original/proposed saved graph changed')
 require(validate_variant(original,graph)==report['graphDelta']and usage(u,h,old)==usage(u,h,material)==report['usage'],'Saved declared graph/usage delta differs')
 require(h['r21'].world_position_offsets(u,old)==h['r21'].world_position_offsets(u,material)==report['worldPositionShaderOffsets'],'World-position offset policy changed')
 texture_helper=bundle['base']['native'].guard.module('r35_saved_shared_texture_snapshot','exterior-context-yard-ground-materials-r32.py')
 require(texture_helper.texture_snapshot(u,bundle['materialSharedTextures'])==report['sharedTextureWitness'],'Shared original texture settings changed')
 for key,value in {'BreziGeneratedBy':OWNER,'BreziSourceOriginalMaterial':row['originalAsset'],'BreziSourceOriginalGraphSha256':row['originalGraphSha256']}.items():require(u.EditorAssetLibrary.get_metadata_tag(material,key)==value,'New material ownership metadata changed')
 return material
