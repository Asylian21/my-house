#include "BreziDoors.h"
#include "BreziDoubleGlassActor.h"
#include "BreziPawn.h"
#include "BreziDoorSelectionPolicy.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "PhysicsEngine/BodySetup.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    TArray<TWeakObjectPtr<UBreziDoors>> Systems;

    bool Number(const TSharedPtr<FJsonObject>& O, const TCHAR* Key, double& V, double Min, double Max)
    {
        return O.IsValid() && O->TryGetNumberField(Key, V) && FMath::IsFinite(V) && V >= Min && V <= Max;
    }

    bool Vector(const TSharedPtr<FJsonObject>& O, const TCHAR* Key, FVector& V)
    {
        const TArray<TSharedPtr<FJsonValue>>* A = nullptr;
        if (!O.IsValid() || !O->TryGetArrayField(Key, A) || A->Num() != 3) return false;
        double N[3];
        for (int32 I = 0; I < 3; ++I) if (!(*A)[I]->TryGetNumber(N[I]) || !FMath::IsFinite(N[I])) return false;
        V = FVector(N[0], N[1], N[2]);
        return true;
    }

    bool ReadPoses(const TSharedPtr<FJsonObject>& O, const TCHAR* Key, int32 Count, TArray<FTransform>& Out)
    {
        const TArray<TSharedPtr<FJsonValue>>* A = nullptr;
        if (!O->TryGetArrayField(Key, A) || A->Num() != Count) return false;
        for (const auto& Value : *A)
        {
            const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
            if (!Value->TryGetArray(Values) || Values->Num() != 16) return false;
            FMatrix M;
            for (int32 I = 0; I < 16; ++I)
            {
                double N = 0;
                if (!(*Values)[I]->TryGetNumber(N) || !FMath::IsFinite(N)) return false;
                M.M[I / 4][I % 4] = N;
            }
            if (!FMath::IsNearlyZero(M.M[0][3], 1.e-6) || !FMath::IsNearlyZero(M.M[1][3], 1.e-6)
                || !FMath::IsNearlyZero(M.M[2][3], 1.e-6) || !FMath::IsNearlyEqual(M.M[3][3], 1., 1.e-6)
                || !FMath::IsNearlyEqual(M.Determinant(), 1., .0002)) return false;
            for (int32 I = 0; I < 3; ++I) for (int32 J = 0; J < 3; ++J)
                if (!FMath::IsNearlyEqual(FVector::DotProduct(M.GetScaledAxis(static_cast<EAxis::Type>(I + 1)),
                    M.GetScaledAxis(static_cast<EAxis::Type>(J + 1))), double(I == J), .0002)) return false;
            FTransform Pose(M);
            Pose.NormalizeRotation();
            if (Pose.ContainsNaN() || !Pose.GetScale3D().Equals(FVector::OneVector, .0002)) return false;
            Out.Add(Pose);
        }
        return true;
    }

    TArray<TSharedPtr<FJsonValue>> JsonVector(const FVector& P)
    {
        return {MakeShared<FJsonValueNumber>(P.X), MakeShared<FJsonValueNumber>(P.Y), MakeShared<FJsonValueNumber>(P.Z)};
    }

    double Smooth(double T) { return T * T * T * (T * (6 * T - 15) + 10); }
    double Handle(double T) { return T < .42 ? FMath::Sin(PI * T / .42) : 0.; }
}

