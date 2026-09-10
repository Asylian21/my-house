#!/usr/bin/env python3
"""Restore the immutable furniture recipe cache; no downloads or Unreal imports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from furniture_reference import CANDIDATE_SHA, STUDY, require

INPUT = Path(__file__).resolve().parent / "inputs" / "roof-surface-transfer-v3" / "candidate.json"
SIZE = 69631


def checked_file(path):
    """Read one regular, non-symlink file and validate its exact pinned bytes."""
    path = Path(path)
    require(not path.is_symlink(), "Refuse a symlink recipe: " + str(path))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode), "Recipe is not a regular file: " + str(path))
        require(info.st_size == SIZE, "Wrong recipe byte count: " + str(path))
        data = b""
        while len(data) < SIZE + 1:
            chunk = os.read(descriptor, SIZE + 1 - len(data))
            if not chunk:
                break
            data += chunk
    finally:
        os.close(descriptor)
    require(len(data) == SIZE and hashlib.sha256(data).hexdigest() == CANDIDATE_SHA,
            "Pinned furniture recipe bytes differ: " + str(path))
    return data


def publish_missing(path, data):
    """Publish a complete file by hard link, never replacing an existing inode."""
    descriptor, temporary = tempfile.mkstemp(prefix=".furniture-recipe-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
            return "restored-recipe"
        except FileExistsError:
            require(checked_file(path) == data, "Destination appeared with different recipe bytes")
            return "verified-concurrent-existing"
    finally:
        os.unlink(temporary)


def restore(destination=STUDY):
    data = checked_file(INPUT)
    destination = Path(destination)
    require(not destination.is_symlink(), "Refuse a symlink recipe directory")
    destination.mkdir(parents=True, exist_ok=True)
    require(destination.is_dir() and not destination.is_symlink(), "Recipe destination is not a regular directory")
    target = destination / "candidate.json"
    require(not target.is_symlink(), "Refuse a symlink recipe destination")
    if target.exists():
        checked_file(target)
        action = "verified-existing"
    else:
        action = publish_missing(target, data)
    checked_file(target)
    return {"status": "pinned-furniture-input-restored", "directory": str(destination.resolve()),
            "file": target.name, "action": action, "bytes": SIZE, "sha256": CANDIDATE_SHA,
            "nativeImportPerformed": False,
            "scope": "Exact historical recipe snapshot restored; photo cache and geometry export are separate prerequisites."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=STUDY)
    args = parser.parse_args()
    print(json.dumps(restore(args.destination), indent=2))
