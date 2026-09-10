"""Independent float64 reference extracted from reviewed CPU source; no source writer or engine dependency."""
import math

dot = lambda a, b: sum(x*y for x,y in zip(a,b))
sub = lambda a, b: tuple(x-y for x,y in zip(a,b))
add = lambda a, b: tuple(x+y for x,y in zip(a,b))
mul = lambda a, s: tuple(x*s for x in a)
cross = lambda a,b: (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def unit(a): return mul(a, 1/math.sqrt(dot(a,a)))


class BVH:
    def __init__(self,triangles):
        self.triangles=triangles;self.nodes=[];self.ray_count=self.triangle_tests=0
        def build(ids):
            low=[min(triangles[t]['low'][i] for t in ids) for i in range(3)]
            high=[max(triangles[t]['high'][i] for t in ids) for i in range(3)]
            idx=len(self.nodes);node={'low':low,'high':high};self.nodes.append(node)
            if len(ids)<=8: node['triangles']=ids
            else:
                axis=max(range(3),key=lambda i:high[i]-low[i]);ids=sorted(ids,key=lambda t:triangles[t]['low'][axis]+triangles[t]['high'][axis]);mid=len(ids)//2
                node['children']=[build(ids[:mid]),build(ids[mid:])]
            return idx
        build(list(range(len(triangles))))

    @staticmethod
    def box(origin,direction,node,limit):
        lo,hi=0.,limit
        for i in range(3):
            if abs(direction[i])<1e-15:
                if not node['low'][i]-1e-8<=origin[i]<=node['high'][i]+1e-8: return False
            else:
                a=(node['low'][i]-origin[i])/direction[i];b=(node['high'][i]-origin[i])/direction[i]
                lo=max(lo,min(a,b)-1e-8);hi=min(hi,max(a,b)+1e-8)
                if lo>hi:return False
        return True

    def first(self,origin,direction):
        self.ray_count+=1;limit=math.inf;hit=None;stack=[0]
        while stack:
            node=self.nodes[stack.pop()]
            if not self.box(origin,direction,node,limit):continue
            if 'children' in node:stack.extend(node['children']);continue
            for id_ in node['triangles']:
                self.triangle_tests+=1;t=self.triangles[id_]
                p=cross(direction,t['e2']);det=dot(t['e1'],p)
                if abs(det)<1e-12:continue
                inv=1/det;delta=sub(origin,t['a']);u=dot(delta,p)*inv
                if u < -1e-9 or u > 1+1e-9:continue
                q=cross(delta,t['e1']);v=dot(direction,q)*inv
                if v < -1e-9 or u+v > 1+1e-9:continue
                distance=dot(t['e2'],q)*inv
                if 1e-7 < distance < limit:limit=distance;hit=(id_,u,v)
        return (hit,limit) if hit else (None,math.inf)


def refract(i,n,ior=1.333):
    ci=-dot(i,n);eta=1/ior;st2=eta*eta*(1-ci*ci)
    assert ci>0 and 0<=st2<1
    ct=math.sqrt(1-st2);t=add(mul(i,eta),mul(n,eta*ci-ct))
    f=.5*(((ci-ior*ct)/(ci+ior*ct))**2+((ct-ior*ci)/(ct+ior*ci))**2)
    return t,f


def normal(x,y,seconds,waves,scale=1):
    gx=gy=0
    for w in waves:
        dx,dy=w['direction'];length=w['wavelengthMetres'];frequency=math.sqrt(9.81/(2*math.pi*length))
        phase=(dx*x+dy*y)/length-frequency*seconds+w['phaseCycles']
        slope=scale*2*math.pi*w['amplitudeMetres']/length*math.cos(2*math.pi*phase)
        gx+=dx*slope;gy+=dy*slope
    return unit((-gx,-gy,1))

