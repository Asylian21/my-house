#include "BreziAvatarBlendSpace.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace1D.h"
#include "Misc/PackageName.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"

UBlendSpace1D* UBreziAvatarBlendSpace::CreateLocomotionAsset(const FString& PackagePath,
    UAnimSequence* Idle, UAnimSequence* Walk, UAnimSequence* Run)
{
#if WITH_EDITOR
    if (!PackagePath.StartsWith(TEXT("/Game/Brezi/Avatar/Michelle/"))
        || !Idle || !Walk || !Run || !Idle->GetSkeleton()
        || Walk->GetSkeleton() != Idle->GetSkeleton() || Run->GetSkeleton() != Idle->GetSkeleton()
        || Idle->GetPlayLength() < 0.2f || Walk->GetPlayLength() < 0.2f || Run->GetPlayLength() < 0.2f) return nullptr;
    UPackage* Package = CreatePackage(*PackagePath);
    const FName Name(*FPackageName::GetLongPackageAssetName(PackagePath));
    UBlendSpace1D* Asset = FindObject<UBlendSpace1D>(Package, *Name.ToString());
    if (!Asset) Asset = NewObject<UBlendSpace1D>(Package, Name, RF_Public | RF_Standalone);
    Asset->SetSkeleton(Idle->GetSkeleton());
    while (Asset->GetNumberOfBlendSamples() > 0) Asset->DeleteSample(Asset->GetNumberOfBlendSamples() - 1);
    // UBlendSpace1D is MinimalAPI. Create the native asset directly; subclassing
    // it would require non-exported virtual symbols in the installed Editor.
    FStructProperty* Parameters = FindFProperty<FStructProperty>(UBlendSpace::StaticClass(), TEXT("BlendParameters"));
    if (!Parameters || Parameters->ArrayDim != 3) return nullptr;
    FBlendParameter* Speed = Parameters->ContainerPtrToValuePtr<FBlendParameter>(Asset, 0);
    Speed->DisplayName = TEXT("Speed cm/s");
    Speed->Min = 0;
    Speed->Max = 240;
    Speed->GridNum = 8;
    Speed->bSnapToGrid = false;
    Asset->TargetWeightInterpolationSpeedPerSec = 8;
    Asset->bTargetWeightInterpolationEaseInOut = true;
    Asset->AddSample(Idle, FVector::ZeroVector);
    Asset->AddSample(Walk, FVector(115, 0, 0));
    Asset->AddSample(Run, FVector(240, 0, 0));
    Asset->ValidateSampleData();
    Asset->ResampleData();
    Asset->MarkPackageDirty();
    return Asset;
#else
    return nullptr;
#endif
}
