"""Isolated native TextureSourceEncoding inspection and linear GPU pixel probe.

Prepare/run use only a fresh output project. Three R8 texture packages are
copied unchanged at their original Content paths; only a diffuse duplicate in
the probe namespace is changed. No provider pixels are edited or converted.
"""
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[3 if Path(__file__).name=='probe-source.py'else 2]
OWNER='scripts/unreal/exterior-texture-encoding-probe.py'
ENGINE=Path('/Users/Shared/Epic Games/UE_5.8')
R8=ROOT/'output/unreal/exterior-20260930-r8'
IMPORT_SHA='1701f1eb8c1cba5a7bfce3c7f802dbecbd10cf84658d5649b7b365854f223fa3'
PACKAGE_SHA='717e4e6284564bb86ddd71a54dbc635e929cb47bbb1f4fab13ddcf389c32848b'
PROBE_PREFIX='/Game/Brezi/EncodingProbe'
SOURCE_HASHES={'albedo':'9ecd60bb97fa26139de6729b4baa817672acdee34f1853618c8930dde7833da7',
    'normal':'4bdcfe8df17aba2bca329cb2d785a7ee36f0aa7bebbbd29f29ebfdc36a47c093',
    'roughness':'9c38cdaa2f8cb926773ac4c2e306e14351373a8e4b551caf116c996ca5d4397e'}
COORDS=[(311,477),(731,1291),(1567,913),(1043,1707),(1781,187),(31,59),
    (1871,1811),(1031,997),(491,1357),(1361,327),(657,743),(1519,1503)]


def require(ok,message):
    if not ok:raise RuntimeError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def now():return datetime.now(timezone.utc).isoformat()
def write(path,value):
    with Path(path).open('x')as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def output_path(value):
    path=(ROOT/value).resolve()
    require(path.parent==ROOT/'output/unreal'and path.name.startswith('exterior-texture-encoding-probe-'),
        'Encoding probe requires a fresh dedicated output directory')
    return path


def pins(values):
    for path,value in values.items():require(sha(path)==value,'Probe input bytes differ: '+path)


def png_samples(path,coords,numeric_rows=False):
    """Decode original PNG byte filters and uint16 values, without image edits."""
    data=Path(path).read_bytes();require(data[:8]==b'\x89PNG\r\n\x1a\n','Source is not PNG')
    offset=8;chunks=[];idat=[];metadata=[]
    while offset<len(data):
        n=struct.unpack('>I',data[offset:offset+4])[0];kind=data[offset+4:offset+8];payload=data[offset+8:offset+8+n]
        crc=struct.unpack('>I',data[offset+8+n:offset+12+n])[0]
        require(zlib.crc32(kind+payload)==crc,'PNG chunk CRC mismatch')
        chunks.append(kind.decode('ascii'))
        if kind==b'IDAT':idat.append(payload)
        elif kind in (b'gAMA',b'sRGB',b'cHRM',b'iCCP'):metadata.append({'kind':kind.decode(),'payloadHex':payload.hex()})
        offset+=n+12
    width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',data[16:29])
    require(depth==16 and color==2 and compression==filtering==interlace==0,'Probe expects original noninterlaced16bit RGB diffuse')
    raw=zlib.decompress(b''.join(idat));bpp=6;stride=width*bpp
    require(len(raw)==height*(stride+1),'PNG byte stream length differs')
    wanted={y:[]for _,y in coords}
    for x,y in coords:require(0<=x<width and 0<=y<height,'Sample outside original PNG');wanted[y].append(x)
    previous=bytearray(stride);samples={};filters={};decoded_rows=[]
    for y in range(height if numeric_rows else max(wanted)+1):
        kind=raw[y*(stride+1)];filters[str(kind)]=filters.get(str(kind),0)+1
        row=bytearray(raw[y*(stride+1)+1:(y+1)*(stride+1)])
        require(kind<=4,'Unsupported PNG filter')
        for x in range(stride):
            left=row[x-bpp]if x>=bpp else 0;up=previous[x];ul=previous[x-bpp]if x>=bpp else 0
            if kind==1:predictor=left
            elif kind==2:predictor=up
            elif kind==3:predictor=(left+up)//2
            elif kind==4:
                p=left+up-ul;a,b,c=abs(p-left),abs(p-up),abs(p-ul)
                predictor=left if a<=b and a<=c else up if b<=c else ul
            else:predictor=0
            row[x]=(row[x]+predictor)&255
        for x in wanted.get(y,[]):samples[x,y]=list(struct.unpack('>HHH',row[x*bpp:x*bpp+6]))
        if numeric_rows:decoded_rows.append(bytes(row))
        previous=row
    result=[]
    for x,y in coords:
        integers=samples[x,y];encoded=[v/65535 for v in integers]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in encoded]
        result.append({'xy':[x,y],'uv':[(x+.5)/width,(y+.5)/height],
            'originalUint16Rgb':integers,'encodedNormalizedRgb':encoded,'expectedSrgbDecodedLinearRgb':linear})
    result={'sourcePath':str(Path(path).resolve()),'sourceSha256':sha(path),'width':width,'height':height,'bitDepth':depth,
        'colorType':color,'chunks':chunks,'embeddedColorMetadata':metadata,'decodedFilterRows':filters,'samples':result,
        'method':'Original byte-filtered uint16 PNG samples at exact texel centers; no pixels or files transformed.'}
    if numeric_rows:result['_numericRows']=decoded_rows
    return result


