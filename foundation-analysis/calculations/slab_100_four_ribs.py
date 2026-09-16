#!/usr/bin/env python3
"""PRELIMINARY 100mm C16/20 slab screening; NOT a four-rib foundation approval.
Independent of slab.py: does not import or overwrite the older study.
Run: python3 foundation-analysis/calculations/slab_100_four_ribs.py
Python standard library only. Internal section units N, mm, MPa.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
B,H,COVER=1000.,100.,35.
FCK,FCTM,FCTK,ECM,ES=16.,1.9,1.3,28600.,200000.
FCD,FYD=.85*FCK/1.5,500/1.15
EPS_CU=.0035
G_SELF,G_FINISH,Q=2.5,2.,2.
GK=G_SELF+G_FINISH
QD=1.35*GK+1.5*Q
PHIS=(1.5,2.5,3.5)
WALL_PATH=BASE/'results/wall-loads.csv'
WALLS=list(csv.DictReader(WALL_PATH.open()))
BY_WALL={w['wall']:w for w in WALLS}
WALL_CASES={
 'floor_only': dict(gwall_kN_m=0.,source_wall=None),
 'wall_H200':dict(gwall_kN_m=float(BY_WALL['IW-STUDY-NORTH']['gk_kN_m']),source_wall='IW-STUDY-NORTH'),
 'wall_SA30':dict(gwall_kN_m=float(BY_WALL['C-OPEN-HALL-S']['gk_kN_m']),source_wall='C-OPEN-HALL-S'),
 'wall_typical_partition':dict(gwall_kN_m=float(BY_WALL['IW-BATH-105-SOUTH-E']['gk_kN_m']),source_wall='IW-BATH-105-SOUTH-E'),
 'wall_heaviest_selfweight':dict(gwall_kN_m=float(BY_WALL['C-GARAGE-SPINE-N']['gk_kN_m']),source_wall='C-GARAGE-SPINE-N'),
}


def section(bar,spacing,direction):
    # One welded mesh near bottom. Crossing wires cannot have identical depth.
    layer=0 if direction=='outer_wire_nearer_soffit' else 1
    clear_cover_to_wire=COVER+layer*bar
    d=H-clear_cover_to_wire-bar/2
    A=math.pi*bar**2/4*B/spacing
    # Actual RC strain-compatible section, rectangular EC2 stress block.
    def equilibrium(x):
        strain=EPS_CU*(d-x)/x
        sigma=min(FYD,ES*strain)
        return .8*B*x*FCD-A*sigma
    lo,hi=1e-9,d*(1-1e-10)
    for _ in range(100):
        mid=(lo+hi)/2
        if equilibrium(mid)>0:hi=mid
        else:lo=mid
    x=(lo+hi)/2; eps_s=EPS_CU*(d-x)/x; fs=min(FYD,ES*eps_s)
    T=A*fs; C=.8*B*x*FCD
    MR=T*(d-.4*x)/1e6
    xlim=.45*d
    Mlim=.8*B*xlim*FCD*(d-.4*xlim)/1e6
    rho=min(A/(B*d),.02);k=min(2.,1+math.sqrt(200/d))
    vr=max(.12*k*(100*rho*FCK)**(1/3),.035*k**1.5*math.sqrt(FCK))
    fbd=2.25*FCTK/1.5
    return dict(bar_mm=bar,spacing_mm=spacing,direction=direction,As_mm2_per_m=A,
      d_mm=d,wire_clear_cover_mm=clear_cover_to_wire,
      concrete_top_cover_for_single_mesh_mm=H-COVER-2*bar,
      single_mesh_nominally_fits=(H-COVER-2*bar)>=COVER,
      two_mesh_clear_gap_mm=H-2*COVER-4*bar,
      two_mesh_required_clear_gap_mm=max(bar,20,16+5),
      two_meshes_fit=(H-2*COVER-4*bar)>=max(bar,20,16+5),
      x_uls_mm=x,x_over_d=x/d,steel_ultimate_strain=eps_s,steel_uls_stress_MPa=fs,
      steel_reaches_fyd=fs>=FYD-1e-8,MRd_strain_compatible_kNm_m=MR,
      x_over_d_0p45_screen_pass=x/d<=.45,
      MRd_xd0p45_comparison_kNm_m=Mlim,
      limiting_block_note='Comparison only: reducing M to this number does not change the fixed section ultimate x/d or certify mesh ductility.',
      Asmin_mm2_m=max(.26*FCTM/500,.0013)*B*d,
      flexural_minimum_area_pass=A>=max(.26*FCTM/500,.0013)*B*d,
      VRdc_kN_m=vr*B*d/1000,vRdc_MPa=vr,
      mesh_spacing_250_and_2h_screen_pass=spacing<=min(250,2*H),
      anchorage_lbrqd_good_bond_full_fyd_mm=bar/4*FYD/fbd,
      compression_tension_equilibrium_residual_N=abs(C-T),
      steel_mass_single_mesh_kg_m2=2*A*1e-6*7850)


def cracked(s,E,M):
    A,d=s['As_mm2_per_m'],s['d_mm'];n=ES/E
    x=(math.sqrt((n*A)**2+2*B*n*A*d)-n*A)/B
    I=B*x**3/3+n*A*(d-x)**2
    M_Nmm=M*1e6
    sigma_s=M_Nmm/(A*(d-x/3))
    sigma_c=2*M_Nmm/(B*x*(d-x/3))
    return dict(x_mm=x,I_mm4=I,sigma_s_MPa=sigma_s,sigma_c_MPa=sigma_c)


def crack(s,M,E,longterm):
    p=cracked(s,E,M)
    # A failed linear model must not produce apparently authoritative huge cracks.
    c_limit=(.45 if longterm else .6)*FCK
    valid=p['sigma_s_MPa']<=500 and p['sigma_c_MPa']<=c_limit
    hceff=min(2.5*(H-s['d_mm']),(H-p['x_mm'])/3,H/2)
    rho=s['As_mm2_per_m']/(B*hceff)
    sr=3.4*s['wire_clear_cover_mm']+.8*.5*.425*s['bar_mm']/rho
    eps=max((p['sigma_s_MPa']-.4*FCTM/rho*(1+ES/ECM*rho))/ES,.6*p['sigma_s_MPa']/ES)
    p.update(valid_linear_screen=valid,concrete_stress_screen_limit_MPa=c_limit,
             wk_mm=sr*eps if valid else None,srmax_mm=sr,hceff_mm=hceff,rho_eff=rho,
             stress_values_are_elastic_predictors=True,
             reason_if_invalid=None if valid else 'Elastic steel or linear-concrete/creep screening limit exceeded; nonlinear SLS not solved.',
             assumed_precracked=True,
             close_bar_formula_valid=s['spacing_mm']<=5*(s['wire_clear_cover_mm']+s['bar_mm']/2))
    return p


def delta_formula(w_N_mm,P_N,L_mm,EI):
    return 5*w_N_mm*L_mm**4/(384*EI)+P_N*L_mm**3/(48*EI)


def sls(s,Lm,wall,wheel,phi):
    L=Lm*1000; psi=.6 if wheel else .3
    # Wall force per one-metre strip is permanent; wheel per 200mm strip is scaled.
    q=0 if wheel else Q
    Pwheel=50. if wheel else 0.
    Mqp=(GK+psi*q)*Lm**2/8+(wall+psi*Pwheel)*Lm/4
    Mdq=((1-psi)*q)*Lm**2/8+(1-psi)*Pwheel*Lm/4
    Mchar=Mqp+Mdq
    Eeff=ECM/(1+phi)
    qp=crack(s,Mqp,Eeff,True)
    char=crack(s,Mchar,ECM,False)
    inc=cracked(s,ECM,Mdq)
    total_ss=qp['sigma_s_MPa']+inc['sigma_s_MPa']
    total_sc=qp['sigma_c_MPa']+inc['sigma_c_MPa']
    valid=qp['valid_linear_screen'] and total_ss<=500 and total_sc<=.6*FCK
    value=None
    if valid:
        value=delta_formula(GK+psi*q,(wall+psi*Pwheel)*1000,L,Eeff*qp['I_mm4'])
        value+=delta_formula((1-psi)*q,(1-psi)*Pwheel*1000,L,ECM*inc['I_mm4'])
    return dict(phi=phi,Mqp_kNm_m=Mqp,Mcharacteristic_kNm_m=Mchar,
       crack_QP=qp,crack_characteristic_instant_comparison=char,
       deflection_valid_linear_screen=valid,deflection_mm=value,limit_L250_mm=L/250,
       deflection_reason_if_invalid=None if valid else 'Linear creep or elastic stress screening failed; no reliable deflection reported.',
       combined_long_plus_short_steel_predictor_MPa=total_ss,
       combined_long_plus_short_concrete_predictor_MPa=total_sc)


def case(s,Lm,wall_id,model):
    wheel=wall_id=='garage_assumed_single_wheel10kN'
    wall=0 if wheel else WALL_CASES[wall_id]['gwall_kN_m']
    qd=1.35*GK+(0 if wheel else 1.5*Q)
    Pd=1.5*50 if wheel else 1.35*wall
    M=qd*Lm**2/8+Pd*Lm/4
    # Uniform plus central wall/wheel response, separate no-reduction moving-line
    # support shear bound. No uncertain near-support beta nor fictitious width.
    Vcenter=qd*Lm/2+Pd/2
    Vupper=qd*Lm/2+Pd
    runs=[sls(s,Lm,wall,wheel,p) for p in PHIS];mid=runs[1]
    eqres=abs(2*Vcenter-(qd*Lm+Pd))
    bending=M<=s['MRd_strain_compatible_kNm_m']
    shear=Vupper<=s['VRdc_kN_m']
    crackpass=None if mid['crack_QP']['wk_mm'] is None else mid['crack_QP']['wk_mm']<=.3
    defpass=None if mid['deflection_mm'] is None else mid['deflection_mm']<=Lm*1000/250
    positive_screen=bending and shear and s['x_over_d_0p45_screen_pass'] and crackpass is True and defpass is True
    return dict(model=model,span_m=Lm,load_case=wall_id,wall_gk_kN_m=wall,
        qEd_kN_m=qd,Pd_kN_per_m_strip=Pd,MEd_kNm_m=M,
        VEd_centered_load_kN_m=Vcenter,VEd_moving_load_no_reduction_upper_kN_m=Vupper,
        ULS_actual_section_bending_comparison_pass=bending,
        ULS_shear_upper_comparison_pass=shear,
        moment_utilization=M/s['MRd_strain_compatible_kNm_m'],
        shear_utilization_upper=Vupper/s['VRdc_kN_m'],
        positive_bending_and_SLS_conservative_screen_pass=positive_screen,
        quasi_permanent_crack_screen_pass=crackpass,deflection_screen_pass=defpass,
        sls_phi2p5=mid,creep_sensitivity=runs,
        equilibrium_residual_kN=eqres,
        negative_bending='NOT VERIFIED: no designed top reinforcement.',
        construction_approval=False)


def verification():
    # Independent virtual work numerical integration for simple beam deflection.
    # mm/N; E*I arbitrary known value, Simpson quadrature and analytical formula.
    L=1500.;q=6.5;P=6253.875;EI=1e11;N=10000;dx=L/N
    integral=0
    for i in range(N+1):
        x=i*dx
        moment=(q*L/2+P/2)*x-q*x*x/2-P*max(x-L/2,0)
        unit=x/2 if x<=L/2 else (L-x)/2
        factor=1 if i in (0,N) else 4 if i%2 else 2
        integral+=factor*moment*unit/EI
    integrated=integral*dx/3
    formula=delta_formula(q,P,L,EI)
    assert abs(integrated/formula-1)<1e-8
    return dict(virtual_work_deflection_mm=integrated,formula_deflection_mm=formula,
        relative_error=abs(integrated/formula-1),simpson_subintervals=N)


def produce_md(out):
    lines=['# 100 mm doska nad štyrmi rebrami – predbežný screening',
     '', '**Nie je to schválenie statiky domu.** Hrúbka 100 mm, spoločná betonáž dosky/rebier a miestny zhutnený zásyp sú deklarované. Výstuž nie je zadaná; nižšie uvedené siete sú iba skúšobné možnosti.',
     '', '## Model a zdroje vstupov',
     '', 'C16/20; B500 bez doloženej triedy ťažnosti; b = 1000 mm, h = 100 mm, cnom = 35 mm. fcd = 0,85 × 16/1,5 = 9,067 MPa, fyd = 500/1,15 = 434,783 MPa; Ecm = 28 600 MPa, Es = 200 000 MPa, fctm = 1,9 MPa. Národné parametre sú výslovné predpoklady; české NA ani expozícia/100-ročná trvanlivosť tým nie sú overené.',
     '', 'Stále plošné zaťaženie je 2,5 kPa vlastná doska + 2,0 kPa predpoklad vrstiev; obytné qk = 2,0 kPa. qEd = 1,35 × 4,5 + 1,5 × 2 = **9,075 kPa**. Vrstva 2,0 kPa zachováva porovnateľnosť so starším výpočtom; skutočná skladba chýba.',
     '', 'Rebrá R7, R1, R2, R4: deklarovaná celková výška 400 mm vrátane dosky, teda 300 mm pod doskou; šírka 350 mm je pracovný predpoklad. Ich výstuž, skutočná zemná podpora, reakcie a uloženie nie sú týmto skriptom posúdené. Zarážka 150 mm nie je automaticky preukázané uloženie alebo zakotvenie.',
     '', 'Líniové hmotnosti sú načítané priamo z `results/wall-loads.csv`. Ide o predpoklady výrobku, skladby a výšky pôvodnej štúdie, nie zamerané hmotnosti. Hodnota 4,05 kN/m nemala doložený zdroj a nepoužíva sa. Ťažké nosné steny tu zahŕňajú iba vlastnú hmotnosť, bez strechy a povaly.',
     '', '| Prípad | Gk steny kN/m | Identifikátor zdroja |', '|---|---:|---|']
    for key,v in WALL_CASES.items():
        lines.append(f"| {key} | {v['gwall_kN_m']:.4f} | {v['source_wall'] or 'bez steny'} |")
    lines += ['', 'V každom 1 m páse sa stena kolmá na smer premostenia zaťažuje samostatnou silou P = gsteny × 1 m uprostred rozpätia. Nie je rozpočítaná do plošného zaťaženia celého domu. To nie je posúdenie skutočnej polohy každej steny; rovnobežná stena, otvory a bodové reakcie potrebujú iný model.',
     '', '## Výpočtové vzťahy a obmedzenia',
     '', 'Skúša sa jedna spodná obojsmerná sieť: pri vonkajšom drôte d = h − c − φ/2; pri krížnom vnútornom drôte d = h − c − 3φ/2. Siete sa preto neposudzujú s rovnakou účinnou výškou oboch smerov.',
     '', 'ULS: MEd = qEd L²/8 + Pd L/4. Stena je stála, Pd = 1,35 gsteny. Šmyk má samostatne centrálnu reakciu qL/2 + P/2 a konzervatívnu pohybovú hornú hranicu qL/2 + P, bez redukcie pri podpore. Prierez rieši rovnováhu 0,8 b x fcd = As min[fyd; Es εcu(d−x)/x], εcu = 0,0035; MRd = T(d−0,4x). Oceľ sa bez kontroly kompatibility nepovažuje vždy za vytečenú.',
     '', 'VRdc = max[0,12 k(100ρ fck)^(1/3); 0,035 k^(3/2)√fck] bd, k ≤ 2, ρ ≤ 0,02. Platnosť potrebuje zakotvenú ťahovú výstuž a správne podopretie, ktoré zatiaľ chýbajú. Minimálna ohybová výstuž As,min = max[0,26 fctm/fyk; 0,0013] bd.',
     '', '**Ťažnosť:** pre tento konzervatívny screening sa požaduje aj x/d ≤ 0,45. Nie je prezentované ako univerzálna hranica každého jednoduchého prierezu bez redistribúcie; EC2 viaže zodpovedajúce obmedzenia na spôsob analýzy, redistribúciu a rotačnú kapacitu. Ø8/100 prekračuje toto prijaté kritérium v oboch smeroch (0,494 / 0,568), preto nie je označená za vyhovujúci návrh ani pri malej MEd. Pomocný MRd pri xlim = 0,45d je iba porovnanie tlakového bloku: nezmení skutočné x/d už navrhnutého množstva ocele.',
     '', 'SLS sa počíta z úplne popraskaného prierezu: n=Es/Ec; x=[√((nAs)²+2bnAsd)−nAs]/b; Icr=bx³/3+nAs(d−x)²; σs=M/[As(d−x/3)]. Trhliny podľa EC2 §7.3.4 s kt=0,4, k1=0,8, k2=0,5, k3=3,4, k4=0,425 a ρeff; limit wk=0,30 mm je porovnávací predpoklad. QP je G+0,3Q, garáž G+0,6P; ψ2 vyžaduje potvrdenie podľa konkrétneho užívania a českej NA.',
     '', 'Dlhodobá časť používa Ec,eff=Ecm/(1+φ), φ=1,5/2,5/3,5; prechodný prírastok krátkodobú tuhosť. δ=5qL⁴/(384EI)+PL³/(48EI), porovnávací limit L/250. Ak elastický prediktor prekročí fy=500 MPa, charakteristický tlak 0,6fck alebo kvázistály tlak 0,45fck, príslušné trhliny/priehyby sa **nevydávajú za platný lineárny výsledok**; v JSON je null a dôvod. Potrebný nelineárny výpočet nie je urobený. Veľká vypočítaná deformácia z neplatného modelu sa teda neprezentuje ako reálna predpoveď.',
     '', 'Zmrašťovanie, teploty, krútenie a záporné ohyby nie sú preukázané. Jedna sieť pri spodku sa nepovažuje za navrhnutú hornú výstuž. Lokálne zásypové dutiny 1 / 1,5 / 2 m sú citlivostné prípady, nie dôkaz ich pravdepodobnosti ani automatická povinnosť pre každý pozemok.',
     '', '## Prierezy – obe výšky krížiacich sa drôtov',
     '', '| Sieť / smer | d mm | As mm²/m | MRd kNm/m | x/d | VRdc kN/m | x/d ≤ 0,45 |', '|---|---:|---:|---:|---:|---:|---|']
    for name,obj in out['meshes'].items():
        for direction,v in obj['directions'].items():
            s=v['section']
            lines.append(f"| {name} / {'vonkajší' if 'outer' in direction else 'vnútorný'} | {s['d_mm']:.0f} | {s['As_mm2_per_m']:.1f} | {s['MRd_strain_compatible_kNm_m']:.3f} | {s['x_over_d']:.3f} | {s['VRdc_kN_m']:.2f} | {'áno' if s['x_over_d_0p45_screen_pass'] else 'NIE'} |")
    lines += ['', 'Dve plné obojsmerné siete hore+dole sa pri cnom=35 mm nezmestia s požadovanou medzerou aspoň 21 mm: Ø6 má medzeru 6 mm, Ø8 zápornú medzeru −2 mm. Jedna spodná sieť sa geometricky zmestí; tým nie sú vyriešené presahy, podložky, tolerancie a krytie v uzloch.',
      '', '## Lokálna dutina – slabší smer siete',
      '', 'Nižšie sú platné QP trhliny a dlhodobý priehyb pri φ=2,5. „—“ znamená prekročený rozsah lineárneho modelu, nie nulový výsledok. Označenie „číselne áno“ sa týka iba uvedených pozitívnych lokálnych kontrol.',
      '', '| Sieť | L m | Zaťaženie | MEd kNm/m | wk QP mm | δ mm | Pozitívny screening |', '|---|---:|---|---:|---:|---:|---|']
    for name,obj in out['meshes'].items():
        cs=obj['directions']['inner_cross_wire']['cases']
        for c in cs:
            if c['model']!='local_void' or c['load_case'] not in ['floor_only','wall_typical_partition','wall_heaviest_selfweight']:continue
            ss=c['sls_phi2p5'];w=ss['crack_QP']['wk_mm'];d=ss['deflection_mm']
            crack_text=f'{w:.3f}' if w is not None else '—'
            delta_text=f'{d:.2f}' if d is not None else '—'
            verdict='číselne áno' if c['positive_bending_and_SLS_conservative_screen_pass'] else 'NEPREUKÁZANÉ / NIE'
            lines.append(f"| {name} | {c['span_m']:.1f} | {c['load_case']} | {c['MEd_kNm_m']:.2f} | {crack_text} | {delta_text} | {verdict} |")
    lines += ['', '## Výhodne idealizované celé medzery bez zemnej podpory',
       '', 'Pevné nepretvárajúce sa jednoduché podpory na dvoch okrajoch, iba podlahové zaťaženie bez stien. Používa sa už svetlá medzera, bez zväčšenia na účinné rozpätie; je to priaznivý predpoklad. Nie je to automatický návrhový stav straty všetkého zásypu ani dôkaz celého L pôdorysu.',
       '', '| L m | MEd kNm/m, iba podlaha | Max MRd všetkých skúšaných smerov kNm/m | Záver |', '|---|---:|---:|---|']
    max_m=max(v['section']['MRd_strain_compatible_kNm_m'] for obj in out['meshes'].values() for v in obj['directions'].values())
    for L in [5.2485,6.65,7.973]:
        lines.append(f'| {L:.4f} | {QD*L*L/8:.3f} | {max_m:.3f} | nevyhovuje všetkým skúšobným sieťam |')
    lines += ['', '5,2485 m je modelová svetlá medzera R7–R1; 7,973 m modelová R2–R4. Hodnota 6,65 m = 7,00 − 0,35 m je výhodná idealizácia šírky krídla s pracovnými podperami; nie je geodeticky potvrdené voľné rozpätie. Presné napojenia a nosná funkcia rebier ostávajú otvorené.',
     '', 'Doplňujúci garážový prípad (JSON): jedno **predpokladané**, nepotvrdené koleso 10 kN na stope 200 × 200 mm, celá sila iba na 200 mm páse. Pri L=1 m MEd=19,509 kNm/m, nad všetkými skúšanými MRd. Je to konzervatívny test bez priečneho roznosu, nie dôkaz, že každá 100 mm doska na skutočnom podloží pod vozidlom zlyhá. Pretlačenie, okraje a súbeh kolies nie sú týmto testom uzavreté.',
     '', '## Čo sa nedá schváliť',
     '', '- Celý dom: strecha, steny, štyri rebrá, obvodový betón a pôvodné pásy nemajú týmto výpočtom potvrdenú nosnú cestu ani únosnosť.',
     '- Jedna spodná sieť: chýba horná výstuž nad rebrami, pri lokálnom zdvihu podložia, zápornom ohybe a obmedzenom zmrašťovaní.',
     '- Miestna hlina/piesok: opis „zhutnené“ neurčuje zrnitosť, vlhkosť, organické prímesi, namŕzavosť, hrúbku vrstiev, modul, sadanie ani budúcu stratu podpory. Výpočet nevyvodzuje sadanie z percent Proctora.',
     '- Pôvodná zemina pod zásypom a pásmi, voda, drenáž, stavebné fázy, trhliny a rozdielne sadanie zostávajú neoverené.',
     '- Krytie 35 mm a C16/20 pre skutočnú expozíciu a životnosť 100 rokov zostávajú podmienene zadanými vstupmi.',
     '- 150 mm zarážka bez rozmerového výkladu, reakcií a výstuže nie je preukázané uloženie, prenesenie šmyku alebo zakotvenie. Orientačné lb,rqd pri dobrých podmienkach vychádza približne 334 mm pre Ø6 a 446 mm pre Ø8; nejde o návrh konkrétneho spoja.',
     '', '## Overenie a opakovanie',
     '', '`python3 foundation-analysis/calculations/slab_100_four_ribs.py` vytvorí iba nové JSON/MD súbory. Kontroly: rovnováha prierezu a reakcií; výpočet priehybu nezávislým numerickým integrálom virtuálnej práce; oba smery každej siete; citlivosť dotvarovania. Starý `slab.py` a `slab-results.json` sa nemenia.',
     '', 'Zdroj základných vzťahov: [JRC, Walraven, EN 1992, 2008](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf), časti analýzy/redistribúcie, prierezových pretvorení, šmyku a trhlín; [JRC Worked Examples, kapitola 5](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/Bridge_Design-Eurocodes-Worked_examples.pdf), §7.3.4 trhliny. Sú to verejné podklady k prvogeneračnému EN 1992-1-1; nenahrádzajú plný text rozhodujúcej ČSN a českej NA.', '']
    return '\n'.join(lines)


def main():
    originals=[BASE/'calculations/slab.py',BASE/'results/slab-results.json']
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}
    meshes={}
    for bar,spacing in [(6,150),(8,150),(8,100)]:
        name=f'phi{bar}_s{spacing}'
        dirs={}
        for direction in ['outer_wire_nearer_soffit','inner_cross_wire']:
            s=section(bar,spacing,direction)
            cs=[case(s,L,w,'local_void') for L in [1.,1.5,2.] for w in WALL_CASES]
            cs += [case(s,L,'floor_only','hypothetical_complete_gap_no_soil') for L in [5.2485,6.65,7.973]]
            cs += [case(s,L,'garage_assumed_single_wheel10kN','garage_local_void_sensitivity') for L in [1.,1.5,2.]]
            assert s['compression_tension_equilibrium_residual_N']<1e-6
            assert all(c['equilibrium_residual_kN']<1e-8 for c in cs)
            assert all(not c['ULS_actual_section_bending_comparison_pass'] for c in cs if c['model']=='hypothetical_complete_gap_no_soil')
            dirs[direction]={'section':s,'cases':cs}
        meshes[name]={'directions':dirs}
    out=dict(status='PRELIMINARY_SCREENING_NOT_CONSTRUCTION_APPROVAL',version_date='2026-09-16',
       user_declarations={'slab_mm':100,'rib_total_height_including_slab_mm':400,'rib_depth_below_slab_mm':300,
           'pour':'slab and ribs cast together','fill':'local clay/sand reportedly compacted','reinforcement':'NOT SUPPLIED',
           'edge_notch_150mm':'direction, force transfer and anchorage UNRESOLVED'},
       assumptions={'rib_width_mm':350,'cover_mm':COVER,'fcd_MPa':FCD,'fyd_MPa':FYD,'Ecm_MPa':ECM,
           'G_self_kPa':G_SELF,'G_finish_kPa':G_FINISH,'Q_residential_kPa':Q,'qEd_floor_kPa':QD,
           'phi_sensitivity':PHIS,'fixed_negative_bending_model':False,'global_L_plan_model':False,
           'linear_SLS_stress_screen':'sigma_s<=500MPa; sigma_c characteristic<=0.6fck; quasi permanent<=0.45fck. Exceedance suppresses unreliable linear w/delta.',
           'ductility':'x/d<=0.45 adopted conservative project screening, not asserted universal simple-section EC2 limit; actual mesh class/rotation unverified.',
           'clear_spans_m':[5.2485,6.65,7.973]},
       wall_source={'path':str(WALL_PATH.relative_to(BASE)),'status':'MODEL_ASSUMPTIONS_NOT_AS_BUILT_WEIGHTS',
           'sha256':hashlib.sha256(WALL_PATH.read_bytes()).hexdigest(),
           'all_rows_min_gk_kN_m':min(float(w['gk_kN_m']) for w in WALLS),
           'all_rows_max_gk_kN_m':max(float(w['gk_kN_m']) for w in WALLS),
           'minimum_warning':'minimum rows are very short jambs; do not treat as representative long partition',
           'selected_cases':WALL_CASES},
       meshes=meshes,verification=verification(),
       sources=['https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf',
       'https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/Bridge_Design-Eurocodes-Worked_examples.pdf'])
    json_path=BASE/'results/slab-100-four-ribs.json'
    json_path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    (BASE/'results/slab-100-four-ribs.md').write_text(produce_md(out))
    for p in originals:assert before[str(p)]==hashlib.sha256(p.read_bytes()).hexdigest()
    print(json_path)
    print('Old slab.py and slab-results.json unchanged; force equilibrium and virtual-work checks passed.')
    for name,obj in meshes.items():
        cs=obj['directions']['inner_cross_wire']['cases']
        for c in cs:
            if c['span_m']!=1 or c['model']!='local_void':continue
            ss=c['sls_phi2p5']
            print(name,c['load_case'],'MEd',round(c['MEd_kNm_m'],3),'wk',ss['crack_QP']['wk_mm'],'delta',ss['deflection_mm'],'positive_screen',c['positive_bending_and_SLS_conservative_screen_pass'])

if __name__=='__main__':main()
