#include "BreziGameViewportClient.h"
#include "BreziPlayerController.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RHI.h"
#include "Slate/SceneViewport.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWindow.h"

namespace
{
#if PLATFORM_MAC
// FSceneViewport forwards only FKey to PlayerInput. Preserve the original Mac
// code for our preset shortcut before that conversion, solely in this viewport.
class SBreziSceneViewport final : public SViewport
{
public:
    void SetPresetOwner(UBreziGameViewportClient* InOwner) { Owner = InOwner; }
    virtual FReply OnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override
    {
        UBreziGameViewportClient* Client = Owner.Get();
        UWorld* World = Client ? Client->GetWorld() : nullptr;
        if (World && World->IsGameWorld() && Client->GetGameViewportWidget().Get() == this)
        {
            if (ABreziPlayerController* Controller = Cast<ABreziPlayerController>(World->GetFirstPlayerController());
                Controller && Controller->IsLocalController())
            {
                bool bPresetCandidate = false;
                const FReply Reply = Controller->HandlePresetShortcut(Event, &bPresetCandidate);
                // Protected modifiers must bubble without reaching permissive
                // legacy bindings for a translated logical Equals/Add key.
                if (bPresetCandidate) return Reply;
            }
        }
        return SViewport::OnKeyDown(Geometry, Event);
    }
private:
    TWeakObjectPtr<UBreziGameViewportClient> Owner;
};
#endif

constexpr uint32 SceneWidth = 3840;
constexpr uint32 SceneHeight = 2160;
const TCHAR* OutputName(BreziOutput::Mode Mode)
{
    return Mode == BreziOutput::Mode::FourK ? TEXT("4k") : Mode == BreziOutput::Mode::Retina ? TEXT("retina") : TEXT("invalid");
}
FIntPoint DrawablePixels(const FGeometry& Geometry)
{
    // Match UE 5.8 FSceneViewport::Paint. Absolute draw geometry already includes
    // the window/application layout scale. Multiplying by DPI again is wrong.
    const FVector2D TopLeft = Geometry.GetAbsolutePosition();
    const FVector2D Draw = Geometry.GetDrawSize(), BottomRight = TopLeft + Draw;
    if (!FMath::IsFinite(TopLeft.X) || !FMath::IsFinite(TopLeft.Y)
        || !FMath::IsFinite(BottomRight.X) || !FMath::IsFinite(BottomRight.Y)
        || Draw.X <= 0 || Draw.Y <= 0) return FIntPoint::ZeroValue;
    return FIntPoint(FMath::RoundToInt(BottomRight.X) - FMath::RoundToInt(TopLeft.X),
        FMath::RoundToInt(BottomRight.Y) - FMath::RoundToInt(TopLeft.Y));
}
BreziOutput::Pixels Pixels(FIntPoint Value) { return {Value.X, Value.Y}; }
FIntPoint TexturePixels(const FSceneViewport& Scene)
{
    const FTextureRHIRef& Texture = Scene.GetRenderTargetTexture();
    return Texture.IsValid() ? FIntPoint(Texture->GetSizeX(), Texture->GetSizeY()) : FIntPoint::ZeroValue;
}
// MoviePlayer initially registers the engine's outer SViewport. Slate requires
// a valid interface there even though this host does not draw a scene or route
// input. Share only size/vsync metadata; the inner viewport alone ticks, draws
// and delivers input to the actual FSceneViewport.
class FBreziWindowHostViewport final : public ISlateViewport
{
public:
    explicit FBreziWindowHostViewport(const TSharedRef<FSceneViewport>& InScene) : Scene(InScene) {}
    virtual FIntPoint GetSize() const override
    {
        const TSharedPtr<FSceneViewport> Pinned = Scene.Pin();
        return Pinned.IsValid() ? Pinned->GetSizeXY() : FIntPoint::ZeroValue;
    }
    virtual FSlateShaderResource* GetViewportRenderTargetTexture() const override { return nullptr; }
    virtual bool RequiresVsync() const override
    {
        const TSharedPtr<FSceneViewport> Pinned = Scene.Pin();
        return Pinned.IsValid() && static_cast<const ISlateViewport&>(*Pinned).RequiresVsync();
    }
private:
    TWeakPtr<FSceneViewport> Scene;
};
TArray<TSharedPtr<FJsonValue>> Pair(double X, double Y)
{
    return {MakeShared<FJsonValueNumber>(X), MakeShared<FJsonValueNumber>(Y)};
}
TArray<TSharedPtr<FJsonValue>> RectangleJson(const FSlateRect& Bounds)
{
    return {MakeShared<FJsonValueNumber>(Bounds.Left), MakeShared<FJsonValueNumber>(Bounds.Top),
        MakeShared<FJsonValueNumber>(Bounds.Right), MakeShared<FJsonValueNumber>(Bounds.Bottom)};
}
}

