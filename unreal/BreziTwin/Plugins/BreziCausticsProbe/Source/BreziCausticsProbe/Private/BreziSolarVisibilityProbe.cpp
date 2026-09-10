// Separate opaque geometry diagnostic. No caustics transport or lighting consumer.
#include "BreziSolarVisibilityProbe.h"
#include "BreziSolarVisibilityContract.h"
#include "SceneViewExtension.h"
#include "SceneInterface.h"
#include "FXRenderingUtils.h"
#include "GlobalShader.h"
#include "ShaderCompilerCore.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RenderUtils.h"
#include "RHIGlobals.h"
#include "RHIGPUReadback.h"
#include "DynamicRHI.h"
#include "RenderingThread.h"
#include "Engine/DirectionalLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/DirectionalLightComponent.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Misc/ScopeLock.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/IConsoleManager.h"
#include "Async/Async.h"
#include <atomic>

DEFINE_LOG_CATEGORY_STATIC(LogBreziSolarVisibility, Log, All);
static constexpr uint32 SolarOutputStride = 48;
static constexpr uint32 SolarWarmupFrames = 60;

static void SolarRequire(bool bValue, const TCHAR* Message)
{
    if (!bValue) UE_LOG(LogBreziSolarVisibility, Fatal, TEXT("%s"), Message);
}
static TArray<TSharedPtr<FJsonValue>> SolarVectorJson(const FVector& V)
{
    return {MakeShared<FJsonValueNumber>(V.X), MakeShared<FJsonValueNumber>(V.Y), MakeShared<FJsonValueNumber>(V.Z)};
}
static FVector SolarReadVector(const TSharedPtr<FJsonObject>& Json, const TCHAR* Key)
{
    const auto& Values=Json->GetArrayField(Key);
    SolarRequire(Values.Num()==3,TEXT("Solar fixture vector has wrong length"));
    FVector V(Values[0]->AsNumber(),Values[1]->AsNumber(),Values[2]->AsNumber());
    SolarRequire(!V.ContainsNaN(),TEXT("Nonfinite solar fixture vector"));
    return V;
}
static FString SolarJsonText(const TSharedRef<FJsonObject>& Json)
{
    FString Text;SolarRequire(FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text)),TEXT("Cannot serialize solar diagnostic"));return Text;
}
static void SolarSaveJson(const FString& Directory,const TSharedRef<FJsonObject>& Json)
{
    IFileManager::Get().MakeDirectory(*Directory,true);
    SolarRequire(FFileHelper::SaveStringToFile(SolarJsonText(Json),*FPaths::Combine(Directory,TEXT("capture.json")),
        FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM),TEXT("Cannot write solar capture state"));
}
struct FSolarRayGPU { FVector4f OriginAndMinCm, DirectionAndMaxCm; };
static_assert(sizeof(FSolarRayGPU)==32);
struct FSolarCases
{
    FString JsonText;
    FString SceneSha256, ObjSha256;
    FVector SunTravel;
    TArray<FSolarRayGPU> Rays;
};
static TSharedRef<FSolarCases,ESPMode::ThreadSafe> SolarLoadCases(const FString& Path)
{
    auto Cases=MakeShared<FSolarCases,ESPMode::ThreadSafe>();TArray<uint8> Bytes;
    SolarRequire(FFileHelper::LoadFileToArray(Bytes,*Path),TEXT("Cannot read frozen solar cases"));
    uint8 Hash[FSHA1::DigestSize];FSHA1::HashBuffer(Bytes.GetData(),Bytes.Num(),Hash);
    SolarRequire(BytesToHex(Hash,FSHA1::DigestSize).Equals(BreziSolarCasesSha1,ESearchCase::IgnoreCase),TEXT("Solar cases differ from compiled exact byte pin"));
    FFileHelper::BufferToString(Cases->JsonText,Bytes.GetData(),Bytes.Num());TSharedPtr<FJsonObject> Json;
    SolarRequire(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Cases->JsonText),Json)&&Json.IsValid(),TEXT("Invalid solar fixture JSON"));
    SolarRequire(Json->GetStringField(TEXT("coordinateSystem"))==TEXT("unreal-axes-centimetres"),TEXT("Solar fixture coordinates changed"));
    Cases->SceneSha256=Json->GetStringField(TEXT("sceneSha256"));Cases->ObjSha256=Json->GetStringField(TEXT("sourceObjSha256"));
    FString WalkingText;TSharedPtr<FJsonObject> Walking;
    SolarRequire(FFileHelper::LoadFileToString(WalkingText,*FPaths::Combine(FPaths::ProjectContentDir(),TEXT("Data/walking.json")))&&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(WalkingText),Walking)&&Walking.IsValid(),TEXT("Missing runtime source provenance"));
    auto Provenance=Walking->GetObjectField(TEXT("provenance"));
    SolarRequire(Provenance->GetStringField(TEXT("sceneSha256"))==Cases->SceneSha256 &&
        Provenance->GetStringField(TEXT("sourceObjSha256"))==Cases->ObjSha256,TEXT("Runtime world is not the reviewed solar fixture source"));
    Cases->SunTravel=SolarReadVector(Json,TEXT("solarTravelDirection"));
    SolarRequire(FMath::Abs(Cases->SunTravel.Size()-1)<1e-9&&Cases->SunTravel.Z<0,TEXT("Solar fixture must use normalized daylight direction"));
    for(const auto& Entry:Json->GetArrayField(TEXT("cases")))
    {
        auto Item=Entry->AsObject();FVector Origin=SolarReadVector(Item,TEXT("originCm")),Direction=SolarReadVector(Item,TEXT("directionTowardSun"));
        SolarRequire((Direction+Cases->SunTravel).Size()<1e-9,TEXT("Solar ray direction differs from frozen sun"));
        const double Min=Item->GetNumberField(TEXT("tMinCm")),Max=Item->GetNumberField(TEXT("tMaxCm"));
        SolarRequire(Min==.01&&Max==50000,TEXT("Solar ray bounds changed"));
        Cases->Rays.Add({FVector4f(FVector3f(Origin),float(Min)),FVector4f(FVector3f(Direction),float(Max))});
    }
    SolarRequire(Cases->Rays.Num()==BreziSolarCaseCount,TEXT("Solar fixture case count changed"));
    return Cases;
}

