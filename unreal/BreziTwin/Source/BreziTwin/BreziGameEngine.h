#pragma once

#include "CoreMinimal.h"
#include "Engine/GameEngine.h"
#include "BreziGameEngine.generated.h"

/** Keep the OS window resolution independent of the fixed scene texture. */
UCLASS()
class UBreziGameEngine : public UGameEngine
{
    GENERATED_BODY()
public:
    virtual void Init(IEngineLoop* InEngineLoop) override;
private:
    void OnPresentationViewportResized(FViewport* Viewport, uint32 Unused);
};
