"""Adapt the frozen covered early-taper study into an explicit future native input.

Copies immutable actual meshes/recipe; re-rasterizes exported triangles at0.25mm.
All roots, crowns, source ground, old assets and camera poses are preserved.
No Unreal process is launched and no visual/performance acceptance is asserted.
"""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-lawn-tapered-integration.py'
OUTPUT=ROOT/'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'


def load_helper():
    spec=importlib.util.spec_from_file_location('explicit_taper_native',ROOT/'scripts/unreal/exterior-lawn-tapered-native.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def write(path,value,compact=False):
    with Path(path).open('x')as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=None if compact else 2,separators=(',',':')if compact else None);stream.write('\n')


def build(output=OUTPUT):
    helper=load_helper();source,library=helper.selected_source();output=Path(output).resolve()
    helper.require(output==OUTPUT and not output.exists(),'Use fresh immutable tapered integration R1 output')
    spec=importlib.util.spec_from_file_location('frozen_tapered_covered',ROOT/helper.STUDY_OWNER)
    study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
    read=study.read;sha=helper.sha
    def pin(path):return {'path':str(Path(path).resolve()),'sha256':sha(path)}
    prior=read(source['priorPlan']['path']);prior_dir=Path(source['priorPlan']['path']).parent
    views=prior_dir/'lawn-qa-views.json'
    inputs=deepcopy(source['inputFiles']);inputs.update({str(helper.STUDY/name):value for name,value in helper.STUDY_PINS.items()})
    inputs.update({str(helper.BASE):helper.BASE_SHA,str(ROOT/helper.OWNER):sha(ROOT/helper.OWNER),str(ROOT/OWNER):sha(__file__),str(views):sha(views)})
    for name,value in helper.POLICY_PINS.items():inputs[str(ROOT/'scripts/unreal'/name)]=value
    for path,value in inputs.items():helper.pinned(path,value)
    base=helper.base_module();managed=base._managed_domain(source)
    geometry=ROOT/'output/unreal/realism-20260926-r5/geometry'
    _,_,_,_,_,domain,_,_,_=study.prior.cover.managed_source(geometry,Path(source['managedLawnPlan']['path']),Path(source['derivedFrom']['path']))
    output.mkdir(parents=True)
    for old,new in [('tapered-covered.glb','lawn-natural.glb'),('lawn-tapered-prototypes.json','lawn-natural-prototypes.json'),('material-manifest.json','material-manifest.json')]:
        (output/new).write_bytes((helper.STUDY/old).read_bytes())
    _,decoded=study.r1.decode_glb(output/'lawn-natural.glb')
    measured=study.r1.measurements(decoded,source['lawnPlacements'],source,{'audit':prior['audit'],'library':read(prior_dir/'geometry-manifest.json')},domain)
    original=read(helper.STUDY/'lawn-tapered-manifest.json')['variant']['measurements']
    helper.require(measured==original,'Fresh decoded geometry/raster measurements differ from frozen selected R2')
    helper.require(measured['interiorTargetsMet']and measured['boundaryTargetsMet']and measured['withinOriginal20MTriangleBudget'],'Actual coverage/budget failed')
    physical={'status':helper.COVER_STATUS,'criteria':helper.COVER_CRITERIA,'windows':measured['physicalCoverage']}
    boundary={'status':helper.BOUNDARY_STATUS,'criteria':helper.BOUNDARY_CRITERIA,'windows':[{'boundaryId':identity,**window} for identity,window in zip(('deck','mulch'),measured['boundaryCoverage'])]}
    write(output/'lawn-coverage-receipt.json',physical);write(output/'lawn-boundary-coverage-receipt.json',boundary)
    cover_pin=pin(output/'lawn-coverage-receipt.json');boundary_pin=pin(output/'lawn-boundary-coverage-receipt.json')
    proof_pin=pin(output/'lawn-natural-prototypes.json');selected=pin(helper.STUDY/'lawn-tapered-manifest.json')
    common={'owner':OWNER,'generatorSha256':sha(__file__),'inputFiles':inputs,'status':helper.STATUS,
            'coverageReceipt':cover_pin,'boundaryCoverageReceipt':boundary_pin,'geometryProof':proof_pin,'selectedStudy':selected}
    newlibrary=deepcopy(library);newlibrary.update(common)
    for m in newlibrary['meshes']:
        m.update(glbPath=str(output/'lawn-natural.glb'),glbSha256=sha(output/'lawn-natural.glb'),
                 composition=f'{48 if m["edgeMaster"] else 64} connected five-vertex pointed leaves; early .36–.45 maximum, curved/torsioned surface, identical three LODs.')
    newlibrary['revision']='Explicit covered early taper; sealed sourceR2 geometry, source-domain and unchanged102011 placements.'
    write(output/'geometry-manifest.json',newlibrary)
    audit=deepcopy(prior['audit']);audit.update(status=helper.STATUS,physicalCoverage=physical,boundaryCoverage=boundary,
        minimumAdditionalCrownClearanceMm=measured['minimumAdditionalCrownClearanceMm'],
        allInstancesTriangleBudgetByLod=measured['allInstancesTriangleBudgetByLod'],nearTriangleBudget=measured['allInstancesTriangleBudgetByLod'][0],
        interiorCoverageTargetsMet=measured['interiorTargetsMet'],boundaryCoverageTargetsMet=measured['boundaryTargetsMet'],
        nativeVerified=False,nativeAppearanceAccepted=False,fullPhotorealismAccepted=False,performanceAccepted=False,integrationAuthorized=False,
        anatomy={'actualVerticesPerLeaf':5,'actualTrianglesPerLeaf':3,'peakTRange':[.36,.45],'rootWidthFractionRange':[.56,.62],
                 'widthRangeCm':[.32,.46],'singlePointTip':True,'tipRootColorRatio':1.12,'priorMeanPerLeafColorPreserved':True},
        retainedConservativePlacementEnvelopes=True,
        studyLimit='Source triangles prove coverage and connected leaf anatomy; actual Unreal appearance, shadows and performance require new same-view QA.')
    plan=deepcopy(source);plan.update(common,geometryManifest=pin(output/'geometry-manifest.json'),audit=audit,priorCameraManifest=pin(views))
    write(output/'lawn-natural-plan.json',plan,True);write(output/'lawn-natural-audit.json',audit)
    asset={'schema':1,**{k:plan[k]for k in ('schemaVersion','activeDesign','housePlacement','sourceSceneSha256','sourceObjSha256')},**common,
        'sources':[{'kind':'original-authored-geometry','generator':helper.STUDY_OWNER,'generatorSha256':helper.STUDY_SOURCE_SHA,
                    'selectedSource':selected,'license':'Original project asset'}],
        'scope':'Shape-only explicit managed turf; source102011 roots/yaws/scales/40groups unchanged,20master/60LOD slots only. No scan, botanical census or survey claim.',
        'nativeAppearanceAccepted':False,'performanceAccepted':False}
    write(output/'asset-manifest.json',asset)
    bundle={**common,'schemaVersion':1,'geometryManifest':plan['geometryManifest'],'plan':pin(output/'lawn-natural-plan.json'),
        'materialManifest':pin(output/'material-manifest.json'),'assetManifest':pin(output/'asset-manifest.json'),'glb':pin(output/'lawn-natural.glb'),
        'audit':audit,'integrationContract':'Explicit taper adapter/native owner. Exact frozen R2 geometry/recipe and source rows; immutable domain/legacy base only. No upright group-validation forwarding; native quality remains pending.'}
    write(output/'lawn-natural-manifest.json',bundle)
    cameras=read(views);cameras.update(owner=OWNER,generatorSha256=sha(__file__),plan=bundle['plan'],priorCameraManifest=pin(views))
    write(output/'lawn-qa-views.json',cameras)
    return {'output':str(output),'plan':bundle['plan'],'coverageReceipt':cover_pin,'boundaryCoverageReceipt':boundary_pin,
            'instances':len(plan['lawnPlacements']),'groups':len(plan['groups']),'allLodTriangleBudget':measured['allInstancesTriangleBudgetByLod'],
            'nativeAppearanceAccepted':False,'performanceAccepted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default=str(OUTPUT))
    print(json.dumps(build(**vars(parser.parse_args())),ensure_ascii=False))