#if RHI_RAYTRACING
class FBreziSolarVisibilityCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FBreziSolarVisibilityCS);
    SHADER_USE_PARAMETER_STRUCT(FBreziSolarVisibilityCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER_STRUCT_REF(FViewUniformShaderParameters,View)
        SHADER_PARAMETER_RDG_BUFFER_SRV(RaytracingAccelerationStructure,SolarTLAS)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<SolarRay>,SolarRays)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<SolarResult>,SolarResults)
        SHADER_PARAMETER(FVector3f,SolarPreViewTranslationCm)
        SHADER_PARAMETER(uint32,SolarRayCount)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {
        return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6)&&IsRayTracingEnabledForProject(P.Platform)
            &&RHISupportsRayTracing(P.Platform)&&RHISupportsInlineRayTracing(P.Platform);
    }
    static void ModifyCompilationEnvironment(const FGlobalShaderPermutationParameters& P,FShaderCompilerEnvironment& Environment)
    {
        FGlobalShader::ModifyCompilationEnvironment(P,Environment);
        Environment.CompilerFlags.Add(CFLAG_InlineRayTracing);
        Environment.CompilerFlags.Add(CFLAG_Wave32);
    }
};
IMPLEMENT_GLOBAL_SHADER(FBreziSolarVisibilityCS,"/Plugin/BreziCausticsProbe/Private/BreziSolarVisibility.usf","SolarVisibilityCS",SF_Compute);
#endif

class FBreziSolarVisibilityExtension : public FSceneViewExtensionBase
{
    TSharedRef<FSolarCases,ESPMode::ThreadSafe> Cases;
    const bool bCaptureRequested;
    std::atomic<bool> bStopped{false};
    FString Directory;
    FCriticalSection SunMutex;
    struct FSolarGameSnapshot
    {
        uint64 FrameCounter=0;uint32 FrameNumber=0;
        const FSceneInterface* Scene=nullptr; // Identity token only; never dereferenced across threads.
        FVector Sun=FVector::ZeroVector;double Lux=0;bool bSunValid=false;
        TMap<FString,double> Cvars;TArray<FString> MissingCvars;
    };
    // Copied under SunMutex. No UObject/shared JSON ownership crosses threads.
    TMap<uint64,FSolarGameSnapshot> GameSnapshots;
    uint32 EligibleFrames=0;
    bool bScheduled=false,bComplete=false;
    FString LastUnavailable=TEXT("No eligible main-view post-TLAS callback observed");
    TUniquePtr<FRHIGPUBufferReadback> Readback;
    TSharedPtr<FJsonObject> PendingMeta;
    TFuture<void> Writer;

