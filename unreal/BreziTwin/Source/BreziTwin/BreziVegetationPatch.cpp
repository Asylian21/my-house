#include "BreziVegetationPatch.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
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
