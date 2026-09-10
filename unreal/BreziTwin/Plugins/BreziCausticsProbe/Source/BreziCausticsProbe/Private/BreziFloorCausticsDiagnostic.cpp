#include "BreziFloorCausticsDiagnostic.h"
#include "BreziFloorCausticsDiagnosticContract.h"
#include "BreziCausticsContract.h"
#include "BreziCausticsTransport.h"
#include "BreziCausticsTransportContract.h"
#include "BreziCausticsWaterBinding.h"
#include "BreziCausticsDeliveryContract.h"
#include "BreziSolarVisibilityContract.h"
#include "RenderingThread.h"

DEFINE_LOG_CATEGORY_STATIC(LogBreziFloorDiagnostic, Log, All);

#if BREZI_HAS_FLOOR_CAUSTICS_API
#include "FloorCausticsRendering.h"
#include "BreziTransportSceneBinding.h"
#include "BreziCookedSceneBinding.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Async/Async.h"
#include "HAL/PlatformProperties.h"
#include "SceneViewExtension.h"
#include "SceneInterface.h"
#include "FXRenderingUtils.h"
#include "RHIGlobals.h"
#include "DynamicRHI.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "GlobalShader.h"
#include "RenderUtils.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"
#include "Engine/World.h"
#include "Engine/DirectionalLight.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/LineBatchComponent.h"
#include "UObject/UObjectIterator.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Misc/ScopeLock.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformTime.h"
#include "HAL/IConsoleManager.h"
#include "Interfaces/IPluginManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include <atomic>

namespace
{
void Require(bool Ok, const TCHAR* Why)
{
    if (!Ok) UE_LOG(LogBreziFloorDiagnostic, Fatal, TEXT("%s"), Why);
}
FString Sha1(const TArray<uint8>& Bytes)
{
    uint8 Hash[FSHA1::DigestSize]; FSHA1::HashBuffer(Bytes.GetData(), Bytes.Num(), Hash);
    return BytesToHex(Hash, FSHA1::DigestSize).ToLower();
}
TArray<TSharedPtr<FJsonValue>> Vec(const FVector& V)
{
    return {MakeShared<FJsonValueNumber>(V.X), MakeShared<FJsonValueNumber>(V.Y), MakeShared<FJsonValueNumber>(V.Z)};
}
FVector ReadVec(const TSharedPtr<FJsonObject>& J, const TCHAR* Key)
{
    const auto& A = J->GetArrayField(Key); Require(A.Num() == 3, TEXT("Expected source vector3"));
    FVector V(A[0]->AsNumber(), A[1]->AsNumber(), A[2]->AsNumber());
    Require(!V.ContainsNaN(), TEXT("Nonfinite source bounds")); return V;
}
void SaveJson(const FString& Directory, const TCHAR* Name, const TSharedRef<FJsonObject>& J)
{
    FString Text; Require(FJsonSerializer::Serialize(J, TJsonWriterFactory<>::Create(&Text)), TEXT("Cannot serialize diagnostic receipt"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    Require(FFileHelper::SaveStringToFile(Text, *FPaths::Combine(Directory, Name), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM), TEXT("Cannot save diagnostic receipt"));
}
struct FContract
{
    FString BytesText, FloorId, FloorAsset, SceneSha256, ObjSha256;
    FBox Bounds = FBox(ForceInit);
    double WaterZ = 0;
};
FContract LoadContract(const FString& Path, bool bTransport = false, bool bContinuous = false)
{
    TArray<uint8> Bytes; Require(FFileHelper::LoadFileToArray(Bytes, *Path), TEXT("Missing diagnostic contract"));
    Require(Sha1(Bytes) == (bContinuous ? BreziDeliveryContractSha1 : bTransport ? BreziTransportContractSha1 : FloorDiagnosticSha1), TEXT("Diagnostic fixture bytes differ from compiled binding"));
    FContract C; FFileHelper::BufferToString(C.BytesText, Bytes.GetData(), Bytes.Num()); TSharedPtr<FJsonObject> J;
    Require(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(C.BytesText), J) && J.IsValid(), TEXT("Invalid diagnostic contract"));
    Require(J->GetIntegerField(TEXT("schemaVersion")) == (bContinuous ? 4 : bTransport ? 3 : 2) && J->GetStringField(TEXT("receiverContractSha256")) == BreziCausticsContractSha256,
        TEXT("Unknown receiver binding"));
    C.FloorId = J->GetStringField(TEXT("floorObjectId")); C.FloorAsset = J->GetStringField(TEXT("floorAsset"));
    C.SceneSha256 = J->GetStringField(TEXT("sceneSha256")); C.ObjSha256 = J->GetStringField(TEXT("sourceObjSha256"));
    const auto Bounds = J->GetObjectField(TEXT("sourceBoundsCm")); C.Bounds = FBox(ReadVec(Bounds, TEXT("min")), ReadVec(Bounds, TEXT("max")));
    C.WaterZ = J->GetNumberField(TEXT("waterSurfaceZCm"));
    Require(C.FloorId == TEXT("DOM_01720") && C.Bounds.IsValid && C.Bounds.GetSize().GetMin() > 0 && C.WaterZ > C.Bounds.Max.Z,
        TEXT("Invalid canonical receiver bounds"));
    FString Text; TSharedPtr<FJsonObject> Walking;
    Require(FFileHelper::LoadFileToString(Text, *FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Data/walking.json")))
        && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Walking) && Walking.IsValid(), TEXT("Missing runtime provenance"));
    const auto P = Walking->GetObjectField(TEXT("provenance"));
    Require(P->GetStringField(TEXT("sceneSha256")) == C.SceneSha256 && P->GetStringField(TEXT("sourceObjSha256")) == C.ObjSha256,
        TEXT("Runtime source differs from receiver diagnostic"));
    return C;
}
struct FLineBatcherIdentity
{
    FString Type, ComponentPath, ClassPath;
    uint32 PrimitiveId = 0;
    int32 Lines = 0, Points = 0, Meshes = 0;
    bool bPresent = false, bRegistered = false, bPrimitiveIdValid = false, bAccurateBounds = false;
};
struct FSnapshot
{
    FFloorCausticsSelection Selection;
    uint64 FrameCounter = 0;
    uint32 FrameNumber = 0;
    FString FloorPath, SunPath, WorldPath, TransportSceneSnapshot, MotionScreenshotPath;
    int32 MotionIndex = INDEX_NONE;
    uint64 MotionRequestCounter = 0;
    TMap<FString, float> Cvars;
    TArray<FLineBatcherIdentity, TInlineAllocator<4>> LineBatchers;
    bool bValid = false;
};
struct FDiagnosticGraph
{
    FRDGTextureRef Atlas = nullptr;
    uint64 FrameCounter = 0;
    FRDGBufferSRVRef CurrentTLAS = nullptr;
    const FSceneView* TLASView = nullptr; // graph-local identity, never retained by provider
    uint64 TLASFrameCounter = 0;
    uint32 TLASFrameNumber = 0;
    FBreziCausticsProducedGraph Transport;
};
}
RDG_REGISTER_BLACKBOARD_STRUCT(FDiagnosticGraph);
namespace
{

#include "BreziContinuousMotionCapture.inl"

class FDiagnosticExtension final : public FSceneViewExtensionBase, public IFloorCausticsProvider
{
    const FContract Contract;
    const FString Mode, Directory;
    const bool bContinuous, bMotionQA;
    bool IsTransport() const { return bContinuous || Mode == TEXT("transport-opaque"); }
    uint64 UnsupportedContinuousFrames = 0;
    TUniquePtr<FBreziContinuousMotionCapture> MotionCapture;
    TUniquePtr<IBreziCausticsTransport> Transport;
    // GT-only cache; RT receives only serialized immutable identity/geometry evidence.
    BreziTransportSceneBinding::FCache SceneBinding;
    BreziCookedSceneBinding::FVerifiedPackage CookedBinding;
    struct FCookedVerification { BreziCookedSceneBinding::FVerifiedPackage Token; FString Error; bool bSuccess=false; };
    TFuture<FCookedVerification> CookedVerification;
    FString ReceiverPath, CookedVerificationError;
    bool bCookedVerificationPending=false, bCookedVerificationFailed=false;
    void InitializeTransport_GT(bool bVerifiedCooked)
    {
        check(IsInGameThread());
        Transport=CreateBreziCausticsTransport(ReceiverPath,bVerifiedCooked);
        for(const auto& Pair:TArray<TPair<FString,FString>>{{TEXT("receiver-contract.json"),Transport->ReceiverJson()},{TEXT("active-water-binding.json"),Transport->WaterJson()},{TEXT("solar-visibility-cases.json"),Transport->SolarJson()}})
            Require(FFileHelper::SaveStringToFile(Pair.Value,*FPaths::Combine(Directory,Pair.Key),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM),TEXT("Cannot copy pinned transport evidence"));
    }
    bool ReadyTransport_GT()
    {
        check(IsInGameThread());
        if(bCookedVerificationPending)
        {
            if(!CookedVerification.IsReady()) { LastGTReason=TEXT("cooked package verification pending; contribution inactive");return false; }
            auto Result=CookedVerification.Get();bCookedVerificationPending=false;
            if(!Result.bSuccess || !Result.Token.IsVerified())
            { bCookedVerificationFailed=true;CookedVerificationError=Result.Error; }
            else { CookedBinding=MoveTemp(Result.Token);InitializeTransport_GT(true); }
        }
        if(bCookedVerificationFailed) { LastGTReason=CookedVerificationError;return false; }
        return !IsTransport() || Transport.IsValid();
    }
    FString SceneBindingPath, SceneBindingError;
    bool bSceneBindingAttempted = false;
    FCriticalSection SnapshotMutex;
    TMap<uint64, FSnapshot> Snapshots;
    TWeakObjectPtr<UWorld> OwnedWorld;
    TWeakObjectPtr<UStaticMeshComponent> OwnedFloor;
    const uint64 Generation = FPlatformTime::Cycles64() | uint64(1);
    uint8 Stencil = 0;
    bool PriorCustomDepth = false;
    int32 PriorStencil = 0;
    ERendererStencilMask PriorMask = ERendererStencilMask::ERSM_Default;
    bool bOwned = false, bRestored = false;
    FString LastGTReason = TEXT("No source-valid game view"), LastRTReason = TEXT("No renderer callback");
    uint64 SelectCalls = 0, BuiltFrames = 0, ObservedFrames = 0, RejectedFrames = 0;
    bool bReadbackSubmitted = false, bReadbackComplete = false;
    TUniquePtr<FRHIGPUBufferReadback> CounterReadback;
    TUniquePtr<FRHIGPUBufferReadback> PhotonReadback, VisibilityReadback, TransportGatesReadback, GPUUniformReadback;
    TUniquePtr<FRHIGPUTextureReadback> AtlasReadback, CompanionReadback;
    TSharedPtr<FJsonObject> PendingMeta;
    FSnapshot SelectedSnapshot;
    struct FStageReadback
    {
        TUniquePtr<FRHIGPUTextureReadback> Color, Depth, Companion;
        TSharedPtr<FJsonObject> Meta;
        bool bSubmitted = false, bSaved = false;
    };
    FStageReadback Stages[4];
    TSharedPtr<FJsonObject> DownstreamMeta;
    uint64 DownstreamFrameCounter = 0;
    uint32 DownstreamFrameNumber = 0;
    uint32 InactiveEligibleFrames = 0;
    int32 NextStage = 0;
    bool bDownstreamStarted = false, bDownstreamComplete = false;
    FString DownstreamError;
    static const TCHAR* StageName(int32 I)
    {
        const TCHAR* Names[] = {TEXT("AfterRenderLights"), TEXT("BeforeComposite"), TEXT("AfterComposite"), TEXT("AfterSingleLayerWater")};
        return Names[I];
    }
    void PollDownstream_RT()
    {
        check(IsInRenderingThread());
        if (!bDownstreamStarted || bDownstreamComplete) return;
        for (int32 I = 0; I < 4; ++I)
        {
            auto& S = Stages[I];
            if (!S.bSubmitted || S.bSaved || !S.Color->IsReady() || !S.Depth->IsReady() || (S.Companion && !S.Companion->IsReady())) continue;
            const FString Prefix = FString::Printf(TEXT("stage-%d-"), I);
            SaveBinaryRecord(*(Prefix + TEXT("scene-color-rgba16f-le.bin")), ReadTexture(*S.Color, FIntPoint(3840, 2160)), S.Meta.ToSharedRef());
            SaveBinaryRecord(*(Prefix + TEXT("device-z-f32le.bin")), ReadTexture(*S.Depth, FIntPoint(3840, 2160), 4), S.Meta.ToSharedRef());
            if (S.Companion) SaveBinaryRecord(*(Prefix + TEXT("companion-rgba16f-le.bin")), ReadTexture(*S.Companion, FIntPoint(3840, 2160)), S.Meta.ToSharedRef());
            S.bSaved = true;
        }
        bool Complete = NextStage == 4 && DownstreamError.IsEmpty();
        for (const auto& S : Stages) Complete &= S.bSaved;
        if (!Complete) return;
        TArray<TSharedPtr<FJsonValue>> Rows;
        for (const auto& S : Stages) Rows.Add(MakeShared<FJsonValueObject>(S.Meta));
        DownstreamMeta->SetArrayField(TEXT("stages"), Rows);
        DownstreamMeta->SetStringField(TEXT("status"), TEXT("gpu-four-stage-readback-captured-awaiting-independent-validation"));
        SaveJson(Directory, TEXT("downstream.json"), DownstreamMeta.ToSharedRef()); bDownstreamComplete = true;
        UE_LOG(LogBreziFloorDiagnostic, Display, TEXT("BREZI_FLOOR_DOWNSTREAM_READBACK %s"), *Directory);
    }

