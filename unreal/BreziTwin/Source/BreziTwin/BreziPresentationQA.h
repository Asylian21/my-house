#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "BreziPresentationQA.generated.h"

class ABreziPlayerController;
class ABreziPawn;
class FJsonObject;
class FJsonValue;
class UPrimitiveComponent;

// An observer and bounded zoom prelude inside the existing validated walking
// harness. It never moves the capsule, captures the OS pointer or creates a route.
UCLASS()
class UBreziPresentationQA : public UObject
{
    GENERATED_BODY()
public:
    bool Begin(ABreziPlayerController* Controller);
    // True means the prelude is complete; inspect HasFailed before continuing.
    bool TickStartup(float DeltaSeconds);
    bool Sample();
    bool Finish();
    bool HasFailed() const { return !Failure.IsEmpty(); }
    const FString& GetFailure() const { return Failure; }
    TSharedRef<FJsonObject> GetDiagnostics() const;

private:
    bool Fail(const FString& Reason);
    bool SendZoomEvent(int32 Index);
    ABreziPawn* Pawn() const;
    TWeakObjectPtr<ABreziPlayerController> OwnerController;
    FString Failure;
    bool bStarted = false;
    bool bStartupComplete = false;
    bool bFinished = false;
    int32 EventIndex = 0;
    double PhaseSeconds = 0;
    double StartupSeconds = 0;
    double InitialZoomCm = 0;
    FVector InitialCapsule = FVector::ZeroVector;
    int64 Samples = 0;
    int64 VisibleRigSamples = 0;
    int64 IdlePoseChanges = 0;
    int64 WalkingPoseChanges = 0;
    int64 ObstructedSamples = 0;
    int64 NavigationProxyBypassSamples = 0;
    TArray<TWeakObjectPtr<UPrimitiveComponent>> IndependentNavigationProxies;
    bool bPriorVisibilityTarget = true;
    double FractionalOpacitySeconds = 0;
    int32 BoneCount = 0;
    double MaximumCameraCacheErrorCm = 0;
    double MaximumBoomLimitErrorCm = 0;
    double MaximumIdleBoneAngle = 0;
    double MaximumWalkingBoneAngle = 0;
    TArray<FTransform> PriorPose;
    TArray<TSharedPtr<FJsonValue>> Events;
};
