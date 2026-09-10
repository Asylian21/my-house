#include "BreziExteriorLighting.h"
#include "Components/SceneComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    constexpr double BodyToleranceCm = 0.15;
    const FName CarrierTag(TEXT("BreziExteriorLightingRuntime"));
    bool VectorField(const TSharedPtr<FJsonObject>& Object, const TCHAR* Name, FVector& Out)
    {
        const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
        if (!Object->TryGetArrayField(Name, Values) || Values->Num() != 3) return false;
        double V[3];
        for (int32 I = 0; I < 3; ++I)
            if (!(*Values)[I]->TryGetNumber(V[I]) || !FMath::IsFinite(V[I])) return false;
        Out = FVector(V[0], V[1], V[2]);
        return true;
    }
    bool FloatField(const TSharedPtr<FJsonObject>& Object, const TCHAR* Name, float& Out)
    {
        double V = 0;
        if (!Object->TryGetNumberField(Name, V) || !FMath::IsFinite(V) || FMath::Abs(V) > MAX_flt) return false;
        Out = static_cast<float>(V);
        return FMath::IsFinite(Out);
    }
    bool Digest(const FString& Value)
    {
        if (Value.Len() != 64) return false;
        for (TCHAR C : Value) if (!((C >= TEXT('0') && C <= TEXT('9')) || (C >= TEXT('a') && C <= TEXT('f')))) return false;
        return true;
    }
    TArray<TSharedPtr<FJsonValue>> XYZ(const FVector& Value)
    {
        return {MakeShared<FJsonValueNumber>(Value.X), MakeShared<FJsonValueNumber>(Value.Y), MakeShared<FJsonValueNumber>(Value.Z)};
    }
}

UBreziExteriorLighting::UBreziExteriorLighting()
{
    PrimaryComponentTick.bCanEverTick = false;
}

bool UBreziExteriorLighting::Fail(const FString& Reason)
{
    Error = Reason;
    Shutdown();
    UE_LOG(LogTemp, Error, TEXT("BreziExteriorLighting rejected reason=%s"), *Error);
    return false;
}

bool UBreziExteriorLighting::SourceMatches(const FBreziExteriorFixture& Fixture) const
{
    const UStaticMeshComponent* C = Fixture.Source.Get();
    const AActor* Actor = C ? C->GetOwner() : nullptr;
    return C && Actor && Actor->GetWorld() == GetWorld() && Actor->ActorHasTag(TEXT("BreziGenerated"))
        && Actor->ActorHasTag(FName(*Fixture.SourceTag)) && !Actor->IsHidden() && C->IsRegistered() && C->IsVisible()
        && C->GetStaticMesh() && C->GetStaticMesh()->GetPathName() == Fixture.MeshPath
        && C->Bounds.Origin.Equals(Fixture.BodyCenter, BodyToleranceCm);
}