bool UBreziDoors::Initialize(UWorld* InWorld)
{
    Shutdown();
    Error = TEXT("doors.json: missing, stale or invalid source motion/bindings");
    DoorWorld = InWorld;
    if (!InWorld) return false;
    TArray<uint8> Bytes;
    FString Text;
    TSharedPtr<FJsonObject> Root;
    const FString Path = FPaths::ProjectContentDir() / TEXT("Data/doors.json");
    if (!FFileHelper::LoadFileToArray(Bytes, *Path) || Bytes.IsEmpty() || Bytes.Num() > 64 * 1024 * 1024) return false;
    FSHAHash Hash;
    FSHA1::HashBuffer(Bytes.GetData(), Bytes.Num(), Hash.Hash);
    ContractSha1 = Hash.ToString().ToLower();
    FFileHelper::BufferToString(Text, Bytes.GetData(), Bytes.Num());
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Root) || !Root.IsValid()) return false;
    FString Status, Coordinates, Initial;
    double Schema = 0;
    if (!Number(Root, TEXT("schemaVersion"), Schema, 1, 1)
        || !Root->TryGetStringField(TEXT("status"), Status) || Status != TEXT("source-door-motion-validated")
        || !Root->TryGetStringField(TEXT("coordinateSystem"), Coordinates) || Coordinates != TEXT("UNREAL_XY_Z_CM")
        || !Root->TryGetStringField(TEXT("initialState"), Initial) || Initial != TEXT("CLOSED")
        || !Root->TryGetStringField(TEXT("sourceManifestSha256"), SourceManifestSha256) || SourceManifestSha256.Len() != 64) return false;
    const TArray<TSharedPtr<FJsonValue>>* Progress = nullptr;
    if (!Root->TryGetArrayField(TEXT("progressSamples"), Progress) || Progress->Num() < 129 || Progress->Num() > 1024) return false;
    for (const auto& V : *Progress)
    {
        double N = 0;
        if (!V->TryGetNumber(N) || !FMath::IsFinite(N) || N < 0 || N > 1 || (!Samples.IsEmpty() && N <= Samples.Last())) return false;
        Samples.Add(N);
    }
    if (Samples[0] != 0 || Samples.Last() != 1) return false;
    const TSharedPtr<FJsonObject>* Interaction = nullptr;
    if (!Root->TryGetObjectField(TEXT("interaction"), Interaction)
        || !Number(*Interaction, TEXT("maxDistanceM"), MaxDistanceCm, .5, 3)
        || !Number(*Interaction, TEXT("nearOmnidirectionalDistanceM"), NearDistanceCm, .1, 1.5)
        || !Number(*Interaction, TEXT("minimumFacingDot"), MinimumFacingDot, -1, 1)
        || !Number(*Interaction, TEXT("leafClearancePaddingM"), PaddingCm, 0, .15)
        || !Number(*Interaction, TEXT("maximumFrameStepMs"), MaxFrameSeconds, 1, 100)
        || !Number(*Interaction, TEXT("minimumReversalDurationMs"), MinimumReversalSeconds, 50, 1000)
        || !Number(*Interaction, TEXT("blockedMessageMs"), BlockedMessageSeconds, 100, 10000)) return false;
    MaxDistanceCm *= 100; NearDistanceCm *= 100; PaddingCm *= 100;
    MaxFrameSeconds /= 1000; MinimumReversalSeconds /= 1000; BlockedMessageSeconds /= 1000;
    TMap<FString, AActor*> Actors;
    const FName DigestTag(*FString(TEXT("BreziDoorContractSha1=") + ContractSha1));
    for (TActorIterator<AActor> It(InWorld); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("BreziDoorMovable"))) continue;
        if (!It->ActorHasTag(DigestTag)) { Error = TEXT("Door map binding differs from doors.json"); return false; }
        for (const FName& Tag : It->Tags)
        {
            const FString Name = Tag.ToString();
            if (!Name.StartsWith(TEXT("BreziDoorMember="))) continue;
            if (Actors.Contains(Name)) { Error = TEXT("Duplicate stable door member binding"); return false; }
            Actors.Add(Name, *It);
        }
    }
    const TArray<TSharedPtr<FJsonValue>>* Records = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Inventory = nullptr;
    if (!Root->TryGetArrayField(TEXT("doors"), Records) || Records->IsEmpty() || Records->Num() > 64
        || !Root->TryGetArrayField(TEXT("architecturalInventory"), Inventory)) return false;
    TSet<FString> Ids, Bound, Architectural;
    for (const auto& Value : *Records)
    {
        const TSharedPtr<FJsonObject>* O = nullptr;
        FBreziAnimatedDoor Door;
        if (!Value->TryGetObject(O) || !(*O)->TryGetStringField(TEXT("id"), Door.Id) || Door.Id.IsEmpty() || Ids.Contains(Door.Id)
            || !(*O)->TryGetStringField(TEXT("label"), Door.Label) || !(*O)->TryGetStringField(TEXT("kind"), Door.Kind)
            || (Door.Kind != TEXT("HINGED") && Door.Kind != TEXT("SLIDING") && Door.Kind != TEXT("OVERHEAD"))
            || !(*O)->TryGetStringField(TEXT("subject"), Door.Subject) || !(*O)->TryGetBoolField(TEXT("architectural"), Door.bArchitectural)
            || !Vector(*O, TEXT("interactionPointCm"), Door.InteractionPoint)
            || !Number(*O, TEXT("openingSeconds"), Door.OpeningSeconds, .1, 10)
            || !Number(*O, TEXT("closingSeconds"), Door.ClosingSeconds, .1, 10)) return false;
        Ids.Add(Door.Id);
        if (Door.bArchitectural) Architectural.Add(Door.Id);
        const TArray<TSharedPtr<FJsonValue>>* Members = nullptr;
        if (!(*O)->TryGetArrayField(TEXT("members"), Members) || Members->IsEmpty() || Members->Num() > 100) return false;
        for (const auto& MemberValue : *Members)
        {
            const TSharedPtr<FJsonObject>* M = nullptr;
            FString Tag;
            bool bHidden = false;
            FBreziDoorMember Member;
            const TSharedPtr<FJsonObject>* Bounds = nullptr;
            FVector Min, Max;
            if (!MemberValue->TryGetObject(M) || !(*M)->TryGetStringField(TEXT("runtimeTag"), Tag) || !Actors.Contains(Tag) || Bound.Contains(Tag)
                || !(*M)->TryGetStringField(TEXT("sourceId"), Member.SourceId) || !(*M)->TryGetBoolField(TEXT("collision"), Member.bCollision)
                || !(*M)->TryGetBoolField(TEXT("hidden"), bHidden) || !(*M)->TryGetObjectField(TEXT("closedBoundsCm"), Bounds)
                || !Vector(*Bounds, TEXT("min"), Min) || !Vector(*Bounds, TEXT("max"), Max)
                || Min.X > Max.X || Min.Y > Max.Y || Min.Z > Max.Z
                || !ReadPoses(*M, TEXT("poses"), Samples.Num(), Member.Poses)
                || !ReadPoses(*M, TEXT("handlePoses"), Samples.Num(), Member.HandlePoses)
                || !Member.Poses[0].Equals(FTransform::Identity, .002)) return false;
            AActor* Actor = Actors[Tag];
            TArray<UStaticMeshComponent*> Components;
            Actor->GetComponents(Components);
            if (Components.Num() != 1 || !Actor->ActorHasTag(FName(*FString(TEXT("BreziDoorId=") + Door.Id)))) return false;
            UStaticMeshComponent* Component = Components[0];
            const UStaticMesh* Mesh = Component->GetStaticMesh();
            const UBodySetup* Body = Mesh ? Mesh->GetBodySetup() : nullptr;
            if (!Mesh || !Component->ComponentHasTag(FName(*Tag)) || Component->Mobility != EComponentMobility::Movable
                || Component->IsVisible() == bHidden || Component->IsQueryCollisionEnabled() != Member.bCollision
                || (Member.bCollision && (!Body || Body->GetCollisionTraceFlag() != CTF_UseComplexAsSimple
                    || Component->GetCollisionResponseToChannel(ECC_Pawn) != ECR_Block))) return false;
            Member.ClosedBounds = FBox(Min, Max);
            const FBox Actual = Component->Bounds.GetBox();
            if (!Actual.Min.Equals(Min, .05) || !Actual.Max.Equals(Max, .05))
            { Error = TEXT("Door is not at its verified source closed pose: ") + Door.Id; return false; }
            Member.Component = Component;
            Member.RestTransform = Component->GetComponentTransform();
            Member.MeshBounds = Mesh->GetBoundingBox();
            Bound.Add(Tag);
            Door.Members.Add(MoveTemp(Member));
        }
        Doors.Add(MoveTemp(Door));
    }
    if (Bound.Num() != Actors.Num() || Architectural.Num() != Inventory->Num()) return false;
    for (const auto& V : *Inventory)
    {
        const TSharedPtr<FJsonObject>* O = nullptr;
        FString Id;
        if (!V->TryGetObject(O) || !(*O)->TryGetStringField(TEXT("id"), Id) || !Architectural.Contains(Id)) return false;
    }
    Error.Empty(); bReady = true;
    Systems.AddUnique(this);
    return true;
}

