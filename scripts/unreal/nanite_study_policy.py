"""Boundaries for a disposable small-opaque Nanite experiment, never a default."""
import math
import re

MAX_MESHES = 128
TARGET_MESHES = 120
MESH_PREFIX = '/Game/Brezi/Geometry/brezi-twin/StaticMeshes/'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def door_object_ids(doors):
    return {member['sourceObjectId'] for door in doors['doors'] for member in door['members']}


def excluded_named_part(record):
    name = ' '.join(str(record.get(key, '')) for key in ('name', 'sourceId'))
    # Fixed jambs, hardware and sidelights are outside the moving-door contract.
    # Omit stove/flame effects as well: their emissive/WPO behavior is a separate study.
    return bool(re.search(r'dve[rř]|dvier|z[áa]rub|door|k[ľl]uč|klika|\bd\d+\.\d+\.|fireplace|flame', name, re.IGNORECASE))


def eligible_record(record, materials, door_ids):
    metadata = record.get('metadata') or {}
    return (bool(re.fullmatch(r'DOM_\d{5}', record['id']))
            and record['group'] == 'Interior' and record.get('enabled') is True
            and isinstance(record['triangles'], int) and not isinstance(record['triangles'], bool)
            and 0 < record['triangles'] < 512 and record.get('instances') == 1
            and record['id'] not in door_ids and not excluded_named_part(record)
            and not any(metadata.get(key) for key in
                        ('doorMotion', 'dynamicCameraOccluder', 'walkSurface', 'cameraOccluder', 'babylonCheckCollisions'))
            and bool(record['materialSlots'])
            and all(materials[slot]['alpha'] >= .999 for slot in record['materialSlots']))


def ranked_records(scene, doors):
    require(doors['sourceManifestSha256'], 'Door contract must name its source scene')
    room = next(room for room in scene['interior']['rooms'] if room['id'] == 'ROOM-1-03')
    center = room['standingPointMm']
    def rank(record):
        bounds = record['boundsMm']
        xy = [(bounds['min'][i] + bounds['max'][i]) / 2 for i in range(2)]
        distance = math.hypot(xy[0] - center['x'], xy[1] - center['y'])
        require(math.isfinite(distance), 'Nonfinite cohort distance')
        return distance, record['id']
    excluded = door_object_ids(doors)
    return sorted((r for r in scene['objects'] if eligible_record(r, scene['materials'], excluded)), key=rank)


def asset_path(identity):
    require(bool(re.fullmatch(r'DOM_\d{5}', identity)), 'Invalid study source object id')
    return MESH_PREFIX + identity + '.' + identity


def asset_file(identity):
    asset_path(identity)
    return 'Brezi/Geometry/brezi-twin/StaticMeshes/' + identity + '.uasset'


def validate_changes(before, after, identities):
    require(0 < len(identities) <= MAX_MESHES and len(identities) == len(set(identities)), 'Invalid bounded study cohort')
    allowed = {asset_file(identity) for identity in identities}
    require(before.keys() == after.keys(), 'Study Content inventory changed')
    require(allowed <= before.keys(), 'Study selected an absent asset')
    changed = {path for path in before if before[path] != after[path]}
    require(changed == allowed, 'Only every selected static mesh asset may change; map/materials/other assets are protected')
    return sorted(changed)


def validate_derived_bounds(before, after):
    """Allow only derived float32 bounds rounding; source positions stay exact."""
    require(len(before) == len(after) == 2 and all(len(row) == 3 for row in [*before, *after]), 'Invalid bounds witness')
    maximum = 0.0
    for old_row, new_row in zip(before, after):
        for old, new in zip(old_row, new_row):
            require(math.isfinite(old) and math.isfinite(new), 'Nonfinite derived bounds')
            magnitude = max(abs(old), abs(new))
            ulp = max(2.0 ** -149, 2.0 ** (math.frexp(magnitude)[1] - 24)) if magnitude else 2.0 ** -149
            error = abs(old - new)
            require(error <= min(ulp, .0002), 'Derived bounds changed beyond one float32 ULP / 0.0002 cm')
            maximum = max(maximum, error)
    return maximum