bool UBreziExteriorLighting::Initialize()
{
    check(IsInGameThread());
    if (bInitialized) return bReady;
    bInitialized = true;
    const APlayerController* Controller = Cast<APlayerController>(GetOwner());
    UWorld* World = GetWorld();
    if (!Controller || !Controller->IsLocalController() || !World || !World->IsGameWorld()) return false;

    TArray<uint8> Bytes;
    FString Text;
    const FString Path = FPaths::ProjectContentDir() / TEXT("Data/exterior-lighting.json");
    if (!FFileHelper::LoadFileToArray(Bytes, *Path) || Bytes.IsEmpty() || Bytes.Num() > 128 * 1024)
        return Fail(TEXT("missing-or-oversized-contract"));
    FSHAHash Hash; FSHA1::HashBuffer(Bytes.GetData(), Bytes.Num(), Hash.Hash); ContractSha1 = Hash.ToString().ToLower();
    FFileHelper::BufferToString(Text, Bytes.GetData(), Bytes.Num());
    TSharedPtr<FJsonObject> Json;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Json) || !Json.IsValid())
        return Fail(TEXT("malformed-contract"));
    double Schema = 0;
    FString Provenance, Coordinates;
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Json->TryGetNumberField(TEXT("schemaVersion"), Schema) || Schema != 1
        || !Json->TryGetStringField(TEXT("provenance"), Provenance) || Provenance != TEXT("AUTHORED_VISUALIZATION_PROPOSAL")
        || !Json->TryGetStringField(TEXT("coordinateSystem"), Coordinates) || Coordinates != TEXT("UNREAL_XY_Z_CM")
        || !Json->TryGetStringField(TEXT("sceneSha256"), SceneSha256) || !Digest(SceneSha256)
        || !Json->TryGetStringField(TEXT("objSha256"), ObjSha256) || !Digest(ObjSha256)
        || !Json->TryGetArrayField(TEXT("fixtures"), Rows) || Rows->Num() != 5)
        return Fail(TEXT("contract-schema"));
    TSet<FString> Expected{TEXT("EXT-TERRACE-WALL-01"), TEXT("EXT-TERRACE-WALL-02"),
        TEXT("EXT-POOL-WALL-01"), TEXT("EXT-POOL-WALL-02"), TEXT("EXT-POOL-WALL-03")};
    TSet<FString> SourceTags;
    for (const auto& Value : *Rows)
    {
        const TSharedPtr<FJsonObject>* Row = nullptr;
        FBreziExteriorFixture F;
        bool Shadows = false;
        if (!Value->TryGetObject(Row) || !Row->IsValid()
            || !(*Row)->TryGetStringField(TEXT("id"), F.Id) || Expected.Remove(F.Id) != 1
            || !(*Row)->TryGetStringField(TEXT("sourceTag"), F.SourceTag) || F.SourceTag.IsEmpty() || SourceTags.Contains(F.SourceTag)
            || !(*Row)->TryGetStringField(TEXT("sourceName"), F.SourceName) || F.SourceName.IsEmpty()
            || !(*Row)->TryGetStringField(TEXT("meshPath"), F.MeshPath) || !F.MeshPath.StartsWith(TEXT("/Game/"))
            || !VectorField(*Row, TEXT("bodyCenterCm"), F.BodyCenter) || !VectorField(*Row, TEXT("positionCm"), F.Position)
            || !VectorField(*Row, TEXT("direction"), F.Direction) || !FMath::IsNearlyEqual(F.Direction.SizeSquared(), 1.0, 0.00001)
            || !FloatField(*Row, TEXT("nominalConeLumens"), F.Lumens) || F.Lumens <= 0
            || !FloatField(*Row, TEXT("temperatureK"), F.Temperature) || F.Temperature < 1000 || F.Temperature > 15000
            || !FloatField(*Row, TEXT("innerConeHalfAngleDeg"), F.InnerAngle) || F.InnerAngle < 0
            || !FloatField(*Row, TEXT("outerConeHalfAngleDeg"), F.OuterAngle) || F.OuterAngle <= F.InnerAngle || F.OuterAngle > 88
            || !FloatField(*Row, TEXT("sourceRadiusCm"), F.SourceRadius) || F.SourceRadius < 0
            || !FloatField(*Row, TEXT("attenuationRadiusCm"), F.AttenuationRadius) || F.AttenuationRadius <= F.SourceRadius
            || !(*Row)->TryGetBoolField(TEXT("castsShadows"), Shadows) || !Shadows)
            return Fail(TEXT("invalid-or-duplicate-fixture"));
        SourceTags.Add(F.SourceTag);
        AActor* Actor = nullptr; int32 Matches = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
            if (It->ActorHasTag(FName(*F.SourceTag))) { Actor = *It; ++Matches; }
        if (Matches != 1) return Fail(TEXT("source-tag-not-unique: ") + F.Id);
        TArray<UStaticMeshComponent*> Components; Actor->GetComponents(Components);
        if (Components.Num() != 1 || Components[0]->GetClass() != UStaticMeshComponent::StaticClass())
            return Fail(TEXT("source-component-identity: ") + F.Id);
        F.Source = Components[0];
        if (!SourceMatches(F)) return Fail(TEXT("source-mesh-visibility-or-centre: ") + F.Id);
        Fixtures.Add(MoveTemp(F));
    }
    for (TActorIterator<AActor> It(World); It; ++It)
        if (It->ActorHasTag(CarrierTag)) return Fail(TEXT("runtime-light-owner-already-present"));

    FActorSpawnParameters Params;
    Params.Owner = GetOwner(); Params.ObjectFlags |= RF_Transient;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    Carrier = World->SpawnActor<AActor>(AActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
    if (!Carrier) return Fail(TEXT("carrier-spawn-failed"));
    Carrier->Tags.Add(CarrierTag); Carrier->SetActorEnableCollision(false); Carrier->SetActorTickEnabled(false);
    USceneComponent* Root = NewObject<USceneComponent>(Carrier, TEXT("ExteriorLightRoot"), RF_Transient);
    if (!Root || !Carrier->SetRootComponent(Root)) return Fail(TEXT("carrier-root-failed"));
    Carrier->AddInstanceComponent(Root); Root->SetMobility(EComponentMobility::Movable); Root->RegisterComponent();
    for (const FBreziExteriorFixture& F : Fixtures)
    {
        USpotLightComponent* Light = NewObject<USpotLightComponent>(Carrier, FName(*F.Id), RF_Transient);
        if (!Light) return Fail(TEXT("light-allocation-failed"));
        Lights.Add(Light); Carrier->AddInstanceComponent(Light); Light->SetupAttachment(Root);
        Light->SetMobility(EComponentMobility::Movable);
        Light->SetRelativeLocation(F.Position); Light->SetRelativeRotation(F.Direction.Rotation());
        Light->SetIntensityUnits(ELightUnits::Lumens); Light->SetUseInverseSquaredFalloff(true);
        Light->SetInverseExposureBlend(0); Light->SetLightColor(FLinearColor::White, false);
        Light->SetUseTemperature(true); Light->SetTemperature(F.Temperature);
        Light->SetInnerConeAngle(F.InnerAngle); Light->SetOuterConeAngle(F.OuterAngle);
        Light->SetSourceRadius(F.SourceRadius); Light->SetSourceLength(0); Light->SetSoftSourceRadius(0);
        Light->SetAttenuationRadius(F.AttenuationRadius); Light->SetCastShadows(true);
        Light->SetIntensity(0); Light->SetVisibility(false); Light->RegisterComponent();
        if (!Light->IsRegistered() || Light->GetLightUnits() != ELightUnits::Lumens || Light->Intensity != 0 || Light->IsVisible())
            return Fail(TEXT("light-registration-readback: ") + F.Id);
    }
    bReady = true;
    UE_LOG(LogTemp, Display, TEXT("BreziExteriorLighting initialized fixtures=%d contractSha1=%s nightAlpha=0"), Lights.Num(), *ContractSha1);
    return true;
}

