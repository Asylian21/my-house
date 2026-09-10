#include "BreziSolarVisibilityProbe.h"
#include "BreziSolarVisibilityContract.h"
#include "BreziCausticsTransport.h"
#include "ShaderCompilerCore.h"
// Source-only isolated probe. No material, geometry, light or production source mutations.
#include "Modules/ModuleManager.h"
#include "BreziCausticsContract.h"
#include "BreziFloorCausticsDiagnostic.h"
#include "BreziCausticsWaterBinding.h"
#include "BreziSceneRevision.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "CoreGlobals.h"
#include "HAL/PlatformProperties.h"
#include "Misc/Parse.h"
#include "Misc/SecureHash.h"
#include "CommonRenderResources.h"
#include "RHIStaticStates.h"
#include <atomic>
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/ScopeLock.h"
#include "Misc/CoreDelegates.h"
#include "RenderingThread.h"
#include "HAL/FileManager.h"
#include "Async/Async.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "SceneInterface.h"
#include "SceneViewExtension.h"
#include "GlobalShader.h"
#include "ShaderCore.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RenderUtils.h"
#include "PipelineStateCache.h"
#include "RHIGPUReadback.h"
#include "ProfilingDebugging/RealtimeGPUProfiler.h"

DEFINE_LOG_CATEGORY_STATIC(LogBreziCausticsProbe, Log, All);
DECLARE_GPU_STAT_NAMED(BreziCausticsProbe, TEXT("BreziCausticsProbe"));
static TAutoConsoleVariable<int32> CVarEnabled(TEXT("brezi.CausticsProbe.Enable"), 0, TEXT("Generate isolated HDR floor atlas; no scene lighting binding."), ECVF_RenderThreadSafe);
static TAutoConsoleVariable<int32> CVarCapture(TEXT("brezi.CausticsProbe.Capture"), 0, TEXT("Increment to asynchronously read back photons and linear RGBA16F atlas once."), ECVF_RenderThreadSafe);
static constexpr uint32 LaunchX=512, LaunchY=230, AtlasX=512, AtlasY=256;
static constexpr uint32 PhotonStride=48, SampleCount=LaunchX*LaunchY;

struct FTriangleGPU { FVector4f A, B, C; };
struct FNodeGPU { FVector4f Low, High, Meta; };
struct FTransportSentinelGPU { FVector4f OriginMin, DirectionMax, Expected; };
static_assert(sizeof(FTriangleGPU)==48 && sizeof(FNodeGPU)==48);
struct FProbeContract
{
    TArray<FTriangleGPU> Triangles;
    TArray<FNodeGPU> Nodes;
    TArray<uint32> LeafIndices;
    FVector4f WaveSpatialTime[12], WaveSlopePhase[12];
    FVector4f Aperture;
    FVector3f Extinction;
    float WaterZ=0, FloorZ=0;
    uint32 FloorObjectIndex=0;
    FString JsonText, WaterBindingText;
    TArray<FString> ObjectIds;
};