UBreziDoors* UBreziDoors::FindForWorld(const UWorld* InWorld)
{
    for (const auto& System : Systems) if (System.IsValid() && System->bReady && System->DoorWorld.Get() == InWorld) return System.Get();
    return nullptr;
}

bool UBreziDoors::GetClosedBounds(const UPrimitiveComponent* Component, FBox& OutBounds) const
{
    if (!bReady || !Component) return false;
    for (const auto& Door : Doors) for (const auto& Member : Door.Members)
        if (Member.Component.Get() == Component) { OutBounds = Member.ClosedBounds; return true; }
    return false;
}

FTransform UBreziDoors::PoseAt(const FBreziDoorMember& Member, double Progress, double Depression) const
{
    int32 Upper = 1;
    while (Upper < Samples.Num() - 1 && Samples[Upper] < Progress) ++Upper;
    const int32 Lower = Upper - 1;
    const double Alpha = FMath::Clamp((Progress - Samples[Lower]) / (Samples[Upper] - Samples[Lower]), 0., 1.);
    FTransform Leaf, HandlePose, Result;
    Leaf.Blend(Member.Poses[Lower], Member.Poses[Upper], Alpha);
    HandlePose.Blend(Member.HandlePoses[Lower], Member.HandlePoses[Upper], Alpha);
    Result.Blend(Leaf, HandlePose, FMath::Clamp(Depression, 0., 1.));
    return Member.RestTransform * Result;
}

