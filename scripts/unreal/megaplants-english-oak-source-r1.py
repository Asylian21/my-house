#!/usr/bin/env python3
"""Isolated, original-content-only ZIP extraction for the licensed oak USD pilot.

This does not start Unreal, alter USD content, synthesize textures, or train models.
The source archive remains untouched. Fresh output is required to preserve history.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path('/Users/davidzita/Downloads/tree_english_oak_forest_01_usd.zip')
ARCHIVE_SHA = 'c0c75dad3c86a4ee04f65211bd3868b45a3ba3a20f66875224691c7243b6cae9'
ARCHIVE_BYTES = 119578436
OUTPUT = ROOT / 'output/unreal/megaplants-english-oak-20261002-r1'
EXPECTED = {
    'Tree_English_Oak_01_Foliage.usd': 28828715,
    'Tree_English_Oak_Forest_01_A.usd': 116140538,
    'Tree_English_Oak_Forest_01_A_DynamicWind.json': 180702,
    'Tree_English_Oak_Forest_01_B.usd': 69097908,
    'Tree_English_Oak_Forest_01_B_DynamicWind.json': 582872,
    'Tree_English_Oak_Forest_01_C.usd': 104639363,
    'Tree_English_Oak_Forest_01_C_DynamicWind.json': 434973,
    'Tree_English_Oak_Forest_01_D.usd': 125123445,
    'Tree_English_Oak_Forest_01_D_DynamicWind.json': 92045,
}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}

def require(value, message):
    if not value:
        raise ValueError(message)

def validate_member(info):
    name = info.filename
    p = PurePosixPath(name)
    win = PureWindowsPath(name)
    mode = info.external_attr >> 16
    require(name and '\\' not in name and '\x00' not in name, 'Invalid member path')
    require(not p.is_absolute() and not win.is_absolute() and not win.drive,
            'Absolute or drive-qualified member')
    require(all(part not in ('', '.', '..') for part in name.split('/')),
            'Traversal or noncanonical member')
    require(len(p.parts) == 1 and name in EXPECTED, 'Unapproved archive member')
    require(not info.is_dir() and not stat.S_ISLNK(mode), 'Directory/symlink member')
    require(stat.S_IFMT(mode) in (0, stat.S_IFREG), 'Special-file member')
    require(not info.flag_bits & 1, 'Encrypted member')
    require(info.file_size == EXPECTED[name], 'Unexpected member size')
    return name

def extract():
    require(ARCHIVE.is_file() and not ARCHIVE.is_symlink(), 'Archive is missing/nonregular')
    before = pin(ARCHIVE)
    require(before['sha256'] == ARCHIVE_SHA and before['bytes'] == ARCHIVE_BYTES,
            'Archive does not match the authorized downloaded original')
    require(not OUTPUT.exists(), 'Fresh output is required; never overwrite history')
    with zipfile.ZipFile(ARCHIVE) as archive:
        infos = archive.infolist()
        names = [validate_member(info) for info in infos]
        require(len(names) == len(set(names)) == 9 and set(names) == set(EXPECTED),
                'Duplicate/missing members')
        require(sum(i.file_size for i in infos) == 445120561, 'Expanded byte total changed')
        source = OUTPUT / 'original'
        source.mkdir(parents=True, exist_ok=False)
        rows = []
        for info in infos:
            target = source / info.filename
            require(target.resolve().parent == source.resolve(), 'Escaping extraction target')
            # exclusive creation, streaming reads also verify each original ZIP CRC
            with archive.open(info) as reader, target.open('xb') as writer:
                count = 0
                for block in iter(lambda: reader.read(1024 * 1024), b''):
                    count += len(block)
                    require(count <= info.file_size, 'Expanded stream exceeds declared size')
                    writer.write(block)
            require(count == info.file_size, 'Truncated member')
            rows.append(dict(pin(target), archiveName=info.filename,
                             compressedBytes=info.compress_size, crc32=f'{info.CRC:08x}',
                             byteContentModified=False))
    require(pin(ARCHIVE) == before, 'Source archive changed during extraction')
    receipt = {
        'schema': 'brezi-original-licensed-english-oak-usd-source-r1',
        'owner': 'scripts/unreal/megaplants-english-oak-source-r1.py',
        'status': 'verified-original-nine-file-zip-extraction-only',
        'archive': before, 'extractor': pin(__file__), 'files': rows,
        'fileCount': len(rows), 'expandedBytes': sum(r['bytes'] for r in rows),
        'pathTraversalChecks': True, 'exclusiveFreshOutput': True,
        'allMemberCrcsCheckedByZipReader': True, 'sourceArchiveUnchanged': True,
        'licenseAuthorization': 'User explicitly approved and accepted Fab EULA; NoAI original-content operation only',
        'textureReplacementAllowed': False, 'originalContentModified': False,
        'unrealExecuted': False, 'nativeAssetsCreated': False,
        'appearanceAccepted': False, 'performanceAccepted': False,
        'fullRealismAccepted': False,
    }
    path = OUTPUT / 'source-extraction-receipt.json'
    path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'receipt': pin(path), 'fileCount': len(rows),
                      'expandedBytes': receipt['expandedBytes']}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', action='store_true', required=True)
    parser.parse_args()
    extract()
