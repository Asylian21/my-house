#!/usr/bin/env python3
"""100mm C16/20 interior floor strip on CONTINUOUS homogeneous soil support.
Own bounded Winkler sensitivity calculation; not a house/rib/foundation approval.
Analytical convolution of finite-width wall pressure with infinite-beam Green
functions. Python standard library only. Internally m, N; section checks mm, MPa.
Run: python3 foundation-analysis/calculations/slab_100_ground_support.py
"""
import csv
import hashlib
import json
import math
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
ECM,ES,FCK,FCTM=28600.,200000.,16.,1.9
FCD,FYD=.85*FCK/1.5,500/1.15
B_MM,H_MM,COVER,PHI,SPACING=1000.,100.,35.,8.,150.
A=math.pi*PHI**2/4*B_MM/SPACING
IG_MM4=B_MM*H_MM**3/12
EI_GROSS=ECM*IG_MM4*1e-6 # MPa*mm4 -> Nm2
G,Q=4.5,2.0
BACKGROUND={'characteristic':G+Q,'quasipermanent':G+.3*Q,'ULS':1.35*G+1.5*Q}
WALL_CSV=BASE/'results/wall-loads.csv'
GEOMETRY=BASE/'inputs/geometry.json'
WALLS={r['wall']:r for r in csv.DictReader(WALL_CSV.open())}
GEOM={r['id']:r for r in json.loads(GEOMETRY.read_text())['walls']}
WALL_IDS=['IW-STUDY-NORTH','IW-BATH-105-SOUTH-E','C-GARAGE-SPINE-N']
KS_VALUES=[5.,10.,20.,50.]


def rc_section(d):
    """Compatible equilibrium at ultimate curvature, no arbitrary steel yielding."""
    def balance(x):
        sig=min(FYD,ES*.0035*(d-x)/x)
        return .8*B_MM*x*FCD-A*sig
    lo,hi=1e-9,d-1e-9
    for _ in range(100):
        x=(lo+hi)/2
        if balance(x)>0:hi=x
        else:lo=x
    x=(lo+hi)/2
    sigma=min(FYD,ES*.0035*(d-x)/x)
    C=.8*B_MM*x*FCD
    rho=min(A/(B_MM*d),.02);k=min(2.,1+math.sqrt(200/d))
    v=max(.12*k*(100*rho*FCK)**(1/3),.035*k**1.5*math.sqrt(FCK))
    return dict(d_mm=d,x_mm=x,x_over_d=x/d,
        sigma_steel_uls_MPa=sigma,eps_steel_uls=.0035*(d-x)/x,
        MRd_kNm_per_m=A*sigma*(d-.4*x)/1e6,VRdc_kN_per_m=v*B_MM*d/1000,
        force_equilibrium_residual_N=abs(C-A*sigma),
        x_d_above_0p45_rotation_screen=x/d>.45,
        note='Section capacity only; steel ductility class, bond, laps, cover durability and deformation capacity unverified. x/d0.45 is not asserted a universal capacity limit.')


def cracked_EI(d,creep_phi=0):
    E=ECM/(1+creep_phi);n=ES/E
    x=(math.sqrt((n*A)**2+2*B_MM*n*A*d)-n*A)/B_MM
    I=B_MM*x**3/3+n*A*(d-x)**2
    return dict(d_mm=d,phi=creep_phi,E_MPa=E,x_mm=x,Icr_mm4=I,
                EI_Nm2=E*I*1e-6,ratio_to_gross_EI=E*I/(ECM*IG_MM4))

SECTIONS={
 'outer_bottom_wire':{'positive':rc_section(61.),'negative':rc_section(39.)},
 'inner_cross_wire':{'positive':rc_section(53.),'negative':rc_section(47.)},
}
STIFFNESSES={
 'gross_uncracked':dict(EI_Nm2=EI_GROSS,ratio_to_gross_EI=1.,phi=0.,basis='Uncracked gross concrete Ig; excludes transformed reinforcement.'),
 'constant_cracked_positive':dict(**cracked_EI(53.),basis='Uniform EI from fully cracked weaker positive section, d=53mm. Sensitivity, not solved cracking pattern.'),
 'constant_cracked_negative':dict(**cracked_EI(39.),basis='Uniform EI from fully cracked weaker negative section, d=39mm. Sensitivity, not solved cracking pattern.'),
 'constant_cracked_negative_phi2p5':dict(**cracked_EI(39.,2.5),basis='Uniform EI from d=39mm fully cracked section with Ecm/(1+2.5). Sensitivity; no soil creep modeled.'),
}


