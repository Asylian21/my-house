#include "BreziRendererSettingsAudit.h"
#if WITH_EDITOR
#include "Engine/RendererSettings.h"
#include "Materials/Material.h"
#endif

FBreziWorkingColorSpaceReadback UBreziRendererSettingsAudit::ReadWorkingColorSpace()
{
    FBreziWorkingColorSpaceReadback Result;
#if WITH_EDITOR
    if (!IsInGameThread()) return Result;
    const URendererSettings* Settings = GetDefault<URendererSettings>();
    if (!Settings) return Result;
    Result.ChoiceValue = static_cast<int32>(Settings->WorkingColorSpaceChoice.GetValue());
    Result.Red = Settings->RedChromaticityCoordinate;
    Result.Green = Settings->GreenChromaticityCoordinate;
    Result.Blue = Settings->BlueChromaticityCoordinate;
    Result.White = Settings->WhiteChromaticityCoordinate;
    Result.bLegacyLuminanceFactors = Settings->bUseLegacyLuminanceFactors != 0;
    Result.SettingsClass = Settings->GetClass()->GetPathName();
    Result.SettingsObject = Settings->GetPathName();
    Result.bValid = true;
#endif
    return Result;
}

bool UBreziRendererSettingsAudit::HasNoPixelDepthOffsetConnection(UMaterial* Material)
{
#if WITH_EDITOR
    if (!IsInGameThread() || !IsValid(Material)) return false;
    const FExpressionInput* Input = Material->GetExpressionInputForProperty(MP_PixelDepthOffset);
    return Input && Input->Expression == nullptr;
#else
    return false;
#endif
}
