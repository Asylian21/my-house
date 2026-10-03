"""CPU descriptor-only preparation. Root invokes this after source freeze."""
import importlib.util
import json
from pathlib import Path

path=Path(__file__).with_name('megaplants-english-oak-pilot-guards-r1.py')
spec=importlib.util.spec_from_file_location('oak_original_guard',path)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def main():
    plan,base=g.validate_plan();clone,expected=g.validate_clone(plan,base)
    descriptor=g.PROJECT/'BreziTwin.uproject';before=g.pin(descriptor)
    data=g.read(descriptor);data['Plugins'].append(g.PLUGIN)
    descriptor.write_text(json.dumps(data,indent=2)+'\n')
    for key,value in expected.items():
        if key!='BreziTwin.uproject':
            p=g.PROJECT/key;g.require(g.sha(p)==value['sha256'] and p.stat().st_size==value['bytes'],
                                    'Descriptor stage changed another original file')
    record={'schema':g.SCHEMA,'owner':'scripts/unreal/megaplants-english-oak-pilot-stage-r1.py',
            'status':'verified-own-descriptor-only-usd-plugin-stage-native-pending',
            'selectedPlan':g.pin(g.PLAN),'initialRootClone':plan['initialRootClone'],
            'descriptorBefore':before,'descriptorAfter':g.pin(descriptor),
            'pluginAddition':g.PLUGIN,'originalFileCount':4218,
            'other4217OriginalFilesByteExact':True,'savedR32SourceUnchanged':True,
            'nativeExecuted':False,'appearanceAccepted':False,'performanceAccepted':False}
    receipt=g.OUTPUT/'oak-usd-project-preparation.json';g.write(receipt,record)
    g.validate_clone(plan,base,prepared=True)
    print(json.dumps({'preparation':g.pin(receipt)}))

if __name__=='__main__':main()
