"""Restore only three pinned Grass004 maps; no source lock or Unreal writes.

Existing valid files are read only. Missing downloads need --download. HTTP Range
selects ZIP members, so the full151 MB archive is never downloaded.
"""
import argparse,hashlib,io,json,os,urllib.request,uuid,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())

def require(ok,message):
 if not ok:raise RuntimeError(message)
def verify_file(path,spec):
 require(path.is_file() and path.resolve()==path,'Missing/symlinked map: '+str(path))
 require(path.stat().st_size==spec['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==spec['sha256'],'Existing map conflicts with pinned Grass004: '+str(path))

def restore(download=False):
 ref=json.loads((HERE/'reference.json').read_text());receipt=json.loads((HERE/'inputs/selected-download.json').read_text())
 specs={Path(v['path']).name:v for v in ref['maps'].values()};missing=[]
 require(set(specs)=={'Grass004_4K-JPG_Color.jpg','Grass004_4K-JPG_NormalGL.jpg','Grass004_4K-JPG_Roughness.jpg'},'Unexpected cache scope')
 for name,spec in specs.items():
  target=ROOT/spec['path'];require(target.parent==ROOT/'output/unreal/lawn-ground-study/Grass004-4K' and target.resolve()==target,'Cache path escaped owned location')
  if target.exists():verify_file(target,spec)
  else:missing.append(name)
 if not missing:return {'status':'all-three-pinned-maps-present','downloadedBytes':0}
 require(download,'Pinned maps missing; explicitly run restore_inputs.py --download')
 size=receipt['remoteArchiveSize'];url=receipt['resolvedUrl'];fileid=receipt['remoteArchiveFileId']
 require(url.startswith('https://acg-download.struffelproductions.com/file/ambientCG-Web/download/Grass004_') and size==151897993,'Official archive identity differs')
 class Remote(io.RawIOBase):
  def __init__(self):self.position=0;self.transferred=0
  def seekable(self):return True
  def readable(self):return True
  def tell(self):return self.position
  def seek(self,offset,whence=0):
   pos=offset if whence==0 else self.position+offset if whence==1 else size+offset;require(0<=pos<=size,'Invalid archive seek');self.position=pos;return pos
  def read(self,n=-1):
   n=min(size-self.position,n if n>=0 else size-self.position)
   if not n:return b''
   require(self.transferred+n<=100*1024*1024,'Selected map download exceeds budget');first,last=self.position,self.position+n-1
   request=urllib.request.Request(url,headers={'Range':f'bytes={first}-{last}','User-Agent':'BreziTwin-pinned-Grass004-restore/1.0'})
   with urllib.request.urlopen(request,timeout=40) as response:
    require(response.status==206 and response.headers.get('Content-Range')==f'bytes {first}-{last}/{size}' and response.headers.get('x-bz-file-id')==fileid,'Archive changed/range unsupported')
    data=response.read(n+1);require(len(data)==n,'Archive range size differs')
   self.position+=n;self.transferred+=n;return data
 remote=Remote();entries={r['zipMember']:r for r in receipt['files']}
 with zipfile.ZipFile(remote) as archive:
  # Complete all member/source preflight before creating any destination.
  for name in missing:
   z=archive.getinfo(name);r=entries[name]
   require(z.file_size==specs[name]['bytes']==r['size'] and f'{z.CRC:08x}'==r['crc32'] and r['sha256']==specs[name]['sha256'],'Pinned archive member differs')
  for name in missing:
   data=archive.read(name);require(hashlib.sha256(data).hexdigest()==specs[name]['sha256'],'Downloaded map SHA differs')
   target=ROOT/specs[name]['path'];target.parent.mkdir(parents=True,exist_ok=True);require(target.parent.resolve()==target.parent and not target.exists() and not target.is_symlink(),'Cache destination changed')
   temp=target.with_name(target.name+'.'+uuid.uuid4().hex+'.part')
   try:
    with temp.open('xb') as stream:stream.write(data)
    # Hard-link publication is atomic and refuses a concurrently created target.
    os.link(temp,target);verify_file(target,specs[name])
   finally:
    if temp.exists():temp.unlink()
 return {'status':'three-pinned-maps-restored','downloadedBytes':remote.transferred,'wholeArchiveHashVerified':False}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--download',action='store_true');args=parser.parse_args();print(json.dumps(restore(args.download),indent=2))
