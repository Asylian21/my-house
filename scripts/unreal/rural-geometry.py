"""Deterministic, source-bounded rural context for parcel 6012/26.

Ordinary Python authoring only. All vertices/instances are Unreal centimetres.
The existing house, cadastral placement, road alignment and walking collision
remain authoritative. Vegetation is illustrative interpretation of p1-p4, not a
botanical inventory or an as-built survey. Native import/readback is separate.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]
SEED = 601226


def require(value, message):
    if not value:
        raise ValueError(message)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def normal(v):
    length = math.sqrt(sum(x*x for x in v))
    return tuple(x / max(length, 1e-12) for x in v)


class Mesh:
    def __init__(self, id_, material, nanite=False, clockwise=False):
        self.id = id_; self.material = material; self.nanite = nanite
        self.clockwise = clockwise
        self.vertices = []; self.indices = []; self.uvs = []

    def triangle(self, a, b, c, uvs=None):
        area=cross([b[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)])
        if sum(v*v for v in area)<1e-14:return
        start = len(self.vertices)
        self.vertices.extend([list(a), list(b), list(c)])
        self.indices.extend([start, start+1, start+2])
        self.uvs.extend(uvs or [[p[0]/100, p[1]/100] for p in (a,b,c)])

    def quad(self, a, b, c, d, uvs=None):
        uv = uvs or [[p[0]/100, p[1]/100] for p in (a,b,c,d)]
        self.triangle(a,b,c,[uv[0],uv[1],uv[2]])
        self.triangle(a,c,d,[uv[0],uv[2],uv[3]])

    def box(self, center, size):
        x,y,z = center; a,b,c = [v/2 for v in size]
        p = [(x+sx*a,y+sy*b,z+sz*c) for sx,sy,sz in
             [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.quad(*(p[i] for i in face))

    def tube(self, a, b, radius, end_radius=None, sides=6):
        axis = normal([b[i]-a[i] for i in range(3)])
        tangent = normal(cross(axis,(0,0,1) if abs(axis[2])<.95 else (1,0,0)))
        bitangent = cross(axis,tangent); end_radius = radius if end_radius is None else end_radius
        ring = lambda p,r: [tuple(p[k]+r*(math.cos(i*math.tau/sides)*tangent[k]+math.sin(i*math.tau/sides)*bitangent[k]) for k in range(3)) for i in range(sides)]
        lo,hi=ring(a,radius),ring(b,end_radius)
        for i in range(sides):
            j=(i+1)%sides; self.quad(lo[i],lo[j],hi[j],hi[i])
        for i in range(1,sides-1):
            self.triangle(lo[0],lo[i+1],lo[i]); self.triangle(hi[0],hi[i],hi[i+1])

    def leaf(self, center, length, width, yaw, tilt, serrated=False):
        # Folded, pointed lamina with a raised midrib, never a spherical canopy.
        along=(math.cos(yaw)*math.cos(tilt),math.sin(yaw)*math.cos(tilt),math.sin(tilt))
        side=(-math.sin(yaw),math.cos(yaw),0)
        point=lambda u,v,h=0: tuple(center[k]+along[k]*u+side[k]*v+(h if k==2 else 0) for k in range(3))
        tip=point(length,0); base=point(0,0); mid=point(length*.45,0,width*.13)
        if serrated:
            perimeter=[base]
            for s in (-1,1):
                order=range(1,8) if s<0 else range(7,0,-1)
                for j in order:
                    fraction=j/8; w=width*math.sin(fraction*math.pi)*(.5 if j%2 else .29)
                    perimeter.append(point(length*fraction,s*w))
                if s<0: perimeter.append(tip)
            for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):
                self.triangle(mid,a,b,[[.5,.5],[0,0],[1,1]])
        else:
            left=point(length*.45,-width/2);right=point(length*.45,width/2)
            for a,b in [(base,left),(left,tip),(tip,right),(right,base)]:
                self.triangle(mid,a,b,[[.5,.5],[0,0],[1,1]])

    def data(self, level=None):
        result={'id':self.id,'material':self.material,'nanite':self.nanite,
                'verticesCm':[[round(v,5) for v in p] for p in self.vertices],
                'indices':self.indices if self.clockwise else [i for t in range(0,len(self.indices),3) for i in (self.indices[t],self.indices[t+2],self.indices[t+1])],
                'uvs':self.uvs,'winding':'clockwise'}
        if level is not None: result['level']=level
        return result


def read_obj(path, wanted):
    vertices=[]; selected={name:[] for name in wanted}; current=None
    for line in path.read_text().splitlines():
        parts=line.split()
        if not parts: continue
        if parts[0]=='v': vertices.append(tuple(map(float,parts[1:4])))
        elif parts[0]=='o': current=parts[1]
        elif parts[0]=='f' and current in selected:
            face=[vertices[int(p.split('/')[0])-1] for p in parts[1:]]
            for i in range(1,len(face)-1): selected[current].append((face[0],face[i],face[i+1]))
    require(all(selected.values()),'Source OBJ target missing')
    return {id_:[tuple((p[0]/10,-p[1]/10,p[2]/10) for p in tri) for tri in triangles] for id_,triangles in selected.items()}


def subdivide(triangle, maximum=65):
    a,b,c=triangle
    distances=[sum((p[k]-q[k])**2 for k in (0,1)) for p,q in [(a,b),(b,c),(c,a)]]
    if max(distances)<=maximum**2:
        yield triangle; return
    i=distances.index(max(distances)); p,q,r=[(a,b,c),(b,c,a),(c,a,b)][i]
    m=tuple((p[k]+q[k])/2 for k in range(3))
    yield from subdivide((p,m,r),maximum);yield from subdivide((m,q,r),maximum)


def clip(poly, axis, bound, less=True):
    output=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ia=(a[axis]<=bound) if less else (a[axis]>=bound)
        ib=(b[axis]<=bound) if less else (b[axis]>=bound)
        if ia: output.append(a)
        if ia != ib:
            t=(bound-a[axis])/(b[axis]-a[axis])
            output.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(3)))
    return output


def barycentric_sample(triangles, density, rng):
    for a,b,c in triangles:
        area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2/10000
        expected=area*density; count=int(expected)+(rng.random()<expected%1)
        for _ in range(count):
            u,v=rng.random(),rng.random()
            if u+v>1:u,v=1-u,1-v
            yield tuple(a[k]+u*(b[k]-a[k])+v*(c[k]-a[k]) for k in range(3))


def terrain_noise(x,y):
    return .9*math.sin(x*.023+y*.019)+.6*math.sin(x*.053-y*.017)+.3*math.sin(x*.19+y*.16)


def boundary_segments(triangles):
    edges={}
    for tri in triangles:
        for a,b in zip(tri,tri[1:]+tri[:1]):
            key=tuple(sorted([tuple(round(v,3) for v in a[:2]),tuple(round(v,3) for v in b[:2])]))
            if key in edges:edges[key][0]+=1
            else:edges[key]=[1,a,b]
    return [(a,b) for count,a,b in edges.values() if count==1]


def segment_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def edge_clear(p,edges,radius):
    return all(segment_distance(p,a,b)>radius for a,b in edges)


def point_in_triangle(p,triangle):
    signs=[(p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0]) for a,b in zip(triangle,triangle[1:]+triangle[:1])]
    return all(s>=-1e-7 for s in signs) or all(s<=1e-7 for s in signs)


def road_continuations(source_roads):
    """Append visual context at exact OBJ terminal edges; never edit source."""
    result=[];meshes=[];triangles=[];shoulders=[]
    for name,identity,selector in [('main_west','DOM_00005',lambda a,b:max(a[0],b[0])<-7000),
                                  ('corner_rear','DOM_00006',lambda a,b:max(a[1],b[1])<-1300),
                                  ('corner_front','DOM_00006',lambda a,b:min(a[1],b[1])>2350)]:
        edges=boundary_segments(source_roads[identity]);matches=[(a,b) for a,b in edges if selector(a,b)]
        require(len(matches)==1,'Ambiguous exact source road terminal: '+name)
        a,b=matches[0]
        tangents=[]
        for endpoint in (a,b):
            adjacent=[q if p==endpoint else p for p,q in edges if (p==endpoint or q==endpoint) and {p,q}!={a,b}]
            require(len(adjacent)==1,'Source terminal tangent ambiguous')
            tangents.append(normal([endpoint[k]-adjacent[0][k] for k in range(3)]))
        tangent=normal([sum(v[k] for v in tangents) for k in range(3)])
        distance=100000.0 # 1 km beyond the clipped cadastre context, not surveyed
        end_a=tuple(a[k]+tangent[k]*distance for k in range(3));end_b=tuple(b[k]+tangent[k]*distance for k in range(3))
        road=Mesh('road_extension_'+name,'road',True)
        points=[a,b,end_b,end_a]
        if cross([b[k]-a[k] for k in range(3)],[end_b[k]-a[k] for k in range(3)])[2]<0:points.reverse()
        road.quad(*points);meshes.append({**road.data(),'collision':'NoCollision'})
        # Save clockwise triangles exactly as emitted to make safety proofs and
        # later deterministic pruning include the extended carriageway.
        native=road.data();triangles.extend(tuple(tuple(native['verticesCm'][j]) for j in native['indices'][i:i+3]) for i in range(0,len(native['indices']),3))
        curb=Mesh('road_extension_curb_'+name,'curb',True)
        shoulder=Mesh('road_extension_shoulder_'+name,'soil',True)
        for endpoint,other in ((a,b),(b,a)):
            outward=normal([endpoint[k]-other[k] for k in range(3)])
            normal_axis=(-tangent[1],tangent[0],0)
            # Meter modules have real joints and follow the source terminal
            # tangent. New colliders are deliberately never generated.
            prototype=Mesh('module','curb');prototype.box((0,0,5),(99.5,12,10))
            for n in range(1000):
                base=tuple(endpoint[k]+tangent[k]*(n*100+50) for k in range(3))
                for i in range(0,len(prototype.indices),3):
                    curb.triangle(*(tuple(base[k]+p[0]*tangent[k]+p[1]*normal_axis[k]+(p[2] if k==2 else 0) for k in range(3))
                                    for p in [prototype.vertices[j] for j in prototype.indices[i:i+3]]))
            width=250.0
            inner=tuple(endpoint[k]+outward[k]*6 for k in range(3));outer=tuple(endpoint[k]+outward[k]*width for k in range(3))
            inner=(inner[0],inner[1],-3.0);outer=(outer[0],outer[1],-19.6)
            ei=tuple(inner[k]+tangent[k]*distance for k in range(3));eo=tuple(outer[k]+tangent[k]*distance for k in range(3))
            points=[inner,outer,eo,ei]
            if cross([outer[k]-inner[k] for k in range(3)],[eo[k]-inner[k] for k in range(3)])[2]<0:points.reverse()
            shoulder.quad(*points)
            shoulders.append({'edgeCm':list(endpoint),'outward':list(outward),'tangent':list(tangent),'widthCm':width})
        meshes.extend([{**curb.data(),'collision':'NoCollision'},{**shoulder.data(),'collision':'NoCollision'}])
        result.append({'id':name,'sourceObjectId':identity,'terminalEdgeCm':[list(a),list(b)],'tangent':list(tangent),
                       'distanceCm':distance,'endEdgeCm':[list(end_a),list(end_b)],'collision':'NoCollision',
                       'provenance':'Exact source seam and adjacent-edge tangent; unsurveyed visual continuation beyond source envelope'})
    return meshes,result,triangles,shoulders


def grass_prototype(variant,level):
    rng=random.Random(SEED+variant*71); mesh=Mesh(f'dry_grass_{variant}','drygrass')
    count=[144,68,26][level]
    # Blade length remains fixed, so width (not sqrt(width)) compensates the
    # lower blade count; this preserves grass area through the far LODs.
    coverage=144/count
    for i in range(count):
        seed_stalk=i%13==0
        yaw=rng.random()*math.tau; height=rng.uniform(49,69) if seed_stalk else rng.uniform(15,44)
        lean=rng.uniform(10,24) if seed_stalk else rng.uniform(18,40)
        root=(rng.uniform(-14,14),rng.uniform(-14,14),0); width=rng.uniform(.55,1.15)*coverage
        side=(-math.sin(yaw),math.cos(yaw),0); points=[]
        for t in (0,.38,.76,1):
            # Senescent field grasses arch and fan out, not upright reed pickets.
            center=(root[0]+math.cos(yaw)*lean*t*t,root[1]+math.sin(yaw)*lean*t*t,height*(t-.25*t*t))
            w=width*(1-t)*.5
            points.append([tuple(center[k]+s*w*side[k] for k in range(3)) for s in (-1,1)])
        for a,b in zip(points,points[1:]):mesh.quad(a[0],a[1],b[1],b[0])
        if seed_stalk:
            tip=(root[0]+math.cos(yaw)*lean,root[1]+math.sin(yaw)*lean,height*.75)
            for j in range(3 if level else 5):
                p=(tip[0],tip[1],tip[2]-j*1.6)
                mesh.leaf(p,3.8,.9,yaw+j*2.4,.65)
    return mesh


def weed_prototype(kind,level):
    rng=random.Random(SEED+(17 if kind=='ragweed' else 39));mesh=Mesh(kind,'weed')
    stems=[7,5,3][level]
    branches=[7,5,3][level]
    leaflets=[5,4,3][level]
    coverage=math.sqrt(7*7*5/(stems*branches*leaflets))
    for s in range(stems):
        height=rng.uniform(38,86);yaw=rng.random()*math.tau;root=(rng.uniform(-12,12),rng.uniform(-12,12),0)
        spread=rng.uniform(9,22);tip=(root[0]+math.cos(yaw)*spread,root[1]+math.sin(yaw)*spread,height)
        mesh.tube(root,tip,.38,.1,4)
        for j in range(branches):
            fraction=.16+.68*j/max(1,branches-1);z=height*fraction;a=yaw+j*2.399
            p=(root[0]+math.cos(yaw)*spread*fraction,root[1]+math.sin(yaw)*spread*fraction,z)
            reach=rng.uniform(19,29)*(1-fraction*.35)
            end=(p[0]+math.cos(a)*reach,p[1]+math.sin(a)*reach,z+rng.uniform(8,17))
            mesh.tube(p,end,.18,.05,3)
            for k in range(leaflets):
                t=.18+.79*k/max(1,leaflets-1)
                center=tuple(p[n]+(end[n]-p[n])*t for n in range(3))
                length=rng.uniform(4.3,7.8)*coverage
                # Alternate compound/lobed leaves distributed along real twigs.
                for sign in (-1,1):
                    angle=a+sign*(.72+rng.random()*.4)
                    mesh.leaf(center,length,length*.39,angle,rng.uniform(-.3,.65),serrated=kind=='thistle' and level==0)
                    if kind=='ragweed':
                        for q in (-1,1):
                            lobe=(center[0]+math.cos(angle)*length*.4,center[1]+math.sin(angle)*length*.4,center[2]+length*.08)
                            mesh.leaf(lobe,length*.48,length*.22,angle+q*.78,.12)
        if kind=='thistle':
            for j in range([12,8,4][level]):
                mesh.leaf((tip[0],tip[1],tip[2]-3),5,1.5,j*math.tau/12,.7)
        else:
            for j in range([8,5,3][level]):
                mesh.leaf((tip[0],tip[1],tip[2]-j*1.3),2.3,1.5,yaw+j*2.4,.5)
    return mesh


def tree_prototype(variant,level):
    rng=random.Random(SEED+variant*101)
    height=[730,910,640][variant];bark=Mesh(f'tree_bark_{variant}','bark');leaves=Mesh(f'tree_leaf_{variant}','leaf')
    bend=(rng.uniform(-24,24),rng.uniform(-18,18));root=(0,0,0);trunk=(bend[0],bend[1],height)
    bark.tube(root,trunk,8+variant*1.4,.65,[9,7,5][level])
    # Ascending boughs produce the tall, irregular Populus/Robinia silhouette.
    branch_count=[28,24,18][level]
    leaf_count=[280,150,75][level]
    coverage=math.sqrt(28*280/(branch_count*leaf_count))
    for i in range(branch_count):
        fraction=.22+.73*i/max(1,branch_count-1);angle=i*2.399+rng.uniform(-.35,.35)
        crown_radius=(55+120*math.sin(fraction*math.pi))*(.82 if variant==1 else 1)
        anchor=(bend[0]*fraction,bend[1]*fraction,height*fraction)
        endpoint=(anchor[0]+math.cos(angle)*crown_radius,anchor[1]+math.sin(angle)*crown_radius,min(height+15,anchor[2]+rng.uniform(65,140)))
        bark.tube(anchor,endpoint,2.1*(1-fraction)+.5,.18,4 if level else 5)
        for j in range(leaf_count):
            t=.32+rng.random()*.68
            # Small separated clusters around individual twigs; no opaque blobs.
            cx=anchor[0]+t*(endpoint[0]-anchor[0]);cy=anchor[1]+t*(endpoint[1]-anchor[1]);cz=anchor[2]+t*(endpoint[2]-anchor[2])
            az=rng.random()*math.tau;radius=math.sqrt(rng.random())*rng.uniform(23,51)
            p=(cx+math.cos(az)*radius,cy+math.sin(az)*radius,cz+rng.uniform(-28,47))
            # Preserve total leaf area through LOD transitions; tiny far leaves
            # disappearing was the cause of R1's skeletal winter canopy.
            size=rng.uniform(7,11.7)*coverage
            leaves.leaf(p,size,size*.7,rng.random()*math.tau,rng.uniform(-.5,.65))
    return bark,leaves


def build(scene, obj_path):
    require(scene['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'},'C/B/B required')
    placement=scene['house']['placement']
    require(placement['streetSetbackMm']==placement['eastSetbackMm']==3000,'3000mm setbacks required')
    require(scene['sceneCenterMm']=={'x':15200,'y':10800},'Review changed scene coordinate frame')
    objects=[o for o in scene['objects'] if o['enabled']];by_id={o['id']:o for o in objects}
    verges=[o for o in objects if o.get('metadata',{}).get('walkSurfaceId','').startswith(('front-road-reserve-','side-road-reserve-'))]
    lawn=next(o for o in objects if o.get('metadata',{}).get('walkSurfaceId')=='parcel-6012-26')
    road_ids=[o['id'] for o in objects if o['materialNames']==['real-road']]
    require(set(road_ids)=={'DOM_00005','DOM_00006'},'Review changed source road identities')
    triangles=read_obj(obj_path,[o['id'] for o in verges]+[lawn['id']]+road_ids)
    meshes=[];groups=[];hide=[];replacements=[];rng=random.Random(SEED)
    extension_meshes,extension_contract,extension_triangles,extension_shoulders=road_continuations(triangles)
    meshes.extend(extension_meshes)
    hide.extend(o['id'] for o in objects
                if o['group']=='Landscape' and o['materialNames']==['real-plant-grass']
                and o['name'].startswith('Riedka náletová vegetácia krajnice ')
                and 'krížená botanická karta' in o['name'])
    legacy_hedge={'DOM_01835':'real-hedge-dark','DOM_01837':'real-hedge-dark',
                  'DOM_01838':'real-hedge-mid','DOM_01839':'real-hedge-light'}
    for id_,material in legacy_hedge.items():
        source=by_id.get(id_)
        require(source and source['materialNames']==[material]
                and source.get('metadata',{}).get('entityId')=='SITE-FENCE'
                and source['name'].startswith('Zadná hranica ·'),'Legacy visual hedge identity changed')
        hide.append(id_)
    def add(mesh):meshes.append(mesh.data());return mesh
    def instances(id_,mesh_id,poses,cull=18000,shadow=True):
        groups.append({'id':id_,'meshId':mesh_id,'instances':poses,'cullStartCm':int(cull*.75),'cullEndCm':cull,'castShadow':shadow,'collision':'NoCollision'})
    def pose(p,scale=1):return {'positionCm':list(p),'yawDeg':rng.random()*360,'scale':[scale,scale,scale]}
    def plan(x,y,z=0):return ((x-15200)/10,(10800-y)/10,z/10)
    for o in objects:
        source_id=o['sourceId'];materials=set(o['materialNames'])
        key=None;nanite=False
        if materials=={'real-road'}:key='road';nanite=True
        elif materials=={'real-terrain'}:key='field'
        elif 'obrubní' in o['name'].casefold() and o.get('metadata',{}).get('entityId')=='ROAD-6012-1':key='curb';nanite=True
        if key:replacements.append({'objectId':o['id'],'sourceId':o['id'],'semanticId':source_id,'material':key,'nanite':nanite})
    foliage_triangles=[]
    for o in verges:
        mesh=Mesh('verge_'+o['id'],'soil',True,clockwise=True)
        for tri in triangles[o['id']]:
            for small in subdivide(tri,55):
                mesh.triangle(*(tuple([p[0],p[1],p[2]+.35+terrain_noise(p[0],p[1])*.45]) for p in small))
        add(mesh);hide.append(o['id']);foliage_triangles.extend(triangles[o['id']])
    # Source-triangulated parcel grass is retained under these thin rough areas;
    # only the front unmaintained strip is covered; atrium/pool remain untouched.
    front=Mesh('parcel_outer_raw_soil','soil',True,clockwise=True);front_triangles=[]
    # Disjoint plan regions cover raw frontage, east side, rear margin and west
    # service strip. Only the courtyard and pool garden retain maintained turf.
    regions=[[(1,780,False)],
             [(1,780,True),(0,1284,False)],
             [(1,-1200,True),(0,1284,True)],
             [(1,780,True),(1,-40,False),(0,-876,True)],
             [(1,-40,True),(1,-1200,False),(0,-1530,True)]]
    for tri in triangles[lawn['id']]:
        for region in regions:
            polygon=list(tri)
            for axis,bound,less in region:
                polygon=clip(polygon,axis,bound,less)
                if not polygon:break
            for i in range(1,len(polygon)-1):
                clipped=(polygon[0],polygon[i],polygon[i+1]);front_triangles.append(clipped)
                for small in subdivide(clipped,60):
                    front.triangle(*(tuple([p[0],p[1],p[2]+.65+terrain_noise(p[0],p[1])*.22]) for p in small))
    add(front)
    # Only seed inside the source-triangulated verge polygons; source openings
    # therefore remain clear without any approximate rectangular exclusion.
    for variant in range(3):
        base=grass_prototype(variant,0).data();base['lods']=[grass_prototype(variant,l).data(l) for l in (1,2)];meshes.append(base)
    for kind in ('ragweed','thistle'):
        base=weed_prototype(kind,0).data();base['lods']=[weed_prototype(kind,l).data(l) for l in (1,2)];meshes.append(base)
    plant_radius={m['id']:max(math.hypot(p[0],p[1]) for lod in [m]+m.get('lods',[]) for p in lod['verticesCm'])
                  for m in meshes if m['material'] in ('drygrass','weed')}
    verge_boundary=boundary_segments(foliage_triangles);raw_boundary=boundary_segments(front_triangles)
    plant_cells={}
    for p in barycentric_sample(foliage_triangles,15.0,rng):
        # Sparse bare sand at curb, irregular clustered vegetation inland.
        density=.66+.24*math.sin(p[0]*.007+p[1]*.004)+.13*math.sin(p[0]*.018-p[1]*.013)
        if rng.random()>density:continue
        kind=rng.choices(['dry_grass_0','dry_grass_1','dry_grass_2','ragweed','thistle'],[22,21,20,32,5])[0]
        scale=rng.uniform(.65,1.08 if kind.startswith('dry_') else 1.23)
        if not edge_clear(p,verge_boundary,plant_radius[kind]*scale+9):continue
        cell=(math.floor(p[0]/1200),math.floor(p[1]/1200),kind)
        plant_cells.setdefault(cell,[]).append(pose((p[0],p[1],p[2]+.6),scale))
    # Patchy dry low growth in front of the house, excluding all source paths.
    exclusions=[]
    for value in scene['surfaces'].values():
        if isinstance(value,dict) and value.get('polygonMm'):
            exclusions.append([plan(p['x'],p['y']) for p in value['polygonMm']])
    def inside(p,poly):
        result=False
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:result=not result
        return result
    for p in barycentric_sample(front_triangles,2.3,rng):
        if any(inside(p,poly) for poly in exclusions):continue
        kind=rng.choice(['dry_grass_0','dry_grass_1','ragweed']);cell=(math.floor(p[0]/1200),math.floor(p[1]/1200),kind)
        scale=rng.uniform(.48,.8);radius=plant_radius[kind]*scale+9
        if not edge_clear(p,raw_boundary,radius) or any(not edge_clear(p,list(zip(poly,poly[1:]+poly[:1])),radius) for poly in exclusions):continue
        plant_cells.setdefault(cell,[]).append(pose((p[0],p[1],p[2]+1),scale))
    # Broken patches continue into neighbouring undeveloped ground, leaving the
    # existing road corridor and the entire subject plot excluded by distance.
    for i in range(1150):
        x=rng.uniform(-7300,-1900);y=rng.uniform(-3500,1000)
        if math.sin(x*.0027+y*.0038)+math.sin(y*.006)<-.45:continue
        kind=rng.choice(['dry_grass_0','dry_grass_1','dry_grass_2','ragweed'])
        cell=(math.floor(x/1200),math.floor(y/1200),kind)
        plant_cells.setdefault(cell,[]).append(pose((x,y,-19.5),rng.uniform(.6,1.08 if kind.startswith('dry_') else 1.2)))
    # Broken early-successional cover on opposite and east undeveloped plots.
    # Bounds are beyond the actual source road branches and subject parcel.
    for i in range(980):
        x=rng.uniform(2600,8500);y=rng.uniform(2500,7000)
        patch=math.sin(x*.0034+y*.0022)+.65*math.sin(x*.008-y*.003)
        if patch<-.05:continue
        kind=rng.choice(['dry_grass_0','dry_grass_1','dry_grass_2'])
        cell=(math.floor(x/1200),math.floor(y/1200),kind)
        plant_cells.setdefault(cell,[]).append(pose((x,y,-19.5),rng.uniform(.58,.95)))
    for shoulder in extension_shoulders:
        for i in range(44):
            along=rng.uniform(200,15000)
            if math.sin(along*.0017)<-.25:continue
            outward=rng.uniform(95,210);a=shoulder['edgeCm'];t=shoulder['tangent'];n=shoulder['outward']
            x=a[0]+t[0]*along+n[0]*outward;y=a[1]+t[1]*along+n[1]*outward
            z=-3-(outward-6)/(250-6)*16.6
            kind=rng.choice(['dry_grass_0','dry_grass_1','dry_grass_2']);cell=(math.floor(x/1200),math.floor(y/1200),kind)
            plant_cells.setdefault(cell,[]).append(pose((x,y,z+.3),rng.uniform(.65,.98)))
    for (x,y,kind),poses in sorted(plant_cells.items()):instances(f'plants_{x}_{y}_{kind}',kind,poses,12500,False)
    # Two irregular rows, following and extending the actual rear cadastral edge.
    # Trees are outside the fence, a minimum 1.1m beyond the boundary.
    rear=next(r for r in scene['fence']['fixedRuns'] if r['id']=='FENCE-FIXED-REAR')['pointsMm']
    start,end=rear[1],rear[0];dx=end['x']-start['x'];dy=end['y']-start['y'];length=math.hypot(dx,dy)
    # Irregular branching understorey replaces only the clipped hedge visuals.
    # Keep the source fence/mulch and all walking collision untouched.
    bush_height=max(p[2] for p in next(m for m in meshes if m['id']=='ragweed')['verticesCm'])
    bushes=[]
    for i in range(48):
        t=(i+.5)/48+rng.uniform(-.012,.012);away=rng.uniform(900,1800)
        x=start['x']+dx*t-dy/length*away;y=start['y']+dy*t+dx/length*away
        bushes.append({'positionCm':list(plan(x,y,-190)),'yawDeg':rng.random()*360,
                       'scale':[rng.uniform(1.12,1.75),rng.uniform(1.05,1.65),rng.uniform(110,160)/bush_height]})
    instances('windbreak_natural_understorey','ragweed',bushes,22000,True)
    treeposes={v:[] for v in range(3)}
    for row in range(2):
        for i in range(31):
            t=(i-5)/20 + rng.uniform(-.011,.011);away=1100+row*1800+rng.uniform(0,750)
            x=start['x']+dx*t-dy/length*away;y=start['y']+dy*t+dx/length*away
            variant=(i+row)%3;treeposes[variant].append(pose(plan(x,y,-190),rng.uniform(.72,1.2)))
    for variant in range(3):
        pairs=[tree_prototype(variant,l) for l in range(3)]
        for j in range(2):
            data=pairs[0][j].data();data['lods']=[pairs[l][j].data(l) for l in (1,2)];meshes.append(data)
            instances(f'windbreak_{variant}_{j}',data['id'],treeposes[variant],50000,True)
    # A small irregular spoil mound in the neighbouring field behind the
    # windbreak, wholly outside parcel and all architectural circulation.
    mound=Mesh('rear_field_topsoil_mound','soil',True);cx,cy,cz=plan(7000,28500,-200)
    rings=8;segments=36;points=[(cx,cy,cz+91)]
    for ring in range(1,rings+1):
        t=ring/rings
        for i in range(segments):
            angle=i*math.tau/segments;r=t*(1+.07*math.sin(angle*5))
            points.append((cx+math.cos(angle)*490*r,cy+math.sin(angle)*205*r,cz+91*(1-t*t)+terrain_noise(i*15,ring*22)*t*2))
    for i in range(segments):mound.triangle(points[0],points[1+i],points[1+(i+1)%segments])
    for r in range(rings-1):
        a=1+r*segments;b=a+segments
        for i in range(segments):j=(i+1)%segments;mound.quad(points[a+i],points[b+i],points[b+j],points[a+j])
    add(mound)
    # Recessed 600mm cast-iron cover flush with the -115mm carriageway datum.
    mx,my,mz=plan(18000,-6600,-115);cover=Mesh('road_manhole_cover','iron',True)
    cover.tube((mx,my,mz-5),(mx,my,mz+.16),30,30,64)
    for axis in range(2):
        for offset in range(-24,25,6):
            extent=math.sqrt(27**2-offset**2)
            center=(mx+offset,my,mz+.29) if axis==0 else (mx,my+offset,mz+.32)
            cover.box(center,(.75,extent*2,.24) if axis==0 else (extent*2,.75,.24))
    add(cover)
    ring=Mesh('road_manhole_frame','iron',True)
    for i in range(64):
        a=i*math.tau/64;b=(i+1)*math.tau/64
        ring.quad((mx+math.cos(a)*30,my+math.sin(a)*30,mz+.22),(mx+math.cos(a)*33,my+math.sin(a)*33,mz+.22),(mx+math.cos(b)*33,my+math.sin(b)*33,mz+.22),(mx+math.cos(b)*30,my+math.sin(b)*30,mz+.22))
    add(ring)
    stakes=Mesh('survey_marker_cap','marker');stakes.box((0,0,2),(9,9,4));add(stakes)
    rod=Mesh('survey_marker_pin','steel');rod.tube((0,0,-12),(0,0,2),.8,sides=8);add(rod)
    # Corner and front markers, illustrative; never redefine legal coordinates.
    marker_points=[plan(-77.913405454,0,-30),plan(28116.086594546,0,-30),plan(31003.086594546,2185,-30)]
    marker_poses=[{'positionCm':list(p),'yawDeg':0,'scale':[1,1,1]} for p in marker_points]
    instances('survey_caps','survey_marker_cap',marker_poses,16000);instances('survey_pins','survey_marker_pin',marker_poses,16000)
    managed=[[-1530,-40],[1284,-40],[1284,-1200],[-1530,-1200]]
    central=[[-876,780],[1284,780],[1284,-40],[-876,-40]]
    # Every vegetation LOD must clear the extended visual road, including trees
    # whose former positions were beyond the old finite corridor. Pair leaf and
    # bark radii so pruning cannot leave either component behind on the road.
    all_road=[t for id_ in road_ids for t in triangles[id_]]+extension_triangles
    road_edges=boundary_segments(all_road);mesh_map={m['id']:m for m in meshes};pruned={}
    for group in groups:
        mesh=mesh_map[group['meshId']]
        if mesh['material'] not in ('drygrass','weed','leaf','bark'):continue
        radius_meshes=[mesh]
        if group['meshId'].startswith(('tree_bark_','tree_leaf_')):
            suffix=group['meshId'].rsplit('_',1)[1]
            radius_meshes=[mesh_map['tree_bark_'+suffix],mesh_map['tree_leaf_'+suffix]]
        radius=max(math.hypot(p[0],p[1]) for m in radius_meshes for lod in [m]+m.get('lods',[]) for p in lod['verticesCm'])
        kept=[]
        for instance in group['instances']:
            p=instance['positionCm'];r=radius*max(instance['scale'])+9
            if any(point_in_triangle(p,t) for t in all_road) or not edge_clear(p,road_edges,r):continue
            kept.append(instance)
        if len(kept)!=len(group['instances']):pruned[group['id']]=len(group['instances'])-len(kept)
        group['instances']=kept
    groups=[g for g in groups if g['instances']]
    return {'schemaVersion':1,'status':'authored-geometry-not-native-verified','units':'centimetres','axes':'UE X=OBJ X/10, Y=-OBJ Y/10, Z=OBJ Z/10',
        'meshes':meshes,'groups':groups,'hideSourceIds':hide,'replacementMaterials':replacements,
        'managedLawnKeepPolygonsCm':[managed,central],
        'roadContinuations':extension_contract,
        'metadata':{'seed':SEED,'activeDesign':scene['activeDesign'],'housePlacement':placement,'sourceObjSha256':hashlib.sha256(obj_path.read_bytes()).hexdigest(),
        'preserved':['house geometry','C/B/B','3000mm street and east setbacks','cadastral boundary','source road curvature','all walking collision','courtyard and pool lawn','existing fence'],
        'hideReason':'Five source soil verges, 27 roadside botanical cards and four exact SITE-FENCE hedge visual proxies are replaced. Source fence/mulch and all collision stay active.',
        'treePlacement':'Two irregular rows 1.1m or more beyond source rear cadastral line; extended along same line for continuous windbreak.',
        'geometrySource':'Authored geometric grass blades, branching ragweed and serrated thistle leaves, tapered branching trunks and folded deciduous leaves. No canopy spheres or billboard rectangles.',
        'siteAccuracy':'Photo interpreted visualization; infrastructure and plants are not as-built survey coordinates.',
        'roadContinuationPrunedInstanceCounts':pruned,
        'performance':'Spatial grass HISM cells 12m; three authored geometry LODs; 125m grass and 500m tree end cull; native frame time remains unmeasured.'}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--geometry',type=Path,required=True);args=parser.parse_args()
    scene=json.loads((args.geometry/'scene.json').read_text());result=build(scene,args.geometry/'dom-mm.obj')
    target=args.geometry/'rural-context-geometry.json';target.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'output':str(target),'meshCount':len(result['meshes']),'groupCount':len(result['groups']),
        'instances':sum(len(g['instances']) for g in result['groups']),'trianglesLod0':sum(len(m['indices'])//3 for m in result['meshes']),
        'hiddenSourceIds':result['hideSourceIds'],'bytes':target.stat().st_size}))


if __name__=='__main__':main()
