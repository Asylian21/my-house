#include "BreziPlayerController.h"
#include "BreziGameViewportClient.h"
#include "BreziDoubleGlassActor.h"
#include "BreziExteriorLighting.h"
#include "Components/RectLightComponent.h"
#include "Engine/Engine.h"
#include "Engine/RectLight.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "RenderUtils.h"
#include "RHI.h"
#include "SceneView.h"
#include "SceneViewExtension.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#endif

#define LOCTEXT_NAMESPACE "BreziTwin"
using BreziRenderQuality::Profile;
using BreziRenderQuality::Origin;
namespace
{
using namespace BreziRenderQuality;
constexpr const TCHAR* ProfileSection = TEXT("Brezi.RenderQuality");
constexpr const TCHAR* ProfileKey = TEXT("ProfileV1");
constexpr EConsoleVariableFlags UserPriority = ECVF_SetByGameOverride;

bool VerifyProfileSave(const FConfigFile* Defaults, const FString& SavedPath, bool bFlushed,
    const TCHAR* Expected, bool& bRead)
{
    bRead = false;
    if (!Defaults || !bFlushed || SavedPath.IsEmpty() || IFileManager::Get().DirectoryExists(*SavedPath)) return false;
    const bool bExists = IFileManager::Get().FileExists(*SavedPath);
    FString Contents, Persisted;
    bRead = bExists && FFileHelper::LoadFileToString(Contents, *SavedPath);
    if (bExists && !bRead) return false;

    // UE5.8 saves a delta against FinalCombinedLayers, and can delete an empty
    // delta. Reconstruct what the next launch reads, never trust InMemoryFile.
    // The UE5.8 copy constructor leaves its private ChangeTracker null; detach
    // the public Branch pointer too, so parsing cannot mutate the live config.
    FConfigFile Disk = *Defaults;
    Disk.Branch = nullptr;
    if (bRead) Disk.CombineFromBuffer(Contents, SavedPath);
    return Disk.GetString(ProfileSection, ProfileKey, Persisted) && Persisted == Expected;
}

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBreziRenderQualityPersistenceTest,
    "BreziTwin.RenderQuality.Persistence", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FBreziRenderQualityPersistenceTest::RunTest(const FString&)
{
    // FConfigBranch's constructor is not exported by the installed engine;
    // exercise the same exported FConfigFile parser used by the live branch.
    FConfigFile Defaults;
    const FString TestPath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Automation"),
        FString::Printf(TEXT("BreziProfileSave-%s.ini"), *FGuid::NewGuid().ToString()));
    if (!IFileManager::Get().MakeDirectory(*FPaths::GetPath(TestPath), true)) return false;
    Defaults.SetString(ProfileSection, ProfileKey, TEXT("performance"));
    Defaults.SetString(TEXT("OtherPreferences"), TEXT("MouseSensitivity"), TEXT("2.5"));
    bool bRead = false;
    auto Verify = [&](const TCHAR* Expected, bool bFlushed = true)
    { return VerifyProfileSave(&Defaults, TestPath, bFlushed, Expected, bRead); };
    auto Write = [&](const TCHAR* Contents)
    { TestTrue(TEXT("Fixture written"), FFileHelper::SaveStringToFile(Contents, *TestPath)); };
    Write(TEXT(";METADATA=(Diff=true, UseCommands=true)\n[OtherPreferences]\nMouseSensitivity=3.0\n"));
    TestTrue(TEXT("Default Performance survives omitted delta key"), Verify(TEXT("performance")));
    TestTrue(TEXT("Disk was independently read"), bRead);
    TestFalse(TEXT("Elided key cannot pretend to restore Native"), Verify(TEXT("native")));
    Write(TEXT("[Brezi.RenderQuality]\nProfileV1=balanced\n"));
    TestTrue(TEXT("Explicit Balanced restores"), Verify(TEXT("balanced")));
    TestFalse(TEXT("Stale Balanced disk defeats requested Native"), Verify(TEXT("native")));
    TestFalse(TEXT("Stale Balanced disk defeats default Performance"), Verify(TEXT("performance")));
    Write(TEXT("[Brezi.RenderQuality]\nProfileV1=native\n"));
    TestTrue(TEXT("Explicit Native restores"), Verify(TEXT("native")));
    TestFalse(TEXT("Failed flush never reports success even with matching disk"), Verify(TEXT("native"), false));
    Write(TEXT("[Brezi.RenderQuality]\n!ProfileV1=ClearArray\n"));
    TestFalse(TEXT("Delta removal command is not an omitted default"), Verify(TEXT("performance")));
    Write(TEXT(""));
    TestTrue(TEXT("Empty delta restores Performance"), Verify(TEXT("performance")));
    IFileManager::Get().Delete(*TestPath);
    TestTrue(TEXT("Absent empty delta restores Performance"), Verify(TEXT("performance")));
    TestFalse(TEXT("Absent file does not restore a nondefault selection"), Verify(TEXT("balanced")));
    TestFalse(TEXT("Failed flush cannot use the default as proof"), Verify(TEXT("performance"), false));
    TestTrue(TEXT("Unreadable-file fixture directory created"), IFileManager::Get().MakeDirectory(*TestPath));
    TestFalse(TEXT("A directory at the saved path is not an absent delta"), Verify(TEXT("performance")));
    IFileManager::Get().DeleteDirectory(*TestPath);
    FString Unchanged;
    TestTrue(TEXT("Live defaults remain unchanged"), Defaults.GetString(
        TEXT("OtherPreferences"), TEXT("MouseSensitivity"), Unchanged) && Unchanged == TEXT("2.5"));
    return true;
}
#endif

