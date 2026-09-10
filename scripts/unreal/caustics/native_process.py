"""Owned native process supervision derived from the accepted candidate host; no import-time execution."""
from pathlib import Path
import hashlib,json,os,shlex,signal,subprocess,time

def need(value, message):
    if not value:
        raise RuntimeError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def save(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)

def processes():
    # comm has a fixed final position; preserve spaces in executable paths.
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,lstart=,state=,comm='],
                            capture_output=True, text=True, timeout=5, check=True)
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split(None, 9)
        if len(fields) != 10:
            continue
        rows.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'pgid': int(fields[2]),
                     'started': ' '.join(fields[3:8]), 'state': fields[8], 'executable': fields[9]})
    return rows

def identity(row):
    return (row['pid'], row['started'])

def alive(row):
    return 'Z' not in row['state']

def name(row):
    return Path(row['executable'].strip('()')).name

def command(pid):
    p = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'args='],
                       capture_output=True, text=True, timeout=5)
    return p.stdout.strip()

def supervise(cfg, out):
    initial = processes()
    reject_conflicts(initial,cfg)
    save(out/'processes-before.json',initial)
    baseline, seen, events, gaps = {identity(p) for p in initial}, {}, [], set()
    data = {**cfg,'pid':None,'remainingOwned':[],'status':'running','hostSha256':sha(Path(__file__)),'errors':[]}
    proc, terminal, start, peak = None, None, time.monotonic(), 0
    env = dict(os.environ); env.update(cfg['environmentSet'])
    for k in cfg['environmentUnset']: env.pop(k,None)
    stopping = [None]
    handlers = {s:signal.signal(s,lambda s,f:stopping.__setitem__(0,'Host signal '+str(s))) for s in (signal.SIGTERM,signal.SIGINT)}
    def owned():
        now = processes()
        parents = {p['pid'] for p in now if identity(p) in seen and alive(p)}
        if proc.poll() is None: parents.add(proc.pid)
        changed = True
        while changed:
            changed = False
            for p in now:
                k = identity(p)
                if k not in baseline and k not in seen and (p['ppid'] in parents or (proc.poll() is None and p['pgid']==proc.pid)):
                    seen[k] = {**p,'args':command(p['pid'])}
                    if alive(p): parents.add(p['pid'])
                    changed = True
        return [p for p in now if identity(p) in seen and alive(p)]
    try:
        with (out/'stdout.log').open('xb') as log:
            proc = subprocess.Popen(cfg['argv'],cwd=cfg['cwd'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            data['pid'] = proc.pid; save(out/'process.json',data)
            print(json.dumps({'status':'started','mode':cfg['mode'],'pid':proc.pid,'directory':str(out)}),flush=True)
            while True:
                rows = owned(); workers = sum(name(p)=='ShaderCompileWorker' for p in rows); peak=max(peak,workers)
                for p in rows:
                    n=name(p)
                    raw=command(p['pid']) if n in COMPILERS|{'xcodebuild'} else seen[identity(p)]['args']
                    seen[identity(p)]['args']=raw
                    errors,gap=process_issues(cfg['mode'],n,raw)
                    data['errors'].extend(errors)
                    if gap:gaps.add(identity(p))
                if cfg['mode'].endswith('-build') and sum(name(p)=='clang++' for p in rows)>4:
                    data['errors'].append('More than four observed clang++ drivers')
                if workers>4: data['errors'].append('More than four ShaderCompileWorkers')
                if stopping[0]: data['errors'].append(stopping[0])
                if time.monotonic()-start>=cfg['deadlineSeconds']: data['errors'].append('Phase deadline exceeded')
                if proc.poll() is not None:
                    if terminal is None:
                        terminal=time.monotonic(); data['nativeExitCode']=proc.returncode; save(out/'process.json',data)
                        print(json.dumps({'status':'native-terminal','pid':proc.pid,'exitCode':proc.returncode,'ownedRemaining':len(rows)}),flush=True)
                    if not rows: break
                    if time.monotonic()-terminal>=10:
                        if proc.returncode==0 and all(name(p)=='ibtoold' for p in rows): data['persistentXcodeHelperCleanup']=True
                        else: data['errors'].append('Owned descendants persisted after native terminal')
                        break
                if data['errors']: break
                time.sleep(.2)
    except BaseException as exc: data['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        if proc is not None:
            try:
                for sig,grace in [(signal.SIGTERM,10),(signal.SIGKILL,5)]:
                    rows=owned()
                    if proc.poll() is not None and not rows: break
                    for p in rows:
                        if any(identity(q)==identity(p) and alive(q) for q in processes()):
                            try:
                                os.kill(p['pid'],sig); events.append({**p,'signal':int(sig),'args':seen[identity(p)]['args']})
                            except ProcessLookupError: pass
                    end=time.monotonic()+grace
                    while time.monotonic()<end and (proc.poll() is None or owned()): time.sleep(.2)
                proc.wait(timeout=1); data['nativeExitCode']=proc.returncode; data['remainingOwned']=owned()
            except BaseException as exc:
                data['errors'].append('Cleanup '+str(exc))
                data['ownedDrainVerified'] = False
                # Enumeration failure must not strand the identity-owned direct Popen child.
                try:
                    if proc.poll() is None:
                        proc.kill()
                        events.append({'pid':proc.pid,'signal':int(signal.SIGKILL),'scope':'direct-Popen-child',
                                       'reason':'cleanup enumeration failed'})
                    proc.wait(timeout=5)
                    data['nativeExitCode'] = proc.returncode
                    data['directChildReapedAfterCleanupFailure'] = True
                except BaseException as fallback:
                    data['errors'].append('Direct-child cleanup fallback: '+str(fallback))
            if proc.returncode!=0 or data.get('remainingOwned') or proc.poll() is None: data['errors'].append('Native nonzero/unreaped/remaining owned process')
        for s,h in handlers.items(): signal.signal(s,h)
    data.update(seconds=time.monotonic()-start,peakShaderWorkers=peak,ownedProcesses=list(seen.values()),
                cleanupEvents=events,argvObservationGaps=[{'pid':p,'started':s} for p,s in sorted(gaps)])
    return data

UE={'UnrealEditor','UnrealEditor-Cmd','BreziTwin','BreziStartupLauncher','ShaderCompileWorker'}
COMPILERS={'clang','clang++','ld','ld64','ld64.lld','lld','metal','metallib','dsymutil'}
BUSY=UE|COMPILERS|{'dotnet','UnrealBuildTool','xcodebuild'}

def process_issues(mode,n,raw):
    tokens=shlex.split(raw) if raw else []
    forbidden={'BreziTwin','BreziStartupLauncher','UnrealEditor','CrashReportClient','CrashReportClientEditor'}
    if mode!='cook':forbidden|={'UnrealEditor-Cmd','ShaderCompileWorker','metal','metallib'}
    if n in forbidden:return ['Forbidden owned process '+n],False
    if mode.endswith('-build'):return [],False
    candidates=(COMPILERS-({'metal','metallib'} if mode=='cook' else set()))|({'xcodebuild'} if mode.endswith('-graph') else set())
    if n not in candidates:return [],False
    if n in {'clang','clang++'} and tokens and tokens[1:] in [['--version'],['-v']]:return [],False
    if not tokens or (len(tokens)==1 and n in {'clang','clang++'}):return [],True
    return ['Unexpected native action in '+mode+': '+raw],False

def reject_conflicts(rows,cfg):
    # Keep unrelated Xcode work in the baseline. It is never adopted or terminated.
    roots=[str(Path(cfg[k])) for k in ('engineRoot','projectRoot')]
    for row in rows:
        n=name(row)
        if not alive(row) or n not in BUSY:continue
        if n in UE:raise RuntimeError('Conflicting native UE process: '+str(row['pid']))
        raw=command(row['pid'])
        if any(root in raw or row['executable'].startswith(root+'/') for root in roots):
            raise RuntimeError('Conflicting candidate build process: '+str(row['pid']))
        cwd=subprocess.run(['/usr/sbin/lsof','-a','-p',str(row['pid']),'-d','cwd','-Fn'],capture_output=True,text=True,timeout=5)
        paths=[line[1:] for line in cwd.stdout.splitlines() if line.startswith('n')]
        need(raw and len(paths)==1,'Cannot classify live build process '+str(row['pid']))
        need(not any(paths[0]==root or paths[0].startswith(root+'/') for root in roots),
             'Conflicting candidate working directory: '+str(row['pid']))
