// Offline UE 5.8 trace analysis. Run only after native frame measurements finish.
import {spawn} from 'node:child_process';
import {createReadStream} from 'node:fs';
import {readFile, writeFile, mkdir, realpath, lstat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {requireIdleApp} from './app-launch.mjs';

const root = resolve(import.meta.dirname, '../..');
assert(process.argv.length === 3 || process.argv.length === 4,
  'Usage: node scripts/unreal/performance-insights.mjs <run-artifact-directory> [--analysis-name=insights-analysis-r2]');
const option = process.argv[3] ?? '--analysis-name=insights-analysis';
assert(option.startsWith('--analysis-name='), 'Unknown analysis option');
const analysisName = option.slice('--analysis-name='.length);
assert(/^insights-analysis(?:-[a-z0-9][a-z0-9-]*)?$/.test(analysisName), 'Invalid analysis directory name');
const run = await realpath(resolve(process.argv[2]));
const directory = resolve(run, analysisName);
const engine = await realpath(resolve(process.env.UNREAL_ENGINE_ROOT ?? '/Users/Shared/Epic Games/UE_5.8'));
const executable = resolve(engine, 'Engine/Binaries/Mac/UnrealInsights.app/Contents/MacOS/UnrealInsights');
const trace = resolve(run, 'runtime.utrace'), runtimeFile = resolve(run, 'runtime.json');
const scope = 'Whole-trace CPU/GPU scope statistics, including startup, warmup and capture. '
  + 'This instrumented trace is separate from uncapped frame benchmarks; these aggregates are not steady-state FPS or frame latency.';
const noCpuThread = '__BreziNoCPUThread__';
const complete = 'Application is closing because it was started with the AutoQuit parameter and session analysis is complete.';
const save = (name, value) => writeFile(resolve(directory, name), JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
async function digest(path) {
  const hash = createHash('sha256');
  for await (const bytes of createReadStream(path)) hash.update(bytes);
  return hash.digest('hex');
}
async function regular(path) {
  const stat = await lstat(path);
  assert(stat.isFile() && !stat.isSymbolicLink() && stat.size > 0, 'Expected nonempty regular file: ' + path);
  return stat;
}
function quote(path) {
  return '"' + path.replaceAll('\\', '\\\\').replaceAll('"', '\\"') + '"';
}
// Threads/timers use UE's UTF-8 CSV writer (quoted cells and doubled quotes).
function csv(text) {
  const rows = []; let row = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; ++i) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; ++i; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"' && !cell.length) quoted = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') ++i;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += c;
  }
  assert(!quoted, 'Unclosed CSV quote');
  if (cell.length || row.length) { row.push(cell); rows.push(row); }
  return rows;
}
async function table(name, columns, statistics = false) {
  const path = resolve(directory, name); await regular(path);
  const text = (await readFile(path, 'utf8')).replace(/^\uFEFF/, '');
  // TraceServices::Table2Csv replaces commas in names with spaces and writes
  // names literally, including quote characters; it is not the UTF-8 CSV writer.
  const rows = statistics ? text.trimEnd().split(/\r?\n/).map(line => line.split(',')) : csv(text);
  assert.deepEqual(rows.shift(), columns, 'Unexpected columns: ' + name);
  assert(rows.length > 0, 'No data rows: ' + name);
  return rows.map(values => {
    assert.equal(values.length, columns.length, 'Malformed row: ' + name);
    return Object.fromEntries(columns.map((column, i) => [column, values[i]]));
  });
}
function statistics(rows) {
  for (const row of rows) {
    assert(row.Name, 'Empty statistics timer name');
    for (const field of Object.keys(row).filter(key => key !== 'Name')) {
      assert(row[field].trim() !== '' && Number.isFinite(Number(row[field])) && Number(row[field]) >= 0,
        'Invalid statistics value: ' + field + '=' + row[field]);
      row[field] = Number(row[field]);
    }
    assert(Number.isSafeInteger(row.Count) && row.Count > 0, 'Invalid timer instance count');
  }
  assert(rows.some(row => row.Incl > 0), 'No positive timer durations');
  return rows;
}