def patch_response(x,P,a,EI,ks):
    """Infinite beam, 1m width, full contact bilateral Winkler trial.
    P[N] is wall line load[kN/m]*1000 on ONE metre along a long wall.
    a[m] is actual idealized wall footprint across the strip. q_patch=P/a[N/m].
    w positive down; M positive sagging; V=dM/dx.
    ks[N/m3], b=1m -> k=ks*b [N/m2].
    """
    k=ks*1.0;beta=(k/(4*EI))**.25
    def F0(z):
        s=1 if z>=0 else -1;t=beta*abs(z)
        return s*(1-math.exp(-t)*math.cos(t))/beta
    def F2(z):
        s=1 if z>=0 else -1;t=beta*abs(z)
        return s*math.exp(-t)*math.sin(t)/beta
    def f2(z):
        t=beta*abs(z)
        return math.exp(-t)*(math.cos(t)-math.sin(t))
    right,left=x+a/2,x-a/2
    w=P/a*beta/(2*k)*(F0(right)-F0(left))
    M=P/a/(4*beta)*(F2(right)-F2(left))
    V=P/a/(4*beta)*(f2(right)-f2(left))
    return w,M,V


def golden_max(fn,lo,hi):
    r=(math.sqrt(5)-1)/2
    c=hi-r*(hi-lo);d=lo+r*(hi-lo)
    fc,fd=fn(c),fn(d)
    for _ in range(75):
        if fc>fd:
            hi,d,fd=d,c,fc;c=hi-r*(hi-lo);fc=fn(c)
        else:
            lo,c,fc=c,d,fd;d=lo+r*(hi-lo);fd=fn(d)
    x=(lo+hi)/2
    return x,fn(x)


def extrema(P,a,EI,ks,n=1200):
    beta=(ks/(4*EI))**.25
    end=12/beta+a/2
    xs=[i*end/n for i in range(n+1)]
    vals=[patch_response(x,P,a,EI,ks) for x in xs]
    out={}
    for name,index,sign in [('w_max',0,1),('w_min',0,-1),('M_max',1,1),('M_min',1,-1),('V_abs_max',2,-1)]:
        best=max(range(n+1),key=lambda i:sign*vals[i][index])
        lo=xs[max(0,best-1)];hi=xs[min(n,best+1)]
        candidates=[(xs[best],sign*vals[best][index]),golden_max(lambda x:sign*patch_response(x,P,a,EI,ks)[index],lo,hi)]
        x,y=max(candidates,key=lambda z:z[1])
        out[name]={'x_m':x,'value':sign*y}
    out['beta_per_m']=beta;out['characteristic_length_1_beta_m']=1/beta
    return out


def simpson(fn,lo,hi,n):
    if hi==lo:return 0.
    assert n%2==0
    dx=(hi-lo)/n
    return dx/3*sum((1 if i in (0,n) else 4 if i%2 else 2)*fn(lo+i*dx) for i in range(n+1))


