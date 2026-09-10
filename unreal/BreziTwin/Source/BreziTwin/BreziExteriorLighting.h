#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "BreziExteriorLighting.generated.h"

class FJsonObject;
class USpotLightComponent;
class UStaticMeshComponent;

struct FBreziExteriorFixture
{
    FString Id, SourceTag, SourceName, MeshPath;
    FVector BodyCenter, Position, Direction;
    float Lumens = 0, Temperature = 0, InnerAngle = 0, OuterAngle = 0, SourceRadius = 0, AttenuationRadius = 0;
    TWeakObjectPtr<UStaticMeshComponent> Source;
};

/** Five authored local lights. No independent tick, source-actor mutation, or saved assets. */
UCLASS()
class UBreziExteriorLighting : public UActorComponent
{
    GENERATED_BODY()
public:
    UBreziExteriorLighting();
    bool Initialize();
    void SetNightAlpha(double Alpha);
    double GetNightAlpha() const { return NightAlpha; }
    TSharedRef<FJsonObject> Readback() const;
    void Shutdown();
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    bool Fail(const FString& Reason);
    bool SourceMatches(const FBreziExteriorFixture& Fixture) const;
    UPROPERTY() TObjectPtr<AActor> Carrier;
    UPROPERTY() TArray<TObjectPtr<USpotLightComponent>> Lights;
    TArray<FBreziExteriorFixture> Fixtures;
    FString ContractSha1, SceneSha256, ObjSha256, Error;
    double NightAlpha = 0;
    bool bInitialized = false;
    bool bReady = false;
};
