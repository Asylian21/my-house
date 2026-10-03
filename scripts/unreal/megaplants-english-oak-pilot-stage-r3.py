"""CPU descriptor-only preparation. Root invokes this after source freeze."""
import importlib.util
import json
from pathlib import Path

path=Path(__file__).with_name('megaplants-english-oak-pilot-guards-r3.py')
spec=importlib.util.spec_from_file_location('oak_original_guard',path)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def main():
    plan,base=g.validate_plan();clone,expected=g.validate_clone(plan,base)
    descriptor=g.PROJECT/'BreziTwin.uproject';before=g.pin(g.BASE/'Project/BreziTwin/BreziTwin.uproject')
    data=g.read(descriptor);data['Plugins'].append(g.PLUGIN)
    descriptor.write_text(json.dumps(data,indent=2)+'\n')
    startup=g.PROJECT/'Config/DefaultEngine.ini'
    startup_before=g.pin(g.BASE/'Project/BreziTwin/Config/DefaultEngine.ini')
    startup.write_text(g.startup_config(startup.read_text()))
    for key,value in expected.items():
        if key not in {'BreziTwin.uproject','Config/DefaultEngine.ini'}:
            p=g.PROJECT/key;g.require(g.sha(p)==value['sha256'] and p.stat().st_size==value['bytes'],
                                    'Descriptor stage changed another original file')
    record={'schema':g.SCHEMA,'owner':'scripts/unreal/megaplants-english-oak-pilot-stage-r3.py',
            'status':'verified-own-usd-plugin-and-startup-assembly-only-stage-native-pending-r3',
            'selectedPlan':g.pin(g.PLAN),'initialRootClone':plan['initialRootClone'],
            'descriptorBefore':before,'descriptorAfter':g.pin(descriptor),
            'startupConfigBefore':startup_before,'startupConfigAfter':g.pin(startup),
            'startupConfigDelta':plan['startupConfigDelta'],
            'pluginAddition':g.PLUGIN,'originalFileCount':4218,
            'other4216OriginalFilesByteExact':True,'savedR32SourceUnchanged':True,
            'nativeExecuted':False,'appearanceAccepted':False,'performanceAccepted':False}
    receipt=g.OUTPUT/'oak-usd-project-preparation-r3.json';g.write(receipt,record)
    g.validate_clone(plan,base,prepared=True)
    print(json.dumps({'preparation':g.pin(receipt)}))

if __name__=='__main__':main()
