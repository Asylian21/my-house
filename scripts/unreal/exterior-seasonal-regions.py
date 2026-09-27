"""Georeference conservative agricultural season-mask polygons; no image edits."""
from pathlib import Path
import argparse
import hashlib
import json
import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'scripts/unreal/regional-canopy/seasonal-fields.json'
ORTHO=ROOT/'output/unreal/exterior-ortho-20260926-r1/orthophoto-manifest.json'
CONTEXT=ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
BUILDINGS=ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def georeference(points,layer):
    a,b,c=layer['worldCmToUvRows'][0];d,e,f=layer['worldCmToUvRows'][1];det=a*e-b*d
    bbox=layer['bboxMetres'];national=[];world=[]
    for x,y in points:
        u,v=x/1600,y/1600
        world.append([(e*(u-c)-b*(v-f))/det,(-d*(u-c)+a*(v-f))/det])
        national.append([bbox[0]+u*(bbox[2]-bbox[0]),bbox[3]-v*(bbox[3]-bbox[1])])
    return world,national


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    output=Path(args.output).resolve()
    assert output.is_relative_to(ROOT/'output/unreal') and not output.exists(),'Fresh output required'
    source,ortho,context,buildings=map(read,[SOURCE,ORTHO,CONTEXT,BUILDINGS])
    layers={r['id']:r for r in ortho['layers']};regions=[];exclusions=[]
    for source_key,target in [('regions',regions),('exclusions',exclusions)]:
        for row in source[source_key]:
            world,national=georeference(row['polygon'],layers[row['sourceLayer']])
            shape=Polygon(world);assert shape.is_valid and shape.area>0,row['id']
            target.append({**row,'annotationPolygonPx':row['polygon'],'polygonCm':world,'polygonSjtskMetres':national,
                           'kind':'field-season-illustration' if source_key=='regions' else 'protected-nonagricultural-envelope',
                           'conservativeInsetCm':1000,'innerFeatherCm':2000,'sourceAreaM2':shape.area/10000})
    # Exact source architecture and accesses win over every manual annotation.
    for i,tri in enumerate(context['protectedTrianglesCm']):
        exclusions.append({'id':'protected_source_triangle_'+str(i),'polygonCm':tri,'bufferCm':2000,'kind':'exact-subject-road-access-exclusion'})
    for building in buildings['buildings']:
        for i,rings in enumerate(building['polygonsCm']):
            exclusions.append({'id':building['id']+'_'+str(i),'polygonCm':rings[0],'bufferCm':2000,'kind':'official-building-footprint-exclusion'})
    for region in context['regionalVegetationPolicy']['regions']:
        exclusions.append({'id':'canopy_'+region['id'],'polygonCm':region['polygonCm'],'bufferCm':1000,'kind':'ortho-canopy-group-exclusion'})
    masks=unary_union([Polygon(row['polygonCm']).buffer(-row['conservativeInsetCm']) for row in regions])
    excluded=unary_union([Polygon(row['polygonCm']).buffer(row.get('bufferCm',0)) for row in exclusions])
    source_exclusions=exclusions
    parts=list(excluded.geoms) if hasattr(excluded,'geoms') else [excluded]
    # Merge the 897 source records before rasterization. Filling enclosed holes
    # is intentionally more conservative around villages and avoids 897 full
    # atlas distance transforms. Geometry already includes its metric buffers.
    exclusions=[{'id':'merged_protected_'+str(i),'polygonCm':[list(p) for p in poly.exterior.coords[:-1]],
                 'bufferCm':0,'kind':'prebuffered-union-of-source-exclusions'} for i,poly in enumerate(parts)]
    excluded=unary_union([Polygon(row['polygonCm']) for row in exclusions])
    safe=masks.difference(excluded)
    input_files={str(p):sha(p) for p in [SOURCE,ORTHO,CONTEXT,BUILDINGS,Path(__file__)]}
    plan={'schemaVersion':1,'status':'GEOMETRIC_SEASON_MASK_PROPOSAL_CPU_COLOUR_AND_NATIVE_REVIEW_PENDING',
          'owner':'scripts/unreal/exterior-seasonal-regions.py','generatorSha256':sha(__file__),'units':'Unreal centimetres',
          'sourceOrthoManifest':str(ORTHO),'sourceOrthoManifestSha256':sha(ORTHO),'sourceCurrencyYear':2024,
          'license':ortho['license'],'interpretation':source['interpretation'],
          'seasonEvidence':'User-requested lush growing-season visual interpretation; no claim these crops or growth state were measured on the acquisition date or currently exist.',
          'regions':regions,'exclusions':exclusions,'exclusionSourceRecords':source_exclusions,'inputFiles':input_files,
          'summary':{'regionCount':len(regions),'exclusionCount':len(exclusions),'sourceExclusionRecords':len(source_exclusions),'rawUnionAreaM2':masks.area/10000,
                     'safeUnionAreaM2':safe.area/10000,'protectedIntersectionAreaM2':safe.intersection(excluded).area/10000},
          'applicationContract':['Only alter source imagery inside an explicit agricultural polygon after a 10m inset and 20m inward feather.',
             'Subtract all supplied exclusions before applying colour; provider alpha/valid UV still gate the photograph.',
             'Apply identical world-space regions to both far16km and detail2km layers, with each original affine unchanged.',
             'Additional brown/dry pixel eligibility may narrow the effect; it must not replace the geographic mask.',
             'Keep source imagery byte-exact on disk; all derivatives/prototypes isolated and labelled seasonal visual interpretation.',
             'Outside the mask or for already-green pixels/NoData, CPU output must remain byte-exact; no changes to roofs/roads/water/woodland/rocks.',
             'Only original distant-ground ortho material scope, zero through300m; no geometry/elevation/collision changes.'],
          'limits':['Manual conservative agricultural interior selection is not cadastral field mapping or surveyed current land use.',
                    'Large excluded settlement/ridge envelopes deliberately sacrifice some fields to protect buildings and rocks.',
                    'This JSON is geometry/provenance only. It does not prove visually successful seasonal colour or native performance.']}
    assert plan['summary']['protectedIntersectionAreaM2']<1e-7
    output.mkdir(parents=True)
    with (output/'seasonal-plan.json').open('x') as f:json.dump(plan,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'path':str(output/'seasonal-plan.json'),'sha256':sha(output/'seasonal-plan.json'),**plan['summary']},indent=2))


if __name__=='__main__':main()
