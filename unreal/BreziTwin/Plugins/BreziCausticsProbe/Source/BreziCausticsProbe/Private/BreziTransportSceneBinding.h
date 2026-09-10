#pragma once
// Live GT binding. Editor source proof or verified cooked lineage; UObject caches stay on GT.
// MeshDescription/StaticMeshDescription are Editor-only module dependencies.
#include "CoreMinimal.h"
#include "BreziCookedSceneBinding.h"
#include "BreziSceneRevision.h"
#include "Containers/StaticArray.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/Material.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "UObject/Package.h"
#if WITH_EDITORONLY_DATA
#include "MeshDescription.h"
#include "StaticMeshAttributes.h"
#endif

namespace BreziTransportSceneBinding
{
// Generated binding.json bytes; do not substitute historical receiver optics.
static constexpr const TCHAR* BindingSha256 = BreziSceneRevision::BindingSha256;
static constexpr const TCHAR* BindingSha1 = BreziSceneRevision::BindingSha1;
struct FRow
{
    FString Id, Asset, Role;
    FBox Bounds = FBox(ForceInit);
    int32 TriangleCount = 0;
    TSharedPtr<FJsonObject> Expected;
    TWeakObjectPtr<AActor> Actor;
    TWeakObjectPtr<UStaticMeshComponent> Component;
    TWeakObjectPtr<UStaticMesh> Mesh;
    TArray<TWeakObjectPtr<UMaterialInterface>> Materials;
    double MaximumVertexErrorCm = 0;
};
struct FCache
{
    TWeakObjectPtr<UWorld> World;
    TArray<FRow> Rows;
    FString MapPackage;
    double BoundsToleranceCm = 0, VertexToleranceCm = 0;
    bool bBound = false;
    bool bCookedLineage = false;
    FString CookedReceiptSha1;
};
inline bool Fail(FString& Error, const FString& Message) { Error = Message; return false; }
inline TArray<TSharedPtr<FJsonValue>> V3(const FVector& V)
{
    return {MakeShared<FJsonValueNumber>(V.X), MakeShared<FJsonValueNumber>(V.Y), MakeShared<FJsonValueNumber>(V.Z)};
}
inline FVector Vec(const TArray<TSharedPtr<FJsonValue>>& A)
{
    // JSON bytes are pinned before parsing; schema is CPU checked by exporter.
    return FVector(A[0]->AsNumber(), A[1]->AsNumber(), A[2]->AsNumber());
}
inline bool FileMatches(const FString& Path, const FString& Sha1)
{
    TArray<uint8> Bytes; if (!FFileHelper::LoadFileToArray(Bytes, *Path)) return false;
    uint8 Hash[FSHA1::DigestSize]; FSHA1::HashBuffer(Bytes.GetData(), Bytes.Num(), Hash);
    return BytesToHex(Hash, FSHA1::DigestSize).Equals(Sha1, ESearchCase::IgnoreCase);
}
// Count both DOM tags and uses of each canonical mesh. A duplicate, untagged
// clone, derived ISM or actor carrying another expected mesh cannot pass.
inline bool Resolve_GT(UWorld* World, const FCache& Cache, TArray<UStaticMeshComponent*>& Out, FString& Error)
{
    TMap<FName,int32> Tags; TMap<FString,int32> Assets;
    TArray<int32> TagCounts, AssetCounts; TagCounts.Init(0,Cache.Rows.Num()); AssetCounts.Init(0,Cache.Rows.Num()); Out.Init(nullptr,Cache.Rows.Num());
    for(int32 I=0;I<Cache.Rows.Num();++I){Tags.Add(FName(*Cache.Rows[I].Id),I);Assets.Add(Cache.Rows[I].Asset,I);}
    for(TActorIterator<AActor> It(World);It;++It)
    {
        AActor* A=*It; int32 Tagged=INDEX_NONE;
        for(const FName& Tag:A->Tags) if(const int32* I=Tags.Find(Tag))
        { if(Tagged!=INDEX_NONE)return Fail(Error,TEXT("Multiple expected source tags on actor"));Tagged=*I;++TagCounts[*I]; }
        TArray<UStaticMeshComponent*> Components; A->GetComponents(Components);
        for(UStaticMeshComponent* C:Components)
        {
            if(!C || !C->GetStaticMesh())continue;
            if(const int32* I=Assets.Find(C->GetStaticMesh()->GetPathName()))
            {
                ++AssetCounts[*I];
                if(Tagged!=*I || !A->ActorHasTag(TEXT("BreziGenerated")) || C->GetClass()!=UStaticMeshComponent::StaticClass())
                    return Fail(Error,TEXT("Canonical asset has foreign source identity/class"));
                Out[*I]=C;
            }
        }
    }
    for(int32 I=0;I<Cache.Rows.Num();++I) if(TagCounts[I]!=1 || AssetCounts[I]!=1 || !Out[I])
        return Fail(Error,TEXT("Missing/duplicate source actor or asset: ")+Cache.Rows[I].Id);
    return true;
}
inline bool CheckRow_GT(UWorld* World, const FRow& R, UStaticMeshComponent* C, double Tolerance, FString& Error)
{
    AActor* A=C ? C->GetOwner() : nullptr; UStaticMesh* M=C ? C->GetStaticMesh() : nullptr;
    if(!A || !M || A->GetWorld()!=World || A->GetLevel()!=World->PersistentLevel || A->IsActorBeingDestroyed()
       || C->IsBeingDestroyed() || !C->IsRegistered() || !C->IsRenderStateCreated() || C->IsRenderStateDirty()
       || C->IsRenderTransformDirty() || !C->GetPrimitiveSceneId().IsValid() || !C->IsVisible() || A->IsHidden()
       || !C->bRenderInMainPass || C->IsReverseCulling() || !C->GetComponentTransform().Equals(FTransform::Identity,0)
       || M->GetPathName()!=R.Asset || M->IsCompiling()
#if WITH_EDITORONLY_DATA
       || M->IsNaniteEnabled()
#else
       || M->HasValidNaniteData()
#endif
       || M->GetOutermost()->IsDirty()
       || !C->Bounds.GetBox().Min.Equals(R.Bounds.Min,Tolerance) || !C->Bounds.GetBox().Max.Equals(R.Bounds.Max,Tolerance))
        return Fail(Error,TEXT("Source pose/visibility/render state differs: ")+R.Id);
    const auto& Slots=R.Expected->GetArrayField(TEXT("materialSlots"));
    const auto& MeshMats=R.Expected->GetArrayField(TEXT("meshMaterials"));
    const auto& Effective=R.Expected->GetArrayField(TEXT("effectiveMaterials"));
    const auto& Overrides=R.Expected->GetArrayField(TEXT("overrides"));
    if(C->GetNumMaterials()!=Slots.Num() || M->GetStaticMaterials().Num()!=Slots.Num() || C->OverrideMaterials.Num()!=Overrides.Num()
       || M->GetNumSections(0)!=Slots.Num() || M->GetNumTriangles(0)!=R.TriangleCount)
        return Fail(Error,TEXT("Source material slots/topology count differs: ")+R.Id);
    for(int32 I=0;I<Slots.Num();++I)
    {
        UMaterialInterface* Mat=C->GetMaterial(I); UMaterialInterface* Source=M->GetMaterial(I);
        UMaterial* Base=Mat ? Mat->GetMaterial() : nullptr;
        if(!Mat || !Source || !Base || Cast<UMaterialInstanceDynamic>(Mat)
           || Mat->GetOutermost()->IsDirty() || Base->GetOutermost()->IsDirty()
           || Mat->GetPathName()!=Effective[I]->AsString() || Source->GetPathName()!=MeshMats[I]->AsString()
           || M->GetStaticMaterials()[I].MaterialSlotName.ToString()!=Slots[I]->AsString()
           || Mat->GetBlendMode()!=BLEND_Opaque || Base->HasVertexPositionOffsetConnected() || Base->HasDisplacementConnected()
           || Base->HasPixelDepthOffsetConnected()
           || (R.Role==TEXT("water") && !Mat->GetShadingModels().HasShadingModel(MSM_SingleLayerWater)))
            return Fail(Error,TEXT("Saved material identity/static-surface contract differs: ")+R.Id);
    }
    for(int32 I=0;I<Overrides.Num();++I)
        if(!C->OverrideMaterials[I] || C->OverrideMaterials[I]->GetPathName()!=Overrides[I]->AsString())
            return Fail(Error,TEXT("Component override differs: ")+R.Id);
    return true;
}
inline bool CheckGeometry_GT(UStaticMesh* Mesh, FRow& Row, double Tolerance, FString& Error)
{
#if WITH_EDITORONLY_DATA
    // Clone reads current cached data or deserializes source bulk into a local
    // value; unlike GetMeshDescription it does not create a cached UObject.
    FMeshDescription LocalDescription;
    if(!Mesh->CloneMeshDescription(0,LocalDescription))return Fail(Error,TEXT("Missing native source MeshDescription: ")+Row.Id);
    const FMeshDescription* MD=&LocalDescription;
    const auto& Source=Row.Expected->GetArrayField(TEXT("trianglesCm"));
    if(MD->Triangles().Num()!=Source.Num())return Fail(Error,TEXT("Native source triangle count: ")+Row.Id);
    const FStaticMeshConstAttributes Attributes(*MD); const auto Positions=Attributes.GetVertexPositions();
    TArray<TStaticArray<FVector,3>> Expected; TMap<FIntVector,TArray<int32>> Buckets;
    auto Cell=[Tolerance](const FVector& V){return FIntVector(FMath::FloorToInt(V.X/Tolerance),FMath::FloorToInt(V.Y/Tolerance),FMath::FloorToInt(V.Z/Tolerance));};
    for(const auto& Value:Source)
    {
        const auto& T=Value->AsArray();TStaticArray<FVector,3> P;
        for(int32 K=0;K<3;++K)P[K]=Vec(T[K]->AsArray());
        const int32 Index=Expected.Add(P);Buckets.FindOrAdd(Cell((P[0]+P[1]+P[2])/3)).Add(Index);
    }
    TBitArray<> Used(false,Expected.Num()); int32 Matched=0;
    for(const FTriangleID Triangle:MD->Triangles().GetElementIDs())
    {
        const auto Corners=MD->GetTriangleVertexInstances(Triangle);TStaticArray<FVector,3> Actual;
        for(int32 K=0;K<3;++K){Actual[K]=FVector(Positions[MD->GetVertexInstanceVertex(Corners[K])]);if(Actual[K].ContainsNaN())return Fail(Error,TEXT("Nonfinite native source position"));}
        const FIntVector C=Cell((Actual[0]+Actual[1]+Actual[2])/3);int32 Winner=INDEX_NONE;double WinnerError=0;
        for(int32 X=-1;X<=1;++X)for(int32 Y=-1;Y<=1;++Y)for(int32 Z=-1;Z<=1;++Z)
        if(const auto* Indices=Buckets.Find(C+FIntVector(X,Y,Z)))for(int32 Index:*Indices)
        {
            if(Used[Index])continue;double Best=TNumericLimits<double>::Max();
            for(int32 Shift=0;Shift<3;++Shift)
            {
                double E=0;for(int32 K=0;K<3;++K)E=FMath::Max(E,(Actual[K]-Expected[Index][(K+Shift)%3]).GetAbsMax());
                Best=FMath::Min(Best,E);
            }
            if(Best<=Tolerance){if(Winner!=INDEX_NONE)return Fail(Error,TEXT("Ambiguous native/source triangle: ")+Row.Id);Winner=Index;WinnerError=Best;}
        }
        if(Winner==INDEX_NONE)return Fail(Error,TEXT("Native source triangle missing/reversed/moved: ")+Row.Id);
        Used[Winner]=true;++Matched;Row.MaximumVertexErrorCm=FMath::Max(Row.MaximumVertexErrorCm,WinnerError);
    }
    return Matched==Source.Num() || Fail(Error,TEXT("Incomplete native source geometry bijection"));
#else
    return Fail(Error,TEXT("This binding proposal requires Editor MeshDescription; no cooked geometry proof is implied"));
#endif
}
inline bool LoadAndBind_GT(UWorld* World, const FString& Path, FCache& Cache, FString& Error, const BreziCookedSceneBinding::FVerifiedPackage* Cooked = nullptr)
{
    if(!IsInGameThread() || !World || Cache.bBound)return Fail(Error,TEXT("Binding needs first GT world initialization"));
    if(!FileMatches(Path,BindingSha1))return Fail(Error,TEXT("Scene binding bytes differ"));
    FString Text;TSharedPtr<FJsonObject> J;
    if(!FFileHelper::LoadFileToString(Text,*Path) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J) || !J.IsValid())return Fail(Error,TEXT("Invalid scene binding JSON"));
    Cache=FCache();Cache.MapPackage=J->GetStringField(TEXT("mapPackage"));Cache.BoundsToleranceCm=J->GetNumberField(TEXT("boundsToleranceCm"));Cache.VertexToleranceCm=J->GetNumberField(TEXT("vertexToleranceMm"))/10;
    if(World->GetOutermost()->GetName()!=Cache.MapPackage)return Fail(Error,TEXT("Binding world map package differs"));
    Cache.bCookedLineage=FPlatformProperties::RequiresCookedData();
    if(Cache.bCookedLineage)
    {
        if(!Cooked || !Cooked->IsVerified())return Fail(Error,TEXT("Cooked scene needs verified source/container lineage token"));
        Cache.CookedReceiptSha1=Cooked->ReceiptSha1();
    }
    else if(Cooked)return Fail(Error,TEXT("Cooked token is not an Editor geometry bypass"));
    for(const auto& Pair:J->GetObjectField(TEXT("assetFileHashes"))->Values)
    {
        const FString Key(*Pair.Key);
        const FString SourceSha1=Pair.Value->AsObject()->GetStringField(TEXT("sha1"));
        if(Cache.bCookedLineage ? !Cooked->CoversSourceAsset(Key,SourceSha1) : !FileMatches(FPaths::Combine(FPaths::ProjectDir(),Key),SourceSha1))
            return Fail(Error,FString::Printf(TEXT("Saved scene source identity differs: %s"), *Key));
    }
    for(const auto& Value:J->GetArrayField(TEXT("objects")))
    {
        FRow R;R.Expected=Value->AsObject();R.Id=R.Expected->GetStringField(TEXT("id"));R.Asset=R.Expected->GetStringField(TEXT("asset"));R.Role=R.Expected->GetStringField(TEXT("role"));R.TriangleCount=R.Expected->GetIntegerField(TEXT("sourceTriangles"));
        const auto B=R.Expected->GetObjectField(TEXT("sourceBoundsCm"));R.Bounds=FBox(Vec(B->GetArrayField(TEXT("min"))),Vec(B->GetArrayField(TEXT("max"))));Cache.Rows.Add(MoveTemp(R));
    }
    TArray<UStaticMeshComponent*> Resolved;if(!Resolve_GT(World,Cache,Resolved,Error))return false;
    for(int32 I=0;I<Cache.Rows.Num();++I)
    {
        FRow& R=Cache.Rows[I];UStaticMeshComponent* C=Resolved[I];
        if(!CheckRow_GT(World,R,C,Cache.BoundsToleranceCm,Error))return false;
        if(!Cache.bCookedLineage && !CheckGeometry_GT(C->GetStaticMesh(),R,Cache.VertexToleranceCm,Error))return false;
        R.Actor=C->GetOwner();R.Component=C;R.Mesh=C->GetStaticMesh();
        for(int32 K=0;K<C->GetNumMaterials();++K)R.Materials.Add(C->GetMaterial(K));
    }
    Cache.World=World;Cache.bBound=true;return true;
}
inline bool Snapshot_GT(UWorld* World, const FCache& Cache, uint64 FrameCounter, uint32 FrameNumber, TSharedPtr<FJsonObject>& Out, FString& Error, bool bDetailed = true)
{
    Out.Reset();if(!IsInGameThread() || !Cache.bBound || Cache.World.Get()!=World)return Fail(Error,TEXT("No same-world initialized source binding"));
    TArray<UStaticMeshComponent*> Resolved;if(!Resolve_GT(World,Cache,Resolved,Error))return false;
    auto J=MakeShared<FJsonObject>();TArray<TSharedPtr<FJsonValue>> Rows;int32 Receivers=0,Water=0;
    for(int32 I=0;I<Cache.Rows.Num();++I)
    {
        const FRow& R=Cache.Rows[I];UStaticMeshComponent* C=Resolved[I];
        if(C!=R.Component.Get() || C->GetOwner()!=R.Actor.Get() || C->GetStaticMesh()!=R.Mesh.Get() || !CheckRow_GT(World,R,C,Cache.BoundsToleranceCm,Error))return Fail(Error,TEXT("Cached source identity/state changed: ")+R.Id+TEXT(" ")+Error);
        for(int32 K=0;K<C->GetNumMaterials();++K)if(C->GetMaterial(K)!=R.Materials[K].Get())return Fail(Error,TEXT("Cached material object changed: ")+R.Id);
        if(R.Role==TEXT("water"))++Water;else ++Receivers;
        if(!bDetailed)continue;
        auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("id"),R.Id);Row->SetStringField(TEXT("role"),R.Role);Row->SetStringField(TEXT("actorPath"),C->GetOwner()->GetPathName());Row->SetStringField(TEXT("componentPath"),C->GetPathName());Row->SetStringField(TEXT("asset"),R.Asset);
        Row->SetNumberField(TEXT("primitiveId"),C->GetPrimitiveSceneId().PrimIDValue);Row->SetArrayField(TEXT("boundsMinCm"),V3(C->Bounds.GetBox().Min));Row->SetArrayField(TEXT("boundsMaxCm"),V3(C->Bounds.GetBox().Max));
        Row->SetBoolField(TEXT("identityWorldTransform"),true);Row->SetBoolField(TEXT("visible"),C->IsVisible());Row->SetBoolField(TEXT("actorHidden"),C->GetOwner()->IsHidden());Row->SetBoolField(TEXT("registered"),C->IsRegistered());Row->SetBoolField(TEXT("renderStateCreated"),C->IsRenderStateCreated());Row->SetBoolField(TEXT("renderInMainPass"),C->bRenderInMainPass);
        Row->SetBoolField(TEXT("visibleInRayTracingSetting"),C->bVisibleInRayTracing);Row->SetBoolField(TEXT("castShadowSetting"),C->CastShadow);Row->SetNumberField(TEXT("nativeSourceTriangles"),R.TriangleCount);if(!Cache.bCookedLineage)Row->SetNumberField(TEXT("maximumVertexErrorCm"),R.MaximumVertexErrorCm);
        Row->SetArrayField(TEXT("effectiveMaterials"),R.Expected->GetArrayField(TEXT("effectiveMaterials")));Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    if(Receivers!=45 || Water!=1)return Fail(Error,TEXT("Bound source scope differs"));
    J->SetStringField(TEXT("bindingSha256"),BindingSha256);J->SetStringField(TEXT("worldPath"),World->GetPathName());J->SetNumberField(TEXT("frameCounter"),double(FrameCounter));J->SetNumberField(TEXT("frameNumber"),FrameNumber);J->SetNumberField(TEXT("matchedReceivers"),Receivers);J->SetNumberField(TEXT("matchedWater"),Water);J->SetArrayField(TEXT("objects"),Rows);
    J->SetBoolField(TEXT("sourceBvhActorBindingPassed"),true);J->SetBoolField(TEXT("editorNativeTriangleBijectionPassed"),!Cache.bCookedLineage);J->SetBoolField(TEXT("priorEditorNativeTriangleBijectionReused"),Cache.bCookedLineage);J->SetStringField(TEXT("geometryProofMode"),Cache.bCookedLineage?TEXT("cooked-container-lineage-and-live-checks"):TEXT("editor-native-triangle-bijection"));J->SetStringField(TEXT("cookedPackageReceiptSha1"),Cache.CookedReceiptSha1);J->SetBoolField(TEXT("detailedObjectRows"),bDetailed);J->SetBoolField(TEXT("geometryCheckedAtInitializationNotEveryFrame"),true);J->SetBoolField(TEXT("opaqueTlasCoverageVerified"),false);J->SetBoolField(TEXT("fullGlassAlphaTransmissionVerified"),false);Out=J;return true;
}
}