    bool BindFloor_GT(UWorld* World, UStaticMeshComponent* Floor)
    {
        if (bOwned) return OwnedWorld.Get() == World && OwnedFloor.Get() == Floor;
        TSet<int32> Used;
        for (TObjectIterator<UPrimitiveComponent> It; It; ++It)
            if (It->GetWorld() == World && It->IsRegistered() && It->bRenderCustomDepth && *It != Floor)
                Used.Add(It->CustomDepthStencilValue);
        int32 Free = 1; while (Free < 256 && Used.Contains(Free)) ++Free;
        if (Free == 256) { LastGTReason = TEXT("No unclaimed custom stencil"); return false; }
        OwnedWorld = World; OwnedFloor = Floor; Stencil = uint8(Free);
        PriorCustomDepth = Floor->bRenderCustomDepth; PriorStencil = Floor->CustomDepthStencilValue; PriorMask = Floor->CustomDepthStencilWriteMask;
        Floor->SetCustomDepthStencilWriteMask(ERendererStencilMask::ERSM_255);
        Floor->SetCustomDepthStencilValue(Stencil); Floor->SetRenderCustomDepth(true); bOwned = true;
        return true;
    }
    TSharedRef<FJsonObject> BaseMeta(const TCHAR* Status) const
    {
        auto J = MakeShared<FJsonObject>(); J->SetNumberField(TEXT("schemaVersion"), bContinuous ? 4 : Mode == TEXT("transport-opaque") ? 3 : 2); J->SetStringField(TEXT("status"), Status);
        J->SetStringField(TEXT("mode"), Mode); J->SetStringField(TEXT("diagnosticContractSha256"), bContinuous ? BreziDeliveryContractSha256 : Mode == TEXT("transport-opaque") ? BreziTransportContractSha256 : FloorDiagnosticSha256);
        J->SetStringField(TEXT("receiverContractSha256"), BreziCausticsContractSha256);
        J->SetStringField(TEXT("sceneSha256"), Contract.SceneSha256); J->SetStringField(TEXT("sourceObjSha256"), Contract.ObjSha256);
        J->SetNumberField(TEXT("nativePid"), FPlatformProcess::GetCurrentProcessId());
        J->SetBoolField(TEXT("syntheticAtlas"), Mode == TEXT("zero") || Mode == TEXT("constant")); J->SetBoolField(TEXT("physicalTransportValidated"), false);
        J->SetBoolField(TEXT("fullConsumerOrWaterResidualValidated"), false); J->SetBoolField(TEXT("fpsMeasured"), false);
        J->SetStringField(TEXT("readbackCost"), TEXT("Single-frame GPU readbacks and synchronous CPU file writes perturb diagnostic timing."));
        if (IsTransport())
        {
            J->SetStringField(TEXT("transportClassification"), bContinuous ? TEXT("continuous-shared-view-time-opaque-TLAS-12-wave-normalized-irradiance-opt-in") : TEXT("same-frame-opaque-TLAS-12-wave-normalized-irradiance-diagnostic"));
            J->SetBoolField(TEXT("fullPhysicalValidated"), false); J->SetBoolField(TEXT("productionDefaultChanged"), false);
            J->SetStringField(TEXT("waterBindingSha256"), BreziCausticsWaterBindingSha256);
            J->SetStringField(TEXT("sceneBindingSha256"), BreziTransportSceneBinding::BindingSha256);
            J->SetStringField(TEXT("traceShaderSha256"), BreziTransportTraceShaderSha256);
            J->SetStringField(TEXT("incomingShaderSha256"), BreziTransportIncomingShaderSha256);
            J->SetStringField(TEXT("solarCasesSha256"), BreziSolarCasesSha256);
            J->SetStringField(TEXT("visibilityScope"), TEXT("current-view opaque-shadow mask4 forced-opaque triangles; procedural skipped; alpha/transmission/coverage not validated"));
            J->SetNumberField(TEXT("originalSampleCount"), BreziTransportSamples); J->SetNumberField(TEXT("waveCount"), 12);
            J->SetNumberField(TEXT("visibilityRecordCount"), BreziTransportVisibilityCount);
            J->SetNumberField(TEXT("visibilityStrideBytes"), 48); J->SetNumberField(TEXT("photonStrideBytes"), 48);
            J->SetNumberField(TEXT("incomingOriginOffsetCm"), .2); J->SetNumberField(TEXT("incomingTMinCm"), .01); J->SetNumberField(TEXT("incomingTMaxCm"), 50000);
            J->SetArrayField(TEXT("atlasPixels"), {MakeShared<FJsonValueNumber>(512),MakeShared<FJsonValueNumber>(256)});
            J->SetStringField(TEXT("producerValidationScope"), TEXT("GT source binding and same-graph inputs accepted; GPU incomplete/sentinel flags zero contribution and require independent readback rejection"));
        }
        if(bContinuous)
        {
            J->SetBoolField(TEXT("continuousSharedViewTime"),true);
            J->SetBoolField(TEXT("motionQAEnabled"),bMotionQA);
            J->SetBoolField(TEXT("heavyDiagnosticReadbacksEnabled"),false);
            J->SetBoolField(TEXT("pluginDefaultActive"),false);
            J->SetBoolField(TEXT("explicitProjectConfigurationMayActivate"),true);
            J->SetStringField(TEXT("unsupportedLightingPolicy"),TEXT("reject current frame; no atlas history; canonical daytime sun direction only"));
            J->SetStringField(TEXT("readbackCost"),bMotionQA ? TEXT("64 small GPU evidence records and two atlas readbacks; timing perturbed") : TEXT("no GPU readback objects or copies; startup provenance copies and request/lifecycle JSON only"));
        }
        return J;
    }
    void SaveBinaryRecord(const TCHAR* Name, const TArray<uint8>& Bytes, const TSharedRef<FJsonObject>& Meta)
    {
        Require(FFileHelper::SaveArrayToFile(Bytes, *FPaths::Combine(Directory, Name)), TEXT("Cannot save diagnostic binary"));
        auto J = MakeShared<FJsonObject>(); J->SetNumberField(TEXT("bytes"), Bytes.Num()); J->SetStringField(TEXT("sha1"), Sha1(Bytes));
        Meta->SetObjectField(Name, J); // Host additionally pins SHA256 before evidence acceptance.
    }
    void SaveBinary(const TCHAR* Name, const TArray<uint8>& Bytes)
    {
        SaveBinaryRecord(Name, Bytes, PendingMeta.ToSharedRef());
    }
    TArray<uint8> ReadTexture(FRHIGPUTextureReadback& Readback, FIntPoint Size, int32 BytesPerPixel = 8)
    {
        int32 Pitch = 0, Height = 0; void* Data = Readback.Lock(Pitch, &Height);
        Require(Data && Pitch >= Size.X && Height >= Size.Y, TEXT("Invalid explicit-format readback pitch"));
        TArray<uint8> Bytes; Bytes.SetNumUninitialized(Size.X * Size.Y * BytesPerPixel);
        for (int32 Y = 0; Y < Size.Y; ++Y) FMemory::Memcpy(Bytes.GetData() + Y * Size.X * BytesPerPixel,
            static_cast<const uint8*>(Data) + Y * Pitch * BytesPerPixel, Size.X * BytesPerPixel);
        Readback.Unlock(); return Bytes;
    }
    TArray<uint8> ReadBuffer(FRHIGPUBufferReadback& Readback, uint32 ByteCount)
    {
        TArray<uint8> Bytes; Bytes.SetNumUninitialized(ByteCount); void* Data=Readback.Lock(ByteCount);
        Require(Data!=nullptr,TEXT("Transport readback lock unavailable")); FMemory::Memcpy(Bytes.GetData(),Data,ByteCount); Readback.Unlock(); return Bytes;
    }
    void PollReadback_RT()
    {
        check(IsInRenderingThread());
        if (!bReadbackSubmitted || bReadbackComplete || !CounterReadback || !AtlasReadback || !CompanionReadback || !CounterReadback->IsReady() || !AtlasReadback->IsReady() || !CompanionReadback->IsReady()) return;
        if (IsTransport() && (!PhotonReadback || !VisibilityReadback || !TransportGatesReadback || !GPUUniformReadback
            || !PhotonReadback->IsReady() || !VisibilityReadback->IsReady() || !TransportGatesReadback->IsReady() || !GPUUniformReadback->IsReady())) return;
        TArray<uint8> Counters; Counters.SetNumUninitialized(16); void* Data = CounterReadback->Lock(16);
        Require(Data != nullptr, TEXT("Missing counter readback")); FMemory::Memcpy(Counters.GetData(), Data, 16); CounterReadback->Unlock();
        uint32 Values[4]; FMemory::Memcpy(Values, Counters.GetData(), 16);
        auto Atlas = ReadTexture(*AtlasReadback, IsTransport() ? FIntPoint(512, 256) : FIntPoint(2, 2)); auto Companion = ReadTexture(*CompanionReadback, FIntPoint(3840, 2160));
        SaveBinary(TEXT("counters-u32le.bin"), Counters); SaveBinary(TEXT("atlas-rgba16f-le.bin"), Atlas); SaveBinary(TEXT("companion-rgba16f-le.bin"), Companion);
        TArray<TSharedPtr<FJsonValue>> Counts; for (uint32 V : Values) Counts.Add(MakeShared<FJsonValueNumber>(V));
        if (IsTransport())
        {
            SaveBinary(TEXT("photons-f32le.bin"), ReadBuffer(*PhotonReadback, BreziTransportSamples*48));
            SaveBinary(TEXT("visibility-r48-le.bin"), ReadBuffer(*VisibilityReadback, BreziTransportVisibilityCount*48));
            auto Gates=ReadBuffer(*TransportGatesReadback,4);auto Uniform=ReadBuffer(*GPUUniformReadback,16);
            SaveBinary(TEXT("transport-gates-u32le.bin"),Gates);SaveBinary(TEXT("transport-gpu-uniform-f32le.bin"),Uniform);
            uint32 Flags=0;float GPUValues[4];FMemory::Memcpy(&Flags,Gates.GetData(),4);FMemory::Memcpy(GPUValues,Uniform.GetData(),16);
            PendingMeta->SetNumberField(TEXT("transportGateFlags"),Flags);PendingMeta->SetBoolField(TEXT("transportGPUChecksPassed"),Flags==0);
            if(FMath::IsFinite(GPUValues[0])&&FMath::IsFinite(GPUValues[1]))
            { PendingMeta->SetNumberField(TEXT("gpuMaterialTimeSeconds"),GPUValues[0]);PendingMeta->SetNumberField(TEXT("gpuViewPreExposure"),GPUValues[1]); }
            PendingMeta->SetBoolField(TEXT("transportUniformFinite"),FMath::IsFinite(GPUValues[0])&&FMath::IsFinite(GPUValues[1])&&GPUValues[1]>0&&GPUValues[2]==0&&GPUValues[3]==0);
        }
        PendingMeta->SetArrayField(TEXT("prepareCounters"), Counts);
        PendingMeta->SetBoolField(TEXT("prepareCounterGatePassed"), Values[0] > 0 && Values[1] == 0 && Values[2] == 0);
        PendingMeta->SetStringField(TEXT("status"), TEXT("gpu-prepare-readback-captured-awaiting-independent-validation"));
        SaveJson(Directory, TEXT("capture.json"), PendingMeta.ToSharedRef()); bReadbackComplete = true;
        UE_LOG(LogBreziFloorDiagnostic, Display, TEXT("BREZI_FLOOR_DIAGNOSTIC_READBACK %s"), *Directory);
    }
public:
    std::atomic<bool> bStopped{false}, bRegistered{false};
    FDiagnosticExtension(const FAutoRegister& AutoRegister, FContract InContract, FString InMode)
        : FSceneViewExtensionBase(AutoRegister), Contract(MoveTemp(InContract)), Mode(MoveTemp(InMode)),
          Directory(FPaths::Combine(FPaths::ProjectSavedDir(), Mode == TEXT("transport-continuous") ? TEXT("FloorCausticsContinuous") : TEXT("FloorCausticsDiagnostic"), FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphens))),
          bContinuous(Mode == TEXT("transport-continuous")), bMotionQA(bContinuous && FParse::Param(FCommandLine::Get(),TEXT("BreziCausticsMotionQA")))
    {
        if(IsTransport())
        {
            ReceiverPath=FPaths::Combine(IPluginManager::Get().FindPlugin(TEXT("BreziCausticsProbe"))->GetBaseDir(),TEXT("Resources/receiver-contract.json"));
            SceneBindingPath=FPaths::Combine(FPaths::GetPath(ReceiverPath),TEXT("transport-scene-binding.json"));
            Require(BreziTransportSceneBinding::FileMatches(SceneBindingPath,BreziTransportSceneBinding::BindingSha1),TEXT("Scene binding bytes changed"));
            TArray<uint8> SceneBytes;Require(FFileHelper::LoadFileToArray(SceneBytes,*SceneBindingPath),TEXT("Missing source scene binding"));
            IFileManager::Get().MakeDirectory(*Directory,true);
            Require(FFileHelper::SaveArrayToFile(SceneBytes,*FPaths::Combine(Directory,TEXT("transport-scene-binding.json"))),TEXT("Cannot copy scene binding"));
            if(bContinuous && FPlatformProperties::RequiresCookedData())
            {
                const FString ReceiptPath=FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::GetPath(ReceiverPath),TEXT("cooked-runtime-binding.json")));
                const FString PakDirectory=FPaths::ConvertRelativePathToFull(FPaths::ProjectContentDir()/TEXT("Paks"));
                bCookedVerificationPending=true;
                // File/JSON/hash-only worker owns no provider/UObject pointer. GT polls once ready.
                CookedVerification=Async(EAsyncExecution::ThreadPool,[ReceiptPath,PakDirectory]()
                {
                    FCookedVerification R;
                    R.bSuccess=BreziCookedSceneBinding::VerifyPackage(ReceiptPath,PakDirectory,R.Token,R.Error);
                    return R;
                });
            }
            else InitializeTransport_GT(false);
        }
        if(bMotionQA) MotionCapture=MakeUnique<FBreziContinuousMotionCapture>(Directory,BaseMeta(TEXT("continuous-motion-readbacks-pending")));
        SaveJson(Directory, TEXT("request.json"), BaseMeta(TEXT("awaiting-registration-source-ownership-and-eligible-renderer")));
        Require(FFileHelper::SaveStringToFile(Contract.BytesText, *FPaths::Combine(Directory, TEXT("contract.json")),
            FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM), TEXT("Cannot save diagnostic source contract"));
    }
    bool OwnsWorld(UWorld* World) const { return OwnedWorld.Get() == World; }
    bool IsActiveThisFrame_Internal(const FSceneViewExtensionContext&) const override { return !bStopped.load(); }
    ESceneViewExtensionFlags GetFlags() const override
    { return IsTransport() ? ESceneViewExtensionFlags::SubscribesToPostTLASBuild | ESceneViewExtensionFlags::RequiresHardwareInlineRayTracing : ESceneViewExtensionFlags::None; }
    void SetupViewFamily(FSceneViewFamily&) override {}
    void SetupView(FSceneViewFamily&, FSceneView&) override {}
    void BeginRenderViewFamily(FSceneViewFamily& Family) override
    {
        check(IsInGameThread());
        if (bStopped.load() || !bRegistered.load() || !Family.Scene || Family.Views.Num() != 1) return;
        UWorld* World = Family.Scene->GetWorld();
        if (!World || !World->IsGameWorld() || Family.Views[0]->bIsSceneCapture || Family.Views[0]->bIsReflectionCapture) return;
        if(IsTransport() && !ReadyTransport_GT())return;
        FSnapshot S; S.FrameCounter = Family.FrameCounter; S.FrameNumber = Family.FrameNumber;
        if(bMotionQA && FScreenshotRequest::IsScreenshotRequested() && GFrameCounter==Family.FrameCounter)
        {
            const FString Filename=FPaths::GetCleanFilename(FScreenshotRequest::GetFilename());
            for(int32 I=0;I<64;++I) if(Filename==FString::Printf(TEXT("frame-%03d.png"),I))
            { S.MotionIndex=I;S.MotionScreenshotPath=FScreenshotRequest::GetFilename();S.MotionRequestCounter=GFrameCounter;break; }
        }
        // Actorless world components: copy plain GT data, never UObject pointers, to the render snapshot.
        const UWorld::ELineBatcherType BatcherTypes[] = {UWorld::ELineBatcherType::World,
            UWorld::ELineBatcherType::WorldPersistent, UWorld::ELineBatcherType::Foreground,
            UWorld::ELineBatcherType::ForegroundPersistent};
        const TCHAR* BatcherNames[] = {TEXT("World"), TEXT("WorldPersistent"), TEXT("Foreground"), TEXT("ForegroundPersistent")};
        for (int32 I = 0; (!bContinuous || bMotionQA) && I < UE_ARRAY_COUNT(BatcherTypes); ++I)
        {
            FLineBatcherIdentity Row; Row.Type = BatcherNames[I];
            if (const ULineBatchComponent* C = World->GetLineBatcher(BatcherTypes[I]))
            {
                Row.bPresent = true; Row.ComponentPath = C->GetPathName(); Row.ClassPath = C->GetClass()->GetPathName();
                Row.PrimitiveId = C->GetPrimitiveSceneId().PrimIDValue; Row.bPrimitiveIdValid = C->GetPrimitiveSceneId().IsValid();
                Row.bRegistered = C->IsRegistered(); Row.bAccurateBounds = C->bCalculateAccurateBounds;
                Row.Lines = C->BatchedLines.Num(); Row.Points = C->BatchedPoints.Num(); Row.Meshes = C->BatchedMeshes.Num();
            }
            S.LineBatchers.Add(MoveTemp(Row));
        }
        UStaticMeshComponent* Floor = nullptr; ULightComponent* Sun = nullptr; int32 FloorActors = 0, FloorComponents = 0, Suns = 0;
        for (TActorIterator<AActor> It(World); It; ++It) if (It->ActorHasTag(FName(*Contract.FloorId)))
        {
            ++FloorActors; TInlineComponentArray<UStaticMeshComponent*> Components; It->GetComponents(Components);
            for (UStaticMeshComponent* C : Components) if (C->IsRegistered()) { ++FloorComponents; Floor = C; }
        }
        for (TActorIterator<ADirectionalLight> It(World); It; ++It) if (It->ActorHasTag(TEXT("BreziSun")))
        { ++Suns; if (!It->IsHidden()) Sun = It->GetLightComponent(); }
        bool Valid = FloorActors == 1 && FloorComponents == 1 && Suns == 1 && Floor && Sun && Floor->GetStaticMesh()
            && Floor->GetStaticMesh()->GetPathName() == Contract.FloorAsset && Floor->IsVisible() && !Floor->GetOwner()->IsHidden()
            && Floor->bRenderInMainPass && Floor->IsRenderStateCreated() && Sun->IsRegistered() && Sun->IsVisible() && Sun->bAffectsWorld
            && Sun->GetLightComponentId().IsValid() && Floor->GetPrimitiveSceneId().IsValid()
            && Floor->Bounds.GetBox().Min.Equals(Contract.Bounds.Min, 0.05) && Floor->Bounds.GetBox().Max.Equals(Contract.Bounds.Max, 0.05);
        if (Valid && IsTransport())
        {
            // First proof precedes our stencil mutation; do not mistake startup frame count for proof.
            if(!bSceneBindingAttempted && Family.FrameNumber>=60 && !Floor->IsRenderStateDirty() && !Floor->IsRenderTransformDirty())
            { bSceneBindingAttempted=true; BreziTransportSceneBinding::LoadAndBind_GT(World,SceneBindingPath,SceneBinding,SceneBindingError,CookedBinding.IsVerified()?&CookedBinding:nullptr); }
            Valid=SceneBinding.bBound;
        }
        if (Valid) Valid = BindFloor_GT(World, Floor);
        if (Valid && IsTransport())
        {
            TSharedPtr<FJsonObject> Plain; SceneBindingError.Reset();
            Valid=BreziTransportSceneBinding::Snapshot_GT(World,SceneBinding,Family.FrameCounter,Family.FrameNumber,Plain,SceneBindingError,!bContinuous || S.MotionIndex!=INDEX_NONE);
            if(Valid && (!bContinuous || S.MotionIndex!=INDEX_NONE)) Valid=Plain.IsValid() && FJsonSerializer::Serialize(Plain.ToSharedRef(),TJsonWriterFactory<>::Create(&S.TransportSceneSnapshot));
        }
        if (Valid)
        {
            Valid = Floor->bRenderCustomDepth && Floor->CustomDepthStencilValue == Stencil && Floor->CustomDepthStencilWriteMask == ERendererStencilMask::ERSM_255;
            for (TObjectIterator<UPrimitiveComponent> It; It && Valid; ++It)
                if (It->GetWorld() == World && It->IsRegistered() && It->bRenderCustomDepth && *It != Floor)
                    Valid = It->CustomDepthStencilValue != Stencil;
        }
        if (Valid)
        {
            S.bValid = true; S.Selection.SceneToken = Family.Scene; S.Selection.Generation = Generation;
            S.Selection.Floor = Floor->GetPrimitiveSceneId(); S.Selection.Sun = Sun->GetLightComponentId(); S.Selection.SourceBoundsCm = Contract.Bounds;
            S.Selection.WaterSurfaceZCm = Contract.WaterZ; S.Selection.UniqueStencil = Stencil; S.Selection.SourceContractSha256 = BreziCausticsContractSha256;
            S.FloorPath = Floor->GetPathName(); S.SunPath = Sun->GetPathName(); S.WorldPath = World->GetPathName();
            LastGTReason = TEXT("exact source floor/sun and exclusive stencil bound");
        }
        else LastGTReason = IsTransport() && !SceneBindingError.IsEmpty() ? SceneBindingError : TEXT("source floor/sun/visibility/bounds/stencil ownership rejected");
        for (const TCHAR* Name : {TEXT("r.Brezi.FloorCaustics"), TEXT("r.CustomDepth"), TEXT("r.CustomDepthTemporalAAJitter"),
            TEXT("r.Water.SingleLayer.RefractionDownsampleFactor"), TEXT("r.Water.SingleLayer.UnderwaterFogWhenCameraIsAboveWater"),
            TEXT("r.ScreenPercentage"), TEXT("r.SecondaryScreenPercentage.GameViewport"), TEXT("r.DynamicRes.OperationMode")})
            if (const IConsoleVariable* C = IConsoleManager::Get().FindConsoleVariable(Name)) S.Cvars.Add(Name, C->GetFloat());
        if (IsTransport())
            for(const TCHAR* Name:{TEXT("r.Test.OverrideTimeMaterialExpressions"),TEXT("r.RayTracing.Culling"),TEXT("r.RayTracing.Culling.PerInstance"),
                TEXT("r.RayTracing.Culling.Radius"),TEXT("r.RayTracing.Culling.Angle"),TEXT("r.RayTracing.Nanite.Mode"),TEXT("r.RayTracing.Geometry.NaniteProxies"),TEXT("r.Lumen.HardwareRayTracing")})
            { if(const auto* C=IConsoleManager::Get().FindConsoleVariable(Name)) S.Cvars.Add(Name,C->GetFloat()); else S.bValid=false; }
        FScopeLock Lock(&SnapshotMutex); Snapshots.Add(S.FrameCounter, MoveTemp(S));
        for (auto It = Snapshots.CreateIterator(); It; ++It) if (It.Key() + 32 < Family.FrameCounter) It.RemoveCurrent();
    }
    void PreRenderViewFamily_RenderThread(FRDGBuilder&, FSceneViewFamily&) override { if (!bStopped.load()) { if(MotionCapture) MotionCapture->Poll_RT(); if(!bContinuous) { PollReadback_RT(); PollDownstream_RT(); } } }
    void PostTLASBuild_RenderThread(FRDGBuilder& GraphBuilder,FSceneView& View) override
    {
        if(bStopped.load() || !IsTransport() || !View.Family || View.Family->Views.Num()!=1 || View.bIsSceneCapture || View.bIsReflectionCapture) return;
#if RHI_RAYTRACING
        if(View.GetFeatureLevel()<ERHIFeatureLevel::SM6 || !GRHISupportsRayTracing || !GRHISupportsInlineRayTracing || !IsRayTracingEnabled()
            || !View.Family->Scene || !UE::FXRenderingUtils::RayTracing::HasRayTracingScene(*View.Family->Scene)) return;
        FScopeLock Lock(&SnapshotMutex);const auto* S=Snapshots.Find(View.Family->FrameCounter);
        if(!S || !S->bValid || S->FrameNumber!=View.Family->FrameNumber || S->Selection.SceneToken!=View.Family->Scene) return;
        auto& Local=GraphBuilder.Blackboard.GetOrCreate<FDiagnosticGraph>();
        Local.CurrentTLAS=UE::FXRenderingUtils::RayTracing::GetRayTracingSceneViewRDG(*View.Family->Scene,View);
        Local.TLASView=&View;Local.TLASFrameCounter=View.Family->FrameCounter;Local.TLASFrameNumber=View.Family->FrameNumber;
#endif
    }
    bool Select_RenderThread(const FSceneView& View, FFloorCausticsSelection& Out) override
    {
        ++SelectCalls; if (bStopped.load() || Mode == TEXT("inactive") || !View.Family) return false;
        FScopeLock Lock(&SnapshotMutex); const FSnapshot* S = Snapshots.Find(View.Family->FrameCounter);
        if (!S || !S->bValid || S->FrameNumber != View.Family->FrameNumber || S->Selection.SceneToken != View.Family->Scene) return false;
        SelectedSnapshot = *S; Out = S->Selection; return true;
    }
    bool Build_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FFloorCausticsBuildInputs& Inputs, FFloorCausticsProducedFrame& Out) override
    {
        if (bStopped.load() || Mode == TEXT("inactive") || !View.Family || SelectedSnapshot.FrameCounter != Inputs.FrameCounter || SelectedSnapshot.FrameNumber != Inputs.FrameNumber) return false;
        auto& Local = GraphBuilder.Blackboard.GetOrCreate<FDiagnosticGraph>(); if (Local.Atlas) return false;
        if (IsTransport())
        {
            const float* HWRT=SelectedSnapshot.Cvars.Find(TEXT("r.Lumen.HardwareRayTracing"));
            const float* Culling=SelectedSnapshot.Cvars.Find(TEXT("r.RayTracing.Culling"));
            const float* Phase=SelectedSnapshot.Cvars.Find(TEXT("r.Test.OverrideTimeMaterialExpressions"));
            if(!Transport || !HWRT || *HWRT!=1 || !Culling || *Culling!=0 || !Phase || !FMath::IsFinite(*Phase) || (bContinuous ? *Phase!=-1 : *Phase<0) || !Local.CurrentTLAS || Local.TLASView!=&View || Local.TLASFrameCounter!=Inputs.FrameCounter || Local.TLASFrameNumber!=Inputs.FrameNumber
                || !Transport->AcceptsSun(Inputs.SunTravelDirection) || (bContinuous && Inputs.SunIlluminance.GetMin()<1.0f)) { LastRTReason=TEXT("Transport lacks paired current TLAS/source/daylight sun or supported time"); if(bContinuous) ++UnsupportedContinuousFrames; return false; }
            Local.Transport=Transport->Build(GraphBuilder,View,Inputs.SunTravelDirection,Local.CurrentTLAS);Local.Atlas=Local.Transport.Atlas;
            if(!Local.Atlas) { LastRTReason=TEXT("Transport producer unavailable"); return false; }
        }
        else
        {
        Local.Atlas = GraphBuilder.CreateTexture(FRDGTextureDesc::Create2D(FIntPoint(2, 2), PF_FloatRGBA,
            FClearValueBinding::Black, TexCreate_ShaderResource | TexCreate_RenderTargetable), TEXT("Brezi.DiagnosticNormalizedFloorIrradiance"));
        const FLinearColor Value = Mode == TEXT("zero") ? FLinearColor(0, 0, 0, 1) : FLinearColor(0.125f, 0.25f, 0.5f, 1);
        AddClearRenderTargetPass(GraphBuilder, Local.Atlas, Value);
        }
        Local.FrameCounter = Inputs.FrameCounter;
        Out.SceneToken = Inputs.Selection.SceneToken; Out.Generation = Inputs.Selection.Generation;
        Out.FrameCounter = Inputs.FrameCounter; Out.FrameNumber = Inputs.FrameNumber; Out.WorldTimeSeconds = Inputs.WorldTimeSeconds;
        Out.NormalizedIrradiance = Local.Atlas;
        // Controls attest only their frozen analytic fixture. Transport attests the
        // explicitly scoped source/TLAS producer; GPU gates zero all energy on failure.
        // Neither mode asserts full physical transport; independent readback remains required.
        Out.bSourceTransportValidated = true; ++BuiltFrames; return true;
    }
    void Rejected_RenderThread(const FSceneView&, const TCHAR* Reason) override { ++RejectedFrames; LastRTReason = Reason; }
    void Observe_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FFloorCausticsBuildInputs& Inputs,
        FRDGTextureRef Companion, FRDGBufferRef Counters) override
    {
        if(bStopped.load())return;
        ++ObservedFrames;
        if(bContinuous)
        {
            LastRTReason=TEXT("continuous prepare submitted; no heavy diagnostic readback");
            if(MotionCapture && SelectedSnapshot.MotionIndex!=INDEX_NONE)
            {
                auto& Local=GraphBuilder.Blackboard.GetOrCreate<FDiagnosticGraph>();
                if(!Local.Atlas || Local.FrameCounter!=Inputs.FrameCounter || Local.TLASView!=&View
                    || !Companion || Companion->Desc.Extent!=FIntPoint(3840,2160) || View.UnscaledViewRect!=FIntRect(0,0,3840,2160))
                { MotionCapture->Reject_RT(TEXT("Requested motion frame lacked exact native4K paired producer"));return; }
                auto J=MakeShared<FJsonObject>();
                J->SetNumberField(TEXT("index"),SelectedSnapshot.MotionIndex);
                J->SetStringField(TEXT("screenshotPath"),SelectedSnapshot.MotionScreenshotPath);
                J->SetNumberField(TEXT("requestFrameCounter"),SelectedSnapshot.MotionRequestCounter);
                J->SetNumberField(TEXT("frameCounter"),Inputs.FrameCounter);J->SetNumberField(TEXT("frameNumber"),Inputs.FrameNumber);
                J->SetNumberField(TEXT("worldTimeSeconds"),Inputs.WorldTimeSeconds);
                J->SetArrayField(TEXT("sunTravelDirection"),Vec(FVector(Inputs.SunTravelDirection)));
                J->SetArrayField(TEXT("sunIlluminance"),Vec(FVector(Inputs.SunIlluminance)));
                J->SetArrayField(TEXT("viewOriginCm"),Vec(View.ViewMatrices.GetViewOrigin()));
                J->SetArrayField(TEXT("viewDirection"),Vec(View.GetViewDirection()));
                J->SetArrayField(TEXT("pixels"),{MakeShared<FJsonValueNumber>(3840),MakeShared<FJsonValueNumber>(2160)});
                J->SetBoolField(TEXT("sameFramePostTLAS"),Local.TLASFrameCounter==Inputs.FrameCounter && Local.TLASFrameNumber==Inputs.FrameNumber);
                J->SetStringField(TEXT("generation"),LexToString(Inputs.Selection.Generation));
                J->SetNumberField(TEXT("floorPrimitiveId"),Inputs.Selection.Floor.PrimIDValue);
                J->SetNumberField(TEXT("uniqueStencil"),Inputs.Selection.UniqueStencil);
                auto Cvars=MakeShared<FJsonObject>();for(const auto& Pair:SelectedSnapshot.Cvars)Cvars->SetNumberField(Pair.Key,Pair.Value);
                J->SetObjectField(TEXT("gameThreadCvars"),Cvars);
                TSharedPtr<FJsonObject> Source;
                if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(SelectedSnapshot.TransportSceneSnapshot),Source)||!Source.IsValid())
                { MotionCapture->Reject_RT(TEXT("Requested motion frame lacked plain source binding"));return; }
                J->SetObjectField(TEXT("transportSceneSnapshotGT"),Source);
                MotionCapture->Enqueue_RT(GraphBuilder,SelectedSnapshot.MotionIndex,J,Local.Transport,Counters);
            }
            return;
        }
        LastRTReason = TEXT("prepare submitted; composition/water not observed by this hook");
        if (bStopped.load() || bReadbackSubmitted || ObservedFrames < 60 || !Companion || Companion->Desc.Extent != FIntPoint(3840, 2160)) return;
        auto& Local = GraphBuilder.Blackboard.GetOrCreate<FDiagnosticGraph>(); if (!Local.Atlas || Local.FrameCounter != Inputs.FrameCounter) return;
        PendingMeta = BaseMeta(TEXT("gpu-readback-submitted-not-complete"));
        PendingMeta->SetArrayField(TEXT("companionPixels"), {MakeShared<FJsonValueNumber>(Companion->Desc.Extent.X), MakeShared<FJsonValueNumber>(Companion->Desc.Extent.Y)});
        PendingMeta->SetArrayField(TEXT("unscaledViewPixels"), {MakeShared<FJsonValueNumber>(View.UnscaledViewRect.Width()), MakeShared<FJsonValueNumber>(View.UnscaledViewRect.Height())});
        PendingMeta->SetNumberField(TEXT("frameCounter"), Inputs.FrameCounter); PendingMeta->SetNumberField(TEXT("frameNumber"), Inputs.FrameNumber);
        PendingMeta->SetNumberField(TEXT("worldTimeSeconds"), Inputs.WorldTimeSeconds); PendingMeta->SetNumberField(TEXT("viewPreExposure"), Inputs.ViewPreExposure);
        PendingMeta->SetNumberField(TEXT("floorPrimitiveId"), Inputs.Selection.Floor.PrimIDValue); PendingMeta->SetNumberField(TEXT("sunComponentIdHash"), GetTypeHash(Inputs.Selection.Sun));
        PendingMeta->SetStringField(TEXT("floorComponentPath"), SelectedSnapshot.FloorPath); PendingMeta->SetStringField(TEXT("sunComponentPath"), SelectedSnapshot.SunPath);
        PendingMeta->SetStringField(TEXT("worldPath"), SelectedSnapshot.WorldPath);
        PendingMeta->SetStringField(TEXT("generation"), LexToString(Inputs.Selection.Generation)); PendingMeta->SetNumberField(TEXT("uniqueStencil"), Inputs.Selection.UniqueStencil);
        PendingMeta->SetArrayField(TEXT("sourceBoundsMinCm"), Vec(Contract.Bounds.Min)); PendingMeta->SetArrayField(TEXT("sourceBoundsMaxCm"), Vec(Contract.Bounds.Max));
        PendingMeta->SetArrayField(TEXT("sunIlluminance"), Vec(FVector(Inputs.SunIlluminance))); PendingMeta->SetArrayField(TEXT("sunTravelDirection"), Vec(FVector(Inputs.SunTravelDirection)));
        if(!IsTransport()) PendingMeta->SetArrayField(TEXT("normalizedRGB"), Vec(Mode == TEXT("zero") ? FVector::ZeroVector : FVector(.125, .25, .5)));
        else
        {
            TSharedPtr<FJsonObject> PlainScene;
            Require(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(SelectedSnapshot.TransportSceneSnapshot),PlainScene)&&PlainScene.IsValid(),TEXT("Missing exact-frame source scene proof"));
            PendingMeta->SetObjectField(TEXT("transportSceneSnapshotGT"),PlainScene);
            PendingMeta->SetBoolField(TEXT("sameFramePostTLAS"),Local.TLASFrameCounter==Inputs.FrameCounter&&Local.TLASFrameNumber==Inputs.FrameNumber&&Local.TLASView==&View);
            PendingMeta->SetArrayField(TEXT("preViewTranslationCm"),Vec(View.ViewMatrices.GetPreViewTranslation()));
            const float* Phase=SelectedSnapshot.Cvars.Find(TEXT("r.Test.OverrideTimeMaterialExpressions"));
            if(Phase) PendingMeta->SetNumberField(TEXT("desiredMaterialTimeSeconds"),*Phase);
            PendingMeta->SetStringField(TEXT("desiredTimeEvidence"),TEXT("GT matched-frame CVar readback; host independently pins requested phase"));
            PhotonReadback=MakeUnique<FRHIGPUBufferReadback>(TEXT("BreziTransportPhotons")); VisibilityReadback=MakeUnique<FRHIGPUBufferReadback>(TEXT("BreziTransportVisibility"));
            TransportGatesReadback=MakeUnique<FRHIGPUBufferReadback>(TEXT("BreziTransportGates"));GPUUniformReadback=MakeUnique<FRHIGPUBufferReadback>(TEXT("BreziTransportGPUUniform"));
            AddEnqueueCopyPass(GraphBuilder,PhotonReadback.Get(),Local.Transport.Photons,BreziTransportSamples*48);
            AddEnqueueCopyPass(GraphBuilder,VisibilityReadback.Get(),Local.Transport.Visibility,BreziTransportVisibilityCount*48);
            AddEnqueueCopyPass(GraphBuilder,TransportGatesReadback.Get(),Local.Transport.Gates,4);
            AddEnqueueCopyPass(GraphBuilder,GPUUniformReadback.Get(),Local.Transport.GPUUniform,16);
        }
        auto Cvars = MakeShared<FJsonObject>(); for (const auto& Pair : SelectedSnapshot.Cvars) Cvars->SetNumberField(Pair.Key, Pair.Value); PendingMeta->SetObjectField(TEXT("gameThreadCvars"), Cvars);
        auto BatcherSnapshot = MakeShared<FJsonObject>();
        BatcherSnapshot->SetNumberField(TEXT("frameCounter"), SelectedSnapshot.FrameCounter);
        BatcherSnapshot->SetNumberField(TEXT("frameNumber"), SelectedSnapshot.FrameNumber);
        BatcherSnapshot->SetStringField(TEXT("worldPath"), SelectedSnapshot.WorldPath);
        TArray<TSharedPtr<FJsonValue>> BatcherRows;
        for (const FLineBatcherIdentity& Row : SelectedSnapshot.LineBatchers)
        {
            auto J = MakeShared<FJsonObject>(); J->SetStringField(TEXT("type"), Row.Type); J->SetBoolField(TEXT("present"), Row.bPresent);
            if (Row.bPresent)
            {
                J->SetStringField(TEXT("componentPath"), Row.ComponentPath); J->SetStringField(TEXT("classPath"), Row.ClassPath);
                J->SetNumberField(TEXT("primitiveId"), Row.PrimitiveId); J->SetBoolField(TEXT("primitiveIdValid"), Row.bPrimitiveIdValid);
                J->SetBoolField(TEXT("registered"), Row.bRegistered); J->SetBoolField(TEXT("calculateAccurateBounds"), Row.bAccurateBounds);
                J->SetNumberField(TEXT("lineCount"), Row.Lines); J->SetNumberField(TEXT("pointCount"), Row.Points); J->SetNumberField(TEXT("meshCount"), Row.Meshes);
            }
            BatcherRows.Add(MakeShared<FJsonValueObject>(J));
        }
        BatcherSnapshot->SetArrayField(TEXT("rows"), BatcherRows);
        PendingMeta->SetObjectField(TEXT("lineBatcherSnapshotGT"), BatcherSnapshot);
        TArray<TSharedPtr<FJsonValue>> Exclusions;
        for (int32 I = 0; I < Inputs.ConservativeExcludedPrimitives.Num(); ++I)
        {
            auto J = MakeShared<FJsonObject>(); J->SetNumberField(TEXT("primitiveId"), Inputs.ConservativeExcludedPrimitives[I].PrimIDValue);
            const auto R = Inputs.ConservativeExcludedBoundsXYCm[I];
            J->SetArrayField(TEXT("boundsXYCm"), {MakeShared<FJsonValueNumber>(R.X), MakeShared<FJsonValueNumber>(R.Y), MakeShared<FJsonValueNumber>(R.Z), MakeShared<FJsonValueNumber>(R.W)});
            Exclusions.Add(MakeShared<FJsonValueObject>(J));
        }
        PendingMeta->SetArrayField(TEXT("rendererConservativeExclusions"), Exclusions);
        CounterReadback = MakeUnique<FRHIGPUBufferReadback>(TEXT("BreziFloorDiagnosticCounters"));
        AtlasReadback = MakeUnique<FRHIGPUTextureReadback>(TEXT("BreziFloorDiagnosticAtlas"));
        CompanionReadback = MakeUnique<FRHIGPUTextureReadback>(TEXT("BreziFloorDiagnosticCompanion"));
        AddEnqueueCopyPass(GraphBuilder, CounterReadback.Get(), Counters, 16);
        AddEnqueueCopyPass(GraphBuilder, AtlasReadback.Get(), Local.Atlas);
        AddEnqueueCopyPass(GraphBuilder, CompanionReadback.Get(), Companion); bReadbackSubmitted = true;
    }
    void ObserveDownstream_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FFloorCausticsObservation& O) override
    {
        check(IsInRenderingThread());
        if(bContinuous)
        {
            if(MotionCapture && !bStopped.load() && View.Family && O.Stage==EFloorCausticsObservationStage::AfterComposite)
            {
                const auto* I=O.PreparedInputs;
                const bool Paired=I && I->FrameCounter==View.Family->FrameCounter && I->FrameNumber==View.Family->FrameNumber
                    && I->Selection.SceneToken==View.Family->Scene && I->Selection.Generation==Generation && O.Companion;
                MotionCapture->Composite_RT(View.Family->FrameCounter,View.Family->FrameNumber,O.bComposited && Paired);
            }
            return;
        }
        if (bStopped.load() || bDownstreamComplete || !View.Family || !DownstreamError.IsEmpty()) return;
        const int32 Stage = int32(O.Stage); if (Stage < 0 || Stage >= 4) { DownstreamError = TEXT("Unknown observation stage"); return; }
        if (bDownstreamStarted && (View.Family->FrameCounter != DownstreamFrameCounter || View.Family->FrameNumber != DownstreamFrameNumber)) return;
        FSnapshot Snapshot;
        { FScopeLock Lock(&SnapshotMutex); const auto* Found = Snapshots.Find(View.Family->FrameCounter);
          if (!Found || !Found->bValid || Found->FrameNumber != View.Family->FrameNumber || Found->Selection.SceneToken != View.Family->Scene) return;
          Snapshot = *Found; }
        const bool Inactive = Mode == TEXT("inactive"); const float* Enabled = Snapshot.Cvars.Find(TEXT("r.Brezi.FloorCaustics"));
        const bool Formats = O.SceneColor && O.SceneDepth && O.SceneColor->HasBeenProduced() && O.SceneDepth->HasBeenProduced()
            && O.SceneColor->Desc.Format == PF_FloatRGBA && O.SceneColor->Desc.NumSamples == 1 && O.SceneDepth->Desc.NumSamples == 1
            && O.SceneColor->Desc.Extent == FIntPoint(3840, 2160) && O.SceneDepth->Desc.Extent == FIntPoint(3840, 2160)
            && EnumHasAllFlags(O.SceneDepth->Desc.Flags, TexCreate_ShaderResource)
            && View.UnscaledViewRect == FIntRect(0, 0, 3840, 2160);
        if (!Enabled || *Enabled != (Inactive ? 0.0f : 1.0f) || !Formats)
        { if (bDownstreamStarted) DownstreamError = TEXT("Mid-frame CVar/format/view dimensions changed"); return; }
        if (!bDownstreamStarted)
        {
            if (Stage != 0) return;
            if (Inactive) { if (++InactiveEligibleFrames < 60) return; }
            else if (!bReadbackSubmitted || !PendingMeta || uint64(PendingMeta->GetNumberField(TEXT("frameCounter"))) != View.Family->FrameCounter) return;
            bDownstreamStarted = true; DownstreamFrameCounter = View.Family->FrameCounter; DownstreamFrameNumber = View.Family->FrameNumber;
            DownstreamMeta = BaseMeta(TEXT("gpu-four-stage-readback-incomplete"));
            DownstreamMeta->SetNumberField(TEXT("frameCounter"), DownstreamFrameCounter); DownstreamMeta->SetNumberField(TEXT("frameNumber"), DownstreamFrameNumber);
            DownstreamMeta->SetStringField(TEXT("worldPath"), Snapshot.WorldPath); DownstreamMeta->SetStringField(TEXT("floorComponentPath"), Snapshot.FloorPath);
            DownstreamMeta->SetStringField(TEXT("sunComponentPath"), Snapshot.SunPath); DownstreamMeta->SetStringField(TEXT("generation"), LexToString(Snapshot.Selection.Generation));
            DownstreamMeta->SetNumberField(TEXT("floorPrimitiveId"), Snapshot.Selection.Floor.PrimIDValue); DownstreamMeta->SetNumberField(TEXT("sunComponentIdHash"), GetTypeHash(Snapshot.Selection.Sun));
            DownstreamMeta->SetNumberField(TEXT("uniqueStencil"), Snapshot.Selection.UniqueStencil);
            auto Cvars = MakeShared<FJsonObject>(); for (const auto& P : Snapshot.Cvars) Cvars->SetNumberField(P.Key, P.Value); DownstreamMeta->SetObjectField(TEXT("gameThreadCvars"), Cvars);
            DownstreamMeta->SetStringField(TEXT("sceneColorEncoding"), TEXT("native pre-exposed linear RGBA16F; no display conversion"));
            DownstreamMeta->SetStringField(TEXT("depthEncoding"), TEXT("native device Z via exact texel Load to PF_R32_FLOAT; no distance linearization"));
            DownstreamMeta->SetBoolField(TEXT("singleBeerApplicationProven"), false);
            DownstreamMeta->SetStringField(TEXT("preExposureEvidence"), TEXT("Renderer FViewInfo::PreExposure CPU value; effective shader uniform is not independently read back"));
        }
        if (Stage != NextStage) { DownstreamError = TEXT("Missing, duplicate or reordered downstream stage"); return; }
        const auto* Inputs = O.PreparedInputs;
        const bool ExpectedComposite = !Inactive && Stage >= 2;
        if (O.bComposited != ExpectedComposite || (Inactive ? (Inputs || O.Companion) : (!Inputs || !O.Companion)))
        { DownstreamError = TEXT("Prepared/composite state differs from explicit control mode"); return; }
        if (Inputs && (Inputs->FrameCounter != DownstreamFrameCounter || Inputs->FrameNumber != DownstreamFrameNumber
            || Inputs->Selection.SceneToken != Snapshot.Selection.SceneToken || Inputs->Selection.Generation != Snapshot.Selection.Generation
            || Inputs->Selection.Floor != Snapshot.Selection.Floor || !(Inputs->Selection.Sun == Snapshot.Selection.Sun)
            || Inputs->Selection.UniqueStencil != Snapshot.Selection.UniqueStencil))
        { DownstreamError = TEXT("Prepared inputs differ from this frame/source selection"); return; }
        if (O.Companion && (O.Companion->Desc.Format != PF_FloatRGBA || O.Companion->Desc.NumSamples != 1
            || O.Companion->Desc.Extent != FIntPoint(3840, 2160) || !O.Companion->HasBeenProduced()))
        { DownstreamError = TEXT("Invalid companion readback format"); return; }
        auto& S = Stages[Stage]; S.Meta = MakeShared<FJsonObject>();
        S.Meta->SetStringField(TEXT("stage"), StageName(Stage)); S.Meta->SetNumberField(TEXT("frameCounter"), View.Family->FrameCounter);
        S.Meta->SetNumberField(TEXT("frameNumber"), View.Family->FrameNumber); S.Meta->SetNumberField(TEXT("worldTimeSeconds"), View.Family->Time.GetWorldTimeSeconds());
        S.Meta->SetNumberField(TEXT("viewPreExposure"), O.ViewPreExposure); S.Meta->SetBoolField(TEXT("preparedInputsPresent"), Inputs != nullptr);
        S.Meta->SetBoolField(TEXT("bComposited"), O.bComposited); S.Meta->SetNumberField(TEXT("nativeSceneDepthFormat"), int32(O.SceneDepth->Desc.Format));
        S.Meta->SetNumberField(TEXT("nativeSceneColorFormat"), int32(O.SceneColor->Desc.Format));
        S.Meta->SetArrayField(TEXT("pixels"), {MakeShared<FJsonValueNumber>(3840), MakeShared<FJsonValueNumber>(2160)});
        S.Meta->SetArrayField(TEXT("viewOriginCm"), Vec(View.ViewMatrices.GetViewOrigin()));
        TArray<TSharedPtr<FJsonValue>> Matrix;
        const auto& ViewProjection = View.ViewMatrices.GetWorldToClip();
        for (int32 R = 0; R < 4; ++R) for (int32 C = 0; C < 4; ++C) Matrix.Add(MakeShared<FJsonValueNumber>(ViewProjection.M[R][C]));
        S.Meta->SetArrayField(TEXT("viewProjectionMatrixRows"), Matrix);
        if (Inputs)
        {
            S.Meta->SetNumberField(TEXT("preparedWorldTimeSeconds"), Inputs->WorldTimeSeconds);
            S.Meta->SetArrayField(TEXT("sunIlluminance"), Vec(FVector(Inputs->SunIlluminance)));
            S.Meta->SetArrayField(TEXT("sunTravelDirection"), Vec(FVector(Inputs->SunTravelDirection)));
        }
        const FString Prefix = FString::Printf(TEXT("BreziFloorStage%d"), Stage);
        S.Color = MakeUnique<FRHIGPUTextureReadback>(FName(*(Prefix + TEXT("Color"))));
        S.Depth = MakeUnique<FRHIGPUTextureReadback>(FName(*(Prefix + TEXT("Depth"))));
        AddEnqueueCopyPass(GraphBuilder, S.Color.Get(), O.SceneColor);
        // Stock helper performs Texture2D.Load into R32F, avoiding depth/stencil byte-layout assumptions.
        FRDGTextureRef DepthCopy = GraphBuilder.CreateTexture(FRDGTextureDesc::Create2D(FIntPoint(3840, 2160), PF_R32_FLOAT,
            FClearValueBinding::None, TexCreate_ShaderResource | TexCreate_RenderTargetable), TEXT("Brezi.FloorDiagnosticDeviceZ"));
        FRDGDrawTextureInfo DrawInfo; DrawInfo.Size = FIntPoint(3840, 2160);
        AddDrawTexturePass(GraphBuilder, GetGlobalShaderMap(View.GetFeatureLevel()), O.SceneDepth, DepthCopy, DrawInfo);
        AddEnqueueCopyPass(GraphBuilder, S.Depth.Get(), DepthCopy);
        if (O.Companion)
        {
            S.Companion = MakeUnique<FRHIGPUTextureReadback>(FName(*(Prefix + TEXT("Companion"))));
            AddEnqueueCopyPass(GraphBuilder, S.Companion.Get(), O.Companion);
        }
        S.bSubmitted = true; ++NextStage;
    }
    void Drain_RT(FRHICommandListImmediate& RHICmdList)
    {
        if(MotionCapture) MotionCapture->Drain_RT(RHICmdList);
        // Diagnostic shutdown only: CPU flush alone is not proof that GPU readback fences completed.
        if ((bReadbackSubmitted && !bReadbackComplete) || (bDownstreamStarted && !bDownstreamComplete))
        { RHICmdList.SubmitAndBlockUntilGPUIdle(); PollReadback_RT(); PollDownstream_RT(); }
        for (auto& S : Stages) { S.Color.Reset(); S.Depth.Reset(); S.Companion.Reset(); }
        CounterReadback.Reset(); AtlasReadback.Reset(); CompanionReadback.Reset();
        PhotonReadback.Reset();VisibilityReadback.Reset();TransportGatesReadback.Reset();GPUUniformReadback.Reset();Transport.Reset();
    }
    void RestoreAndRecord_GT()
    {
        check(IsInGameThread());
        if (bOwned && OwnedFloor.IsValid())
        {
            auto* Floor = OwnedFloor.Get();
            if (Floor->bRenderCustomDepth && Floor->CustomDepthStencilValue == Stencil && Floor->CustomDepthStencilWriteMask == ERendererStencilMask::ERSM_255)
            {
                Floor->SetRenderCustomDepth(PriorCustomDepth); Floor->SetCustomDepthStencilValue(PriorStencil); Floor->SetCustomDepthStencilWriteMask(PriorMask);
                bRestored = Floor->bRenderCustomDepth == PriorCustomDepth && Floor->CustomDepthStencilValue == PriorStencil && Floor->CustomDepthStencilWriteMask == PriorMask;
            }
            else LastGTReason = TEXT("Restoration refused: another owner changed the scoped stencil state");
        }
        auto J = BaseMeta(TEXT("stopped")); J->SetBoolField(TEXT("registrationSucceeded"), bRegistered.load()); J->SetBoolField(TEXT("unregisterCommandDrained"), true);
        J->SetBoolField(TEXT("ownershipAcquired"), bOwned); J->SetBoolField(TEXT("originalStencilRestored"), bRestored);
        J->SetBoolField(TEXT("floorAlreadyDestroyed"), bOwned && !OwnedFloor.IsValid());
        J->SetNumberField(TEXT("priorStencil"), PriorStencil); J->SetNumberField(TEXT("priorMask"), int32(PriorMask)); J->SetBoolField(TEXT("priorCustomDepth"), PriorCustomDepth);
        J->SetNumberField(TEXT("selectionCalls"), SelectCalls); J->SetNumberField(TEXT("builtFrames"), BuiltFrames); J->SetNumberField(TEXT("observedFrames"), ObservedFrames);
        J->SetNumberField(TEXT("rejectedFrames"), RejectedFrames); J->SetBoolField(TEXT("readbackSubmitted"), bReadbackSubmitted); J->SetBoolField(TEXT("readbackComplete"), bReadbackComplete);
        J->SetBoolField(TEXT("downstreamStarted"), bDownstreamStarted); J->SetBoolField(TEXT("downstreamComplete"), bDownstreamComplete);
        J->SetNumberField(TEXT("downstreamSubmittedStages"), NextStage); J->SetStringField(TEXT("downstreamError"), DownstreamError);
        if(IsTransport()) { J->SetBoolField(TEXT("sceneBindingAttempted"),bSceneBindingAttempted);J->SetBoolField(TEXT("sceneBindingPassed"),SceneBinding.bBound);J->SetStringField(TEXT("sceneBindingError"),SceneBindingError); }
        if(bContinuous) { J->SetNumberField(TEXT("unsupportedContinuousFrames"),UnsupportedContinuousFrames);
            J->SetBoolField(TEXT("cookedPackageRequired"),FPlatformProperties::RequiresCookedData());
            J->SetBoolField(TEXT("cookedPackageVerified"),CookedBinding.IsVerified());J->SetBoolField(TEXT("cookedVerificationPendingAtStop"),bCookedVerificationPending);
            J->SetStringField(TEXT("cookedVerificationError"),CookedVerificationError);J->SetStringField(TEXT("cookedReceiptSha1"),CookedBinding.ReceiptSha1());
            if(MotionCapture) MotionCapture->AddLifecycle_GT(J); }
        J->SetStringField(TEXT("lastGTReason"), LastGTReason); J->SetStringField(TEXT("lastRTReason"), LastRTReason);
        SaveJson(Directory, TEXT("lifecycle.json"), J);
    }
};

