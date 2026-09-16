"""Build supplementary soil-founded support routes, preserving R1-R7 and every wall.

Axes are DESIGN PROPOSALS in the unchanged C/B/B model frame, not field survey.
Joining concrete geometry does not establish a suspended-beam load path or bar
anchorage. Door gaps are bridged only below floor level; no walls are added.
"""
import json,math,sys,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'.deps'))
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
G=json.loads((BASE/'inputs/geometry.json').read_text())
def buffer(r):return LineString(r['points']).buffer(r['b']/2,cap_style=2,join_style=2)
def route(id,points,b,ids,note):
 return {'id':id,'points':points,'b':b,'major':False,'source_ids':ids,'length_m':LineString(points).length,'status':'PREDPOKLAD_SOIL_FOUNDED_ROUTE','note':note,'support':'New continuous footing on verified natural bearing stratum; no suspended span between route ends implied','node_anchorage_min_m':1.0}
R=[]
R.append(route('R8',[[22.711,5.1075],[22.711,11.550]],.35,
 ['IW-ENTRY-TOP-E2','IW-SPINE-EAST-1','IW-SPINE-EAST-2','IW-SPINE-EAST-3','C-OFFICE-NORTH-JAMB','C-WC-DOOR-JAMB','C-ENTRY-HALL-JAMB'],
 'One east corridor support below existing office, bathroom and WC door gaps. Axis shift of widest upper jamb is 29.5 mm; width350 mm contains all modeled jamb faces. Top extends87.5mm beyond wall end to lower face ofR3 for full-height connection geometry; bottom remains a soil-supported end.'))
R.append(route('R9',[[13.413,6.492],[27.691,6.492]],.35,
 ['C-BATH-HALL-W','C-BATH-HALL-E','B-STREET-KID-TOP','C-KID-HALL-POCKET-WALL','C-ENTRY-HALL-JAMB','IW-STUDY-NORTH'],
 'Merge centerlinesY6.482/Y6.502, difference20 mm, into proposedY6.492. Width350 contains 140mm partitions and200mmH200. Continuity only under existing doorways and intersecting wall nodes. H200 remains nonbearing for roof/attic.'))
R.append(route('R10',[[24.7515,7.671],[24.7515,10.862]],.30,
 ['IW-BATH-105-EAST','IW-WC-EAST'],
 'Continuous collinear service-core partition support; joins R11/R12 and R2 below floor.'))
R.append(route('R11',[[24.682,7.671],[27.691,7.671]],.30,
 ['IW-BATH-105-SOUTH-E'],
 'Extend ends within wall-node widths to R10 and east perimeter cap.'))
R.append(route('R12',[[22.711,8.842],[24.7515,8.842]],.30,
 ['IW-BATH-105-NORTH'],
 'Connect west end to R8 and east end to R10; wall end overhangs are contained by crossing strips.'))
R.append(route('R13',[[10.993,7.721],[20.6915,7.721],[20.6915,7.791],[21.543,7.791]],.35,
 ['C-CLOSET-NORTH-W','C-CLOSET-NORTH-E','C-BED-PRIVACY-W','C-BED-PRIVACY-E','B-GARDEN-KID-SOUTH-W','B-GARDEN-KID-SOUTH-E','C-GARDEN-CLOSET-SOUTH'],
 'One north hall support below three existing doorways. At R1, last851.5mm moves70mm to center the adjoining140+140mm wall rectangles within350mm. This terminal widened junction is an explicit local support design, not a claim these two wall axes are collinear within50mm; longitudinal bars should run through union envelope with engineered detail, not copy a70mm abrupt bar kink.'))
R.append(route('R14',[[12.912,3.354],[12.912,5.674]],.30,
 ['C-GARAGE-BAY-EAST'],
 'Join south perimeter to transverse R15; existing partition unchanged.'))
R.append(route('R15',[[10.842,5.674],[13.413,5.674]],.35,
 ['C-GARAGE-BAY-RETURN','C-BATH-NORTH-W'],
 'Merge exactly collinear return and bathroom wall. Intersects R14,R16,R17. Initial151mm past R16 is only cover of actual wall extent.'))
R.append(route('R16',[[10.993,5.604],[10.993,8.897]],.35,
 ['C-GARAGE-SPINE-S','C-GARAGE-SPINE-N'],
 'Complete garage spine from R15 to existing R5/R6 node. Centerline rounding0.5mm from wall center. Ends atR5 so does not duplicate existingR6 length.'))
R.append(route('R17',[[13.413,5.604],[13.413,7.721]],.30,
 ['C-CLOSET-EAST'],
 'Connect closet east partition to R15,R9,R13;70mm initial length contains wall corner above crossing centerline.'))