void UBreziExteriorLighting::SetNightAlpha(double Alpha)
{
    check(IsInGameThread());
    if (!bReady) return;
    if (!FMath::IsFinite(Alpha) || Alpha < 0 || Alpha > 1) { Fail(TEXT("invalid-night-alpha")); return; }
    if (!IsValid(Carrier) || Lights.Num() != Fixtures.Num()) { Fail(TEXT("runtime-owner-lost")); return; }
    for (int32 I = 0; I < Lights.Num(); ++I)
    {
        USpotLightComponent* Light = Lights[I];
        if (!IsValid(Light) || !Light->IsRegistered() || Light->GetOwner() != Carrier || !SourceMatches(Fixtures[I]))
        { Fail(TEXT("runtime-light-or-source-lost")); return; }
        const float Intensity = static_cast<float>(Fixtures[I].Lumens * Alpha);
        Light->SetIntensity(Intensity); Light->SetVisibility(Intensity > 0);
        if (Light->Intensity != Intensity || Light->IsVisible() != (Intensity > 0))
        { Fail(TEXT("runtime-intensity-readback")); return; }
    }
    NightAlpha = Alpha;
}

TSharedRef<FJsonObject> UBreziExteriorLighting::Readback() const
{
    check(IsInGameThread());
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    bool Ready = bReady && IsValid(Carrier) && Lights.Num() == 5 && Fixtures.Num() == 5;
    J->SetBoolField(TEXT("initialized"), bInitialized); J->SetStringField(TEXT("error"), Error);
    J->SetStringField(TEXT("contractSha1"), ContractSha1); J->SetStringField(TEXT("sceneSha256"), SceneSha256);
    J->SetStringField(TEXT("objSha256"), ObjSha256); J->SetNumberField(TEXT("nightAlpha"), NightAlpha);
    J->SetBoolField(TEXT("renderThreadObserved"), false);
    J->SetStringField(TEXT("carrierPath"), GetPathNameSafe(Carrier));
    TArray<TSharedPtr<FJsonValue>> Rows;
    for (int32 I = 0; I < Fixtures.Num(); ++I)
    {
        const FBreziExteriorFixture& F = Fixtures[I];
        const USpotLightComponent* Light = Lights.IsValidIndex(I) ? Lights[I].Get() : nullptr;
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("id"), F.Id); Row->SetStringField(TEXT("sourceTag"), F.SourceTag);
        const bool ValidSource = SourceMatches(F), Present = IsValid(Light);
        Ready &= Present && ValidSource && Light->IsRegistered() && Light->GetOwner() == Carrier;
        Row->SetBoolField(TEXT("sourceMatches"), ValidSource); Row->SetBoolField(TEXT("componentPresent"), Present);
        Row->SetStringField(TEXT("sourceComponentPath"), GetPathNameSafe(F.Source.Get()));
        if (F.Source.IsValid()) Row->SetArrayField(TEXT("bodyCenterCm"), XYZ(F.Source->Bounds.Origin));
        if (Present)
        {
            Row->SetStringField(TEXT("componentPath"), Light->GetPathName());
            Row->SetBoolField(TEXT("registered"), Light->IsRegistered()); Row->SetBoolField(TEXT("visible"), Light->IsVisible());
            Row->SetArrayField(TEXT("positionCm"), XYZ(Light->GetComponentLocation())); Row->SetArrayField(TEXT("direction"), XYZ(Light->GetDirection()));
            Row->SetNumberField(TEXT("intensity"), Light->Intensity); Row->SetNumberField(TEXT("intensityUnits"), static_cast<int32>(Light->GetLightUnits()));
            Row->SetNumberField(TEXT("temperatureK"), Light->Temperature); Row->SetBoolField(TEXT("useTemperature"), Light->bUseTemperature);
            Row->SetBoolField(TEXT("inverseSquaredFalloff"), Light->bUseInverseSquaredFalloff);
            Row->SetNumberField(TEXT("inverseExposureBlend"), Light->InverseExposureBlend);
            Row->SetNumberField(TEXT("innerConeHalfAngleDeg"), Light->InnerConeAngle); Row->SetNumberField(TEXT("outerConeHalfAngleDeg"), Light->OuterConeAngle);
            Row->SetNumberField(TEXT("sourceRadiusCm"), Light->SourceRadius); Row->SetNumberField(TEXT("attenuationRadiusCm"), Light->AttenuationRadius);
            Row->SetBoolField(TEXT("castsShadows"), Light->CastShadows); Row->SetBoolField(TEXT("affectsWorld"), Light->bAffectsWorld);
            Row->SetBoolField(TEXT("hasIES"), Light->IESTexture != nullptr);
        }
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    J->SetBoolField(TEXT("ready"), Ready); J->SetArrayField(TEXT("fixtures"), Rows);
    return J;
}

void UBreziExteriorLighting::Shutdown()
{
    check(IsInGameThread());
    bReady = false; NightAlpha = 0;
    for (USpotLightComponent* Light : Lights)
        if (IsValid(Light)) { Light->SetIntensity(0); Light->SetVisibility(false); Light->DestroyComponent(); }
    const bool HadCarrier = IsValid(Carrier);
    const bool DestroyRequested = HadCarrier && Carrier->Destroy();
    Carrier = nullptr; Lights.Empty();
    if (HadCarrier) UE_LOG(LogTemp, Display, TEXT("BreziExteriorLighting shutdown ownedLightsUnregistered=1 carrierDestroyAccepted=%d renderThreadDrainedObserved=0"), DestroyRequested);
}

void UBreziExteriorLighting::EndPlay(const EEndPlayReason::Type Reason)
{
    Shutdown();
    Super::EndPlay(Reason);
}