bool UBreziDoors::WouldHitPlayer(const FBreziAnimatedDoor& Door, double Progress, double Depression) const
{
    const APawn* Pawn = Player.IsValid() ? Player->GetPawn() : nullptr;
    const UCapsuleComponent* Capsule = Pawn ? Pawn->FindComponentByClass<UCapsuleComponent>() : nullptr;
    if (!Capsule) return false;
    const double Radius = Capsule->GetScaledCapsuleRadius() + PaddingCm;
    const double Shaft = FMath::Max(0., double(Capsule->GetScaledCapsuleHalfHeight() - Capsule->GetScaledCapsuleRadius()));
    const FVector Center = Capsule->GetComponentLocation();
    const FVector Axis = Capsule->GetUpVector() * Shaft;
    for (const auto& Member : Door.Members)
    {
        if (!Member.bCollision || !Member.Component.IsValid()) continue;
        const FTransform Next = PoseAt(Member, Progress, Depression);
        const FVector Scale = Next.GetScale3D().GetAbs();
        const double SmallestScale = FMath::Max(.0001, FMath::Min3(Scale.X, Scale.Y, Scale.Z));
        // An expanded local box is conservative for the source triangles. The
        // capsule segment avoids the false diagonal collisions of world AABBs.
        const FBox Envelope = Member.MeshBounds.ExpandBy(Radius / SmallestScale);
        const FVector A = Next.InverseTransformPosition(Center - Axis);
        const FVector B = Next.InverseTransformPosition(Center + Axis);
        if (Envelope.IsInsideOrOn(A) || Envelope.IsInsideOrOn(B) || FMath::LineBoxIntersection(Envelope, A, B, B - A)) return true;
    }
    return false;
}