static void Require(bool Condition, const TCHAR* Message)
{
    if (!Condition) UE_LOG(LogBreziCausticsProbe, Fatal, TEXT("%s"), Message);
}
static FVector3f Vector3(const TArray<TSharedPtr<FJsonValue>>& A)
{
    Require(A.Num()==3,TEXT("Expected source vector3"));
    FVector3f V(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());
    Require(FMath::IsFinite(V.X)&&FMath::IsFinite(V.Y)&&FMath::IsFinite(V.Z),TEXT("Nonfinite source geometry"));return V;
}
static TSharedRef<FProbeContract,ESPMode::ThreadSafe> LoadContract(const FString& Path, bool bVerifiedCookedBinding = false)
{
    auto Result=MakeShared<FProbeContract,ESPMode::ThreadSafe>();
    TArray<uint8> Bytes;
    Require(FFileHelper::LoadFileToArray(Bytes,*Path),TEXT("Cannot read frozen receiver contract"));
    uint8 ByteHash[FSHA1::DigestSize]; FSHA1::HashBuffer(Bytes.GetData(),Bytes.Num(),ByteHash);
    Require(BytesToHex(ByteHash,FSHA1::DigestSize).Equals(BreziCausticsContractSha1,ESearchCase::IgnoreCase),TEXT("Receiver bytes differ from compiled source binding"));
    FFileHelper::BufferToString(Result->JsonText,Bytes.GetData(),Bytes.Num());
    TSharedPtr<FJsonObject> Json;
    Require(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Result->JsonText),Json)&&Json.IsValid(),TEXT("Malformed receiver contract"));
    FString WalkingText; TSharedPtr<FJsonObject> Walking;
    Require(FFileHelper::LoadFileToString(WalkingText,*FPaths::Combine(FPaths::ProjectContentDir(),TEXT("Data/walking.json")))
        && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(WalkingText),Walking) && Walking.IsValid(),TEXT("Missing canonical runtime provenance"));
    const auto Sources=Json->GetObjectField(TEXT("sourceSha256"));
    const auto Provenance=Walking->GetObjectField(TEXT("provenance"));
    Require(Provenance->GetStringField(TEXT("sceneSha256"))==BreziSceneRevision::CurrentSceneSha256
        && Provenance->GetStringField(TEXT("sourceObjSha256"))==BreziSceneRevision::CurrentObjSha256,
        TEXT("Runtime map provenance differs from current scene revision"));
    Require(Sources->GetStringField(TEXT("output/unreal/geometry/scene.json"))==BreziSceneRevision::ReceiverOriginSceneSha256
        && Sources->GetStringField(TEXT("output/unreal/geometry/dom-mm.obj"))==BreziSceneRevision::ReceiverOriginObjSha256,
        TEXT("Frozen receiver origin differs from reviewed scene revision"));
    Require(Json->GetStringField(TEXT("coordinateSystem"))==TEXT("unreal-axes-metres"),TEXT("Wrong receiver units/axes"));
    Require(FMath::Abs(Json->GetNumberField(TEXT("iorAirToWater"))-1.333)<1e-9,TEXT("IOR contract changed"));
    const auto& Objects=Json->GetArrayField(TEXT("receiverObjects"));
    for (const auto& Object:Objects) Result->ObjectIds.Add(Object->AsObject()->GetStringField(TEXT("id")));
    const int32 FloorIndex=Result->ObjectIds.Find(TEXT("DOM_01720"));
    Require(FloorIndex!=INDEX_NONE,TEXT("Canonical floor source missing"));Result->FloorObjectIndex=FloorIndex;
    const auto Floor=Objects[FloorIndex]->AsObject();
    Require(Floor->GetArrayField(TEXT("materialNames"))[0]->AsString()==TEXT("real-pool-tile"),TEXT("Unexpected floor material identity"));
    const auto Bounds=Floor->GetObjectField(TEXT("boundsMm"));
    FVector3f Low=Vector3(Bounds->GetArrayField(TEXT("min"))),High=Vector3(Bounds->GetArrayField(TEXT("max")));
    Result->Aperture=FVector4f(Low.X/1000,-High.Y/1000,(High.X-Low.X)/1000,(High.Y-Low.Y)/1000);
    Result->FloorZ=High.Z/1000; Result->WaterZ=Json->GetNumberField(TEXT("waterMeanPlaneMetres"));
    Require(FMath::Abs(Result->WaterZ+.012f)<.0005f&&FMath::Abs(Result->WaterZ-Result->FloorZ-1.4f)<.0005f,TEXT("Canonical pool elevations changed"));
    Require(FMath::Abs(Result->Aperture.Z-6)<.0005f&&FMath::Abs(Result->Aperture.W-2.7f)<.0005f,TEXT("Canonical aperture changed"));
    // Geometry remains the frozen reviewed receiver; optical state comes from the current saved graph.
    TArray<uint8> WaterBytes;
    Require(FFileHelper::LoadFileToArray(WaterBytes,*FPaths::Combine(FPaths::GetPath(Path),TEXT("active-water-binding.json"))),TEXT("Missing current water binding"));
    FSHA1::HashBuffer(WaterBytes.GetData(),WaterBytes.Num(),ByteHash);
    Require(BytesToHex(ByteHash,FSHA1::DigestSize).Equals(BreziCausticsWaterBindingSha1,ESearchCase::IgnoreCase),TEXT("Water binding differs from compiled bytes"));
    FFileHelper::BufferToString(Result->WaterBindingText,WaterBytes.GetData(),WaterBytes.Num());
    TSharedPtr<FJsonObject> Water;
    Require(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Result->WaterBindingText),Water)&&Water.IsValid(),TEXT("Malformed water binding"));
    Require(Water->GetStringField(TEXT("receiverContractSha256"))==BreziCausticsContractSha256,TEXT("Water binding names another receiver"));
    Require(Water->GetStringField(TEXT("coordinateSystem"))==TEXT("unreal-axes-centimetres-for-normal")&&Water->GetNumberField(TEXT("waveCount"))==12,TEXT("Unsupported saved water normal contract"));
    if(!bVerifiedCookedBinding)
    {
    TArray<uint8> MaterialBytes;
    Require(FFileHelper::LoadFileToArray(MaterialBytes,*FPaths::Combine(FPaths::ProjectDir(),BreziCausticsWaterMaterialRelativePath)),TEXT("Cannot verify saved water material for diagnostic"));
    FSHA1::HashBuffer(MaterialBytes.GetData(),MaterialBytes.Num(),ByteHash);
    Require(BytesToHex(ByteHash,FSHA1::DigestSize).Equals(BreziCausticsWaterMaterialSha1,ESearchCase::IgnoreCase),TEXT("Saved water asset differs from normal readback"));
    }
    else Require(FPlatformProperties::RequiresCookedData(),TEXT("Cooked binding cannot bypass Editor material bytes"));
    const auto& Rows=Water->GetArrayField(TEXT("savedNormalRows"));Require(Rows.Num()==12,TEXT("Expected twelve saved normal rows"));
    for (int32 I=0;I<12;++I)
    {
        const auto Row=Rows[I]->AsObject();
        Require(Row->GetNumberField(TEXT("index"))==I&&Row->GetNumberField(TEXT("cosinePeriod"))==1,TEXT("Wave order or cosine period differs"));
        Result->WaveSpatialTime[I]=FVector4f(Vector3(Row->GetArrayField(TEXT("positionCyclesPerCm"))),float(Row->GetNumberField(TEXT("timeCyclesPerSecond"))));
        Result->WaveSlopePhase[I]=FVector4f(Vector3(Row->GetArrayField(TEXT("slopeVector"))),float(Row->GetNumberField(TEXT("phaseCycles"))));
    }
    Require(FMath::Abs(Water->GetNumberField(TEXT("iorAirToWater"))-1.333)<1e-9,TEXT("Current water IOR differs"));
    Result->Extinction=Vector3(Water->GetArrayField(TEXT("absorptionPerMetre")))+Vector3(Water->GetArrayField(TEXT("scatteringPerMetre")));
    for (const auto& Entry:Json->GetArrayField(TEXT("triangles")))
    {
        auto T=Entry->AsObject();const auto& P=T->GetArrayField(TEXT("verticesMetres"));Require(P.Num()==3,TEXT("Only source triangles accepted"));
        const int32 ObjectIndex=Result->ObjectIds.Find(T->GetStringField(TEXT("objectId")));Require(ObjectIndex!=INDEX_NONE,TEXT("Unowned receiver triangle"));
        FVector3f A=Vector3(P[0]->AsArray()),B=Vector3(P[1]->AsArray()),C=Vector3(P[2]->AsArray());
        Result->Triangles.Add({FVector4f(A,float(ObjectIndex)),FVector4f(B,float(T->GetNumberField(TEXT("sourceFaceIndex")))),FVector4f(C,0)});
    }
    for (const auto& Entry:Json->GetArrayField(TEXT("bvhNodes")))
    {
        auto N=Entry->AsObject();FNodeGPU G;G.Low=FVector4f(Vector3(N->GetArrayField(TEXT("low"))),0);G.High=FVector4f(Vector3(N->GetArrayField(TEXT("high"))),0);
        const TArray<TSharedPtr<FJsonValue>>* Children=nullptr;
        if (N->TryGetArrayField(TEXT("children"),Children))
        {Require(Children->Num()==2,TEXT("Nonbinary BVH"));G.Meta=FVector4f((*Children)[0]->AsNumber(),(*Children)[1]->AsNumber(),0,0);}
        else
        {
            const auto& Indices=N->GetArrayField(TEXT("triangles"));Require(Indices.Num()>0&&Indices.Num()<=8,TEXT("Invalid BVH leaf"));
            G.Meta=FVector4f(-1,-1,Result->LeafIndices.Num(),Indices.Num());
            for(const auto& Id:Indices){uint32 V=uint32(Id->AsNumber());Require(V<uint32(Result->Triangles.Num()),TEXT("BVH triangle out of range"));Result->LeafIndices.Add(V);}
        }
        Result->Nodes.Add(G);
    }
    Require(Result->Triangles.Num()==1076&&Result->Nodes.Num()==359&&Result->ObjectIds.Num()==45,TEXT("Review changed frozen receiver topology before use"));
    for(int32 I=0;I<Result->Nodes.Num();++I)
    {
        const auto& N=Result->Nodes[I];
        if(N.Meta.W==0) Require(N.Meta.X>I&&N.Meta.Y>I&&N.Meta.X<Result->Nodes.Num()&&N.Meta.Y<Result->Nodes.Num(),TEXT("Invalid or cyclic BVH children"));
    }
    return Result;
}

class FProbeTraceCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FProbeTraceCS);SHADER_USE_PARAMETER_STRUCT(FProbeTraceCS,FGlobalShader);
    class FTransportDim : SHADER_PERMUTATION_BOOL("BREZI_TRANSPORT_OPAQUE");
    using FPermutationDomain = TShaderPermutationDomain<FTransportDim>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER_STRUCT_REF(FViewUniformShaderParameters,View)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<IncomingResult>,IncomingVisibility)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,TransportGates)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,RWTransportGPUUniform)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<TriangleData>,Triangles)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<NodeData>,Nodes)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,LeafIndices)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<PhotonData>,RWPhotons)
        SHADER_PARAMETER_ARRAY(FVector4f,WaveSpatialTime,[12])
        SHADER_PARAMETER_ARRAY(FVector4f,WaveSlopePhase,[12])
        SHADER_PARAMETER(FVector3f,SunDirection)
        SHADER_PARAMETER(FVector3f,Extinction)
        SHADER_PARAMETER(FVector4f,Aperture)
        SHADER_PARAMETER(float,WaterZ)
        SHADER_PARAMETER(float,FloorZ)
        SHADER_PARAMETER(uint32,FloorObjectIndex)
        SHADER_PARAMETER(FUintVector2,LaunchSize)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P){return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6);}
};
IMPLEMENT_GLOBAL_SHADER(FProbeTraceCS,"/Plugin/BreziCausticsProbe/Private/BreziCaustics.usf","TraceCS",SF_Compute);
BEGIN_SHADER_PARAMETER_STRUCT(FSplatParameters,)
    SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<PhotonData>,Photons)
    SHADER_PARAMETER(FVector4f,Aperture)
    SHADER_PARAMETER(FUintVector2,AtlasSize)
    RENDER_TARGET_BINDING_SLOTS()
END_SHADER_PARAMETER_STRUCT()
class FProbeSplatVS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FProbeSplatVS);SHADER_USE_PARAMETER_STRUCT(FProbeSplatVS,FGlobalShader);
    using FParameters=FSplatParameters;
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P){return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6);}
};
class FProbeSplatPS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FProbeSplatPS);SHADER_USE_PARAMETER_STRUCT(FProbeSplatPS,FGlobalShader);
    using FParameters=FSplatParameters;
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P){return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6);}
};
IMPLEMENT_GLOBAL_SHADER(FProbeSplatVS,"/Plugin/BreziCausticsProbe/Private/BreziCaustics.usf","SplatVS",SF_Vertex);
IMPLEMENT_GLOBAL_SHADER(FProbeSplatPS,"/Plugin/BreziCausticsProbe/Private/BreziCaustics.usf","SplatPS",SF_Pixel);