#if PLATFORM_MAC
// A derived widget otherwise gets the default false trait. Preserve SViewport's
// existing invalidation support; this change only intercepts preset key presses.
template <> struct TWidgetTypeTraits<SBreziSceneViewport> : TWidgetTypeTraits<SViewport> {};
#endif

TSharedRef<FSceneViewport> UBreziGameViewportClient::CreateViewport(TSharedPtr<SViewport> Widget)
{
    ResolveOutputMode();
#if PLATFORM_MAC
    if (!GIsEditor && Widget.IsValid())
    {
        // MoviePlayer restores the engine's SViewport as window content on every
        // frame, even with no movie. Keep that host intact and put the actual
        // scene/input viewport inside an aspect-constrained child container.
        WindowHostWidget = Widget;
        WindowHostWidget->SetRenderDirectlyToWindow(true);
        const TSharedRef<SBreziSceneViewport> SceneWidget = SNew(SBreziSceneViewport)
            .RenderDirectlyToWindow(false).EnableGammaCorrection(false).EnableStereoRendering(false);
        SceneWidget->SetPresetOwner(this);
        const TSharedRef<FSceneViewport> Scene = Super::CreateViewport(SceneWidget);
        WindowHostInterface = MakeShared<FBreziWindowHostViewport>(Scene);
        WindowHostWidget->SetViewportInterface(WindowHostInterface.ToSharedRef());
        PresentationRoot = SNew(SBorder).Padding(0).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
            .BorderBackgroundColor(FLinearColor::Black)
            [SNew(SBox).MinAspectRatio(16.0f / 9.0f).MaxAspectRatio(16.0f / 9.0f)
                .HAlign(HAlign_Fill).VAlign(VAlign_Fill)[SceneWidget]];
        WindowHostWidget->SetContent(PresentationRoot);
        return Scene;
    }
#endif
    return Super::CreateViewport(Widget);
}

void UBreziGameViewportClient::ResolveOutputMode()
{
    if (bOutputResolved) return;
    bOutputResolved = true;
    const TCHAR* CLI = FCommandLine::Get();
    FString Named;
    const bool bNamed = FParse::Value(CLI, TEXT("BreziOutput="), Named)
        || FParse::Param(CLI, TEXT("BreziOutput"))
        || FString(CLI).Contains(TEXT("-BreziOutput="), ESearchCase::IgnoreCase);
    const auto Requested = Named == TEXT("4k") ? BreziOutput::Mode::FourK
        : Named == TEXT("retina") ? BreziOutput::Mode::Retina : BreziOutput::Mode::Invalid;
    const auto Decision = BreziOutput::Select(bNamed, Requested, FParse::Param(CLI, TEXT("BreziCapture4K")),
        FParse::Param(CLI, TEXT("BreziCaptureUI")), FParse::Param(CLI, TEXT("BreziCaptureScene")));
    OutputMode = Decision.Output;
    if (Decision.Problem == BreziOutput::Error::InvalidArgument)
        OutputSelectionError = TEXT("BreziOutput requires exactly retina or 4k.");
    else if (Decision.Problem == BreziOutput::Error::ConflictingCapture)
        OutputSelectionError = TEXT("BreziCaptureScene cannot be combined with BreziCapture4K or BreziCaptureUI.");
    else if (Decision.Problem == BreziOutput::Error::ConflictingOutput)
        OutputSelectionError = TEXT("BreziOutput=retina conflicts with the fixed 4K capture request.");
    if (!OutputSelectionError.IsEmpty()) UE_LOG(LogTemp, Error, TEXT("BreziPresentation: %s"), *OutputSelectionError);
}

