#!/usr/bin/env python3
"""Read-only exact UE patch-state preflight; never applies patches or starts native tools."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(engine,state):
 root=Path(engine).absolute();m=json.loads((HERE/'manifest.json').read_text())
 if root.resolve()!=root or not root.is_dir():raise ValueError('Use a real absolute engine directory')
 if sha(HERE/'engine.patch')!=m['patchSha256']:raise ValueError('Engine patch changed')
 version=root/'Engine/Build/Build.version'
 if sha(version)!=m['engineBuildVersionSha256']:raise ValueError('Unexpected UE Build.version')
 rows=[]
 for row in m['files']:
  p=root/row['path'];want=row[state+'Sha256']
  if p.is_symlink() or (p.exists() and p.resolve()!=p):raise ValueError('Linked engine source: '+str(p))
  actual=sha(p) if p.is_file() else None
  if p.exists() and not p.is_file():raise ValueError('Non-file source target: '+str(p))
  if actual!=want:raise ValueError('Wrong '+state+' source state: '+str(p))
  rows.append({'path':row['path'],'sha256':actual})
 return {'status':'engine-'+state+'-source-pins-verified','fileCount':len(rows),'files':rows,
         'nativeBuildVerified':False,'shaderCompilationVerified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',type=Path,required=True);p.add_argument('--state',choices=('base','result'),required=True)
 a=p.parse_args();print(json.dumps(verify(a.engine,a.state),indent=2))
