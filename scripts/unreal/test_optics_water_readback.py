"""CPU doubles exercise the real builder/readback; no Unreal or asset writes."""
import copy,importlib.util,math,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
U=types.ModuleType('unreal')
PINS={'Add':['A','B'],'Multiply':['A','B'],'DotProduct':['A','B'],'Cosine':['Input'],'Normalize':['VectorInput']}
class Node:
 def __init__(self):
  self.props={'period':0.,'ignore_pause':False,'override_period':False,'world_position_shader_offset':'ABSOLUTE'};self.inputs={k:None for k in PINS.get(self.kind,[])};self.name='temporary'
 def set_editor_property(self,k,v):self.props[k]=v
 def get_editor_property(self,k):return self.props[k]
for kind in ('Add','Multiply','DotProduct','Cosine','Normalize','Constant','Constant3Vector','Time','WorldPosition'):
 setattr(U,'MaterialExpression'+kind,type(kind,(Node,),{'kind':kind}))
U.LinearColor=lambda r,g,b,a:types.SimpleNamespace(r=r,g=g,b=b,a=a)
U.MaterialProperty=types.SimpleNamespace(MP_NORMAL='NORMAL')
U.WorldPositionIncludedOffsets=types.SimpleNamespace(WPT_DEFAULT='ABSOLUTE')
with patch.dict(sys.modules,{'unreal':U}):
 s=importlib.util.spec_from_file_location('water_readback_under_test',Path(__file__).with_name('optics.py'));M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
class Material:
 def __init__(self):self.nodes=[];self.outputs={}
 def get_editor_property(self,k):return False if k=='tangent_space_normal' else None
class Lib:
 def create_material_expression(self,m,cls):n=cls();n.material=m;m.nodes.append(n);return n
 def get_material_expressions(self,m):return list(m.nodes)
 def get_material_expression_input_names(self,n):return list(n.inputs)
 def get_material_expression_output_names(self,n):return ['RGB','R','G','B'] if n.kind=='Constant3Vector' else ['XYZ','X','Y','Z'] if n.kind=='WorldPosition' else ['']
 def connect_material_expressions(self,a,channel,b,pin):
  if not pin:pin=next(iter(b.inputs))
  b.inputs[pin]=(a,channel or self.get_material_expression_output_names(a)[0]);return True
 def connect_material_property(self,n,channel,p):n.material.outputs[p]=(n,channel or self.get_material_expression_output_names(n)[0]);return True
 def get_inputs_for_material_expression(self,m,n):return [v[0] if v else None for v in n.inputs.values()]
 def get_input_node_output_name_for_material_expression(self,n,up):return next((True,v[1]) for v in n.inputs.values() if v and v[0] is up)
 def get_material_property_input_node(self,m,p):return m.outputs.get(p,(None,None))[0]
 def get_material_property_input_node_output_name(self,m,p):return True,m.outputs[p][1]
