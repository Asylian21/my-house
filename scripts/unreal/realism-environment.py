"""Coherent daylight atmosphere for the isolated realism revision.

Clouds use the installed engine's volume material and the existing solar light,
so cloud shading, reflections, shadowing and the day/night transition agree.
The distant aerial haze starts beyond the house. No photographic site accuracy
or measured meteorological state is claimed.
"""
from pathlib import Path
import hashlib

OWNER_TAG = 'BreziRealism20260926'
PREFIX = '/Game/Brezi/Realism/Environment'
CLOUD_SOURCE = '/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst'
CLOUD_VALUES = {
    'layer_bottom_altitude': 1.8,
    'layer_height': 7.0,
    'tracing_start_max_distance': 200.0,
    'tracing_max_distance': 50.0,
    'view_sample_count_scale': 1.0,
    'reflection_view_sample_count_scale_value': 1.0,
    'shadow_view_sample_count_scale': 1.0,
    'shadow_reflection_view_sample_count_scale_value': 1.0,
    'use_per_sample_atmospheric_light_transmittance': True,
    'sky_light_cloud_bottom_occlusion': 0.35,
    'visible_in_real_time_sky_captures': True,
}
SUN_VALUES = {
    'cast_cloud_shadows': True,
    'cloud_shadow_strength': 0.75,
    'cloud_shadow_on_surface_strength': 1.0,
    'cloud_shadow_on_atmosphere_strength': 1.0,
    'cloud_shadow_extent': 10.0,
    'cloud_shadow_map_resolution_scale': 1.0,
    'cloud_shadow_ray_sample_count_scale': 1.0,
}
SKY_VALUES = {
    'cloud_ambient_occlusion': True,
    'cloud_ambient_occlusion_strength': 0.35,
    'cloud_ambient_occlusion_extent': 10.0,
    'cloud_ambient_occlusion_map_resolution_scale': 1.0,
    'cloud_ambient_occlusion_aperture_scale': 0.5,
}
FOG_VALUES = {
    'fog_density': 0.0015,
    'fog_height_falloff': 0.2,
    'start_distance': 6000.0,
    'fog_max_opacity': 0.7,
    'enable_volumetric_fog': False,
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def properties(component, values):
    return {key: component.get_editor_property(key) for key in values}


def set_properties(component, values):
    for key, value in values.items():
        component.set_editor_property(key, value)


def matches(actual, expected):
    return all(actual[k] == value if isinstance(value, bool)
               else abs(float(actual[k]) - value) < 1e-5 for k, value in expected.items())


def tagged(u, actors, tag, cls):
    found = [a for a in actors.get_all_level_actors() if a.actor_has_tag(tag) and isinstance(a, cls)]
    require(len(found) == 1, 'Expected exactly one ' + tag)
    return found[0]


def apply(u, actors, output):
    require(not any(a.actor_has_tag(OWNER_TAG) and isinstance(a, (u.VolumetricCloud, u.ExponentialHeightFog))
                    for a in actors.get_all_level_actors()), 'Environment already refined')
    sun = tagged(u, actors, 'BreziSun', u.DirectionalLight)
    sky = tagged(u, actors, 'BreziSky', u.SkyLight)
    sun_component = sun.get_component_by_class(u.DirectionalLightComponent)
    sky_component = sky.get_component_by_class(u.SkyLightComponent)
    require(sky_component.get_editor_property('real_time_capture'), 'Cloud environment requires real-time SkyLight capture')
    require(not any(isinstance(a, (u.VolumetricCloud, u.ExponentialHeightFog))
                    for a in actors.get_all_level_actors()), 'Inspect pre-existing cloud/fog before adding an environment')
    source = u.load_asset(CLOUD_SOURCE)
    require(source is not None, 'Installed engine cloud material missing')
    target = PREFIX + '/MI_DaylightClouds'
    require(not u.EditorAssetLibrary.does_asset_exist(target), 'Refuse to overwrite environment material')
    material = u.EditorAssetLibrary.duplicate_asset(CLOUD_SOURCE, target)
    require(material is not None, 'Could not create owned cloud instance')
    # Leave the engine's profile/noise topology intact; saved parameter values
    # are recorded for review. Atmospheric light supplies day/night radiance.
    u.MaterialEditingLibrary.update_material_instance(material)
    require(u.EditorAssetLibrary.save_loaded_asset(material), 'Cannot save cloud material')
    cloud = actors.spawn_actor_from_class(u.VolumetricCloud, u.Vector(0, 0, 0))
    fog = actors.spawn_actor_from_class(u.ExponentialHeightFog, u.Vector(0, 0, -100))
    require(cloud is not None and fog is not None, 'Environment actor creation failed')
    for actor, label in ((cloud, 'Fotoreal · vrstvená oblačnosť'), (fog, 'Fotoreal · vzdialený vzdušný opar')):
        actor.set_actor_label(label)
        actor.set_editor_property('tags', [u.Name(OWNER_TAG)])
        actor.set_folder_path('Brezi/Realism/Environment')
    cc = cloud.get_component_by_class(u.VolumetricCloudComponent)
    cc.set_material(material)
    set_properties(cc, CLOUD_VALUES)
    fc = fog.get_component_by_class(u.ExponentialHeightFogComponent)
    set_properties(fc, FOG_VALUES)
    # Black authored inscattering avoids an independent glowing fog color;
    # SkyAtmosphere supplies the actual radiance, including night mode.
    fc.set_editor_property('fog_inscattering_luminance', u.LinearColor(0, 0, 0, 1))
    fc.set_editor_property('directional_inscattering_luminance', u.LinearColor(0, 0, 0, 1))
    previous_sun = properties(sun_component, SUN_VALUES)
    previous_sky = properties(sky_component, SKY_VALUES)
    set_properties(sun_component, SUN_VALUES)
    set_properties(sky_component, SKY_VALUES)
    engine_content = Path(u.Paths.engine_content_dir()).resolve() / 'EngineSky/VolumetricClouds'
    engine_pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in engine_content.glob('*.uasset')}
    report = {'owner': 'scripts/unreal/realism-environment.py',
              'addedActors': [cloud.get_path_name(), fog.get_path_name()],
              'ownedAssets': [material.get_path_name()],
              'changedActors': [{'actor': sun.get_path_name(), 'previousProperties': previous_sun},
                                {'actor': sky.get_path_name(), 'previousProperties': previous_sky}],
              'cloudActor': cloud.get_path_name(), 'fogActor': fog.get_path_name(),
              'sunActor': sun.get_path_name(), 'skyActor': sky.get_path_name(),
              'material': material.get_path_name(), 'engineAssetPins': engine_pins,
              'source': 'Installed Unreal Engine volume material; authored fair-weather atmosphere',
              'sourceGeometryChanged': False, 'sunDirectionOrIntensityChanged': False,
              'hazeStartMetres': FOG_VALUES['start_distance'] / 100}
    report['readback'] = verify(u, actors, report)
    return report


def verify(u, actors, report):
    found = {a.get_path_name(): a for a in actors.get_all_level_actors()}
    rows = {}
    for key, cls, values in (
        ('cloudActor', u.VolumetricCloudComponent, CLOUD_VALUES),
        ('fogActor', u.ExponentialHeightFogComponent, FOG_VALUES),
        ('sunActor', u.DirectionalLightComponent, SUN_VALUES),
        ('skyActor', u.SkyLightComponent, SKY_VALUES),
    ):
        require(report[key] in found, 'Saved environment actor missing: ' + key)
        component = found[report[key]].get_component_by_class(cls)
        actual = properties(component, values)
        require(matches(actual, values), 'Saved atmosphere property mismatch: ' + key)
        rows[key] = actual
    for path in report['addedActors']:
        require(found[path].actor_has_tag(OWNER_TAG), 'Environment owner tag missing')
    cloud_material = found[report['cloudActor']].get_component_by_class(u.VolumetricCloudComponent).get_editor_property('material')
    require(cloud_material.get_path_name() == report['material'], 'Saved cloud material differs')
    rows['material'] = report['material']
    rows['status'] = 'native-atmosphere-properties-verified'
    return rows
