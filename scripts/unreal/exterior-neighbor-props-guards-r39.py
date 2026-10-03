"""Closed source/before-state contract for whole original R39 props.

No UObject calls, historical generation or source optical equivalence claims.
Initial clone provenance remains separate from the later map/package delta.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-guards-r39.py'
NATIVE_OWNER = 'scripts/unreal/exterior-neighbor-props-native-r39.py'
SCHEMA = 'brezi-original-whole-neighbor-props-native-r39'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r39a'
PROJECT = CANDIDATE/'Project/BreziTwin'
STUDY = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-native-study'
PLAN = STUDY/'neighbor-props-native-plan.json'
CLONE = CANDIDATE/'neighbor-props-project-clone-r39-r1.json'
CLONE_SHA = '9fd24b04840f3b3c9cefaba048e99a9ad5be956e1f30eda0bd50725ee1ba6e97'
CLONE_SCHEMA = 'brezi-image-selected-saved-r38b-whole-props-project-clone-r39'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-image-selected-r38b-before-whole-original-neighbor-props-native-r39'
BASE = ROOT/'output/unreal/exterior-20261002-r38b'
BASE_REPORT = BASE/'soft-ground-native-report-r2.json'
BASE_REPORT_SHA = '077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9'
BASE_AUDIT = BASE/'root-native-success-byte-audit-r38b-r2.json'
BASE_AUDIT_SHA = 'a30063dc99bd3fa3fcd7d202aa77209b74f36c06bde77a47fba1c071564c5edb'
BASE_PROCESS = BASE/'soft-ground-native-r2-process.json'
BASE_PROCESS_SHA = 'c5fb163aa2989503b842d17dd464ec5baae88f881a3f543207101a7f640fa3e5'
IMAGE_DECISION = ROOT/'output/unreal/exterior-soft-ground-20261002-r38-image-base-selection-r1/root-image-base-selection-r1.json'
IMAGE_DECISION_SHA = 'b2c0ee46147b88824a2214a074c6c745d47454a118e4c151cf494f92c4304d4b'
CONTRACT = ROOT/'scripts/unreal/exterior-neighbor-props-contract-r39-draft.py'
CONTRACT_SHA = 'fdfa061438bff7bb93390d9ea6a9b0d6a758457b46647429ff33a489429581c5'
CHECKER = ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-editor-check-r29-r3.py'
CHECKER_SHA = '75a39cdaa649efdf3696b5e4ddfa9b381c3a3788c097949519e24d2e460b0e11'
BASE_NATIVE_SHA = 'e8bd757c0958f4245c4d2c2d7bbd577643b15150333ef5074047bb769f631998'
TEXTURE_FIELDS = {'srgb', 'compression_settings', 'mip_gen_settings', 'filter', 'power_of_two_mode',
    'resize_during_build_x', 'resize_during_build_y', 'lod_bias', 'max_texture_size', 'virtual_texture_streaming',
    'never_stream', 'flip_green_channel', 'address_x', 'address_y', 'do_scale_mips_for_alpha_coverage',
    'adjust_brightness', 'adjust_brightness_curve', 'adjust_vibrance', 'adjust_saturation', 'adjust_rgb_curve',
    'adjust_hue', 'adjust_min_alpha', 'adjust_max_alpha', 'chroma_key_texture'}
COUNTS = {'beforeActors': 5364, 'savedActors': 5368, 'beforeHismComponents': 2325,
    'savedHismComponents': 2329, 'beforeHismInstances': 678197, 'savedHismInstances': 678205,
    'newActors': 4, 'newInstances': 8, 'newMeshes': 4, 'newMaterialGraphs': 3,
    'newTextureObjects': 11, 'newPipelineAssets': 3, 'newPackages': 21,
    'beforeContentFiles': 4103, 'savedContentFiles': 4124, 'protectedFiles': 132,
    'beforeMaterialGraphs': 66, 'savedMaterialGraphs': 69,
    'beforeTextureObjects': 97, 'savedTextureObjects': 108, 'sourceMasterTriangles': 26601}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def checked(row):
    require(isinstance(row, dict) and set(row) == {'path', 'sha256', 'bytes'}, 'Exact file pin required')
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and not p.is_symlink() and p.is_file()
            and row == pin(p), 'Pinned original file changed: '+str(p))
    return p


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def module(name, path):
    p = checked(path) if isinstance(path, dict) else Path(path)
    spec = importlib.util.spec_from_file_location(name, p)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


require(sha(CONTRACT) == CONTRACT_SHA, 'Immutable original R39 source contract changed')
c = module('_r39_frozen_source_contract', CONTRACT)
PREFIX, TAG, MODEL_IDS, SOURCE, SOURCE_SHA = (getattr(c, k) for k in ('PREFIX', 'TAG', 'MODEL_IDS', 'SOURCE', 'SOURCE_SHA'))


def expected_binding():
    for path, wanted in ((SOURCE, SOURCE_SHA), (BASE_REPORT, BASE_REPORT_SHA), (BASE_PROCESS, BASE_PROCESS_SHA),
                         (BASE_AUDIT, BASE_AUDIT_SHA), (IMAGE_DECISION, IMAGE_DECISION_SHA), (CLONE, CLONE_SHA)):
        require(sha(path) == wanted, 'Exact selected original/source binding changed: '+str(path))
    return {'schema': SCHEMA, 'schemaVersion': 1, 'nativeOwner': NATIVE_OWNER,
        'sourceProposal': pin(SOURCE), 'selectedNativeReport': pin(BASE_REPORT),
        'selectedNativeProcess': pin(BASE_PROCESS), 'selectedCurrentByteAudit': pin(BASE_AUDIT),
        'selectedRootImageDecision': pin(IMAGE_DECISION), 'selectedNativeProcessId': 72504,
        'projectClone': pin(CLONE), 'candidateProject': str(PROJECT),
        'scope': {'wholeAssemblyRoots': 6, 'renderingSourceMeshInstances': 8, 'newHismActors': 4,
                  'changedOldActors': 0, 'oldRootsMovedRemovedOrReconstructed': 0},
        'activeOutputPromoted': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False}


def require_native_binding(binding):
    wanted = expected_binding()
    require(binding == wanted and digest(binding) == digest(wanted), 'Only the exact image-selected saved R38b/fresh R39 binding is allowed')
    return True


def validate_clone_header(clone, binding, content, protected):
    require_native_binding(binding)
    require(clone['schema'] == CLONE_SCHEMA and clone['schemaVersion'] == 1 and clone['status'] == CLONE_STATUS
        and clone['sourceNativeReport'] == binding['selectedNativeReport']
        and clone['sourceNativeProcess'] == binding['selectedNativeProcess']
        and clone['sourceCurrentByteAudit'] == binding['selectedCurrentByteAudit']
        and clone['rootImageBaseSelection'] == binding['selectedRootImageDecision']
        and clone['sourceModelProposal'] == binding['sourceProposal']
        and clone['sourceProject'] == str(BASE/'Project/BreziTwin') and clone['project'] == str(PROJECT)
        and clone['wholeOriginalPropsNativePending'] is True and clone['nativeExecuted'] is False
        and clone['activeOutputPromoted'] is False and clone['sourcePhotoPixelsEdited'] is False,
        'Only the original actual R39 clone provenance is accepted')
    require(clone['fileCount'] == len(clone['files']) == 4235 and clone['contentFiles'] == len(content) == 4103
        and clone['protectedFiles'] == len(protected) == 132, 'Exact initial 4103+132 project census required')
    expected = {'Content/'+k: v for k, v in content.items()}
    expected.update(protected)
    seen = set()
    for row in clone['files']:
        dst = Path(row['destination'])
        require(dst.is_relative_to(PROJECT) and row['independentInodes'] is True, 'Only independent own project clone rows allowed')
        rel = dst.relative_to(PROJECT).as_posix()
        require(rel in expected and rel not in seen and row['source'] == str(BASE/'Project/BreziTwin'/rel)
            and {k: row[k] for k in ('sha256', 'bytes')} == expected[rel], 'Initial clone row/source inventory differs')
        seen.add(rel)
    require(seen == set(expected), 'Initial clone row coverage differs')


def inventories(project):
    project = Path(project)
    result = {}
    for p in project.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(project)
        if rel.parts[0] not in ('Content', 'Config', 'Source', 'Binaries') and rel.as_posix() != 'BreziTwin.uproject':
            continue
        require(not p.is_symlink(), 'Symlink project files are not owned independent originals')
        result[rel.as_posix()] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    content = {p[len('Content/'):]: v for p, v in result.items() if p.startswith('Content/')}
    protected = {p: v for p, v in result.items() if not p.startswith('Content/')}
    return content, protected


def validate_clone(bundle, after=False):
    base, binding = bundle['base'], bundle['binding']
    clone = read(checked(binding['projectClone']))
    validate_clone_header(clone, binding, base['content'], base['protected'])
    # Initial rows/independence remain valid after map-save; old map size/hash
    # is compared only before native, while the typed current delta is separate.
    for row in clone['files']:
        src, dst = Path(row['source']), Path(row['destination'])
        require(src.is_file() and dst.is_file() and src.stat().st_ino != dst.stat().st_ino,
                'Each original clone file must retain an independent inode')
        require(src.stat().st_size == row['bytes'], 'Original selected source size changed')
        if not after:
            require(dst.stat().st_size == row['bytes'], 'Pristine candidate original size changed')
    current, protected = inventories(PROJECT)
    source, source_protected = inventories(base['project'])
    require(source == base['content'] and source_protected == protected == base['protected'], 'Original selected source or protected132 bytes changed')
    if not after:
        require(current == base['content'], 'Before native the candidate must be byte-exact to selected saved R38b')
    return current


def validate_base_header(report, image, terminal, audit):
    require(report['schema'] == 'brezi-image-selected-fixed-world-soft-ground-material-overlay-r38'
        and report['schemaVersion'] == 2 and report['owner'] == 'scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2.py'
        and report['status'] == 'verified-saved-image-selected-fixed-world-soft-ground-material-overlay'
        and report['project'] == str(BASE/'Project/BreziTwin')
        and report['nativeProcessId'] == 72504 and report['nativeApplied'] is True
        and report['savedMapUnloadedReloaded'] is True and report['sourceInputsUnchanged'] is True
        and report['actualCounts'] == {'savedActors': 5364, 'fullHismComponents': 2325, 'fullHismInstances': 678197,
            'scopedMaterialGraphs': 66, 'scopedTextureObjects': 97, 'contentFiles': 4103, 'protectedFiles': 132, 'newPackages': 3},
        'Actual saved R38b complete census is required')
    require(image['selectedNativeReport'] == pin(BASE_REPORT) and image['selectedCurrentByteAudit'] == pin(BASE_AUDIT)
        and image['selectedNativeProcessId'] == 72504
        and image['status'] == 'selected-saved-r38b-only-as-next-whole-original-neighbor-props-pilot-base'
        and all(image[k] is False for k in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted',
                                          'shippingVerified', 'packageVerified', 'activeOutputPromoted')),
        'Root image selection grants only the next props pilot')
    require(terminal['reportSha256'] == BASE_REPORT_SHA and terminal['sourcePinsUnchangedAfterNative'] is True
        and len(terminal['sourcePinsBeforeNative']) == 1048 and len(report['inputFiles']) == 1039
        and audit['nativeReport'] == pin(BASE_REPORT) and audit['nativeProcess'] == pin(BASE_PROCESS)
        and audit['all2325RawControls678197MembersBeforeAndSavedExact'] is True
        and audit['all64OriginalGraphsAuxUsage96TexturesExact'] is True
        and audit['actualCompiled70And73GraphsNativeMaskPropertyPolicyValidated'] is True
        and audit['freshNativeActorOrAttributeDecodeExecuted'] is False,
        'Only actual process0/current byte and stored full-scope evidence is allowed')


def complete_materials(report):
    graphs = read(checked(report['originalMaterialWitnessSaved']))
    textures = read(checked(report['originalTextureWitnessSaved']))
    built = read(checked(report['newMaterialReport']))
    require(built == report['newMaterials'] and len(graphs) == 64 and len(textures) == 96, 'Actual complete original64/96 and new receipt required')
    records = {asset: {'graph': row['graph'], 'route': row['reader'], 'aux': row['aux'],
        'usage': row['usage'], 'usageRecordedInSelectedNativeReceipt': True} for asset, row in graphs.items()}
    for row in built['materials'].values():
        require(row['asset'] not in records and row['compileErrors'] == [] and digest(row['graph']) == row['graphSha256'], 'Exact compiled new graph identity required')
        records[row['asset']] = {'graph': row['graph'], 'route': 'basic', 'aux': row['aux'], 'metadata': row['metadata'],
            'usage': None, 'usageRecordedInSelectedNativeReceipt': False}
    mask = built['maskTexture']
    require(mask['asset'] not in textures, 'The original R38 generated mask must be distinct')
    textures = {**textures, mask['asset']: mask}
    validate_material_records(records, textures)
    return records, textures


def validate_material_records(records, textures):
    require(len(records) == 66 and len(textures) == 97 and {route: sum(v['route'] == route for v in records.values())
        for route in ('basic', 'neighbor', 'tree')} == {'basic': 54, 'neighbor': 9, 'tree': 3}, 'Closed54/9/3 graph and97 texture dispatch required')
    unrecorded = []
    for asset, row in records.items():
        require(set(row['aux']) == {'samplerSources', 'worldPositionShaderOffsets'}, 'Full source sampler/world-position auxiliary record required')
        if row['usageRecordedInSelectedNativeReceipt']:
            require(set(row['usage']) == {'instancedStaticMeshes', 'nanite'} and all(type(v) is bool for v in row['usage'].values()),
                    'Actual old64 usage flags must remain available')
        else:
            require(row['usage'] is None and row['route'] == 'basic' and asset.startswith('/Game/Brezi/ContextYardSoftCoherence20261002R38/Materials/')
                    and len(row['graph']['nodes']) in (70, 73), 'Only two new R38 graphs have unrecorded usage; do not invent flags')
            unrecorded.append(asset)
    require(len(unrecorded) == 2, 'Exactly64 actual old usage records and two future observed usage records required')
    for asset, row in textures.items():
        require(row['asset'] == asset and set(row['values']) == TEXTURE_FIELDS, 'Every old Texture2D needs its24 actual visible settings')


def validate_placements(source, saved, parent):
    proposal = source['proposal']
    require(proposal['referenceSavedContextReport'] == pin(BASE_REPORT.parent.parent/'exterior-20261002-r37b/garden-yard-integration-native-report-r2.json')
        and proposal['referenceSavedContextReport']['sha256'] == 'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532', 'Original source reference must be the preserved actual R37 parent')
    require(proposal['scope']['wholeAssemblyRoots'] == len(proposal['placements']) == 6
        and proposal['scope']['renderingSourceMeshInstances'] == 8 and proposal['scope']['oldActorsModified'] == 0
        and proposal['scope']['oldRootsMovedOrRemoved'] == 0, 'Exactly six whole assemblies/eight source parts without original mutations required')
    parent_witness = read(checked(parent['savedActorWitness']))
    seen = set(); instances = 0
    for row in proposal['placements']:
        require(row['id'] not in seen and row['modelId'] in MODEL_IDS and row['uniformScale'] > 0
            and math.isfinite(row['uniformScale']) and len(row['positionCm']) == 3
            and all(math.isfinite(v) for v in [*row['positionCm'], row['yawDegrees']])
            and row['sourceOnlyPlacement'] is True and row['nativeApplied'] is False and row['nativeVisibilityVerified'] is False,
            'Exact positive uniform source placement; native contact/visibility remains pending')
        parts = source['parts'][row['modelId']]
        require(row['wholeAssemblyPartCount'] == len(parts) and row['sourceTriangleCount'] == sum(p['triangles'] for p in parts)
            and row['groundWalkingRouteUnchanged'] is True and min(row['walkingRouteClearanceCm'], row['doorCenterClearanceCm'],
            row['minimumExistingShrubContainingCircleClearanceCm']) > 0, 'Whole source assembly/declared placement clearances differ')
        if 'wallFit' in row:
            actor = row['wallFit']['referenceWallActor']
            require(saved[actor] == parent_witness[actor] and row['wallFit']['wholeAssemblyProjectedHullInsideSolidFrontWall'] is True
                and row['wallFit']['nativeWallContactVerified'] is False, 'Referenced original solid wall actor changed')
            meshes = [v['mesh'] for v in saved[actor]['components'] if v.get('mesh')]
            require(len(meshes) == 1 and meshes[0].rsplit('.', 1)[-1] == row['wallFit']['referenceWallMesh']+'_LOD0', 'Exact original wall mesh reference differs')
        else:
            require(row['courtFit']['wholeDecodedProjectedHullInsideCourt'] is True and row['courtFit']['boundaryClearanceCm'] > 0
                and row['sourceBottomContact']['nativeBottomContactOrCollisionVerified'] is False, 'Original court/source-contact evidence differs')
        seen.add(row['id']); instances += len(parts)
    require(seen == {'neighbor_prop_r39_'+str(i) for i in range(6)} and instances == 8, 'All exact source placement identities required')


def expected_counterfactual(before, added):
    require(sha(BASE_REPORT) == BASE_REPORT_SHA and digest(before) == read(BASE_REPORT)['savedActorWitnessSha256'],
            'Before must be the immutable complete selected R38 saved witness')
    require(len(before) == 5364 and len(added) == 4 and not (set(before) & set(added)), 'Four fresh props actors, all old5364 untouched')
    expected = copy.deepcopy(before)
    new_components = []
    for actor, row in added.items():
        require(actor.startswith('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.')
            and row['class'] == '/Script/BreziTwin.BreziVegetationPatch'
            and any(t.startswith(TAG) for t in row['tags']), 'Only owned props patch actors may be added')
        comps = [c for c in row['components'] if 'instanceCount' in c]
        require(len(comps) == 1 and comps[0]['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent'
            and comps[0]['instanceCount'] > 0 and comps[0]['mesh'].startswith(PREFIX+'/Geometry/StaticMeshes/'),
            'Exactly one nonempty owned whole-source HISM per new group')
        new_components.extend(comps); expected[actor] = copy.deepcopy(row)
    require(sum(c['instanceCount'] for c in new_components) == 8 and len({c['mesh'] for c in new_components}) == 4,
            'Four source part groups contain exactly eight source members')
    require(len(expected) == 5368, 'Full counterfactual census differs')
    return expected


def expected_new_packages(source):
    assets = []
    for recipe in source['recipes'].values():
        key = recipe['key']; base = PREFIX+'/'+key
        assets.append(base+'/Materials/M_'+key+'.M_'+key)
        for role, row in recipe['maps'].items():
            name = 'T_'+role+'_'+row['sha256'][:16]
            assets.append(base+'/Textures/'+name+'.'+name)
    for key, parts in source['parts'].items():
        for part in parts:
            name = key+'_part_'+str(part['nodeIndex'])
            assets.append(PREFIX+'/Geometry/StaticMeshes/'+name+'.'+name)
    assets += [PREFIX+'/Pipeline/'+name+'.'+name for name in ('Assets', 'Materials', 'Level')]
    require(len(assets) == len(set(assets)) == 21, 'Exact21 owned graph/texture/mesh/pipeline packages required')
    return sorted(assets)


def validate_content_delta(before, after, assets):
    require(len(before) == 4103 and len(after) == 4124 and set(before) <= set(after), 'Exact retained4103 plus21 Content files required')
    changed = sorted(p for p in before if before[p] != after[p])
    added = sorted(set(after)-set(before))
    wanted = sorted(a.split('.')[0].removeprefix('/Game/')+'.uasset' for a in assets)
    require(changed == ['Brezi/Maps/Brezi.umap'] and added == wanted and len(wanted) == len(set(wanted)) == 21,
            'Only original map and exact21 owned packages may differ')
    return {'onlyOriginalMapChanged': True, 'newPackages': list(assets), 'newRelativeContentFiles': added}


def load_contract(validate_current=True):
    binding = expected_binding()
    require(sha(CHECKER) == CHECKER_SHA, 'Immutable actual saved R38 checker changed')
    checker = module('_r39_selected_saved_checker', CHECKER)
    require(sha(ROOT/checker.HELPER) == BASE_NATIVE_SHA and sha(ROOT/checker.g.OWNER) == checker.GUARD_SHA,
            'Frozen actual source native/guard changed')
    r, image, terminal, audit = (read(p) for p in (BASE_REPORT, IMAGE_DECISION, BASE_PROCESS, BASE_AUDIT))
    validate_base_header(r, image, terminal, audit)
    plan, pf, parent, study = (read(checked(r[k])) for k in ('selectedPlan', 'sourcePreflight', 'baseNativeReport', 'sourceStudy'))
    require(r['selectedPlan']['sha256'] == checker.PLAN_SHA and r['sourcePreflight']['sha256'] == checker.PF_SHA,
            'Only actually consumed R38 plan/preflight required')
    checker.terminal_and_audit(r)
    summary = checker.validate_saved(r, plan, pf, parent, study)
    saved = read(checked(r['savedActorWitness']))
    raw = read(checked(r['rawInstanceControlsSaved']))
    require(digest(saved) == r['savedActorWitnessSha256'] and len(raw) == 2325
        and sum(v['instances'] for v in raw.values()) == 678197, 'Whole saved actor/raw census and hash must remain exact')
    source = c.load_source()
    for row in source['receipt']['files']:
        checked({k: row[k] for k in ('path', 'sha256', 'bytes')})
    validate_placements(source, saved, parent)
    records, textures = complete_materials(r)
    base = {'report': r, 'reportPin': pin(BASE_REPORT), 'plan': plan, 'preflight': pf,
        'parentReport': parent, 'sourceStudy': study, 'savedWitness': saved,
        'content': read(checked(r['afterContentInventory'])), 'protected': read(checked(r['protectedProjectProof'])),
        'project': Path(r['project']), 'process': terminal, 'processPin': pin(BASE_PROCESS),
        'audit': audit, 'auditPin': pin(BASE_AUDIT), 'native': checker.n, 'checker': checker,
        'rawControls': raw, 'materialRecords': records, 'textureRecords': textures, 'savedSourceSummary': summary,
        'readerPacket': {'base': {'report': parent}}}
    bundle = {'source': source, 'base': base, 'binding': binding}
    validate_clone_header(read(checked(binding['projectClone'])), binding, base['content'], base['protected'])
    if validate_current:
        validate_clone(bundle)
    return bundle