class ReadbackTests(unittest.TestCase):
 def build(self):
  w=M.OpticsWriter.__new__(M.OpticsWriter);w.lib=Lib();m=Material();w.water_normal(m);return w,m
 def test_current_and_historical_four_wave_values(self):
  historical=[{'direction':[1,0],'wavelengthMetres':.36,'amplitudeMetres':.0006,'phaseCycles':0},{'direction':[.6,.8],'wavelengthMetres':.19,'amplitudeMetres':.00035,'phaseCycles':.21},{'direction':[-.8,.6],'wavelengthMetres':.11,'amplitudeMetres':.00018,'phaseCycles':.47},{'direction':[.28,-.96],'wavelengthMetres':.07,'amplitudeMetres':.0001,'phaseCycles':.73}]
  for waves in (M.WAVES,historical):
   with patch.object(M,'WAVES',waves):
    w,m=self.build();r=w.validate_water_normal(m);self.assertEqual(r['cosineCount'],len(waves));self.assertEqual(r['reachableExpressionCount'],11*len(waves)+6)
    for i,wave in enumerate(waves):
     a=r['waves'][i];self.assertEqual(a['phaseCycles'],wave['phaseCycles']);self.assertEqual(a['cosinePeriod'],1)
     self.assertAlmostEqual(a['timeCyclesPerSecond'],-math.sqrt(9.81/(2*math.pi*wave['wavelengthMetres'])))
    for i,n in enumerate(m.nodes):n.name='Completely_Renamed_'+str(i+947)
    self.assertEqual(w.validate_water_normal(m),r)
 def test_float32_defaults_are_accepted(self):
  import struct
  w,m=self.build();f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
  for n in m.nodes:
   if n.kind=='Constant':n.props['r']=f32(n.props['r'])
   if n.kind=='Constant3Vector':
    c=n.props['constant'];n.props['constant']=U.LinearColor(*(f32(getattr(c,k)) for k in ('r','g','b')),1)
  self.assertEqual(w.validate_water_normal(m)['status'],'native-water-normal-graph-readback-validated')
 def test_twelve_float32_branches_and_late_bad_value(self):
  import struct
  # Independent test values, not a proposed production spectrum.
  waves=[{'direction':[math.cos(i*.47),math.sin(i*.47)],'wavelengthMetres':.08+i*.019,'amplitudeMetres':.0001+i*.000011,'phaseCycles':(i*.173)%1} for i in range(12)]
  f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
  with patch.object(M,'WAVES',waves):
   w,m=self.build()
   for n in m.nodes:
    if n.kind=='Constant':n.props['r']=f32(n.props['r'])
    if n.kind=='Constant3Vector':
     c=n.props['constant'];n.props['constant']=U.LinearColor(*(f32(getattr(c,k)) for k in ('r','g','b')),1)
   result=w.validate_water_normal(m);self.assertEqual(result['cosineCount'],12);self.assertEqual(result['reachableExpressionCount'],138)
   for index,wave in enumerate(waves):
    row=result['waves'][index];length=wave['wavelengthMetres'];direction=wave['direction'];slope=2*math.pi*wave['amplitudeMetres']/length
    self.assertEqual(row,{'index':index,'cosinePeriod':1.,'positionCyclesPerCm':[f32(direction[0]/(100*length)),f32(direction[1]/(100*length)),0.], 'timeCyclesPerSecond':f32(-math.sqrt(9.81/(2*math.pi*length))),'phaseCycles':f32(wave['phaseCycles']),'slopeVector':[f32(-slope*direction[0]),f32(-slope*direction[1]),0.]})
   last_cosine=[n for n in m.nodes if n.kind=='Cosine'][-1];phase=last_cosine.inputs['Input'][0];phase.inputs['B'][0].props['r']+=.01
   with self.assertRaisesRegex(RuntimeError,'constant differs'):w.validate_water_normal(m)
 def test_unsupported_wave_count_is_refused(self):
  with patch.object(M,'WAVES',[copy.deepcopy(M.WAVES[0]) for _ in range(5)]):
   w,m=self.build()
   with self.assertRaisesRegex(RuntimeError,'4/12-wave'):w.validate_water_normal(m)
 def test_changed_values_connections_and_time_are_rejected(self):
  for kind in ('period','frequency','phase','position','slope','normal-output','channel','extra-cosine','time-pause','time-loop','position-mode','nan','missing-phase','wrong-normal-type'):
   with self.subTest(kind=kind):
    w,m=self.build();cos=next(n for n in m.nodes if n.kind=='Cosine');phase=cos.inputs['Input'][0];travel=phase.inputs['A'][0];dot=travel.inputs['A'][0];temporal=travel.inputs['B'][0];normal=m.outputs['NORMAL'][0]
    if kind=='period':cos.props['period']=2
    elif kind=='frequency':temporal.inputs['B'][0].props['r']*=.5
    elif kind=='phase':phase.inputs['B'][0].props['r']+=.01
    elif kind=='position':dot.inputs['B'][0].props['constant'].r+=.01
    elif kind=='slope':next(n for n in m.nodes if n.kind=='Multiply' and n.inputs['A'][0] is cos).inputs['B'][0].props['constant'].g+=.01
    elif kind=='normal-output':m.outputs['NORMAL']=(None,'')
    elif kind=='channel':dot.inputs['B']=(dot.inputs['B'][0],'R')
    elif kind=='extra-cosine':m.nodes.append(U.MaterialExpressionCosine())
    elif kind=='time-pause':temporal.inputs['A'][0].props['ignore_pause']=True
    elif kind=='time-loop':temporal.inputs['A'][0].props['override_period']=True
    elif kind=='position-mode':dot.inputs['A'][0].props['world_position_shader_offset']='CAMERA_RELATIVE'
    elif kind=='nan':phase.inputs['B'][0].props['r']=float('nan')
    elif kind=='missing-phase':phase.inputs['B']=None
    else:m.outputs['NORMAL']=(dot,'')
    with self.assertRaises(RuntimeError):w.validate_water_normal(m)
 def test_shared_time_and_position_are_required(self):
  for kind in ('Time','WorldPosition'):
   w,m=self.build();original=next(n for n in m.nodes if n.kind==kind);replacement=w.lib.create_material_expression(m,type(original));replacement.props=copy.deepcopy(original.props)
   for n in m.nodes:
    matches=[k for k,v in n.inputs.items() if v and v[0] is original]
    if matches:n.inputs[matches[0]]=(replacement,n.inputs[matches[0]][1]);break
   with self.assertRaises(RuntimeError):w.validate_water_normal(m)
if __name__=='__main__':unittest.main()
