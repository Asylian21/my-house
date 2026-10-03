"""Fresh R8-context colour-encoding probe; preparation never starts Unreal.

Reuses the immutable R7 probe's host helpers and native raw GPU method. Original
provider PNGs and R8 packages stay unchanged. RGBA16 alpha is numeric coverage,
never passed through the RGB sRGB transfer curve. Native execution is a separate
operator action after the parent finishes the R9 six-view job.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT=Path(__file__).resolve().parents[3 if Path(__file__).name=='context-probe-source.py'else 2]
OWNER='scripts/unreal/exterior-texture-encoding-context-probe.py'
DONOR=ROOT/'output/unreal/exterior-texture-encoding-probe-20260930-r7/probe-source.py'
DONOR_SHA='b45e9eea151aa59119bcb9897d98af565d1fdb0eacea0687fb17889ca34cce7c'
if hashlib.sha256(DONOR.read_bytes()).hexdigest()!=DONOR_SHA:raise RuntimeError('Frozen R7 probe source differs')
spec=importlib.util.spec_from_file_location('immutable_r7_encoding_probe',DONOR)
frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
require,sha,read,write,pins,now=frozen.require,frozen.sha,frozen.read,frozen.write,frozen.pins,frozen.now
R8,ENGINE,IMPORT_SHA,PACKAGE_SHA=frozen.R8,frozen.ENGINE,frozen.IMPORT_SHA,frozen.PACKAGE_SHA
PREFIX='/Game/Brezi/EncodingContextProbe'
ENV='BREZI_CONTEXT_TEXTURE_ENCODING_PROBE'
SOURCES={
 'farm_soil':'5b2aa6ce68bf82c1ae3b3433eeefc2a4ec6aae441740b6fbc42db16a2e2597b0',
 'nettle':'7b235e32340475f582baea7f5deb1b452f118c5ae61a68dca4001b0f7fbf97d3',
 'tree_small_02_trunk':'78a6bc3b6465277379cc7db062316ca34fd9f6334b112b0c279a1033d68c77e7',
 'shrub_04':'fc386b9d205ba38fc7cda66a2499680e6443a7b3fc91496a3d5890e4f98f71a4',
 'periwinkle':'2bd96cd167ea4a79a68a98b5de3b33be426c1d272024cde39bca9e8b98a4a33d'}


def output_path(value):
    path=(ROOT/value).resolve()
    require(path.parent==ROOT/'output/unreal'and path.name.startswith('exterior-texture-encoding-context-probe-'),
        'Context probe needs a fresh dedicated output/unreal directory')
    return path


def linear_srgb(value):return value/12.92 if value<=.04045 else((value+.055)/1.055)**2.4


def decode_png(path):
    """Exact PNG byte-filter decoding. No display conversion or file writes."""
    raw=Path(path).read_bytes();require(raw[:8]==b'\x89PNG\r\n\x1a\n','Provider is not PNG')
    offset=8;chunks=[];metadata=[];idat=[];header=None;finished=False
    while offset<len(raw):
        require(offset+12<=len(raw),'PNG chunk header truncated')
        size,=struct.unpack_from('>I',raw,offset);kind=raw[offset+4:offset+8];payload=raw[offset+8:offset+8+size]
        require(offset+12+size<=len(raw),'PNG chunk payload truncated')
        crc,=struct.unpack_from('>I',raw,offset+8+size)
        require(zlib.crc32(kind+payload)==crc,'PNG CRC differs')
        chunks.append(kind.decode('ascii'))
        if kind==b'IHDR':require(header is None and len(payload)==13,'PNG header differs');header=struct.unpack('>IIBBBBB',payload)
        elif kind==b'IDAT':idat.append(payload)
        elif kind in(b'gAMA',b'sRGB',b'cHRM',b'iCCP'):metadata.append({'kind':kind.decode(),'payloadHex':payload.hex()})
        elif kind==b'IEND':require(size==0,'PNG end differs');finished=True
        offset+=size+12
        if finished:break
    require(finished and offset==len(raw)and header is not None,'PNG trailing/missing chunks refused')
    width,height,depth,color,compression,filtering,interlace=header
    require(width>0 and height>0 and depth in(8,16)and color in(0,2,4,6)
        and compression==filtering==interlace==0,'Unsupported ordinary provider PNG')
    channels={0:1,2:3,4:2,6:4}[color];bpp=channels*(depth//8);stride=width*bpp
    encoded=zlib.decompress(b''.join(idat));require(len(encoded)==height*(stride+1),'PNG decompressed extent differs')
    previous=bytearray(stride);rows=[];filters={}
    for y in range(height):
        kind=encoded[y*(stride+1)];require(kind<=4,'PNG filter differs');filters[str(kind)]=filters.get(str(kind),0)+1
        row=bytearray(encoded[y*(stride+1)+1:(y+1)*(stride+1)])
        if kind:
            for x in range(stride):
                left=row[x-bpp]if x>=bpp else 0;up=previous[x];ul=previous[x-bpp]if x>=bpp else 0
                if kind==1:predictor=left
                elif kind==2:predictor=up
                elif kind==3:predictor=(left+up)//2
                else:
                    p=left+up-ul;a,b,c=abs(p-left),abs(p-up),abs(p-ul)
                    predictor=left if a<=b and a<=c else up if b<=c else ul
                row[x]=(row[x]+predictor)&255
        rows.append(bytes(row));previous=row
    return {'sourcePath':str(Path(path).resolve()),'sourceSha256':sha(path),'width':width,'height':height,
        'bitDepth':depth,'colorType':color,'channels':channels,'chunks':chunks,'embeddedColorMetadata':metadata,
        'decodedFilterRows':filters,'_rows':rows,'decodedNumericByteSha256':hashlib.sha256(b''.join(rows)).hexdigest()}


def pixel(source,x,y):
    require(0<=x<source['width']and 0<=y<source['height'],'Provider sample outside image')
    n=source['channels'];size=source['bitDepth']//8;start=x*n*size
    return struct.unpack('>'+('H'if size==2 else'B')*n,source['_rows'][y][start:start+n*size])


def source_alpha(source,x,y):
    value=pixel(source,x,y);maximum=(1<<source['bitDepth'])-1
    return value[-1]/maximum if source['colorType']in(4,6)else 1.


def alpha_mask(source,x,y):
    value=pixel(source,x,y);maximum=(1<<source['bitDepth'])-1
    # Separate provider opacity maps are linear scalar data; their first channel
    # is the recipe's actual mask. Embedded albedo alpha is recorded separately.
    return value[0]/maximum


def select_low_contrast(source,mask=None):
    require(source['bitDepth']==16 and source['colorType']in(2,6),'Only original RGB/RGBA16 albedo is probed')
    if mask:require((mask['width'],mask['height'])==(source['width'],source['height']),'Provider alpha-map dimensions differ')
    width,height=source['width'],source['height'];chosen=[];empty=[]
    for ry in range(3):
        for rx in range(4):
            best=None
            for y in range(ry*(height//3)+32,(ry+1)*(height//3)-32,16):
                y-=y%4
                for x in range(rx*(width//4)+32,(rx+1)*(width//4)-32,16):
                    points=[(x+dx,y+dy)for dy in range(4)for dx in range(4)]
                    rgb=[pixel(source,*p)[:3]for p in points]
                    mean=[sum(p[c]for p in rgb)/16/65535 for c in range(3)]
                    # Neutral, brown and green tissue all qualify. Black atlas
                    # backgrounds and transparency never become "stable" proof.
                    if not(.08<max(mean)<.85 and sum(mean)/3>.06):continue
                    alpha=min(source_alpha(source,*p)for p in points)
                    separate=min(alpha_mask(mask,*p)for p in points)if mask else 1.
                    if min(alpha,separate)<.98:continue
                    ranges=[(max(p[c]for p in rgb)-min(p[c]for p in rgb))/65535 for c in range(3)]
                    score=(max(ranges),sum(ranges),y,x)
                    if best is None or score<best[0]:best=(score,{'xy':[x+1,y+1],'region':[rx,ry],
                        'originalBlockOrigin':[x,y],'blockMeanEncodedRgb':mean,'blockRangeEncodedRgb':ranges,
                        'minimumEmbeddedAlpha':alpha,'minimumSeparateMask':separate})
            if best is None:empty.append({'region':[rx,ry],'reason':'No opaque non-background source 4x4 block satisfies declared source-only gates'})
            elif best[0][0]>.03:empty.append({'region':[rx,ry],'reason':'Lowest source-only block RGB span exceeds fixed .03 ceiling',
                'lowestAvailableMaximumEncodedChannelSpan':best[0][0]})
            else:chosen.append(best[1])
    require(len(chosen)>=6,'Fewer than six independent visible low-contrast source regions; do not force a sample pass')
    return {'policy':'Source only: fixed4x3 regions,16px grid,4x4 blocks aligned to4px. Lowest(max RGB span,sum RGB spans,y,x). .08<max mean<.85,mean RGB>.06, embedded alpha and separate mask>=.98, maximum block RGB span<=.03. Empty or high-contrast regions disclosed; no GPU values or colour-family preference.',
        'samples':chosen,'unavailableRegions':empty,'comparisonAbsoluteTolerance':.015,'alphaComparisonAbsoluteTolerance':.005,
        'maximumBlockEncodedChannelSpan':.03,
        'fourByFourBlockSelectionBeforeAnyNativeRun':True,'gpuValuesParticipated':False}


def provider_samples(source,coords,mask=None):
    result={k:v for k,v in source.items()if k!='_rows'};samples=[]
    for x,y in coords:
        original=list(pixel(source,x,y));rgb=original[:3];encoded=[v/65535 for v in rgb]
        alpha=source_alpha(source,x,y)
        point={'xy':[x,y],'uv':[(x+.5)/source['width'],(y+.5)/source['height']],
            'originalUint16Rgb':rgb,'originalUint16Channels':original,'encodedNormalizedRgb':encoded,
            'expectedSrgbDecodedLinearRgb':[linear_srgb(v)for v in encoded],
            'originalUint16Alpha':original[3]if source['colorType']==6 else None,
            'expectedUnchangedLinearAlpha':alpha,'alphaTransferCurveApplied':False}
        if mask:point['originalSeparateMaskChannels']=list(pixel(mask,x,y));point['expectedUnchangedSeparateMask']=alpha_mask(mask,x,y)
        samples.append(point)
    result.update(samples=samples,method='Exact source uint16 channels at texel centres; sRGB transfer on RGB only; unchanged numeric alpha; no image edits or conversion.')
    if mask:result['separateAlphaSource']={k:v for k,v in mask.items()if k!='_rows'}
    return result


def prepare(value):
    out=output_path(value);require(not out.exists(),'Preserve existing context probe; use a fresh revision')
    require(sha(R8/'exterior-import-report.json')==IMPORT_SHA and sha(R8/'model-package.json')==PACKAGE_SHA,'Frozen R8 receipt differs')
    report=read(R8/'exterior-import-report.json');textures=report['materials']['textures'];materials=report['materials']['materials']
    project=out/'Project/EncodingContextProbe.uproject';project.parent.mkdir(parents=True)
    descriptor={'FileVersion':3,'EngineAssociation':'5.8','Category':'Editor Diagnostic',
        'Description':'Isolated original-versus-explicit-source-sRGB raw floating GPU probe; not a model project.',
        'DisableEnginePluginsByDefault':True,'Plugins':[{'Name':n,'Enabled':True,'TargetAllowList':['Editor']}
        for n in('PythonScriptPlugin','EditorScriptingUtilities')],'TargetPlatforms':['Mac']}
    write(project,descriptor);config=project.parent/'Config/DefaultEngine.ini';config.parent.mkdir()
    config.write_text('[/Script/EngineSettings.GameMapsSettings]\nEditorStartupMap=/Engine/Maps/Entry\nGameDefaultMap=/Engine/Maps/Entry\n\n'
        '[/Script/UnrealEd.EditorLoadingSavingSettings]\nbAutoSaveEnable=False\n\n[/Script/Engine.RendererSettings]\nr.DefaultFeature.AutoExposure=False\n')
    protected={str(R8/'exterior-import-report.json'):IMPORT_SHA,str(R8/'model-package.json'):PACKAGE_SHA,str(DONOR):DONOR_SHA}
    input_pins={str(p):sha(p)for p in(Path(__file__).resolve(),project,config,ENGINE/'Engine/Build/Build.version')}
    records={};provider={};copied={}
    def copy_texture(row):
        package=row['asset'].split('.',1)[0];relative=package.removeprefix('/Game/');files=[]
        for suffix in('.uasset','.uexp','.ubulk'):
            source=R8/'Project/BreziTwin/Content'/(relative+suffix)
            if not source.exists():continue
            destination=project.parent/'Content'/(relative+suffix);destination.parent.mkdir(parents=True,exist_ok=True)
            if str(source)not in copied:
                shutil.copyfile(source,destination);value=sha(source);require(sha(destination)==value,'R8 package copy differs')
                copied[str(source)]=value;protected[str(source)]=value;input_pins[str(destination)]=value
            files.append({'source':str(source),'copy':str(destination),'sha256':copied[str(source)]})
        require(any(r['source'].endswith('.uasset')for r in files),'Actual R8 texture package missing')
        protected[row['sourcePath']]=row['sourceSha256'];require(sha(row['sourcePath'])==row['sourceSha256'],'Provider source changed')
        return {'asset':row['asset'],'package':package,'sourcePixels':{'path':row['sourcePath'],'sha256':row['sourceSha256']},'files':files}
    for name,source_sha in SOURCES.items():
        selected=[r for r in textures.values()if r['role']=='albedo'and r['sourceSha256']==source_sha]
        require(len(selected)==1,'Exact requested R8 albedo missing or ambiguous: '+name);row=selected[0]
        bound={key:r for key,r in materials.items()if r['recipe'].get('maps',{}).get('albedo',{}).get('sha256')==source_sha}
        require(bound,'Albedo has no actual R8 material binding');record=copy_texture(row)
        record['r8MaterialKeys']=list(bound);record['sourceLicense']=row['sourceLicense'];record['sourcePage']=row['sourcePage']
        alpha_sources={json.dumps(r['recipe']['maps']['alpha'],sort_keys=True)for r in bound.values()if'alpha'in r['recipe'].get('maps',{})}
        require(len(alpha_sources)<=1,'Albedo uses inconsistent original alpha sources');mask=None
        if alpha_sources:
            alpha=json.loads(next(iter(alpha_sources)));alpha_rows=[r for r in textures.values()if r['role']=='alpha'and r['sourceSha256']==alpha['sha256']]
            require(len(alpha_rows)==1,'Actual R8 alpha texture missing or ambiguous');record['separateAlpha']=copy_texture(alpha_rows[0]);mask=decode_png(alpha['path'])
        decoded=decode_png(row['sourcePath']);stable=select_low_contrast(decoded,mask)
        coords=list(frozen.COORDS)+[tuple(p['xy'])for p in stable['samples']]
        samples=provider_samples(decoded,coords,mask);samples['sourceOnlyLowContrastSelection']=stable
        if decoded['colorType']==2:
            reference=frozen.png_samples(row['sourcePath'],frozen.COORDS)
            require(all(a['originalUint16Rgb']==b['originalUint16Rgb']for a,b in zip(samples['samples'],reference['samples'])),
                'Extended decoder disagrees with frozen R7 RGB16 decoder')
            samples['frozenR7Rgb16SampleAgreement']=True
        sample_file=out/(name+'-provider-samples.json');write(sample_file,samples);input_pins[str(sample_file)]=sha(sample_file)
        record['providerSamples']={'path':str(sample_file),'sha256':sha(sample_file)};records[name]=record;provider[name]=record['providerSamples']
        print(json.dumps({'preparedSource':name,'colorType':decoded['colorType'],'visibleStableRegions':len(stable['samples']),
            'unavailableRegions':stable['unavailableRegions']}),flush=True)
    code=out/'context-probe-source.py';shutil.copyfile(__file__,code);input_pins[str(code)]=sha(code)
    test_receipt=self_test(out);input_pins[str(test_receipt)]=sha(test_receipt)
    pins(protected);pins(input_pins)
    write(out/'prepared.json',{'schemaVersion':1,'owner':OWNER,'sourceSha256':sha(__file__),'status':'prepared-native-not-run',
        'generatedAtUtc':now(),'output':str(out),'project':str(project),'textures':records,'inputPins':input_pins,'protectedR8AndProviderPins':protected,
        'providerSamples':provider,'nativeScript':str(code),'frozenR7Source':{'path':str(DONOR),'sha256':DONOR_SHA},
        'preparationTests':{'path':str(test_receipt),'sha256':sha(test_receipt)},'nativeRunAuthorized':False,
        'providerPixelsConvertedOrEdited':False,'originalAlphaTransferCurveApplied':False,'r8ProjectAndPackageUnchanged':True,
        'gpuSamplingVerified':False,'materialCorrectionsApplied':False})
    print(json.dumps({'output':str(out),'project':str(project),'albedosCopied':5,'separateAlphaTexturesCopied':3,'status':'prepared-native-not-run'}))


def self_test(out):
    def make_png(path,depth,color,pixels):
        channels={0:1,2:3,4:2,6:4}[color];width=len(pixels[0]);bpp=channels*(depth//8);previous=bytes(width*bpp);encoded=[]
        for y,values in enumerate(pixels):
            row=b''.join(struct.pack('>'+('H'if depth==16 else'B')*channels,*v)for v in values);kind=y%5;filtered=bytearray(row)
            for i,v in enumerate(row):
                left=row[i-bpp]if i>=bpp else 0;up=previous[i];ul=previous[i-bpp]if i>=bpp else 0
                if kind==0:p=0
                elif kind==1:p=left
                elif kind==2:p=up
                elif kind==3:p=(left+up)//2
                else:
                    q=left+up-ul;a,b,c=abs(q-left),abs(q-up),abs(q-ul);p=left if a<=b and a<=c else up if b<=c else ul
                filtered[i]=(v-p)&255
            encoded.append(bytes([kind])+filtered);previous=row
        def chunk(kind,payload):return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload))
        path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,len(pixels),depth,color,0,0,0))+
            chunk(b'IDAT',zlib.compress(b''.join(encoded)))+chunk(b'IEND',b''))
    checks=[]
    with tempfile.TemporaryDirectory(dir=out,prefix='prepare-selftest-')as temp:
        temp=Path(temp)
        for depth,color in((16,2),(16,6),(8,0)):
            channels={2:3,6:4,0:1}[color];maximum=(1<<depth)-1
            values=[[tuple((x*2771+y*131+c*9389)%maximum for c in range(channels))for x in range(7)]for y in range(10)]
            path=temp/f'exact-{depth}-{color}.png';make_png(path,depth,color,values);decoded=decode_png(path)
            require(decoded['decodedFilterRows']=={str(k):2 for k in range(5)},'Selftest did not cover all PNG filters')
            require(all(pixel(decoded,x,y)==values[y][x]for y in range(10)for x in range(7)),'Original PNG integer decoding differs')
            if color==6:
                sample=provider_samples(decoded,[(2,3)])['samples'][0]
                require(sample['originalUint16Alpha']==values[3][2][3]and sample['expectedUnchangedLinearAlpha']==values[3][2][3]/65535
                    and sample['alphaTransferCurveApplied']is False,'RGBA alpha was transformed')
            checks.append('exact-all-five-filter-'+str(depth)+'bit-color'+str(color))
            if depth==16 and color==2:
                reference=frozen.png_samples(path,[(x,y)for y in range(10)for x in range(7)])
                require(all(p['originalUint16Rgb']==list(values[p['xy'][1]][p['xy'][0]])for p in reference['samples']),
                    'Frozen R7 decoder fixture agreement failed')
                checks.append('unchanged-r7-rgb16-decoder-agreement')
        path=temp/'bad-crc.png';raw=bytearray((temp/'exact-16-6.png').read_bytes());raw[29]^=1;path.write_bytes(raw)
        try:decode_png(path)
        except RuntimeError:checks.append('reject-invalid-provider-crc')
        else:raise RuntimeError('Bad PNG CRC accepted')
        # Opaque, varied RGB fixture proves regional ordering and tie-breaks are
        # deterministic before any GPU job. The expected alpha is never sRGB.
        path=temp/'selection.png';values=[[tuple([15000+x%7,24000+y%9,11000,65535])for x in range(384)]for y in range(288)]
        make_png(path,16,6,values);source=decode_png(path);a=select_low_contrast(source);b=select_low_contrast(source)
        require(a==b and len(a['samples'])==12 and a['gpuValuesParticipated']is False,'Source-only sample selection differs')
        checks.append('deterministic-visible-twelve-region-source-only-selection')
        require(abs(linear_srgb(.5)-.21404114048223255)<1e-15 and linear_srgb(0)==0 and linear_srgb(1)==1,'sRGB transfer differs')
        checks.append('rgb-transfer-reference-values-alpha-independent')
        try:output_path('output/unreal/exterior-20260930-r8')
        except RuntimeError:checks.append('reject-shared-model-output-path')
        else:raise RuntimeError('Shared model output allowed')
        try:run(out,False)
        except RuntimeError:checks.append('reject-native-launch-without-after-r9-authorization')
        else:raise RuntimeError('Unauthorised native process allowed')
    path=out/'preparation-tests.json';write(path,{'schema':1,'owner':OWNER,'sourceSha256':sha(__file__),'status':'PASS_SOURCE_PREPARATION_ONLY',
        'checks':checks,'checkCount':len(checks),'nativeProcessesStarted':0,'providerOrR8ImagesEdited':False})
    return path


def native():
    """Same controlled RGBA32F method as immutable R7, now for five albedos."""
    import unreal as u
    out=output_path(os.environ[ENV]);prepared=read(out/'prepared.json');pins(prepared['inputPins']);pins(prepared['protectedR8AndProviderPins'])
    require(Path(u.Paths.project_dir()).resolve()==Path(prepared['project']).parent,'Wrong isolated context probe project')
    report={'schemaVersion':1,'owner':OWNER,'sourceSha256':prepared['sourceSha256'],'status':'pending','startedAtUtc':now(),
        'nativeProcessId':os.getpid(),'engineVersion':u.SystemLibrary.get_engine_version(),'preparedSha256':sha(out/'prepared.json'),
        'textures':{},'gpuSamplingVerified':False,'r8AssetsUnchanged':False,'providerPixelsConvertedOrEdited':False,'materialCorrectionsApplied':False}
    def settings(texture):
        color=texture.get_editor_property('source_color_settings');result={}
        for field in('encoding_override','color_space','chromatic_adaptation_method','red_chromaticity_coordinate',
            'green_chromaticity_coordinate','blue_chromaticity_coordinate','white_chromaticity_coordinate'):
            v=color.get_editor_property(field);result[field]=[float(v.x),float(v.y)]if hasattr(v,'x')else str(v)
        props={k:str(texture.get_editor_property(k))for k in('compression_settings','mip_gen_settings','filter','address_x','address_y')}
        props.update({k:texture.get_editor_property(k)for k in('srgb','lod_bias','max_texture_size','never_stream','virtual_texture_streaming',
            'adjust_brightness','adjust_brightness_curve','adjust_saturation','adjust_hue')})
        return {'sourceColorSettings':result,'properties':props,'dimensions':[texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]}
    try:
        assets=u.EditorAssetLibrary;tools=u.AssetToolsHelpers.get_asset_tools();lib=u.MaterialEditingLibrary
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(levels.load_level('/Engine/Maps/Entry'),'No isolated probe world')
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();require(world is not None,'No GPU rendering world')
        u.SystemLibrary.execute_console_command(world,'r.TextureStreaming 0')
        loaded={name:assets.load_asset(row['package'])for name,row in prepared['textures'].items()}
        alpha_loaded={name:assets.load_asset(row['separateAlpha']['package'])for name,row in prepared['textures'].items()if'separateAlpha'in row}
        u.SystemLibrary.execute_console_command(world,'Editor.AsyncTextureCompilationFinishAll')
        u.SystemLibrary.execute_console_command(world,'r.TextureStreaming 0')
        original_settings={};duplicates={}
        for name,texture in loaded.items():
            row=prepared['textures'][name];require(texture and texture.get_path_name()==row['asset'],'Copied albedo path/class differs')
            original_settings[name]=settings(texture);require(original_settings[name]['dimensions']==[2048,2048],'Full2048 texture not compiled')
            require(texture.get_editor_property('srgb')is True,'Original albedo sRGB flag differs')
            fixed=assets.duplicate_asset(row['package'],PREFIX+'/T_'+name+'_ExplicitSourceSRGB');require(fixed is not None,'Duplicate creation failed')
            before=settings(fixed);color=fixed.get_editor_property('source_color_settings');color.set_editor_property('encoding_override',u.TextureSourceEncoding.TSE_S_RGB)
            fixed.set_editor_property('source_color_settings',color);u.SystemLibrary.execute_console_command(world,'Editor.AsyncTextureCompilationFinishAll')
            require(assets.save_loaded_asset(fixed,only_if_is_dirty=False),'Cannot save owned explicit-sRGB duplicate')
            after=settings(fixed);expected=json.loads(json.dumps(original_settings[name]));expected['sourceColorSettings']['encoding_override']=str(u.TextureSourceEncoding.TSE_S_RGB)
            require(after==expected,'Duplicate changed settings beyond source encoding');duplicates[name]=fixed
            report['textures'][name]={'original':{'asset':texture.get_path_name(),**original_settings[name]},'duplicate':{'asset':fixed.get_path_name(),'before':before,'after':after},
                'onlyIntendedChange':'source_color_settings.encoding_override=TSE_S_RGB'}
        for name,texture in alpha_loaded.items():
            require(texture and settings(texture)['dimensions']==[2048,2048],'Separate alpha texture not compiled')
            report['textures'][name]['separateAlphaOriginal']={'asset':texture.get_path_name(),**settings(texture)}
        report['fullTextureDimensionsVerified']=True
        target=u.RenderingLibrary.create_render_target2d(world,8,8,u.TextureRenderTargetFormat.RTF_RGBA32F,u.LinearColor(0,0,0,0),False,False)
        report['renderTarget']={'format':str(target.get_editor_property('render_target_format')),'width':8,'height':8,
            'readback':'RenderingLibrary.read_render_target_raw_pixel(normalize=False)','sceneExposureAndToneMappingUsed':False,
            'alphaMethod':'Texture A sampled separately as emissive RGB; target alpha is not treated as texture alpha.'}
        def material(name):
            m=tools.create_asset(name,PREFIX,u.Material,u.MaterialFactoryNew());m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);return m
        def draw(m):
            u.RenderingLibrary.clear_render_target2d(world,target,u.LinearColor(-.02,-.02,-.02,0))
            u.RenderingLibrary.draw_material_to_render_target(world,target,m);v=u.RenderingLibrary.read_render_target_raw_pixel(world,target,4,4,False)
            return [float(v.r),float(v.g),float(v.b),float(v.a)]
        control=material('M_LinearControl');constant=lib.create_material_expression(control,u.MaterialExpressionConstant3Vector,0,0)
        constant.set_editor_property('constant',u.LinearColor(.125,.25,.5,1));require(lib.connect_material_property(constant,'',u.MaterialProperty.MP_EMISSIVE_COLOR),'Control emissive failed')
        require(not list(lib.recompile_material(control)or[]),'Control compile failed');assets.save_loaded_asset(control,only_if_is_dirty=False)
        actual=draw(control);report['gpuLinearControl']={'expected':[.125,.25,.5],'actual':actual,'absoluteTolerance':.002}
        require(max(abs(a-b)for a,b in zip(actual[:3],[.125,.25,.5]))<.002,'Raw GPU linear control failed')
        def sample_material(name,texture,channel):
            m=material(name);sample=lib.create_material_expression(m,u.MaterialExpressionTextureSampleParameter2D,300,0)
            sample.set_editor_property('parameter_name','ProbeTexture');sample.set_editor_property('texture',texture)
            sample.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR)
            sample.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_LEVEL);sample.set_editor_property('const_mip_value',0)
            sample.set_editor_property('automatic_view_mip_bias',False)
            mip=lib.create_material_expression(m,u.MaterialExpressionConstant,150,150);mip.set_editor_property('r',0.)
            uv=lib.create_material_expression(m,u.MaterialExpressionVectorParameter,0,0);uv.set_editor_property('parameter_name','ProbeUV')
            mask=lib.create_material_expression(m,u.MaterialExpressionComponentMask,150,0)
            for field,value in(('r',True),('g',True),('b',False),('a',False)):mask.set_editor_property(field,value)
            links={'uvToRG':lib.connect_material_expressions(uv,'',mask,''),'rgToUv':lib.connect_material_expressions(mask,'',sample,'UVs'),
                'mipZero':lib.connect_material_expressions(mip,'',sample,'Level'),'textureToEmissive':lib.connect_material_property(sample,channel,u.MaterialProperty.MP_EMISSIVE_COLOR)}
            require(all(links.values()),'Sample material links failed');require(not list(lib.recompile_material(m)or[]),'Sample material compile failed')
            assets.save_loaded_asset(m,only_if_is_dirty=False)
            mic=tools.create_asset('MI_'+name,PREFIX,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());lib.set_material_instance_parent(mic,m)
            return mic,{'links':links,'textureOutputs':list(lib.get_material_expression_output_names(sample)),'emissiveSource':channel or'first RGB',
                'explicitMipLevel':0,'automaticViewMipBias':False}
        first=loaded[next(iter(loaded))];rgb_mic,rgb_proof=sample_material('M_ColourMipZero',first,'')
        alpha_mic,alpha_proof=sample_material('M_EmbeddedAlphaMipZero',first,'A');report['samplingExpressions']={'rgb':rgb_proof,'alpha':alpha_proof}
        for name,original in loaded.items():
            expected=read(prepared['textures'][name]['providerSamples']['path']);rows=[]
            for point in expected['samples']:
                record=dict(point)
                for channel,mic in(('Rgb',rgb_mic),('Alpha',alpha_mic)):
                    lib.set_material_instance_vector_parameter_value(mic,'ProbeUV',u.LinearColor(*point['uv'],0,0))
                    for label,texture in(('original',original),('explicitSourceSRGB',duplicates[name])):
                        lib.set_material_instance_texture_parameter_value(mic,'ProbeTexture',texture);lib.update_material_instance(mic)
                        record[label+'GpuLinear'+channel+'Rgba']=draw(mic)
                rows.append(record)
            report['textures'][name]['gpuSamples']=rows
            stable={tuple(p['xy'])for p in expected['sourceOnlyLowContrastSelection']['samples']};stable_rows=[r for r in rows if tuple(r['xy'])in stable]
            report['textures'][name]['sourceOnlyStableComparison']={
                'absoluteToleranceRgb':.015,'absoluteToleranceAlpha':.005,'count':len(stable_rows),
                'originalMaxAbsLinearRgbError':max(abs(a-b)for r in stable_rows for a,b in zip(r['originalGpuLinearRgbRgba'][:3],r['expectedSrgbDecodedLinearRgb'])),
                'explicitSourceSRGBMaxAbsLinearRgbError':max(abs(a-b)for r in stable_rows for a,b in zip(r['explicitSourceSRGBGpuLinearRgbRgba'][:3],r['expectedSrgbDecodedLinearRgb'])),
                'originalVsExplicitMaxAbsAlphaDifference':max(abs(a-b)for r in stable_rows for a,b in zip(r['originalGpuLinearAlphaRgba'][:3],r['explicitSourceSRGBGpuLinearAlphaRgba'][:3])),
                'explicitSourceSRGBMaxAbsAlphaError':max(abs(a-r['expectedUnchangedLinearAlpha'])for r in stable_rows for a in r['explicitSourceSRGBGpuLinearAlphaRgba'][:3])}
            alpha_difference=max(abs(a-b)for r in rows for a,b in zip(r['originalGpuLinearAlphaRgba'][:3],r['explicitSourceSRGBGpuLinearAlphaRgba'][:3]))
            report['textures'][name]['allSamplesAlphaComparison']={'count':len(rows),'absoluteTolerance':.005,
                'includesSharpAndPartialAlphaSourceSamples':True,'originalVsExplicitMaxAbsAlphaDifference':alpha_difference,
                'unchangedWithinTolerance':alpha_difference<=.005,
                'originalMaxAbsSourceAlphaError':max(abs(a-r['expectedUnchangedLinearAlpha'])for r in rows for a in r['originalGpuLinearAlphaRgba'][:3]),
                'explicitMaxAbsSourceAlphaError':max(abs(a-r['expectedUnchangedLinearAlpha'])for r in rows for a in r['explicitSourceSRGBGpuLinearAlphaRgba'][:3])}
            require(alpha_difference<=.005,'Explicit source-RGB encoding changed sampled alpha; preserve failed diagnostic without corrections')
        for name,texture in loaded.items():require(settings(texture)==original_settings[name],'Original copied albedo settings changed')
        report['gpuSamplingVerified']=True;report['status']='native-source-encoding-and-gpu-samples-recorded-no-material-correction'
    except Exception as error:report['status']='failed-preserved-native-attempt';report['error']=str(error);raise
    finally:
        try:pins(prepared['protectedR8AndProviderPins']);pins(prepared['inputPins']);report['r8AssetsUnchanged']=True;report['originalCopiedTextureBytesUnchanged']=True
        except Exception as error:report['protectedByteVerificationError']=str(error)
        report['endedAtUtc']=now();write(out/'native-report.json',report)


def run(value,authorized=False):
    require(authorized,'Native run is separate and requires the parent authorization after R9 six-view completion')
    out=output_path(value);prepared=read(out/'prepared.json');pins(prepared['inputPins']);pins(prepared['protectedR8AndProviderPins'])
    require(not(out/'native-process.json').exists(),'Preserve prior context-native probe attempt')
    argv=[str(ENGINE/'Engine/Binaries/Mac/UnrealEditor-Cmd'),prepared['project'],'-run=pythonscript','-script='+prepared['nativeScript'],
        '-AllowCommandletRendering','-metal','-NoTextureStreaming','-unattended','-nop4','-nosplash']
    receipt={'command':argv,'startedAtUtc':now(),'preparedSha256':sha(out/'prepared.json'),'operatorAuthorizedAfterR9SixViews':True}
    with(out/'native.log').open('xb')as log:
        child=subprocess.Popen(argv,cwd=ROOT,env={**os.environ,ENV:str(out),'BREZI_CONTEXT_TEXTURE_ENCODING_NATIVE':'1'},stdout=log,stderr=subprocess.STDOUT)
        receipt.update(pid=child.pid,returncode=child.wait())
    receipt.update(endedAtUtc=now(),logSha256=sha(out/'native.log'));write(out/'native-process.json',receipt)
    pins(prepared['protectedR8AndProviderPins']);pins(prepared['inputPins']);require(receipt['returncode']==0,'Native attempt failed; preserve output')


if __name__=='__main__':
    if os.environ.get('BREZI_CONTEXT_TEXTURE_ENCODING_NATIVE')=='1':native()
    elif len(sys.argv)==3 and sys.argv[1]=='--prepare':prepare(sys.argv[2])
    elif len(sys.argv)==4 and sys.argv[1]=='--run'and sys.argv[3]=='--authorized-after-r9':run(sys.argv[2],True)
    else:raise SystemExit('Use --prepare FRESH_OUTPUT; native --run requires separate authorization after R9 six views.')
