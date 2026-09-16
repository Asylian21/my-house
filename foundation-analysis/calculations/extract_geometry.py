"""Extract current C/B/B coordination geometry; never an as-built survey."""
import json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
snapshot=ROOT/'output/pdf/construction-cbb/model-snapshot.json'
s=json.loads(snapshot.read_text())
def pts(p): return [[v/1000 for v in row] for row in p]
def rect(r): return {k:v/1000 for k,v in r.items()}
def centerline(r):
 if r['x1']-r['x0']>=r['y1']-r['y0']:
  return [[r['x0']/1000,(r['y0']+r['y1'])/2000],[r['x1']/1000,(r['y0']+r['y1'])/2000]]
 return [[(r['x0']+r['x1'])/2000,r['y0']/1000],[(r['x0']+r['x1'])/2000,r['y1']/1000]]
fi=s['foundationIllustration']
g={'schema':'foundation-analysis.geometry.v1','units':'m, kN unless named otherwise','status':'OVERENE_MODEL_NOT_AS_BUILT','design':'C/B/B','coordinate_frame':'Repository local X east, Y garden; street at minimum Y. NOT surveyed axes. Drawing origin may subtract [6.440,3.000].','source':'output/pdf/construction-cbb/model-snapshot.json','source_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'source_date':s['provenance']['date'],'field_survey':None,'existing_state':{'status':'DEKLAROVANE','source':'Current investor task and follow-up 2026-09-15','bottom_perimeter_strips_cast':True,'upper_formwork_cast':False,'slab_cast':False,'concrete':'C16/20','bottom_strip_width_m':[0.38,0.40],'cast_height_m':0.60,'founding_depth_below_finished_ground_m':None,'as_built_outline':None,'existing_reinforcement':None,'upper_formwork_35cm_meaning':None},'superseded_statement':'Prior foundation illustration said slab cast including terraces. Current investor clarification explicitly replaces that state; outline remains model only.','outline_m':pts(fi['castOutline']),'closed_envelope_m':pts(fi['closedOutline']),'perimeter_axis_m':pts(fi['perimeterAxis']),'proposed_axis_warning':'Prior coordination proposal from nominal 300mm wall cores. Must be tied to actual strip centerlines by survey; terrace ends are proposal, not facade loading.','area_m2':s['roof']['projectedAreaMm2']/1e6,'upper_wall_nominal_height_m':3.125,'ribs_prior_candidates':[],'walls':[],'facades':[],'heavy_items':[],'roof':{},'source_hash_checks':{}}
for p,h in s['provenance']['files'].items():
 if (ROOT/p).exists():g['source_hash_checks'][p]={'snapshot_sha256':h,'current_sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'matches':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h}
for r in fi['ribs']:
 rr={'id':r['id'],'points_m':pts(r['points']),'length_m':sum(math.dist(a,b)/1000 for a,b in zip(r['points'],r['points'][1:])),'source_ids':r['sourceIds'],'status':'PREDPOKLAD_ROUTE_NOT_DESIGNED','note':r['note']}
 if 'loadedIntervalsMm' in r:rr['loaded_intervals_m']=[{'code':q['code'],'from':q['from']/1000,'to':q['to']/1000} for q in r['loadedIntervalsMm']]
 g['ribs_prior_candidates'].append(rr)
for w in s['walls']:
 r=w['rectMm'];line=centerline(r)
 spec=next((a for a in s['acousticWalls'] if a['wallId']==w['id']),None)
 assembly=spec['assembly']['code'] if spec else 'MASONRY_PRODUCT_UNCONFIRMED'
 a={'id':w['id'],'model_role':w['role'],'rect_m':rect(r),'line_m':line,'length_m':math.dist(*line),'width_m':min(r['x1']-r['x0'],r['y1']-r['y0'])/1000,'height_m':3.125,'height_status':'PREDPOKLAD_NOMINAL_MODEL_ENVELOPE','assembly':assembly,'source':'lib/floor-plan-concept.ts + snapshot walls','weight_status':'CHYBA_FINAL_PRODUCT_AND_SURFACES'}
 if assembly=='SM30':a.update({'masonry_kg_m2':None,'masonry_thickness_m':.3,'wool_thickness_m':0,'leaf_axes_x_m':[(r['x0']+r['x1'])/2000],'weight_status':'CHYBA_SELECTED_300_MM_BRICK_AND_SURFACES','revision':'CLIENT-SM30-20260916'})
 if assembly=='SA30':a.update({'masonry_kg_m2':146,'finish_layers':[{'thickness_m':.015,'density_kg_m3':1800,'status':'PREDPOKLAD'}]*2,'wool_thickness_m':.1,'wool_density_kg_m3':None,'leaf_axes_x_m':[14.993,15.193],'finish_source':'docs/active-design.md updated 2026-09-15: 15mm VC plaster each room face; snapshot missing finishes superseded'})
 if assembly=='H200':a.update({'masonry_kg_m2':73,'finish_layers':[{'thickness_m':.015,'density_kg_m3':1800,'status':'PREDPOKLAD'}]*2,'silentboard_kg_m2':35,'silentboard_status':'PREDPOKLAD_TWO_LAYERS_17.5_EACH_VERIFY_DELIVERY','lining_misc_kg_m2':None})
 g['walls'].append(a)
for f in s['facades']:
 d=f['def']; ff={'id':d['id'],'name':d['name'],'axis':d['axis'],'outer_m':d['outer']/1000,'inner_m':d['inner']/1000,'from_m':d['from']/1000,'to_m':d['to']/1000,'outward':d['outward'],'segments':[]}
 for seg in f['segments']:
  a={'from_m':seg['a']/1000,'to_m':seg['b']/1000,'kind':seg['kind']}
  if 'item' in seg:
   a['opening_id']=seg['item']['id']; a['opening']=seg['item'].get('opening')
  ff['segments'].append(a)
 g['facades'].append(ff)
h=s['heating']; living=s['living'];
g['heavy_items']=[{'id':'AKU800','center_m':{k:v/1000 for k,v in h['accumulator']['centerMm'].items()},'outer_diameter_m':h['accumulator']['outerDiameterMm']/1000,'water_l':800,'water_weight_kN':7.848,'dry_weight_kN':None,'feet_contact_area':None,'source':'lib/technical-design.ts HEATING_LAYOUTS.B','status':'MODEL_LOCATION_AND_CAPACITY; CHYBA_TOTAL_WEIGHT_AND_FEET'}, {'id':'BOILER15','rect_m':rect(h['boiler']['assemblyFootprintMm']),'body_rect_m':rect(h['boiler']['body']['footprintMm']),'pellet_hopper_kg':180,'dry_weight_kN':None,'operating_water_kN':None,'feet_contact_area':None,'source':'lib/technical-design.ts HEATING_LAYOUTS.B','status':'CHYBA_OPERATING_MASS_AND_CONTACT'}, {'id':'STOVE_B','center_m':[21.853,18.620],'rect_m':{'x0':21.598,'y0':18.365,'x1':22.108,'y1':18.875},'total_weight_kN':None,'flue_weight_kN':None,'source':'lib/twin-living-layouts.ts FIREPLACE_STOVE_B','status':'MODEL_LOCATION; CHYBA_LOAD'}, {'id':'PELLET_BAGS','rect_m':rect(h['storage']['footprintMm']),'mass_kg':45,'source':'lib/technical-design.ts HEATING_LAYOUTS.B','status':'MODEL_ALLOWANCE'}, {'id':'KITCHEN_ISLAND','rect_m':{'x0':23.381,'y0':12.880,'x1':26.021,'y1':13.800},'geometry_source':'lib/twin-interior.ts KITCHEN_ISLAND derived from unchanged core geometry source','total_weight_kN':None,'status':'CHYBA_ACTUAL_FINISHES_STORAGE_FEET'}]
g['terraces']={k:rect(v) for k,v in fi['terraces'].items()}
g['porch_supports_model']=[{**{k:v for k,v in q.items() if not k.endswith('mm')},'rect_m':{'x0':q['startXmm']/1000,'x1':q['endXmm']/1000,'y0':q['startYmm']/1000,'y1':q['endYmm']/1000},'status':'MODEL_SUPERSTRUCTURE_ENVELOPE_NOT_PAD_FOOTPRINT'} for q in s['house']['porches']['wingEnd']['portalFrame']['supportsMm']]
g['loggia_corner_support_model']={'rectangles_m':[{'x0':6.440,'y0':10.700,'x1':7.840,'y1':11.200},{'x0':6.440,'y0':10.200,'x1':6.940,'y1':10.700}],'union_area_m2':.95,'geometric_centroid_m':[7.021578947368422,10.81842105263158],'roof_reaction_point_m':None,'status':'MODEL_L_SHAPED_PIER_NOT_FOUNDATION_OR_REACTION','source':'lib/twin-active-house.ts / HOUSE.porches.gardenLoggia.cornerPier'}
g['roof']={'status':'MODEL_GEOMETRY_NOT_COMPLETED_STRUCTURAL_DESIGN','projected_area_m2':s['roof']['projectedAreaMm2']/1e6,'surface_area_m2':s['roof']['surfaceAreaMm2']/1e6,'ridge_height_m':5.56,'eaves_height_m':3.125,'ridge_axes_m':{'main_y':7.1,'wing_x':24.54},'wood_ceiling_storage_attic':True,'attic_live_load_kPa':None,'actual_support_reactions':None,'original_structural_system':'rafters 120x200 max 930; purlin 2xU240 carried by HEA160 steel frames at max 7.7m; conventional portion ridge purlin on posts to ceiling beams above bearing walls; current support mapping not finalized','original_source':'D2 statics PDF p4; D1.1.003 p1'}
g['grid']={'x':[{'id':a['label'],'at_m':a['at']/1000} for a in s['gridX']],'y':[{'id':a['label'],'at_m':a['at']/1000} for a in s['gridY']]}
(ROOT/'foundation-analysis/inputs/geometry.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n')
print('Extracted',len(g['walls']),'walls',len(g['ribs_prior_candidates']),'candidate ribs',g['area_m2'],'m2. All geometry is model, not survey.')
