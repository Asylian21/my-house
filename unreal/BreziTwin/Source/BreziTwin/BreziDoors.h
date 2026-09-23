#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "BreziDoors.generated.h"

class APlayerController;
class UPrimitiveComponent;
class UStaticMeshComponent;
class FJsonObject;

struct FBreziDoorMember
{
    TWeakObjectPtr<UStaticMeshComponent> Component;
    FTransform RestTransform;
    FBox ClosedBounds;
    FBox MeshBounds;
    TArray<FTransform> Poses;
    TArray<FTransform> HandlePoses;
    FString SourceId;
    bool bCollision = false;
};

struct FBreziAnimatedDoor
{
    FString Id, Label, Kind, Subject;
    FVector InteractionPoint = FVector::ZeroVector;
    TArray<FBreziDoorMember> Members;
    bool bArchitectural = false;
    double OpeningSeconds = 0.76, ClosingSeconds = 0.68;
    double Progress = 0, StartProgress = 0, TargetProgress = 0;
    double Elapsed = 0, Duration = 0, BlockedUntil = 0;
};

/** Source-registered web motion, applied to the exact saved native members.
 * Bounds are immutable closed-pose evidence; query collision moves with leaves.
 */
UCLASS()
class UBreziDoors : public UObject
{
    GENERATED_BODY()
public:
    bool Initialize(UWorld* InWorld);
    void Tick(float DeltaSeconds, APlayerController* Controller);
    bool Interact();
    FText GetPrompt() const;
    TSharedPtr<FJsonObject> GetDiagnostics() const;
    void Shutdown();
    bool SetOpen(const FString& DoorId, bool bOpen);
    bool GetClosedBounds(const UPrimitiveComponent* Component, FBox& OutBounds) const;
    static UBreziDoors* FindForWorld(const UWorld* InWorld);

private:
    void UpdateTarget(APlayerController* Controller);
    FTransform PoseAt(const FBreziDoorMember& Member, double Progress, double Handle) const;
    bool WouldHitPlayer(const FBreziAnimatedDoor& Door, double Progress, double Handle) const;
    bool BeginMotion(FBreziAnimatedDoor& Door, bool bOpen);
    TWeakObjectPtr<UWorld> DoorWorld;
    TWeakObjectPtr<APlayerController> Player;
    TArray<FBreziAnimatedDoor> Doors;
    TArray<double> Samples;
    FString Error, ContractSha1, SourceManifestSha256;
    int32 Selected = INDEX_NONE;
    bool bReady = false;
    double Clock = 0, MaxDistanceCm = 190, NearDistanceCm = 82, MinimumFacingDot = 0.309;
    double PaddingCm = 4.5, MaxFrameSeconds = .05, MinimumReversalSeconds = .22, BlockedMessageSeconds = 1.8;
};
