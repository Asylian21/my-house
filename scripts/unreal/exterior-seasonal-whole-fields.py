"""Replace rejected interior patches with three traced whole-field units."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json

from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'scripts/unreal/regional-canopy/seasonal-whole-fields.json'
BASE=ROOT/'output/unreal/exterior-seasonal-regions-20260927-r2/seasonal-plan.json'
HELPER=ROOT/'scripts/unreal/exterior-seasonal-regions.py'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output).resolve();assert out.is_relative_to(ROOT/'output/unreal') and not out.exists()
    base,source=map(read,[BASE,SOURCE]);ortho=read(base['sourceOrthoManifest']);layers={row['id']:row for row in ortho['layers']}
    spec=importlib.util.spec_from_file_location('frozen_field_affine',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    def transform(row,kind):
        world,national=helper.georeference(row['polygon'],layers[row['sourceLayer']])
        polygon=Polygon(world);assert polygon.is_valid and polygon.area>0,row['id']
        return {**row,'kind':kind,'polygonCm':world,'polygonSjtskMetres':national,'annotationPolygonPx':row['polygon'],'sourceAreaM2':polygon.area/10000}
    regions=[transform(row,'field-season-illustration') for row in source['regions']]
    exclusions=[row for row in base['exclusionSourceRecords'] if row['id']!='village_brezi_conservative_envelope']
    exclusions += [transform(source['settlementRefinement'],'refined-settlement-envelope')]
    exclusions += [transform(row,'existing-field-management-strip') for row in source['additionalExclusions']]
    protect=unary_union([Polygon(row['polygonCm']).buffer(row.get('bufferCm',0)) for row in exclusions])
    pieces=list(protect.geoms) if hasattr(protect,'geoms') else [protect]
    merged=[{'id':'wholefield_protected_'+str(i),'polygonCm':[list(p) for p in shape.exterior.coords[:-1]],'bufferCm':0,'kind':'prebuffered-union-of-source-exclusions'} for i,shape in enumerate(pieces)]
    protect=unary_union([Polygon(row['polygonCm']) for row in merged])
    masks=unary_union([Polygon(row['polygonCm']).buffer(-row['conservativeInsetCm']) for row in regions]);safe=masks.difference(protect)
    unchanged=[row for row in base['exclusionSourceRecords'] if row['id']!='village_brezi_conservative_envelope']
    assert all(row in exclusions for row in unchanged),'An exact source exclusion changed'
    plan=copy.deepcopy(base)
    plan.update(owner='scripts/unreal/exterior-seasonal-whole-fields.py',generatorSha256=sha(__file__),interpretation=source['interpretation'],
                regions=regions,exclusions=merged,exclusionSourceRecords=exclusions)
    plan['derivedFrom']={'path':str(BASE),'sha256':sha(BASE),'reason':'R2 conservative interior polygons and oversized village envelope produced arbitrary green patches within uniform fields in actual CPU previews. R3 traces three whole physical field contours.',
                         'retainedExactExclusionRecords':len(unchanged),'refinedManualEnvelopeId':'village_brezi_conservative_envelope'}
    plan['inputFiles'].update({str(p):sha(p) for p in [SOURCE,BASE,HELPER,Path(__file__)]})
    plan['summary']={'regionCount':len(regions),'exclusionCount':len(merged),'sourceExclusionRecords':len(exclusions),
                     'rawUnionAreaM2':masks.area/10000,'safeUnionAreaM2':safe.area/10000,'protectedIntersectionAreaM2':safe.intersection(protect).area/10000}
    plan['applicationContract'][0]='Alter only three traced whole agricultural units with5m inward safety inset and10m inward feather; exact exclusions always win.'
    plan['limits'][0]='Physical field boundaries are visually traced with approximately1–3m uncertainty, not cadastral borders or current crop mapping.'
    assert plan['summary']['protectedIntersectionAreaM2']<1e-7
    assert all(sha(p)==h for p,h in plan['inputFiles'].items()),'Input drift'
    out.mkdir(parents=True)
    with (out/'seasonal-plan.json').open('x') as f:json.dump(plan,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'path':str(out/'seasonal-plan.json'),'sha256':sha(out/'seasonal-plan.json'),**plan['summary']},indent=2))


if __name__=='__main__':main()
