#!/usr/bin/env python3
"""List actual archived IoStore packages using the selected candidate UnrealPak."""
from pathlib import Path
import argparse
import json
import sys
import uuid

sys.dont_write_bytecode = True
import native_process as H
import phase_runner as F


def execute(archive_receipt):
    ref = F.path(archive_receipt)
    archive = F.read(ref)
    H.need(archive['mode'] == 'archive' and archive['status'] == F.STATUS
           and archive['nativeExitCode'] == 0 and not archive['errors']
           and not archive['remainingOwned'], 'Archive did not close cleanly')
    engine, project, run_root = F.paths(archive['engineRoot'], archive['projectRoot'], archive['runRoot'])
    H.need(ref.parent.is_relative_to(run_root), 'Foreign archive receipt')
    app = F.path(archive['appPath'])
    H.need(app.is_relative_to(ref.parent / 'archive'), 'Foreign archived app')
    pak = app / 'Contents/UE/BreziTwin/Content/Paks'
    before = {str(pak / name): digest for name, digest in F.inventory(pak).items()}
    out = ref.parent / ('listing-' + uuid.uuid4().hex)
    executable = engine / 'Engine/Binaries/Mac/UnrealPak'
    csv = out / 'listing.csv'
    cfg = {
        'mode': 'listing', 'directory': str(out), 'engineRoot': str(engine), 'projectRoot': str(project),
        'argv': [str(executable), '-ListContainer=' + str(pak / 'BreziTwin-Mac.utoc'),
                 '-Csv=' + str(csv), '-unattended', '-notraceserver',
                 '-UserDir=' + str(out / 'user') + '/', '-abslog=' + str(out / 'unrealpak.log')],
        'cwd': str(executable.parent), 'environmentSet': {'TMPDIR': str(out / 'tmp') + '/'},
        'environmentUnset': [], 'deadlineSeconds': 60, 'maxShaderWorkers': 0,
    }
    H.reject_conflicts(H.processes(), cfg)
    out.mkdir()
    for name in ('tmp', 'user'):
        (out / name).mkdir()
    pins = {str(p): H.sha(p) for p in (ref, Path(__file__).resolve(), Path(H.__file__), Path(F.__file__), executable)}
    H.save(out / 'pins-before.json', pins)
    H.save(out / 'command.json', cfg)
    native = H.supervise(cfg, out)
    H.save(out / 'process.json', native)
    H.need(native['nativeExitCode'] == 0 and not native['errors'] and not native['remainingOwned'], 'Native listing failed')
    after = {str(pak / name): digest for name, digest in F.inventory(pak).items()}
    H.need(before == after, 'Archived containers changed during listing')
    F.check(pins)
    receipt = {
        'status': 'actual-iostore-listing-exited-zero-and-drained', 'argv': cfg['argv'],
        'exitCode': native['nativeExitCode'], 'nativePid': native['pid'],
        'stdoutPath': str(out / 'stdout.log'), 'stdoutSha256': H.sha(out / 'stdout.log'),
        'outputSha256': H.sha(csv), 'inputsBefore': before, 'inputsAfter': after, 'hostInputs': pins,
    }
    H.save(out / 'listing-receipt.json', receipt)
    return {'status': receipt['status'], 'listingCsv': str(csv), 'listingReceipt': str(out / 'listing-receipt.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-receipt', required=True)
    try:
        print(json.dumps(execute(**vars(parser.parse_args())), indent=2))
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(1)
