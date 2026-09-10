#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
class FSceneView;
struct FBreziCausticsProducedGraph
{
    FRDGTextureRef Atlas = nullptr;
    FRDGBufferRef Photons = nullptr, Visibility = nullptr, Gates = nullptr, GPUUniform = nullptr;
};
// Editor diagnostic producer; no prior-frame texture, no light/albedo/exposure multiplication.
class IBreziCausticsTransport
{
public:
    virtual ~IBreziCausticsTransport() = default;
    virtual FBreziCausticsProducedGraph Build(FRDGBuilder&, const FSceneView&, FVector3f SunTravel, FRDGBufferSRVRef CurrentTLAS) = 0;
    virtual FString ReceiverJson() const = 0;
    virtual FString WaterJson() const = 0;
    virtual FString SolarJson() const = 0;
    virtual bool AcceptsSun(FVector3f SunTravel) const = 0;
};
TUniquePtr<IBreziCausticsTransport> CreateBreziCausticsTransport(const FString& ReceiverPath, bool bVerifiedCookedBinding = false);
inline constexpr uint32 BreziTransportSamples = 512 * 230;
inline constexpr uint32 BreziTransportVisibilityCount = BreziTransportSamples + 6;
inline constexpr uint32 BreziTransportRecordBytes = 48;
