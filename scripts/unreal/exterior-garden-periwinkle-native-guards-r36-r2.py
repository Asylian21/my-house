"""NEW R36 R2 provenance adapter; original source/control math is immutable.

Only the fresh candidate, typed R2 plan, and sealed failed-attempt evidence
are new. The original guard is loaded under a private module name and never
has its globals rewritten. No mesh package was saved by the failed attempt;
the future import must establish identity by full native source-corner proof.
"""
from pathlib import Path
import importlib.util
import hashlib
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-periwinkle-native-guards-r36-r2.py'
ORIGINAL_GUARD = ROOT/'scripts/unreal/exterior-garden-periwinkle-native-guards-r36.py'
ORIGINAL_GUARD_SHA = '4dd86369ae79b80e58296329b0e1b183a45c26dd7f3b609f7795e42421804138'
if hashlib.sha256(ORIGINAL_GUARD.read_bytes()).hexdigest() != ORIGINAL_GUARD_SHA:
 raise RuntimeError('Immutable R36 original source/control guard differs')
spec = importlib.util.spec_from_file_location('r36_r2_immutable_original_guard', ORIGINAL_GUARD)
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)

SCHEMA = original.SCHEMA
PREFIX = original.PREFIX
TAG = original.TAG
MODELS = original.MODELS
COUNTS = original.COUNTS
CONTACT_POLICY = original.CONTACT_POLICY
PROPOSAL = original.PROPOSAL
PROPOSAL_SHA = original.PROPOSAL_SHA
BASE = original.BASE
BASE_REPORT = original.BASE_REPORT
MATERIAL_READY = original.MATERIAL_READY
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r36b'
STUDY = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-native-study-r2'
PLAN = STUDY/'periwinkle-native-plan-r2.json'
CLONE_STATUS = original.CLONE_STATUS
CLONE_SHA = '0e62e41553e2b2e089a2d1481fb890c345e01e0261f09a503b7d1eea2512ea4f'
REPAIR_SCHEMA = 'brezi-original-periwinkle-source-geometry-identity-repair-r2'
FAILED = ROOT/'output/unreal/exterior-20261002-r36a'
FAILED_REPORT = FAILED/'garden-periwinkle-native-report.json'
FAILED_REPORT_SHA = 'c35a5c0628c6827662cfa5a8515c0c8d6e35639a12657e274e1d662d8535de53'
FAILURE_AUDIT = FAILED/'root-native-failure-byte-audit-r36a-r1.json'
FAILURE_AUDIT_SHA = '9365d3f5d7095d0d0c70d0490f5a39c7e5c2de359919c1c21fcbd360045de3d3'


def __getattr__(name):
 return getattr(original, name)


