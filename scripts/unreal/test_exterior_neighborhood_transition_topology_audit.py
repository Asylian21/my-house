"""Read-only adversarial R12c receipt schemas; no native success is fabricated.

Frozen R11 data, original source geometry and the isolated material graph shim
are fixtures. Synthesized future receipt fields test rejection boundaries only.
No test launches Unreal, saves assets, alters old receipts or accepts appearance.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('transition_audit',HERE/'exterior-neighborhood-transition-topology-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
ROOT=audit.ROOT
SHIM=ROOT/'output/unreal/exterior-neighborhood-transition-materials-validation-20261001-r2/source-material-proof.json'
SHIM_SHA='95631666126b8979b642f8dcee141fa15a8eb1643b16da0f497277da7a84b41c'
R11_QA=ROOT/'output/unreal/exterior-validation-20260930-r1/qa/after-exterior-r11-shape-artifacts-1790847691627/summary.json'


class TransitionEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior,cls.history=audit.historical_r11()
        cls.plan=audit.read(audit.pin(audit.TRANSITION_PLAN,audit.TRANSITION_PLAN_SHA))
        cls.context=audit.read(audit.pin(cls.plan['sourceContext']['path'],cls.plan['sourceContext']['sha256']))
        cls.topology=audit.read(audit.pin(audit.NATIVE_TOPOLOGY,audit.NATIVE_TOPOLOGY_SHA))
        cls.topology_rows={row['sourceMeshId']:row for row in cls.topology['rows']}
        cls.shim=audit.read(audit.pin(SHIM,SHIM_SHA))
        cls.actual_r12c=audit.read(audit.pin(audit.SOURCE/'exterior-import-report.json',
            '3a3824b05aff496a7df45cc033b88a64d3c3de73cf9c0c747bd88a21427904ee'))
        cls.native={r['id']:r for r in cls.prior['savedPlantReadback']}
        qa=audit.read(R11_QA)['results'][0]
        cls.qa=audit.read(Path(qa['evidence'])/'qa.json')
        cls.runtime=audit.read(Path(qa['evidence'])/'runtime.json')

    def graph_fixture(self):
        old=deepcopy(self.prior['materials']['materials']['context_meadow']['graph'])
        graph=deepcopy(old);tag='BreziExterior:'
        rewires={('groundcover-'+k,'Amount'):'continuous-ground-cover' for k in ('albedo','normal','roughness')}
        rewires.update({('natural-ground-color','Tint'):'continuous-ground-tint',
            ('natural-ground-color','AlbedoScale'):'continuous-ground-albedo-response',
            ('world-ground-normal','Strength'):'continuous-ground-normal-strength'})
        for node in graph['nodes']:
            for p in node['inputs']:
                target=rewires.get((node['role'].removeprefix(tag),p[0]))
                if target:p[1:]=[tag+target,'']
        old_roles={r['role']for r in old['nodes']}
        for source in self.shim['newMaterial']['graph']['nodes']:
            if source['role']in old_roles:continue
            node=deepcopy(source)
            if node['class']=='MaterialExpressionConstant3Vector':
                node['values']['constant']=[struct.unpack('<f',struct.pack('<f',v))[0]for v in node['values']['constant']]
            elif node['class']=='MaterialExpressionCustom':
                width=int(node['values']['output_type'][-1])
                node['values']['output_type']=f'<CustomMaterialOutputType.CMOT_FLOAT{width}: {width-1}>'
                if node['role']==tag+'continuous-condition-world-uv':
                    node['inputs'][0][2]='XYZ'
            elif node['class']=='MaterialExpressionTextureSample':
                node['values']['sampler_type']='<MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR: 6>'
                node['values']['mip_value_mode']='<TextureMipValueMode.TMVM_NONE: 0>'
                node['inputs'] += [['Tex',None,None],['Apply View MipBias',None,None]]
            graph['nodes'].append(node)
        return old,graph,self.shim['conditionTexture']['asset']

    def condition_fixture(self):
        condition=deepcopy(self.shim['neighborhoodTransition']['condition'])
        return condition,{'conditionTexture':self.plan['conditionTexture']}

    def saved_fixture(self):
        # The actor names/hash below are explicit schema fixtures, not a native
        # R12c inspection; source vertices/rows/master assets remain real pins.
        report={'neighborhoodTransition':{'nativeTopologyBaseline':{'path':str(audit.NATIVE_TOPOLOGY),'sha256':audit.NATIVE_TOPOLOGY_SHA}},
            'inputFiles':{str(audit.NATIVE_TOPOLOGY):audit.NATIVE_TOPOLOGY_SHA,**self.topology['inputFiles']},
            'geometry':{'actors':{},'meshes':{},'groups':{}},
            'materials':{'materials':{audit.TRANSITION_KEY:{'asset':'/Game/Test.M_Transition'}}}}
        source={m['id']:m for m in self.context['meshes']}
        bindings=[]
        for b in self.plan['materialBindingProposal']:
            key=b['sourceMeshId'];mesh=source[key]
            bounds={k:[fn(p[i]for p in mesh['verticesCm'])for i in range(3)]for k,fn in [('min',min),('max',max)]}
            observed=self.topology_rows[key];actual=deepcopy(observed['actualBoundsCm'])
            error=max(abs(actual[k][i]-bounds[k][i])for k in ('min','max')for i in range(3))
            report['geometry']['actors'][key]=b['nativeActor'];report['geometry']['meshes'][key]=b['nativeMesh']
            bindings.append({'sourceMeshId':key,'actor':b['nativeActor'],'mesh':b['nativeMesh'],
                'material':'/Game/Test.M_Transition','triangles':len(mesh['indices'])//3,
                'renderTriangles':observed['renderTriangles'],'descriptionVertices':observed['descriptionVertices'],
                'sourceGeometrySha256':b['sourceGeometrySha256'],'actualBoundsCm':actual,
                'expectedBoundsCm':bounds,'maximumBoundsErrorCm':error,
                'actorTransform':[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]],
                'collision':'NoCollision','canEverAffectNavigation':False})
        for i,g in enumerate(self.plan['groups']):
            report['geometry']['groups'][g['id']]={'actor':f'/Game/Test:GROUP_{i}',
                'mesh':self.native[g['meshId']]['mesh'],'instances':len(g['instances']),
                'cullStartCm':3200,'cullEndCm':4000,'qualityDetail':False,'transformsSha256':'a'*64}
        report['neighborhoodTransition']['savedReadback']={'status':'verified-saved-neighborhood-transition',
            'instances':7000,'allNewVisualsNoCollision':True,'sourceGroundBoundsTopologyAndOriginVerified':True,
            'sourceTransformsComparedAfterReload':True,'nativeVisualAccepted':False,'performanceAccepted':False,
            'maximumPositionErrorCm':0.,'maximumScaleError':0.,'maximumQuaternionErrorSignEquivalent':0.,
            'materialBindings':bindings,'groupIds':[g['id']for g in self.plan['groups']]}
        return report,{'materialBindings':self.plan['materialBindingProposal'],'groups':self.plan['groups']}

    def test_only_success_candidate_r12c_excludes_failed_r12_and_r12b_before_reads(self):
        self.assertEqual(audit.candidate(audit.SOURCE),ROOT/'output/unreal/exterior-20261001-r12c')
        with patch.object(audit,'read',side_effect=AssertionError('Failed/old candidate cannot be read')):
            for old in ('exterior-20261001-r12','exterior-20261001-r12b','exterior-20261001-r11','exterior-20260930-r9a'):
                with self.assertRaisesRegex(RuntimeError,'exact R12c'):audit.audit_import(ROOT/'output/unreal'/old)

    def test_historical_code_resolves_sealed_bytes_without_old_live_hash_substitution(self):
        self.assertEqual(len(self.history['frozenPipelineCodePins']),16)
        self.assertTrue(self.history['oldCodeHashesNeverSubstitutedForCurrentLivePaths'])
        for path,value in self.history['frozenPipelineCodePins'].items():
            self.assertTrue(Path(path).is_relative_to(audit.R11_SNAPSHOT.parent))
            self.assertEqual(audit.sha(path),value)
        importer=str(ROOT/'scripts/unreal/exterior-import.py')
        self.assertNotEqual(self.prior['pipelineFiles'][importer],audit.sha(importer))

    def test_current_required_pipeline_rejects_missing_transition_module(self):
        report={'pipelineFiles':{str(ROOT/'scripts/unreal'/name):audit.sha(ROOT/'scripts/unreal'/name)
            for name in audit.PIPELINE_NAMES}}
        audit.required_pipeline(report)
        for name in ('exterior-neighborhood-transition-native.py','exterior-neighborhood-transition-materials.py'):
            unsafe=deepcopy(report);unsafe['pipelineFiles'].pop(str(ROOT/'scripts/unreal'/name))
            with self.assertRaisesRegex(RuntimeError,'pipeline dependency'):audit.required_pipeline(unsafe)

    def test_native_graph_accepts_only_ten_added_nodes_and_six_exact_input_rewires(self):
        old,graph,texture=self.graph_fixture()
        proof=audit._transition_graph(graph,old,texture)
        self.assertEqual((proof['nodes'],proof['newNodes'],proof['allowedOriginalInputRewires']),(114,10,6))
        actual=self.actual_r12c['materials']
        self.assertEqual(audit._transition_graph(actual['materials'][audit.TRANSITION_KEY]['graph'],old,
            actual['textures'][audit.CONDITION_KEY]['asset']),proof)

    def test_preserved_geographic_shader_rejects_field_macro_or_camera_change(self):
        old,graph,texture=self.graph_fixture()
        for fragment in ('field-macro-world-uv','licensed-ortho-basecolor'):
            unsafe=deepcopy(graph);node=next(n for n in unsafe['nodes']if n['role'].endswith(fragment))
            node['values']['code']='return 1;'
            with self.assertRaisesRegex(RuntimeError,'original PBR/fieldMacro'):audit._transition_graph(unsafe,old,texture)

    def test_condition_graph_rejects_role_alias_mips_uv_drift_and_unbounded_response(self):
        old,graph,texture=self.graph_fixture()
        changes=[('ground_condition-world-condition',lambda n:n['values'].update(sampler_type='<MaterialSamplerType.SAMPLERTYPE_COLOR: 0>')),
            ('continuous-condition-world-uv',lambda n:n['inputs'][0].__setitem__(2,'XY')),
            ('continuous-condition-world-uv',lambda n:n['inputs'][0].__setitem__(2,'')),
            ('ground_condition-world-condition',lambda n:n['values'].update(automatic_view_mip_bias=True)),
            ('ground_condition-world-condition',lambda n:n['values'].update(mip_value_mode='<TextureMipValueMode.TMVM_MIP_LEVEL: 1>')),
            ('continuous-condition-RowU',lambda n:n['values']['constant'].__setitem__(0,.001)),
            ('continuous-condition-bounded',lambda n:n['values'].update(code='return Condition;'))]
        for suffix,change in changes:
            unsafe=deepcopy(graph);change(next(n for n in unsafe['nodes']if n['role'].endswith(suffix)))
            with self.assertRaisesRegex(RuntimeError,'condition|bounded'):audit._transition_graph(unsafe,old,texture)

    def test_condition_interpretation_requires_truthful_unexposed_api_and_artist_provenance(self):
        condition,prepared=self.condition_fixture()
        self.assertEqual(audit.condition_metadata(condition,prepared),condition)
        for key,value in [('compressionNone',True),('compressionNonePropertyExposed',True),('role','ortho'),
                ('sourceEncodingReadback','TSE_S_RGB'),('ordinaryMips',False),('sRGB',0),
                ('sourceLicense','CC0-1.0'),('uncompressedFormatBasis','invented native boolean')]:
            with self.assertRaisesRegex(RuntimeError,'texture role/interpretation'):
                audit.condition_metadata({**condition,key:value},prepared)

    def test_actual_transient_api_support_preserves_failure_and_counts_no_extra_unit_or_native_pid(self):
        evidence=audit.texture_api_support()
        self.assertTrue(evidence['zeroAdditionalUnitTests'])
        self.assertFalse(evidence['nativePidClaimed']);self.assertFalse(evidence['assetsSaved'])
        self.assertTrue(evidence['actualR12cSavedSceneValidationStillRequired'])

    def test_original40_materials73_textures_reject_changed_maps_graphs_or_boolean_types(self):
        records=deepcopy(self.prior['materials']['materials']);textures=deepcopy(self.prior['materials']['textures'])
        records[audit.TRANSITION_KEY]={};textures[audit.CONDITION_KEY]={}
        audit.original_material_conservation(records,textures,self.prior)
        for change in ('missing','graph','typedFlag'):
            wrong=deepcopy(records)
            if change=='missing':wrong.pop('context_meadow')
            elif change=='graph':wrong['context_meadow']['graphSha256']='b'*64
            else:wrong['context_meadow']['graph']['flags']['two_sided']=0
            with self.assertRaisesRegex(RuntimeError,'census|original R11'):audit.original_material_conservation(wrong,textures,self.prior)

    def test_exact65_bounds_and7000_group_schema_records_source_only_flags(self):
        report,validated=self.saved_fixture()
        proof=audit._transition_saved(report,validated,self.context,self.native)
        self.assertEqual((proof['sourceGroundBindings'],proof['groups'],proof['instances']),(65,158,7000))
        self.assertTrue(proof['nativeBoundsIndependentlyComparedToAllSourceVertices'])
        topology=proof['nativeSourceAndRenderTopology']
        self.assertEqual((topology['sourceDescriptionTriangles'],topology['nativeRenderTriangles'],topology['nativeDescriptionVertices']),(3671,3613,11013))
        self.assertEqual(len(topology['meshesWithInheritedDifferentRenderCounter']),3)
        self.assertTrue(topology['all65NativeProbeRowsExactlyEqual'])
        self.assertFalse(topology['geometryReductionOrCauseClaimed'])
        self.assertFalse(proof['nativeVisualAccepted']);self.assertFalse(proof['performanceAccepted'])
        expected=deepcopy(self.actual_r12c['neighborhoodTransition']['validation'])
        expected['maximumCrownRadiusCm']=4.927855302790991
        comparison=audit.transition_validation(self.actual_r12c['neighborhoodTransition']['validation'],expected)
        self.assertEqual(comparison['absoluteDifferenceCm'],8.881784197001252e-16)
        self.assertTrue(comparison['everyOtherValidationLeafExact'])

    def test_saved_bindings_reject_forged_expected_bounds_actual_error_and_geometry_identity(self):
        for change in ('expected','actual','wrongError','topology','renderCount','vertexCount','baselinePin','missingProbe','material','collision','origin'):
            report,validated=self.saved_fixture();row=report['neighborhoodTransition']['savedReadback']['materialBindings'][0]
            if change=='expected':row['expectedBoundsCm']['max'][0]+=.001
            elif change=='actual':row['actualBoundsCm']['max'][0]+=.051;row['maximumBoundsErrorCm']=.051
            elif change=='wrongError':row['maximumBoundsErrorCm']=.001
            elif change=='topology':row['triangles']+=1
            elif change=='renderCount':row['renderTriangles']+=1
            elif change=='vertexCount':row['descriptionVertices']+=1
            elif change=='baselinePin':report['neighborhoodTransition']['nativeTopologyBaseline']['sha256']='f'*64
            elif change=='missingProbe':report['inputFiles'].pop(next(iter(self.topology['inputFiles'])))
            elif change=='material':row['material']='/Game/Wrong.Material'
            elif change=='collision':row['collision']='QueryAndPhysics'
            else:row['actorTransform'][0][0]=1.
            with self.assertRaisesRegex(RuntimeError,'Transition|Native topology|Native inherited'):audit._transition_saved(report,validated,self.context,self.native)

    def test_saved_group_rejects_wrong_count_cull_density_alias_and_malformed_hash(self):
        for change in ('count','cull','density','actorAlias','hash'):
            report,validated=self.saved_fixture();ids=report['neighborhoodTransition']['savedReadback']['groupIds']
            row=report['geometry']['groups'][ids[0]]
            if change=='count':row['instances']+=1
            elif change=='cull':row['cullEndCm']=5000
            elif change=='density':row['qualityDetail']=True
            elif change=='actorAlias':row['actor']=report['geometry']['groups'][ids[1]]['actor']
            else:row['transformsSha256']='z'*64
            with self.assertRaisesRegex(RuntimeError,'Transition'):audit._transition_saved(report,validated,self.context,self.native)

    def test_saved_transform_error_guards_reject_bool_nonfinite_and_out_of_range(self):
        for field,value in [('maximumPositionErrorCm',.003),('maximumScaleError',float('nan')),
                ('maximumQuaternionErrorSignEquivalent',True)]:
            report,validated=self.saved_fixture();report['neighborhoodTransition']['savedReadback'][field]=value
            with self.assertRaisesRegex(RuntimeError,'float32 transform'):audit._transition_saved(report,validated,self.context,self.native)
        exact=deepcopy(self.actual_r12c['neighborhoodTransition']['validation'])
        for value in (True,'4.9278553027909915',float('nan'),float('inf'),-1.,5.1,exact['maximumCrownRadiusCm']+2e-12):
            unsafe=deepcopy(exact);unsafe['maximumCrownRadiusCm']=value
            with self.assertRaisesRegex(RuntimeError,'Transition validation'):audit.transition_validation(unsafe,exact)
        for field,value in [('instances',7001),('nativeVisualAccepted',0),('originalRemovalIndicesPreserved',True),
                ('artistInterpretation',False),('sourceGeometryAndOriginalMaterialsUnchanged',False)]:
            unsafe=deepcopy(exact);unsafe[field]=value
            with self.assertRaisesRegex(RuntimeError,'Transition validation'):audit.transition_validation(unsafe,exact)
        unsafe=deepcopy(exact);unsafe['sourcePlan']['sha256']='a'*64
        with self.assertRaisesRegex(RuntimeError,'Transition validation'):audit.transition_validation(unsafe,exact)

    def test_inherited_group_conservation_catches_undeclared_tree_lawn_cull_and_instance_drift(self):
        new,validated=self.saved_fixture();report=deepcopy(self.prior)
        report['geometry']['groups'].update(new['geometry']['groups'])
        ids=new['neighborhoodTransition']['savedReadback']['groupIds']
        proof=audit.preserved_r11_geometry(report,self.prior,ids)
        self.assertEqual((proof['originalMeshBindings'],proof['originalSceneGroups'],proof['originalSavedMasters']),(551,1816,100))
        for field,value in [('instances',1),('cullEndCm',1),('transformsSha256','b'*64),('qualityDetail',True)]:
            unsafe=deepcopy(report);key=next(iter(self.prior['geometry']['groups']))
            unsafe['geometry']['groups'][key][field]=value
            # First inherited group already has one instance; change distinctly.
            if field=='instances':unsafe['geometry']['groups'][key][field]+=1
            with self.assertRaisesRegex(RuntimeError,'inherited scene group'):audit.preserved_r11_geometry(unsafe,self.prior,ids)

    def test_inherited_master_or_unapproved_group_loss_is_rejected(self):
        new,_=self.saved_fixture();report=deepcopy(self.prior);report['geometry']['groups'].update(new['geometry']['groups'])
        ids=new['neighborhoodTransition']['savedReadback']['groupIds']
        for change in ('lostGroup','changedMaster'):
            unsafe=deepcopy(report)
            if change=='lostGroup':unsafe['geometry']['groups'].pop(next(iter(self.prior['geometry']['groups'])))
            else:unsafe['savedPlantReadback'][0]['lodTriangles'][0]+=1
            with self.assertRaisesRegex(RuntimeError,'scene group|all-LOD'):audit.preserved_r11_geometry(unsafe,self.prior,ids)

    def test_exact_five_views_reject_old_source_duplicates_missing_and_package_swap(self):
        summary={'source':str(audit.SOURCE),'packageReportSha256':'a'*64,
            'results':[{'scene':scene,'id':str(i),'evidence':str(ROOT/f'output/unreal/SCHEMA_ONLY_{i}')}
                for i,scene in enumerate(audit.QA_SCENES)]}
        audit.qa_identity(summary,audit.SOURCE,'a'*64)
        for change in ('source','duplicate','missing','package'):
            unsafe=deepcopy(summary)
            if change=='source':unsafe['source']=str(audit.SOURCE.with_name('exterior-20261001-r12'))
            elif change=='duplicate':unsafe['results'][0]['scene']=unsafe['results'][1]['scene']
            elif change=='missing':unsafe['results'].pop()
            else:unsafe['packageReportSha256']='b'*64
            with self.assertRaisesRegex(RuntimeError,'suite|five-view'):audit.qa_identity(unsafe,audit.SOURCE,'a'*64)

    def test_keyboard_focus_is_required_for_timing_even_when_application_and_window_active(self):
        runtime,qa=deepcopy(self.runtime),deepcopy(self.qa)
        focus=runtime['focusDuringBenchmark'];samples=runtime['frameInterval']['sampleCount']
        for field in ('applicationForegroundSamples','gameWindowActiveSamples','sceneViewportKeyboardFocusSamples'):focus[field]=samples
        focus['applicationForegroundThroughoutBenchmark']=True;qa['foreground']=deepcopy(focus)
        self.assertTrue(audit.timing_evidence(runtime,qa)['timingValid'])
        focus['sceneViewportKeyboardFocusSamples']=0;qa['foreground']=deepcopy(focus)
        with self.assertRaisesRegex(RuntimeError,'keyboard focus'):audit.timing_evidence(runtime,qa)
        artifact=audit.timing_evidence(runtime,qa,True)
        self.assertTrue(artifact['timingInvalid']);self.assertFalse(artifact['performanceAccepted'])

    def test_runtime_fixed_density_groups_cannot_join_detail_scaling_or_restore_legacy_lawn(self):
        report,_=self.saved_fixture();transition=report['geometry']['groups']
        managed={k:v for k,v in self.prior['geometry']['groups'].items()if v['qualityDetail']}
        runtime,qa=deepcopy(self.runtime),deepcopy(self.qa)
        qa['profile']='cinematic'
        hidden={r['legacyLawnGroup']:r for r in self.prior['naturalLawn']['hiddenOriginalGroups']}
        proof=audit.check_runtime_detail(runtime,qa,managed,hidden,transition)
        self.assertEqual(proof['ownedManagedDetailGroups'],477)
        self.assertEqual(proof['transitionFixedDensityGroupsAbsentFromDetailScaling'],158)
        for actor in (next(iter(transition.values()))['actor'],next(iter(hidden.values()))['actor']):
            wrong=deepcopy(runtime);entry=deepcopy(wrong['detailLightingState'][0]);entry['actor']=actor
            wrong['detailLightingState'].append(entry);badqa={**qa,'detailLightingState':wrong['detailLightingState']}
            with self.assertRaisesRegex(RuntimeError,'Hidden old lawn|fixed-density'):audit.check_runtime_detail(wrong,badqa,managed,hidden,transition)


if __name__=='__main__':unittest.main()
