#include "BreziGameEngine.h"
#include "BreziGameViewportClient.h"
#include "Slate/SceneViewport.h"

void UBreziGameEngine::Init(IEngineLoop* InEngineLoop)
{
    Super::Init(InEngineLoop);
    // UE 5.8 CreateGameViewport registers this engine object's OnViewportResized.
    // That handler copies scene texture dimensions into GSystemResolution and
    // requests a matching OS window. Route this one subscription through a
    // filter, retaining the engine's normal behavior for other viewport modes.
    FViewport::ViewportResizedEvent.RemoveAll(this);
    FViewport::ViewportResizedEvent.AddUObject(this, &UBreziGameEngine::OnPresentationViewportResized);
}

void UBreziGameEngine::OnPresentationViewportResized(FViewport* Viewport, uint32 Unused)
{
    if (const UBreziGameViewportClient* Presentation = Cast<UBreziGameViewportClient>(GameViewport))
    {
        const FSceneViewport* Scene = Presentation->GetGameViewport();
        if (Viewport == Scene && Scene && Scene->HasFixedSize()
            && static_cast<const ISlateViewport*>(Scene)->UseSeparateRenderTarget()) return;
    }
    OnViewportResized(Viewport, Unused);
}