    TSharedRef<FJsonObject> BaseMeta(const FString& Status) const
    {
        auto Meta=MakeShared<FJsonObject>();Meta->SetStringField(TEXT("status"),Status);
        Meta->SetStringField(TEXT("captureId"),FPaths::GetCleanFilename(Directory));
        Meta->SetStringField(TEXT("casesSha256"),BreziSolarCasesSha256);
        Meta->SetStringField(TEXT("shaderSha256"),BreziSolarShaderSha256);
        Meta->SetStringField(TEXT("sceneSha256"),Cases->SceneSha256);Meta->SetStringField(TEXT("sourceObjSha256"),Cases->ObjSha256);
        Meta->SetNumberField(TEXT("rendererPid"),FPlatformProcess::GetCurrentProcessId());
        Meta->SetNumberField(TEXT("caseCount"),Cases->Rays.Num());Meta->SetNumberField(TEXT("resultStrideBytes"),SolarOutputStride);
        Meta->SetBoolField(TEXT("productionLightingBound"),false);Meta->SetBoolField(TEXT("sunVisibilityImplemented"),false);
        Meta->SetBoolField(TEXT("opaqueForced"),true);Meta->SetBoolField(TEXT("proceduralGeometrySkipped"),true);
        Meta->SetNumberField(TEXT("instanceMask"),4);Meta->SetBoolField(TEXT("nativeIdsAreCanonicalSourceIds"),false);
        Meta->SetStringField(TEXT("scope"),TEXT("Finite source-derived opaque shadow geometry controls only; no leaf alpha, transmission or full-scene visibility proof"));
        return Meta;
    }
    void ResolveReadback()
    {
        if(!bScheduled||bComplete||!Readback||!Readback->IsReady())return;
        const uint32 ByteCount=Cases->Rays.Num()*SolarOutputStride;TArray<uint8> Bytes;Bytes.SetNumUninitialized(ByteCount);
        void* Data=Readback->Lock(ByteCount);SolarRequire(Data!=nullptr,TEXT("Solar readback lock failed"));
        FMemory::Memcpy(Bytes.GetData(),Data,ByteCount);Readback->Unlock();
        PendingMeta->SetStringField(TEXT("status"),TEXT("GPU-readback-awaiting-opaque-source-validation"));
        const FString MetaText=SolarJsonText(PendingMeta.ToSharedRef()),CaseText=Cases->JsonText,Output=Directory;
        Writer=Async(EAsyncExecution::ThreadPool,[MetaText,CaseText,Output,Bytes=MoveTemp(Bytes)]()
        {
            IFileManager::Get().MakeDirectory(*Output,true);
            SolarRequire(FFileHelper::SaveArrayToFile(Bytes,*FPaths::Combine(Output,TEXT("solar-results-le.bin"))),TEXT("Cannot save solar readback"));
            SolarRequire(FFileHelper::SaveStringToFile(CaseText,*FPaths::Combine(Output,TEXT("solar-visibility-cases.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM),TEXT("Cannot save solar fixture"));
            // Completion marker is written last, after both immutable inputs.
            SolarRequire(FFileHelper::SaveStringToFile(MetaText,*FPaths::Combine(Output,TEXT("capture.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM),TEXT("Cannot save solar metadata"));
            UE_LOG(LogBreziSolarVisibility,Display,TEXT("BREZI_SOLAR_VISIBILITY_CAPTURE %s"),*Output);
        });
        bComplete=true;
    }
public:
    FBreziSolarVisibilityExtension(const FAutoRegister& AutoRegister,TSharedRef<FSolarCases,ESPMode::ThreadSafe> InCases,bool bInCapture)
        :FSceneViewExtensionBase(AutoRegister),Cases(InCases),bCaptureRequested(bInCapture)
    {
        Directory=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("SolarVisibilityProbe"),FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphens));
        if(bCaptureRequested)SolarSaveJson(Directory,BaseMeta(TEXT("awaiting-main-view-HWRT-TLAS-and-GPU-readback")));
    }
    void Stop() { bStopped.store(true); }
    ~FBreziSolarVisibilityExtension() override
    {
        if(Writer.IsValid())Writer.Wait();
        if(bCaptureRequested&&!bComplete)
        {
            auto Meta=BaseMeta(TEXT("incomplete-no-validated-GPU-readback"));Meta->SetStringField(TEXT("reason"),LastUnavailable);
            SolarSaveJson(Directory,Meta);
            UE_LOG(LogBreziSolarVisibility,Warning,TEXT("BREZI_SOLAR_VISIBILITY_INCOMPLETE %s; %s"),*Directory,*LastUnavailable);
        }
    }
    ESceneViewExtensionFlags GetFlags() const override
    {
        return bCaptureRequested ? ESceneViewExtensionFlags::SubscribesToPostTLASBuild|ESceneViewExtensionFlags::RequiresHardwareInlineRayTracing
                                 : ESceneViewExtensionFlags::None;
    }
    void SetupViewFamily(FSceneViewFamily&) override {}
    void SetupView(FSceneViewFamily&,FSceneView&) override {}
    void BeginRenderViewFamily(FSceneViewFamily& Family) override
    {
        if(bStopped.load()||!bCaptureRequested||Family.Views.Num()!=1||Family.Views[0]->bIsSceneCapture||Family.Views[0]->bIsReflectionCapture)return;
        UWorld* World=Family.Scene?Family.Scene->GetWorld():nullptr;
        if(!World||!World->IsGameWorld())return;
        FVector Direction=FVector::ZeroVector;double Lux=0;int32 Count=0;
        if(World&&World->IsGameWorld())for(TActorIterator<ADirectionalLight> It(World);It;++It)if(It->ActorHasTag(TEXT("BreziSun")))
        {
            ++Count;ULightComponent* Light=It->GetLightComponent();
            if(Light&&Light->IsRegistered()&&Light->IsVisible()&&Light->bAffectsWorld&&!It->IsHidden())
            {Direction=Light->GetDirection();Lux=Light->Intensity;}
        }
        FSolarGameSnapshot Snapshot;Snapshot.FrameCounter=Family.FrameCounter;Snapshot.FrameNumber=Family.FrameNumber;Snapshot.Scene=Family.Scene;
        Snapshot.Sun=Direction;Snapshot.Lux=Lux;Snapshot.bSunValid=Count==1&&Lux>0&&(Direction-Cases->SunTravel).Size()<1e-5;
        // NaniteProxies is not ECVF_RenderThreadSafe in UE 5.8. Read every
        // diagnostic cvar on GT and carry values with this exact family identity.
        for(const TCHAR* Name:{TEXT("r.RayTracing.Culling"),TEXT("r.RayTracing.Culling.PerInstance"),TEXT("r.RayTracing.Culling.Radius"),TEXT("r.RayTracing.Culling.Angle"),TEXT("r.RayTracing.Nanite.Mode"),TEXT("r.RayTracing.Geometry.NaniteProxies"),TEXT("r.Lumen.HardwareRayTracing")})
        {
            if(auto* Variable=IConsoleManager::Get().FindConsoleVariable(Name))Snapshot.Cvars.Add(Name,Variable->GetFloat());
            else Snapshot.MissingCvars.Add(Name);
        }
        FScopeLock Lock(&SunMutex);GameSnapshots.Add(Family.FrameCounter,MoveTemp(Snapshot));
        for(auto It=GameSnapshots.CreateIterator();It;++It)
            if(It.Key()<Family.FrameCounter&&Family.FrameCounter-It.Key()>32)It.RemoveCurrent();
    }
    void PostRenderBasePassDeferred_RenderThread(FRDGBuilder&,FSceneView&,const FRenderTargetBindingSlots&,TRDGUniformBufferRef<FSceneTextureUniformParameters>) override
    {
        if(!bStopped.load())ResolveReadback();
    }
    void PostTLASBuild_RenderThread(FRDGBuilder& GraphBuilder,FSceneView& View) override
    {
        if(bStopped.load()||!bCaptureRequested)return;
        ResolveReadback();if(bScheduled)return;
        if(View.bIsSceneCapture||View.bIsReflectionCapture||!View.Family||View.Family->Views.Num()!=1||!View.Family->Scene)return;
        FSolarGameSnapshot Snapshot;
        {
            FScopeLock Lock(&SunMutex);const auto* Found=GameSnapshots.Find(View.Family->FrameCounter);
            if(!Found||Found->FrameNumber!=View.Family->FrameNumber||Found->Scene!=View.Family->Scene)
            {LastUnavailable=TEXT("No GT sun/settings snapshot for this exact TLAS frame/family");return;}
            Snapshot=*Found;
        }
        if(!Snapshot.bSunValid){LastUnavailable=TEXT("Runtime game sun differs from the frozen daylight case direction or is disabled");return;}
        const FVector Sun=Snapshot.Sun;const double Lux=Snapshot.Lux;
#if RHI_RAYTRACING
        if(View.GetFeatureLevel()<ERHIFeatureLevel::SM6||!GRHISupportsRayTracing||!GRHISupportsInlineRayTracing||!IsRayTracingEnabled())
        {LastUnavailable=TEXT("Current main view does not have supported active SM6 HWRT/inline ray tracing");return;}
        if(!UE::FXRenderingUtils::RayTracing::HasRayTracingScene(*View.Family->Scene))
        {LastUnavailable=TEXT("Current main view has no ray-tracing scene");return;}
        if(++EligibleFrames<SolarWarmupFrames)return;
        // This callback follows the actual per-view TLAS build. Never retrieve
        // or cache this SRV at another stage or retain it across RDG frames.
        FRDGBufferSRVRef TLAS=UE::FXRenderingUtils::RayTracing::GetRayTracingSceneViewRDG(*View.Family->Scene,View);
        if(!TLAS){LastUnavailable=TEXT("Post-TLAS callback returned no current-view TLAS SRV");return;}
        // RayTracingCommon/TraceRayInline use View for translated-world/TLAS
        // transforms. Bind this exact paired FSceneView's public uniform buffer.
        FRHIUniformBuffer* const PairedViewUniform=View.ViewUniformBuffer.GetReference();
        if(!PairedViewUniform){LastUnavailable=TEXT("Current Post-TLAS view has no View uniform buffer");return;}
        FRDGBufferRef Rays=CreateStructuredBuffer(GraphBuilder,TEXT("Brezi.SolarVisibility.Rays"),sizeof(FSolarRayGPU),Cases->Rays.Num(),Cases->Rays.GetData(),Cases->Rays.Num()*sizeof(FSolarRayGPU));
        FRDGBufferRef Results=GraphBuilder.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(SolarOutputStride,Cases->Rays.Num()),TEXT("Brezi.SolarVisibility.Results"));
        auto* Parameters=GraphBuilder.AllocParameters<FBreziSolarVisibilityCS::FParameters>();
        Parameters->View=GetShaderBinding(View.ViewUniformBuffer);
        const bool bPairedViewUniformBound=Parameters->View.GetUniformBuffer()==PairedViewUniform&&Parameters->View.IsShader();
        SolarRequire(bPairedViewUniformBound,TEXT("Solar shader View uniform is not the current paired view's explicit shader binding"));
        Parameters->SolarTLAS=TLAS;Parameters->SolarRays=GraphBuilder.CreateSRV(Rays);Parameters->SolarResults=GraphBuilder.CreateUAV(Results);
        Parameters->SolarPreViewTranslationCm=FVector3f(View.ViewMatrices.GetPreViewTranslation());Parameters->SolarRayCount=Cases->Rays.Num();
        TShaderMapRef<FBreziSolarVisibilityCS> Shader(GetGlobalShaderMap(View.GetFeatureLevel()));
        FComputeShaderUtils::AddPass(GraphBuilder,RDG_EVENT_NAME("Brezi.SolarVisibility.OpaqueControls"),Shader,Parameters,FIntVector((Cases->Rays.Num()+31)/32,1,1));
        Readback=MakeUnique<FRHIGPUBufferReadback>(TEXT("BreziSolarVisibility"));
        AddEnqueueCopyPass(GraphBuilder,Readback.Get(),Results,Cases->Rays.Num()*SolarOutputStride);
        PendingMeta=BaseMeta(TEXT("GPU-readback-pending"));PendingMeta->SetNumberField(TEXT("frameNumber"),View.Family->FrameNumber);
        PendingMeta->SetNumberField(TEXT("gameTimeSeconds"),View.Family->Time.GetWorldTimeSeconds());
        PendingMeta->SetArrayField(TEXT("cameraOriginCm"),SolarVectorJson(View.ViewMatrices.GetViewOrigin()));
        PendingMeta->SetArrayField(TEXT("preViewTranslationCm"),SolarVectorJson(View.ViewMatrices.GetPreViewTranslation()));
        PendingMeta->SetArrayField(TEXT("solarTravelDirection"),SolarVectorJson(Sun));PendingMeta->SetNumberField(TEXT("nativeDirectionalLux"),Lux);
        PendingMeta->SetBoolField(TEXT("pairedViewUniformBindingValid"),bPairedViewUniformBound);
        PendingMeta->SetStringField(TEXT("pairedViewUniformSource"),TEXT("current-PostTLAS-FSceneView.ViewUniformBuffer"));
        PendingMeta->SetStringField(TEXT("pairedViewUniformBindingMode"),TEXT("explicit-shader-binding"));
        PendingMeta->SetNumberField(TEXT("pairedViewUniformFrameNumber"),View.Family->FrameNumber);
        PendingMeta->SetBoolField(TEXT("nativeSunAffectsWorldVisible"),true);
        PendingMeta->SetBoolField(TEXT("sameFramePostTLAS"),true);PendingMeta->SetBoolField(TEXT("mainViewOnly"),true);
        PendingMeta->SetNumberField(TEXT("eligiblePostTLASCallbacks"),EligibleFrames);
        PendingMeta->SetBoolField(TEXT("runtimeRayTracingEnabled"),IsRayTracingEnabled());
        PendingMeta->SetBoolField(TEXT("runtimeHWRTSupported"),GRHISupportsRayTracing);PendingMeta->SetBoolField(TEXT("runtimeInlineSupported"),GRHISupportsInlineRayTracing);
        PendingMeta->SetStringField(TEXT("rhi"),GDynamicRHI?GDynamicRHI->GetName():TEXT("unavailable"));
        auto Cvars=MakeShared<FJsonObject>();
        for(const auto& Pair:Snapshot.Cvars)Cvars->SetNumberField(Pair.Key,Pair.Value);
        for(const auto& Name:Snapshot.MissingCvars)Cvars->SetField(Name,MakeShared<FJsonValueNull>());
        PendingMeta->SetObjectField(TEXT("capturedCvars"),Cvars);
        PendingMeta->SetNumberField(TEXT("viewFamilyFrameCounter"),View.Family->FrameCounter);
        PendingMeta->SetNumberField(TEXT("gameSnapshotFrameCounter"),Snapshot.FrameCounter);
        PendingMeta->SetNumberField(TEXT("gameSnapshotFrameNumber"),Snapshot.FrameNumber);
        PendingMeta->SetBoolField(TEXT("gameSnapshotSceneIdentityMatched"),true);
        PendingMeta->SetStringField(TEXT("cvarSnapshotThread"),TEXT("game-thread-matched-frame-and-family"));
        bScheduled=true;LastUnavailable=TEXT("Scheduled GPU readback has not completed");
#else
        LastUnavailable=TEXT("RHI_RAYTRACING was not compiled for this platform");
#endif
    }
};

class FBreziSolarVisibilityOwner final : public IBreziSolarVisibilityProbe
{
    TSharedPtr<FBreziSolarVisibilityExtension,ESPMode::ThreadSafe> Extension;
public:
    FBreziSolarVisibilityOwner(const FString& Path,bool bCapture)
    {Extension=FSceneViewExtensions::NewExtension<FBreziSolarVisibilityExtension>(SolarLoadCases(Path),bCapture);}
    ~FBreziSolarVisibilityOwner() override {Stop();}
    void Stop() override
    {if(Extension){Extension->Stop();FlushRenderingCommands();Extension.Reset();}}
};
TUniquePtr<IBreziSolarVisibilityProbe> CreateBreziSolarVisibilityProbe(const FString& CasesPath,bool bCaptureRequested)
{
    return MakeUnique<FBreziSolarVisibilityOwner>(CasesPath,bCaptureRequested);
}
