#pragma once

#include "CoreMinimal.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "BreziCharacterMovementComponent.generated.h"

struct FBreziWalkingContract;

UCLASS()
class UBreziCharacterMovementComponent : public UCharacterMovementComponent
{
    GENERATED_BODY()
public:
    UBreziCharacterMovementComponent();
    void Configure(const FBreziWalkingContract& Contract);
    void SetWalkingSpeed(double CentimetersPerSecond);
    bool ProbeSupport(const FVector& CapsuleCenter, double DistanceCm, FFindFloorResult& OutFloor) const;
    double SupportHeight(const FVector& CapsuleCenter, const FFindFloorResult& Floor) const;
    void AdoptValidatedFloor(const FFindFloorResult& Floor);
    virtual bool IsWalkable(const FHitResult& Hit) const override;
    virtual bool CanStepUp(const FHitResult& Hit) const override;
    virtual bool CanWalkOffLedges() const override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    mutable int64 SupportQueryCount = 0;
    mutable int64 RejectedFloorHitCount = 0;
    int64 RejectedDropCount = 0;
    int64 ControlledDropCount = 0;
    double DiscardedHitchSeconds = 0;

protected:
    virtual void MoveAlongFloor(const FVector& InVelocity, float DeltaSeconds, FStepDownResult* OutStepDownResult = nullptr) override;
    virtual bool CheckFall(const FFindFloorResult& OldFloor, const FHitResult& Hit, const FVector& Delta,
        const FVector& OldLocation, float RemainingTime, float TimeTick, int32 Iterations, bool bMustJump) override;

private:
    bool HasBoundedLanding(double PreviousSupportZ) const;
    double MaxDropCm = 0;
    double AccelTauSeconds = 0.09;
    double DecelTauSeconds = 0.055;
    double PreviousSupportZ = 0;
    bool bHavePreviousSupport = false;
};