bool UBreziGameViewportClient::InitializePresentation()
{
    if (!IsOutputSelectionValid()) return false;
    const TSharedPtr<SWindow> Window = GetWindow();
    const TSharedPtr<SViewport> Widget = GetGameViewportWidget();
    FSceneViewport* Scene = GetGameViewport();
    if (!Window.IsValid() || !Widget.IsValid() || !Scene || !FSlateApplication::IsInitialized()) return false;
    if (!static_cast<const ISlateViewport*>(Scene)->UseSeparateRenderTarget())
    {
        UE_LOG(LogTemp, Error, TEXT("BreziPresentation: separate scene target was not established before viewport creation."));
        return false;
    }
    if (!WindowHostWidget.IsValid() || Window->GetContent() != WindowHostWidget
        || WindowHostWidget->GetContent() != PresentationRoot) return false;
    const TSharedPtr<SWidget> PreviousFocus = FSlateApplication::Get().GetKeyboardFocusedWidget();
    FSlateApplication::Get().RegisterGameViewport(Widget.ToSharedRef());
    if (!PreviousFocus.IsValid() || PreviousFocus == WindowHostWidget)
        FSlateApplication::Get().SetKeyboardFocus(Widget, EFocusCause::SetDirectly);
    if (!bWindowPlacementInitialized && Window->GetWindowMode() == EWindowMode::Windowed)
    {
        const FVector2D Position = Window->GetPositionInScreen();
        const FVector2D OuterSize = Window->GetSizeInScreen();
        const FSlateRect Work = FSlateApplication::Get().GetWorkArea(FSlateRect(Position, Position + OuterSize));
        const FMargin Border = Window->GetWindowBorderSize(true);
        const float Margin = 24.0f * Window->GetDPIScaleFactor();
        const float AvailableWidth = FMath::Max(320.0f, Work.GetSize().X - 2 * Margin - Border.Left - Border.Right);
        const float AvailableHeight = FMath::Max(180.0f, Work.GetSize().Y - 2 * Margin - Border.Top - Border.Bottom);
        const FVector2D CurrentClient = Window->GetClientSizeInScreen();
        const float Width = FMath::Max(320.0f, FMath::Min3(static_cast<float>(CurrentClient.X), AvailableWidth, AvailableHeight * 16.0f / 9.0f));
        const FVector2D ClientSize(Width, Width * 9.0f / 16.0f);
        Window->Resize(ClientSize);
        const FVector2D FittedOuter = ClientSize + FVector2D(Border.Left + Border.Right, Border.Top + Border.Bottom);
        Window->MoveWindowTo(FVector2D(Work.Left + (Work.GetSize().X - FittedOuter.X) * 0.5f,
            Work.Top + (Work.GetSize().Y - FittedOuter.Y) * 0.5f));
        bWindowFitted = true;
    }
    bWindowPlacementInitialized = true;
    if (OutputMode == BreziOutput::Mode::FourK) Scene->SetFixedViewportSize(SceneWidth, SceneHeight);
    else Scene->SetFixedViewportSize(0, 0);
    Window->SlatePrepass(FSlateApplication::Get().GetApplicationScale() * Window->GetDPIScaleFactor());
    bPresentationConfigured = true;
    return true;
}

bool UBreziGameViewportClient::PresentationMatchesOutput() const
{
    const FSceneViewport* Scene = GetGameViewport();
    const TSharedPtr<SViewport> Widget = GetGameViewportWidget();
    if (!Scene || !Widget.IsValid()) return false;
    const FIntPoint Drawable = DrawablePixels(Widget->GetCachedGeometry());
    return BreziOutput::Matches(OutputMode, Scene->HasFixedSize(), Drawable.X > 0 && Drawable.Y > 0,
        Pixels(Drawable), Pixels(Scene->GetSizeXY()), Pixels(Scene->GetRenderTargetTextureSizeXY()), Pixels(TexturePixels(*Scene)));
}