prior=[{'id':r['id'],'points':r['points_m'],'b':.35,'major':r['id'] not in ['R6','R7'],'source_ids':r['source_ids']} for r in G['ribs_prior_candidates']]
cap={'id':'OB','points':G['perimeter_axis_m']+[G['perimeter_axis_m'][0]],'b':.35}
all_routes=[cap]+prior+R
union=unary_union([buffer(r) for r in all_routes])
checks=[]
for w in G['walls']:
 wr=box(*[w['rect_m'][k] for k in ['x0','y0','x1','y1']])
 missing=wr.difference(union).area
 owners=[r['id'] for r in all_routes if buffer(r).intersection(wr).area>1e-8]
 checks.append({'wall':w['id'],'area_m2':wr.area,'uncovered_area_m2':missing,'route_ids':owners,'all_model_faces_covered':missing<1e-9})
 assert missing<1e-9,(w['id'],missing)
# Geometrical connectivity checks; not a structural support or anchorage check.
adj={r['id']:[] for r in all_routes};nodes=[]
for i,a in enumerate(all_routes):
 for b in all_routes[i+1:]:
  if buffer(a).intersects(buffer(b)):
   adj[a['id']].append(b['id']);adj[b['id']].append(a['id'])
   nodes.append({'members':[a['id'],b['id']],'overlap_area_m2':buffer(a).intersection(buffer(b)).area,'status':'GEOMETRIC_INTERSECTION_ONLY','required_anchorage_m':1.0,'detail_note':'Develop each relevant bar for at least1.0m in actual receiving concrete along feasible L/U/continuous bar arrangement, while satisfying calculated lbd and bend/cover limits. No artificial1m leg outside concrete. Short terminal stubs require return/continuation into longer crossing run; otherwise connection remains unverified.'})
seen={'OB'};todo=['OB']
while todo:
 for x in adj[todo.pop()]:
  if x not in seen:seen.add(x);todo.append(x)
assert len(seen)==len(all_routes),set(adj)-seen
# Reference literal old fragmentation algorithm, for transparent length/union comparison.
old=list(prior);cov=unary_union([buffer(cap)]+[buffer(r) for r in old])
for w in G['walls']:
 wr=box(*[w['rect_m'][k] for k in ['x0','y0','x1','y1']])
 if wr.difference(cov.buffer(.015)).area>1e-5:
  q={'id':f'OLD{len(old)+1}','points':w['line_m'],'b':max(.30,w['width_m']+.04)}
  old.append(q);cov=unary_union([cov,buffer(q)])
old_length=sum(LineString(r['points']).length for r in old)
new_length=sum(LineString(r['points']).length for r in prior+R)
old_internal=unary_union([buffer(r) for r in old]);new_internal=unary_union([buffer(r) for r in prior+R])
out={'schema':'foundation-analysis.supplementary-routes.v1','status':'CONDITIONAL_GEOMETRIC_SUPPORT_PROPOSAL_NOT_FOR_CONSTRUCTION','units':'m','geometry_sha256':hashlib.sha256((BASE/'inputs/geometry.json').read_bytes()).hexdigest(),'preserved_ids':[r['id'] for r in prior],'routes':R,'wall_coverage':checks,'geometric_junctions':nodes,'geometric_connectivity':{'connected_to_perimeter':sorted(seen),'all_connected':len(seen)==len(all_routes)},'comparison':{'old_total_route_count':len(old),'new_total_route_count':len(prior)+len(R),'old_internal_centerline_length_m':old_length,'new_internal_centerline_length_m':new_length,'length_change_m':new_length-old_length,'old_internal_union_area_m2':old_internal.area,'new_internal_union_area_m2':new_internal.area,'union_area_change_m2':new_internal.area-old_internal.area},'construction_constraints':['No wall position, role or opening is changed.','All support concrete remains below floor; no sill or wall is inserted through a doorway.','New footings bear continuously on verified natural bearing stratum. Geometric connection never proves end-supported beam behavior.','No credit for masonry arches or old/new concrete monolithicity.','Existing R1-R7 coordinates and IDs remain exactly unchanged.','Min1m actual bar development/continuity at nodes is a detailing requirement, not verified by polygon overlap. Calculated lbd, barshape, cover and room for anchorage govern if more demanding.','Terminal70mm jog at R1/R13 is a local widened junction; do not fabricate an abrupt70mm kink in main bars.','Quantities must be recalculated from unions of all actual width layers; centerline count reduction does not itself prove cost reduction.']}
(BASE/'inputs/supplementary-routes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out['comparison'],indent=2));print('Coverage:',sum(q['all_model_faces_covered'] for q in checks),'of',len(checks),'walls; connected:',len(seen),'members incl perimeter')
