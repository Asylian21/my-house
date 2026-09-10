#!/usr/bin/env python3
"""Restore the pinned TV oak input cache. Never overwrite a different file."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.request
from urllib.parse import urlparse

import oak_reference as ref

INPUTS = Path(__file__).resolve().parent / "inputs"


def checked(data, spec, label):
    ref.require(len(data) == spec["size"], "Wrong byte count: " + label)
    ref.require(hashlib.sha256(data).hexdigest() == spec["sha256"], "Wrong SHA-256: " + label)
    if "md5" in spec:
        ref.require(hashlib.md5(data).hexdigest() == spec["md5"], "Wrong source MD5: " + label)
        ref.require(ref.jpeg_size(data) == (4096, 4096), "Wrong photograph dimensions: " + label)
    return data


def publish_missing(path, data):
    """Publish a complete verified file atomically without replacing any existing inode."""
    descriptor, temporary = tempfile.mkstemp(prefix=".oak-download-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            ref.require(not path.is_symlink() and path.is_file() and path.read_bytes() == data,
                        "Destination appeared with different data: " + str(path))
    finally:
        os.unlink(temporary)


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        parsed = urlparse(new_url)
        ref.require(parsed.scheme == "https" and parsed.netloc == "dl.polyhaven.org",
                    "Photograph redirect left its pinned HTTPS origin")
        return super().redirect_request(request, fp, code, message, headers, new_url)


def download(spec):
    parsed = urlparse(spec["url"])
    ref.require(parsed.scheme == "https" and parsed.netloc == "dl.polyhaven.org",
                "Photograph URL is not the pinned HTTPS origin")
    request = urllib.request.Request(spec["url"], headers={"User-Agent": "BreziTwin-pinned-material-fetch/1"})
    deadline = time.monotonic() + 180
    with urllib.request.build_opener(SameOriginRedirect()).open(request, timeout=45) as response:
        ref.require(response.status == 200, "Photograph download did not return HTTP 200")
        length = response.headers.get("Content-Length")
        ref.require(length is None or int(length) == spec["size"], "Unexpected download length")
        data = bytearray()
        while len(data) <= spec["size"]:
            ref.require(time.monotonic() < deadline, "Photograph download exceeded its deadline")
            chunk = response.read1(min(65536, spec["size"] + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        return checked(bytes(data), spec, spec["url"])


def restore(destination=ref.STUDY, downloader=download):
    destination = Path(destination)
    ref.require(not destination.is_symlink(), "Refuse a symlink cache directory")
    destination.mkdir(parents=True, exist_ok=True)
    snapshots = {}
    for name, expected in ref.FILES.items():
        data = (INPUTS / name).read_bytes()
        ref.require(hashlib.sha256(data).hexdigest() == expected, "Pinned recipe changed: " + name)
        snapshots[name] = data
    candidate = json.loads(snapshots["candidate.json"])
    maps = candidate["maps"]
    ref.require(set(maps) == set(ref.MAP_HASHES), "Photograph role set changed")
    planned = []
    for name, data in snapshots.items():
        planned.append((name, {"size": len(data), "sha256": ref.FILES[name]}, data))
    for role, expected in ref.MAP_HASHES.items():
        spec = maps[role]
        path = Path(spec["path"])
        ref.require(path.parent.as_posix() == "output/unreal/wood-study" and spec["sha256"] == expected,
                    "Photograph identity/path changed: " + role)
        planned.append((path.name, spec, None))
    # Check the entire existing destination before downloading or writing anything.
    for name, spec, _ in planned:
        target = destination / name
        ref.require(not target.is_symlink(), "Refuse a symlink input: " + name)
        if target.exists():
            ref.require(target.is_file(), "Input is not a regular file: " + name)
            checked(target.read_bytes(), spec, name)
    results = []
    for name, spec, recipe in planned:
        target = destination / name
        action = "verified-existing"
        if not target.exists():
            data = recipe if recipe is not None else downloader(spec)
            checked(data, spec, name)
            publish_missing(target, data)
            action = "restored-recipe" if recipe is not None else "downloaded-verified"
        checked(target.read_bytes(), spec, name)
        results.append({"file": name, "action": action, "sha256": spec["sha256"], "bytes": spec["size"]})
    return {"status": "pinned-oak-inputs-restored", "directory": str(destination.resolve()),
            "files": results, "nativeImportPerformed": False,
            "scope": "Restored immutable input snapshots and verified photographs; no native asset or rendering claim."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ref.STUDY)
    args = parser.parse_args()
    print(json.dumps(restore(args.destination), indent=2))
