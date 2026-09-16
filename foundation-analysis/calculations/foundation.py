"""Conditional C16/20 foundation study. SI geometry, kN loads, MPa RC.
No soil property or support reaction generated here is a field measurement.
"""
import json, math, sys, hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'.deps'))
from shapely.geometry import Polygon, LineString, box, mapping
from shapely.ops import unary_union
G=json.loads((BASE/'inputs/geometry.json').read_text())
snap=json.loads((BASE/'inputs/model-snapshot.json').read_text())
FCD=.85*16/1.5; FYD=500/1.15
def dump(name,obj): (BASE/'results'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def buf(line,width): return LineString(line).buffer(width/2,cap_style=2,join_style=2)
perim=G['perimeter_axis_m']; ring=perim+[perim[0]]
# Structural slab ends at outer cap face, not the ETICS outline.
slab_poly=Polygon(perim).buffer(.175,join_style=2)
cap=buf(ring,.35)
old=buf(ring,.38)
routes=[]
for r in G['ribs_prior_candidates']:
 routes.append({'id':r['id'],'points':r['points_m'],'b':.35,'major':r['id'] not in ['R6','R7'],'source_ids':r['source_ids']})
routes.extend(json.loads((BASE/'inputs/supplementary-routes.json').read_text())['routes'])
# Connected support network under wall/door lines. Ground bearing routes need
# no fictitious beam end supports; geometric connectivity is not anchorage proof.
covered=unary_union([cap]+[buf(r['points'],r['b']) for r in routes])
wall_map=[]
for w in G['walls']:
 wr=box(**dict(zip(['minx','miny','maxx','maxy'],[w['rect_m'][k] for k in ['x0','y0','x1','y1']])))
 assert wr.difference(covered.buffer(.015)).area<1e-5, w['id']
 ids=[r['id'] for r in routes if buf(r['points'],r['b']).buffer(.016).intersects(wr)]
 # Wall self-weight includes finished surfaces. Unknown products conservatively 12 kN/m3.
 if w['assembly']=='SM30':raise ValueError('SM30 AK-01/AK-02: select the 300 mm brick and establish a new load basis; never reuse SA30 mass or a generic density.')
 if w['assembly']=='SA30': q=(146+54+4)*3.125*9.81/1000
 elif w['assembly']=='H200': q=(73+54+35+8)*3.125*9.81/1000
 else: q=(w['width_m']*12+.03*18)*3.125
 wall_map.append({'wall':w['id'],'routes':ids,'length_m':w['length_m'],'gk_kN_m':q,'Gk_kN':q*w['length_m'],'assembly':w['assembly'],'status':'PREDPOKLAD_PRODUCT_AND_FINISH; MODEL_LENGTH'})
assert all(box(*[w['rect_m'][k] for k in ['x0','y0','x1','y1']]).difference(covered.buffer(.016)).area<1e-5 for w in G['walls'])
for r in routes:r['length_m']=LineString(r['points']).length
terraces=unary_union([box(*[t[k] for k in ['x0','y0','x1','y1']]) for t in G['terraces'].values()]).intersection(slab_poly)
garage=unary_union([box(*[r[k]/1000 for k in ['x0','y0','x1','y1']]) for r in next(x for x in snap['rooms'] if x['number']=='1.12')['rectsMm']]).intersection(slab_poly)
# Heavy equipment has continuous soil-founded local blocks, never point loads on slab.
pads=[{'id':'P1','center':[25.410,10.123],'size':[1.2,1.2],'Pk':20,'kind':'AKU800'},
 {'id':'P2','center':[25.760,8.445],'size':[1.6,1.4],'Pk':20,'kind':'BOILER15'},
 {'id':'P3','center':[21.853,18.620],'size':[1.0,1.0],'Pk':10,'kind':'STOVE_B'},
 {'id':'P4','center':[21.290,21.785],'size':[1.2,1.2],'Pk':60,'kind':'TERRACE_W'},
 {'id':'P5','center':[27.790,20.785],'size':[.9,2.9],'Pk':60,'kind':'TERRACE_E_LONG_PIER_REACTION_UNVERIFIED'},
 {'id':'P6','center':[7.140,10.700],'size':[1.8,1.4],'Pk':60,'kind':'LOGGIA_L_PIER_TRANSFER_UNVERIFIED'}]
for p in pads:p['polygon']=box(p['center'][0]-p['size'][0]/2,p['center'][1]-p['size'][1]/2,p['center'][0]+p['size'][0]/2,p['center'][1]+p['size'][1]/2)
padpoly=unary_union([p['polygon'] for p in pads]); internal=unary_union([buf(r['points'],r['b']) for r in routes])
upper_union=unary_union([cap,internal,padpoly])
# All variants use same natural-ground support concept, same assumed reference levels.
# Old top z0; old bottom -0.60; new slab top +0.60. Footings -0.60..-0.30.
variants=[]
for name,t,bfoot,diam in [('MIN',.15,.60,12),('MEDIUM',.18,.65,14),('MAX',.20,.70,16)]:
 foot=unary_union([buf(r['points'],bfoot if r['major'] else .40) for r in routes]+[padpoly]).difference(old)
 stem=unary_union([internal,padpoly]).difference(old)
 # Divide by horizontal layers: no double counts at crossings, beam/slab or pads.
 area=slab_poly.area; slabvol=area*t+(.03*garage.area if name=='MIN' else 0)
 uppervol=upper_union.intersection(slab_poly).area*(.6-t)+upper_union.difference(slab_poly).area*.6-(.03*garage.intersection(upper_union).area if name=='MIN' else 0)
 lowervol=foot.area*.30+stem.area*.30
 lengths=sum(r['length_m'] for r in routes)+LineString(ring).length
 steelmesh=(area-garage.area)*4*(math.pi*(8 if name!='MAX' else 10)**2/4)*7850/1e6/.15
 steelmesh+=garage.area*4*(math.pi*(10 if name!='MAX' else 12)**2/4)*7850/1e6/({'MIN':.125,'MEDIUM':.10,'MAX':.15}[name])
 meshkg=steelmesh*1.15 # explicitly estimated lap/cutting factor; no BBS claim
 longkg=lengths*6*(diam**2/162)*1.15
 stirrupkg=lengths/.20*(2*(.35-.10+.60-.10)+.16)*(8**2/162)
 # Stems need vertical + transverse footing reinforcement, all accounted as schedule allowance.
 footsteel=foot.area*2/(.15)*(12**2/162)*1.15
 stemvertical=sum(r['length_m'] for r in routes)/.20*2*1.35*(10**2/162)
 padextra=sum((p['size'][0]*p['size'][1]*2/.15*(12**2/162)+2*sum(p['size'])*1.2/.2*2*(10**2/162))*1.15 for p in pads)+80
 # additional pad top mesh and two-direction face steel, distinct from slab mesh;
 # plus80kg junction/stirrup densification allowance (not final bending schedule).
 steel=meshkg+longkg+stirrupkg+footsteel+stemvertical+padextra
 variants.append({'id':name,'slab_m':t,'garage_slab_m':max(t,.18),'major_foot_width_m':bfoot,'minor_foot_width_m':.40,'foot_height_m':.30,'upper_height_including_slab_m':.60,'upper_longitudinal':f'3d{diam} top + 3d{diam} bottom','stirrups':'d8/200; d8/100 within 600 mm of junctions (extra quantity allowance)','concrete_m3':slabvol+uppervol+lowervol,'slab_m3':slabvol,'upper_below_slab_m3':uppervol,'new_lower_m3':lowervol,'steel_kg_estimate':steel,'steel_components_kg':{'slab_including_15pct_laps':meshkg,'longitudinal_including_15pct_laps':longkg,'stirrups_base':stirrupkg,'footing_mesh':footsteel,'stem_dowels':stemvertical,'local_and_dense_stirrups_allowance':padextra},'formwork_m2':LineString(ring).length*1.2+sum(r['length_m'] for r in routes)*1.2+padpoly.length*.6,'trench_excavation_m3':foot.buffer(.15,join_style=2).area*.60,'fill_geometric_m3':slab_poly.difference(upper_union).area*(.60-t)-(.03*garage.difference(upper_union).area if name=='MIN' else 0),'stripping_allowance_m3':area*.20,'note':'z levels/fill/excavation assumed; reuse external formwork; strip organic layer 0.20 m scenario not survey; disposal loose volume factor not assumed'})
# Representative perimeter line; not a substitute for absent actual roof reactions.
# Load width4.10m from half nominal west roof span8.20m. Full upper walls included.
loads=[]
for attic in [2.,7.5]:
 Gk=4.1*(1.40+.75)+(.30*12+.03*18)*3.125+.3*.25*25+.38*.6*25+.35*.6*25
 Qk=4.1*attic; snow=4.1*.8 # bound mu.8*sk1.0 original zone; no drift reduction
 Nd=1.35*Gk+1.5*(Qk+snow) # simultaneous full variables conservative vs psi reduction
 Ns=Gk+Qk+snow
 for B in [.38,.40]:
  for e in [0,.025,.05]:
   bp=B-2*e
   loads.append({'attic_q_kPa':attic,'B_m':B,'e_m':e,'Gk_kN_m':Gk,'Qk_kN_m':Qk,'snow_kN_m':snow,'NEd_kN_m':Nd,'NSLS_kN_m':Ns,'effective_width_m':bp,'qEd_kPa':Nd/bp,'qSLS_max_kPa':Ns/B*(1+6*e/B),'B_required_at_150kPa_m':Nd/150+2*e,'status_at_reference_150kPa':'PASS_ENVELOPE_ONLY' if Nd/bp<=150 else 'FAIL'})
# Independent service settlement bound: 2:1 spreading infinite strip, homogeneous
# constrained modulus; excludes creep/collapse/swelling, groundwater changes.
settlement=[]
for qcase in [2.,7.5]:
 L=next(l for l in loads if l['attic_q_kPa']==qcase and l['B_m']==.38 and l['e_m']==0)
 for E in [3000,8500,15000]:
  H=2.; s=L['NSLS_kN_m']*math.log((.38+H)/.38)/E*1000
  surcharge=20*.6*H/E*1000
  settlement.append({'attic_q_kPa':qcase,'Eoed_kPa':E,'compressible_depth_m':H,'settlement_mm':s,'additional_broad_fill_0p6m_surcharge_bound_mm':surcharge,'total_with_surcharge_bound_mm':s+surcharge,'absolute_limit_mm_assumed':25,'differential_half_modulus_mm':s,'differential_limit_over_4m_mm_assumed':8,'status':'PARAMETRIC_ONLY_NO_SITE_PASS'})
# Upper cap beam over local 1m/2m ground void, bending + stirrup shear;
# no credit for old unreinforced concrete in longitudinal bending.
beam=[]
for v in variants:
 dia={'MIN':12,'MEDIUM':14,'MAX':16}[v['id']]; d=600-50-8-dia/2; As=3*math.pi*dia**2/4
 x=As*FYD/(.8*350*FCD); z=d-.4*x; mr=As*FYD*z/1e6
 rho=As/(350*d); k=min(2,1+math.sqrt(200/d)); vr=max(.12*k*(100*rho*16)**(1/3),.035*k**1.5*math.sqrt(16))*350*d/1000
 vs=(2*math.pi*8**2/4)/200*.9*d*FYD/1000
 for span in [1.,2.]:
  q=next(l['NEd_kN_m'] for l in loads if l['attic_q_kPa']==7.5)
  Eeff=28600/3.5; n=200000/Eeff
  xc=(-n*As+math.sqrt((n*As)**2+2*350*n*As*d))/350
  Icr=350*xc**3/3+n*As*(d-xc)**2
  qs=next(l['NSLS_kN_m'] for l in loads if l['attic_q_kPa']==7.5)
  defl=5*qs*(span*1000)**4/(384*Eeff*Icr)
  Ms=qs*span**2/8*1e6; sig=Ms*n*(d-xc)/Icr
  hc=min(2.5*(600-d),(600-xc)/3,300); rho_eff=As/(350*hc)
  sr=3.4*58+.8*.5*.425*dia/rho_eff
  strain=max((sig-.4*1.9/rho_eff*(1+200000/28600*rho_eff))/200000,.6*sig/200000)
  vrdmax=350*.9*d*.6*(1-16/250)*FCD/2/1000
  beam.append({'variant':v['id'],'span_m':span,'qEd_kN_m':q,'MEd_kNm':q*span**2/8,'MRd_kNm':mr,'M_util':q*span**2/8/mr,'VEd_kN':q*span/2,'VRdc_kN':vr,'VRds_kN_cot1':vs,'VRdmax_kN':vrdmax,'deflection_fully_cracked_phi2_5_mm':defl,'deflection_limit_mm':span*1000/250,'wk_characteristic_mm':sr*strain,'wk_limit_mm':.3,'note':'SLS conservative whole characteristic load long-term; transient void robustness, not full-span R1; single tension layer stiffness ignores compression steel conservatively'})
# New footing transverse cantilever: bounding uniform200kPa under widest .65
footcheck=[]
for v in variants:
 B=v['major_foot_width_m']; a=(B-.35)/2; d=300-50-6; As=math.pi*12**2/4/.15
 x=As*FYD/(.8*1000*FCD); mr=As*FYD*(d-.4*x)/1e6
 footcheck.append({'variant':v['id'],'a_m':a,'qEd_assumed_kPa':200,'MEd_kNm_m':200*a*a/2,'MRd_kNm_m':mr,'VEd_kN_m':200*max(0,a-d/1000),'As_mm2_m':As,'As_min_mm2_m':max(.26*1.9/500,.0013)*1000*d})
padchecks=[]
for p in pads:
 A=p['size'][0]*p['size'][1]; Gpad=25*A*1.2
 Nd=1.5*p['Pk']+1.35*Gpad
 # Screening on a COMPLETE perimeter at radius d (inside all pad edges),
 # not an invented truncation of the 2d perimeter. Neglect soil relief.
 # This is a force/shear-demand screen, NOT completed EC2 footing punching proof.
 d=.294; u=4*.2+2*math.pi*d; ved=1.15*Nd/(u*d)*.001
 rho=(math.pi*12**2/4/.15)/(1000*d*1000); kval=min(2,1+math.sqrt(.2/d))
 vrd=max(.12*kval*(100*rho*16)**(1/3),.035*kval**1.5*4)
 padchecks.append({'id':p['id'],'design_load_envelope_kN':p['Pk'],'NEd_including_block_kN':Nd,'qEd_kPa':Nd/A,'base_zone_height_m':.35,'screening_perimeter_at_d_m':u,'vEd_MPa':ved,'vRdc_MPa':vrd,'screen_pass':ved<=vrd,'status':'SCREEN_ONLY_NOT_PUNCHING_APPROVAL','note':'350mm base zone within solid1200mm block; closed control line d from200mm assumed load patch, beta1.15 assumed, soil relief ignored; complete footing punching incl eccentricity pending; old/new pad overlap not proven composite'})
# Interface: explicitly use no cohesion/anchor tension capacity until tested.
interface=[]
for h in [.45,.6]:
 Hk=.5*(1-math.sin(math.radians(30)))*20*h*h+10*(1-math.sin(math.radians(30)))*h
 Hd=1.5*Hk
 Gcap=25*.35*.6
 interface.append({'fill_height_m':h,'Hk_kN_m':Hk,'HEd_kN_m':Hd,'friction_design_only_selfweight_kN_m':.5*.9*Gcap,'required_tie_kN_m_before_floors':max(0,Hd-.5*.9*Gcap),'note':'at rest K0=.5, construction surcharge10kPa; formwork/temporary bracing must resist; no passive soil credited'})
routechecks=[]
for v in variants:
 for r in routes:
  B=v['major_foot_width_m'] if r['major'] else .4
  wallg=max([w['gk_kN_m'] for w in wall_map if r['id'] in w['routes']]+[12.94 if r['id'] in ['R4','R5'] else 0])
  trib=3.5 if r['major'] else 0
  g=wallg+trib*(1.4+.75)+25*(B*.3+r['b']*.9)
  N=1.35*g+1.5*trib*(7.5+.8)
  routechecks.append({'variant':v['id'],'route':r['id'],'tributary_width_m_assumed':trib,'gwall_kN_m_envelope':wallg,'Gk_kN_m':g,'NEd_kN_m':N,'B_m':B,'qEd_kPa':N/B,'qRd_reference_kPa':150,'util':N/B/150,'note':'centered load envelope only; actual roof support reactions absent'})
loadextras={'status':'SENSITIVITY_NOT_SITE_ACTION_DEFINITION','wind':[{'net_pressure_kPa_assumed':w,'horizontal_force_kN':w*21.6*5.56,'overturning_kNm_about_base_assuming_uniform_height':w*21.6*5.56*5.56/2,'roof_net_design_uplift_kN_1p5W_minus0p9G':(1.5*w-.9*1.4)*G['area_m2']} for w in [.8,1.5]],'snow_drift_sensitivity':{'roof_snow_kPa':1.6,'extra_perimeter_NE_d_kN_m':1.5*(1.6-.8)*4.1,'note':'Illustrative doubled snow, not normative drift envelope; roof geometry-specific drift missing'},'pv':{'module_count':6,'localized_dead_load_kN_assumed':3.0,'NEd_kN':4.05,'note':'separate localized load on WING_INNER; actual assembly mass and wind fixing absent'},'groundwater':[{'head_above_slab_underside_m':h,'uplift_kPa':9.81*h,'design_uplift_kPa_1p5':1.5*9.81*h,'MED_restraining_dead_kPa_0p9':.9*(25*.18+2),'note':'hydrostatic sensitivity, not measured water level; draining is not credited'} for h in [0,.3,.6]],'point_reaction_on_old_strip':[{'point_NE_d_kN':P,'assumed_spread_length_m':L,'additional_contact_kPa_at_Beff0p33m':P/(.33*L),'note':'additional to line-load background; transfer length not verified'} for P in [30,60,100] for L in [.5,1.,2.]],'fill_settlement':[{'fill_thickness_m':.42,'Eoed_fill_MPa_assumed':E,'load_kPa':8.5,'settlement_mm':8.5*.42/(E*1000)*1000,'note':'1D homogeneous layer sensitivity only, not Proctor or Ev2 conversion'} for E in [10,20,50]]}
dump('load-envelope.json',loadextras)
out={'status':'CONDITIONAL_STUDY_NOT_FOR_CONSTRUCTION','concrete':'C16/20','input_sha256':hashlib.sha256((BASE/'inputs/geometry.json').read_bytes()).hexdigest(),'slab_structural_area_m2':slab_poly.area,'architectural_area_m2':G['area_m2'],'garage_area_m2':garage.area,'external_terraces_structural_area_m2':terraces.area,'perimeter_length_m':LineString(ring).length,'internal_routes_length_m':sum(r['length_m'] for r in routes),'routes':routes,'wall_loads':wall_map,'pads':[{k:(mapping(v) if k=='polygon' else v) for k,v in p.items()} for p in pads],'variants':variants,'perimeter_load_envelopes':loads,'new_route_checks':routechecks,'settlement_sensitivity':settlement,'cap_robustness':beam,'footing_checks':footcheck,'pad_checks':padchecks,'construction_interface':interface,'geometry':{'slab':mapping(slab_poly),'old':mapping(old),'cap':mapping(cap),'internal':mapping(internal),'garage':mapping(garage),'terraces':mapping(terraces)},'limits':{'soil_Rd_reference_kPa':150,'settlement_limit_mm_project_assumption':25,'relative_rotation_limit_project_assumption':'1/500','wk_mm':.3,'final_design_release':False}}
dump('foundation-results.json',out)
print('Foundation calculation:',len(routes),'routes; slab area',round(slab_poly.area,3),'m2')
for v in variants:print(v['id'],round(v['concrete_m3'],2),'m3',round(v['steel_kg_estimate']),'kg (allowance)')
print('Perimeter qEd high-storage,380mm,e25mm:',next(round(x['qEd_kPa'],1) for x in loads if x['attic_q_kPa']==7.5 and x['B_m']==.38 and x['e_m']==.025),'kPa')
