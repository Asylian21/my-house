"""Rendering-only defaults shared by fresh imports and cloned-map migration.

Density scaling is restricted to small, collisionless detail. Tree crowns,
privacy hedges, architectural actors, material bindings and instance transforms
are never changed here. Profile-specific Lumen overrides live in the runtime.
"""

LUMEN_DEFAULTS = {
    'lumen_scene_lighting_quality': 1.0,
    'lumen_scene_detail': 1.0,
    'lumen_scene_view_distance': 10000.0,
    'lumen_final_gather_quality': 1.0,
    'lumen_reflection_quality': 1.0,
    'lumen_max_trace_distance': 10000.0,
}

DETAIL_FLAGS = {
    'cast_shadow': False,
    'visible_in_ray_tracing': False,
    'affect_distance_field_lighting': False,
    'enable_density_scaling': True,
}
LAWN_CULL_CM = (1500, 2500)
RURAL_DETAIL_CULL_CM = (6000, 8000)


def detail_policy(tags, label):
    """Select explicit owned detail classes, never by a shared mesh/material.

    Rural windbreak shrubs reuse the ragweed mesh at a larger scale. The owned
    plants_* spatial groups are small detail; windbreak groups remain intact.
    """
    tags = set(tags)
    if 'BreziPhotorealLawn' in tags:
        return {'kind': 'lawn', 'flags': dict(DETAIL_FLAGS), 'cullCm': LAWN_CULL_CM}
    if 'BreziLawnDetail' in tags:
        return {'kind': 'legacy-lawn', 'flags': dict(DETAIL_FLAGS), 'cullCm': (600, 1200)}
    if 'BreziRural20260923' in tags and label.startswith('plants_'):
        return {'kind': 'rural-detail', 'flags': dict(DETAIL_FLAGS), 'cullCm': RURAL_DETAIL_CULL_CM}
    return None


def density_owner(component):
    owner = component.get_owner()
    if owner is None or owner.get_editor_property('instances') != component:
        raise RuntimeError('Density scaling requires the owned vegetation HISM')
    return owner


def read_detail_flag(component, name):
    if name == 'enable_density_scaling':
        return bool(density_owner(component).get_detail_density_scaling())
    return bool(component.get_editor_property(name))


def set_detail_flag(component, name, value):
    if name == 'enable_density_scaling':
        if not density_owner(component).set_detail_density_scaling(value):
            raise RuntimeError('Native density scaling rejected a non-collisionless owned HISM')
    else:
        component.set_editor_property(name, value)


def apply_detail(component, policy):
    component.set_cull_distances(*policy['cullCm'])
    for name, value in policy['flags'].items():
        set_detail_flag(component, name, value)


def verify_detail(component, policy):
    for name, value in policy['flags'].items():
        if read_detail_flag(component, name) != value:
            raise RuntimeError('Detail rendering policy differs: ' + name)
    distances = tuple(component.get_editor_property(name) for name in
                      ('instance_start_cull_distance', 'instance_end_cull_distance'))
    if distances != tuple(policy['cullCm']):
        raise RuntimeError('Detail cull distances differ')
