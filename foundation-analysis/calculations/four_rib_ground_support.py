"""Four 350x400 ribs on continuous Winkler support: bounded sensitivity.

Reads the prior free-beam patch loads, never its boundary conditions/results.
Writes only new ground-support results. No site stiffness or design approval.
Units: m, kN, kPa. Deflection is positive downward; M positive is sagging.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from numpy.polynomial import polynomial as poly

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'results/four-rib-free-beam-screen.json'
PREV = json.loads(SOURCE.read_text())
WIDTH = .350
KS_VALUES = [5000., 10000., 20000., 50000.]  # kN/m3, sensitivity, not soil tests
E_CM_MPA = 28600.
PHI_CREEP = 2.5  # stiffness sensitivity only, not calibrated creep prediction
ES_MPA = 200000.
GAMMA_G = 1.35


def mesh(L, patches, maximum_length):
    breaks = sorted(set([0., round(L, 12)] + [round(p[k], 12) for p in patches for k in ['a_m', 'b_m']]))
    xs = [breaks[0]]
    for start, stop in zip(breaks, breaks[1:]):
        count = max(1, math.ceil((stop - start) / maximum_length))
        xs.extend(start + (stop - start) * j / count for j in range(1, count + 1))
    return np.array(xs)


def real_unit_roots(coefficients):
    result = []
    # Tiny high-order FE roundoff should not produce spurious near-real roots.
    c = poly.polytrim(np.array(coefficients, dtype=float), tol=1e-14)
    if len(c) > 1:
        for z in poly.polyroots(c):
            if abs(z.imag) < 1e-8 and -1e-10 <= z.real <= 1 + 1e-10:
                result.append(float(max(0., min(1., z.real))))
    return result


def solve(L, patches, EI, ks, maximum_length, trace=False):
    """Cubic Hermite EB elements + exactly integrated continuous springs.

    All endpoints are free; no end settlement or rotation is fixed. Distributed
    soil stiffness is ks*WIDTH, not ks alone. Element load boundaries coincide
    with patch boundaries. Recovered M/V follow exact polynomial equilibrium
    under the FE deflection and continuous reaction field.
    """
    xs = mesh(L, patches, maximum_length)
    ndof = 2 * len(xs)
    K = np.zeros((ndof, ndof))
    F = np.zeros(ndof)
    elems = []
    k_line = ks * WIDTH
    for i, (a, b) in enumerate(zip(xs, xs[1:])):
        ell = b - a
        q = sum(p['qk_kN_m'] for p in patches if p['a_m'] - 1e-10 <= (a + b) / 2 <= p['b_m'] + 1e-10)
        kb = EI / ell**3 * np.array([
            [12, 6*ell, -12, 6*ell], [6*ell, 4*ell**2, -6*ell, 2*ell**2],
            [-12, -6*ell, 12, -6*ell], [6*ell, 2*ell**2, -6*ell, 4*ell**2]])
        # Integral of k_line * N.T * N, same polynomial matrix as consistent mass.
        kf = k_line * ell / 420 * np.array([
            [156, 22*ell, 54, -13*ell], [22*ell, 4*ell**2, 13*ell, -3*ell**2],
            [54, 13*ell, 156, -22*ell], [-13*ell, -3*ell**2, -22*ell, 4*ell**2]])
        ids = np.array([2*i, 2*i+1, 2*i+2, 2*i+3])
        K[np.ix_(ids, ids)] += kb + kf
        F[ids] += q * ell / 2 * np.array([1, ell/6, 1, -ell/6])
        elems.append((a, ell, q, ids))
    u = np.linalg.solve(K, F)
    scaled_residual = float(np.linalg.norm(K @ u - F) / max(np.linalg.norm(F), 1.))
    total_force = sum(p['qk_kN_m'] * (p['b_m'] - p['a_m']) for p in patches)
    total_moment = sum(p['qk_kN_m'] * (p['b_m'] - p['a_m']) * (p['a_m'] + p['b_m']) / 2 for p in patches)
    soil_force = 0.
    soil_moment = 0.
    V0, M0 = 0., 0.
    points = []
    for a, ell, q, ids in elems:
        wi, ti, wj, tj = u[ids]
        wc = np.array([wi, ell*ti, -3*wi-2*ell*ti+3*wj-ell*tj, 2*wi+ell*ti-2*wj+ell*tj])
        net = -k_line * wc
        net[0] += q
        # Q(t) = integral_0^(ell*t) (q - spring reaction) dx.
        Qc = np.r_[0., ell * net / np.arange(1, 5)]
        Jc = np.r_[0., 0., ell**2 * net / np.arange(2, 6)]
        Vc = -Qc
        Vc[0] += V0
        Mc = np.zeros(6)
        Mc[0], Mc[1] = M0, V0 * ell
        Mc[1:] -= ell * Qc
        Mc += Jc
        theta_c = poly.polyder(wc) / ell
        # Extrema of displacement, slope, V and M are polynomial roots.
        candidates = [0., 1.] + real_unit_roots(theta_c) + real_unit_roots(poly.polyder(theta_c)) + real_unit_roots(net) + real_unit_roots(Vc)
        if trace:
            candidates += [.25, .5, .75]
        for t in sorted(set(candidates)):
            w = float(poly.polyval(t, wc))
            points.append({'x_m': float(a + ell*t), 'w_mm': w*1000,
                'rotation_rad': float(poly.polyval(t, theta_c)), 'soil_pressure_kPa': ks*w,
                'M_Gk_kNm': float(poly.polyval(t, Mc)), 'V_Gk_kN': float(poly.polyval(t, Vc))})
        soil_element_force = k_line * ell * sum(wc / np.arange(1, 5))
        soil_element_moment = a * soil_element_force + k_line * ell**2 * sum(wc / np.arange(2, 6))
        soil_force += soil_element_force
        soil_moment += soil_element_moment
        V0, M0 = float(poly.polyval(1., Vc)), float(poly.polyval(1., Mc))
    summary = {
        'elements': len(elems), 'maximum_element_length_m': float(max(np.diff(xs))),
        'Gk_total_kN': total_force, 'soil_reaction_integral_kN': float(soil_force),
        'force_equilibrium_relative_error': float(abs(soil_force-total_force)/max(total_force,1)),
        'moment_equilibrium_relative_error': float(abs(soil_moment-total_moment)/max(abs(total_moment),1)),
        'linear_system_relative_residual': scaled_residual,
        'free_right_end_V_residual_kN': V0, 'free_right_end_M_residual_kNm': M0,
        'w_min_mm': min(p['w_mm'] for p in points), 'w_max_mm': max(p['w_mm'] for p in points),
        'rotation_abs_max_mrad': 1000*max(abs(p['rotation_rad']) for p in points),
        'pressure_min_Gk_kPa': min(p['soil_pressure_kPa'] for p in points),
        'pressure_max_Gk_kPa': max(p['soil_pressure_kPa'] for p in points),
        'pressure_average_Gk_kPa': total_force/(WIDTH*L),
        'M_sagging_Gk_kNm': max(0., max(p['M_Gk_kNm'] for p in points)),
        'M_hogging_Gk_kNm': min(0., min(p['M_Gk_kNm'] for p in points)),
        'V_abs_Gk_kN': max(abs(p['V_Gk_kN']) for p in points),
    }
    summary['pressure_max_scaled_1p35G_kPa'] = GAMMA_G*summary['pressure_max_Gk_kPa']
    summary['M_sagging_Ed_kNm'] = GAMMA_G*summary['M_sagging_Gk_kNm']
    summary['M_hogging_Ed_kNm'] = GAMMA_G*summary['M_hogging_Gk_kNm']
    summary['V_abs_Ed_kN'] = GAMMA_G*summary['V_abs_Gk_kN']
    summary['linear_contact_all_compressive'] = summary['pressure_min_Gk_kPa'] >= -1e-6
    assert summary['force_equilibrium_relative_error'] < 1e-6, summary
    assert summary['moment_equilibrium_relative_error'] < 1e-6, summary
    assert scaled_residual < 1e-6, summary
    return summary, points


def stiffness_scenarios():
    b_mm, h_mm, d_mm = 350., 400., 349.
    gross_I = b_mm*h_mm**3/12
    scenarios = [{'id': 'gross_instantaneous', 'EI_kNm2': E_CM_MPA*gross_I/1e9,
        'note': 'Uncracked gross rectangle with Ecm 28600 MPa; not effective T-section.'}]
    E_eff = E_CM_MPA/(1+PHI_CREEP)
    n = ES_MPA/E_eff
    for capacity in PREV['capacities']:
        As = capacity['As_mm2']
        xc = (-n*As + math.sqrt((n*As)**2 + 2*b_mm*n*As*d_mm))/b_mm
        Icr = b_mm*xc**3/3 + n*As*(d_mm-xc)**2
        scenarios.append({'id': 'cracked_sustained_'+capacity['tension_reinforcement'],
            'EI_kNm2': E_eff*Icr/1e9, 'Eeff_MPa_assumed': E_eff,
            'neutral_axis_mm': xc, 'Icr_mm4': Icr,
            'note': 'Fully cracked transformed section, one tension layer; phi=2.5 stiffness sensitivity. Constant EI in both moment signs requires analogous section properties; not a prediction of actual cracking or prescribed top reinforcement.'})
    return scenarios


def main():
    stiffnesses = stiffness_scenarios()
    # Exact finite-beam solution under full-length UDL: constant settlement,
    # zero rotation/M/V, independent of EI and free-ended beam length.
    qtest, ktest, Ltest = 12., 10000., 8.
    uniform, _ = solve(Ltest, [{'a_m':0., 'b_m':Ltest, 'qk_kN_m':qtest}],
        stiffnesses[0]['EI_kNm2'], ktest, .12)
    exact_w = qtest/(ktest*WIDTH)*1000
    uniform_validation = {'exact_w_mm': exact_w, 'computed_w_mm': uniform['w_max_mm'],
        'relative_w_error': abs(uniform['w_max_mm']/exact_w-1),
        'max_abs_M_kNm': max(abs(uniform['M_sagging_Gk_kNm']), abs(uniform['M_hogging_Gk_kNm'])),
        'max_abs_V_kN': uniform['V_abs_Gk_kN']}
    assert uniform_validation['relative_w_error'] < 1e-6
    assert uniform_validation['max_abs_M_kNm'] < 1e-5
    rows, traces = [], []
    for rib in PREV['cases']:
        for stiffness in stiffnesses:
            for ks in KS_VALUES:
                L = rib['old_model_axis_length_m_assumed_span']
                coarse, _ = solve(L, rib['patch_loads'], stiffness['EI_kNm2'], ks, .10)
                fine, trace = solve(L, rib['patch_loads'], stiffness['EI_kNm2'], ks, .05, trace=True)
                errors = {}
                for key in ['w_max_mm', 'rotation_abs_max_mrad', 'pressure_max_Gk_kPa', 'M_sagging_Ed_kNm', 'M_hogging_Ed_kNm', 'V_abs_Ed_kN']:
                    errors[key] = abs(fine[key]-coarse[key])/max(abs(fine[key]), .001)
                maximum_change = max(errors.values())
                assert maximum_change < .005, (rib['rib'], stiffness['id'], ks, errors)
                row = {'rib': rib['rib'], 'length_m': L, 'stiffness': stiffness['id'],
                    'EI_kNm2': stiffness['EI_kNm2'], 'ks_MN_m3_assumed': ks/1000,
                    'contact_width_m_assumed': WIDTH, **fine,
                    'coarse_fine_max_relative_change': maximum_change,
                    'convergence_relative_change': errors,
                    'capacity_comparisons': []}
                for cap in PREV['capacities']:
                    row['capacity_comparisons'].append({'tension_layer_scenario': cap['tension_reinforcement'],
                        'MRd_kNm': cap['MRd_kNm'], 'VRdc_kN': cap['VRdc_kN'],
                        'sagging_MEd_over_MRd': row['M_sagging_Ed_kNm']/cap['MRd_kNm'],
                        'hogging_MEd_over_MRd_IF_same_top_steel': abs(row['M_hogging_Ed_kNm'])/cap['MRd_kNm'],
                        'VEd_over_VRdc': row['V_abs_Ed_kN']/cap['VRdc_kN'],
                        'note': 'Positive moment comparison assumes stated bottom tension layer fully developed. Negative comparison requires same fully developed reinforcement on top; actual top steel/anchorage unknown. Not reinforcement instructions.'})
                rows.append(row)
                for point in trace:
                    traces.append({'rib': rib['rib'], 'stiffness': stiffness['id'], 'ks_MN_m3_assumed':ks/1000, **point})
    all_contact = all(r['linear_contact_all_compressive'] for r in rows)
    out = {'status': 'CONDITIONAL_CONTINUOUS_GROUND_SUPPORT_SENSITIVITY_NOT_SITE_DESIGN',
        'source_file': str(SOURCE.relative_to(BASE)), 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'scope': 'Existing exact permanent patch loads + full350x400 beam selfweight; continuous soil support. Old free-beam boundary conditions are not reused.',
        'geometry': {'width_m_working':WIDTH, 'total_height_m_user':.4, 'included_slab_thickness_m':.1,
            'own_weight_kN_m':3.5, 'own_weight_decomposition_kN_m':{'downstand_300mm':2.625, 'included_slab_strip100mm':.875}},
        'ground_assumptions': {'ks_MN_m3':[k/1000 for k in KS_VALUES], 'status':'ASSUMED_NOT_TESTED',
            'continuous_support':'under entire rib footprint at a common reference level, no voids or imposed ground settlement',
            'boundary_conditions':'both beam ends free in vertical displacement and rotation; natural M=V=0. This models isolated rib on ground without relying on an unresolved connection to the perimeter.',
            'equation':'EI * fourth_derivative(w) + ks*b*w = q(x); spring pressure p=ks*w. Winkler springs independent, no lateral soil coupling.',
            'no_tension_check':'Linear solution checked for p>=0 everywhere. A negative-pressure case would not be admissible as compression-only soil support; no uplift area may be claimed supported.',
            'all_48_cases_compressive':all_contact},
        'stiffness_scenarios':stiffnesses, 'patch_loads':[{'rib':r['rib'],'patches':r['patch_loads']} for r in PREV['cases']],
        'validation':{'uniform_load_exact_solution':uniform_validation,
            'max_force_equilibrium_relative_error':max(r['force_equilibrium_relative_error'] for r in rows),
            'max_moment_equilibrium_relative_error':max(r['moment_equilibrium_relative_error'] for r in rows),
            'max_coarse_to_fine_relative_change':max(r['coarse_fine_max_relative_change'] for r in rows),
            'case_count':len(rows), 'refinement_max_lengths_m':[.10,.05]},
        'cases':rows,
        'limitations':[
            'ks values are sensitivity inputs, not tested soil properties or a bearing-resistance value. ks cannot be inferred from the words local clay/sand, compacted or a percentage Proctor.',
            'Continuous physical contact is an explicit user scenario, not verification of layer quality, moisture, organic removal, thickness, local weakness or long-term settlement.',
            'No roof/attic/snow/wind/live-load/vehicle/equipment or transverse-wall reactions are included. They remain missing inputs, not asserted zero actions.',
            'No unknown slab tributary width is assigned. Only the350mm-wide100mm slab strip already inside total400mm beam is counted once.',
            'Pressure outputs are demands from a linear support model, not a soil bearing/settlement approval. Do not compare them directly with old Rd150 as a current site pass.',
            'Other walls outside the four ribs can transfer through a ground-supported slab to soil. Absence of a rib alone is not a missing load path or proof of failure; their100mm slab/ground interaction must be checked separately.',
            'Free ends avoid assuming a sound old/new joint. They do not verify actual perimeter compatibility, continuity, imposed rotations, lateral actions, torsion or corner nodes.',
            'One-dimensional strips ignore two-dimensional slab distribution, adjacent spring interaction and differential support at existing perimeter. No global building analysis.',
            'Constant gross/cracked EI values bracket stiffness assumptions but are not guaranteed upper/lower bounds of every response, nor a nonlinear cracking/creep history.',
            'No crack-width, shrinkage, reinforcement detailing/anchorage, punching, interface or durability approval. Negative moment requires actual top-side tension capacity.',
        ],
        'method_links':[
            'https://ccaprani.github.io/pycba/notebooks/foundation.html',
            'https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf'],
    }
    (BASE/'results/four-rib-ground-support.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    with (BASE/'results/four-rib-ground-support-traces.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(traces[0]));writer.writeheader();writer.writerows(traces)
    flat = [{k:v for k,v in r.items() if k not in ['convergence_relative_change','capacity_comparisons']} for r in rows]
    with (BASE/'results/four-rib-ground-support-summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    write_markdown(out)
    print(json.dumps(out['validation'],indent=2))
    print('All-compressive contact:',all_contact)
    for rid in ['R7','R1','R2','R4']:
        rr=[r for r in rows if r['rib']==rid]
        print(rid,'wmax_mm range',round(min(r['w_max_mm'] for r in rr),4),round(max(r['w_max_mm'] for r in rr),4),
            'max pGk',round(max(r['pressure_max_Gk_kPa'] for r in rr),4),
            'max abs MEd',round(max(max(abs(r['M_sagging_Ed_kNm']),abs(r['M_hogging_Ed_kNm'])) for r in rr),4),
            'max VEd',round(max(r['V_abs_Ed_kN'] for r in rr),4),
            'maxrotation_mrad',round(max(r['rotation_abs_max_mrad'] for r in rr),4))


def write_markdown(out):
    rows=out['cases']
    lines=['# Štyri rebrá 350 × 400 mm na priebežne podopierajúcej zemine', '',
        '**Podmienená citlivostná analýza podľa výslovného predpokladu používateľa: rebrá sú priebežne podopreté zhutnenou zeminou. Nie je to voľný nosník nesený iba na koncoch.** Rozsah je vlastná tiaž a priamo súosé modelové steny; chýbajúce ostatné zaťaženia sa nepovažujú za nulové.', '',
        '## Model', '',
        '- Konečný Eulerov–Bernoulliho nosník na spojitých Winklerových pružinách: `EI·w⁽⁴⁾ + ks·b·w = q(x)`, tlak `p = ks·w`. Oba konce sú voľné, M = V = 0. Nevytvára sa tak nepreukázaná podpora v dnešnom obvode. Dĺžky 7,495/6,298 m tu znamenajú dĺžku priebežne podopretého pásu, nie voľné rozpätie.',
        '- Pracovný pôdorysný kontakt b = 350 mm po celej dĺžke; rovnaká výška a tuhosť podkladu, bez dutín a vynúteného sadania. Samostatný pás nepreukazuje skutočný spoj s obvodom ani kompatibilitu so susednou doskou.',
        '- Celková výška 400 mm zahŕňa 100 mm dosku. Vlastná tiaž je **3,500 kN/m = 2,625 + 0,875 kN/m**; pruh dosky v šírke rebra je započítaný raz. Širšia neznáma zaťažovacia plocha dosky sa nepriraďuje.',
        '- Presné intervalové tiaže stien sú načítané z predchádzajúceho vstupu; jeho voľné uloženie ani vnútorné sily sa nepreberajú. Pri R4 je zahrnuté predpokladané murivo nad otvorom, nie neznáma vlastná tiaž nadpražia a reakcie strechy.',
        '- Predpokladané **ks = 5 / 10 / 20 / 50 MN/m³** predstavujú citlivosť. Nie sú skúškou miestnej zeminy ani únosnosťou podložia. Hlina/piesok a „zhutnené“ neurčujú ks.',
        '- Pre každé ks sa skúša okamžitá tuhosť neporušeného obdĺžnika a dve konštantné plne popraskané tuhosti s 3Ø16/4Ø16 a predpokladaným dotvarovaním φ = 2,5. Nie je to predikcia trhlín alebo záruka, že tieto hodnoty ohraničia každú odozvu.', '',
        '| Scenár tuhosti | EI [kNm²] |', '|---|---:|']
    for s in out['stiffness_scenarios']:
        lines.append(f"| {s['id']} | {s['EI_kNm2']:.1f} |")
    lines += ['', '## Výsledky — obálka tuhostí pri jednotlivých ks', '',
        'w a p sú pre zahrnuté charakteristické stále tiaže Gk. MEd/VEd sú tieto výsledky násobené 1,35. Záporný M je horný ťah. Rotácia je najväčší miestny sklon, nie posúdenie relatívneho sadania celého domu.', '',
        '| Rebro | ks [MN/m³] | max w [mm] | max p(Gk) [kPa] | max |MEd| [kNm] | max |VEd| [kN] | max sklon [mrad] |',
        '|---|---:|---:|---:|---:|---:|---:|']
    # Escape | characters in header cells to keep Markdown column count valid.
    lines[-2]='| Rebro | ks [MN/m³] | max w [mm] | max p(Gk) [kPa] | max absolútne MEd [kNm] | max absolútne VEd [kN] | max sklon [mrad] |'
    for rid in ['R7','R1','R2','R4']:
        for ks in [5.,10.,20.,50.]:
            rr=[r for r in rows if r['rib']==rid and r['ks_MN_m3_assumed']==ks]
            lines.append(f"| {rid} | {ks:.0f} | {max(r['w_max_mm'] for r in rr):.3f} | {max(r['pressure_max_Gk_kPa'] for r in rr):.2f} | {max(max(abs(r['M_sagging_Ed_kNm']),abs(r['M_hogging_Ed_kNm'])) for r in rr):.3f} | {max(r['V_abs_Ed_kN'] for r in rr):.3f} | {max(r['rotation_abs_max_mrad'] for r in rr):.3f} |")
    lines += ['', 'Každá bunka je obálka troch tuhostí, preto nie celý riadok jednej fyzickej zostavy. Všetkých 48 samostatných prípadov vrátane znamienok M, minima tlaku a integrálu reakcií obsahuje JSON/CSV.', '',
        '## Porovnanie prierezu bez predpisovania výstuže', '',
        'Pre identický obdĺžnik z predchádzajúceho prierezového výpočtu: MRd = 80,69 kNm (3Ø16) a 102,77 kNm (4Ø16), VRd,c = 51,29 a 56,46 kN. Platí prijaté C16/20, B500, krytie 35 mm ku strmeňu Ø8 a plné rozvinutie napätia v prútoch. Porovnanie kladného M predpokladá výstuž dole; pre záporný M musí byť rovnaká účinná vrstva hore. Skutočná horná výstuž a kotvenie nie sú určené.', '',
        '| Rebro | Najväčšie absolútne MEd, všetky prípady [kNm] | Pomer k MRd 3Ø16, len s účinnou výstužou na ťahovej strane | Najväčšie VEd [kN] |',
        '|---|---:|---:|---:|']
    for rid in ['R7','R1','R2','R4']:
        rr=[r for r in rows if r['rib']==rid]
        moment=max(max(abs(r['M_sagging_Ed_kNm']),abs(r['M_hogging_Ed_kNm'])) for r in rr)
        lines.append(f"| {rid} | {moment:.3f} | {100*moment/PREV['capacities'][0]['MRd_kNm']:.2f} % | {max(r['V_abs_Ed_kN'] for r in rr):.3f} |")
    lines += ['', '**Čítanie výsledku:** táto priebežná podpora podstatne mení vnútorné sily oproti voľnému nosníku. Prípadné vyhovenie týchto čiastkových M/V porovnaní však potvrdzuje iba zvolený obmedzený výpočtový scenár; neschvaľuje rebro, 100 mm dosku ani dom.', '',
        '## Overenie výpočtu', '',
        '- Konzistentná spojitá pružinová matica, štandardné kubické nosníkové prvky; hranice zaťažených úsekov sú uzlami siete. Priehyb, tlak a vnútorné sily sa vyhodnocujú aj v analyticky nájdených vnútorných extrémoch.',
        '- Kontrola rovnováhy celkovej zvislej sily a momentu, nulových koncových síl a rezídua lineárnej sústavy.',
        '- Nezávislé presné riešenie pri plnom rovnomernom zaťažení: w = q/(ks·b), nulové M/V a sklon, ľubovoľné EI.',
        f"- Sieť do 100 mm oproti sieti do 50 mm: najväčšia relatívna zmena sledovaného extrému **{100*out['validation']['max_coarse_to_fine_relative_change']:.5f} %**.",
        f"- Najväčšia relatívna chyba rovnováhy sily **{out['validation']['max_force_equilibrium_relative_error']:.3e}**, momentu **{out['validation']['max_moment_equilibrium_relative_error']:.3e}**.",
        f"- Kontrola kontaktu: všetkých 48 prípadov má iba tlakové reakcie: **{'áno' if out['ground_assumptions']['all_48_cases_compressive'] else 'NIE — ťahové prípady nemožno prevziať ako zeminu'}**. Ide o kontrolu vypočítaného stavu, nie dôkaz fyzického kontaktu na stavbe.", '',
        '## Rozsah a chýbajúce údaje', '',
        '**Stena mimo štyroch rebier nie je automaticky bez nosnej cesty.** Pri priebežne podopretej podlahovej doske môže zaťaženie prechádzať zo steny cez dosku do zeminy. Pôdorysný audit 37 stien preto neurčuje povinnosť doplniť rebro pod každú priečku a sám nepreukazuje zlyhanie; príslušnú 100 mm dosku a podložie treba posúdiť pre tieto stenové zaťaženia.', '',
        'Na konečné posúdenie zostávajú: overené vlastnosti a vrstvy zásypu/základovej zeminy, vlhkosť, organické prímesi, kvalita zhutnenia a dlhodobé/nerovnomerné sadanie; skutočná geometria podpory; reakcie strechy a povaly, užitné a bodové zaťaženia; prenos mimo rebier cez 100 mm dosku; spoje so starým obvodom a L-roh; výstuž na oboch potrebných ťahových stranách a kotvenie; trhliny, zmrašťovanie, prerazenie, prestupy, škáry a trvanlivosť. Stará hodnota Rd = 150 kPa sa nepoužíva ako schválenie vypočítaných tlakov.', '',
        'Winklerove pružiny nemodelujú vzájomné pôsobenie susedných pásov alebo súvislého objemu zeminy. Výsledné w je deformácia ideálneho pružinového podložia, nie úplná prognóza sadania budovy. Šmykové deformácie nosníka a 2D pôsobenie dosky sa v tomto obmedzenom modeli nezapočítali.', '',
        'Metodické zdroje: [PyCBA — beam on an elastic Winkler foundation](https://ccaprani.github.io/pycba/notebooks/foundation.html) pre spojitú pružinovú podporu a voľné konce; [JRC — EC2 worked examples](https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf) pre prierezové vzťahy. Použitie týchto vzťahov nie je normovou autorizáciou konkrétnej stavby.', '',
        'Reprodukcia:', '', '```text',
        '/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 foundation-analysis/calculations/four_rib_ground_support.py',
        '```', '',
        'Výstupy: `four-rib-ground-support.json`, `four-rib-ground-support-summary.csv`, `four-rib-ground-support-traces.csv`. Pôvodné vstupy, staré výsledky a report sa nemenia.', '']
    (BASE/'results/four-rib-ground-support.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