class FDiagnosticOwner final : public IBreziFloorCausticsDiagnostic
{
    TSharedPtr<FDiagnosticExtension, ESPMode::ThreadSafe> Extension;
    FDelegateHandle Cleanup;
public:
    FDiagnosticOwner(FContract Contract, FString Mode)
    {
        Extension = FSceneViewExtensions::NewExtension<FDiagnosticExtension>(MoveTemp(Contract), MoveTemp(Mode));
        auto Strong = Extension.ToSharedRef();
        ENQUEUE_RENDER_COMMAND(BreziRegisterFloorDiagnostic)([Strong](FRHICommandListImmediate&)
        { Strong->bRegistered.store(RegisterFloorCausticsProvider_RenderThread(StaticCastSharedRef<IFloorCausticsProvider>(Strong))); });
        Cleanup = FWorldDelegates::OnWorldCleanup.AddLambda([this](UWorld* World, bool, bool) { if (Extension && Extension->OwnsWorld(World)) Stop(); });
    }
    ~FDiagnosticOwner() override { Stop(); }
    void Stop() override
    {
        check(IsInGameThread()); FWorldDelegates::OnWorldCleanup.Remove(Cleanup); Cleanup.Reset();
        if (!Extension) return;
        Extension->bStopped.store(true); auto Strong = Extension.ToSharedRef();
        ENQUEUE_RENDER_COMMAND(BreziUnregisterFloorDiagnostic)([Strong](FRHICommandListImmediate& RHICmdList)
        { UnregisterFloorCausticsProvider_RenderThread(&Strong.Get()); Strong->Drain_RT(RHICmdList); });
        FlushRenderingCommands(); Strong->RestoreAndRecord_GT(); Extension.Reset();
    }
};
}
#endif

TUniquePtr<IBreziFloorCausticsDiagnostic> CreateBreziFloorCausticsDiagnostic(const FString& ContractPath, const FString& Mode)
{
#if BREZI_HAS_FLOOR_CAUSTICS_API
    Require(Mode == TEXT("inactive") || Mode == TEXT("zero") || Mode == TEXT("constant") || Mode == TEXT("transport-opaque") || Mode == TEXT("transport-continuous"), TEXT("Unsupported explicit floor provider mode"));
    const bool bContinuous=Mode==TEXT("transport-continuous"), bTransport=bContinuous || Mode==TEXT("transport-opaque");
    const FString Path=bTransport?FPaths::Combine(FPaths::GetPath(ContractPath),bContinuous?TEXT("delivery-provider.json"):TEXT("transport-provider.json")):ContractPath;
    return MakeUnique<FDiagnosticOwner>(LoadContract(Path,bTransport,bContinuous),Mode);
#else
    UE_LOG(LogBreziFloorDiagnostic, Error, TEXT("Requested floor diagnostic unavailable: this engine has no exact reviewed FloorCaustics provider API. No provider registered."));
    return nullptr;
#endif
}