TAutoConsoleVariable<int32> LocalLightShadows(TEXT("r.Brezi.LocalLightShadows"), 1,
    TEXT("Allow authored interior/exterior local-light shadows. Profiles preserve the sun's shadows."));
TAutoConsoleVariable<float> FinalGather(TEXT("r.Brezi.Lumen.FinalGatherQuality"), -1,
    TEXT("Main-view Lumen final gather budget; negative preserves authored postprocess settings."));
TAutoConsoleVariable<float> Reflections(TEXT("r.Brezi.Lumen.ReflectionQuality"), -1,
    TEXT("Main-view Lumen reflection budget; negative preserves authored postprocess settings."));
TAutoConsoleVariable<float> SceneLighting(TEXT("r.Brezi.Lumen.SceneLightingQuality"), -1,
    TEXT("Main-view Lumen scene lighting budget; negative preserves authored postprocess settings."));
TAutoConsoleVariable<float> SceneDetail(TEXT("r.Brezi.Lumen.SceneDetail"), -1,
    TEXT("Main-view Lumen scene detail budget; negative preserves authored postprocess settings."));
TAutoConsoleVariable<float> SceneDistance(TEXT("r.Brezi.Lumen.SceneViewDistance"), -1,
    TEXT("Main-view Lumen scene distance in cm; negative preserves authored postprocess settings."));
TAutoConsoleVariable<float> TraceDistance(TEXT("r.Brezi.Lumen.MaxTraceDistance"), -1,
    TEXT("Main-view Lumen trace distance in cm; negative preserves authored postprocess settings."));

bool HardwareLumenSupported()
{
    // Query the initialized RHI, not a device-name/M-series guess. Keep software
    // distance fields cooked so unsupported Apple GPUs have the software path.
    return IsRayTracingEnabled() && GRHISupportsRayTracing
        && (GRHISupportsInlineRayTracing || GRHISupportsRayTracingShaders);
}

template<typename Visitor> void VisitSettings(Profile Value, Visitor&& Visit)
{
    const Settings S = Values(Value);
    Visit(TEXT("sg.GlobalIlluminationQuality"), float(S.GlobalIllumination));
    Visit(TEXT("sg.ShadowQuality"), float(S.Shadows));
    Visit(TEXT("sg.ReflectionQuality"), float(S.Reflections));
    Visit(TEXT("sg.FoliageQuality"), float(S.Foliage));
    Visit(TEXT("sg.PostProcessQuality"), float(S.PostProcess));
    Visit(TEXT("sg.EffectsQuality"), float(S.Effects));
    // Set direct budgets after scalability callbacks (foliage scalability also
    // writes DensityScale). Never change their priority flags by hand.
    Visit(TEXT("r.ScreenPercentage"), float(S.ScreenPercentage));
    Visit(TEXT("r.TSR.History.ScreenPercentage"), float(S.HistoryPercentage));
    Visit(TEXT("r.Brezi.Lumen.FinalGatherQuality"), S.FinalGather);
    Visit(TEXT("r.Brezi.Lumen.ReflectionQuality"), S.ReflectionQuality);
    Visit(TEXT("r.Brezi.Lumen.SceneLightingQuality"), S.SceneLighting);
    Visit(TEXT("r.Brezi.Lumen.SceneDetail"), S.SceneDetail);
    Visit(TEXT("r.Brezi.Lumen.SceneViewDistance"), S.SceneDistanceCm);
    Visit(TEXT("r.Brezi.Lumen.MaxTraceDistance"), S.TraceDistanceCm);
    Visit(TEXT("r.Brezi.DoubleGlass"), float(S.DoubleGlass));
    Visit(TEXT("r.Brezi.LocalLightShadows"), float(S.LocalLightShadows));
    Visit(TEXT("foliage.DensityScale"), S.FoliageDensity);
}