def independent_checks():
    P=12975.;a=.301;EI=EI_GROSS;ks=5e6;beta=(ks/(4*EI))**.25
    # Direct convolution by numerical integration; primitive formulas not used.
    errors=[]
    for x in [0.,a/2,.35,1.,2.,4.]:
        def green(z,which):
            t=beta*abs(z)
            if which=='w':return beta/(2*ks)*math.exp(-t)*(math.cos(t)+math.sin(t))
            return 1/(4*beta)*math.exp(-t)*(math.cos(t)-math.sin(t))
        split=sorted(set([-a/2,max(-a/2,min(a/2,x)),a/2]))
        for j,which in enumerate(['w','M']):
            numeric=sum(simpson(lambda xi:P/a*green(x-xi,which),l,r,1000) for l,r in zip(split,split[1:]))
            analytic=patch_response(x,P,a,EI,ks)[j]
            errors.append(abs(numeric-analytic)/max(abs(analytic),1e-12))
    # Extra soil reaction must sum to entire wall load, with baseline subtracted.
    end=18/beta+a/2
    reaction=2*simpson(lambda x:ks*patch_response(x,P,a,EI,ks)[0],0,end,40000)
    # Independently reproduce point-load limit, and differential equation away
    # from footprint discontinuities using finite differences of M.
    tiny=1e-5
    w0,m0,_=patch_response(0,P,tiny,EI,ks)
    point_w=P*beta/(2*ks);point_m=P/(4*beta)
    residual=[]
    for x in [0.,.05,.5,1.,2.]:
        h=.0001
        wm,mm,_=patch_response(x,P,a,EI,ks)
        mplus=patch_response(x+h,P,a,EI,ks)[1]
        mminus=patch_response(x-h,P,a,EI,ks)[1]
        q=P/a if abs(x)<a/2 else 0
        residual.append(abs(-(mplus-2*mm+mminus)/h**2+ks*wm-q))
    e1=extrema(P,a,EI,ks,600);e2=extrema(P,a,EI,ks,2400)
    convergence=max(abs(e1[k]['value']-e2[k]['value'])/max(abs(e2[k]['value']),1e-12) for k in ['w_max','w_min','M_max','M_min','V_abs_max'])
    assert max(errors)<1e-8
    assert abs(reaction/P-1)<1e-6
    assert abs(w0/point_w-1)<1e-5 and abs(m0/point_m-1)<1e-5
    assert max(residual)<.1
    assert convergence<1e-6
    return dict(numerical_convolution_max_relative_error=max(errors),
       wall_force_N=P,integrated_additional_ground_reaction_N=reaction,
       force_equilibrium_relative_error=abs(reaction/P-1),
       point_load_limit_w_relative_error=abs(w0/point_w-1),point_load_limit_M_relative_error=abs(m0/point_m-1),
       differential_equation_max_absolute_residual_N_per_m=max(residual),
       extremum_grid600_vs2400_relative_change=convergence,
       finite_domain_integral_extent_each_side_m=end,
       odd_shear_and_even_w_M_symmetry='by exact kernel; checked numerically in main')


