"""Fresh decorative ecology plan without the rejected conical root collars.

All 78 original tree transforms and every non-collar detail are retained byte
for byte as JSON values. This does not hide an inherited actor or remove a
tree. The unused collar masters remain in the immutable source library.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-canopy-ecology-unflared.py'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
def require(ok,message):
    if not ok:raise ValueError(message)

def build(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    require(not output.exists(),'Use a fresh unflared ecology output')
    prior=read(source/'canopy-ecology-plan.json')
    require(prior['owner']=='scripts/unreal/exterior-canopy-ecology.py' and prior['regionId']=='village_nearest_grove',
            'The exact original grove ecology source is required')
    for path,value in prior['inputFiles'].items():require(sha(path)==value,'Original ecology source drift: '+path)
    require(prior['audit']['instances']==24851 and prior['audit']['groups']==166,'Original ecology population differs')
    geometry=read(source/'geometry-manifest.json');lookup={m['id']:m for m in geometry['meshes']}
    groups=[deepcopy(g) for g in prior['groups'] if lookup[g['meshId']]['ecologyFamily']!='flare']
    removed=[g for g in prior['groups'] if lookup[g['meshId']]['ecologyFamily']=='flare']
    rows=[{'meshId':g['meshId'],**r} for g in groups for r in g['instances']]
    expected=[r for r in prior['ecologyPlacements'] if r['ecologyFamily']!='flare']
    require(Counter(map(digest,rows))==Counter(map(digest,expected)),'Non-collar details changed')
    require(len(groups)==130 and len(rows)==24773 and len(removed)==36 and sum(len(g['instances'])for g in removed)==78,
            'Exact 78-collar removal scope differs')
    inputs=dict(prior['inputFiles'])
    inputs.update({str(ROOT/OWNER):sha(ROOT/OWNER),str(source/'canopy-ecology-plan.json'):sha(source/'canopy-ecology-plan.json'),
        str(source/'geometry-manifest.json'):sha(source/'geometry-manifest.json'),
        str(source/'material-manifest.json'):sha(source/'material-manifest.json')})
    common={k:deepcopy(prior[k]) for k in ('schemaVersion','sourceSceneSha256','sourceObjSha256','activeDesign','housePlacement')}
    common.update(owner=OWNER,generatorSha256=sha(ROOT/OWNER),inputFiles=inputs)
    geometry.update(common)
    plan=deepcopy(prior);plan.update(common,groups=groups,ecologyPlacements=rows)
    plan['sourceEcology']={'path':str(source/'canopy-ecology-plan.json'),'sha256':sha(source/'canopy-ecology-plan.json')}
    audit=plan['audit']
    audit.update(instances=len(rows),groups=len(groups),perFamily=dict(Counter(r['ecologyFamily']for r in rows)),
        groundSources=dict(Counter(r['renderedGround']['meshId']for r in rows)),
        minimumAdditionalWholeFootprintClearanceCm=min(r['clearanceCm']-r['radiusCm']for r in rows),
        allInstancesTriangleBudgetByLod=[sum(lookup[r['meshId']]['lods'][level]['triangles']for r in rows)for level in range(3)],
        remainingCanopyMorphologyIssue='Tree bases retain their original morphology; rejected authored conical collars are omitted. Native acceptance still required.',
        collarRemoval={'sourcePlan':deepcopy(plan['sourceEcology']),'removedInstances':78,'removedGroups':36,
            'retainedNonCollarRowsSha256':digest(expected),'retainedNonCollarGroupsSha256':digest(groups),
            'originalTreeTransformsChanged':False,'inheritedNativeActorsHidden':0})
    output.mkdir(parents=True)
    write(output/'geometry-manifest.json',geometry)
    plan['geometryManifest']={'path':str(output/'geometry-manifest.json'),'sha256':sha(output/'geometry-manifest.json')}
    write(output/'material-manifest.json',read(source/'material-manifest.json'))
    assets=read(source/'asset-manifest.json');assets.update(common)
    assets['sourceEcology']=deepcopy(plan['sourceEcology']);assets['scope']='Exact original non-collar details; original tree transforms preserved.'
    write(output/'asset-manifest.json',assets)
    write(output/'canopy-ecology-plan.json',plan)
    old_bundle=read(source/'canopy-ecology-manifest.json')
    bundle=deepcopy(old_bundle);bundle.update(common,sourceEcology=deepcopy(plan['sourceEcology']),audit=audit)
    bundle.update(plan={'path':str(output/'canopy-ecology-plan.json'),'sha256':sha(output/'canopy-ecology-plan.json')},
        geometryManifest=plan['geometryManifest'],materialManifest={'path':str(output/'material-manifest.json'),'sha256':sha(output/'material-manifest.json')})
    write(output/'canopy-ecology-manifest.json',bundle)
    return {'output':str(output),'instances':len(rows),'groups':len(groups),'removedNewCollars':78,
        'nativeAccepted':False,'sourceGroundChanged':False,'generatedAtUtc':datetime.now(timezone.utc).isoformat()}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(build(args.source,args.output)))
