#include "BreziWalkingContract.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "PhysicsEngine/BodySetup.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    bool Number(const TSharedPtr<FJsonObject>& Object, const TCHAR* Key, double& Value, double Min, double Max)
    {
        return Object.IsValid() && Object->TryGetNumberField(Key, Value) && FMath::IsFinite(Value) && Value >= Min && Value <= Max;
    }

    bool Vector(const TSharedPtr<FJsonObject>& Object, const TCHAR* Key, FVector& Value)
    {
        const TArray<TSharedPtr<FJsonValue>>* Array = nullptr;
        if (!Object.IsValid() || !Object->TryGetArrayField(Key, Array) || Array->Num() != 3) return false;
        double Components[3];
        for (int32 Index = 0; Index < 3; ++Index)
            if (!(*Array)[Index]->TryGetNumber(Components[Index]) || !FMath::IsFinite(Components[Index])) return false;
        Value = FVector(Components[0], Components[1], Components[2]);
        return true;
    }

    bool HasTag(const UPrimitiveComponent* Component, const FName& Tag)
    {
        return Component->ComponentHasTag(Tag) || (Component->GetOwner() && Component->GetOwner()->ActorHasTag(Tag));
    }

    bool BlocksWalker(const UPrimitiveComponent* Component)
    {
        return Component && Component->IsQueryCollisionEnabled() && Component->GetCollisionResponseToChannel(ECC_Pawn) == ECR_Block;
    }

    bool IsAuxiliaryId(const FString& Id)
    {
        if (!Id.StartsWith(TEXT("COLL_")) || Id.Len() != 25) return false;
        for (int32 Index = 5; Index < Id.Len(); ++Index)
            if (!((Id[Index] >= '0' && Id[Index] <= '9') || (Id[Index] >= 'a' && Id[Index] <= 'f'))) return false;
        return true;
    }

    bool IsHiddenSourceCollider(const UPrimitiveComponent* Component)
    {
        const UStaticMeshComponent* MeshComponent = Cast<UStaticMeshComponent>(Component);
        const UStaticMesh* Mesh = MeshComponent ? MeshComponent->GetStaticMesh() : nullptr;
        const UBodySetup* Body = Mesh ? Mesh->GetBodySetup() : nullptr;
        return MeshComponent && Body && Body->GetCollisionTraceFlag() == CTF_UseComplexAsSimple
            && Mesh->LODForCollision == 0 && !Body->bNeverNeedsCookedCollisionData
            && !Body->bFailedToCreatePhysicsMeshes && !Body->TriMeshGeometries.IsEmpty()
            && Component->GetCollisionProfileName() == FName(TEXT("BlockAll"))
            && !Component->IsVisible() && Component->bHiddenInGame && !Component->CastShadow
            && !Component->bCastHiddenShadow && !Component->bAffectDynamicIndirectLighting
            && !Component->bAffectIndirectLightingWhileHidden
            && !Component->bVisibleInRayTracing && !Component->bAffectDistanceFieldLighting
            && !FBreziWalkingContract::IsFloor(Component);
    }
}

bool FBreziWalkingContract::IsFloor(const UPrimitiveComponent* Component)
{
    // Component-only: an offset support and its lower visual mesh may share an actor.
    return Component && Component->ComponentHasTag(TEXT("BreziWalkSurface"));
}

FString FBreziWalkingContract::ObjectId(const UPrimitiveComponent* Component)
{
    if (!Component) return FString();
    const auto Find = [](const TArray<FName>& Tags)
    {
        for (const FName& Tag : Tags)
        {
            const FString Text = Tag.ToString();
            if (Text.StartsWith(TEXT("BreziSourceObjectId="))) return Text.RightChop(20);
            if (Text.StartsWith(TEXT("DOM_"))) return Text;
        }
        return FString();
    };
    const FString OnComponent = Find(Component->ComponentTags);
    return !OnComponent.IsEmpty() ? OnComponent : Component->GetOwner() ? Find(Component->GetOwner()->Tags) : FString();
}

