"""Read-only source audit; writes only new four-rib audit results.

Plan overlap is not support capacity. The old upper ring is included as a
hypothetical geometric candidate only; it is not centered on the newly declared
lower concrete axes. No soil, reinforced-concrete or whole-building approval.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / '.deps'))
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

G_PATH = BASE / 'inputs/geometry.json'
A_PATH = BASE / 'inputs/client-agreed-layout.json'
W_PATH = BASE / 'results/wall-loads.csv'
G = json.loads(G_PATH.read_text())
A = json.loads(A_PATH.read_text())
assert {r['id'] for r in A['agreed_ribs']} == {'R1', 'R2', 'R4', 'R7'}
assert len(G['walls']) == 37
WIDTH = A['technical_drawing']['working_width_mm'] / 1000
assert WIDTH == .350

def strip(points, width):
    return LineString(points).buffer(width / 2, cap_style=2, join_style=2)

def rect(r):
    return box(*[r[k] for k in ['x0', 'y0', 'x1', 'y1']])

def closed(points):
    return points + [points[0]]

ribs = {r['id']: strip(r['points_m'], WIDTH) for r in A['agreed_ribs']}
rib_union = unary_union(list(ribs.values()))
upper = strip(closed(G['perimeter_axis_m']), WIDTH)
candidate = unary_union([rib_union, upper])
lower_400 = strip(closed(A['existing_perimeter']['points_m']), .400)
lower_380 = strip(closed(A['existing_perimeter']['points_m']), .380)
with W_PATH.open() as f:
    old_weights = {w['wall']: w for w in csv.DictReader(f)}

walls = []
for w in G['walls']:
    footprint = rect(w['rect_m'])
    line = LineString(w['line_m'])
    row = {
        'wall': w['id'], 'model_role': w['model_role'], 'assembly': w['assembly'],
        'length_m': line.length,
        'width_m': w['width_m'],
        'prior_study_assumed_gk_kN_m': float(old_weights[w['id']]['gk_kN_m']),
        'prior_study_assumed_Gk_kN': float(old_weights[w['id']]['Gk_kN']),
        'rib_ids_intersecting_wall_footprint': [rid for rid, p in ribs.items() if p.intersection(footprint).area > 1e-10],
    }
    for label, geom in [('four_ribs', rib_union), ('four_ribs_plus_old_upper_ring', candidate)]:
        missing_area = footprint.difference(geom).area
        row[label + '_axis_covered_m'] = line.intersection(geom).length
        row[label + '_footprint_covered_fraction'] = max(0., min(1., 1 - missing_area / footprint.area))
        row[label + '_status'] = ('FULL_PLAN_COVERAGE' if missing_area < 1e-9 else
            'NO_PLAN_COVERAGE' if footprint.intersection(geom).area < 1e-9 else 'PARTIAL_PLAN_COVERAGE')
    walls.append(row)

def total_for(label):
    counts = {k: sum(w[label + '_status'] == k for w in walls) for k in
        ['FULL_PLAN_COVERAGE', 'PARTIAL_PLAN_COVERAGE', 'NO_PLAN_COVERAGE']}
    return {'counts': counts, 'total_wall_axis_length_m': sum(w['length_m'] for w in walls),
        'axis_length_inside_candidate_footprints_m': sum(w[label + '_axis_covered_m'] for w in walls),
        'axis_length_outside_candidate_footprints_m': sum(w['length_m'] - w[label + '_axis_covered_m'] for w in walls),
        'full_walls_assumed_Gk_kN': sum(w['prior_study_assumed_Gk_kN'] for w in walls if w[label + '_status'] == 'FULL_PLAN_COVERAGE'),
        'not_fully_covered_walls_assumed_Gk_kN': sum(w['prior_study_assumed_Gk_kN'] for w in walls if w[label + '_status'] != 'FULL_PLAN_COVERAGE'),
        'note': 'Candidate footprint only; crossing a transverse rib does not support an entire wall. Gk totals are full wall weights from old study assumptions, not transferred reactions.'}

offsets = []
for name, index, coordinate in [('left', 0, 0), ('street', 0, 1), ('right', 1, 0),
    ('back', 2, 1), ('courtyard_return', 5, 1), ('inner_wing_side', 3, 0)]:
    old_axis = G['perimeter_axis_m'][index][coordinate]
    declared_axis = A['existing_perimeter']['points_m'][index][coordinate]
    signed_delta = round((old_axis - declared_axis) * 1000, 6)
    e = abs(signed_delta)
    offsets.append({'side': name, 'old_upper_axis_minus_declared_lower_axis_mm': signed_delta,
        'upper_width_mm': 350,
        'straight_strip_overlap_lower400_mm': max(0., 375 - e),
        'straight_strip_overlap_lower380_mm': max(0., 365 - e),
        'note': 'Cross-section interval overlap only. Uniform rectangular widths, common elevation, exact coordinate alignment assumed. No capacity or bearing-pressure model.'})

equipment = []
for item in G['heavy_items']:
    if 'rect_m' in item:
        footprint = rect(item['rect_m'])
    elif isinstance(item.get('center_m'), dict):
        footprint = Point(item['center_m']['x'], item['center_m']['y']).buffer(item['outer_diameter_m'] / 2)
    else:
        continue
    equipment.append({'id': item['id'], 'distance_footprint_to_four_ribs_m': footprint.distance(rib_union),
        'distance_footprint_to_four_ribs_plus_old_upper_ring_m': footprint.distance(candidate),
        'intersects_four_ribs': footprint.intersects(rib_union),
        'note': 'Envelope geometry, not actual feet/contact patches or proof that a separate footing is mandatory.'})

old_load_screen = []
for b in [.8, .4, .38]:
    old_load_screen.append({'B_m': b, 'old_Nser_kN_m': 48.57, 'old_NEd_kN_m': 68.,
        'Nser_over_B_kPa': 48.57 / b, 'NEd_over_B_kPa': 68 / b,
        'reference_Rd_kPa': 150., 'NEd_over_B_over_reference_Rd': 68 / b / 150,
        'note': 'Original project load only; centered uniform strip screen; excludes footing/overburden weights and new model loads. Not current soil or current eccentric interface verification.'})

out = {
    'status': 'GEOMETRY_AND_ORIGINAL_LOAD_SCREEN_ONLY_NOT_STRUCTURAL_APPROVAL',
    'source_sha256': {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [G_PATH, A_PATH, W_PATH]},
    'working_rib_width_m': WIDTH,
    'method': 'Shapely exact polygon intersections without added tolerance; flat rib ends, mitred perimeter corners. Full wall includes the stored wall rectangle, not later additional finish layers. Only 37 internal wall segments are counted; facade L/NN2 and piers discussed separately.',
    'summary': {label: total_for(label) for label in ['four_ribs', 'four_ribs_plus_old_upper_ring']},
    'walls': walls, 'perimeter_cross_section_offsets': offsets, 'heavy_item_envelopes': equipment,
    'ribs_plan_contact_with_declared_lower400': [
        {'rib': rid, 'intersection_area_m2': p.intersection(lower_400).area,
         'minimum_plan_gap_m': p.distance(lower_400)} for rid, p in ribs.items()],
    'original_project_centered_load_screen': old_load_screen,
    'no_current_approval': ['No actual wall/roof/attic reactions', 'No confirmed new rib ground support',
        'No surveyed concrete registration', 'No verified soil properties or compaction',
        'No actual 100mm slab reinforcement/cover/support model',
        'No proof of old/new concrete joint or load transfer across offset perimeter'],
}
(BASE / 'results/four-rib-load-path-audit.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
with (BASE / 'results/four-rib-wall-coverage.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(walls[0]))
    writer.writeheader()
    writer.writerows(walls)
print(json.dumps(out['summary'], ensure_ascii=False, indent=2))
print('Uncovered LOAD_BEARING:', [(w['wall'], w['length_m']) for w in walls if w['model_role'] == 'LOAD_BEARING' and w['four_ribs_plus_old_upper_ring_status'] != 'FULL_PLAN_COVERAGE'])
print('Perimeter offsets:', offsets)
print('Equipment:', equipment)
print('Rib / declared lower400 contact:', out['ribs_plan_contact_with_declared_lower400'])