def validate_failure_header(report, terminal, raw, audit):
 original.require(report['schema'] == SCHEMA and report['schemaVersion'] == 1
  and report['owner'] == 'scripts/unreal/exterior-garden-periwinkle-native-r36.py'
  and report['status'] == 'failed' and report['nativeProcessId'] == 42780
  and report['nativeApplied'] is False
  and report['error'] == 'Exact six original source-node actor labels required'
  and report['sourceProposal'] == original.pin(PROPOSAL),
  'Exact failed original R36 source-node identity boundary required')
 original.require(raw['pid'] == 42780 and raw['code'] == 255 and raw['signal'] is None
  and raw['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
  and raw['args'][0] == str(FAILED/'Project/BreziTwin/BreziTwin.uproject')
  and '-script='+str(ROOT/report['owner']) in raw['args']
  and '-run=pythonscript' in raw['args'] and '-nullrhi' in raw['args'],
  'Actual failed R36 root process255 required')
 original.require(terminal['sourcePinsUnchangedAfterNative'] is True
  and len(terminal['sourcePinsBeforeNative']) == 560
  and terminal['reportSha256'] == FAILED_REPORT_SHA,
  'Sealed failed R36 original source closure differs')
 original.require(audit['schema'] == 'brezi-root-r36a-native-failure-current-byte-audit-r1'
  and audit['report'] == original.pin(FAILED_REPORT)
  and audit['currentProjectFiles'] == 4209 and audit['currentContentFiles'] == 4077
  and audit['protectedFiles'] == 132 and audit['all4203OriginalR34SourceFilesExact'] is True
  and audit['all4203OriginalOwnFilesExact'] is True and audit['originalMapByteExact'] is True
  and audit['sourcePinsBeforeAfterAndCurrentExact'] == 560
  and len(audit['newOwnedPartialFiles']) == 6 and audit['newOwnedPartialBytes'] == 42504571
  and all(path.startswith('Content/Brezi/GardenPeriwinkle20261002R36/Materials/')
          or path.startswith('Content/Brezi/GardenPeriwinkle20261002R36/Textures/')
          for path in audit['newOwnedPartialFiles'])
  and audit['newNativeActorOrGeometryDecodeByThisCpuAudit'] is False
  and audit['nativeApplied'] is audit['nativeAppearanceAccepted']
      is audit['fullPhotorealismAccepted'] is False and audit['partialEvidenceRetained'] is True,
  'Failed original map/source byte audit or partial-only scope differs')


def source_triangle_count_bindings(models):
 expected = dict(zip(MODELS, (11252, 9096, 5338, 4108, 3078, 1478)))
 original.require(set(models) == set(expected)
  and {key: row['triangles'] for key, row in models.items()} == expected
  and len(set(expected.values())) == 6 and sum(expected.values()) == 34350,
  'Exact six unique original whole-source triangle counts required')
 return {count: key for key, count in expected.items()}


def import_identity_evidence():
 original.require(original.sha(FAILED_REPORT) == FAILED_REPORT_SHA
  and original.sha(FAILURE_AUDIT) == FAILURE_AUDIT_SHA,
  'Immutable original failed R36 report/audit differs')
 report = original.read(FAILED_REPORT)
 terminal_path = FAILED/'garden-periwinkle-native-r1-process.json'
 raw_path = FAILED/'garden-periwinkle-native-r1.log.json'
 terminal, raw, audit = map(original.read, (terminal_path, raw_path, FAILURE_AUDIT))
 validate_failure_header(report, terminal, raw, audit)
 original.require(terminal['processFile'] == str(raw_path)
  and terminal['processFileSha256'] == original.sha(raw_path)
  and original.sha(terminal['logFile']) == terminal['logSha256']
  and terminal['controllerSha256BeforeNative'] == terminal['controllerSha256AfterNative']
      == original.sha(terminal['controller'])
  and audit['process'] == original.pin(terminal_path),
  'Frozen failed process/log/controller pins differ')
 for key in ('selectedPlan', 'sourcePreflight'):
  original.check_pin(report[key])
 for key in ('clone', 'byteHelper', 'rootAuditController', 'partialContentInventory'):
  original.check_pin(audit[key])
 return {'schema': REPAIR_SCHEMA, 'failedReport': original.pin(FAILED_REPORT),
  'failedNativeProcess': {'receipt': original.pin(terminal_path), 'raw': original.pin(raw_path),
   'log': original.pin(terminal['logFile']), 'pid': 42780, 'exitCode': 255, 'sourcePinCount': 560},
  'failedCurrentByteAudit': original.pin(FAILURE_AUDIT),
  'policy': 'SIX_UNIQUE_SOURCE_TRIANGLE_COUNTS_THEN_FULL_NATIVE_F32_P_UV0_UV1_ORDER_WINDING_IDENTITY_NO_EPSILON',
  'futureFullNativeIdentityTriangles': 34350,
  'nativeOriginalNodeLabelIdentityObserved': False,
  'persistedPartialMeshDiagnosticAvailable': False,
  'failedPartialFilesContainSavedMeshPackages': False,
  'sixMeshIdentityVerifiedByThisSourceReceipt': False,
  'sourceGeometryOrExpectedCornerOrderChanged': False,
  'originalSourceControlMathChanged': False, 'guardRelaxed': False,
  'nativeApplied': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False}


def validate_source():
 import_identity_evidence()
 return original.validate_source()


source_bundle = validate_source


def validate_clone_header(c, base, project):
 original.require(c['schema'] == SCHEMA and c['schemaVersion'] == 1 and c['status'] == CLONE_STATUS
  and c['sourceProject'] == str(base['project']) and c['project'] == str(project)
  and c['nativeBaseReport'] == base['reportPin']
  and c['sourceProposal'] is c['selectedPlan'] is c['sourcePreflight'] is None
  and c['nativeExecuted'] is False and c['nativePreflightPending'] is True
  and c['fileCount'] == len(c['files']) == 4203
  and c['contentFiles'] == 4071 and c['protectedFiles'] == 132,
  'Exact fresh R36b original R34 clone provenance required')


def validate_clone(base):
 path = CANDIDATE/'garden-periwinkle-project-clone.json'
 original.require(CLONE_SHA is not None and original.sha(path) == CLONE_SHA,
  'Actual frozen fresh R36b clone receipt is pending or differs')
 c = original.read(path)
 project = CANDIDATE/'Project/BreziTwin'
 validate_clone_header(c, base, project)
 expected = {'Content/'+key: value for key, value in base['content'].items()}
 expected.update(base['protected'])
 seen = set()
 for row in c['files']:
  source, destination = Path(row['source']), Path(row['destination'])
  relative = destination.relative_to(project).as_posix()
  original.require(relative in expected and relative not in seen
   and source == base['project']/relative and row['independentInodes'] is True
   and {key: row[key] for key in ('sha256', 'bytes')} == expected[relative]
   and source.stat().st_size == row['bytes']
   and (source.stat().st_dev, source.stat().st_ino)
       != (destination.stat().st_dev, destination.stat().st_ino),
   'Fresh initial clone membership/inode/source metadata differs')
  seen.add(relative)
 original.require(seen == set(expected), 'Exact4203 fresh initial clone membership differs')
 return original.pin(path)


def validate_plan_header(p, bundle, clone_pin, evidence):
 original.require(p['schema'] == SCHEMA and p['schemaVersion'] == 2
  and p['owner'] == 'scripts/unreal/exterior-garden-periwinkle-native-study-r36-r2.py'
  and p['nativeOwner'] == 'scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py'
  and p['status'] == 'source-ready-exact-saved-r34-whole384-original-periwinkle-native-r2-pending'
  and p['sourceProposal'] == original.pin(PROPOSAL)
  and p['baseNativeReport'] == bundle['base']['reportPin']
  and p['baseNativeProcess'] == bundle['base']['process']
  and p['baseCurrentByteAudit'] == bundle['base']['audit']
  and p['candidateOutput'] == str(CANDIDATE)
  and p['projectClone'] == clone_pin
  and p['expectedCounts'] == COUNTS and p['newGroupOrder'] == list(MODELS)
  and p['materialReadiness'] == original.pin(MATERIAL_READY)
  and p['immutableSourceGuard'] == original.pin(ORIGINAL_GUARD)
  and p['repairSchema'] == REPAIR_SCHEMA
  and p['importIdentityEvidence'] == evidence,
  'Exact actual R34/fresh R36b/native R2 source binding required')


def validate_plan(bundle=None):
 if bundle is None:
  bundle = validate_source()
 else:
  original.require(set(bundle) == {'source', 'base', 'groups', 'originalControls', 'oldFernMeasurements', 'reference'}
   and bundle['source']['proposal'] == original.read(PROPOSAL)
   and bundle['base']['reportPin'] == original.pin(BASE_REPORT)
   and bundle['reference'] is bundle['base']['bundle'],
   'Only exact already-validated actual R34 source packet may be reused')
 evidence = import_identity_evidence()
 source_triangle_count_bindings(bundle['source']['models'])
 p = original.read(PLAN)
 validate_plan_header(p, bundle, validate_clone(bundle['base']), evidence)
 original.require(p['retiredRootIds'] == [row['rootId'] for row in bundle['source']['placements']]
  and p['wholeGroupRetirements'] == bundle['source']['proposal']['retireWholeOriginalGroups']
  and p['activeDesign'] == bundle['source']['proposal']['activeDesign']
  and p['setbacksMm'] == {'street': 3000, 'east': 3000},
  'Whole384 retirement/design differs')
 original.material_readiness()
 names = {'exterior-garden-periwinkle-native-study-r36-r2.py',
  'exterior-garden-periwinkle-native-guards-r36-r2.py',
  'exterior-garden-periwinkle-native-r36-r2.py',
  'exterior-garden-periwinkle-materials-r36.py',
  'test_exterior_garden_periwinkle_native_r36_r2.py',
  'test_exterior_garden_periwinkle_native_guards_r36_r2.py'}
 original.require(set(p['ownedSources']) == names, 'Exact six R2 native sources required')
 for name, row in p['ownedSources'].items():
  original.require(Path(row['path']) == ROOT/'scripts/unreal'/name, 'Owned R2 source path differs')
  original.check_pin(row)
 for path, value in p['inputFiles'].items():
  original.require(original.sha(path) == value, 'Consumed R2 source changed')
 for key in ('nativeApplied', 'nativeExecuted', 'gpuExecuted', 'nativeAppearanceAccepted',
             'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified',
             'packageVerified', 'yardIntegrationApplied', 'surveyedPlacementVerified'):
  original.require(p[key] is False, 'R2 source plan fabricates acceptance')
 return p, bundle