bool UBreziGameViewportClient::IsPresentationReadyForCurrentOutput() const
{
    check(IsInGameThread());
    const TSharedPtr<SWindow> Window = GetWindow();
    return bPresentationConfigured && bPresentationReady && IsOutputSelectionValid()
        && Window.IsValid() && WindowHostWidget.IsValid() && PresentationRoot.IsValid()
        && Window->GetContent() == WindowHostWidget && WindowHostWidget->GetContent() == PresentationRoot
        && PresentationMatchesOutput();
}

void UBreziGameViewportClient::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
#if PLATFORM_MAC
    if (GIsEditor || IsRunningCommandlet() || !IsOutputSelectionValid()) return;
    // Let the initial engine window registration complete before registering
    // the nested scene widget as the actual game input viewport.
    if (++StartupTicks <= 2) return;
    if (bPresentationConfigured && GetWindow().IsValid() && GetWindow()->GetContent() != WindowHostWidget)
    {
        bPresentationReady = false;
        bPresentationConfigured = false;
    }
    if (!bPresentationReady && InitializationAttempts < 300)
    {
        ++InitializationAttempts;
        // Configure/register/fit once. Waiting for Slate's first paint must not
        // recenter the window or steal keyboard focus on every startup tick.
        if (!bPresentationConfigured) InitializePresentation();
        if (bPresentationConfigured && PresentationMatchesOutput())
        {
            bPresentationReady = true;
            UE_LOG(LogTemp, Display, TEXT("BreziPresentation: ready=1, output=%s, scene=%dx%d; window/UI sizes are reported separately."),
                OutputName(OutputMode), GetGameViewport()->GetSizeXY().X, GetGameViewport()->GetSizeXY().Y);
        }
        if (!bPresentationReady && InitializationAttempts == 300)
            UE_LOG(LogTemp, Error, TEXT("BreziPresentation: %s scene/window initialization timed out."), OutputName(OutputMode));
    }
    else if (bPresentationReady)
    {
        // Resize/DPI changes settle through SceneViewport::Paint in Retina mode.
        // A transient target mismatch never repeats registration, focus or fitting.
        if (FSceneViewport* Scene = GetGameViewport())
        {
            if (OutputMode == BreziOutput::Mode::FourK && (!Scene->HasFixedSize() || Scene->GetSizeXY() != FIntPoint(SceneWidth, SceneHeight)))
                Scene->SetFixedViewportSize(SceneWidth, SceneHeight);
            else if (OutputMode == BreziOutput::Mode::Retina && Scene->HasFixedSize()) Scene->SetFixedViewportSize(0, 0);
        }
    }
#endif
}

