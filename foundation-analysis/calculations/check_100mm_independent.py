"""Independent, bounded comparisons for a 100 mm C16/20 slab. Not a building approval.
SI plate geometry; RC section N, mm, MPa; only Python standard library.
"""
import json, math
from pathlib import Path
B=Path(__file__).resolve().parents[1]
DIMS=json.loads((B/'results/agreed-ribs-dimensions.json').read_text())
G=json.loads((B/'inputs/geometry.json').read_text())
fcd=.85*16/1.5; fyd=500/1.15; fbd=2.25*1.3/1.5
qed=1.35*(25*.1+2)+1.5*2
qser=25*.1+2+2

def navier(a,b,q,n):
    """All four edges simply supported, uncracked linear plate, uniform q kPa.
    Return only centre moments (kNm/m), elastic deflection (mm). q in kN/m2.
    These are comparison results, not full Mxy/edge/punching/contact checks.
    """
    E=28600*1000; h=.1; nu=.2; rigidity=E*h**3/(12*(1-nu**2))
    mx=my=w=load=0.
    for m in range(1,n+1,2):
        for k in range(1,n+1,2):
            qmn=16*q/(math.pi**2*m*k)
            sx=m*math.pi/a;sy=k*math.pi/b
            W=qmn/(rigidity*(sx*sx+sy*sy)**2)
            sin=math.sin(m*math.pi/2)*math.sin(k*math.pi/2)
            w+=W*sin
            mx+=rigidity*(sx*sx+nu*sy*sy)*W*sin
            my+=rigidity*(nu*sx*sx+sy*sy)*W*sin
            load+=qmn*4*a*b/(m*k*math.pi**2)
    return {'odd_mode_max':n,'Mx_kNm_m':mx,'My_kNm_m':my,'w_uncracked_mm':1000*w,'integrated_Fourier_load_kN':load,'exact_load_kN':q*a*b,'load_integral_relative_error':abs(load-q*a*b)/(q*a*b)}

r={r['id']:r for r in DIMS['routes']}
a=(r['R1']['face_coordinates_mm'][0]-r['R7']['face_coordinates_mm'][1])/1000
old=G['perimeter_axis_m']
b=old[4][1]-old[0][1]-.350
panels=[]
for name,ax,by,source in [
 ('P1_R7_R1',a,b,'Clear width R7-R1; clear length between original gray upper perimeter faces (assumed350mm). These old supports are NOT verified aligned with cast perimeter.'),
 ('P2_wing',6.65,7.973,'Hypothetical centered350mm caps on blue7m width: clear6.65m; clearR2-R4=7.973m. Ideal four-edge support is assumed, not verified.')]:
    convergence=[navier(ax,by,qed,n) for n in [21,41,81,161]]
    last,prev=convergence[-1],convergence[-2]
    assert max(abs(last[k]-prev[k])/abs(last[k]) for k in ['Mx_kNm_m','My_kNm_m'])<.005
    assert last['load_integral_relative_error']<.01
    panels.append({'id':name,'a_m':ax,'b_m':by,'geometry_note':source,'qEd_kPa':qed,'qSLS_characteristic_kPa':qser,'ULS':last,'SLS_uncracked_only':navier(ax,by,qser,161),'convergence':convergence})
# Limiting one-way rectangle check for a/b=1/10: center moment approaches q*a²/8.
limit=navier(1,10,qed,161)
assert abs(limit['Mx_kNm_m']/(qed/8)-1)<.005

capacities=[]
for bar,spacing in [(6,150),(8,150),(8,100)]:
    steel=math.pi*bar**2/4*1000/spacing
    for direction,d in [('outer_direction',100-35-bar/2),('inner_direction',100-35-1.5*bar)]:
        x=steel*fyd/(.8*1000*fcd);z=d-.4*x
        es=.0035*(d-x)/x
        capacity=steel*fyd*z/1e6
        capacities.append({'trial_mesh':f'd{bar}/{spacing}','direction':direction,'d_mm':d,'As_mm2_m':steel,'MRd_yield_block_kNm_m':capacity,'x_over_d':x/d,'steel_reaches_fyd_at_ecu3p5permille':es>=fyd/200000,'x_d_le_045_optional_rotation_screen':x/d<=.45})
# Even the most favourable investigated direction of the densest trial cannot resist P1 Mx.
maxcap=max(c['MRd_yield_block_kNm_m'] for c in capacities)
assert panels[0]['ULS']['Mx_kNm_m']>maxcap
anchors=[{'bar_mm':bar,'sigma_sd_assumed_MPa':fyd,'fbd_assumed_MPa':fbd,'basic_required_mm':bar*fyd/(4*fbd),'stress_equivalent_for150mm_all_alpha1_MPa':4*fbd*150/bar,'note':'Straight tension bar, good bond and all modifiers unity; not final lbd, lap, hook or joint design.'} for bar in [8,10,12,14,16]]
# 150mm seat and350mm rib: only pressure-vs-reaction identity; no approval of notch.
seat=[{'reaction_kN_assumed':v,'horizontal_seat_length_mm_ASSUMED':150,'width_mm_ASSUMED':350,'average_contact_MPa':v*1000/(150*350)} for v in [20,40,60,80]]
result={'status':'CONDITIONAL_COMPARISON_NOT_AS_BUILT_OR_WHOLE_BUILDING_APPROVAL','user_declared':{'slab_mm':100,'concrete':'C16/20','rib_height_including_slab_mm_interpreted_from_question':400,'rib_below_slab_mm':300,'slab_and_ribs_cast_together':True,'fill':'Site soil described as clay and sand, compacted; grading, moisture, stiffness and layer acceptance unknown.','notch_or_seat_depth_mm':150,'upper_perimeter_dimension_mm':300,'notch_orientation_and_seat_length':'NOT_CONFIRMED','reinforcement':'NOT_SPECIFIED'},'assumptions':{'cover_mm':35,'steel':'B500 (trial only)','gamma_c':1.5,'gamma_s':1.15,'alpha_cc':.85,'additional_finishes_Gk_kPa':2,'residential_Qk_kPa':2,'qEd_kPa':qed,'design_void_extent':'Not agreed;1/1.5/2m are sensitivity cases, not surveyed defects.'},'two_way_comparisons':panels,'one_way_limit_check':limit,'independent_section_capacities':capacities,'basic_straight_bar_anchorage':anchors,'conditional_150mm_seat_pressure':seat,'seat_note':'User150mm is not established as horizontal bearing or bar development length; these identities are illustrative only. Notch, shear, splitting, local compression, reinforcement continuity and construction interface are NOT verified.','sources':['https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf','inputs/geometry.json','results/agreed-ribs-dimensions.json']}
(B/'results/check-100mm-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for p in panels: print(p['id'],p['a_m'],p['b_m'],p['ULS']['Mx_kNm_m'],p['ULS']['My_kNm_m'],p['SLS_uncracked_only']['w_uncracked_mm'])
print('max trial MRd',maxcap,'basic anchor phi12',anchors[2]['basic_required_mm'])