await requireIdleApp();
for (const path of [run, executable]) assert(!/["\r\n\t]/.test(path), 'Unsupported command-line path character');
await Promise.all([regular(trace), regular(runtimeFile), regular(executable)]);
await mkdir(directory); // EEXIST is intentional: never replace an earlier analysis.
const report = {schemaVersion: 1, status: 'analysis-failed', scope, run, directory, executable, startedAt: new Date().toISOString()};
try {
  const runtime = JSON.parse(await readFile(runtimeFile, 'utf8'));
  assert.equal(runtime.status, 'capture-complete', 'Input run did not complete');
  assert.equal(runtime.rhi, 'Metal', 'Expected the native Metal run');
  report.inputs = {[trace]: await digest(trace), [runtimeFile]: await digest(runtimeFile),
    [executable]: await digest(executable), [resolve(import.meta.filename)]: await digest(import.meta.filename)};
  const qaFile = resolve(run, 'qa.json');
  try {
    const qa = JSON.parse(await readFile(qaFile, 'utf8'));
    if (qa.runtimeReportSha256) assert.equal(qa.runtimeReportSha256, report.inputs[runtimeFile], 'Producer runtime report hash differs');
    report.inputs[qaFile] = await digest(qaFile);
    const cleanExit = qa.outcome?.code === 0 && qa.outcome?.signal === null;
    report.producer = {qaStatus: qa.status, outcome: qa.outcome, cleanExit,
      traceWithoutWorkerThread: qa.args?.includes('-notracethreading') === true};
    if (!cleanExit) report.scope += ` Producer did not exit cleanly (${qa.outcome?.signal ?? qa.outcome?.code ?? 'unknown'}); `
      + 'the recovered trace may be incomplete and supplies attribution only, not valid FPS evidence.';
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    report.producer = {cleanExit: null, status: 'producer-outcome-unavailable'};
  }
  report.runtime = {recordedAtUtc: runtime.recordedAtUtc, processId: runtime.processId,
    buildConfiguration: runtime.buildConfiguration, activeView: runtime.activeView, renderSettings: runtime.renderSettings};
  const names = ['threads.csv', 'timers.csv', 'statistics.csv', 'gpu-statistics.csv'];
  const files = names.map(name => resolve(directory, name));
  const response = resolve(directory, 'export.rsp'), logFile = resolve(directory, 'analysis.log');
  const commands = [
    `TimingInsights.ExportThreads ${quote(files[0])}`,
    `TimingInsights.ExportTimers ${quote(files[1])} -ShowFormatInTimerNames=false`,
    `TimingInsights.ExportTimerStatistics ${quote(files[2])} -sortBy=TotalInclusiveTime -sortOrder=Descending`,
    // UE5.8 applies this filter only to CPU threads, always including GPU queues.
    `TimingInsights.ExportTimerStatistics ${quote(files[3])} -threads=${noCpuThread} -sortBy=TotalInclusiveTime -sortOrder=Descending`,
  ];
  await writeFile(response, commands.join('\n') + '\n', {flag: 'wx'});
  const args = [`-OpenTraceFile=${trace}`, `-ABSLOG=${logFile}`, '-AutoQuit', '-NoUI',
    `-ExecOnAnalysisCompleteCmd=@=${response}`, '-log'];
  report.args = args; report.commands = commands; report.responseSha256 = await digest(response);
  await requireIdleApp();
  const chunks = [];
  const processStartedAt = new Date().toISOString();
  const outcome = await new Promise((accept, reject) => {
    const child = spawn(executable, args, {cwd: root, stdio: ['ignore', 'pipe', 'pipe']});
    let timedOut = false, killTimer;
    const timer = setTimeout(() => {
      timedOut = true; child.kill('SIGTERM');
      killTimer = setTimeout(() => child.kill('SIGKILL'), 10000);
    }, 15 * 60 * 1000);
    for (const stream of [child.stdout, child.stderr]) stream.on('data', chunk => chunks.push(chunk));
    const clear = () => { clearTimeout(timer); clearTimeout(killTimer); };
    child.once('error', error => { clear(); reject(error); });
    child.once('close', (code, signal) => { clear(); accept({pid: child.pid, code, signal, timedOut}); });
  });
  await writeFile(resolve(directory, 'process.log'), Buffer.concat(chunks), {flag: 'wx'});
  report.process = {command: executable, args, cwd: root, startedAt: processStartedAt,
    endedAt: new Date().toISOString(), ...outcome};
  await save('process.json', report.process);
  assert.equal(outcome.code, 0); assert.equal(outcome.signal, null); assert.equal(outcome.timedOut, false);
  const log = await readFile(logFile, 'utf8');
  const markerPatterns = [
    /Analysis has completed in [^\r\n]+/,
    /Executing commands on analysis completed\.\.\./,
    /Commands executed in [^\r\n]+/,
  ];
  report.completionMarkers = markerPatterns.map(pattern => {
    const match = log.match(pattern); assert(match, 'Missing analysis marker: ' + pattern); return match[0];
  });
  assert(log.includes(complete), 'Missing successful AutoQuit marker');
  report.completionMarkers.push(complete);
  assert(!/Failed to (?:export|open the response|write the CSV)|session analysis failed to start|Unknown Cmd Param|Unsupported sortBy/i.test(log),
    'Insights reported an export/analysis failure');
  const warnings = log.split(/\r?\n/).filter(line => /\b(?:Warning|Error):/.test(line));
  const gpuWarnings = warnings.filter(line => /\[GpuProfiler\]/.test(line));
  const incompleteWarnings = warnings.filter(line => /pending RHI command lists|force-closing|truncat|corrupt|lost events/i.test(line));
  report.analysisWarnings = warnings;
  report.timingIntegrity = {gpuTimingsUsable: gpuWarnings.length === 0,
    gpuWarningCount: gpuWarnings.length, incompleteWarningCount: incompleteWarnings.length,
    producerCleanExit: report.producer.cleanExit,
    status: gpuWarnings.length || incompleteWarnings.length || report.producer.cleanExit !== true
      ? 'qualified-attribution-only' : 'whole-trace-export-without-detected-integrity-warnings'};
  if (gpuWarnings.length) report.scope += ' The analyzer reports GPU timeline ordering/timestamp problems; '
    + 'GPU exports demonstrate recorded scopes only and their numeric durations must not be used as timing evidence.';
  if (incompleteWarnings.length) report.scope += ' The analyzer also reports incomplete/force-closed trace data.';
  const threads = await table(names[0], ['Id', 'Name', 'Group']);
  const timers = await table(names[1], ['Id', 'Type', 'Name', 'File', 'Line']);
  assert(!threads.some(row => row.Name === noCpuThread), 'GPU-only CPU exclusion name collided');
  assert(threads.some(row => row.Name === 'GameThread'), 'Missing GameThread track');
  assert(timers.some(row => row.Type === 'CPU') && timers.some(row => row.Type === 'GPU'), 'Missing CPU/GPU timers');
  const columns = ['Name', 'Count', 'C.Avg', 'Incl', 'I.Min', 'I.Max', 'I.Avg', 'I.Med', 'Excl', 'E.Min', 'E.Max', 'E.Avg', 'E.Med'];
  const all = statistics(await table(names[2], columns, true));
  const gpu = statistics(await table(names[3], columns, true));
  const types = new Map();
  for (const timer of timers) {
    const name = timer.Name.replaceAll(',', ' ');
    if (!types.has(name)) types.set(name, new Set());
    types.get(name).add(timer.Type);
  }
  const cpu = all.filter(row => types.get(row.Name)?.size === 1 && types.get(row.Name).has('CPU'));
  assert(cpu.some(row => row.Incl > 0), 'No unambiguous CPU timer duration was exported');
  assert(gpu.every(row => types.get(row.Name)?.has('GPU')), 'GPU-only statistics contain an unknown/non-GPU timer');
  for (const [i, count] of [[0, threads.length], [1, timers.length]]) {
    const marker = `Exported ${count} ${i ? 'timers' : 'threads'} to file in`;
    assert(log.includes(marker), 'Exported row count differs from log: ' + names[i]);
    report.completionMarkers.push(marker);
  }
  for (const file of files) {
    const marker = `("${file}").`;
    const line = log.split(/\r?\n/).find(line => line.includes('Exported ') && line.endsWith(marker));
    assert(line, 'Missing export completion for ' + file);
    report.completionMarkers.push(line);
  }
  for (const [path, hash] of Object.entries(report.inputs)) assert.equal(await digest(path), hash, 'Analysis input changed: ' + path);
  report.artifacts = Object.fromEntries(await Promise.all([...files, response, logFile,
    resolve(directory, 'process.log'), resolve(directory, 'process.json')].map(async path => [path, await digest(path)])));
  report.summary = {threadRows: threads.length, timerRows: timers.length, statisticsRows: all.length,
    gpuStatisticsRows: gpu.length, unambiguousCpuStatisticsRows: cpu.length,
    topCpuByTotalInclusiveSeconds: cpu.slice(0, 20), topGpuByTotalInclusiveSeconds: gpu.slice(0, 20),
    units: 'seconds; counts are scope instances; inclusive totals overlap and must not be summed as frame time',
    gpuFilter: 'All GPU queues; no CPU threads. UE5.8 statistics -threads filters CPU only.',
    cpuClassification: 'Only names exclusively typed CPU in timers.csv; duplicate CPU/GPU names are excluded from the CPU summary.'};
  report.exportValidationStatus = 'native-analysis-and-four-exports-validated';
  report.status = report.timingIntegrity.status === 'qualified-attribution-only'
    ? 'whole-trace-analysis-qualified' : 'whole-trace-analysis-validated';
  if (report.status === 'whole-trace-analysis-qualified') process.exitCode = 2;
} catch (error) {
  report.error = String(error.stack ?? error); process.exitCode = 1;
} finally {
  report.endedAt = new Date().toISOString(); await save('analysis.json', report);
  console.log(JSON.stringify({status: report.status, directory, error: report.error}));
}