TSharedRef<FJsonObject> UBreziGameViewportClient::GetPresentationDiagnostics() const
{
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("initialized"), bPresentationReady);
    Result->SetStringField(TEXT("outputMode"), OutputName(OutputMode));
    Result->SetBoolField(TEXT("outputSelectionValid"), IsOutputSelectionValid());
    Result->SetStringField(TEXT("outputSelectionError"), OutputSelectionError);
    Result->SetBoolField(TEXT("targetMatchesOutputContract"), PresentationMatchesOutput());
    Result->SetBoolField(TEXT("windowFittedAtStartup"), bWindowFitted);
    Result->SetNumberField(TEXT("initializationAttempts"), InitializationAttempts);
    Result->SetNumberField(TEXT("presentationAspectRatio"), 16.0 / 9.0);
    Result->SetBoolField(TEXT("windowHostViewportInterfaceValid"), WindowHostWidget.IsValid()
        && WindowHostWidget->GetViewportInterface().IsValid());
    if (const FSceneViewport* Scene = GetGameViewport())
    {
        Result->SetBoolField(TEXT("separateSceneRenderTarget"), static_cast<const ISlateViewport*>(Scene)->UseSeparateRenderTarget());
        Result->SetBoolField(TEXT("fixedSceneSize"), Scene->HasFixedSize());
        const FIntPoint Size = Scene->GetSizeXY(), Target = Scene->GetRenderTargetTextureSizeXY();
        Result->SetArrayField(TEXT("sceneViewportPixels"), Pair(Size.X, Size.Y));
        Result->SetArrayField(TEXT("sceneRenderTargetPixels"), Pair(Target.X, Target.Y));
        const FIntPoint Rhi = TexturePixels(*Scene);
        Result->SetArrayField(TEXT("sceneRhiTexturePixels"), Pair(Rhi.X, Rhi.Y));
    }
    if (const TSharedPtr<SWindow> Window = GetWindow(); Window.IsValid())
    {
        const FVector2D Position = Window->GetPositionInScreen(), Size = Window->GetSizeInScreen();
        const FVector2D Client = Window->GetClientSizeInScreen(), Backbuffer = Window->GetViewportSize();
        Result->SetBoolField(TEXT("aspectContainerAttachedToWindow"), PresentationRoot.IsValid()
            && WindowHostWidget.IsValid() && Window->GetContent() == WindowHostWidget
            && WindowHostWidget->GetContent() == PresentationRoot);
        Result->SetArrayField(TEXT("windowOuterRectSlateScreenUnits"), RectangleJson(FSlateRect(Position, Position + Size)));
        Result->SetArrayField(TEXT("windowClientSizeSlateScreenUnits"), Pair(Client.X, Client.Y));
        Result->SetArrayField(TEXT("windowReportedBackbufferPixels"), Pair(Backbuffer.X, Backbuffer.Y));
        Result->SetNumberField(TEXT("windowDPIScale"), Window->GetDPIScaleFactor());
        if (FSlateApplication::IsInitialized())
        {
            const FSlateRect Work = FSlateApplication::Get().GetWorkArea(FSlateRect(Position, Position + Size));
            Result->SetArrayField(TEXT("monitorWorkAreaSlateScreenUnits"), RectangleJson(Work));
            Result->SetBoolField(TEXT("windowInsideMonitorWorkArea"), Position.X >= Work.Left - 1 && Position.Y >= Work.Top - 1
                && Position.X + Size.X <= Work.Right + 1 && Position.Y + Size.Y <= Work.Bottom + 1);
        }
    }
    if (const TSharedPtr<SViewport> Widget = GetGameViewportWidget(); Widget.IsValid())
    {
        const FGeometry& Geometry = Widget->GetCachedGeometry();
        const FVector2D LocalSize = Geometry.GetLocalSize(), DrawSize = Geometry.GetDrawSize();
        const FIntPoint Drawable = DrawablePixels(Geometry);
        Result->SetArrayField(TEXT("expectedDrawablePixels"), Pair(Drawable.X, Drawable.Y));
        const FSceneViewport* Scene = GetGameViewport();
        Result->SetBoolField(TEXT("targetMatchesDrawable"), Drawable.X > 0 && Drawable.Y > 0 && Scene
            && Scene->GetSizeXY() == Drawable && Scene->GetRenderTargetTextureSizeXY() == Drawable && TexturePixels(*Scene) == Drawable);
        Result->SetArrayField(TEXT("slateViewportLocalSize"), Pair(LocalSize.X, LocalSize.Y));
        Result->SetArrayField(TEXT("slateViewportDrawSizeScreenUnits"), Pair(DrawSize.X, DrawSize.Y));
        Result->SetArrayField(TEXT("slateViewportRectScreenUnits"), RectangleJson(Geometry.GetRenderBoundingRect()));
    }
    Result->SetStringField(TEXT("interpretation"), OutputMode == BreziOutput::Mode::FourK
        ? TEXT("Scene output target is fixed 3840x2160; internal sampling percentages are reported separately. Slate presents it aspect-preserved within the monitor-fitting window. Window/UI and scene screenshot dimensions are distinct. Window reported backbuffer dimensions are Slate allocation metadata, not a GPU texture readback.")
        : OutputMode == BreziOutput::Mode::Retina
        ? TEXT("Scene output target follows Slate's rounded absolute viewport draw endpoints, including the existing application/window scale once. Retina names this adaptive sizing policy, not a fixed resolution. Internal sampling percentages are separate. A resize may temporarily mismatch drawable and target; actual RHI texture dimensions are reported separately from window backbuffer allocation metadata.")
        : TEXT("Invalid output arguments; presentation is not accepted."));
    return Result;
}