static FBreziCausticsProducedGraph BuildSharedCaustics(FRDGBuilder& GraphBuilder, const FSceneView& View,
    TSharedRef<FProbeContract,ESPMode::ThreadSafe> Contract, FVector3f Sun,
    TRefCountPtr<FRDGPooledBuffer>& TrianglesPooled, TRefCountPtr<FRDGPooledBuffer>& NodesPooled,
    TRefCountPtr<FRDGPooledBuffer>& IndicesPooled, FRDGBufferRef Visibility = nullptr,
    FRDGBufferRef Gates = nullptr, FRDGBufferRef GPUUniform = nullptr)
{
        FRDGBufferRef Triangles,Nodes,Indices;
        if(!TrianglesPooled)
        {
            Triangles=CreateStructuredBuffer(GraphBuilder,TEXT("Brezi.Caustics.Triangles"),sizeof(FTriangleGPU),Contract->Triangles.Num(),Contract->Triangles.GetData(),Contract->Triangles.Num()*sizeof(FTriangleGPU));
            Nodes=CreateStructuredBuffer(GraphBuilder,TEXT("Brezi.Caustics.Nodes"),sizeof(FNodeGPU),Contract->Nodes.Num(),Contract->Nodes.GetData(),Contract->Nodes.Num()*sizeof(FNodeGPU));
            Indices=CreateStructuredBuffer(GraphBuilder,TEXT("Brezi.Caustics.LeafIndices"),sizeof(uint32),Contract->LeafIndices.Num(),Contract->LeafIndices.GetData(),Contract->LeafIndices.Num()*sizeof(uint32));
            GraphBuilder.QueueBufferExtraction(Triangles,&TrianglesPooled);GraphBuilder.QueueBufferExtraction(Nodes,&NodesPooled);GraphBuilder.QueueBufferExtraction(Indices,&IndicesPooled);
        }
        else{Triangles=GraphBuilder.RegisterExternalBuffer(TrianglesPooled);Nodes=GraphBuilder.RegisterExternalBuffer(NodesPooled);Indices=GraphBuilder.RegisterExternalBuffer(IndicesPooled);}
        FRDGBufferRef Photons=GraphBuilder.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(PhotonStride,SampleCount),TEXT("Brezi.Caustics.Photons"));
        auto* Trace=GraphBuilder.AllocParameters<FProbeTraceCS::FParameters>();Trace->View=GetShaderBinding(View.ViewUniformBuffer);
        Require(Trace->View.IsShader() && Trace->View.GetUniformBuffer()==View.ViewUniformBuffer.GetReference(),TEXT("Trace shader View is not paired"));
        Trace->Triangles=GraphBuilder.CreateSRV(Triangles);Trace->Nodes=GraphBuilder.CreateSRV(Nodes);Trace->LeafIndices=GraphBuilder.CreateSRV(Indices);Trace->RWPhotons=GraphBuilder.CreateUAV(Photons);
        for(int32 I=0;I<12;++I){Trace->WaveSpatialTime[I]=Contract->WaveSpatialTime[I];Trace->WaveSlopePhase[I]=Contract->WaveSlopePhase[I];}Trace->SunDirection=Sun;Trace->Extinction=Contract->Extinction;Trace->Aperture=Contract->Aperture;Trace->WaterZ=Contract->WaterZ;Trace->FloorZ=Contract->FloorZ;Trace->FloorObjectIndex=Contract->FloorObjectIndex;Trace->LaunchSize=FUintVector2(LaunchX,LaunchY);
        FProbeTraceCS::FPermutationDomain Permutation; Permutation.Set<FProbeTraceCS::FTransportDim>(Visibility != nullptr);
        Trace->IncomingVisibility = Visibility ? GraphBuilder.CreateSRV(Visibility) : nullptr;
        Trace->TransportGates = Gates ? GraphBuilder.CreateSRV(Gates) : nullptr;
        Trace->RWTransportGPUUniform = GPUUniform ? GraphBuilder.CreateUAV(GPUUniform) : nullptr;
        TShaderMapRef<FProbeTraceCS> CS(GetGlobalShaderMap(View.GetFeatureLevel()), Permutation);FComputeShaderUtils::AddPass(GraphBuilder,RDG_EVENT_NAME("Brezi.Caustics.Trace"),CS,Trace,FIntVector((LaunchX+7)/8,(LaunchY+7)/8,1));
        FRDGTextureRef Atlas=GraphBuilder.CreateTexture(FRDGTextureDesc::Create2D(FIntPoint(AtlasX,AtlasY),PF_FloatRGBA,FClearValueBinding::Transparent,ETextureCreateFlags::RenderTargetable|ETextureCreateFlags::ShaderResource),TEXT("Brezi.Caustics.FloorIrradiance"));
        auto* Splat=GraphBuilder.AllocParameters<FSplatParameters>();Splat->Photons=GraphBuilder.CreateSRV(Photons);Splat->Aperture=Contract->Aperture;Splat->AtlasSize=FUintVector2(AtlasX,AtlasY);Splat->RenderTargets[0]=FRenderTargetBinding(Atlas,ERenderTargetLoadAction::EClear);
        TShaderMapRef<FProbeSplatVS> VS(GetGlobalShaderMap(View.GetFeatureLevel()));TShaderMapRef<FProbeSplatPS> PS(GetGlobalShaderMap(View.GetFeatureLevel()));
        GraphBuilder.AddPass(RDG_EVENT_NAME("Brezi.Caustics.Splat"),Splat,ERDGPassFlags::Raster,[Splat,VS,PS](FRHICommandList& RHICmdList)
        {
            FGraphicsPipelineStateInitializer State;RHICmdList.ApplyCachedRenderTargets(State);State.BlendState=TStaticBlendState<CW_RGBA,BO_Add,BF_One,BF_One,BO_Add,BF_One,BF_One>::GetRHI();State.RasterizerState=TStaticRasterizerState<FM_Solid,CM_None>::GetRHI();State.DepthStencilState=TStaticDepthStencilState<false,CF_Always>::GetRHI();State.PrimitiveType=PT_TriangleList;
            State.BoundShaderState.VertexDeclarationRHI=GEmptyVertexDeclaration.VertexDeclarationRHI;State.BoundShaderState.VertexShaderRHI=VS.GetVertexShader();State.BoundShaderState.PixelShaderRHI=PS.GetPixelShader();SetGraphicsPipelineState(RHICmdList,State,0);
            SetShaderParameters(RHICmdList,VS,VS.GetVertexShader(),*Splat);SetShaderParameters(RHICmdList,PS,PS.GetPixelShader(),*Splat);RHICmdList.SetViewport(0,0,0,AtlasX,AtlasY,1);RHICmdList.DrawPrimitive(0,SampleCount*2,1);
        });
    return {Atlas, Photons, Visibility, Gates, GPUUniform};
}