def make_case(wall_id,ks_MN,stiff_id):
    P=float(WALLS[wall_id]['gk_kN_m'])*1000
    a=GEOM[wall_id]['width_m'];EI=STIFFNESSES[stiff_id]['EI_Nm2'];ks=ks_MN*1e6
    ex=extrema(P,a,EI,ks)
    Mplus=ex['M_max']['value']/1000;Mminus=ex['M_min']['value']/1000
    Vk=abs(ex['V_abs_max']['value'])/1000
    wdmax=ex['w_max']['value'];wdmin=ex['w_min']['value']
    reactions={}
    for combo,q in BACKGROUND.items():
        factor=1.35 if combo=='ULS' else 1.
        reactions[combo]=dict(background_load_kPa=q,
           wall_factor=factor,
           displacement_max_mm=1000*(q*1000/ks+factor*wdmax),
           displacement_min_mm=1000*(q*1000/ks+factor*wdmin),
           additional_wall_indentation_max_mm=1000*factor*wdmax,
           ground_pressure_max_kPa=q+factor*ks*wdmax/1000,
           ground_pressure_min_kPa=q+factor*ks*wdmin/1000,
           compression_only_contact_consistent=q+factor*ks*wdmin/1000>=0)
    comparisons={}
    for direction,secs in SECTIONS.items():
        pos=secs['positive'];neg=secs['negative']
        comparisons[direction]=dict(positive_moment_utilization=1.35*Mplus/pos['MRd_kNm_per_m'],
           negative_moment_utilization=1.35*abs(Mminus)/neg['MRd_kNm_per_m'],
           positive_M_comparison_pass=1.35*Mplus<=pos['MRd_kNm_per_m'],
           negative_M_comparison_pass=1.35*abs(Mminus)<=neg['MRd_kNm_per_m'],
           shear_utilization=1.35*Vk/min(pos['VRdc_kN_per_m'],neg['VRdc_kN_per_m']),
           section_comparison_only=True)
    mcr=FCTM*B_MM*H_MM**2/6/1e6
    # Profile is even for w/M; positive x suffices; V sign exposed.
    end=6/ex['beta_per_m'];profile=[]
    for i in range(81):
        x=i*end/80;w,m,v=patch_response(x,P,a,EI,ks)
        wn,mn,vn=patch_response(-x,P,a,EI,ks)
        assert abs(wn-w)<1e-12 and abs(mn-m)<1e-7 and abs(vn+v)<1e-7
        profile.append(dict(x_m=x,wall_increment_w_mm=w*1000,M_service_kNm_m=m/1000,V_service_kN_m=v/1000,
            pressure_service_char_kPa=BACKGROUND['characteristic']+ks*w/1000))
    return dict(wall_id=wall_id,wall_load_Gk_kN_per_m=P/1000,wall_footprint_width_m=a,
        load_status=WALLS[wall_id]['status'],ks_MN_per_m3=ks_MN,ks_status='ASSUMED_SENSITIVITY_NOT_SITE_TEST',
        stiffness_id=stiff_id,EI_Nm2=EI,EI_ratio_gross=EI/EI_GROSS,
        beta_per_m=ex['beta_per_m'],influence_decay_5_over_beta_m=5/ex['beta_per_m'],
        M_positive_service_kNm_m=Mplus,M_negative_service_kNm_m=Mminus,
        M_positive_ULS_kNm_m=1.35*Mplus,M_negative_ULS_kNm_m=1.35*Mminus,
        negative_M_location_m=ex['M_min']['x_m'],max_shear_ULS_kN_m=1.35*Vk,
        mean_cracking_Mcr_kNm_m=mcr,
        gross_uncracked_load_stress_consistent=max(abs(Mplus),abs(Mminus))<=mcr if stiff_id=='gross_uncracked' else None,
        gross_consistency_note='Load cracking check using fctm only; absence of prior shrinkage/thermal cracks NOT proved.',
        ground_response=reactions,section_comparisons=comparisons,
        profile_service=profile,
        construction_approval=False)