bool Writable(const IConsoleVariable* Variable)
{
    return Variable && (Variable->GetFlags() & (ECVF_ReadOnly | ECVF_Unregistered)) == 0
        && (Variable->GetFlags() & ECVF_SetByMask) <= UserPriority;
}

class FRenderQualityView final : public FWorldSceneViewExtension
{
public:
    FRenderQualityView(const FAutoRegister& AutoRegister, UWorld* World) : FWorldSceneViewExtension(AutoRegister, World) {}
    virtual void SetupView(FSceneViewFamily&, FSceneView& View) override
    {
        check(IsInGameThread());
        if (View.bIsSceneCapture || View.bIsReflectionCapture) return;
        // UE5.8 LocalPlayer invokes this after EndFinalPostprocessSettings. The
        // effective main-view budget therefore wins over imported unbound volumes
        // without modifying saved map assets, exposure, materials or geometry.
        auto& PP = View.FinalPostProcessSettings;
        const auto Override = [](float& Target, const TAutoConsoleVariable<float>& Variable, float Minimum, float Maximum)
        {
            const float Value = Variable.GetValueOnGameThread();
            if (FMath::IsFinite(Value) && Value >= 0) Target = FMath::Clamp(Value, Minimum, Maximum);
        };
        Override(PP.LumenFinalGatherQuality, FinalGather, .25f, 4.f);
        Override(PP.LumenReflectionQuality, Reflections, .25f, 4.f);
        Override(PP.LumenSceneLightingQuality, SceneLighting, .25f, 4.f);
        Override(PP.LumenSceneDetail, SceneDetail, .25f, 4.f);
        Override(PP.LumenSceneViewDistance, SceneDistance, 100.f, 30000.f);
        Override(PP.LumenMaxTraceDistance, TraceDistance, 100.f, 30000.f);
    }
};
IConsoleVariable* ScreenVariable() { return IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage")); }
IConsoleVariable* HistoryVariable() { return IConsoleManager::Get().FindConsoleVariable(TEXT("r.TSR.History.ScreenPercentage")); }
const TCHAR* ProfileName(Profile Value)
{
    return Value == Profile::Native ? TEXT("native") : Value == Profile::Balanced ? TEXT("balanced")
        : Value == Profile::Performance ? TEXT("performance") : TEXT("unknown");
}
Profile ParseProfile(const FString& Value)
{
    for (Profile Item : {Profile::Native, Profile::Balanced, Profile::Performance})
        if (Value == ProfileName(Item)) return Item;
    return Profile::Unknown;
}
bool HasDiagnosticArguments(const TCHAR* CLI)
{
    for (const TCHAR* Name : {TEXT("BreziCapture4K"), TEXT("BreziCaptureScene"), TEXT("BreziCaptureUI"), TEXT("BreziExitAfterCapture"),
        TEXT("BreziMotionQA"), TEXT("BreziRealtimeOrbit"), TEXT("BreziRealtimeWalk"), TEXT("BreziCausticsMotionQA"), TEXT("BreziWalk"), TEXT("BreziWalkAudit"),
        TEXT("BreziProfileGPU"), TEXT("BreziCausticsProbe"), TEXT("BreziSolarVisibilityProbe"),
        TEXT("BreziAXInitStress"), TEXT("BreziAXShutdownStress"), TEXT("BreziSkipNativeAccessibility"),
        TEXT("BreziSkipAXFocusForwarding"), TEXT("BreziSolarVisibilityCapture"), TEXT("BreziCausticsCapture"), TEXT("benchmark")})
        if (FParse::Param(CLI, Name)) return true;
    FString Ignored;
    for (const TCHAR* Name : {TEXT("BreziBenchmarkFrames="), TEXT("BreziBenchmarkSeconds="), TEXT("BreziWalkTraversal="),
        TEXT("BreziFlameStudyScale="), TEXT("BreziFlameStudyContract="), TEXT("BreziFlameShape="),
        TEXT("BreziWarmupFrames="), TEXT("BreziFloorCausticsDiagnostic=")})
        if (FParse::Value(CLI, Name, Ignored)) return true;
    return false;
}
bool HasRawRenderArguments(const TCHAR* CLI)
{
    // This also catches quoted/deferred ExecCmds and -ini overrides before the first engine tick.
    const FString Arguments(CLI);
    for (const TCHAR* Name : {TEXT("r.ScreenPercentage"), TEXT("r.TSR.History.ScreenPercentage"),
        TEXT("r.AntiAliasingMethod"), TEXT("r.DynamicRes.OperationMode"), TEXT("r.SecondaryScreenPercentage.GameViewport")})
        if (Arguments.Contains(Name, ESearchCase::IgnoreCase)) return true;
    return false;
}
}

