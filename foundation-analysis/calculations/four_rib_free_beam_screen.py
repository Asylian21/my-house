"""Conditional free-span screen for 350x400 C16/20 ribs, not a design.

Only each rib's own weight and its directly aligned model wall self-weight.
No wider slab tributary area, soil springs, roof, imposed loads, masonry arch,
frame restraint, T-section flange, compression steel or reaction redistribution.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
G_PATH = BASE / 'inputs/geometry.json'
A_PATH = BASE / 'inputs/client-agreed-layout.json'
W_PATH = BASE / 'results/wall-loads.csv'
G = json.loads(G_PATH.read_text())
A = json.loads(A_PATH.read_text())
with W_PATH.open() as f:
    weights = {r['wall']: float(r['gk_kN_m']) for r in csv.DictReader(f)}
wallmap = {w['id']: w for w in G['walls']}
gamma_g = 1.35
b, h, c, stirrup, phi = 350., 400., 35., 8., 16.
d = h - c - stirrup - phi / 2
fck, alpha_cc, gamma_c, gamma_s, fyk = 16., .85, 1.5, 1.15, 500.
fcd, fyd = alpha_cc * fck / gamma_c, fyk / gamma_s
q_self = b / 1000 * h / 1000 * 25

def solve_span(L, patches):
    """Exact simply supported result for uniformly loaded finite intervals."""
    assert all(0 <= p['a_m'] < p['b_m'] <= L + 1e-10 for p in patches)
    total = sum(p['qk_kN_m'] * (p['b_m'] - p['a_m']) for p in patches)
    RB = sum(p['qk_kN_m'] * (p['b_m'] - p['a_m']) * (p['a_m'] + p['b_m']) / 2 for p in patches) / L
    RA = total - RB
    def shear(x):
        return RA - sum(p['qk_kN_m'] * max(0., min(x - p['a_m'], p['b_m'] - p['a_m'])) for p in patches)
    def moment(x):
        result = RA * x
        for p in patches:
            ell = max(0., min(x - p['a_m'], p['b_m'] - p['a_m']))
            result -= p['qk_kN_m'] * ell * (x - p['a_m'] - ell / 2)
        return result
    bounds = sorted(set([0., L] + [p[k] for p in patches for k in ['a_m', 'b_m']]))
    candidates = list(bounds)
    for left, right in zip(bounds, bounds[1:]):
        q_here = sum(p['qk_kN_m'] for p in patches if p['a_m'] <= (left + right) / 2 <= p['b_m'])
        if q_here:
            root = left + shear(left) / q_here
            if left <= root <= right:
                candidates.append(root)
    x_max = max(candidates, key=moment)
    assert abs(moment(L)) < 1e-8
    assert abs(RA + RB - total) < 1e-8
    return {'Gk_total_kN': total, 'RA_kN': RA, 'RB_kN': RB,
        'x_Mmax_m': x_max, 'M_gk_max_kNm': moment(x_max),
        'MEd_kNm': gamma_g * moment(x_max), 'VEd_at_left_kN': gamma_g * RA,
        'VEd_at_right_kN': gamma_g * RB, 'VEd_max_unreduced_kN': gamma_g * max(RA, RB)}

# Independent textbook identities verify the load integration, not the design.
test = solve_span(8., [{'a_m': 0., 'b_m': 8., 'qk_kN_m': 1.}])
assert abs(test['M_gk_max_kNm'] - 8.) < 1e-10
assert abs(test['RA_kN'] - 4.) < 1e-10

capacities = []
for n in [3, 4]:
    As = n * math.pi * phi ** 2 / 4
    x = As * fyd / (.8 * b * fcd)
    z = d - .4 * x
    steel_strain_at_concrete_limit = .0035 * (d - x) / x
    assert steel_strain_at_concrete_limit > fyd / 200000
    rho = min(As / (b * d), .02)
    k = min(2., 1 + math.sqrt(200 / d))
    vmin = .035 * k ** 1.5 * math.sqrt(fck)
    VRdc = max(.18 / gamma_c * k * (100 * rho * fck) ** (1 / 3), vmin) * b * d / 1000
    row = {'tension_reinforcement': f'{n}phi16', 'As_mm2': As, 'd_mm': d,
        'x_mm': x, 'x_over_d': x / d, 'z_mm': z,
        'MRd_kNm': As * fyd * z / 1e6, 'VRdc_kN': VRdc,
        'As_min_mm2': max(.26 * 1.9 / fyk, .0013) * b * d,
        'stirrup_scenarios': []}
    for spacing in [100., 150., 200.]:
        for cot in [1., 2.5]:
            z_shear = min(.9 * d, z)
            VRds = (2 * math.pi * stirrup ** 2 / 4) / spacing * z_shear * fyd * cot / 1000
            VRdmax = b * z_shear * .6 * (1 - fck / 250) * fcd / (cot + 1 / cot) / 1000
            row['stirrup_scenarios'].append({'two_leg_phi_mm': 8, 'spacing_mm_assumed': spacing,
                'cot_theta_assumed': cot, 'z_mm': z_shear, 'VRds_kN': VRds,
                'VRdmax_kN': VRdmax, 'minimum_of_VRds_VRdmax_kN': min(VRds, VRdmax)})
    capacities.append(row)

cases = []
for r in A['agreed_ribs']:
    p0, p1 = r['points_m']
    coordinate = 1 if abs(p1[1] - p0[1]) > abs(p1[0] - p0[0]) else 0
    L = abs(p1[coordinate] - p0[coordinate])
    assert abs(L - r['length_m']) < 1e-9
    patches = [{'source': 'full_350x400_selfweight', 'a_m': 0., 'b_m': L, 'qk_kN_m': q_self}]
    for wid in r['source_ids']:
        if wid in wallmap:
            w = wallmap[wid]
            walla, wallb = sorted(pt[coordinate] - p0[coordinate] for pt in w['line_m'])
            patches.append({'source': wid, 'a_m': max(0., walla), 'b_m': min(L, wallb), 'qk_kN_m': weights[wid]})
        elif wid == 'NN2':
            facade = next(f for f in G['facades'] if f['id'] == wid)
            for seg in facade['segments']:
                masonry_height = 3.125 if seg['kind'] == 'wall' else 3.125 - seg['opening']['height'] / 1000
                # Same old-study density/finish assumption; no lintel mass or roof reaction.
                qwall = (.300 * 12 + .030 * 18) * masonry_height
                patches.append({'source': f'NN2_{seg["kind"]}_{seg["from_m"]}',
                    'a_m': seg['from_m'] - p0[coordinate], 'b_m': seg['to_m'] - p0[coordinate], 'qk_kN_m': qwall})
        else:
            raise AssertionError(wid)
    demand = solve_span(L, patches)
    case = {'rib': r['id'], 'old_model_axis_length_m_assumed_span': L, 'patch_loads': patches,
        'demand': demand, 'capacity_comparisons': []}
    for cap in capacities:
        case['capacity_comparisons'].append({'reinforcement': cap['tension_reinforcement'],
            'MEd_over_MRd': demand['MEd_kNm'] / cap['MRd_kNm'],
            'VEd_over_VRdc': demand['VEd_max_unreduced_kN'] / cap['VRdc_kN'],
            'uniform_total_qEd_flexural_limit_kN_m': 8 * cap['MRd_kNm'] / L ** 2,
            'uniform_total_Gk_only_flexural_limit_kN_m': 8 * cap['MRd_kNm'] / (gamma_g * L ** 2),
            'uniform_extra_Gk_above_full_beam_selfweight_flexural_limit_kN_m': 8 * cap['MRd_kNm'] / (gamma_g * L ** 2) - q_self,
            'note': 'Uniform q limits are bending-only for this simply-supported rectangle; cannot be equated to localized loads or a certified allowable wall load.'})
    cases.append(case)

out = {'status': 'CONDITIONAL_FREE_SPAN_SELFWEIGHT_SCREEN_NOT_FINAL_DESIGN',
    'input_sha256': {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [G_PATH, A_PATH, W_PATH]},
    'parameters': {'b_mm_working': b, 'h_mm_total_user_declared': h, 'slab_mm_included_in_h': 100,
        'cover_to_stirrup_mm_assumed': c, 'stirrup_phi_mm_assumed': stirrup, 'fck_MPa': fck,
        'alpha_cc_assumed': alpha_cc, 'gamma_c_assumed': gamma_c, 'gamma_s_assumed': gamma_s,
        'fyk_MPa_assumed': fyk, 'fcd_MPa': fcd, 'fyd_MPa': fyd, 'gamma_g_assumed': gamma_g,
        'beam_total_selfweight_kN_m': q_self, 'downstand300_selfweight_kN_m': .35 * .30 * 25,
        'included_slab_strip100_selfweight_kN_m': .35 * .10 * 25},
    'source_method': {'url': 'https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf',
        'title': 'JRC 2014, Eurocode 2: Background & Applications — Design of Concrete Buildings, Worked examples',
        'sections': '3.2.1.2 bending, 3.2.1.4 shear, 3.3 serviceability, 4.1 anchorage',
        'limit': 'Background equations only. Adopted material/factor values are stated screening assumptions, not confirmation of the current Czech NA or a complete standards check.'},
    'capacities': capacities, 'cases': cases,
    'limits': [
        'No intermediate ground support: hypothetical simply supported full-span beam only.',
        'Nominal old model lengths are optimistic placeholders; actual supports and effective spans are unresolved after new perimeter interpretation.',
        'Direct wall self-weight only. No roof/attic/snow/wind/occupied floor/live storage/vehicle/equipment/transverse-wall/lintel support loads.',
        'A 350mm by100mm slab strip is already inside the full400mm beam selfweight. No wider slab load is assigned.',
        'Rectangular section, fully developed single tension layer assumed; no T-flange, compression-steel, arching, frame/fixity or composite old-concrete resistance credited.',
        'Shear force at supports unreduced; 100/150/200mm link spacings and cot(theta) are scenarios, not reinforcement instructions.',
        'SLS crack width, deflection/creep, torsion, lap/anchorage/node bearing, soil/settlement and interface capacity not checked.',
        'Passing a listed M/V comparison does not approve the beam, slab, support joint or house.',
    ]}
(BASE / 'results/four-rib-free-beam-screen.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print('CAPACITIES', [(c['tension_reinforcement'], round(c['MRd_kNm'], 3), round(c['VRdc_kN'], 3)) for c in capacities])
for case in cases:
    print(case['rib'], 'L=', case['old_model_axis_length_m_assumed_span'], 'MEd=', round(case['demand']['MEd_kNm'], 3),
        'VEd=', round(case['demand']['VEd_max_unreduced_kN'], 3), 'M_util=', [round(c['MEd_over_MRd'], 3) for c in case['capacity_comparisons']])

lines = ['# Rebrá 350 × 400 mm — samostatný scenár voľného nosníka', '',
    '**Podmienený kontrolný scenár, nie návrh na realizáciu.** Výška 400 mm zahŕňa 100 mm dosku. Šírka 350 mm ostáva pracovným vstupom. Posudzuje sa iba vlastná tiaž a priamo súosé modelové steny.', '',
    '## Statický model a vstupy', '',
    '- Prostý nosník bez priebežného podopretia zeminou; obidva konce sú idealizované kĺby. Skutočné uloženie na dnešnom obvode nie je preukázané.',
    '- Rozpätia 7,495 a 6,298 m sú pôvodné modelové dĺžky, optimistické pracovné náhrady za zatiaľ neznáme účinné rozpätia.',
    '- C16/20; B500; αcc = 0,85; γc = 1,50; γs = 1,15; stála tiaž γG = 1,35. Hodnoty sú prevzaté pracovné predpoklady, nie overenie aktuálnej českej národnej prílohy.',
    '- Krytie 35 mm k vonkajšiemu lícu strmeňa Ø8, spodné prúty Ø16 v jednej vrstve: d = 400 − 35 − 8 − 8 = 349 mm. Krytie/expozícia/detaily nie sú týmto schválené.',
    '- Vlastná tiaž celého prierezu = 0,350 × 0,400 × 25 = **3,500 kN/m**. Obsahuje 300 mm spodnú časť 2,625 kN/m aj pruh 100 mm dosky 0,875 kN/m. Táto časť dosky sa druhýkrát nepripočítava; širšia zaťažovacia plocha dosky sa bez podkladov nepriraďuje.',
    '- Do zaťaženia nevstupuje strecha, strop/povala, sneh, vietor, úžitkové zaťaženie, auto, zariadenia ani nepreukázaný prenos priečnych stien. R4 používa nominálne 300 mm murivo a 30 mm povrchov, vrátane pásu nad zasklením; hmotnosť nadpražia ani jeho reakcie nie sú známe.',
    '- Nezapočítava sa T-prierez, votknutie, klenbové pôsobenie muriva, tlaková výstuž ani starý betón.', '',
    '## Zaťaženie a ohyb', '',
    'Intervalové stenové zaťaženia sa integrujú presne; pod dverami a v chodbách sa nevytvára plná stena. Polohy a tiaže každého úseku sú v JSON. Únosnosť obdĺžnika: x = As·fyd/(0,8·b·fcd), z = d − 0,4x, MRd = As·fyd·z. Oceľ v oboch scenároch dosahuje medzu klzu pri prijatom medznom pretvorení betónu.', '',
    '| Spodná ťahová výstuž | As [mm²] | d [mm] | x/d | MRd [kNm] | VRd,c [kN] |', '|---|---:|---:|---:|---:|---:|']
for cap in capacities:
    lines.append(f"| {cap['tension_reinforcement'].replace('phi','Ø')} | {cap['As_mm2']:.2f} | {d:.0f} | {cap['x_over_d']:.3f} | {cap['MRd_kNm']:.2f} | {cap['VRdc_kN']:.2f} |")
lines += ['', '| Rebro | Modelové L [m] | MEd [kNm] | Najväčšie VEd [kN] | MEd/MRd, 3Ø16 | MEd/MRd, 4Ø16 |', '|---|---:|---:|---:|---:|---:|']
for case in cases:
    ds = case['demand']; cc = case['capacity_comparisons']
    lines.append(f"| {case['rib']} | {case['old_model_axis_length_m_assumed_span']:.3f} | {ds['MEd_kNm']:.2f} | {ds['VEd_max_unreduced_kN']:.2f} | {100*cc[0]['MEd_over_MRd']:.1f} % | {100*cc[1]['MEd_over_MRd']:.1f} % |")
lines += ['', '**Interpretácia:** pomer nad 100 % nevyhovuje uvedenému obdĺžnikovému nosníkovému scenáru už pri samotnej vlastnej tiaži a zahrnutých stenách. Pomer pod 100 % nepreukazuje celkové vyhovenie — chýbajú ďalšie zaťaženia, podpery, kotvenie a medzné stavy používateľnosti.', '',
    '## Šmyk — parametrické strmene, bez návrhu rozstupu', '',
    'VRd,c používa CRd,c = 0,18/γc, k = min(2; 1 + √(200/d)), ρl = As/(b·d), dolnú hranicu vmin = 0,035·k^(3/2)·√fck. Pre zvislé dvojramenné strmene Ø8: VRd,s = Asw/s·z·fyd·cotθ; VRd,max = b·z·0,6(1−fck/250)·fcd/(cotθ + tanθ). Používa sa z ≤ min(0,9d; vypočítané z). Kapacity VRd,c a VRd,s sa nesčítavajú.', '',
    '| Spodné prúty | Strmene — scenár | cotθ | min(VRd,s; VRd,max) [kN] |', '|---|---|---:|---:|']
for cap in capacities:
    for s in cap['stirrup_scenarios']:
        lines.append(f"| {cap['tension_reinforcement'].replace('phi','Ø')} | 2 ramená Ø8 / {s['spacing_mm_assumed']:.0f} mm | {s['cot_theta_assumed']:.1f} | {s['minimum_of_VRds_VRdmax_kN']:.2f} |")
lines += ['', 'VEd je reakcia pri idealizovanej podpere bez priaznivého zníženia pri priamom uložení. Rozstupy a cotθ sú výslovne scenáre. Neoverujú styk so starým betónom, zarážku, kotevnú dĺžku, torziu, uzly ani únosnosť podpery.', '',
    '## Ohybový limit rovnomerného čiarového zaťaženia', '',
    '`qEd,lim = 8·MRd/L²`. Celkové q zahŕňa vlastnú tiaž nosníka. Posledný stĺpec je iba matematický zvyšok pre rovnomerné stále zaťaženie pri γG = 1,35, po odpočítaní 3,5 kN/m vlastnej tiaže. Nie je to dovolené zaťaženie domu ani lokálnej steny.', '',
    '| L [m] | Spodné prúty | Celkové qEd,lim [kN/m] | Rovnomerné ďalšie Gk nad tiaž nosníka [kN/m] |', '|---|---|---:|---:|']
for L in [7.495, 6.298]:
    for cap in capacities:
        q = 8 * cap['MRd_kNm'] / L ** 2
        lines.append(f"| {L:.3f} | {cap['tension_reinforcement'].replace('phi','Ø')} | {q:.2f} | {q/gamma_g-q_self:.2f} |")
lines += ['', '## Čo tento scenár uzatvára', '',
    'Je to samostatný audit možnosti nosníkového prenosu pri úplnej absencii priebežnej podpory. Nenahrádza model rebier a dosky na zhutnenom podloží. Pre ten treba poznať vlastnosti a sadanie podložia; miestna hlina/piesok a slovné „zhutnené“ neurčujú tuhosť podpory. Priehyb, dotvarovanie a trhliny sa tu neoverili. Výsledky nemožno označiť za schválenie 100 mm dosky alebo celého domu.', '',
    'Metodický podklad: [JRC — Eurocode 2: Design of Concrete Buildings, Worked examples (2014)](https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf), kapitoly 3.2.1.2 a 3.2.1.4. Verejný metodický príklad nie je potvrdením dnešnej českej národnej prílohy. Konkrétne dosadené hodnoty a obmedzenia sú vyššie.', '',
    'Reprodukcia: `python3 foundation-analysis/calculations/four_rib_free_beam_screen.py`. Skript overuje rovnováhu síl a momentov aj známy výsledok rovnomerne zaťaženého prostého nosníka. Použité vstupy s SHA-256 a všetky intervaly sú v `four-rib-free-beam-screen.json`.', '']
(BASE / 'results/four-rib-free-beam-screen.md').write_text('\n'.join(lines))
