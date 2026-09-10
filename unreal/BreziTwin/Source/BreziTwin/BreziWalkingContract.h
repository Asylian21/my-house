#pragma once

#include "CoreMinimal.h"

class UPrimitiveComponent;
class UWorld;

struct FBreziWalkingRecord
{
    FString ObjectId;
    FString SurfaceId;
    TArray<FName> RequiredTags;
    FBox BoundsCm = FBox(ForceInit);
    double SupportOffsetCm = 0;
    bool bFloor = false;
    bool bClosed = false;
    bool bAuxiliary = false;
};

/** Runtime settings are read from the shared export; no room or parcel geometry is invented here. */
struct FBreziWalkingContract
{
    double EyeHeightCm = 0;
    double CapsuleRadiusCm = 0;
    double CapsuleHalfHeightCm = 0;
    double PrecisionSpeed = 0;
    double NormalSpeed = 0;
    double BoostSpeed = 0;
    double MaxStepCm = 0;
    double MaxDropCm = 0;
    double ProbeHeadroomCm = 0;
    double AccelTauSeconds = 0;
    double DecelTauSeconds = 0;
    double MaxMoveSubstepCm = 0;
    double MinSupportZ = 0;
    FString SceneSha256;
    FString SourceObjSha256;
    TArray<FBreziWalkingRecord> Records;
    int32 FloorCount = 0;
    int32 OffsetCount = 0;
    int32 ClosedCount = 0;
    int32 AuxiliaryCount = 0;

    bool Load(FString& Error);
    bool ValidateWorld(UWorld* World, TArray<FString>& Errors) const;
    static bool IsFloor(const UPrimitiveComponent* Component);
    static FString ObjectId(const UPrimitiveComponent* Component);
};