bool FBreziWalkingContract::Load(FString& Error)
{
    *this = FBreziWalkingContract();
    Error = TEXT("walking.json: missing or invalid shared walking contract");
    FString Text;
    TSharedPtr<FJsonObject> Root;
    if (!FFileHelper::LoadFileToString(Text, *(FPaths::ProjectContentDir() / TEXT("Data/walking.json")))
        || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Root) || !Root.IsValid()) return false;
    FString Coordinates;
    double Schema = 0;
    if (!Number(Root, TEXT("schemaVersion"), Schema, 1, 1)
        || !Root->TryGetStringField(TEXT("coordinateSystem"), Coordinates) || Coordinates != TEXT("unreal-centimeters")
        || !Number(Root, TEXT("eyeHeightCm"), EyeHeightCm, 100, 220)
        || !Number(Root, TEXT("capsuleRadiusCm"), CapsuleRadiusCm, 10, 50)
        || !Number(Root, TEXT("capsuleHalfHeightCm"), CapsuleHalfHeightCm, 50, 120)
        || CapsuleHalfHeightCm <= CapsuleRadiusCm || CapsuleHalfHeightCm * 2 <= EyeHeightCm
        || !Number(Root, TEXT("maxStepHeightCm"), MaxStepCm, 0, 50)
        || !Number(Root, TEXT("maxDropCm"), MaxDropCm, MaxStepCm, 100)
        || !Number(Root, TEXT("probeHeadroomCm"), ProbeHeadroomCm, 0, 20)) return false;
    const TSharedPtr<FJsonObject>* Speeds = nullptr;
    const TSharedPtr<FJsonObject>* Constants = nullptr;
    const TSharedPtr<FJsonObject>* Camera = nullptr;
    const TSharedPtr<FJsonObject>* Provenance = nullptr;
    if (!Root->TryGetObjectField(TEXT("speedsCmPerSecond"), Speeds)
        || !Number(*Speeds, TEXT("precision"), PrecisionSpeed, 1, 500)
        || !Number(*Speeds, TEXT("normal"), NormalSpeed, PrecisionSpeed, 500)
        || !Number(*Speeds, TEXT("boost"), BoostSpeed, NormalSpeed, 1000)
        || !Root->TryGetObjectField(TEXT("sourceConstants"), Constants)
        || !(*Constants)->TryGetObjectField(TEXT("WALK_CAMERA"), Camera)
        || !Number(*Camera, TEXT("accelTauS"), AccelTauSeconds, 0.01, 1)
        || !Number(*Camera, TEXT("decelTauS"), DecelTauSeconds, 0.01, 1)
        || !Number(*Camera, TEXT("maxMoveSubstepM"), MaxMoveSubstepCm, 0.001, 0.1)
        || !Root->TryGetObjectField(TEXT("provenance"), Provenance)
        || !(*Provenance)->TryGetStringField(TEXT("sceneSha256"), SceneSha256) || SceneSha256.Len() != 64
        || !(*Provenance)->TryGetStringField(TEXT("sourceObjSha256"), SourceObjSha256) || SourceObjSha256.Len() != 64) return false;
    MaxMoveSubstepCm *= 100;
    MinSupportZ = TNumericLimits<double>::Max();
    for (const TCHAR* Key : {TEXT("walkSurfaces"), TEXT("staticBlockers"), TEXT("capturedClosedBlockers")})
    {
        const TArray<TSharedPtr<FJsonValue>>* Array = nullptr;
        if (!Root->TryGetArrayField(Key, Array) || Array->IsEmpty() || Array->Num() > 10000) return false;
        TSet<FString> Seen;
        for (const TSharedPtr<FJsonValue>& Value : *Array)
        {
            const TSharedPtr<FJsonObject>* Object = nullptr;
            FBreziWalkingRecord Record;
            Record.bFloor = FString(Key) == TEXT("walkSurfaces");
            Record.bClosed = FString(Key) == TEXT("capturedClosedBlockers");
            if (!Value->TryGetObject(Object) || !Object->IsValid()
                || !(*Object)->TryGetStringField(TEXT("objectId"), Record.ObjectId) || !Record.ObjectId.StartsWith(TEXT("DOM_")) || Seen.Contains(Record.ObjectId)) return false;
            Seen.Add(Record.ObjectId);
            const TSharedPtr<FJsonObject>* Bounds = nullptr;
            FVector Min, Max;
            if (!(*Object)->TryGetObjectField(TEXT("nativeBoundsCm"), Bounds)
                || !Vector(*Bounds, TEXT("min"), Min) || !Vector(*Bounds, TEXT("max"), Max)
                || Min.X > Max.X || Min.Y > Max.Y || Min.Z > Max.Z) return false;
            Record.BoundsCm = FBox(Min, Max);
            if (Record.bFloor)
            {
                if (!(*Object)->TryGetStringField(TEXT("walkSurfaceId"), Record.SurfaceId)
                    || !Number(*Object, TEXT("supportOffsetCm"), Record.SupportOffsetCm, -50, 50)) return false;
                ++FloorCount;
                if (!FMath::IsNearlyZero(Record.SupportOffsetCm)) ++OffsetCount;
                MinSupportZ = FMath::Min(MinSupportZ, Min.Z + Record.SupportOffsetCm);
            }
            if (Record.bClosed)
            {
                FString State;
                if (!(*Object)->TryGetStringField(TEXT("requiredState"), State) || State != TEXT("captured-closed")) return false;
                ++ClosedCount;
            }
            if (Record.bFloor || Record.bClosed)
            {
                for (const TCHAR* TagsKey : {TEXT("runtimeTags"), TEXT("supportRuntimeTags")})
                {
                    const TArray<TSharedPtr<FJsonValue>>* Tags = nullptr;
                    if (!(*Object)->TryGetArrayField(TagsKey, Tags))
                    {
                        if (FString(TagsKey) == TEXT("runtimeTags")) return false;
                        continue;
                    }
                    for (const TSharedPtr<FJsonValue>& TagValue : *Tags)
                    {
                        FString Tag;
                        if (!TagValue->TryGetString(Tag) || Tag.IsEmpty()) return false;
                        Record.RequiredTags.AddUnique(FName(*Tag));
                    }
                }
            }
            Records.Add(MoveTemp(Record));
        }
    }
    // Auxiliary navigation hulls have their own namespace and exact source contract.
    // They never become visual DOM identities or valid floor supports.
    Error = TEXT("hidden-collision.json: missing, stale or invalid source collision supplement");
    TSharedPtr<FJsonObject> Auxiliary;
    if (!FFileHelper::LoadFileToString(Text, *(FPaths::ProjectContentDir() / TEXT("Data/hidden-collision.json")))
        || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Auxiliary) || !Auxiliary.IsValid()) return false;
    FString AuxiliaryScene, AuxiliaryObj, Namespace;
    const TArray<TSharedPtr<FJsonValue>>* Objects = nullptr;
    if (!Number(Auxiliary, TEXT("schemaVersion"), Schema, 1, 1)
        || !Auxiliary->TryGetStringField(TEXT("coordinateSystem"), Coordinates) || Coordinates != TEXT("unreal-centimeters")
        || !Auxiliary->TryGetStringField(TEXT("sourceManifestSha256"), AuxiliaryScene) || AuxiliaryScene != SceneSha256
        || !Auxiliary->TryGetStringField(TEXT("mainObjSha256"), AuxiliaryObj) || AuxiliaryObj != SourceObjSha256
        || !Auxiliary->TryGetStringField(TEXT("namespace"), Namespace) || Namespace != TEXT("COLL_")
        || !Auxiliary->TryGetArrayField(TEXT("objects"), Objects) || Objects->IsEmpty() || Objects->Num() > 10000) return false;
    TSet<FString> AuxiliaryIds, SourceIds;
    for (const TSharedPtr<FJsonValue>& Value : *Objects)
    {
        const TSharedPtr<FJsonObject>* Object = nullptr;
        const TSharedPtr<FJsonObject>* Bounds = nullptr;
        const TArray<TSharedPtr<FJsonValue>>* Tags = nullptr;
        FBreziWalkingRecord Record;
        Record.bAuxiliary = true;
        FString SourceId, Role;
        FVector Min, Max;
        if (!Value->TryGetObject(Object) || !Object->IsValid()
            || !(*Object)->TryGetStringField(TEXT("id"), Record.ObjectId) || !IsAuxiliaryId(Record.ObjectId)
            || AuxiliaryIds.Contains(Record.ObjectId)
            || !(*Object)->TryGetStringField(TEXT("sourceId"), SourceId) || SourceId.IsEmpty() || SourceIds.Contains(SourceId)
            || !(*Object)->TryGetStringField(TEXT("nativeRole"), Role) || Role != TEXT("blocking-only-never-a-floor")
            || !(*Object)->TryGetObjectField(TEXT("nativeBoundsCm"), Bounds)
            || !Vector(*Bounds, TEXT("min"), Min) || !Vector(*Bounds, TEXT("max"), Max)
            || Min.X >= Max.X || Min.Y >= Max.Y || Min.Z >= Max.Z
            || !(*Object)->TryGetArrayField(TEXT("runtimeTags"), Tags) || Tags->Num() > 32) return false;
        AuxiliaryIds.Add(Record.ObjectId);
        SourceIds.Add(SourceId);
        Record.BoundsCm = FBox(Min, Max);
        for (const TSharedPtr<FJsonValue>& TagValue : *Tags)
        {
            FString Tag;
            if (!TagValue->TryGetString(Tag) || Tag.IsEmpty() || Tag.StartsWith(TEXT("BreziWalkSurface"))) return false;
            Record.RequiredTags.AddUnique(FName(*Tag));
        }
        for (const FString& Required : {FString(TEXT("BreziHiddenCollision")),
            FString(TEXT("BreziSourceObjectId=")) + Record.ObjectId, FString(TEXT("BreziSourceId=")) + SourceId})
            if (!Record.RequiredTags.Contains(FName(*Required))) return false;
        ++AuxiliaryCount;
        Records.Add(MoveTemp(Record));
    }
    Error.Empty();
    return FloorCount > 0 && FMath::IsFinite(MinSupportZ);
}

