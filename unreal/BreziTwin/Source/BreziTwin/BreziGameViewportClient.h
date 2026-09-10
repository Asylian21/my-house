#pragma once

#include "CoreMinimal.h"
#include "Engine/GameViewportClient.h"
#include "BreziOutputPolicy.h"
#include "BreziGameViewportClient.generated.h"

class FJsonObject;
class SWidget;
class SViewport;
class ISlateViewport;

/** An aspect-preserving macOS scene target sized by Slate, with explicit fixed 4K capture. */
UCLASS()
class UBreziGameViewportClient : public UGameViewportClient
{
    GENERATED_BODY()
public:
    virtual TSharedRef<FSceneViewport> CreateViewport(TSharedPtr<SViewport> InViewportWidget) override;
    virtual void Tick(float DeltaTime) override;
    TSharedRef<FJsonObject> GetPresentationDiagnostics() const;
    bool IsRetinaOutput() const { return OutputMode == BreziOutput::Mode::Retina; }
    bool IsOutputSelectionValid() const { return bOutputResolved && OutputMode != BreziOutput::Mode::Invalid; }
    // Game-thread observation only; never initializes, resizes or changes focus.
    bool IsPresentationReadyForCurrentOutput() const;
private:
    void ResolveOutputMode();
    bool InitializePresentation();
    bool PresentationMatchesOutput() const;
    TSharedPtr<SWidget> PresentationRoot;
    TSharedPtr<SViewport> WindowHostWidget;
    TSharedPtr<ISlateViewport> WindowHostInterface;
    int32 InitializationAttempts = 0;
    int32 StartupTicks = 0;
    bool bPresentationReady = false;
    bool bPresentationConfigured = false;
    bool bWindowPlacementInitialized = false;
    bool bWindowFitted = false;
    bool bOutputResolved = false;
    BreziOutput::Mode OutputMode = BreziOutput::Mode::Retina;
    FString OutputSelectionError;
};
