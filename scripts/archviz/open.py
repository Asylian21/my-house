"""Configure this interactive Blender process without overwriting user preferences."""

import bpy

scene = bpy.context.scene
for obj in scene.objects:
    if obj.hide_render:
        obj.hide_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.overlay.show_overlays = False
            area.spaces.active.region_3d.view_camera_zoom = 20
try:
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "METAL"
    preferences.refresh_devices()
    for device in preferences.devices:
        device.use = device.type == "METAL"
    scene.cycles.device = "GPU" if any(d.use for d in preferences.devices) else "CPU"
except (TypeError, RuntimeError):
    scene.cycles.device = "CPU"
print("ARCHVIZ_INTERACTIVE", scene.cycles.device, flush=True)