void ABreziPlayerController::InitializeRenderQuality()
{
    RenderQualityView = FSceneViewExtensions::NewExtension<FRenderQualityView>(GetWorld());
    // The imported room lights are stable; retain their authored shadow flags and
    // weak references once, then only revisit them when the shadow policy changes.
    for (TActorIterator<ARectLight> It(GetWorld()); It; ++It)
        if (URectLightComponent* Light = Cast<URectLightComponent>(It->GetLightComponent()))
            if (It->ActorHasTag(TEXT("BreziArchvizInteriorLighting")))
            {
                RenderQualityRoomLights.Add(Light);
                RenderQualityRoomLightShadows.Add(Light->CastShadows);
            }
    const TCHAR* CLI = FCommandLine::Get();
    FString Named, Saved;
    const bool bNamed = FParse::Value(CLI, TEXT("BreziRenderProfile="), Named)
        || FParse::Param(CLI, TEXT("BreziRenderProfile"))
        || FString(CLI).Contains(TEXT("-BreziRenderProfile="), ESearchCase::IgnoreCase);
    const bool bDiagnostic = GIsEditor || IsRunningCommandlet() || HasDiagnosticArguments(CLI);
    const bool bRawOverride = HasRawRenderArguments(CLI);
    if (!bDiagnostic && !bRawOverride && GConfig && !GGameUserSettingsIni.IsEmpty())
        GConfig->GetString(ProfileSection, ProfileKey, Saved, GGameUserSettingsIni);
    const auto Decision = BreziRenderQuality::Startup(bDiagnostic, bRawOverride, bNamed,
        ParseProfile(Named), ParseProfile(Saved), CanChangeRenderQuality(), HardwareLumenSupported());
    RenderQualityOrigin = Decision.Source;
    // A named diagnostic recipe applies once before locking the UI/persistence.
    if (Decision.Apply) ApplyRenderQuality(Decision.Requested, false);
    else TraceRenderQuality(TEXT("launch-locked"), Profile::Unknown,
        ScreenVariable() ? ScreenVariable()->GetFloat() : -1, HistoryVariable() ? HistoryVariable()->GetFloat() : -1, false);
    bRenderQualityLocked = Decision.Locked;
}

bool ABreziPlayerController::CanChangeRenderQuality() const
{
    const IConsoleVariable* Screen = ScreenVariable();
    const IConsoleVariable* History = HistoryVariable();
    const auto* AA = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod"));
    const auto* Dynamic = IConsoleManager::Get().FindConsoleVariable(TEXT("r.DynamicRes.OperationMode"));
    const auto* Secondary = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SecondaryScreenPercentage.GameViewport"));
    if (!Screen || !History || !AA || !Dynamic || !Secondary) return false;
    bool bWritable = true;
    VisitSettings(Profile::Balanced, [&bWritable](const TCHAR* Name, float)
    {
        bWritable &= Writable(IConsoleManager::Get().FindConsoleVariable(Name));
    });
    return BreziRenderQuality::CanApply(bRenderQualityLocked, bWritable,
        Screen->GetFlags() & ECVF_SetByMask, History->GetFlags() & ECVF_SetByMask, UserPriority,
        AA->GetInt(), Dynamic->GetInt(), Secondary->GetFloat());
}

