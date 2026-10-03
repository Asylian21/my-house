"""CPU diagnostic only: census rejected F32 faces; never export a candidate."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r32_frozen_failed_source_r3',ROOT/'scripts/unreal/exterior-context-yard-ground-study-r32-r3.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
OUTPUT=ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-topology-diagnostic-r1'


def main():
 c.require(not OUTPUT.exists(),'Diagnostic output is immutable')
 census=[]
 def observe(row):
  decoded=c.q.native_points(row['verticesCm']);failures=[];zeros=[]
  for offset in range(0,len(row['indices']),3):
   ids=row['indices'][offset:offset+3];original=[row['verticesCm'][i]for i in ids];points=[decoded[i]for i in ids]
   before=c.q.cross(*original);after=c.q.cross(*points)
   values={'sourceTriangle':offset//3,'sourcePositionsCm':original,'decodedNativeProposalPositionsCm':points,
    'sourceCrossCm2':before,'decodedCrossCm2':after}
   if after==[0.,0.,0.]:zeros.append(values)
   elif after[2]>=0.:failures.append(values)
  census.append({'id':row['id'],'triangles':len(row['indices'])//3,'exactZeroFaces':zeros,'nonzeroRejectedFaces':failures})
  # Instrumentation bypasses pruning/rejection only to record every original
  # source face. No acceptance, GLB, proposal or native receipt is produced.
  return row
 c.q.compact_exact_zero_faces=observe
 layout=c.read(c.read(c.SOURCE/'yard-source-plan.json')['layout']['path'])
 data={key:c.read(ROOT/c.p.SOURCES[key])for key in ('buildings','context','terrain')}
 domain=c.unary_union([c.shape(r['domainCm'])for r in layout['surfaces']]).buffer(250)
 ground=c.p.Ground(data['context'],data['terrain'],domain)
 for row in layout['surfaces']:
  if row['role']=='worn_edge':
   c.mesh(c.shape(row['domainCm']),'diagnostic_zero_ground_'+row['id'],8,ground,sample_ground=False)
  elif row['role']in('entry_walk','service_court'):
   c.mesh(c.shape(row['domainCm']),'candidate_actual_ground_'+row['id'],6,ground,hard_max_relief=row['maximumAddedReliefCm'])
 OUTPUT.mkdir();report={'scope':'CPU_ORIGINAL_FACE_F32_CENSUS_ONLY_NOT_ACCEPTED_GEOMETRY','rows':census,
  'instrumentationBypassedTopologyGateForObservationOnly':True,'candidateOrGlbExported':False,'nativeExecuted':False,
  'sourceAccepted':False,'inputs':[c.pin(ROOT/'scripts/unreal/exterior-context-yard-ground-study-r32-r3.py'),
   c.pin(ROOT/'scripts/unreal/exterior-context-yard-ground-quantization-r32-r3.py')]}
 c.write(OUTPUT/'topology-diagnostic.json',report)
 print(json.dumps({'report':c.pin(OUTPUT/'topology-diagnostic.json'),
  'counts':[{'id':r['id'],'triangles':r['triangles'],'exactZero':len(r['exactZeroFaces']),'nonzeroRejected':len(r['nonzeroRejectedFaces'])}for r in census]},indent=2))


if __name__=='__main__':main()
