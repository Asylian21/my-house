"""Bounded R21 artistic foreground study. CPU/source only; no Unreal writes.

The actual close camera sees unresolved flat backdrop outside the authored
context classes. This does not infer land use or surveyed ground. A fresh
feathered PBR surface and <=512 roots reuse frozen photographic assets; original
ground, grove litter, trees, existing groups and house architecture stay intact.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Point, Polygon, box, shape, mapping
from shapely.ops import unary_union, triangulate
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-foreground-study.py'
DESTINATION = ROOT/'output/unreal/exterior-canopy-foreground-20261001-r21-study'
SEED = 601226300021
SOURCES = {
    'nativeR16': ('output/unreal/exterior-20261001-r16a/exterior-import-report.json', '1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'),
    'views': ('output/unreal/exterior-20261001-r16a/Project/BreziTwin/Content/Data/viewpoints.json', '06127e9b9d8d4c3798e4a08601b909e81d992fc2b2f8ca1f761dd7df36d7bff7'),
    'context': ('output/unreal/exterior-context-20260927-r8/context-plan.json', '4b0b72a5f39d5bec3915846abb159147a4cf73b65cbf920884ffe7dd762a4176'),
    'terrain': ('output/unreal/exterior-terrain-20260926-r4/terrain-plan.json', '7106824dd0e489c1688cbe9569811a59314e8a56b6b5479000fa5d8f84fbdced'),
    'ecology': ('output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json', '27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576'),
    'ecologyGeometry': ('output/unreal/exterior-canopy-ecology-20260930-r4/geometry-manifest.json', '9ac5696a201f367dd800330440a5a29c4bf3edf8331626104ca94818a24345df'),
    'ecologyPrototypes': ('output/unreal/exterior-canopy-ecology-20260930-r3/canopy-ecology-prototypes.json', '0033503c31d7ba69aa19d1b14a6bdf1f98ea5f4c01cc09e0b7bd1bb920b2faba'),
    'substrate': ('output/unreal/exterior-grove-substrate-20260930-r3/grove-substrate-plan.json', 'cb8ecc37bae3dc77e34bf5da4b7ea0d1c7be91599f941473254eebee328d9e10'),
    'managedLawn': ('output/unreal/exterior-lawn-photo-integration-20261001-r1/lawn-natural-plan.json', '5226c3d437decb065d4b792be16a7f8182f8c03a583bfb06cc0384bcd7bb3621'),
}
MODELS = ('canopy_ecology_grass_0', 'canopy_ecology_grass_1', 'canopy_ecology_herb_0', 'canopy_ecology_herb_1')
GROUND_KEYS = {'context_fallow', 'context_meadow', 'context_crop', 'context_arable', 'context_track'}


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def pin(path): return {'path': str(path), 'sha256': sha(path), 'bytes': Path(path).stat().st_size}
def write(path, value):
    with Path(path).open('x') as stream: json.dump(value, stream, separators=(',', ':'), allow_nan=False); stream.write('\n')


def noise(x, y, length, seed):
    x, y = x/length, y/length; ix, iy = math.floor(x), math.floor(y)
    fx, fy = x-ix, y-iy; fx, fy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
    def h(a, b):
        v = math.sin(a*127.1+b*311.7+seed)*43758.5453; return v-math.floor(v)
    return ((1-fx)*h(ix, iy)+fx*h(ix+1, iy))*(1-fy)+((1-fx)*h(ix, iy+1)+fx*h(ix+1, iy+1))*fy


def smooth(value):
    t = min(1., max(0., value)); return t*t*(3-2*t)


class Camera:
    def __init__(self, row):
        self.row = row; self.eye = np.asarray(row['eyeCm'], dtype=float)
        forward = np.asarray(row['targetCm'])-self.eye; self.forward = forward/np.linalg.norm(forward)
        self.plan_forward = self.forward[:2]/np.linalg.norm(self.forward[:2])
        self.right = np.array([self.plan_forward[1], -self.plan_forward[0], 0.])
        self.up = np.cross(self.right, self.forward)
        self.tan_h = math.tan(math.radians(row['horizontalFovDegrees']/2)); self.tan_v = self.tan_h/(16/9)

    def inside(self, point):
        delta = np.asarray(point)-self.eye; depth = float(delta@self.forward)
        return depth > 0 and abs(float(delta@self.right)) <= depth*self.tan_h+1e-6 and abs(float(delta@self.up)) <= depth*self.tan_v+1e-6

    def ground_domain(self):
        # Exact planar source frustum and Euclidean 2..20m ground-distance cap.
        h = math.hypot(*self.forward[:2]); z = -25-self.eye[2]
        near = max(200., (-h*z-self.forward[2]*z*self.tan_v)/(h*self.tan_v-self.forward[2]))
        points = []
        for along, sign in ((near, -1), (2000., -1), (2000., 1), (near, 1)):
            depth = h*along+self.forward[2]*z
            points.append((self.eye[:2]+self.plan_forward*along+self.right[:2]*depth*self.tan_h*sign).tolist())
        return Polygon(points).intersection(Point(self.eye[:2]).buffer(2000, quad_segs=128)).difference(Point(self.eye[:2]).buffer(200, quad_segs=64))


class Ground:
    def __init__(self, context, terrain, local):
        bounds = local.bounds; self.rows, shapes = [], []
        for mesh in [m for m in context['meshes'] if m['material'] in GROUND_KEYS]+terrain['meshes']:
            vertices = np.asarray(mesh['verticesCm']); indices = np.asarray(mesh['indices']).reshape(-1, 3); triangles = vertices[indices]
            low, high = triangles[:, :, :2].min(axis=1), triangles[:, :, :2].max(axis=1)
            keep = (high[:, 0]>=bounds[0]) & (high[:, 1]>=bounds[1]) & (low[:, 0]<=bounds[2]) & (low[:, 1]<=bounds[3])
            for ordinal in np.flatnonzero(keep):
                triangle = triangles[ordinal].tolist(); poly = Polygon([p[:2] for p in triangle])
                if poly.area>1e-6:
                    self.rows.append((mesh['id'], int(ordinal), triangle, mesh['material'])); shapes.append(poly)
        self.index = STRtree(shapes)

    def sample(self, xy, require_original=True):
        candidates = []
        for index in self.index.query(Point(xy)):
            mid, ordinal, tri, material = self.rows[int(index)]; a,b,c = tri
            d=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            u=((b[0]-xy[0])*(c[1]-xy[1])-(b[1]-xy[1])*(c[0]-xy[0]))/d
            v=((c[0]-xy[0])*(a[1]-xy[1])-(c[1]-xy[1])*(a[0]-xy[0]))/d; w=1-u-v
            if min(u,v,w)>=-1e-7: candidates.append((a[2]*u+b[2]*v+c[2]*w, mid, ordinal, [u,v,w], material))
        require(candidates, 'No actual source ground under candidate')
        z,mid,ordinal,weights,material=max(candidates)
        if require_original: require(mid=='context_unresolved_flat_backdrop' and abs(z+25)<1e-6, 'Foreground source ground class/elevation differs')
        return {'meshId': mid, 'triangleOrdinal': ordinal, 'barycentric': weights, 'zCm': z, 'material': material, 'measuredElevation': False}


def prototypes(data):
    result = {}; native = {r['id']:r for r in data['nativeR16']['savedPlantReadback']}; models={m['id']:m for m in data['ecologyGeometry']['meshes']}
    for identity in MODELS:
        levels=sorted([r for r in data['ecologyPrototypes'] if r['nodeName'].startswith(identity+'_LOD')], key=lambda r:r['level'])
        require([r['level'] for r in levels]==[0,1,2], 'Original existing ecology prototype LOD census differs')
        points=[]; decoded=[]
        for row in levels:
            count=0
            for part in row['parts'].values():
                vs=np.asarray(part['positionsCm']); uv=np.asarray(part['uv0']); faces=np.asarray(part['triangles'])
                require(vs.shape[1]==3 and uv.shape==(len(vs),2) and np.isfinite(vs).all() and np.isfinite(uv).all(), 'Invalid prototype positions/UV')
                require(faces.shape[1]==3 and faces.min()>=0 and faces.max()<len(vs), 'Invalid original prototype indices')
                tri=vs[faces]; require((np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>1e-10).all(), 'Degenerate original prototype')
                points.extend(vs.tolist()); count+=len(faces)
            require(count==native[identity]['lodTriangles'][row['level']]==models[identity]['lods'][row['level']]['triangles'], 'Native/source LOD triangle census differs')
            decoded.append({'level':row['level'],'triangles':count,'recordSha256':digest(row)})
        radius=max(math.hypot(*p[:2]) for p in points); low=min(p[2]for p in points); high=max(p[2]for p in points)
        result[identity]={'id':identity, 'nativeMesh':native[identity]['mesh'], 'nativeMaterials':native[identity]['materials'], 'lodScreens':native[identity]['lodScreens'],
            'decodedLods':decoded, 'radiusCm':radius, 'minZcm':low, 'maxZcm':high, 'nativeAssetEvidence':'Frozen R16 saved prototype census; new native readback pending',
            'sourceModeling':'Authored curved blades or leaf/petiole geometry using unchanged photographic pixels; not original provider plant modeling', '_points':points}
    return result


def surface(domain, ground):
    vertices, uvs, uv1, indices, witnesses = [], [], [], [], {}; lookup={}
    def vertex(xy):
        key=tuple(round(v,7)for v in xy)
        if key in lookup:return lookup[key]
        p=Point(xy); edge=p.distance(domain.boundary); width=95+25*noise(*xy,310,12); coverage=smooth(edge/width)
        witness=ground.sample(xy); relief=(.12+.68*noise(*xy,90,28))*coverage
        index=len(vertices); vertices.append([*map(float,xy),witness['zCm']+relief]);uvs.append([xy[0]/200,xy[1]/200]);uv1.append([coverage,0.])
        lookup[key]=index; witnesses[str(index)]=witness; return index
    x0,y0,x1,y1=domain.bounds
    for x in range(math.floor(x0/50)*50,math.ceil(x1/50)*50,50):
        for y in range(math.floor(y0/50)*50,math.ceil(y1/50)*50,50):
            poly=domain.intersection(box(x,y,x+50,y+50))
            if poly.is_empty:continue
            for tri in triangulate(poly):
                if tri.area<1e-7 or not poly.covers(tri):continue
                points=list(tri.exterior.coords)[:3]; a,b,c=points
                if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0: points=[a,c,b]
                indices.extend(vertex(p) for p in points)
    mesh={'id':'canopy_foreground_r21_surface','material':'canopy_foreground_r21_meadow_feather','verticesCm':vertices,'indices':indices,'uv0':uvs,'uv1':uv1,
          'winding':'clockwise','nanite':False,'collision':'NoCollision','canEverAffectNavigation':False,'castShadow':False,'maxDrawDistanceCm':6000,'nativeApplied':False}
    return mesh,witnesses


def plants(domain, camera, ground, models, new_surface):
    rng=random.Random(SEED); centers=[]; roots=[]; counts=Counter(); rejected=Counter()
    x0,y0,x1,y1=domain.bounds
    for _ in range(10000):
        xy=[rng.uniform(x0,x1),rng.uniform(y0,y1)]
        if domain.contains(Point(xy)) and all(math.dist(xy,c['centerCm'])>120 for c in centers):
            centers.append({'centerCm':xy,'axisCm':[rng.uniform(85,145),rng.uniform(45,85)],'yawRad':rng.uniform(-math.pi,math.pi)})
        if len(centers)==24:break
    require(len(centers)>=12, 'Too few irregular foreground clusters')
    for attempt in range(60000):
        center=centers[attempt%len(centers)]; a,b=center['axisCm']; phi=center['yawRad']; u,v=rng.gauss(0,a),rng.gauss(0,b)
        xy=[center['centerCm'][0]+u*math.cos(phi)-v*math.sin(phi), center['centerCm'][1]+u*math.sin(phi)+v*math.cos(phi)]
        field=.7*noise(*xy,280,71)+.3*noise(*xy,75,97)
        if rng.random()>.48+.48*field:rejected['coherent-field-thinning']+=1;continue
        kind='grass' if len(roots)%6 else 'herb'; identity=MODELS[(counts[kind]%2)+(0 if kind=='grass'else 2)]; m=models[identity]
        scale=round((.75+.48*field+rng.uniform(-.08,.08)) if kind=='grass' else (.78+.40*field+rng.uniform(-.08,.08)),6)
        radius=m['radiusCm']*scale; p=Point(xy)
        if not domain.covers(p.buffer(radius+.5,quad_segs=64)):rejected['complete-footprint']+=1;continue
        if any(math.dist(xy,r['positionCm'][:2])<20 for r in roots):rejected['local-root-spacing']+=1;continue
        witness=ground.sample(xy); yaw=rng.uniform(-180,180); phase=math.radians(yaw)
        surface_witness=new_surface.sample(xy,require_original=False)
        root=[*xy,surface_witness['zCm']+.08-m['minZcm']*scale]
        world=[[root[0]+scale*(v[0]*math.cos(phase)-v[1]*math.sin(phase)),root[1]+scale*(v[0]*math.sin(phase)+v[1]*math.cos(phase)),root[2]+scale*v[2]]for v in m['_points']]
        if not all(camera.inside(v) for v in world):rejected['actual-all-LOD-source-vertex-frustum']+=1;continue
        roots.append({'id':f'foreground_r21_root_{len(roots):04d}','meshId':identity,'positionCm':root,'yawDeg':yaw,'scale':[scale]*3,'radiusCm':radius,
                      'actualHeightCm':(m['maxZcm']-m['minZcm'])*scale,'clusterIndex':attempt%len(centers),'growthField':field,'sourceGround':witness,'newSurfaceContact':surface_witness,
                      'landUseEvidence':'ARTISTIC_UNSURVEYED_CLEARING_TRANSITION_OUTSIDE_AUTHORED_CONTEXT_CLASSES'})
        counts[kind]+=1
        if len(roots)==512:break
    require(len(roots)==512, 'Bounded plant population not reached')
    return roots,centers,dict(rejected)


def plots(output, camera, frustum, domain, masks, substrate, ecology, roots, mesh):
    def canvas(title,bounds):
        image=Image.new('RGB',(1500,1200),'#f4f2e9');draw=ImageDraw.Draw(image);draw.text((35,20),title,fill='#182722')
        x0,y0,x1,y1=bounds;scale=min(1400/(x1-x0),1090/(y1-y0))
        def xy(p):return (50+(p[0]-x0)*scale,1160-(p[1]-y0)*scale)
        def geometry(g,fill,outline=None):
            for poly in ([g]if g.geom_type=='Polygon'else getattr(g,'geoms',[])):
                if poly.geom_type!='Polygon' or poly.is_empty or poly.area<1e-6:continue
                draw.polygon([xy(p)for p in poly.exterior.coords],fill=fill,outline=outline)
                for ring in poly.interiors:draw.polygon([xy(p)for p in ring.coords],fill='#f4f2e9')
        return image,draw,xy,geometry
    bounds=(3100,17000,8500,22500)
    image,draw,xy,geo=canvas('SOURCE PLAN: frustum/masks. Unknown land use; no native render or survey.',bounds)
    for name,mask in masks.items():geo(mask.intersection(box(*bounds)),'#deb9a3')
    geo(substrate.intersection(box(*bounds)),'#8c795a');geo(frustum,'#d6e4bf','#687658');geo(domain,'#aebf85','#43533c')
    for row in ecology['existingTrees']:
        p=row['positionCm'];r=row['radiusCm'];draw.ellipse([xy([p[0]-r,p[1]+r]),xy([p[0]+r,p[1]-r])],outline='#37553b',width=2)
    eye=xy(camera.eye);draw.ellipse((eye[0]-5,eye[1]-5,eye[0]+5,eye[1]+5),fill='#192f96')
    draw.text((35,55),'Brown: protected source masks | dark tan: unchanged grove substrate | green: new feathered domain',fill='#182722');image.save(output/'source-mask-plan.png')
    local=(4300,18500,7300,20750)
    image,draw,xy,geo=canvas('SOURCE GEOMETRY: irregular low-root groups, not a rendered meadow.',local)
    geo(substrate.intersection(box(*local)),'#b7a98b');geo(domain,'#d5ddb5','#738456')
    for row in ecology['ecologyPlacements']:
        p=row['positionCm'];px,py=xy(p)
        if 0<px<1500 and 70<py<1200:draw.ellipse((px-1,py-1,px+1,py+1),fill='#817863')
    for row in roots:
        p=row['positionCm'];r=row['radiusCm'];color='#426243'if 'grass'in row['meshId']else'#304f80'
        draw.ellipse([xy([p[0]-r,p[1]+r]),xy([p[0]+r,p[1]-r])],outline=color)
    draw.text((35,55),'512 new roots: green curved grass / blue herbs; grey original roots remain unchanged.',fill='#182722');image.save(output/'source-root-layout.png')
    image,draw,xy,geo=canvas('SOURCE SURFACE: 50cm topology, UV1 feather coverage and <=0.8cm relief. Native pending.',local)
    for i in range(0,len(mesh['indices']),3):
        ids=mesh['indices'][i:i+3];coverage=sum(mesh['uv1'][j][0]for j in ids)/3;shade=int(230-90*coverage)
        draw.polygon([xy(mesh['verticesCm'][j])for j in ids],fill=(shade,int(shade*1.03),int(shade*.83)),outline='#8d9680')
    draw.text((35,55),'One NEW masked copy of the native meadow PBR graph; old graph/texture objects untouched.',fill='#182722');image.save(output/'source-surface-feather.png')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=DESTINATION);args=parser.parse_args();output=args.output.resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Fresh isolated output required')
    input_pins={};data={}
    for key,(relative,expected)in SOURCES.items():
        path=ROOT/relative;require(sha(path)==expected,'Frozen source differs: '+key);input_pins[key]=pin(path);data[key]=read(path)
    context=data['context'];native=data['nativeR16'];ecology=data['ecology']
    require(context['activeDesign']==native['activeDesign'] and context['housePlacement']['streetSetbackMm']==context['housePlacement']['eastSetbackMm']==3000,'C/B/B3000 source changed')
    camera=Camera(next(v for v in data['views']['views']if v['id']=='exterior-canopy-close'));frustum=camera.ground_domain()
    masks={k:shape(json.loads(v))for k,v in ecology['exclusionDomainsCm'].items()}
    require(set(masks)=={'protected','subject','roads','buildings','cultivatedGround'},'Exact original safeguards missing')
    masks['managedLawn']=unary_union([Polygon(p)for p in data['managedLawn']['managedLawnKeepPolygonsCm']])
    substrate=shape(json.loads(data['substrate']['domainCm']));require(substrate.equals(shape(json.loads(ecology['ecologyDomainCm']))),'Original litter domain differs')
    blocked=unary_union([p.buffer(75)for p in masks.values()]);domain=frustum.difference(blocked).difference(substrate.buffer(2))
    require(domain.is_valid and 100<domain.area/10000<260,'Unexpected bounded clearing domain')
    ground=Ground(context,data['terrain'],frustum.buffer(50));models=prototypes(data)
    classification=[]
    for m in context['meshes']:
        if m['material']not in GROUND_KEYS:continue
        vs=np.asarray(m['verticesCm']); faces=np.asarray(m['indices']).reshape(-1,3);tri=vs[faces]
        lo,hi=tri[:,:,:2].min(axis=1),tri[:,:,:2].max(axis=1);x0,y0,x1,y1=frustum.bounds
        selected=(hi[:,0]>=x0)&(hi[:,1]>=y0)&(lo[:,0]<=x1)&(lo[:,1]<=y1)
        area=sum(Polygon(t[:,:2]).intersection(frustum).area for t in tri[selected])/10000
        if area>1e-8:classification.append({'meshId':m['id'],'material':m['material'],'intersectionAreaM2':area})
    require(not classification,'Clearing intersects an existing authored land-use surface; reclassify before proposing')
    mesh,witnesses=surface(domain,ground)
    new_surface=Ground({'meshes':[]},{'meshes':[mesh]},domain)
    roots,centers,rejected=plants(domain,camera,ground,models,new_surface)
    tris=np.asarray(mesh['verticesCm'])[np.asarray(mesh['indices']).reshape(-1,3)];area=sum(Polygon(t[:,:2]).area for t in tris)
    require(abs(area-domain.area)<.001 and len(mesh['indices'])//3<12000,'Surface partition coverage/budget differs')
    # GEOS clipped-cell coordinates can differ at their shared boundary by
    # sub-micrometre float rounding. This is not a mask-clearance relaxation.
    boundary_epsilon_cm=1e-6
    require(all(domain.buffer(boundary_epsilon_cm).covers(Polygon(t[:,:2]))for t in tris),'Surface triangle leaves valid source domain')
    outside_area=sum(Polygon(t[:,:2]).difference(domain).area for t in tris)
    require(outside_area<1e-4,'Surface has substantive area outside exact domain')
    require(all(-25-1e-6<=p[2]<=-24.2+1e-6 for p in mesh['verticesCm']),'Source microrelief exceeds0.8cm')
    material=native['materials']['materials']['context_meadow'];terrain_material=native['materials']['materials']['context_distant_terrain']
    maps=[]
    for rec in [material['recipe'],material['recipe'].get('groundCover',{})]:
        for role,row in rec.get('maps',{}).items():
            path=Path(row['path']);require(sha(path)==row['sha256'],'Existing PBR source pixels changed');maps.append({'role':role,**pin(path)})
    selected_plant_recipes={}
    for key in ('garden_blade_photo','regional_green_leaf','canopy_understory_stem'):
        record=native['materials']['materials'][key];selected_plant_recipes[key]={'nativeMaterial':record['asset'],'nativeGraphSha256':record['graphSha256'],'recipe':record['recipe']}
        for role,row in record['recipe'].get('maps',{}).items():
            path=Path(row['path']);require(sha(path)==row['sha256'],'Existing plant photographic pixels changed')
            input_pins['existingPlantTexture:'+key+':'+role]=pin(path)
    for index,row in enumerate(maps):input_pins['existingPBRTexture:'+str(index)]=row
    for rec in models.values():rec.pop('_points')
    groups=[{'id':'EX_canopy_foreground_r21_'+identity,'meshId':identity,'nativeMesh':models[identity]['nativeMesh'],'nativeMaterials':models[identity]['nativeMaterials'],
             'instances':[r for r in roots if r['meshId']==identity],'renderingPolicy':{'collision':'NoCollision','navigation':False,'windDisplacementCm':0,'qualityDetail':True,'cullStartCm':4500,'cullEndCm':6000}}for identity in MODELS]
    budget=[sum(len(g['instances'])*models[g['meshId']]['decodedLods'][level]['triangles']for g in groups)for level in range(3)]
    mask_audit={k:{'sourceGeometrySha256':digest(mapping(v)),'areaM2':v.area/10000,'frustumIntersectionAreaM2':v.intersection(frustum).area/10000,'minimumNewRootWholeFootprintClearanceCm':min(Point(r['positionCm'][:2]).distance(v)-r['radiusCm']for r in roots)}for k,v in masks.items()}
    dither_path=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Content/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.uasset')
    require(sha(dither_path)=='e92577ec6d1ede4570eb7c8520ac63e82890cb7335cc9e389503406d145b72a7','Installed dither function differs')
    input_pins['installedDitherFunction']=pin(dither_path)
    material_recipe={'id':mesh['material'],'kind':'fresh-native-meadow-graph-copy-with-masked-UV1-temporal-dither-feather','sourceNativeMaterial':material['asset'],
        'sourceGraphSha256':material['graphSha256'],'preserveOriginalGraph':True,'preserveAllExistingPBRRootsExceptNewOpacityMask':True,'newMaterialCount':1,'newTextureObjects':0,
        'sourceTexturePins':maps,'baseRecipe':material['recipe'],'featherCoverage':'UV1.x smoothstep(distance-to-exact-domain-edge / coherent95..120cmwidth)',
        'opacityMaskProposal':'DitherTemporalAA(UV1.x), new MASKED material only; native graph/saved values and actual seam appearance pending',
        'nativeDitherFunction':'/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA','installedDitherFunction':pin(dither_path),
        'sourcePixelsUnchanged':True,'scanClaim':'SparseGrass PolyHaven photographic input plus existing AmbientCG Grass004 procedural cover; never all-photographic claim'}
    audit={'sourceOnly':True,'sourceLandUseClass':'UNRESOLVED_OUTSIDE_AUTHORED_CONTEXT_SURFACES','landUseObservationClaimed':False,'measuredElevation':False,
        'ground':'context_unresolved_flat_backdrop','baseZcm':-25,'actualFrustumAreaM2':frustum.area/10000,'surfaceAreaM2':domain.area/10000,'surfaceTriangles':len(mesh['indices'])//3,
        'newLowRoots':len(roots),'newGroups':4,'newMeshAssets':1,'newMaterialAssets':1,'newTextureAssets':0,'sourceInstanceTriangleBudgetByLOD':budget,
        'maximumVisibleSourceDrawSectionsAtOneLOD':7,'drawLimit':'1 surface +2grass single-section groups+2herb two-section groups; excludes shadow passes, cluster splitting and native GPU cost',
        'sourceRootDistanceM':[min(math.dist(r['positionCm'][:2],camera.eye[:2])for r in roots)/100,max(math.dist(r['positionCm'][:2],camera.eye[:2])for r in roots)/100],
        'rootHeightRangeCm':[min(r['actualHeightCm']for r in roots),max(r['actualHeightCm']for r in roots)],'allSourceLODVerticesInsideActualCameraFrustum':True,
        'minimumRootSpacingCm':min(math.dist(a['positionCm'][:2],b['positionCm'][:2])for i,a in enumerate(roots)for b in roots[i+1:]),
        'maximumMicroreliefCm':max(p[2]+25 for p in mesh['verticesCm']),'sourceBoundaryEpsilonCm':boundary_epsilon_cm,'actualOutsideExactDomainAreaCm2':outside_area,
        'masks':mask_audit,'authoringClusters':len(centers),'rejections':rejected,
        'originalEcologyRootsPreserved':len(ecology['ecologyPlacements']),'originalNearestGroveTreesPreserved':len(ecology['existingTrees']),
        'originalTreeRootGroupsChanged':0,'originalGroundChanged':False,'originalGroveSubstrateExpanded':False,'nativeApplied':False,'nativeGeometryDecoded':False,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    output.mkdir(parents=True)
    write(output/'foreground-surface-geometry.json',{'mesh':mesh,'sourceGroundVertexWitnesses':witnesses})
    write(output/'foreground-root-groups.json',{'groups':groups,'models':models,'authoringClusters':centers})
    write(output/'foreground-material-recipe.json',material_recipe)
    plots(output,camera,frustum,domain,masks,substrate,ecology,roots,mesh)
    plan={'schemaVersion':1,'owner':OWNER,'status':'source-only-bounded-artistic-foreground-native-pending','generatorSha256':sha(ROOT/OWNER),'inputFiles':input_pins,
        'activeDesign':context['activeDesign'],'housePlacement':context['housePlacement'],'camera':camera.row,'cameraAspectRatio':16/9,'cameraForward':camera.forward.tolist(),
        'scope':'ONE bounded unsurveyed grass/soil transition candidate, 2..20m Euclidean ground range in the existing close camera; no wider scene population',
        'domainCm':json.dumps(mapping(domain),separators=(',',':')),'frustumGroundDomainCm':json.dumps(mapping(frustum),separators=(',',':')),
        'sourceClassification':{'contextSurfaceIntersections':classification,'groundSource':data['terrain']['heightPolicy']if 'heightPolicy'in data['terrain']else'Unresolved flat source fallback; not measured elevation'},
        'groundShaderDiagnosis':{'actualTerrainNodes':len(terrain_material['graph']['nodes']),'actualTerrainGraphSha256':terrain_material['graphSha256'],
            'actualNormalRoot':terrain_material['graph']['roots']['NORMAL'],'actualRoughnessRoot':terrain_material['graph']['roots']['ROUGHNESS'],
            'reason':'Existing terrain has PBR response, but scanRGB/normal strength only.30Near over green procedural fallback; it is not a constant-only shader.'},
        'geometry':pin(output/'foreground-surface-geometry.json'),'roots':pin(output/'foreground-root-groups.json'),'materialRecipe':pin(output/'foreground-material-recipe.json'),
        'existingPlantMaterialRecipes':selected_plant_recipes,
        'audit':audit,'preservedSourceArrays':{k:digest(context[k])for k in ['regionalVegetationPlacements','meadowBladePlacements','meadowUnderstoryPlacements','meshes','groups']},
        'limits':['Artist-authored clearing interpretation outside observed source land-use classes; no planting, cadastral-use or surveyed-height claim.',
                  'Source masks and geometry prove containment only; native import, saved material copy, temporal dither seam and paired visual review remain required.',
                  'Original source meshes, shaders, textures, house, trees, managed lawn, cultivated parcels and grove leaf substrate stay unchanged.',
                  'Source draw/triangle budgets exclude occlusion, cluster submissions, transparency, shadow passes, GPU timing and packaging.'],
        'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    for row in input_pins.values():require(sha(row['path'])==row['sha256'],'Input changed during source study')
    write(output/'foreground-transition-plan.json',plan)
    write(output/'source-validation.json',{'schemaVersion':1,'owner':OWNER,'status':'PASS_SOURCE_GEOMETRY_MASKS_BUDGETS_NATIVE_PENDING','createdAt':datetime.now(timezone.utc).isoformat(),
        'plan':pin(output/'foreground-transition-plan.json'),'audit':audit,'outputs':{p.name:pin(p)for p in sorted(output.iterdir())if p.is_file()},'nativeExecuted':False})
    print(json.dumps({'plan':pin(output/'foreground-transition-plan.json'),'audit':audit}))


if __name__=='__main__':main()
