"""Presentation lighting, preserving the canonical light positions and navigation.

UE filmic ACES remains the display transform. These are authored quality choices,
not a photometric certification. Runtime Metal captures are a separate gate.
"""

VALUES = {
    'lumen_scene_lighting_quality': 3.0,
    'lumen_scene_detail': 2.0,
    'lumen_scene_view_distance': 30000.0,
    'lumen_final_gather_quality': 4.0,
    'lumen_reflection_quality': 4.0,
    'lumen_front_layer_translucency_reflections': True,
    'lumen_max_roughness_to_trace_reflections': .6,
    'lumen_max_trace_distance': 30000.0,
    'bloom_intensity': 0.0,
    'lens_flare_intensity': 0.0,
    'film_grain_intensity': 0.0,
    'scene_fringe_intensity': 0.0,
    'motion_blur_amount': 0.0,
    'vignette_intensity': 0.0,
    'white_temp': 5500.0,
    'white_tint': 0.0,
    'auto_exposure_bias': 0.0,
    'auto_exposure_speed_up': 2.0,
    'auto_exposure_speed_down': 1.0,
    'local_exposure_highlight_contrast_scale': .85,
    'local_exposure_shadow_contrast_scale': .9,
    'local_exposure_detail_strength': 1.0,
    'ambient_occlusion_intensity': .65,
}


def selected(u, actors):
    volumes = [a for a in actors.get_all_level_actors()
               if isinstance(a, u.PostProcessVolume) and a.get_editor_property('unbound')]
    if len(volumes) != 1:
        raise RuntimeError('Expected exactly one canonical unbound exposure volume')
    return volumes[0]


def apply_lighting(actors):
    import unreal as u
    volume = selected(u, actors)
    settings = volume.get_editor_property('settings')
    before = {}
    for key, value in VALUES.items():
        before[key] = settings.get_editor_property(key)
        settings.set_editor_property('override_' + key, True)
        settings.set_editor_property(key, value)
    volume.set_editor_property('settings', settings)
    sun = [a for a in actors.get_all_level_actors() if a.actor_has_tag('BreziSun')]
    if len(sun) != 1:
        raise RuntimeError('Expected canonical sun')
    light = sun[0].get_component_by_class(u.DirectionalLightComponent)
    old_angle = float(light.get_editor_property('light_source_angle'))
    light.set_editor_property('light_source_angle', .75)
    fill_lights = []
    for actor in actors.get_all_level_actors():
        tags = {str(t) for t in actor.get_editor_property('tags')}
        if 'BreziArchvizInteriorLighting' not in tags or not any(t.startswith('AV-ROOM-1-03-ceiling-') for t in tags):
            continue
        fill = actor.get_component_by_class(u.RectLightComponent)
        prior = float(fill.get_editor_property('intensity'))
        fill.set_editor_property('temperature', 4000.0)
        fill.set_intensity(prior * .7)
        fill_lights.append({'actor':actor.get_path_name(), 'previousLumens':prior,
                            'lumens':prior*.7, 'temperatureK':4000.0})
    return {'status': 'applied', 'settings': VALUES, 'previousSettings': before,
            'sunSourceAngleDegrees': .75, 'previousSunSourceAngleDegrees': old_angle,
            'sunPositionIntensityPreserved': True, 'fixturePositionsPreserved': True,
            'livingSupplementLights':fill_lights,
            'lightingIntent':'Neutral daylight with restrained proposed ceiling fill; actual pendant/task source flux and temperature unchanged',
            'toneMapper': 'Unmodified UE filmic ACES',
            'exposure': 'Histogram with runtime camera EV100 limits -6 to 14 for day/night; stable warmup for stills',
            'nativeRenderedVerified': False}


def verify_lighting(actors, report):
    import unreal as u
    settings = selected(u, actors).get_editor_property('settings')
    for key, value in report['settings'].items():
        if not settings.get_editor_property('override_' + key) or abs(float(settings.get_editor_property(key)) - float(value)) > 1e-5:
            raise RuntimeError('Saved post-process setting differs: ' + key)
    light = next(a for a in actors.get_all_level_actors() if a.actor_has_tag('BreziSun')).get_component_by_class(u.DirectionalLightComponent)
    if abs(float(light.get_editor_property('light_source_angle')) - report['sunSourceAngleDegrees']) > 1e-5:
        raise RuntimeError('Saved sun angular diameter differs')
    by_name = {a.get_path_name():a for a in actors.get_all_level_actors()}
    for entry in report['livingSupplementLights']:
        fill = by_name[entry['actor']].get_component_by_class(u.RectLightComponent)
        if abs(float(fill.get_editor_property('intensity'))-entry['lumens'])>.001 or float(fill.get_editor_property('temperature'))!=entry['temperatureK']:
            raise RuntimeError('Saved living supplemental light differs')
    return {**report, 'status': 'saved-reloaded-validated'}
