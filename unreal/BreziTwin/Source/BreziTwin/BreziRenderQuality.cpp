#include "BreziPlayerController.h"
#include "BreziGameViewportClient.h"
#include "Engine/Engine.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"

#define LOCTEXT_NAMESPACE "BreziTwin"
using BreziRenderQuality::Profile;
using BreziRenderQuality::Origin;
namespace
{
using namespace BreziRenderQuality;
constexpr const TCHAR* ProfileSection = TEXT("Brezi.RenderQuality");
constexpr const TCHAR* ProfileKey = TEXT("ProfileV1");
constexpr EConsoleVariableFlags UserPriority = ECVF_SetByGameOverride;
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
        TEXT("BreziMotionQA"), TEXT("BreziRealtimeOrbit"), TEXT("BreziCausticsMotionQA"), TEXT("BreziWalk"), TEXT("BreziWalkAudit"),
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
        ParseProfile(Named), ParseProfile(Saved), CanChangeRenderQuality());
    RenderQualityOrigin = Decision.Source;
    bRenderQualityLocked = Decision.Locked;
    if (Decision.Apply) ApplyRenderQuality(Decision.Requested, false);
    else TraceRenderQuality(TEXT("launch-locked"), Profile::Unknown,
        ScreenVariable() ? ScreenVariable()->GetFloat() : -1, HistoryVariable() ? HistoryVariable()->GetFloat() : -1, false);
}

bool ABreziPlayerController::CanChangeRenderQuality() const
{
    const IConsoleVariable* Screen = ScreenVariable();
    const IConsoleVariable* History = HistoryVariable();
    const auto* AA = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod"));
    const auto* Dynamic = IConsoleManager::Get().FindConsoleVariable(TEXT("r.DynamicRes.OperationMode"));
    const auto* Secondary = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SecondaryScreenPercentage.GameViewport"));
    if (!Screen || !History || !AA || !Dynamic || !Secondary) return false;
    const bool bWritable = ((Screen->GetFlags() | History->GetFlags()) & (ECVF_ReadOnly | ECVF_Unregistered)) == 0;
    return BreziRenderQuality::CanApply(bRenderQualityLocked, bWritable,
        Screen->GetFlags() & ECVF_SetByMask, History->GetFlags() & ECVF_SetByMask, UserPriority,
        AA->GetInt(), Dynamic->GetInt(), Secondary->GetFloat());
}

bool ABreziPlayerController::IsRenderQualitySelected(BreziRenderQuality::Profile Value) const
{
    const auto* AA = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod"));
    const auto* Dynamic = IConsoleManager::Get().FindConsoleVariable(TEXT("r.DynamicRes.OperationMode"));
    const auto* Secondary = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SecondaryScreenPercentage.GameViewport"));
    return AA && Dynamic && Secondary && BreziRenderQuality::CompatiblePipeline(AA->GetInt(), Dynamic->GetInt(), Secondary->GetFloat())
        && ScreenVariable() && HistoryVariable()
        && BreziRenderQuality::Match(ScreenVariable()->GetFloat(), HistoryVariable()->GetFloat()) == Value;
}

bool ABreziPlayerController::ApplyRenderQuality(BreziRenderQuality::Profile Value, bool bDeliberateSelection)
{
    if (!BreziRenderQuality::IsValid(Value) || !CanChangeRenderQuality()) return false;
    IConsoleVariable* Screen = ScreenVariable();
    IConsoleVariable* History = HistoryVariable();
    const float PriorScreen = Screen->GetFloat(), PriorHistory = History->GetFloat();
    const auto Pair = BreziRenderQuality::Values(Value);
    // User override is stronger than project/device defaults and weaker than CLI/console.
    // Do not use SetByCode/Console or rewrite priority bits to defeat an external override.
    Screen->Set(Pair.ScreenPercentage, UserPriority);
    History->Set(Pair.HistoryPercentage, UserPriority);
    bRenderQualityApplyFailed = !IsRenderQualitySelected(Value) || !CanChangeRenderQuality();
    bool bSaved = false;
    if (BreziRenderQuality::Persist(bDeliberateSelection, !bRenderQualityApplyFailed, bRenderQualityLocked))
    {
        bRenderQualitySaveFailed = true;
        if (GConfig && !GGameUserSettingsIni.IsEmpty())
        {
            GConfig->SetString(ProfileSection, ProfileKey, ProfileName(Value), GGameUserSettingsIni);
            const bool bFlushed = GConfig->Flush(false, GGameUserSettingsIni);
            // UE5.8 known globals are cache keys ("GameUserSettings"), not physical paths.
            // Read the branch destination independently of both GConfig and config override delegates.
            const FConfigBranch* Branch = GConfig->FindBranch(FName(*GGameUserSettingsIni), GGameUserSettingsIni);
            const FString SavedPath = Branch ? Branch->IniPath : FString();
            FString Contents, Persisted;
            const bool bRead = !SavedPath.IsEmpty() && FFileHelper::LoadFileToString(Contents, *SavedPath);
            FConfigFile Disk;
            if (bRead) Disk.ProcessInputFileContents(Contents, SavedPath);
            const bool bMatched = bRead && Disk.GetString(ProfileSection, ProfileKey, Persisted) && Persisted == ProfileName(Value);
            bSaved = bFlushed && bMatched;
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

void ABreziPlayerController::TraceRenderQuality(const TCHAR* Event, BreziRenderQuality::Profile Value,
    float PriorScreen, float PriorHistory, bool bSaved)
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys")) || RenderQualityTraceEvents++ >= 24) return;
    const IConsoleVariable* Screen = ScreenVariable(); const IConsoleVariable* History = HistoryVariable();
    UE_LOG(LogTemp, Display, TEXT("BreziRenderQuality: event=%s schema=%d profile=%s origin=%d locked=%d saved=%d prior=%.3f/%.3f actual=%.3f/%.3f priority=%s/%s"),
        Event, BreziRenderQuality::NativeProfileSchemaVersion, ProfileName(Value), static_cast<int32>(RenderQualityOrigin),
        bRenderQualityLocked, bSaved, PriorScreen, PriorHistory, Screen ? Screen->GetFloat() : -1, History ? History->GetFloat() : -1,
        Screen ? GetConsoleVariableSetByName(static_cast<EConsoleVariableFlags>(Screen->GetFlags())) : TEXT("missing"),
        History ? GetConsoleVariableSetByName(static_cast<EConsoleVariableFlags>(History->GetFlags())) : TEXT("missing"));
}
#undef LOCTEXT_NAMESPACE