void UBreziDoors::Tick(float DeltaSeconds, APlayerController* Controller)
{
    if (!bReady || !DoorWorld.IsValid()) return;
    Player = Controller;
    const double Step = FMath::Clamp(double(DeltaSeconds), 0., MaxFrameSeconds);
    Clock += Step;
    bool bSceneChanged = false;
    for (auto& Door : Doors)
    {
        if (Door.Duration <= 0) continue;
        const double Elapsed = FMath::Min(Door.Duration, Door.Elapsed + Step);
        const double T = Elapsed / Door.Duration;
        const double Progress = FMath::Lerp(Door.StartProgress, Door.TargetProgress, Smooth(T));
        const double Depression = Handle(T);
        if (WouldHitPlayer(Door, Progress, Depression)) { Door.BlockedUntil = Clock + BlockedMessageSeconds; continue; }
        Door.Elapsed = Elapsed; Door.Progress = Progress;
        bSceneChanged = true;
        for (const auto& Member : Door.Members)
            if (Member.Component.IsValid()) Member.Component->SetWorldTransform(PoseAt(Member, Progress, Depression), false, nullptr, ETeleportType::TeleportPhysics);
        if (Elapsed >= Door.Duration) { Door.Duration = 0; Door.Progress = Door.TargetProgress; }
    }
    if (bSceneChanged) ABreziDoubleGlassActor::InvalidateScene(DoorWorld.Get());
    UpdateTarget(Controller);
}

void UBreziDoors::UpdateTarget(APlayerController* Controller)
{
    Selected = INDEX_NONE;
    const APawn* Pawn = Controller ? Controller->GetPawn() : nullptr;
    if (!Pawn || !DoorWorld.IsValid()) return;
    FVector Eye; FRotator ViewRotation;
    if (const ABreziPawn* Twin = Cast<ABreziPawn>(Pawn)) Twin->GetInteractionView(Eye, ViewRotation);
    else Controller->GetPlayerViewPoint(Eye, ViewRotation);
    const FVector Forward = ViewRotation.Vector().GetSafeNormal2D();
    const FVector Position = Pawn->GetActorLocation();
    double Best = TNumericLimits<double>::Max();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziDoorSelection), true, Pawn);
    for (int32 I = 0; I < Doors.Num(); ++I)
    {
        const auto& Door = Doors[I];
        const FVector Delta = Door.InteractionPoint - Position;
        const double Distance = Delta.Size2D();
        if (Distance > MaxDistanceCm || FMath::Abs(Delta.Z) > 220) continue;
        const double Dot = FVector::DotProduct(Forward, Delta.GetSafeNormal2D());
        if (Distance > NearDistanceCm && Dot < MinimumFacingDot) continue;
        const FName DoorTag(*FString(TEXT("BreziDoorId=") + Door.Id));
        const auto Visible = [&](const FVector& Point)
        {
            FHitResult Hit;
            return !DoorWorld->LineTraceSingleByChannel(Hit, Eye, Point, ECC_Visibility, Params)
                || (Hit.GetActor() && Hit.GetActor()->ActorHasTag(DoorTag));
        };
        bool bVisible = Visible(Door.InteractionPoint);
        // HS interaction points lie on the center mullion. From the exterior,
        // its fixed pane can cover that point while the movable sash is visible.
        // A second ray into an actual closed leaf keeps both sides usable and
        // still rejects doors hidden behind room walls.
        if (!bVisible) for (const auto& Member : Door.Members)
        {
            if (Member.bCollision && Visible(Member.ClosedBounds.GetCenter())) { bVisible = true; break; }
        }
        if (!bVisible) continue;
        const FVector ViewDirection = ViewRotation.Vector();
        const FVector EyeToTarget = Door.InteractionPoint - Eye;
        const bool bSpatialAim = Door.Subject == TEXT("APPLIANCE_DOOR") || Door.Subject == TEXT("ACCESS_HATCH");
        const double Score = BreziDoorSelection::Score(Distance, Dot, bSpatialAim,
            {ViewDirection.X, ViewDirection.Y, ViewDirection.Z}, {EyeToTarget.X, EyeToTarget.Y, EyeToTarget.Z});
        if (Score < Best) { Best = Score; Selected = I; }
    }
}

bool UBreziDoors::BeginMotion(FBreziAnimatedDoor& Door, bool bOpen)
{
    const double Target = bOpen ? 1. : 0.;
    if (FMath::IsNearlyEqual(Door.TargetProgress, Target) && (Door.Duration > 0 || FMath::IsNearlyEqual(Door.Progress, Target))) return false;
    Door.StartProgress = Door.Progress; Door.TargetProgress = Target; Door.Elapsed = 0;
    Door.Duration = FMath::Max(MinimumReversalSeconds, (bOpen ? Door.OpeningSeconds : Door.ClosingSeconds) * FMath::Abs(Target - Door.Progress));
    Door.BlockedUntil = 0;
    return true;
}

