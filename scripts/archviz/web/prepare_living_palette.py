from pathlib import Path
from PIL import Image,ImageStat
import argparse
import json
parser = argparse.ArgumentParser(description='Prepare the warm living-room variants of existing material maps.')
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
parser.add_argument('--output', type=Path)
args = parser.parse_args()
ROOT = args.root.resolve() / 'public/assets/textures'
OUT = (args.output or args.root / 'output/archviz/living-palette').resolve()
OUT.mkdir(parents=True, exist_ok=True)
SPECS=[('boucle-taupe-albedo.jpg','living-boucle-ecru-albedo.jpg','#D8C8B2',.60),('rug-wool-taupe-albedo.jpg','living-wool-sand-albedo.jpg','#BCAE96',.70),('oak-veneer-albedo.jpg','living-natural-oak-albedo.jpg','#BE9566',.90),('stone-dark-albedo.jpg','living-warm-stone-albedo.jpg','#BDAF98',.60)]
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def srgb(v):return 12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055
result=[]
for source,name,color,contrast in SPECS:
 im=Image.open(ROOT/source).convert('RGB');mean=ImageStat.Stat(im).mean;target=[int(color[i:i+2],16) for i in (1,3,5)];channels=[]
 for channel,average,t in zip(im.split(),mean,target):
  lut=[]
  for i in range(256):
   variation=(linear(i/255)/max(.001,linear(average/255)))**contrast
   variation=max(.6,min(1.35,variation))
   lut.append(round(max(0,min(1,srgb(linear(t/255)*variation)))*255))
  channels.append(channel.point(lut))
 output=Image.merge('RGB',channels);output.save(OUT/name,quality=94,optimize=True);result.append({'file':name,'source':source,'targetSrgb':color,'meanSrgb':[round(x,1) for x in ImageStat.Stat(output).mean],'bytes':(OUT/name).stat().st_size})
(OUT/'candidate-textures.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