def source_selected_low_contrast(path):
    """Choose stable samples using source bytes only, before any GPU comparison."""
    data=png_samples(path,[(0,0)],numeric_rows=True);rows=data['_numericRows'];width=data['width'];height=data['height'];chosen=[]
    for region_y in range(3):
        for region_x in range(4):
            best=None
            for y in range(region_y*(height//3)+64,(region_y+1)*(height//3)-64,16):
                y-=y%4
                for x in range(region_x*(width//4)+64,(region_x+1)*(width//4)-64,16):
                    rgb=[struct.unpack('>HHH',rows[y+dy][(x+dx)*6:(x+dx)*6+6])for dy in range(4)for dx in range(4)]
                    mean=[sum(p[c]for p in rgb)/16/65535 for c in range(3)]
                    if not(.2<mean[0]<.75 and mean[0]>mean[1]>mean[2] and mean[2]>.03):continue
                    ranges=[(max(p[c]for p in rgb)-min(p[c]for p in rgb))/65535 for c in range(3)]
                    score=(max(ranges),sum(ranges),y,x)
                    if best is None or score<best[0]:best=(score,{'xy':[x+1,y+1],'region':[region_x,region_y],
                        'originalBlockOrigin':[x,y],'blockMeanEncodedRgb':mean,'blockRangeEncodedRgb':ranges})
            require(best is not None,'No stable brown source block in a fixed region');chosen.append(best[1])
    return {'policy':'Before native run, choose lowest maximum4x4 channel span on a16px source grid in each of12 fixed4x3 regions; brown encodedRGB .2<R<.75 andR>G>B>.03. No GPU values participate.',
        'samples':chosen,'comparisonAbsoluteTolerance':.015,'sharpOriginalSamplesAlsoRetained':True}


def prepare(value):
    out=output_path(value);require(not out.exists(),'Preserve prior encoding probe; use a fresh revision')
    require(sha(R8/'exterior-import-report.json')==IMPORT_SHA,'R8 import receipt differs')
    require(sha(R8/'model-package.json')==PACKAGE_SHA,'R8 package receipt differs')
    report=read(R8/'exterior-import-report.json');selected={}
    for role,value in SOURCE_HASHES.items():
        found=[r for r in report['materials']['textures'].values()if r['role']==role and r['sourceSha256']==value]
        require(len(found)==1,'Exact R8 floor texture is missing/ambiguous');selected[role]=found[0]
    project=out/'Project/EncodingProbe.uproject';project.parent.mkdir(parents=True)
    descriptor={'FileVersion':3,'EngineAssociation':'5.8','Category':'Editor Diagnostic',
        'Description':'Isolated source-encoding readback and unlit floating GPU samples only.',
        'DisableEnginePluginsByDefault':True,'Plugins':[{'Name':n,'Enabled':True,'TargetAllowList':['Editor']}
        for n in ('PythonScriptPlugin','EditorScriptingUtilities')],'TargetPlatforms':['Mac']}
    write(project,descriptor);config=project.parent/'Config/DefaultEngine.ini';config.parent.mkdir()
    config.write_text('[/Script/EngineSettings.GameMapsSettings]\nEditorStartupMap=/Engine/Maps/Entry\nGameDefaultMap=/Engine/Maps/Entry\n\n'
        '[/Script/UnrealEd.EditorLoadingSavingSettings]\nbAutoSaveEnable=False\n\n'
        '[/Script/Engine.RendererSettings]\nr.DefaultFeature.AutoExposure=False\n')
    protected={str(R8/'exterior-import-report.json'):IMPORT_SHA,str(R8/'model-package.json'):PACKAGE_SHA}
    input_pins={str(p):sha(p)for p in (Path(__file__).resolve(),project,config,ENGINE/'Engine/Build/Build.version')}
    records={}
    for role,row in selected.items():
        package=row['asset'].split('.',1)[0];relative=package.removeprefix('/Game/')
        source=R8/'Project/BreziTwin/Content'/(relative+'.uasset')
        require(source.is_file(),'Actual R8 texture package is missing');copied=[]
        for suffix in ('.uasset','.uexp','.ubulk'):
            p=source.with_suffix(suffix)
            if not p.exists():continue
            destination=project.parent/'Content'/(relative+suffix);destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,destination);value=sha(p);require(sha(destination)==value,'Texture copy is not byte exact')
            protected[str(p)]=value;input_pins[str(destination)]=value;copied.append({'source':str(p),'copy':str(destination),'sha256':value})
        protected[row['sourcePath']]=row['sourceSha256']
        require(sha(row['sourcePath'])==row['sourceSha256'],'Provider source bytes differ')
        records[role]={'asset':row['asset'],'package':package,'sourcePixels':{'path':row['sourcePath'],'sha256':row['sourceSha256']},'files':copied}
    stable=source_selected_low_contrast(selected['albedo']['sourcePath'])
    sample_data=png_samples(selected['albedo']['sourcePath'],COORDS+[tuple(row['xy'])for row in stable['samples']])
    sample_data['sourceOnlyLowContrastSelection']=stable
    sample_file=out/'provider-samples.json';write(sample_file,sample_data)
    input_pins[str(sample_file)]=sha(sample_file)
    code=out/'probe-source.py';shutil.copyfile(__file__,code);input_pins[str(code)]=sha(code)
    write(out/'prepared.json',{'schemaVersion':1,'owner':OWNER,'sourceSha256':sha(__file__),'status':'prepared-native-not-run',
        'generatedAtUtc':now(),'output':str(out),'project':str(project),'textures':records,'inputPins':input_pins,'protectedR8AndProviderPins':protected,
        'providerSamples':{'path':str(sample_file),'sha256':sha(sample_file)},'nativeScript':str(code),
        'r8ProjectAndPackageUnchanged':True,'providerPixelsConvertedOrEdited':False})
    print(json.dumps({'output':str(out),'project':str(project),'texturesCopied':3,'originalPixelSamples':len(sample_data['samples'])}))


def native():
    import unreal as u
    out=output_path(os.environ['BREZI_TEXTURE_ENCODING_PROBE']);prepared=read(out/'prepared.json')
    pins(prepared['inputPins']);pins(prepared['protectedR8AndProviderPins'])
    require(Path(u.Paths.project_dir()).resolve()==Path(prepared['project']).parent,'Wrong native probe project')
    report={'schemaVersion':1,'owner':OWNER,'sourceSha256':prepared['sourceSha256'],'status':'pending','startedAtUtc':now(),
        'nativeProcessId':os.getpid(),'engineVersion':u.SystemLibrary.get_engine_version(),'preparedSha256':sha(out/'prepared.json'),
        'textures':{},'gpuSamplingVerified':False,'r8AssetsUnchanged':False,'providerPixelsConvertedOrEdited':False}
    def settings(texture):
        color=texture.get_editor_property('source_color_settings');result={}
        for field in ('encoding_override','color_space','chromatic_adaptation_method','red_chromaticity_coordinate',
                'green_chromaticity_coordinate','blue_chromaticity_coordinate','white_chromaticity_coordinate'):
            v=color.get_editor_property(field)
            result[field]=[float(v.x),float(v.y)]if hasattr(v,'x')else str(v)
        props={k:str(texture.get_editor_property(k))for k in ('compression_settings','mip_gen_settings','filter','address_x','address_y')}
        props.update({k:texture.get_editor_property(k)for k in ('srgb','lod_bias','max_texture_size','never_stream','virtual_texture_streaming',
            'adjust_brightness','adjust_brightness_curve','adjust_saturation','adjust_hue')})
        return {'sourceColorSettings':result,'properties':props,'dimensions':[texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]}
    try:
        assets=u.EditorAssetLibrary;tools=u.AssetToolsHelpers.get_asset_tools();lib=u.MaterialEditingLibrary
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(levels.load_level('/Engine/Maps/Entry'),'Cannot load isolated rendering world')
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();require(world is not None,'No isolated editor world for GPU draw')
        u.SystemLibrary.execute_console_command(world,'r.TextureStreaming 0')
        textures={role:assets.load_asset(row['package'])for role,row in prepared['textures'].items()}
        report['initialLoadedDimensions']={role:[t.blueprint_get_size_x(),t.blueprint_get_size_y()]for role,t in textures.items()}
        u.SystemLibrary.execute_console_command(world,'Editor.AsyncTextureCompilationFinishAll')
        u.SystemLibrary.execute_console_command(world,'r.TextureStreaming 0')
        report['transientRenderingCommands']=['r.TextureStreaming 0 before texture loads','Editor.AsyncTextureCompilationFinishAll','r.TextureStreaming 0']
        for role,texture in textures.items():
            require(texture and texture.get_path_name()==prepared['textures'][role]['asset'],'Copied texture path/class differs')
            report['textures'][role]={'asset':texture.get_path_name(),**settings(texture)}
        require(textures['albedo'].get_editor_property('srgb')is True,'Copied actual diffuse sRGB flag differs')
        fixed=assets.duplicate_asset(prepared['textures']['albedo']['package'],PROBE_PREFIX+'/T_Floor_ExplicitSourceSRGB')
        require(fixed is not None,'Cannot create owned diffuse duplicate')
        old_fixed=settings(fixed);color=fixed.get_editor_property('source_color_settings')
        color.set_editor_property('encoding_override',u.TextureSourceEncoding.TSE_S_RGB)
        fixed.set_editor_property('source_color_settings',color)
        u.SystemLibrary.execute_console_command(world,'Editor.AsyncTextureCompilationFinishAll')
        require(assets.save_loaded_asset(fixed,only_if_is_dirty=False),'Cannot save explicit-source-encoding duplicate')
        report['correctedDuplicate']={'asset':fixed.get_path_name(),'before':old_fixed,'after':settings(fixed),
            'onlyIntendedChange':'source_color_settings.encoding_override=TSE_S_RGB'}
        for role,texture in textures.items():require(settings(texture)=={k:v for k,v in report['textures'][role].items()if k!='asset'},'Original copied texture readback changed')
        require(all(settings(t)['dimensions']==[2048,2048]for t in [*textures.values(),fixed]),'Full2048 native texture compilation not verified')
        report['fullTextureDimensionsVerified']=True
        target=u.RenderingLibrary.create_render_target2d(world,8,8,u.TextureRenderTargetFormat.RTF_RGBA32F,u.LinearColor(0,0,0,0),False,False)
        report['renderTarget']={'format':str(target.get_editor_property('render_target_format')),
            'linearGammaVerification':'RGBA32F actual raw GPU control required; force_linear_gamma is not a reflected property in local5.8.',
            'width':8,'height':8,'readback':'RenderingLibrary.read_render_target_raw_pixel(normalize=False)','sceneExposureAndToneMappingUsed':False}
        def material(name):
            m=tools.create_asset(name,PROBE_PREFIX,u.Material,u.MaterialFactoryNew())
            m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
            return m
        def draw(m):
            u.RenderingLibrary.clear_render_target2d(world,target,u.LinearColor(-.02,-.02,-.02,0))
            u.RenderingLibrary.draw_material_to_render_target(world,target,m)
            v=u.RenderingLibrary.read_render_target_raw_pixel(world,target,4,4,False)
            return [float(v.r),float(v.g),float(v.b),float(v.a)]
        control=material('M_LinearControl');v=lib.create_material_expression(control,u.MaterialExpressionConstant3Vector,0,0)
        v.set_editor_property('constant',u.LinearColor(.125,.25,.5,1))
        require(lib.connect_material_property(v,'',u.MaterialProperty.MP_EMISSIVE_COLOR),'Control emissive link failed')
        require(not list(lib.recompile_material(control)or[]),'Control material compiler errors')
        assets.save_loaded_asset(control,only_if_is_dirty=False)
        readback=draw(control);report['gpuLinearControl']={'expected':[.125,.25,.5],'actual':readback,'absoluteTolerance':.002}
        require(max(abs(a-b)for a,b in zip(readback[:3],[.125,.25,.5]))<.002,'GPU linear control failed; pixel sampling is unverified')
        m=material('M_OriginalAndCorrectedSample');sample=lib.create_material_expression(m,u.MaterialExpressionTextureSampleParameter2D,300,0)
        sample.set_editor_property('parameter_name','ProbeTexture');sample.set_editor_property('texture',textures['albedo'])
        sample.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR)
        sample.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_LEVEL);sample.set_editor_property('const_mip_value',0)
        sample.set_editor_property('automatic_view_mip_bias',False)
        mip=lib.create_material_expression(m,u.MaterialExpressionConstant,150,150);mip.set_editor_property('r',0.)
        uv=lib.create_material_expression(m,u.MaterialExpressionVectorParameter,0,0);uv.set_editor_property('parameter_name','ProbeUV')
        mask=lib.create_material_expression(m,u.MaterialExpressionComponentMask,150,0)
        for field,value in [('r',True),('g',True),('b',False),('a',False)]:mask.set_editor_property(field,value)
        report['samplingExpressionPins']={'textureInputs':list(lib.get_material_expression_input_names(sample)),
            'textureOutputs':list(lib.get_material_expression_output_names(sample)),
            'uvToRG':lib.connect_material_expressions(uv,'',mask,''),
            'rgToTextureCoordinates':lib.connect_material_expressions(mask,'',sample,'UVs'),
            'explicitMipZero':lib.connect_material_expressions(mip,'',sample,'Level'),
            'firstRgbOutputToEmissive':lib.connect_material_property(sample,'',u.MaterialProperty.MP_EMISSIVE_COLOR)}
        require(all(report['samplingExpressionPins'][k]for k in ('uvToRG','rgToTextureCoordinates','explicitMipZero','firstRgbOutputToEmissive')),'Texture sample links failed')
        report['sampleMipProperties']={'mipValueMode':str(sample.get_editor_property('mip_value_mode')),
            'constMipValue':sample.get_editor_property('const_mip_value'),
            'automaticViewMipBias':sample.get_editor_property('automatic_view_mip_bias')}
        require(not list(lib.recompile_material(m)or[]),'Sampling material compiler errors');assets.save_loaded_asset(m,only_if_is_dirty=False)
        mic=tools.create_asset('MI_PixelSample',PROBE_PREFIX,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        lib.set_material_instance_parent(mic,m);expected=read(prepared['providerSamples']['path']);rows=[]
        for point in expected['samples']:
            lib.set_material_instance_vector_parameter_value(mic,'ProbeUV',u.LinearColor(*point['uv'],0,0));record=dict(point)
            actual_uv=lib.get_material_instance_vector_parameter_value(mic,'ProbeUV');record['nativeParameterUv']=[float(actual_uv.r),float(actual_uv.g)]
            for name,texture in [('original',textures['albedo']),('explicitSourceSRGB',fixed)]:
                lib.set_material_instance_texture_parameter_value(mic,'ProbeTexture',texture);lib.update_material_instance(mic)
                record[name+'GpuLinearRgba']=draw(mic)
            rows.append(record)
        u.SystemLibrary.execute_console_command(world,'ListTextures')
        report['gpuSamples']=rows;report['gpuSamplingVerified']=True;report['status']='native-source-encoding-and-gpu-samples-recorded'
    except Exception as error:
        report['status']='failed-preserved-native-attempt';report['error']=str(error);raise
    finally:
        try:pins(prepared['protectedR8AndProviderPins']);pins(prepared['inputPins']);report['r8AssetsUnchanged']=True;report['originalCopiedTextureBytesUnchanged']=True
        except Exception as error:report['protectedByteVerificationError']=str(error)
        report['endedAtUtc']=now();write(out/'native-report.json',report)


def run(value):
    out=output_path(value);prepared=read(out/'prepared.json');pins(prepared['inputPins']);pins(prepared['protectedR8AndProviderPins'])
    require(not(out/'native-process.json').exists(),'Preserve previous native probe attempt')
    argv=[str(ENGINE/'Engine/Binaries/Mac/UnrealEditor-Cmd'),prepared['project'],'-run=pythonscript',
        '-script='+prepared['nativeScript'],'-AllowCommandletRendering','-metal','-NoTextureStreaming','-unattended','-nop4','-nosplash']
    process={'command':argv,'startedAtUtc':now(),'preparedSha256':sha(out/'prepared.json')}
    with(out/'native.log').open('xb')as log:
        child=subprocess.Popen(argv,cwd=ROOT,env={**os.environ,'BREZI_TEXTURE_ENCODING_PROBE':str(out)},stdout=log,stderr=subprocess.STDOUT)
        process['pid']=child.pid;process['returncode']=child.wait()
    process.update(endedAtUtc=now(),logSha256=sha(out/'native.log'));write(out/'native-process.json',process)
    pins(prepared['protectedR8AndProviderPins']);pins(prepared['inputPins'])
    print(json.dumps({'output':str(out),'returncode':process['returncode'],'nativeReport':str(out/'native-report.json'),
        'nativeLog':str(out/'native.log'),'r8AndProviderPinsUnchanged':True}))
    require(process['returncode']==0,'Native encoding probe failed; preserve logs and use a new revision for repair')


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--prepare':prepare(sys.argv[2])
    elif len(sys.argv)==3 and sys.argv[1]=='--run':run(sys.argv[2])
    else:native()