bool UBreziDoors::SetOpen(const FString& DoorId, bool bOpen)
{
    if (!bReady) return false;
    for (auto& Door : Doors) if (Door.Id == DoorId)
    {
        const double Target = bOpen ? 1. : 0.;
        if (FMath::IsNearlyEqual(Door.TargetProgress, Target)
            && (Door.Duration > 0 || FMath::IsNearlyEqual(Door.Progress, Target))) return true;
        return BeginMotion(Door, bOpen);
    }
    return false;
}

bool UBreziDoors::Interact()
{
    if (!bReady || !Player.IsValid()) return false;
    UpdateTarget(Player.Get());
    if (!Doors.IsValidIndex(Selected)) return false;
    return BeginMotion(Doors[Selected], Doors[Selected].TargetProgress < .5);
}

FText UBreziDoors::GetPrompt() const
{
    if (!bReady || !Doors.IsValidIndex(Selected)) return FText::GetEmpty();
    const auto& Door = Doors[Selected];
    if (Door.BlockedUntil > Clock) return FText::FromString(TEXT("Ustúpte z dráhy dverí · E zmeniť smer"));
    return FText::FromString(FString(TEXT("E · ")) + (Door.TargetProgress < .5 ? TEXT("Otvoriť ") : TEXT("Zavrieť ")) + Door.Label);
}

TSharedPtr<FJsonObject> UBreziDoors::GetDiagnostics() const
{
    auto Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("ready"), bReady);
    Result->SetStringField(TEXT("error"), Error);
    Result->SetStringField(TEXT("contractSha1"), ContractSha1);
    Result->SetStringField(TEXT("sourceManifestSha256"), SourceManifestSha256);
    Result->SetStringField(TEXT("selectedDoorId"), Doors.IsValidIndex(Selected) ? Doors[Selected].Id : FString());
    Result->SetNumberField(TEXT("doorCount"), Doors.Num());
    int32 Count = 0;
    TArray<TSharedPtr<FJsonValue>> Records;
    for (const auto& Door : Doors)
    {
        auto O = MakeShared<FJsonObject>();
        O->SetStringField(TEXT("id"), Door.Id); O->SetStringField(TEXT("label"), Door.Label);
        O->SetStringField(TEXT("kind"), Door.Kind); O->SetStringField(TEXT("subject"), Door.Subject);
        O->SetBoolField(TEXT("architectural"), Door.bArchitectural);
        O->SetNumberField(TEXT("progress"), Door.Progress); O->SetNumberField(TEXT("targetProgress"), Door.TargetProgress);
        O->SetStringField(TEXT("phase"), Door.Duration > 0 ? (Door.TargetProgress > Door.Progress ? TEXT("OPENING") : TEXT("CLOSING")) : Door.Progress > .5 ? TEXT("OPEN") : TEXT("CLOSED"));
        O->SetBoolField(TEXT("blocked"), Door.BlockedUntil > Clock);
        O->SetArrayField(TEXT("interactionPointCm"), JsonVector(Door.InteractionPoint));
        O->SetNumberField(TEXT("memberCount"), Door.Members.Num());
        Count += Door.Members.Num(); Records.Add(MakeShared<FJsonValueObject>(O));
    }
    Result->SetNumberField(TEXT("memberCount"), Count);
    Result->SetArrayField(TEXT("doors"), Records);
    return Result;
}

void UBreziDoors::Shutdown()
{
    Systems.RemoveAll([this](const auto& Item) { return !Item.IsValid() || Item.Get() == this; });
    if (bReady) for (const auto& Door : Doors) for (const auto& Member : Door.Members)
        if (Member.Component.IsValid() && !Member.Component->IsBeingDestroyed())
            Member.Component->SetWorldTransform(Member.RestTransform, false, nullptr, ETeleportType::TeleportPhysics);
    if (bReady) ABreziDoubleGlassActor::InvalidateScene(DoorWorld.Get());
    bReady = false; Selected = INDEX_NONE; Clock = 0;
    Doors.Empty(); Samples.Empty(); Player.Reset(); DoorWorld.Reset();
}
