#include "BreziVegetationPatch.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Dom/JsonObject.h"
#if WITH_EDITOR
#include "StaticMeshCompiler.h"
#endif

ABreziVegetationPatch::ABreziVegetationPatch()
{
    PrimaryActorTick.bCanEverTick = false;
    Instances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Instances"));
    SetRootComponent(Instances);
    Instances->SetMobility(EComponentMobility::Static);
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void ABreziVegetationPatch::SynchronizeInstanceBounds()
{
#if WITH_EDITOR
    if (Instances && Instances->GetStaticMesh() && Instances->GetInstanceCount() > 0)
    {
        Instances->Modify();
        Instances->BuildTreeIfOutdated(false, true);
        Instances->UpdateBounds();
        Instances->MarkRenderStateDirty();
        MarkPackageDirty();
    }
#endif
}

bool ABreziVegetationPatch::SetDetailDensityScaling(bool bEnabled)
{
    if (!Instances || Instances->GetOwner() != this || GetRootComponent() != Instances
        || Instances->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
        return false;

    Instances->Modify();
    Instances->bEnableDensityScaling = bEnabled;
    Instances->UpdateDensityScaling();
    Instances->MarkRenderStateDirty();
    MarkPackageDirty();
    return Instances->bEnableDensityScaling == bEnabled;
}

bool ABreziVegetationPatch::GetDetailDensityScaling() const
{
    return Instances && Instances->bEnableDensityScaling;
}

bool ABreziVegetationPatch::IsQualityDetailPatch() const
{
    // The imported density marker selects rural plants_* groups, not larger
    // windbreak shrubs reusing the same mesh. Actor labels are editor-only.
    return Instances && GetRootComponent() == Instances && Instances->GetOwner() == this
        && Instances->GetCollisionEnabled() == ECollisionEnabled::NoCollision
        && Instances->GetStaticMesh() && Instances->GetInstanceCount() > 0
        && Instances->bEnableDensityScaling
        && (ActorHasTag(TEXT("BreziPhotorealLawn")) || ActorHasTag(TEXT("BreziLawnDetail"))
            || ActorHasTag(TEXT("BreziRural20260923")));
}

void ABreziVegetationPatch::SetQualityDetailLighting(bool bEnabled)
{
    if (!IsQualityDetailPatch()) return;
    if (!bQualityDetailCaptured)
    {
        bQualityDetailAuthoredShadow = Instances->CastShadow;
        bQualityDetailAuthoredRayTracing = Instances->bVisibleInRayTracing;
        bQualityDetailAuthoredDistanceField = Instances->bAffectDistanceFieldLighting;
        bQualityDetailCaptured = true;
    }
    bQualityDetailEnabled = bEnabled;
    Instances->SetCastShadow(bEnabled || bQualityDetailAuthoredShadow);
    Instances->SetVisibleInRayTracing(bEnabled || bQualityDetailAuthoredRayTracing);
    Instances->SetAffectDistanceFieldLighting(bEnabled || bQualityDetailAuthoredDistanceField);
}

TSharedRef<FJsonObject> ABreziVegetationPatch::GetQualityDetailLightingDiagnostics() const
{
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("actor"), GetPathName());
    Result->SetBoolField(TEXT("managedDetail"), IsQualityDetailPatch());
    Result->SetBoolField(TEXT("authoredFlagsCaptured"), bQualityDetailCaptured);
    Result->SetBoolField(TEXT("qualityEnabled"), bQualityDetailEnabled);
    Result->SetBoolField(TEXT("authoredCastShadow"), bQualityDetailAuthoredShadow);
    Result->SetBoolField(TEXT("authoredVisibleInRayTracing"), bQualityDetailAuthoredRayTracing);
    Result->SetBoolField(TEXT("authoredAffectDistanceFieldLighting"), bQualityDetailAuthoredDistanceField);
    Result->SetBoolField(TEXT("castShadow"), Instances && Instances->CastShadow);
    Result->SetBoolField(TEXT("visibleInRayTracing"), Instances && Instances->bVisibleInRayTracing);
    Result->SetBoolField(TEXT("affectDistanceFieldLighting"), Instances && Instances->bAffectDistanceFieldLighting);
    Result->SetNumberField(TEXT("instanceCount"), Instances ? Instances->GetInstanceCount() : 0);
    return Result;
}

TArray<int32> ABreziVegetationPatch::ConfigureDetailLods(UStaticMesh* Mesh)
{
    TArray<int32> Counts;
#if WITH_EDITOR
    if (!Mesh || !Mesh->GetPathName().StartsWith(TEXT("/Game/Brezi/VegetationGenerated/"))
        || Mesh->GetNumSourceModels() < 1)
        return Counts;

    TArray<UStaticMesh*> Pending = {Mesh};
    FStaticMeshCompilingManager::Get().FinishCompilation(Pending);
    Mesh->Modify();
    FMeshNaniteSettings Nanite = Mesh->GetNaniteSettings();
    Nanite.bEnabled = false;
    Mesh->SetNaniteSettings(Nanite);
    Mesh->SetNumSourceModels(1);
    Mesh->SetAutoComputeLODScreenSize(false);
    Mesh->GetSourceModel(0).ReductionSettings.PercentTriangles = 1.0f;
    Mesh->GetSourceModel(0).ScreenSize.Default = 1.0f;
    const float Fractions[] = {1.0f, 0.5f, 0.2f};
    const float Screens[] = {1.0f, 0.3f, 0.1f};
    for (int32 Index = 1; Index < 3; ++Index)
    {
        FStaticMeshSourceModel& Model = Mesh->AddSourceModel();
        Model.BuildSettings = Mesh->GetSourceModel(0).BuildSettings;
        Model.BuildSettings.bGenerateLightmapUVs = false;
        Model.BuildSettings.bUseFullPrecisionUVs = true;
        Model.ReductionSettings = Mesh->GetSourceModel(0).ReductionSettings;
        Model.ReductionSettings.BaseLODModel = 0;
        Model.ReductionSettings.PercentTriangles = Fractions[Index];
        Model.ScreenSize.Default = Screens[Index];
    }
    TArray<FText> Errors;
    Mesh->Build(false, &Errors);
    FStaticMeshCompilingManager::Get().FinishCompilation(Pending);
    if (!Errors.IsEmpty() || Mesh->GetNumLODs() != 3)
        return Counts;
    for (int32 Index = 0; Index < 3; ++Index)
    {
        const int32 Triangles = Mesh->GetNumTriangles(Index);
        if (Triangles <= 0)
            return {};
        Counts.Add(Triangles);
    }
    Mesh->MarkPackageDirty();
#endif
    return Counts;
}
