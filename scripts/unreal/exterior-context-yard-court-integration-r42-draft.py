"""Unbound R42 court consumer draft; no producer replay or UObject mutations.

The frozen source already contains the sole visual overlay. A future immutable
consumer must bind the actual selected R43 saved report and image decision.
This draft deliberately has no runnable native entry point.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-court-integration-r42-draft.py'
SCHEMA = 'brezi-frozen-first-court-unbound-integration-draft-r42'
SOURCE = ROOT / 'output/unreal/exterior-context-yard-court-20261002-r42-source-study/court-source-plan.json'
SOURCE_SHA = 'd30576916b3c78a709b2ec0a84576470cfdb6be537305391475a882e65dd27a4'
GEOMETRY_SHA = '5a1d244f830479830ecddbed965365940bf4e3e18b57c2953c57d5084d81f9f9'
PROPOSAL = ROOT / 'output/unreal/exterior-context-yard-court-20261002-r42-unbound-integration-draft/integration-proposal.json'
SELECTED_NATIVE_BASE = None
SELECTED_ROOT_IMAGE_DECISION = None
SELECTED_PROJECT_CLONE = None
NATIVE_PLAN = None
NATIVE_REPORT = None


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def read(path):
    return json.loads(Path(path).read_text())


def checked(row):
    require(pin(row['path']) == row, 'Frozen court source file changed')
    return Path(row['path'])


def load_source():
    """Read existing frozen arrays only; never imports the original producer."""
    require(pin(SOURCE)['sha256'] == SOURCE_SHA, 'Frozen R42 source plan changed')
    plan = read(SOURCE)
    require(plan['schema'] == 'brezi-first-authored-neighbor-court-source-r42'
            and plan['schemaVersion'] == 1, 'Exact frozen court source required')
    require(plan['geometry']['sha256'] == GEOMETRY_SHA, 'Exact frozen geometry required')
    geometry = read(checked(plan['geometry']))
    require(geometry['id'] == 'yard_court_r42_BU_572063_visual_overlay'
            and len(geometry['verticesCm']) == len(geometry['normals']) == len(geometry['uv0']) == 366
            and len(geometry['indices']) == 1998, 'Sole 366-vertex/666-triangle source overlay required')
    require(geometry['collision'] == 'NoCollision' and geometry['navigation'] is False,
            'New visual-only NoCollision overlay required')
    for row in plan['materialProposal']['originalMaps'].values():
        checked(row)
    return {'sourcePlan': plan, 'geometry': geometry,
            'materialProposal': plan['materialProposal']}


def describe_draft():
    return read(PROPOSAL)


def import_geometry(*args, **kwargs):
    raise RuntimeError('Unbound R42 draft: actual R43 image-selected saved base and fresh clone are pending')


def build_materials(*args, **kwargs):
    raise RuntimeError('Unbound R42 draft: compatible saved material/texture readback must be bound in a new consumer')


def apply(*args, **kwargs):
    raise RuntimeError('Unbound R42 draft has no native mutation entry point')