def markdown(out):
    lines=['# 100 mm doska so súvislou podporou zeminy – lokálny výpočet', '',
      '**Hlavný model ponecháva zeminu pod celou doskou.** Ide o vnútorný metrový pás na homogénnej pružnej podpore, nie o dosku visiacu medzi rebrami. Výsledok je podmienená citlivosť, nie súhlas s betonážou ani preukázanie nosnosti celého domu.', '',
      '## Vstupy a nosná cesta', '',
      'C16/20, h=100 mm; skúšobná spodná obojsmerná sieť Ø8/150 B500, cnom=35 mm. Výstuž používateľ nezadal. Stena → lokálny ohyb dosky → súvislá tlaková reakcia zásypu. Rebrá, obvod, ich tuhosť a reakcie strechy sa týmto lokálnym modelom nenahrádzajú.', '',
      'k_s = **5 / 10 / 20 / 50 MN/m³** sú vedome zvolené citlivostné hodnoty. Nie sú skúškou miestnej hliny/piesku, prevodom z Proctora ani dovolenou únosnosťou zeminy. k_s závisí od rozmeru zaťaženej oblasti, vrstiev a skúšobnej metódy; nijaká z týchto hodnôt sa nepredpisuje realizátorovi ako už dosiahnutý stav.', '',
      'Plošné Gk=4,5 kPa (doska2,5 + predpoklad vrstiev2,0), Qk=2,0 kPa. Charakteristická kombinácia6,5; kvázistála5,1; ULS9,075 kPa. ψ2=0,3 je výslovný predpoklad. Steny sú stále: SLS1,0Gsteny, ULS1,35Gsteny. Podlahové plošné zaťaženie na nekonečnej homogénnej podpore spôsobí konštantný posun q/k_s, bez lokálneho ohybu. Pri reálnych okrajoch a rozdieloch tuhosti to neplatí.', '',
      '| Stena z interného modelu | Gk kN/m | Kontaktná šírka m |', '|---|---:|---:|']
    for w in WALL_IDS:lines.append(f"| {w} | {float(WALLS[w]['gk_kN_m']):.6f} | {GEOM[w]['width_m']:.3f} |")
    lines += ['', 'Hmotnosti pochádzajú z `results/wall-loads.csv`, šírky z `inputs/geometry.json`; ide o modelové predpoklady, nie potvrdené zaťaženia z dodacích listov. Šírka H200=200 mm idealizuje celý pás rovnomerne; skutočné rozdelenie hmotnosti muriva/predsadenej konštrukcie treba doplniť. Pri najťažšej stene12,975 kN/m sa nepočíta strecha ani povala.', '',
      '## Riešenie a kontrola kontaktu', '',
      'Použité jednotky: m, N. P=gsteny×1 m; šírka metrového pásu b=1 m, k=k_s b. Rovnica EI w⁽⁴⁾ + k w = q(x), β=(k/(4EI))^(1/4). Stena je konečná rovnomerná tlaková stopa šírky a: qsteny=P/a. Analyticky sa integruje Greenova funkcia cez celý tento pás. M=−EI w″, V=dM/dx. Výpočet obsahuje kladné aj záporné momenty.', '',
      'Jadrové funkcie jednotkovej bodovej sily sú w₁(x)=β/(2k) exp(−β|x|)[cos(β|x|)+sin(β|x|)] a M₁(x)=1/(4β) exp(−β|x|)[cos(β|x|)−sin(β|x|)]. Nejde o rozmazanie steny na celý dom: konečná stopa sa konvoluuje s presnou reakciou podporeného pásu.', '',
      'Pružiny lineárneho riešenia matematicky vedia prenášať aj ťah. Preto sa výslovne overuje celkový tlak p=qpodlahy+k_s wsteny ≥0. Samotný prírastok od steny môže byť záporný; rozhoduje celkový kontakt vrátane vlastnej tiaže. V uvedených kombináciách vyšiel kontakt všade tlakový. Ak by vyšiel ťah, výsledok by nebol fyzikálne prípustný a bolo by potrebné riešenie s oddeľovaním kontaktu; záporná reakcia by sa neskrývala.', '',
      '## Tuhosť – štyri odlišné citlivosti', '',
      '| Označenie | EI kN·m² | Pomer k hrubému prierezu |', '|---|---:|---:|']
    for key,v in STIFFNESSES.items():lines.append(f"| {key} | {v['EI_Nm2']/1000:.3f} | {v['ratio_to_gross_EI']:.4f} |")
    lines += ['', 'Hrubý nepopraskaný prierez má Ecm=28 600 MPa a Ig=bh³/12. Znížené tuhosti sa reprodukovateľne odvodia z úplne popraskaného prierezu jednej siete: n=Es/Ec, x=[√((nAs)²+2bnAsd)−nAs]/b, Icr=bx³/3+nAs(d−x)². Použité d=53 mm pre kladný ohyb alebo d=39 mm pre záporný; posledný prípad má Ec=Ecm/(1+2,5).', '',
      '**Každý znížený EI je konštantná citlivosť pre celý pás.** Nie je to skutočne vyriešené rozdelenie trhlín, nelineárne materiálové správanie alebo nameraná tuhosť dosky. Zmenšenie EI zníži roznesenie sily a momenty, ale zväčší miestny tlak a zatlačenie. Nemožno z neho vybrať iba priaznivý moment a ignorovať zhoršenie kontaktnej deformácie.', '',
      '## Skutočné účinné výšky jednej spodnej siete', '',
      '| Drôt | d+ mm | MRd+ kNm/m | d− mm | MRd− kNm/m |', '|---|---:|---:|---:|---:|']
    for k,v in SECTIONS.items():lines.append(f"| {k} | {v['positive']['d_mm']:.0f} | {v['positive']['MRd_kNm_per_m']:.3f} | {v['negative']['d_mm']:.0f} | {v['negative']['MRd_kNm_per_m']:.3f} |")
    lines += ['', 'Pri zápornom ohybe sa tlaková strana otočí; preto má rovnaký drôt d−=h−d+, nie d+=61/53 mm. Sieť umiestnená pri spodku môže ležať v ťahovej oblasti aj pri menšej zápornomomentovej účinnej výške, takže jej vypočítaná záporná kapacita nie je automaticky nulová. Tým sa z nej nestáva navrhnutá horná sieť: chýba preukázanie trhlín pri hornom povrchu, ťažnosti, kotvenia a správania nad rebrami. Pri d−39 mm vychádza x/d≈0,515; rotačná kapacita a spôsob analýzy potrebujú osobitné overenie.', '',
      'MRd je z kompatibility pretvorení pri εcu=0,0035 a rovnováhe tlakového bloku0,8bx fcd s As min(fyd,Esεs). fcd=9,067 MPa; fyd434,783 MPa. Nejde o úplný návrh podľa českých NA ani trvanlivostný dôkaz C16/20 pri cieľovej životnosti100 rokov.', '',
      '## Výsledky: nepopraskaná tuhosť', '',
      '| Stena | k_s MN/m³ | MEd+ / MEd− kNm/m | pmax SLS kPa | max posun SLS mm | minimum tlaku SLS kPa |', '|---|---:|---:|---:|---:|---:|']
    for c in out['cases']:
        if c['stiffness_id']!='gross_uncracked':continue
        g=c['ground_response']['characteristic']
        lines.append(f"| {c['wall_id']} | {c['ks_MN_per_m3']:.0f} | {c['M_positive_ULS_kNm_m']:.3f} / {c['M_negative_ULS_kNm_m']:.3f} | {g['ground_pressure_max_kPa']:.2f} | {g['displacement_max_mm']:.3f} | {g['ground_pressure_min_kPa']:.2f} |")
    lines += ['', 'SLS tabulka je charakteristická kombinácia. Kvázistála aj ULS kontaktová odozva je v JSON. Nepopraskaný model sa musí kontrolovať proti Mcr=fctm bh²/6=3,167 kNm/m; prekročenie sa v JSON označuje. Ani nižší moment nepreukazuje, že nevznikli predchádzajúce zmrašťovacie alebo teplotné trhliny.', '',
      '## Najťažšia stena: vplyv tuhosti pri k_s=5 MN/m³', '',
      '| EI prípad | MEd+ / MEd− kNm/m | pmax SLS kPa | max posun SLS mm | zatlačenie navyše od steny mm |', '|---|---:|---:|---:|---:|']
    for c in out['cases']:
        if c['wall_id']!='C-GARAGE-SPINE-N' or c['ks_MN_per_m3']!=5:continue
        g=c['ground_response']['characteristic']
        lines.append(f"| {c['stiffness_id']} | {c['M_positive_ULS_kNm_m']:.3f} / {c['M_negative_ULS_kNm_m']:.3f} | {g['ground_pressure_max_kPa']:.2f} | {g['displacement_max_mm']:.3f} | {g['additional_wall_indentation_max_mm']:.3f} |")
    lines += ['', '## Hranice výsledku', '',
      '- Počítané posuny sú pružná Winklerova odozva modelovanej podpory na uvedené zaťaženie. Nezahŕňajú vlastné sadanie/navlhnutie/konsolidáciu zásypu, sadanie prirodzenej zeminy, zoschnutie hliny, mráz ani históriu výstavby. Nie sú garantovaným celkovým sadaním domu.',
      '- Rovnaký k_s všade nepreukazuje, že miestna zemina bola rovnomerne zhutnená. Materiál, vrstvy, voda, skutočná skúška a jej interpretácia do modelu chýbajú.',
      '- Pás je dlhý a vnútorný, stena rovnako dlhá v priečnom smere. Hrany dosky, L-rohy, konce stien, dvere, prestupy, susediace steny a rigidné rebrá môžu výsledok zmeniť. Dĺžka5/β v JSON ukazuje vzdialenosť približného doznievania; blízky okraj/podpera porušuje predpoklad nekonečného pásu.',
      '- Tlak zeminy sa vypočítal, ale neporovnával s neznámou návrhovou únosnosťou; k_s sa nesmie zamieňať za túto únosnosť.',
      '- Porovnanie ohybových účinkov s prierezom nezahŕňa horné povrchové trhliny, pracovné škáry, kotvenie, dotvarovanie zeminy, zmršťovanie ani celý systém štyroch rebier. Sústredené reakcie strechy, ťažké zariadenia a kolesá auta nie sú nahradené týmito líniami stien.',
      '- Žiadna zo skúšobných sietí ani k_s nie sú realizačným predpisom.', '',
      '## Opakovanie a overenie', '',
      '`python3 foundation-analysis/calculations/slab_100_ground_support.py` vytvorí iba vlastné JSON a MD. Kontrola: nezávislá numerická konvolúcia, integrál dodatočnej reakcie = hmotnosť steny, bodový limit stopy, diferenciálna rovnica, symetria a zjemnenie siete extrémov600→2400 bodov. Staršie výpočty sa nemenia.', '',
      'Zdroje: [NPTEL/IIT Madras, Beam on Elastic Foundation, kapitola11](https://archive.nptel.ac.in/content/storage2/courses/105106049/lecnotes/mainch11.html) pre rovnicu, základnú funkciu a význam negatívnej kontaktnej reakcie; [University of Florida, kapitola10](https://web.mae.ufl.edu/nkim/egm5533/solution/Chap10Student.pdf) pre odlíšenie k od k_s a vzťah β; [JRC, Walraven EN1992](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf) pre prierezové pretvorenia betónu/ocele. Hodnoty k_s nie sú prevzaté z týchto zdrojov ako vlastnosti tejto stavby.', '']
    return '\n'.join(lines)