bool FBreziWalkingContract::ValidateWorld(UWorld* World, TArray<FString>& Errors) const
{
    Errors.Reset();
    if (!World || Records.IsEmpty()) { Errors.Add(TEXT("No loaded walking contract/world")); return false; }
    TMap<FString, TArray<UPrimitiveComponent*>> ById;
    TSet<FString> ExpectedAuxiliaryIds;
    for (const FBreziWalkingRecord& Record : Records)
        if (Record.bAuxiliary) ExpectedAuxiliaryIds.Add(Record.ObjectId);
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        TArray<UPrimitiveComponent*> Components;
        It->GetComponents(Components);
        for (UPrimitiveComponent* Component : Components)
        {
            const FString Id = ObjectId(Component);
            if ((HasTag(Component, TEXT("BreziHiddenCollision")) || Id.StartsWith(TEXT("COLL_")))
                && !ExpectedAuxiliaryIds.Contains(Id))
                Errors.Add(FString::Printf(TEXT("%s: unregistered auxiliary source collision component"), *Component->GetPathName()));
            if (!Id.IsEmpty()) ById.FindOrAdd(Id).Add(Component);
        }
    }
    for (const FBreziWalkingRecord& Record : Records)
    {
        int32 Matching = 0;
        const TArray<UPrimitiveComponent*>* Components = ById.Find(Record.ObjectId);
        if (Components) for (UPrimitiveComponent* Component : *Components)
        {
            if (!BlocksWalker(Component) || (Record.bFloor && !IsFloor(Component))) continue;
            if (Record.bAuxiliary && !IsHiddenSourceCollider(Component)) continue;
            bool bTags = true;
            for (const FName& Tag : Record.RequiredTags) bTags &= HasTag(Component, Tag);
            if (!bTags) continue;
            // Catch incorrect support offsets and moved/opened captured blockers. Bounds are integration
            // evidence, never substitute collision geometry or a complete test of every door transform.
            const FBox Expected = Record.BoundsCm.ShiftBy(FVector(0, 0, Record.bFloor ? Record.SupportOffsetCm : 0));
            const FBox Actual = Component->CalcBounds(Component->GetComponentTransform()).GetBox();
            if (!Actual.Min.Equals(Expected.Min, 0.02) || !Actual.Max.Equals(Expected.Max, 0.02)) continue;
            ++Matching;
        }
        if (Matching == 0 || ((Record.bFloor || Record.bAuxiliary) && Matching != 1)
            || (Record.bAuxiliary && Components && Components->Num() != 1))
            Errors.Add(FString::Printf(TEXT("%s: %s requires %s matching query collider (found %d)"), *Record.ObjectId,
                Record.bFloor ? TEXT("floor/tags/offset") : Record.bAuxiliary ? TEXT("hidden source blocker/profile/triangles/tags/bounds")
                    : Record.bClosed ? TEXT("captured-closed blocker/tags/bounds") : TEXT("static blocker/bounds"),
                (Record.bFloor || Record.bAuxiliary) ? TEXT("exactly one") : TEXT("at least one"), Matching));
    }
    return Errors.IsEmpty();
}