#if RHI_RAYTRACING
class FTransportIncomingCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FTransportIncomingCS); SHADER_USE_PARAMETER_STRUCT(FTransportIncomingCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER_STRUCT_REF(FViewUniformShaderParameters,View)
        SHADER_PARAMETER_RDG_BUFFER_SRV(RaytracingAccelerationStructure,IncomingTLAS)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<SentinelData>,IncomingSentinels)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<IncomingResult>,RWIncomingVisibility)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,RWIncomingGates)
        SHADER_PARAMETER(FVector3f,IncomingSunTravel)
        SHADER_PARAMETER(FVector3f,IncomingPreViewTranslationCm)
        SHADER_PARAMETER(FVector4f,IncomingAperture)
        SHADER_PARAMETER(float,IncomingWaterZMetres)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6) && IsRayTracingEnabledForProject(P.Platform)
        && RHISupportsRayTracing(P.Platform) && RHISupportsInlineRayTracing(P.Platform); }
    static void ModifyCompilationEnvironment(const FGlobalShaderPermutationParameters& P,FShaderCompilerEnvironment& E)
    { FGlobalShader::ModifyCompilationEnvironment(P,E); E.CompilerFlags.Add(CFLAG_InlineRayTracing); E.CompilerFlags.Add(CFLAG_Wave32); }
};
IMPLEMENT_GLOBAL_SHADER(FTransportIncomingCS,"/Plugin/BreziCausticsProbe/Private/BreziCausticsIncoming.usf","IncomingCS",SF_Compute);
#endif

class FBreziCausticsTransport final : public IBreziCausticsTransport
{
    TSharedRef<FProbeContract,ESPMode::ThreadSafe> Contract;
    TRefCountPtr<FRDGPooledBuffer> TrianglesPooled,NodesPooled,IndicesPooled;
    TArray<FTransportSentinelGPU> Sentinels;
    FVector3f SentinelSun;
    FString SolarText;
public:
    explicit FBreziCausticsTransport(const FString& Path, bool bVerifiedCookedBinding) : Contract(LoadContract(Path,bVerifiedCookedBinding))
    {
        TArray<uint8> Bytes; Require(FFileHelper::LoadFileToArray(Bytes,*FPaths::Combine(FPaths::GetPath(Path),TEXT("solar-visibility-cases.json"))),TEXT("Missing opaque source sentinel fixture"));
        uint8 Hash[FSHA1::DigestSize]; FSHA1::HashBuffer(Bytes.GetData(),Bytes.Num(),Hash);
        Require(BytesToHex(Hash,FSHA1::DigestSize).Equals(BreziSolarCasesSha1,ESearchCase::IgnoreCase),TEXT("Opaque sentinel bytes changed"));
        FFileHelper::BufferToString(SolarText,Bytes.GetData(),Bytes.Num()); TSharedPtr<FJsonObject> Json;
        Require(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(SolarText),Json)&&Json.IsValid(),TEXT("Invalid opaque sentinels"));
        SentinelSun=Vector3(Json->GetArrayField(TEXT("solarTravelDirection")));
        for(const auto& Entry:Json->GetArrayField(TEXT("cases")))
        {
            const auto C=Entry->AsObject(); const bool Blocked=C->GetStringField(TEXT("expected"))==TEXT("blocked");
            Sentinels.Add({FVector4f(Vector3(C->GetArrayField(TEXT("originCm"))),C->GetNumberField(TEXT("tMinCm"))),
                FVector4f(Vector3(C->GetArrayField(TEXT("directionTowardSun"))),C->GetNumberField(TEXT("tMaxCm"))),
                FVector4f(Blocked?1:0,Blocked?C->GetNumberField(TEXT("expectedHitDistanceCm")):-1,.05f,0)});
        }
        Require(Sentinels.Num()==6,TEXT("Expected six frozen visibility controls"));
    }
    FString ReceiverJson() const override { return Contract->JsonText; }
    FString WaterJson() const override { return Contract->WaterBindingText; }
    FString SolarJson() const override { return SolarText; }
    bool AcceptsSun(FVector3f Sun) const override { return Sun.Equals(SentinelSun,1e-5f); }
    FBreziCausticsProducedGraph Build(FRDGBuilder& GraphBuilder,const FSceneView& View,FVector3f Sun,FRDGBufferSRVRef TLAS) override
    {
#if RHI_RAYTRACING
        if(!TLAS || !View.ViewUniformBuffer.IsValid() || !AcceptsSun(Sun)) return {};
        FRDGBufferRef Visibility=GraphBuilder.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(48,BreziTransportVisibilityCount),TEXT("Brezi.Transport.IncomingVisibility"));
        FRDGBufferRef Gates=GraphBuilder.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(4,1),TEXT("Brezi.Transport.Gates"));
        FRDGBufferRef Uniform=GraphBuilder.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(16,1),TEXT("Brezi.Transport.GPUUniform"));
        AddClearUAVPass(GraphBuilder,GraphBuilder.CreateUAV(Gates),0u);
        auto* P=GraphBuilder.AllocParameters<FTransportIncomingCS::FParameters>(); P->View=GetShaderBinding(View.ViewUniformBuffer);
        Require(P->View.IsShader()&&P->View.GetUniformBuffer()==View.ViewUniformBuffer.GetReference(),TEXT("Incoming shader View not paired"));
        P->IncomingTLAS=TLAS; P->IncomingSunTravel=Sun; P->IncomingAperture=Contract->Aperture;
        P->IncomingWaterZMetres=Contract->WaterZ; P->IncomingPreViewTranslationCm=FVector3f(View.ViewMatrices.GetPreViewTranslation());
        auto SentinelBuffer=CreateStructuredBuffer(GraphBuilder,TEXT("Brezi.Transport.Sentinels"),sizeof(FTransportSentinelGPU),Sentinels.Num(),Sentinels.GetData(),Sentinels.Num()*sizeof(FTransportSentinelGPU));
        P->IncomingSentinels=GraphBuilder.CreateSRV(SentinelBuffer);P->RWIncomingVisibility=GraphBuilder.CreateUAV(Visibility);P->RWIncomingGates=GraphBuilder.CreateUAV(Gates);
        TShaderMapRef<FTransportIncomingCS> Shader(GetGlobalShaderMap(View.GetFeatureLevel()));
        FComputeShaderUtils::AddPass(GraphBuilder,RDG_EVENT_NAME("Brezi.Transport.IncomingOpaque117760Plus6"),Shader,P,FIntVector((BreziTransportVisibilityCount+31)/32,1,1));
        return BuildSharedCaustics(GraphBuilder,View,Contract,Sun,TrianglesPooled,NodesPooled,IndicesPooled,Visibility,Gates,Uniform);
