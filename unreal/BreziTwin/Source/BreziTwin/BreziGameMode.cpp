#include "BreziGameMode.h"
#include "BreziPawn.h"
#include "BreziPlayerController.h"

ABreziGameMode::ABreziGameMode()
{
    DefaultPawnClass = ABreziPawn::StaticClass();
    PlayerControllerClass = ABreziPlayerController::StaticClass();
}