bool ABreziPlayerController::IsRenderQualitySelected(BreziRenderQuality::Profile Value) const
{
    const auto* AA = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod"));
    const auto* Dynamic = IConsoleManager::Get().FindConsoleVariable(TEXT("r.DynamicRes.OperationMode"));
    const auto* Secondary = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SecondaryScreenPercentage.GameViewport"));
    if (!BreziRenderQuality::IsValid(Value) || !AA || !Dynamic || !Secondary
        || !BreziRenderQuality::CompatiblePipeline(AA->GetInt(), Dynamic->GetInt(), Secondary->GetFloat())) return false;
    bool bMatches = true;
    VisitSettings(Value, [&bMatches](const TCHAR* Name, float Expected)
    {
        const IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(Name);
        bMatches &= Variable && FMath::IsNearlyEqual(Variable->GetFloat(), Expected);
    });
    return bMatches;
}

bool ABreziPlayerController::ApplyRenderQuality(BreziRenderQuality::Profile Value, bool bDeliberateSelection)
{
    if (!BreziRenderQuality::IsValid(Value) || !CanChangeRenderQuality()) return false;
    IConsoleVariable* Screen = ScreenVariable();
    IConsoleVariable* History = HistoryVariable();
    const float PriorScreen = Screen->GetFloat(), PriorHistory = History->GetFloat();
    // User override is stronger than project/device defaults and weaker than CLI/console.
    // Do not use SetByCode/Console or rewrite priority bits to defeat an external override.
    VisitSettings(Value, [](const TCHAR* Name, float Expected)
    {
        IConsoleManager::Get().FindConsoleVariable(Name)->Set(Expected, UserPriority);
    });
    // Hardware tracing is a capability preference. A stronger explicit CLI/console
    // choice (including software-Lumen QA) is permitted and never overwritten.
    IConsoleVariable* Hardware = IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.HardwareRayTracing"));
    if (Writable(Hardware)) Hardware->Set(int32(UseHardwareRayTracing(Value, HardwareLumenSupported())), UserPriority);
    RefreshRenderQualityScenePolicy();
    ABreziDoubleGlassActor::InvalidateScene(GetWorld());
    bRenderQualityApplyFailed = !IsRenderQualitySelected(Value) || !CanChangeRenderQuality();
    bool bSaved = false;
    if (BreziRenderQuality::Persist(bDeliberateSelection, !bRenderQualityApplyFailed, bRenderQualityLocked))
    {
        bRenderQualitySaveFailed = true;
        if (GConfig && !GGameUserSettingsIni.IsEmpty())
        {
            GConfig->SetString(ProfileSection, ProfileKey, ProfileName(Value), GGameUserSettingsIni);
            // UE5.8 known globals are cache keys ("GameUserSettings"), not physical paths.
            // Flush returns true even when global/no-save flags suppress writes.
            const FConfigBranch* Branch = GConfig->FindBranch(FName(*GGameUserSettingsIni), GGameUserSettingsIni);
            const bool bWritesAllowed = Branch && !Branch->InMemoryFile.NoSave && !GConfig->AreFileOperationsDisabled()
                && !FParse::Param(FCommandLine::Get(), TEXT("nowrite"))
                && (!FParse::Param(FCommandLine::Get(), TEXT("Multiprocess"))
                    || FParse::Param(FCommandLine::Get(), TEXT("MultiprocessSaveConfig")));
            const bool bFlushed = bWritesAllowed && GConfig->Flush(false, GGameUserSettingsIni);
            const FString SavedPath = Branch ? Branch->IniPath : FString();
            bool bRead = false;
            const bool bMatched = VerifyProfileSave(Branch ? &Branch->FinalCombinedLayers : nullptr,
                SavedPath, bFlushed, ProfileName(Value), bRead);
            bSaved = bMatched;
            bRenderQualitySaveFailed = !bSaved;
            if (FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys")) && RenderQualityTraceEvents < 24)
                UE_LOG(LogTemp, Display, TEXT("BreziRenderQualitySave: key=%s file=%s flushed=%d read=%d matched=%d"),
                    *GGameUserSettingsIni, *SavedPath, bFlushed, bRead, bMatched);
        }
        RenderQualityOrigin = Origin::UserSelection;
    }
    TraceRenderQuality(bDeliberateSelection ? TEXT("user-selection") : TEXT("launch-apply"), Value, PriorScreen, PriorHistory, bSaved);
    return !bRenderQualityApplyFailed;
}

void ABreziPlayerController::SelectRenderQuality(BreziRenderQuality::Profile Value)
{
    if (ApplyRenderQuality(Value, true)) return;
    bRenderQualityApplyFailed = true;
    TraceRenderQuality(TEXT("selection-rejected"), Value,
        ScreenVariable() ? ScreenVariable()->GetFloat() : -1, HistoryVariable() ? HistoryVariable()->GetFloat() : -1, false);
}

FText ABreziPlayerController::RenderQualityStatus() const
{
    if (RenderQualityOrigin == Origin::NamedDiagnostic) return LOCTEXT("QualityNamedDiagnostic", "Overovací beh používa pomenovaný profil.");
    if (RenderQualityOrigin == Origin::Diagnostic) return LOCTEXT("QualityDiagnostic", "Profil riadia overovacie parametre.");
    if (RenderQualityOrigin == Origin::InvalidCommandLine) return LOCTEXT("QualityInvalid", "Neplatný profil pri spustení.");
    if (bRenderQualityLocked || !CanChangeRenderQuality()) return LOCTEXT("QualityExternal", "Profil riadia parametre spustenia alebo konzola.");
    if (bRenderQualityApplyFailed) return LOCTEXT("QualityApplyFailed", "Profil sa nepodarilo použiť.");
    if (bRenderQualitySaveFailed) return LOCTEXT("QualitySaveFailed", "Voľba platí teraz; uloženie sa nepodarilo.");
    const UBreziGameViewportClient* Presentation = GEngine ? Cast<UBreziGameViewportClient>(GEngine->GameViewport) : nullptr;
    if (Presentation && !Presentation->IsOutputSelectionValid())
        return LOCTEXT("QualityInvalidOutput", "Neplatné rozlíšenie pri spustení.");
    return Presentation && Presentation->IsRetinaOutput()
        ? LOCTEXT("QualityRetinaOutput", "Rozlíšenie sa prispôsobuje oknu a Retina displeju.")
        : LOCTEXT("QualityOutput", "4K výstup vo všetkých profiloch.");
}

void ABreziPlayerController::RefreshRenderQualityScenePolicy()
{
    const int32 AllowShadows = LocalLightShadows.GetValueOnGameThread() != 0;
    if (AllowShadows == RenderQualityLastLocalShadows) return;
    RenderQualityLastLocalShadows = AllowShadows;
    for (int32 Index = 0; Index < RenderQualityRoomLights.Num(); ++Index)
        if (URectLightComponent* Light = RenderQualityRoomLights[Index].Get())
            Light->SetCastShadows(AllowShadows && RenderQualityRoomLightShadows[Index]);
    if (ExteriorLighting) ExteriorLighting->RefreshShadowPolicy();
    ABreziDoubleGlassActor::InvalidateScene(GetWorld());
}

void ABreziPlayerController::TraceRenderQuality(const TCHAR* Event, BreziRenderQuality::Profile Value,
    float PriorScreen, float PriorHistory, bool bSaved)
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys")) || RenderQualityTraceEvents++ >= 24) return;
    const IConsoleVariable* Screen = ScreenVariable(); const IConsoleVariable* History = HistoryVariable();
    UE_LOG(LogTemp, Display, TEXT("BreziRenderQuality: event=%s schema=%d recipe=%d profile=%s origin=%d locked=%d saved=%d prior=%.3f/%.3f actual=%.3f/%.3f priority=%s/%s"),
        Event, BreziRenderQuality::NativeProfileSchemaVersion, BreziRenderQuality::RecipeRevision, ProfileName(Value), static_cast<int32>(RenderQualityOrigin),
        bRenderQualityLocked, bSaved, PriorScreen, PriorHistory, Screen ? Screen->GetFloat() : -1, History ? History->GetFloat() : -1,
        Screen ? GetConsoleVariableSetByName(static_cast<EConsoleVariableFlags>(Screen->GetFlags())) : TEXT("missing"),
        History ? GetConsoleVariableSetByName(static_cast<EConsoleVariableFlags>(History->GetFlags())) : TEXT("missing"));
}
#undef LOCTEXT_NAMESPACE