#else
        return {};
#endif
    }
};
TUniquePtr<IBreziCausticsTransport> CreateBreziCausticsTransport(const FString& Path, bool bVerifiedCookedBinding)
{ return MakeUnique<FBreziCausticsTransport>(Path,bVerifiedCookedBinding); }

class FProbeExtension : public FSceneViewExtensionBase
{
    std::atomic<bool> bStopped{false};
    TSharedRef<FProbeContract,ESPMode::ThreadSafe> Contract;
    FCriticalSection SunMutex;
    FVector3f SubmittedSun=FVector3f::ZeroVector;
    float SubmittedLux=0;bool bSunValid=false;
    TRefCountPtr<FRDGPooledBuffer> TrianglesPooled,NodesPooled,IndicesPooled;
    TRefCountPtr<IPooledRenderTarget> LatestAtlas;
    TUniquePtr<FRHIGPUBufferReadback> PhotonReadback;
    TUniquePtr<FRHIGPUTextureReadback> AtlasReadback;
    int32 LastRequest=0;bool bPending=false;
    TFuture<void> CaptureWrite;
    FVector3f CaptureSun;float CaptureLux=0;uint32 CaptureFrame=0;FIntPoint CaptureViewPixels=FIntPoint::ZeroValue;
    void ResolveCapture()
    {
        if(!bPending||!PhotonReadback->IsReady()||!AtlasReadback->IsReady())return;
        TArray<uint8> Photons;Photons.SetNumUninitialized(SampleCount*PhotonStride);
        void* P=PhotonReadback->Lock(Photons.Num());Require(P!=nullptr,TEXT("Photon GPU readback unavailable"));FMemory::Memcpy(Photons.GetData(),P,Photons.Num());PhotonReadback->Unlock();
        int32 RowPitch=0,Height=0;void* A=AtlasReadback->Lock(RowPitch,&Height);Require(A&&RowPitch>=int32(AtlasX)&&Height>=int32(AtlasY),TEXT("Unexpected RGBA16F readback layout"));
        TArray<uint8> Atlas;Atlas.SetNumUninitialized(AtlasX*AtlasY*8);
        for(uint32 Y=0;Y<AtlasY;++Y)FMemory::Memcpy(Atlas.GetData()+Y*AtlasX*8,static_cast<uint8*>(A)+Y*RowPitch*8,AtlasX*8);
        AtlasReadback->Unlock();bPending=false;
        FString Directory=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("CausticsProbe"),FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphens));
        const FString SourceJson=Contract->JsonText;const FString WaterJson=Contract->WaterBindingText;const FVector3f Sun=CaptureSun;const float Lux=CaptureLux;const int32 Request=LastRequest;const uint32 Frame=CaptureFrame;const FIntPoint ViewPixels=CaptureViewPixels;
        CaptureWrite=Async(EAsyncExecution::ThreadPool,[Directory,SourceJson,WaterJson,Sun,Lux,Request,Frame,ViewPixels,Photons=MoveTemp(Photons),Atlas=MoveTemp(Atlas)]() mutable
        {
            IFileManager::Get().MakeDirectory(*Directory,true);
            Require(FFileHelper::SaveArrayToFile(Photons,*FPaths::Combine(Directory,TEXT("photons-f32le.bin")))&&FFileHelper::SaveArrayToFile(Atlas,*FPaths::Combine(Directory,TEXT("atlas-rgba16f-le.bin"))),TEXT("Cannot save probe readback"));
            Require(FFileHelper::SaveStringToFile(SourceJson,*FPaths::Combine(Directory,TEXT("receiver-contract.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM),TEXT("Cannot save capture contract"));
            Require(FFileHelper::SaveStringToFile(WaterJson,*FPaths::Combine(Directory,TEXT("active-water-binding.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM),TEXT("Cannot save capture water binding"));
            float ShaderTime=0;FMemory::Memcpy(&ShaderTime,Photons.GetData()+44,4);
            auto Meta=MakeShared<FJsonObject>();Meta->SetStringField(TEXT("status"),TEXT("GPU-readback-awaiting-reference-validation"));Meta->SetNumberField(TEXT("shaderTimeSeconds"),ShaderTime);Meta->SetNumberField(TEXT("request"),Request);
            Meta->SetArrayField(TEXT("launchSize"),{MakeShared<FJsonValueNumber>(LaunchX),MakeShared<FJsonValueNumber>(LaunchY)});Meta->SetArrayField(TEXT("atlasSize"),{MakeShared<FJsonValueNumber>(AtlasX),MakeShared<FJsonValueNumber>(AtlasY)});
            Meta->SetArrayField(TEXT("sunRayDirection"),{MakeShared<FJsonValueNumber>(Sun.X),MakeShared<FJsonValueNumber>(Sun.Y),MakeShared<FJsonValueNumber>(Sun.Z)});Meta->SetNumberField(TEXT("nativeDirectionalLux"),Lux);
            Meta->SetStringField(TEXT("sourceContractSha256"),BreziCausticsContractSha256);
            Meta->SetNumberField(TEXT("viewFamilyFrameNumber"),Frame);Meta->SetArrayField(TEXT("unscaledViewPixels"),{MakeShared<FJsonValueNumber>(ViewPixels.X),MakeShared<FJsonValueNumber>(ViewPixels.Y)});
            Meta->SetStringField(TEXT("waterBindingSha256"),BreziCausticsWaterBindingSha256);Meta->SetNumberField(TEXT("waveCount"),12);
            Meta->SetNumberField(TEXT("photonStrideBytes"),PhotonStride);Meta->SetBoolField(TEXT("productionLightingBound"),false);Meta->SetBoolField(TEXT("sunVisibilityImplemented"),false);Meta->SetBoolField(TEXT("finiteSolarDiskImplemented"),false);
            FString Text;FJsonSerializer::Serialize(Meta,TJsonWriterFactory<>::Create(&Text));Require(FFileHelper::SaveStringToFile(Text,*FPaths::Combine(Directory,TEXT("capture.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM),TEXT("Cannot save capture metadata"));
            UE_LOG(LogBreziCausticsProbe,Display,TEXT("BREZI_CAUSTICS_CAPTURE %s"),*Directory);
        });
    }
public:
    FProbeExtension(const FAutoRegister& AutoRegister,TSharedRef<FProbeContract,ESPMode::ThreadSafe> InContract):FSceneViewExtensionBase(AutoRegister),Contract(InContract){}
    // Stop scheduling before draining the render thread; a missing readback remains pending evidence.
    void Stop() { bStopped.store(true); }
    ~FProbeExtension() override
    {
        if(CaptureWrite.IsValid()) CaptureWrite.Wait();
        if(bPending) UE_LOG(LogBreziCausticsProbe,Warning,TEXT("BREZI_CAUSTICS_CAPTURE_INCOMPLETE request=%d; GPU readback did not finish before shutdown"),LastRequest);
    }
    void SetupViewFamily(FSceneViewFamily&) override {}
    void SetupView(FSceneViewFamily&,FSceneView&) override {}
    void BeginRenderViewFamily(FSceneViewFamily& Family) override
    {
        if(bStopped.load()||!CVarEnabled.GetValueOnGameThread())return;
        UWorld* World=Family.Scene?Family.Scene->GetWorld():nullptr;FVector3f Direction=FVector3f::ZeroVector;float Lux=0;int32 Count=0;
        if(World&&World->IsGameWorld())for(TActorIterator<ADirectionalLight> It(World);It;++It)if(It->ActorHasTag(TEXT("BreziSun")))
        {Direction=FVector3f(It->GetActorForwardVector());Lux=It->GetLightComponent()->Intensity;++Count;}
        FScopeLock Lock(&SunMutex);SubmittedSun=Direction;SubmittedLux=Lux;bSunValid=Count==1;
    }
    void PostRenderBasePassDeferred_RenderThread(FRDGBuilder& GraphBuilder,FSceneView& View,const FRenderTargetBindingSlots&,TRDGUniformBufferRef<FSceneTextureUniformParameters>) override
    {
        if(bStopped.load())return;
        ResolveCapture();
        if(!CVarEnabled.GetValueOnRenderThread()||View.bIsSceneCapture||View.bIsReflectionCapture||View.Family->Views.Num()!=1)return;
        if(View.GetFeatureLevel()<ERHIFeatureLevel::SM6)return;
        FVector3f Sun;float Lux;
        {FScopeLock Lock(&SunMutex);if(!bSunValid)return;Sun=SubmittedSun;Lux=SubmittedLux;}
        Require(View.ViewUniformBuffer.IsValid(),TEXT("View uniform buffer absent after base pass"));
        Require(RHIPixelFormatHasCapabilities(PF_FloatRGBA,EPixelFormatCapabilities::RenderTarget|EPixelFormatCapabilities::TextureBlendable|EPixelFormatCapabilities::TextureSample),TEXT("Metal RGBA16F additive render target unsupported"));
        RDG_EVENT_SCOPE_STAT(GraphBuilder,BreziCausticsProbe,"BreziCausticsProbe");
        auto Produced = BuildSharedCaustics(GraphBuilder, View, Contract, Sun, TrianglesPooled, NodesPooled, IndicesPooled);
        FRDGBufferRef Photons = Produced.Photons; FRDGTextureRef Atlas = Produced.Atlas;
        GraphBuilder.QueueTextureExtraction(Atlas,&LatestAtlas); // Keeps output alive; deliberately no production consumer.
        const int32 Request=CVarCapture.GetValueOnRenderThread();
        // Startup can render before ExecCmds applies the material-time override.
        if(View.Family->FrameNumber>=60&&Request>LastRequest&&!bPending&&(!CaptureWrite.IsValid()||CaptureWrite.IsReady()))
        {
            if(!PhotonReadback){PhotonReadback=MakeUnique<FRHIGPUBufferReadback>(TEXT("BreziCausticsPhotons"));AtlasReadback=MakeUnique<FRHIGPUTextureReadback>(TEXT("BreziCausticsAtlas"));}
            AddEnqueueCopyPass(GraphBuilder,PhotonReadback.Get(),Photons,SampleCount*PhotonStride);AddEnqueueCopyPass(GraphBuilder,AtlasReadback.Get(),Atlas);bPending=true;LastRequest=Request;CaptureSun=Sun;CaptureLux=Lux;CaptureFrame=View.Family->FrameNumber;CaptureViewPixels=View.UnscaledViewRect.Size();
        }
    }
};

class FBreziCausticsProbeModule : public IModuleInterface
{
    TSharedPtr<FProbeExtension,ESPMode::ThreadSafe> Extension;
    TUniquePtr<IBreziSolarVisibilityProbe> SolarVisibility;
    TUniquePtr<IBreziFloorCausticsDiagnostic> FloorDiagnostic;
    FDelegateHandle PostEngineInitHandle, EnginePreExitHandle;
    void StopExtension()
    {
        if(FloorDiagnostic) { FloorDiagnostic->Stop(); FloorDiagnostic.Reset(); }
        if(Extension) { Extension->Stop(); FlushRenderingCommands(); Extension.Reset(); }
        if(SolarVisibility) { SolarVisibility->Stop(); SolarVisibility.Reset(); }
    }
public:
    bool SupportsDynamicReloading() override { return false; }
    void StartupModule() override
    {
        auto Plugin=IPluginManager::Get().FindPlugin(TEXT("BreziCausticsProbe"));Require(Plugin.IsValid(),TEXT("Plugin source directory absent"));
        AddShaderSourceDirectoryMapping(TEXT("/Plugin/BreziCausticsProbe"),FPaths::Combine(Plugin->GetBaseDir(),TEXT("Shaders")));
        // Cook commandlets need shader registration, but must never start a runtime provider.
        if(IsRunningCommandlet())return;
        // Parse one closed diagnostic mode; do not infer activation from a renderer cvar.
        FString FloorMode, Token; int32 FloorSwitches=0; const TCHAR* Cursor=FCommandLine::Get();
        while(FParse::Token(Cursor,Token,false)) if(Token.StartsWith(TEXT("-BreziFloorCausticsDiagnostic"),ESearchCase::IgnoreCase))
        {
            ++FloorSwitches; Require(Token.RemoveFromStart(TEXT("-BreziFloorCausticsDiagnostic="),ESearchCase::IgnoreCase),TEXT("Expected explicit floor diagnostic mode"));
            FloorMode=Token;
        }
        // An explicit CLI diagnostic wins; project configuration is an intentional opt-in.
        if(FloorSwitches==0 && GConfig)
        {
            GConfig->GetString(TEXT("BreziFloorCaustics"),TEXT("Mode"),FloorMode,GGameIni);
            Require(FloorMode.IsEmpty() || FloorMode==TEXT("transport-continuous"),TEXT("Project floor provider mode must be absent or transport-continuous"));
        }
        const bool bFloor=FloorSwitches>0 || !FloorMode.IsEmpty();
        Require(FloorSwitches<=1 && (!bFloor || FloorMode==TEXT("inactive") || FloorMode==TEXT("zero") || FloorMode==TEXT("constant") || FloorMode==TEXT("transport-opaque") || FloorMode==TEXT("transport-continuous")),TEXT("Floor provider requires one explicit control or transport mode"));
        const bool bMotionQA=FParse::Param(FCommandLine::Get(),TEXT("BreziCausticsMotionQA"));
        Require(!bMotionQA || (FloorMode==TEXT("transport-continuous") && FParse::Param(FCommandLine::Get(),TEXT("BreziMotionQA"))),TEXT("Caustics motion evidence requires continuous mode and existing BreziMotionQA"));
        // Plugin discovery alone never enables any diagnostic.
        const bool bTransport=FParse::Param(FCommandLine::Get(),TEXT("BreziCausticsProbe"));
        const bool bSolar=FParse::Param(FCommandLine::Get(),TEXT("BreziSolarVisibilityProbe"));
        const bool bSolarCapture=FParse::Param(FCommandLine::Get(),TEXT("BreziSolarVisibilityCapture"));
        Require(!bSolarCapture||bSolar,TEXT("Solar capture requires its explicit independent probe opt-in"));
        Require(!bFloor || (!bTransport && !bSolar),TEXT("Floor provider modes cannot run duplicate standalone transport/solar producers"));
        if(!bTransport&&!bSolar&&!bFloor)
        {
            UE_LOG(LogBreziCausticsProbe,Display,TEXT("Brezi diagnostics inactive; explicit transport, solar-visibility or floor-control opt-in required"));
            return;
        }
        EnginePreExitHandle=FCoreDelegates::OnEnginePreExit.AddRaw(this,&FBreziCausticsProbeModule::StopExtension);
        if(bTransport)
        {
            CVarEnabled.AsVariable()->Set(1,ECVF_SetByCommandline);
            if(FParse::Param(FCommandLine::Get(),TEXT("BreziCausticsCapture"))) CVarCapture.AsVariable()->Set(1,ECVF_SetByCommandline);
        }
        const FString ContractPath=FPaths::Combine(Plugin->GetBaseDir(),TEXT("Resources/receiver-contract.json"));
        const FString SolarPath=FPaths::Combine(Plugin->GetBaseDir(),TEXT("Resources/solar-visibility-cases.json"));
        const FString FloorPath=FPaths::Combine(Plugin->GetBaseDir(),TEXT("Resources/floor-provider-diagnostic.json"));
        PostEngineInitHandle=FCoreDelegates::GetOnPostEngineInit().AddLambda([this,ContractPath,SolarPath,FloorPath,FloorMode,bFloor,bTransport,bSolar,bSolarCapture]()
        {
            if(bFloor)FloorDiagnostic=CreateBreziFloorCausticsDiagnostic(FloorPath,FloorMode);
            if(bTransport)Extension=FSceneViewExtensions::NewExtension<FProbeExtension>(LoadContract(ContractPath));
            if(bSolar)SolarVisibility=CreateBreziSolarVisibilityProbe(SolarPath,bSolarCapture);
        });
    }
    void ShutdownModule() override
    {
        FCoreDelegates::GetOnPostEngineInit().Remove(PostEngineInitHandle);
        FCoreDelegates::OnEnginePreExit.Remove(EnginePreExitHandle);
        StopExtension();
    }
};
IMPLEMENT_MODULE(FBreziCausticsProbeModule,BreziCausticsProbe)
