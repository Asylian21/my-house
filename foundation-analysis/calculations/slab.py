#!/usr/bin/env python3
"""Local ground-supported slab checks. Python 3 standard library only.
Run: python3 foundation-analysis/calculations/slab.py
Output is conditional section verification, NOT approval of a complete foundation.
Units internally N, mm, MPa; explicitly converted output kN/m, kNm/m, mm.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FCK, FCTM, FCTK, ECM, ES = 16., 1.9, 1.3, 28600., 200000.
GAMMA_C, GAMMA_S, ALPHA_CC = 1.5, 1.15, .85
FCD, FYD = ALPHA_CC*FCK/GAMMA_C, 500/GAMMA_S
COVER, AGGREGATE, RHO_STEEL = 35., 16., 7850.
CONFIGS = {
 'REF100': (100,8,150), 'REF150': (150,8,150), 'REF200': (200,8,150),
 'REJECT_GARAGE150': (150,10,125),
 'MIN_RESIDENTIAL': (150,8,150), 'MIN_GARAGE': (180,10,125),
 'MEDIUM_RESIDENTIAL': (180,8,150), 'MEDIUM_GARAGE': (180,10,100),
 'MAX_RESIDENTIAL': (200,10,150), 'MAX_GARAGE': (200,12,150),
}
SOURCES = {
 'EC2_primary_training': 'https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf',
 'JRC_crack_example': 'https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/Bridge_Design-Eurocodes-Worked_examples.pdf',
 'industry_EC2_worked_examples': 'https://www.concretecentre.com/TCC/media/TCCMediaLibrary/Events/Online%20course/CCIP_Worked_Examples_EC2.pdf',
 'industry_punching_reference': 'https://www.concretecentre.com/TCC/media/TCCMediaLibrary/Events/Online%20course/CCIP_EC2_Bridges.pdf',
}

def section(h, bar, spacing):
    # Two directions at each face; use less favourable inner layer in both.
    d = h-COVER-1.5*bar
    steel = math.pi*bar**2/4*1000/spacing
    a = steel*FYD/(1000*FCD)  # rectangular stress block depth a=0.8*x
    x = a/.8
    mr = steel*FYD*(d-a/2)/1e6
    rho = min(steel/(1000*d), .02)
    k = min(1+math.sqrt(200/d),2)
    v = max(.18/GAMMA_C*k*(100*rho*FCK)**(1/3), .035*k**1.5*math.sqrt(FCK))
    gap = h-2*COVER-4*bar
    clear_min=max(bar,20,AGGREGATE+5)
    amin = max(.26*FCTM/500, .0013)*1000*d
    # Full axial restraint at fct_eff=fctm; both faces share tensile force.
    # k=1 for h<300mm, kc=1 pure tension, sigma_s=300 MPa voluntary crack target.
    restraint_req_per_face = FCTM*1000*h/(2*300)
    fbd = 2.25*1*1*(FCTK/GAMMA_C)
    lb_rqd = bar/4*FYD/fbd
    return dict(h_mm=h,bar_mm=bar,spacing_mm=spacing,cnom_mm=COVER,
        d_mm=d,As_mm2_per_m_per_face_direction=steel,As_min_flex_mm2_per_m=amin,
        MRd_kNm_per_m=mr,VRdc_kN_per_m=v*1000*d/1000,vRdc_MPa=v,
        x_over_d=x/d,ductile_section=x/d<=.45,
        mesh_clear_gap_mm=gap,required_clear_gap_mm=clear_min,
        dual_mesh_fits=gap>=clear_min,As_min_pass=steel>=amin,
        spacing_pass=spacing<=min(2*h,250),
        steel_kg_per_m2_four_layers=4*steel*1e-6*RHO_STEEL,
        concrete_m3_per_m2=h/1000,
        full_restraint_As_per_face_at_300MPa=restraint_req_per_face,
        full_restraint_steel_pass=steel>=restraint_req_per_face,
        lbrqd_full_fyd_mm=lb_rqd,
        lap_1p5_lbrqd_mm=1.5*lb_rqd,
        raw_near_support_limit_kN_per_m=.5*1000*d*.6*(1-FCK/250)*FCD/1000)

def cracked(s,E):
    A,d,b=s['As_mm2_per_m_per_face_direction'],s['d_mm'],1000
    n=ES/E
    x=(math.sqrt((n*A)**2+2*b*n*A*d)-n*A)/b
    I=b*x**3/3+n*A*(d-x)**2
    return x,I

def crack(s,M_kNm,E_for_x,kt):
    x,I=cracked(s,E_for_x)
    A,d=s['As_mm2_per_m_per_face_direction'],s['d_mm']
    sigma=M_kNm*1e6/(A*(d-x/3))
    hc=min(2.5*(s['h_mm']-d),(s['h_mm']-x)/3,s['h_mm']/2)
    rho=A/(1000*hc)
    clear_to_inner=COVER+s['bar_mm']
    sr=3.4*clear_to_inner+.8*.5*.425*s['bar_mm']/rho
    eps=max((sigma-kt*FCTM/rho*(1+ES/ECM*rho))/ES,.6*sigma/ES)
    return dict(wk_mm=sr*eps,sigma_s_MPa=sigma,x_mm=x,
                hceff_mm=hc,rho_eff=rho,srmax_mm=sr,mean_strain=eps,
                close_bar_formula_valid=s['spacing_mm']<=5*(clear_to_inner+s['bar_mm']/2),
                elastic_steel=sigma<=500)

def deflection(s,L,zone,phi):
    # Fully cracked stiffness throughout: deliberately neglect tension stiffening,
    # compression reinforcement and concrete tensile stiffness.
    Eeff=ECM/(1+phi)
    _,Ilong=cracked(s,Eeff)
    _,Ishort=cracked(s,ECM)
    G=.025*s['h_mm']+2  # kPa = N/mm on 1m strip
    if zone=='residential':
        qlong, qshort = G+.3*2, .7*2
        Plong,Pshort=0,0
    else:
        qlong,qshort=G,0
        Plong,Pshort=.6*10000/.2,.4*10000/.2 # N per 1m strip, not whole slab
    long=5*qlong*L**4/(384*Eeff*Ilong)+Plong*L**3/(48*Eeff*Ilong)
    short=5*qshort*L**4/(384*ECM*Ishort)+Pshort*L**3/(48*ECM*Ishort)
    return dict(total_mm=long+short,sustained_mm=long,transient_mm=short,
                fully_cracked_Ilong_mm4_per_m=Ilong,phi=phi)

def check(s,Lm,zone):
    L=Lm*1000
    G=.025*s['h_mm']+2
    Q=2 if zone=='residential' else 0
    wuls=1.35*G+1.5*Q
    Pk=0 if zone=='residential' else 10/.2 # kN on 1m strip
    Pd=1.5*Pk
    M=wuls*Lm**2/8+Pd*Lm/4 # centre point wheel = upper bound to finite footprint
    Mchar=(G+Q)*Lm**2/8+Pk*Lm/4
    Mqp=(G+.3*Q)*Lm**2/8+.6*Pk*Lm/4
    Vuniform=wuls*Lm/2 # support face, do not use d-section shortcut
    Vraw,Vdesign,wheel_x,beta_at_max=Vuniform,Vuniform,None,None
    equilibrium_residual=0
    if zone=='garage':
        # Whole 0.2m footprint stays inside void. Wheel can move continuously;
        # reaction = Pd*(L-x)/L. Treat full wheel as force at its centroid for
        # near-support beta; do NOT use nearest footprint edge. The maximum
        # point-force beta*reaction bounds any nonnegative footprint pressure
        # because its integral cannot exceed the largest point-force influence.
        # Include beta kink x=2d exactly, plus dense independent grid.
        coords={100+(L-200)*i/10000 for i in range(10001)}
        coords.add(min(L-100,max(100,2*s['d_mm'])))
        for xc in sorted(coords):
            av=xc
            beta=max(.25,min(av/(2*s['d_mm']),1))
            V=Vuniform+beta*Pd*(L-xc)/L
            raw=Vuniform+Pd*(L-xc)/L
            if V>Vdesign:
                Vdesign,wheel_x,beta_at_max=V,xc,beta
            Vraw=max(Vraw,raw)
            left=Vuniform+Pd*(L-xc)/L
            right=Vuniform+Pd*xc/L
            equilibrium_residual=max(equilibrium_residual,abs(left+right-(wuls*Lm+Pd)))
    chars=crack(s,Mchar,ECM,.4) # conservative long-duration kt under full char load
    qps=crack(s,Mqp,ECM/3.5,.4)
    dels=[deflection(s,L,zone,p) for p in (1.5,2.5,3.5)]
    dd=dels[1]
    # Interior punching of 200x200 wheel. No soil reaction is subtracted;
    # include all G inside 2d perimeter. d lower-direction bound used.
    d=s['d_mm']; u1=800+4*math.pi*d
    area_inside=(200*200+800*2*d+math.pi*(2*d)**2)/1e6
    Vp=15+1.35*G*area_inside
    punch_v=1.15*Vp*1000/(u1*d)
    # Loaded-face crushing, beta deliberately also 1.15.
    face_v=1.15*15*1000/(800*d)
    face_lim=.5*.6*(1-FCK/250)*FCD
    passes={
      'flexure':M<=s['MRd_kNm_per_m'] and s['ductile_section'],
      'shear_conditional_direct_support_anchorage':Vdesign<=s['VRdc_kN_per_m'],
      'raw_compression_strut_limit':Vraw<=s['raw_near_support_limit_kN_per_m'],
      'QP_crack_0p3mm':qps['wk_mm']<=.3 and qps['elastic_steel'],
      'characteristic_crack_0p3mm_extra':chars['wk_mm']<=.3 and chars['elastic_steel'],
      'deflection_L250':dd['total_mm']<=L/250,
      'reinforcement_fits':s['dual_mesh_fits'],
      'minimum_flexural_steel':s['As_min_pass'],
      'spacing':s['spacing_pass'],
      'interior_punching':zone!='garage' or punch_v<=s['vRdc_MPa'],
      'loaded_face_compression':zone!='garage' or face_v<=face_lim,
    }
    return dict(zone=zone,span_m=Lm,scenario=('DESIGN' if Lm==1 else 'ROBUSTNESS' if Lm<=2 else 'HYPOTHETICAL_EXTREME'),
       Gk_kPa=G,Qk_kPa=Q,Pk_kN_per_1m_strip=Pk,
       MEd_kNm_per_m=M,VEd_kN_per_m=Vdesign,VEd_raw_face_kN_per_m=Vraw,
       raw_face_shear_pass_without_near_support_rule=Vraw<=s['VRdc_kN_per_m'],
       governing_wheel_centre_mm=wheel_x,governing_near_support_beta=beta_at_max,
       M_characteristic_kNm_per_m=Mchar,M_quasipermanent_kNm_per_m=Mqp,
       crack_characteristic_conservative=chars,crack_quasipermanent=qps,
       deflection=dd,deflection_phi_sensitivity=dels,deflection_limit_mm=L/250,
       interior_punching_vEd_MPa=punch_v if zone=='garage' else None,
       loaded_face_vEd_MPa=face_v if zone=='garage' else None,
       passes=passes,all_selected_checks_pass=all(passes.values()),
       equilibrium_force_residual_kN=equilibrium_residual,
       utilization_M=M/s['MRd_kNm_per_m'],utilization_V=Vdesign/s['VRdc_kN_per_m'])

def navier(a,b,h,q_kPa,P_kN,modes):
    """Elastic isotropic simply supported FOUR-edge rectangular patch, centre load.
    Analytic Fourier expansion, no finite element software. Only centre M and w;
    not a Wood-Armer/shear/free-edge/L-corner design proof. N, mm throughout.
    """
    nu=.2; D=ECM*h**3/(12*(1-nu**2)); q=q_kPa/1000; P=P_kN*1000
    out={'w_mm':0.,'Mx_kNm_per_m':0.,'My_kNm_per_m':0.,'integrated_load_N':0.}
    sinc=lambda z: math.sin(z)/z if z else 1
    for m in range(1,modes+1,2):
        al=m*math.pi/a; sm=math.sin(m*math.pi/2)
        for n in range(1,modes+1,2):
            be=n*math.pi/b; sn=math.sin(n*math.pi/2)
            qmn=16*q/(m*n*math.pi**2)+4*P/(a*b)*sm*sn*sinc(al*100)*sinc(be*100)
            W=qmn/(D*(al*al+be*be)**2)
            out['w_mm']+=W*sm*sn
            out['Mx_kNm_per_m']+=D*(al*al+nu*be*be)*W*sm*sn/1000
            out['My_kNm_per_m']+=D*(be*be+nu*al*al)*W*sm*sn/1000
            out['integrated_load_N']+=qmn*4/(al*be)
    target=q*a*b+P
    out.update(a_mm=a,b_mm=b,h_mm=h,q_kPa=q_kPa,P_kN=P_kN,modes=modes,
               target_load_N=target,load_integral_relative_error=(out['integrated_load_N']-target)/target)
    return out

def main():
    results={}
    for name,cfg in CONFIGS.items():
        s=section(*cfg)
        zones=['garage'] if 'GARAGE' in name else ['residential'] if 'RESIDENTIAL' in name else ['residential','garage']
        results[name]={'section':s,'cases':[check(s,L,z) for z in zones for L in (1,1.5,2,4)]}
    plate=[]
    for dims,q,p in [((1000,1000),8.775,15),((1000,4000),8.775,15),((1000,6000),10.7625,0)]:
        plate.append({'convergence':[navier(*dims,180,q,p,n) for n in (21,41,81,161)]})
    # Analytic checks independent of stress-block evaluation and Fourier grid.
    uniform_w=1.35*(25*.15+2)+1.5*2
    assert abs(uniform_w-10.7625)<1e-12
    assert abs(results['MIN_RESIDENTIAL']['cases'][0]['MEd_kNm_per_m']-uniform_w/8)<1e-12
    for obj in results.values():
        for case in obj['cases']:
            assert case['equilibrium_force_residual_kN']<1e-9
    assert not results['REF100']['section']['dual_mesh_fits']
    assert not results['REJECT_GARAGE150']['cases'][0]['passes']['shear_conditional_direct_support_anchorage']
    for name in ['MIN_RESIDENTIAL','MIN_GARAGE','MEDIUM_RESIDENTIAL','MEDIUM_GARAGE','MAX_RESIDENTIAL','MAX_GARAGE']:
        assert results[name]['cases'][0]['all_selected_checks_pass'], name
    # Long four-supported-edge plate approaches simply supported 1-way strip.
    longplate=plate[2]['convergence'][-1]
    assert abs(longplate['Mx_kNm_per_m']/(10.7625/8)-1)<.01
    for model in plate:
        last,prev=model['convergence'][-1],model['convergence'][-2]
        assert abs(last['Mx_kNm_per_m']/prev['Mx_kNm_per_m']-1)<.005
        assert abs(last['load_integral_relative_error'])<.01
    output={
      'status':'CONDITIONAL LOCAL SECTION COMPARISON; entire building/foundation NOT verified',
      'materials':dict(fck_MPa=FCK,fctm_MPa=FCTM,fctk005_MPa=FCTK,Ecm_MPa=ECM,Es_MPa=ES,
        gamma_c=GAMMA_C,gamma_s=GAMMA_S,alpha_cc_assumed=ALPHA_CC,fcd_MPa=FCD,fyd_MPa=FYD),
      'assumptions':{
        'slab_role':'Ground-supported floor panels; all masonry/heavy reactions have independent designed strips; no raft action assumed.',
        'loss_of_support':'Interior long trench; simply supported parallel edges; isolated from construction/free edges and openings; local anchorage in supported slab on both sides.',
        'design_void_m':1.,'robustness_void_m':[1.5,2.], 'outside_required_function_void_m':4.,
        'cover_mm':COVER,'aggregate_Dmax_mm':AGGREGATE,'nominal_mesh_laps':'Locally stagger lap layers; do not overlap all four meshes at one location.',
        'wheel':'10kN characteristic ONE wheel / 200x200mm footprint; forces assigned only to 200mm strip, no transverse spread.',
        'wheel_axle_limitation':'Another wheel in the same local void, van/truck/jack/lift/point storage loads NOT covered.',
        'garage_psi2_assumed':.6,'residential_psi2_assumed':.3,'deflection_limit':'L/250 chosen project screening criterion, not a floor finish settlement tolerance.',
        'crack_limit':'0.3mm chosen target; code-style QP plus voluntarily more conservative full-characteristic kt=0.4 envelope.',
        'shear_near_support_rule':'EC2 6.2.2(6); beta=max(0.25,min(av/(2d),1)); av=xc to FORCE CENTROID, not near footprint edge. Moving point-force maximum bounds a distributed positive footprint. Load on top, direct supported ground and full tensile anchorage required. No generic d-section shortcut.',
        'required_supported_mesh_extension':'At least 1000mm beyond each void edge (bar development), and ground reaction/support settlement verified separately.',
        'durability':'C16/20 exposure suitability, 100yr life and actual cover acceptance unresolved separately; 35mm is conditional geometric input.',
        'restraint':'Flexural cracks calculated; full axial restraint screening generally fails. Jointed/slip layer detailing and early shrinkage/temperature analysis remain required.',
        'CZ_NA':'Exact relevant Czech National Annex text not inspected here; parameters explicit conservative/project assumptions, not asserted CZ approval.'},
      'sources':SOURCES,'sections':results,'independent_navier_checks':plate,
      'verification':'Internal force equilibrium <1e-9 kN; independent one-way UDL formula; Navier 21/41/81/161 mode convergence; long-rectangle analytical limit; predicted rejected 100mm cage and 150mm garage.'}
    path=ROOT/'results/slab-results.json'
    path.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
    print(path)
    for name,obj in results.items():
        s=obj['section'];c=obj['cases'][0]
        print(f"{name:22} h={s['h_mm']:3.0f} Ø{s['bar_mm']:.0f}/{s['spacing_mm']:.0f} MRd={s['MRd_kNm_per_m']:.2f} VRd={s['VRdc_kN_per_m']:.2f} | L1 M={c['MEd_kNm_per_m']:.2f} V={c['VEd_kN_per_m']:.2f} w_char={c['crack_characteristic_conservative']['wk_mm']:.3f} w_qp={c['crack_quasipermanent']['wk_mm']:.3f} defl={c['deflection']['total_mm']:.2f} pass={c['all_selected_checks_pass']}")

if __name__=='__main__':
    main()
