#!/usr/bin/env python3
"""Unbound R45 material proposal; no native import or scene mutation entry."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / 'output/unreal/exterior-clay-roof-photo-20261002-r45-unbound-proposal/clay-roof-photo-proposal.json'
PROPOSAL_SHA = 'b1c2d14be64ff121683a358d0d614e9cbfae67a411cfe45a5ae44a1faf8798ea'
SCHEMA = 'brezi-unbound-original-red-clay-roof-photo-material-proposal-r45'


def describe_proposal():
    raw = PROPOSAL.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROPOSAL_SHA:
        raise RuntimeError('Pinned R45 proposal differs')
    proposal = json.loads(raw)
    if proposal['schema'] != SCHEMA or proposal['schemaVersion'] != 1:
        raise RuntimeError('Wrong R45 source proposal')
    if any(value is not None for value in proposal['futureBinding'].values()):
        raise RuntimeError('This draft cannot consume a selected native base')
    if proposal['scope']['existingTrianglesReused'] != 332:
        raise RuntimeError('R45 whole roof/ridge scope differs')
    if proposal['materialProposal']['uv']['shaderScale'] != [0.25, -0.25]:
        raise RuntimeError('R45 metric V-reflection contract differs')
    if proposal['materialProposal']['normalChain']['reflectionSignCorrection'] != [1, -1, 1]:
        raise RuntimeError('R45 unchanged-tangent reflection correction differs')
    return proposal


def import_textures(*args, **kwargs):
    raise RuntimeError('R45 is unbound: native texture import is unavailable')


def build_materials(*args, **kwargs):
    raise RuntimeError('R45 is unbound: native material creation is unavailable')


def apply(*args, **kwargs):
    raise RuntimeError('R45 is unbound: scene mutation is unavailable')
