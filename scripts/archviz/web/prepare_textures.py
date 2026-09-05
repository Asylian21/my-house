from pathlib import Path
import json,math,argparse
from PIL import Image,ImageChops
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);parser.add_argument('--output',type=Path);args=parser.parse_args()
ROOT=args.root.resolve();DEST=(args.output or ROOT/'output/archviz/web').resolve();DEST.mkdir(parents=True,exist_ok=True);OUT=DEST/'textures';OUT.mkdir(exist_ok=True)
ASSETS=ROOT/'output/archviz/assets'
lock=json.loads((ROOT/'scripts/archviz/assets.lock.json').read_text())
manifest={}
def srgb(v):return 12.92*v if v<=0.0031308 else 1.055*v**(1/2.4)-0.055
def linear(v):return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4

def save(src,key,color=False,alpha=None,tint=None,variant=None,size=1024):
 src=Path(src)
 if src.suffix=='.exr':return None
 im=Image.open(src).convert('RGB');im.thumbnail((size,size),Image.Resampling.LANCZOS)
 if variant=='plaster':
  im=Image.merge('RGB',[ch.point([int(255*srgb(.85*c+.15*linear(i/255))) for i in range(256)]) for ch,c in zip(im.split(),(.82,.80,.75))])
 if variant in ('grass','mulch'):
  im=im.convert('L'); lo,hi=((.026,.055,.009),(.065,.115,.023)) if variant=='grass' else ((.018,.008,.003),(.13,.065,.025))
  im=Image.merge('RGB',[im.point([int(255*srgb(a+(b-a)*linear(i/255))) for i in range(256)]) for a,b in zip(lo,hi)])
 if tint:
  tinted=Image.merge('RGB',[ch.point([int(255*srgb(linear(i/255)*c)) for i in range(256)]) for ch,c in zip(im.split(),tint)])
  mask=src.with_name(src.name.replace('_diff_','_mask_')).with_suffix('.png')
  im=Image.composite(tinted,im,Image.open(mask).convert('L').resize(im.size)) if mask.exists() else tinted
 if alpha:
  a=Image.open(alpha).convert('L').resize(im.size,Image.Resampling.LANCZOS)
  im.putalpha(a)
 suffix='.png' if alpha else '.jpg'; dest=OUT/(key+suffix)
 im.save(dest,**({'optimize':True} if alpha else {'quality':88 if color else 92,'optimize':True}))
 manifest[key]=str(dest)
 return dest
for asset in ('white_plaster_02','leafy_grass','gravel_floor_02','hinoki_planks','concrete_pavement'):
 spec=lock['assets'][asset]
 for kind in ('diffuse','normal','roughness'):
  variant=('plaster' if asset=='white_plaster_02' else 'grass' if asset=='leafy_grass' else None) if kind=='diffuse' else None
  save(ASSETS/spec['maps'][kind]['path'],asset+'-'+kind,kind=='diffuse',variant=variant,size=512 if kind=='roughness' else 1024)
 if asset=='leafy_grass':save(ASSETS/spec['maps']['diffuse']['path'],'mulch-diffuse',True,variant='mulch')
for src in (ROOT/'public/assets/textures').iterdir():
 if src.suffix.lower() not in ('.jpg','.png'):continue
 save(src,'native-'+src.stem,'albedo' in src.stem,size=1024)
for asset in ('shrub_02','tree_small_02','grass_bermuda_01','outdoor_table_chair_set_01'):
 for src in sorted((ASSETS/asset/'textures').glob('*')):
  if src.suffix not in ('.png','.jpg'):continue
  if any(k in src.stem for k in ('_disp_','_mask_','_alpha_')):continue
  key=src.stem.replace('_1k','').replace('_2k','')
  alpha=src.with_name(src.name.replace('_diff_','_alpha_')).with_suffix('.png')
  save(src,key,'_diff_' in src.name,alpha=alpha if '_diff_' in src.name and alpha.exists() else None,tint=(.45,.85,.30) if src.name.startswith('shrub_02_diff') else (.70,.85,.55) if src.name.startswith('grass_bermuda_01_diff') else None,size=512 if '_rough_' in src.name or '_metal_' in src.name else 1024)
(DEST/'texture-index.json').write_text(json.dumps(manifest,indent=2))
print('Prepared',len(manifest),'maps',sum(p.stat().st_size for p in OUT.iterdir()),'bytes')
