"""Non-runnable R38 scene-overlay blueprint. No Unreal entry point or owner.

A NEW immutable final revision must validate an image-selected saved report,
fresh independent clone, current Content/protected/module closure, and all own
source pins before enabling this route. Nothing in this module selects R37b.
"""
import importlib.util
from pathlib import Path

OWNER = 'scripts/unreal/exterior-context-yard-soft-coherence-native-r38-draft.py'
SCHEMA = 'brezi-r38-soft-ground-unbound-scene-overlay-draft'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    result = importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


g = module('r38_draft_scene_guards', 'exterior-context-yard-soft-coherence-guards-r38-draft.py')
maps = module('r38_draft_scene_materials', 'exterior-context-yard-soft-coherence-materials-r38-draft.py')


def describe_draft(bundle):
    row = g.draft_contract(bundle)
    row.update(schema=SCHEMA, owner=OWNER,
        requiredFutureBindings=['actualImageSelection', 'actualSavedBaseReport', 'actualProcessZero',
            'actualCurrentContentInventory', 'actualProtectedProjectProof', 'actualNativeModuleWitness',
            'freshIndependentProjectClone', 'actualMappedSubstrateActor', 'sourcePreflightAndFinalOwner'],
        plannedDelta={'existingActorSlot0Bindings': 2, 'newMaterials': 2, 'newTechnicalMaskTextures': 1,
            'newPhotoTextures': 0, 'newMeshes': 0, 'newActors': 0, 'newRootTransforms': 0,
            'changedOriginalPackages': ['Content/Brezi/Maps/Brezi.umap'], 'newPackageAssets': sorted([*g.ASSETS.values(), g.MASK_ASSET])},
        requiredBeforeAfterReadbacks=['fullActorCounterfactualIncludingOverrideMaterials',
            'allOriginalMaterialGraphPoliciesAndTextureWitness', 'exact70And73NodeGraphs',
            'allOriginalSamplerSourceAndWorldPositionModes', 'newMaskTexturePolicy',
            'mapUnloadReloadFullWitness', 'currentContentMapOnlyPlusThreeOwnedPackages'],
        normalTangentGeometryReadbackRequired=False, geometryChanged=False,
        nativeTexelsDecoded=False, nativeGpuPixelFormatVerified=False, nativeGpuMaskContainmentVerified=False,
        nativeGpuOutsideResponseByteEquivalenceVerified=False, nativeApplied=False)
    return row


def resolve_future_targets(before, binding):
    """Pure mapping kernel only: the external final binder must authenticate it."""
    mapping = binding['selectedReport']['newActorMapping']
    g.require(g.DONOR668 in mapping and isinstance(mapping[g.DONOR668], str), 'Exact original donor668 mapping required')
    paths = {'backdrop': g.ACTOR197, 'substrate': mapping[g.DONOR668]}
    g.require(paths['substrate'] != g.DONOR668 and paths['substrate'] != g.ACTOR197, 'Relocated substrate actor identity required')
    targets = {}
    for key, actor in paths.items():
        g.require(actor in before, 'Mapped target missing from supplied witness')
        original = binding['targetWitnesses'][key]
        g.require(before[actor] == original, 'Fresh target witness differs from authenticated final binding')
        rows = [c for c in original['components'] if c['name'] == 'StaticMeshComponent0']
        g.require(len(rows) == 1 and rows[0]['class'] == '/Script/Engine.StaticMeshComponent'
            and rows[0]['materials'], 'One explicit StaticMeshComponent slot0 required')
        c = rows[0]
        targets[key] = {'actor': actor, 'component': c['name'], 'originalMesh': c['mesh'], 'originalMaterial': c['materials'][0]}
    return targets


def apply_overlay(u, context, bundle, binding):
    g.require_native_binding(binding)  # immutable draft always rejects before ANY scene/asset/API access.
    # The final binder must supply frozen-version-dispatched callbacks, not an
    # assumed generic historical graph reader (R37 taught why this matters).
    maps.preflight_enums(u)
    context['verify_current_project_and_all_source_pins']()
    before = context['full_actor_witness'](u)
    protected = context['all_original_material_texture_witness'](u)
    targets = resolve_future_targets(before, binding)
    expected = g.counterfactual_two_slots(before, targets)
    materials, material_report = maps.build_materials(u, bundle, binding,
        context['graph_snapshot'], context['shared_texture_snapshot'])
    for key, target in targets.items():
        component = context['exact_component'](u, target['actor'], target['component'])
        g.require(component.get_editor_property('static_mesh').get_path_name() == target['originalMesh']
            and component.get_material(0).get_path_name() == target['originalMaterial'], 'Actual target changed before rebind')
        component.set_material(0, materials[key])
    g.require(context['full_actor_witness'](u) == expected, 'Only declared two slot0/overrideMaterials changes allowed')
    g.require(context['all_original_material_texture_witness'](u) == protected, 'Any original graph/texture policy change rejected')
    context['save_map_unload_reload'](u)
    g.require(context['full_actor_witness'](u) == expected, 'Saved/reloaded full counterfactual differs')
    maps.verify_materials(u, bundle, binding, material_report, context['graph_snapshot'], context['shared_texture_snapshot'])
    g.require(context['all_original_material_texture_witness'](u) == protected, 'Protected saved original policies differ')
    context['verify_only_map_plus_exact_new_packages'](sorted([*g.ASSETS.values(), g.MASK_ASSET]))
    return {'schema': SCHEMA, 'owner': OWNER, 'sourceStudy': bundle['source'], 'materialReport': material_report,
        'targetBindings': targets, 'expectedCounterfactualSha256': g.digest(expected), 'nativeApplied': True,
        'nativeImportedTexelsDecoded': False, 'nativeGpuPixelFormatVerified': False,
        'nativeGpuOutsideResponseByteEquivalenceVerified': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False, 'packageVerified': False}
