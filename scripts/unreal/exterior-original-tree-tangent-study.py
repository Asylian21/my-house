"""R24 R2 source-only tangent supplement; immutable R1/provider inputs.

The installed UE MikkTSpace CPU library generates an explicitly DERIVED vec4
TANGENT for each unchanged original index. Incompatible per-corner frames are
rejected; original vertices/indices/normal/UV attributes are never split or
rewritten. No Unreal runtime, native asset, GPU or appearance claim.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-original-tree-tangent-study.py'
OUTPUT = ROOT/'output/unreal/exterior-original-tree-20261002-r24-tangent-r2-study'
R1 = ROOT/'output/unreal/exterior-original-tree-20261002-r24-study'
R1_SHA = 'c45ff265adc98c394a58b69167066f3445f53800d4c6d9aa7fdb7d0cc1eb1ba6'
ENGINE = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
HEADER = ENGINE/'Source/ThirdParty/MikkTSpace/inc/mikktspace.h'
LIBRARY = ENGINE/'Source/ThirdParty/MikkTSpace/lib/Mac/libMikkTSpace.a'
HARNESS = ROOT/'scripts/unreal/exterior-original-tree-mikk.c'
SPEC = importlib.util.spec_from_file_location('r24_immutable_original_study', ROOT/'scripts/unreal/exterior-original-tree-study.py')
source = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(source)
require, read, write, sha, pin, digest = (getattr(source, k) for k in ('require','read','write','sha','pin','digest'))
PARTS = ('branches','leaves','trunk')


def check_pin(row):
    p = Path(row['path']); require(p.is_file() and sha(p) == row['sha256'] and p.stat().st_size == row['bytes'], 'Consumed input pin changed: '+str(p)); return p


def expected_descriptor(r1, output, counts, tangent_bytes):
    doc = deepcopy(r1)
    for row in doc['buffers'] + doc['images']:
        row['uri'] = os.path.relpath((R1/row['uri']).resolve(), output)
    doc['buffers'].append({'uri':'derived-mikk-tangents.bin','byteLength':tangent_bytes})
    offset = 0
    for primitive, count in zip(doc['meshes'][0]['primitives'], counts):
        view = len(doc['bufferViews']); doc['bufferViews'].append({'buffer':1,'byteOffset':offset,'byteLength':count*16,'byteStride':16,'target':34962})
        index = len(doc['accessors']); doc['accessors'].append({'bufferView':view,'byteOffset':0,'componentType':5126,'count':count,'type':'VEC4'})
        primitive['attributes']['TANGENT'] = index; offset += count*16
    require(offset == tangent_bytes, 'Derived tangent byte census differs'); return doc


def validate_descriptor(doc, r1, output, counts, tangent_bytes):
    require(doc == expected_descriptor(r1, output, counts, tangent_bytes), 'R2 descriptor changed original source attributes/indices/UV/KHR/node scope or derived tangent layout')
    require(len(counts) == 3 and counts == [62772,1698569,15937], 'Exact original three vertex populations required')
    require(len(r1['buffers']) == 1 and len(doc['buffers']) == 2, 'Only one owned derived tangent buffer may be appended')
    require(len(doc['accessors']) == len(r1['accessors'])+3 and len(doc['bufferViews']) == len(r1['bufferViews'])+3, 'Only three derived tangent accessors/views may be appended')


def validate_mikk_report(report, vertices, indices):
    expected = {'mikkSucceeded':True,'sourceVertices':vertices,'sourceTriangles':indices//3,
        'cornerCallbacks':indices,'sharedIndexBinary32CornerConflicts':0,'sharedIndexHandednessConflicts':0,
        'maximumSharedIndexDifference':0,'unreferencedVertices':0,'nativeOrGpuExecuted':False}
    require(report == expected and all(type(report[k]) is type(v) for k,v in expected.items()), 'MikkTSpace per-corner frame incompatible with unchanged original indices')


def tangent_metrics(binary, doc, primitive, tangents):
    a, normals = source.accessor(doc,binary,primitive['attributes']['NORMAL'])
    require(len(tangents) == a['count']*16, 'Derived tangent byte count differs from original normals')
    signs = {'negative':0,'positive':0}; max_dot = max_length_error = 0.
    for i, normal in enumerate(normals):
        tangent = struct.unpack_from('<ffff',tangents,i*16)
        require(all(math.isfinite(v) for v in tangent) and tangent[3] in (-1.,1.), 'Derived tangent must be finite with exact signed handedness')
        dot = abs(sum(n*t for n,t in zip(normal,tangent)))
        length_error = abs(sum(t*t for t in tangent[:3])-1.)
        require(dot <= 2e-5 and length_error <= 2e-5, 'Derived tangent is not orthogonal to original normal or unit length')
        max_dot = max(max_dot,dot); max_length_error = max(max_length_error,length_error)
        signs['negative' if tangent[3] == -1. else 'positive'] += 1
    return {'validatedVertices':a['count'],'handednessCounts':signs,'maximumAbsoluteNormalDotTangent':max_dot,
        'maximumTangentSquaredLengthError':max_length_error,'sourceBasisValidationTolerance':2e-5,
        'orderedFloat32Vec4Sha256':hashlib.sha256(tangents).hexdigest(),
        'annotationExactAcrossPythonRuntimesRequired':False}


def material_proposal(r1_materials, rows):
    proposed = deepcopy(r1_materials)
    for material, row in zip(proposed,rows):
        require(material['uvSet'] == row['normalTextureTexCoord'] and material['KHRTextureTransform'] == row['KHRTextureTransform'], 'Generated tangent basis must use selected original normal-map UV+KHR transform')
        material['nativeProposal']['normalTangentBasis'] = {'source':'Owned derived MikkTSpace TANGENT vec4 from original POSITION/NORMAL/indices and selected normalTexture UV set with original KHR transform.',
            'derivedAttribute':True,'providerTangentAttribute':False,'texCoord':row['normalTextureTexCoord'],
            'KHRTextureTransform':row['KHRTextureTransform'],'orderedFloat32Vec4Sha256':row['tangentValidation']['orderedFloat32Vec4Sha256'],
            'nativeImportRecomputeTangents':False,'nativeImportRecomputeNormals':False,
            'nativeTangentBasisVerified':False,'nativeUV0UV1Verified':False,'nativeHandednessVerified':False}
    return proposed


def run_mikk(executable, original, source_bin, primitive, uv_set, transform, output, name):
    indices = [primitive['attributes'][k] for k in ('POSITION','NORMAL','TEXCOORD_'+str(uv_set))]+[primitive['indices']]
    accessors = [original['accessors'][i] for i in indices]; views = [original['bufferViews'][a['bufferView']] for a in accessors]
    widths = {5126:4,5125:4,5123:2}; components = {'VEC3':3,'VEC2':2,'SCALAR':1}
    offsets = [v.get('byteOffset',0)+a.get('byteOffset',0) for a,v in zip(accessors,views)]
    strides = [v.get('byteStride',widths[a['componentType']]*components[a['type']]) for a,v in zip(accessors,views)]
    path = output/(name+'-derived-tangents.bin'); report = output/(name+'-mikk-report.json')
    args = [str(executable),str(source_bin),str(accessors[0]['count']),str(accessors[3]['count']),*map(str,offsets),*map(str,strides),
        str(widths[accessors[3]['componentType']]),*map(str,transform['scale']),*map(str,transform['offset']),str(path),str(report)]
    result = subprocess.run(args,capture_output=True,text=True,check=False)
    require(result.returncode == 0, 'CPU MikkTSpace failed for '+name+': '+result.stderr)
    actual = read(report); validate_mikk_report(actual,accessors[0]['count'],accessors[3]['count'])
    return path, report, {'command':args,'exitCode':result.returncode,'stderr':result.stderr,'stdout':result.stdout}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=OUTPUT); args = parser.parse_args(); output = args.output.resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Fresh isolated tangent supplement output required')
    require(sha(R1/'original-tree-source-plan.json') == R1_SHA, 'Immutable R24 R1 plan changed')
    r1_plan = read(R1/'original-tree-source-plan.json'); require(r1_plan['owner'] == source.OWNER and r1_plan['status'] == 'source-only-single-original-tree-native-R22-base-pending', 'Known source-only R1 required')
    inputs = {'r1:'+p.name:pin(p) for p in sorted(R1.iterdir()) if p.is_file()}
    inputs.update(r1_plan['inputFiles'])
    for row in inputs.values(): check_pin(row)
    original_path = check_pin(r1_plan['inputFiles']['provider:tree_small_02_2k.gltf']); original = read(original_path)
    source_bin = check_pin(r1_plan['inputFiles']['provider:tree_small_02.bin']); binary = source_bin.read_bytes()
    descriptor = read(check_pin(r1_plan['candidateGLTF'])); r1_materials = read(check_pin(r1_plan['materialProposal']))
    counts = [original['accessors'][p['attributes']['POSITION']]['count'] for p in original['meshes'][0]['primitives']]
    for key,p in {'mikkHeader':HEADER,'mikkStaticLibrary':LIBRARY,'mikkHarness':HARNESS,'clang':Path('/usr/bin/clang'),'r2Producer':ROOT/OWNER}.items(): inputs[key] = pin(p)
    output.mkdir(); executable = output/'source-mikk'; command = ['/usr/bin/clang','-std=c11','-O2','-fno-fast-math','-ffp-contract=off','-I',str(HEADER.parent),str(HARNESS),str(LIBRARY),'-o',str(executable)]
    compiled = subprocess.run(command,capture_output=True,text=True,check=False); require(compiled.returncode == 0, 'Installed MikkTSpace CPU harness compilation failed: '+compiled.stderr)
    compiler_version = subprocess.run(['/usr/bin/clang','--version'],capture_output=True,text=True,check=True).stdout
    build = {'owner':OWNER,'command':command,'exitCode':0,'stdout':compiled.stdout,'stderr':compiled.stderr,'compilerVersion':compiler_version,
        'executable':pin(executable),'installedMikkHeader':pin(HEADER),'installedMikkLibrary':pin(LIBRARY),'harness':pin(HARNESS),
        'nativeOrGpuExecuted':False}
    write(output/'cpu-mikk-build-receipt.json',build)
    rows = []; chunks = []
    for i,(name,primitive,material) in enumerate(zip(PARTS,original['meshes'][0]['primitives'],r1_materials)):
        path, report, run = run_mikk(executable,original,source_bin,primitive,material['uvSet'],material['KHRTextureTransform'],output,name)
        tangents = path.read_bytes(); metrics = tangent_metrics(binary,original,primitive,tangents); chunks.append(tangents)
        rows.append({'part':name,'primitiveIndex':i,'vertices':counts[i],'triangles':read(report)['sourceTriangles'],
            'normalTextureTexCoord':material['uvSet'],'KHRTextureTransform':material['KHRTextureTransform'],
            'derivedTangents':pin(path),'perCornerMikkReport':pin(report),'cpuRun':run,'tangentValidation':metrics,
            'originalAttributesAndIndices':read(check_pin(r1_plan['decoderProof']))['parts'][i]})
    tangent_data = b''.join(chunks); tangent_path = output/'derived-mikk-tangents.bin'
    with tangent_path.open('xb') as stream: stream.write(tangent_data)
    augmented = expected_descriptor(descriptor,output,counts,len(tangent_data)); validate_descriptor(augmented,descriptor,output,counts,len(tangent_data))
    descriptor_path = output/'candidate-original-tree-derived-tangents.gltf'; write(descriptor_path,augmented)
    proposals = material_proposal(r1_materials,rows); proposal_path = output/'derived-tangent-material-proposal.json'; write(proposal_path,proposals)
    proof = {'schemaVersion':2,'owner':OWNER,'status':'PASS_SOURCE_MIKKTSPACE_ORIGINAL_INDEX_AND_ATTRIBUTE_PRESERVATION_NATIVE_PENDING',
        'algorithm':'genTangSpaceDefault from installed UE5.8 MikkTSpace static library; original indexed triangles + original normals and selected normal-map UV/KHR transform.',
        'sourceOnly':True,'sourceVertices':sum(counts),'sourceTriangles':sum(r['triangles'] for r in rows),'parts':rows,
        'derivedAttribute':'TANGENT','providerTangentsPresent':False,'originalVertexSplits':0,'originalIndexChanges':0,
        'allOriginalPositionNormalUV0UV1AndIndexBytesPreserved':True,'allOriginalMaterialKHRTransformsPreserved':True,
        'sharedIndexCornerFrameConflicts':0,'derivedTangentBuffer':pin(tangent_path),'candidateDescriptor':pin(descriptor_path),
        'cpuBuildReceipt':pin(output/'cpu-mikk-build-receipt.json'),'basisRelation':'glTF bitangent = TANGENT.w * cross(original NORMAL, derived TANGENT.xyz).',
        'sourceFloat32TangentBytesAuthoritative':True,'exactCrossRuntimeComputedMathAnnotationGate':False,
        'nativeNormalTangentReadbackAvailable':False,'nativeBasisTransformAndHandednessVerified':False,
        'nativeLimit':'Installed Python MeshDescription exposes position/UV/index readback but no reflected normal/tangent/binormal-sign getter. Preserve the frozen native module/Source/Binaries. Future import must request original+derived tangents without recomputation and prove both UV sets/source F32 corner order/three sections, while tangent/basis handedness native readback remains unavailable and actual visual shading is subsequent evidence.',
        'nativeOrGpuExecuted':False,'nativeAppearanceAccepted':False}
    proof_path = output/'derived-tangent-decoder-proof.json'; write(proof_path,proof)
    plan = {'schemaVersion':2,'owner':OWNER,'status':'source-only-original-tree-derived-tangent-supplement-native-R22-base-pending',
        'generatedAt':datetime.now(timezone.utc).isoformat(),'r1SourceStudy':pin(R1/'original-tree-source-plan.json'),'inputFiles':inputs,
        'candidateDescriptor':pin(descriptor_path),'derivedTangentBuffer':pin(tangent_path),'tangentProof':pin(proof_path),
        'materialProposal':pin(proposal_path),'cpuBuildReceipt':pin(output/'cpu-mikk-build-receipt.json'),
        'budget':deepcopy(r1_plan['budget'])|{'derivedTangentBytes':len(tangent_data),'derivedTangentAccessors':3,'providerFileChanges':0},
        'selection':deepcopy(r1_plan['selection']),'maskReview':deepcopy(r1_plan['maskReview']),
        'activeDesign':r1_plan['activeDesign'],'housePlacement':r1_plan['housePlacement'],
        'pendingNativeBase':deepcopy(r1_plan['pendingNativeBase']),
        'sourceEvidenceLimit':r1_plan['sourceEvidenceLimit'],'nativeApplied':False,'nativeAppearanceAccepted':False,
        'fullPhotorealismAccepted':False,'ecologicalFitVerified':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    plan_path = output/'original-tree-tangent-supplement-r2.json'; write(plan_path,plan)
    for row in inputs.values(): check_pin(row)
    validate_descriptor(read(descriptor_path),descriptor,output,counts,len(tangent_data))
    write(output/'source-validation-receipt-r2.json',{'schemaVersion':2,'owner':OWNER,
        'status':'PASS_SOURCE_ORIGINAL_TREE_DERIVED_TANGENTS_NO_PROVIDER_OR_R1_WRITES_NATIVE_PENDING',
        'supplement':pin(plan_path),'r1StudyFilesVerifiedUnchanged':8,'providerFilesVerifiedUnchanged':12,
        'sourceVertices':sum(counts),'sourceTriangles':2062487,'derivedTangentBytes':len(tangent_data),
        'sharedIndexCornerFrameConflicts':0,'originalVertexSplits':0,'originalIndexChanges':0,
        'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False})
    print(json.dumps({'supplement':pin(plan_path),'receipt':pin(output/'source-validation-receipt-r2.json'),'descriptor':pin(descriptor_path),
        'derivedTangentBytes':len(tangent_data),'sourceVertices':sum(counts),'sourceTriangles':2062487,'nativeApplied':False},indent=2))


if __name__ == '__main__': main()