def main():
    old=[BASE/'calculations/slab.py',BASE/'results/slab-results.json',BASE/'calculations/slab_100_four_ribs.py',BASE/'results/slab-100-four-ribs.json']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in old}
    cases=[make_case(w,k,e) for w in WALL_IDS for k in KS_VALUES for e in STIFFNESSES]
    for secs in SECTIONS.values():
        for v in secs.values():assert v['force_equilibrium_residual_N']<1e-6
    out=dict(status='CONTINUOUS_GROUND_SUPPORTED_INTERIOR_STRIP_SENSITIVITY_NOT_APPROVAL',date='2026-09-16',
       model={'slab_h_mm':100,'strip_b_m':1,'support':'continuous homogeneous Winkler; no void inserted',
         'wall':'finite-width uniform load on interior long strip, no roof reaction included',
         'reinforcement':'trial bottom mesh8/150; user specification absent',
         'boundary':'infinite strip; no imposed rib/end support'},
       materials={'Ecm_MPa':ECM,'Es_MPa':ES,'fck_MPa':FCK,'fctm_MPa':FCTM,'fcd_MPa':FCD,'fyd_MPa':FYD},
       uniform_floor_baselines=[dict(ks_MN_m3=k,**{f'{c}_mm':q/k for c,q in BACKGROUND.items()}) for k in KS_VALUES],
       input_files={'wall_loads':str(WALL_CSV.relative_to(BASE)),'wall_widths':str(GEOMETRY.relative_to(BASE))},
       ks_MN_per_m3_assumed=KS_VALUES,background_kPa=BACKGROUND,
       gross_I_mm4=IG_MM4,gross_EI_Nm2=EI_GROSS,
       section_capacities=SECTIONS,stiffness_sensitivities=STIFFNESSES,
       cases=cases,verification=independent_checks(),
       sources=['https://archive.nptel.ac.in/content/storage2/courses/105106049/lecnotes/mainch11.html',
         'https://web.mae.ufl.edu/nkim/egm5533/solution/Chap10Student.pdf',
         'https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf'])
    p=BASE/'results/slab-100-ground-support.json';p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    (BASE/'results/slab-100-ground-support.md').write_text(markdown(out))
    for path in old:assert hashlib.sha256(path.read_bytes()).hexdigest()==hashes[str(path)]
    print(p)
    print(json.dumps(out['verification'],indent=2))
    for c in cases:
        if c['ks_MN_per_m3']==5:
            g=c['ground_response']['characteristic']
            print(c['wall_id'],c['stiffness_id'],'MEd+',round(c['M_positive_ULS_kNm_m'],3),'MEd-',round(c['M_negative_ULS_kNm_m'],3),'w_mm',round(g['displacement_max_mm'],3),'pmax_kPa',round(g['ground_pressure_max_kPa'],3),'pmin',round(g['ground_pressure_min_kPa'],3))
    print('All old calculation files unchanged.')

if __name__=='__main__':main()
