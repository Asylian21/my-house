"""Independent arithmetic/geometric and delivery checks, not engineering approval."""
import json, math, sys, hashlib, csv
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE/'.deps'))
from shapely.geometry import shape,Polygon,LineString,box
from shapely.ops import unary_union
from pypdf import PdfReader
R=json.loads((BASE/'results/foundation-results.json').read_text())
S=json.loads((BASE/'results/slab-results.json').read_text())
G=json.loads((BASE/'inputs/geometry.json').read_text())
N=json.loads((BASE/'inputs/supplementary-routes.json').read_text())
checks={}
assert [x['id'] for x in R['variants']]==['MIN','MEDIUM','MAX']
assert R['limits']['final_design_release'] is False
assert len(R['routes'])==17 and len(R['wall_loads'])==37
assert all(x['all_model_faces_covered'] for x in N['wall_coverage'])
assert N['geometric_connectivity']['all_connected']
assert len({r['id'] for r in R['routes']})==17
checks['17_unique_routes_cover_all_37_wall_rectangles']='PASS (geometry only)'
p=G['perimeter_axis_m'];closed=p+[p[0]]
A=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(closed,closed[1:])))/2
P=sum(math.dist(a,b) for a,b in zip(closed,closed[1:]))
# Orthogonal simple polygon offset, square/mitred corners; signed turns sum4.
manual_area=A+P*.175+4*.175**2
assert abs(manual_area-R['slab_structural_area_m2'])<1e-8
checks['structural_slab_area_independent_shoelace_offset']='PASS'
for v in R['variants']:
 assert abs(sum(v[k] for k in ['slab_m3','upper_below_slab_m3','new_lower_m3'])-v['concrete_m3'])<1e-9
 assert abs(sum(v['steel_components_kg'].values())-v['steel_kg_estimate'])<1e-7
 assert v['garage_slab_m']>=.18
checks['volume_and_steel_component_sums']='PASS'
for l in R['perimeter_load_envelopes']:
 assert abs(1.35*l['Gk_kN_m']+1.5*(l['Qk_kN_m']+l['snow_kN_m'])-l['NEd_kN_m'])<1e-9
 assert abs(l['NEd_kN_m']/(l['B_m']-2*l['e_m'])-l['qEd_kPa'])<1e-9
checks['load_combination_and_effective_width_units']='PASS'
for name in ['MIN','MEDIUM','MAX']:
 for zone in ['RESIDENTIAL','GARAGE']:
  sec=S['sections'][name+'_'+zone];case=next(c for c in sec['cases'] if c['span_m']==1)
  assert case['all_selected_checks_pass']
  assert abs(case['equilibrium_force_residual_kN'])<1e-9
assert not S['sections']['REF100']['section']['dual_mesh_fits']
assert not S['sections']['REJECT_GARAGE150']['cases'][0]['passes']['shear_conditional_direct_support_anchorage']
checks['selected_local_cases_and_expected_failures']='PASS (conditional local checks only)'
reader=PdfReader(BASE/'report.pdf');assert len(reader.pages)==10
for pg in reader.pages:
 assert abs(float(pg.mediabox.width)-595.2756)<.1 and abs(float(pg.mediabox.height)-841.8898)<.1
 assert len(pg.extract_text())>400
full='\n'.join(pg.extract_text() for pg in reader.pages)
for v in R['variants']:
 assert f'{v["concrete_m3"]:.2f}' in full
 assert f'{v["steel_kg_estimate"]:.0f}' in full
assert 'Ø10/100' in full and 'R8-R17' in full
assert 'R8-R35' not in full
checks['PDF_10_A4_pages_no_empty_pages_and_current_quantities']='PASS'
for f in ['existing-state','plan-min','plan-medium','plan-max','sections-medium','joint-medium']:
 assert (BASE/'drawings'/f'{f}.svg').is_file()
 assert (BASE/'drawings'/f'{f}.pdf').is_file()
checks['required_vector_figures']='PASS'
manifest=json.loads((BASE/'inputs/original-source-manifest.json').read_text())
for item in manifest:
 path=BASE.parent/item['path']
 assert path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],item['path']
checks['original_sources_hashes_unchanged']=f'PASS ({len(manifest)} originals)'
result={'status':'CALCULATION_AND_ARTIFACT_CHECKS_ONLY_NOT_DESIGN_APPROVAL','checks':checks,'pdf_sha256':hashlib.sha256((BASE/'report.pdf').read_bytes()).hexdigest(),'visual_review':'Run after rendering all ten final pages; see visual-review.md','engineering_unresolved':['as-built survey','site bearing/settlement/frost/groundwater','actual roof/attic/point/wind reactions','old/new interfaces and anchorage','shrinkage/joints/free slab edges','100-year durability/exposure','effective pad area at old/new overlap','final bar bending schedule and complete cost']}
(BASE/'results/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(checks,ensure_ascii=False,indent=2))
