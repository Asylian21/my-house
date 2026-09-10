#include "BreziCharacterMovementComponent.h"
#include "BreziWalkingContract.h"
#include "BreziPawn.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"

UBreziCharacterMovementComponent::UBreziCharacterMovementComponent()
{
    bTickBeforeOwner = false; // The pawn explicitly orders movement after its input tick.
    DefaultLandMovementMode = MOVE_None;
    DefaultWaterMovementMode = MOVE_None;
    bOrientRotationToMovement = false;
    bUseControllerDesiredRotation = false;
    bEnablePhysicsInteraction = false;
    bCanWalkOffLedges = true; // The override permits only a verified, bounded landing.
    bCanWalkOffLedgesWhenCrouching = false;
    AirControl = 0;
    AirControlBoostMultiplier = 0;
    GroundFriction = 8;
    bUseSeparateBrakingFriction = true;
    BrakingFriction = 0;
    BrakingFrictionFactor = 1;
    SetWalkableFloorAngle(45); // Native slope cap; semantic source-floor membership is mandatory as well.
    MaxSimulationIterations = 16;
    NavAgentProps.bCanJump = false;
    NavAgentProps.bCanCrouch = false;
    NavAgentProps.bCanSwim = false;
    NavAgentProps.bCanFly = false;
}

void UBreziCharacterMovementComponent::Configure(const FBreziWalkingContract& Contract)
{
    MaxStepHeight = Contract.MaxStepCm;
    MaxDropCm = Contract.MaxDropCm;
    AccelTauSeconds = Contract.AccelTauSeconds;
    DecelTauSeconds = Contract.DecelTauSeconds;
    MaxSimulationTimeStep = FMath::Clamp(Contract.MaxMoveSubstepCm / Contract.BoostSpeed, 0.001, 0.05);
    SetWalkingSpeed(Contract.NormalSpeed);
}

void UBreziCharacterMovementComponent::SetWalkingSpeed(double Speed)
{
    MaxWalkSpeed = Speed;
    MaxAcceleration = Speed / AccelTauSeconds;
    BrakingDecelerationWalking = Speed / DecelTauSeconds;
}

bool UBreziCharacterMovementComponent::IsWalkable(const FHitResult& Hit) const
{
    if (!FBreziWalkingContract::IsFloor(Hit.GetComponent()))
    {
        if (Hit.IsValidBlockingHit()) ++RejectedFloorHitCount;
        return false;
    }
    return Super::IsWalkable(Hit);
}

bool UBreziCharacterMovementComponent::CanStepUp(const FHitResult& Hit) const
{
    return FBreziWalkingContract::IsFloor(Hit.GetComponent()) && Super::CanStepUp(Hit);
}

bool UBreziCharacterMovementComponent::ProbeSupport(const FVector& Center, double Distance, FFindFloorResult& Floor) const
{
    ++SupportQueryCount;
    Floor.Clear();
    if (!CharacterOwner || !UpdatedComponent || Distance <= 0) return false;
    ComputeFloorDist(Center, Distance, Distance, Floor, CharacterOwner->GetCapsuleComponent()->GetScaledCapsuleRadius());
    return Floor.IsWalkableFloor() && !Floor.HitResult.bStartPenetrating;
}

double UBreziCharacterMovementComponent::SupportHeight(const FVector& Center, const FFindFloorResult& Floor) const
{
    return Center.Z - CharacterOwner->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - Floor.GetDistanceToFloor();
}

void UBreziCharacterMovementComponent::AdoptValidatedFloor(const FFindFloorResult& Floor)
{
    CurrentFloor = Floor;
    PreviousSupportZ = SupportHeight(UpdatedComponent->GetComponentLocation(), Floor);
    bHavePreviousSupport = true;
    SetBaseFromFloor(Floor);
    bForceNextFloorCheck = true;
}

bool UBreziCharacterMovementComponent::HasBoundedLanding(double OldSupportZ) const
{
    if (!UpdatedComponent || MaxDropCm <= 0) return false;
    const FVector Center = UpdatedComponent->GetComponentLocation();
    FFindFloorResult Landing;
    if (!ProbeSupport(Center, MaxDropCm + MAX_FLOOR_DIST * 2, Landing)) return false;
    const double Drop = OldSupportZ - SupportHeight(Center, Landing);
    return Drop >= -MaxStepHeight - MAX_FLOOR_DIST && Drop <= MaxDropCm + 0.01;
}

bool UBreziCharacterMovementComponent::CanWalkOffLedges() const
{
    return bHavePreviousSupport && Super::CanWalkOffLedges() && HasBoundedLanding(PreviousSupportZ);
}

void UBreziCharacterMovementComponent::MoveAlongFloor(const FVector& InVelocity, float DeltaSeconds, FStepDownResult* OutStepDownResult)
{
    if (CurrentFloor.IsWalkableFloor())
    {
        PreviousSupportZ = SupportHeight(UpdatedComponent->GetComponentLocation(), CurrentFloor);
        bHavePreviousSupport = true;
    }
    Super::MoveAlongFloor(InVelocity, DeltaSeconds, OutStepDownResult);
}

bool UBreziCharacterMovementComponent::CheckFall(const FFindFloorResult& OldFloor, const FHitResult& Hit, const FVector& Delta,
    const FVector& OldLocation, float RemainingTime, float TimeTick, int32 Iterations, bool bMustJump)
{
    const double OldSupportZ = OldFloor.IsWalkableFloor() ? SupportHeight(OldLocation, OldFloor) : PreviousSupportZ;
    if (!HasBoundedLanding(OldSupportZ))
    {
        ++RejectedDropCount;
        return false; // PhysWalking retains its ordinary ledge slide/revert behavior.
    }
    // A permitted step-down is vertical and bounded. It is not a jump, swimming, or air-controlled flight.
    // Stopping lateral velocity keeps a landing validated at this XY from becoming invalid in mid-air.
    Velocity.X = 0;
    Velocity.Y = 0;
    ++ControlledDropCount;
    return Super::CheckFall(OldFloor, Hit, Delta, OldLocation, RemainingTime, TimeTick, Iterations, true);
}

void UBreziCharacterMovementComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    // UE's final substep otherwise consumes all remaining time even when it exceeds the step limit.
    // This local single-player viewer discards a long stall instead of moving metres after a UI pause.
    const float BoundedDelta = FMath::Min(DeltaTime, MaxSimulationTimeStep * MaxSimulationIterations);
    DiscardedHitchSeconds += FMath::Max(0.0f, DeltaTime - BoundedDelta);
    Super::TickComponent(BoundedDelta, TickType, ThisTickFunction);
    if (ABreziPawn* Pawn = Cast<ABreziPawn>(CharacterOwner)) Pawn->UpdateWalkingCamera(BoundedDelta);
}
