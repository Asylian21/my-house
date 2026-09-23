#pragma once

#include <initializer_list>

#include "CoreMinimal.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateTypes.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/Text/STextBlock.h"

// Shared native Slate vocabulary. Colors are authored in sRGB and converted
// once; brushes have static lifetime because Slate retains their addresses.
namespace BreziUI
{
    inline FLinearColor SRGB(uint8 R, uint8 G, uint8 B, float Alpha = 1.0f)
    {
        FLinearColor Color = FLinearColor::FromSRGBColor(FColor(R, G, B));
        Color.A = Alpha;
        return Color;
    }

    inline const FLinearColor Ink = SRGB(0xF2, 0xEE, 0xE5);
    inline const FLinearColor Quiet = SRGB(0xA9, 0xA9, 0xA5);
    inline const FLinearColor Accent = SRGB(0xDC, 0xB6, 0x7A);
    inline const FLinearColor Surface = SRGB(0x18, 0x1D, 0x21);
    inline const FLinearColor Inset = SRGB(0x11, 0x16, 0x1A);
    inline const FLinearColor Line = SRGB(0x3B, 0x42, 0x47);
    inline const FLinearColor SliderRail = SRGB(0x7B, 0x85, 0x8B);
    inline constexpr float MinimumTargetSize = 44.0f;

    inline FSlateFontInfo Font(const char* Weight, int32 Size, int32 Tracking = 0)
    {
        FSlateFontInfo Result = FCoreStyle::GetDefaultFontStyle(Weight, Size);
        Result.LetterSpacing = Tracking;
        return Result;
    }

    inline const FSlateRoundedBoxBrush& PanelBrush(bool HighContrast = false)
    {
        static const FSlateRoundedBoxBrush Normal(Surface, 14.0f, Line, 1.0f);
        static const FSlateRoundedBoxBrush Contrast(Surface, 14.0f, Quiet, 1.5f);
        return HighContrast ? Contrast : Normal;
    }

    inline const FSlateRoundedBoxBrush& InsetBrush(bool HighContrast = false)
    {
        static const FSlateRoundedBoxBrush Normal(Inset, 9.0f, Line, 1.0f);
        static const FSlateRoundedBoxBrush Contrast(Inset, 9.0f, Quiet, 1.5f);
        return HighContrast ? Contrast : Normal;
    }

    inline const FSlateRoundedBoxBrush& FocusBrush()
    {
        // Warm white remains visible around both graphite and sand buttons.
        static const FSlateRoundedBoxBrush Brush(FLinearColor::Transparent, 9.0f, Ink, 2.0f);
        return Brush;
    }

    inline const FButtonStyle& ButtonStyle(bool Primary = false)
    {
        static const FButtonStyle QuietStyle = FButtonStyle()
            .SetNormal(FSlateRoundedBoxBrush(SRGB(0x22, 0x28, 0x2D), 9.0f, Line, 1.0f))
            .SetHovered(FSlateRoundedBoxBrush(SRGB(0x32, 0x3A, 0x40), 9.0f, SRGB(0x67, 0x6D, 0x70), 1.0f))
            .SetPressed(FSlateRoundedBoxBrush(SRGB(0x14, 0x19, 0x1D), 9.0f, Accent, 1.0f))
            .SetDisabled(FSlateRoundedBoxBrush(SRGB(0x1B, 0x20, 0x24), 9.0f, SRGB(0x2C, 0x32, 0x36), 1.0f))
            .SetNormalForeground(Ink).SetHoveredForeground(Ink).SetPressedForeground(Accent)
            .SetDisabledForeground(Quiet)
            .SetNormalPadding(FMargin(0)).SetPressedPadding(FMargin(0));
        static const FButtonStyle PrimaryStyle = FButtonStyle()
            .SetNormal(FSlateRoundedBoxBrush(Accent, 9.0f, Accent, 1.0f))
            .SetHovered(FSlateRoundedBoxBrush(SRGB(0xEC, 0xCA, 0x96), 9.0f, SRGB(0xF5, 0xD9, 0xB1), 1.0f))
            .SetPressed(FSlateRoundedBoxBrush(SRGB(0xC7, 0x9D, 0x62), 9.0f, Accent, 1.0f))
            .SetDisabled(FSlateRoundedBoxBrush(SRGB(0x69, 0x5D, 0x4B), 9.0f, Line, 1.0f))
            .SetNormalForeground(Inset).SetHoveredForeground(Inset).SetPressedForeground(Inset)
            .SetDisabledForeground(Quiet)
            .SetNormalPadding(FMargin(0)).SetPressedPadding(FMargin(0));
        return Primary ? PrimaryStyle : QuietStyle;
    }

    inline const FCheckBoxStyle& ToggleStyle()
    {
        static const FCheckBoxStyle Style = FCheckBoxStyle()
            .SetCheckBoxType(ESlateCheckBoxType::ToggleButton)
            .SetUncheckedImage(FSlateRoundedBoxBrush(Inset, 9.0f, Line, 1.0f))
            .SetUncheckedHoveredImage(FSlateRoundedBoxBrush(SRGB(0x2E, 0x36, 0x3B), 9.0f, Quiet, 1.0f))
            .SetUncheckedPressedImage(FSlateRoundedBoxBrush(SRGB(0x16, 0x1C, 0x20), 9.0f, Accent, 1.0f))
            .SetCheckedImage(FSlateRoundedBoxBrush(SRGB(0x3A, 0x33, 0x29), 9.0f, Accent, 1.0f))
            .SetCheckedHoveredImage(FSlateRoundedBoxBrush(SRGB(0x4B, 0x40, 0x30), 9.0f, Accent, 1.0f))
            .SetCheckedPressedImage(FSlateRoundedBoxBrush(SRGB(0x2B, 0x26, 0x20), 9.0f, Accent, 1.0f))
            .SetUndeterminedImage(FSlateRoundedBoxBrush(Inset, 9.0f, Quiet, 1.0f))
            .SetUndeterminedHoveredImage(FSlateRoundedBoxBrush(Surface, 9.0f, Quiet, 1.0f))
            .SetUndeterminedPressedImage(FSlateRoundedBoxBrush(Inset, 9.0f, Accent, 1.0f))
            .SetForegroundColor(Ink).SetHoveredForegroundColor(Ink).SetPressedForegroundColor(Accent)
            .SetCheckedForegroundColor(Accent).SetCheckedHoveredForegroundColor(Accent)
            .SetCheckedPressedForegroundColor(Accent).SetPadding(FMargin(0));
        return Style;
    }

    inline FLinearColor SliderRailColor(bool HighContrast = false)
    {
        return HighContrast ? Ink : SliderRail;
    }

    inline const FSliderStyle& SliderStyle()
    {
        // SSlider multiplies these brush tints by SliderBarColor and
        // SliderHandleColor. White base brushes avoid double-darkening our
        // sRGB-authored colors. Rounded vector brushes need no engine textures.
        static const FSliderStyle Style = FSliderStyle()
            .SetNormalBarImage(FSlateRoundedBoxBrush(FLinearColor::White, 2.0f))
            .SetHoveredBarImage(FSlateRoundedBoxBrush(FLinearColor::White, 2.0f))
            .SetDisabledBarImage(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.35f), 2.0f))
            .SetNormalThumbImage(FSlateRoundedBoxBrush(FLinearColor::White, 8.0f, Ink, 1.0f, FVector2f(16, 16)))
            .SetHoveredThumbImage(FSlateRoundedBoxBrush(FLinearColor::White, 8.0f, Ink, 2.0f, FVector2f(16, 16)))
            .SetDisabledThumbImage(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.4f), 8.0f,
                Quiet.CopyWithNewOpacity(0.4f), 1.0f, FVector2f(16, 16)))
            .SetBarThickness(4.0f);
        return Style;
    }

    // Inherits SButton's real click, key, pointer, and accessibility behavior.
    // UE 5.8 SWidget::GetFocusBrush is virtual; no global CoreStyle mutation.
    class SGameButton : public SButton
    {
    public:
        using FArguments = SButton::FArguments;

        void Construct(const FArguments& Args) { SButton::Construct(Args); }

        virtual const FSlateBrush* GetFocusBrush() const override { return &FocusBrush(); }

    protected:
        virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override
        {
            const FVector2D Desired = SButton::ComputeDesiredSize(LayoutScaleMultiplier);
            return FVector2D(FMath::Max(double(MinimumTargetSize), Desired.X),
                FMath::Max(double(MinimumTargetSize), Desired.Y));
        }
    };

    class SGameCheckBox : public SCheckBox
    {
    public:
        using FArguments = SCheckBox::FArguments;

        void Construct(const FArguments& Args) { SCheckBox::Construct(Args); }

        virtual const FSlateBrush* GetFocusBrush() const override { return &FocusBrush(); }

    protected:
        virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override
        {
            const FVector2D Desired = SCheckBox::ComputeDesiredSize(LayoutScaleMultiplier);
            return FVector2D(FMath::Max(double(MinimumTargetSize), Desired.X),
                FMath::Max(double(MinimumTargetSize), Desired.Y));
        }
    };

    class SGameSlider : public SSlider
    {
    public:
        using FArguments = SSlider::FArguments;

        void Construct(const FArguments& Args) { SSlider::Construct(Args); }

        virtual const FSlateBrush* GetFocusBrush() const override { return &FocusBrush(); }

    protected:
        virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override
        {
            const FVector2D Desired = SSlider::ComputeDesiredSize(LayoutScaleMultiplier);
            return FVector2D(FMath::Max(double(MinimumTargetSize), Desired.X),
                FMath::Max(double(MinimumTargetSize), Desired.Y));
        }
    };

    inline TSharedRef<SWidget> Keycap(FText Label, bool bAccent = false)
    {
        static const FSlateRoundedBoxBrush NormalBrush(SRGB(0x2B, 0x32, 0x37), 5.0f, SRGB(0x55, 0x5D, 0x62), 1.0f);
        static const FSlateRoundedBoxBrush AccentBrush(SRGB(0x3A, 0x33, 0x29), 5.0f, Accent, 1.0f);
        return SNew(SBox).MinDesiredWidth(25).HeightOverride(25)
            .Visibility(EVisibility::HitTestInvisible)
            [SNew(SBorder).BorderImage(bAccent ? &AccentBrush : &NormalBrush)
                .Padding(FMargin(6, 2)).HAlign(HAlign_Center).VAlign(VAlign_Center)
                [SNew(STextBlock).Text(Label).Font(Font("Bold", 9)).ColorAndOpacity(bAccent ? Accent : Ink)]];
    }

    enum class Icon
    {
        Rooms, Person, Eye, Recenter, Plus, Minus, Sun, Moon, Settings,
        Cursor, Mouse, Menu, ArrowLeft, ArrowRight, ArrowUp, ArrowDown,
        Stop, Door, Play, Close, Check, Flight
    };

    // Compact original 24-unit line drawings. There are no font symbols,
    // imported textures, Unicode fallback dependencies, or per-frame assets.
    class SGameGlyph final : public SLeafWidget
    {
    public:
        SLATE_BEGIN_ARGS(SGameGlyph) : _Symbol(Icon::Rooms), _Size(20.0f), _Tint(Ink) {}
            SLATE_ARGUMENT(Icon, Symbol)
            SLATE_ARGUMENT(float, Size)
            SLATE_ARGUMENT(FLinearColor, Tint)
        SLATE_END_ARGS()

        void Construct(const FArguments& Args)
        {
            Size = FMath::Max(1.0f, Args._Size);
            Tint = Args._Tint;
            SetVisibility(EVisibility::HitTestInvisible);
            const auto Path = [this](std::initializer_list<FVector2D> Points)
            {
                TArray<FVector2D>& LinePath = Paths.AddDefaulted_GetRef();
                LinePath.Reserve(int32(Points.size()));
                for (const FVector2D& Point : Points) LinePath.Add(Point);
            };
            const auto Circle = [this](double X, double Y, double Radius)
            {
                TArray<FVector2D>& LinePath = Paths.AddDefaulted_GetRef();
                constexpr int32 Steps = 32;
                LinePath.Reserve(Steps + 1);
                for (int32 I = 0; I <= Steps; ++I)
                {
                    const double Angle = double(I) / Steps * 2.0 * PI;
                    LinePath.Emplace(X + FMath::Cos(Angle) * Radius, Y + FMath::Sin(Angle) * Radius);
                }
            };
            switch (Args._Symbol)
            {
            case Icon::Rooms:
                Path({{4, 4}, {20, 4}, {20, 20}, {4, 20}, {4, 4}});
                Path({{10, 4}, {10, 13}, {20, 13}});
                Path({{4, 13}, {7, 13}}); Path({{10, 17}, {10, 20}}); break;
            case Icon::Person:
                Circle(12, 7, 3);
                Path({{5, 21}, {5, 19}, {5.5, 16.5}, {7, 15}, {9, 14}, {15, 14}, {17, 15}, {18.5, 16.5}, {19, 19}, {19, 21}}); break;
            case Icon::Eye:
                Path({{2, 12}, {4, 9}, {7, 6.5}, {10, 5.5}, {14, 5.5}, {17, 6.5}, {20, 9}, {22, 12},
                    {20, 15}, {17, 17.5}, {14, 18.5}, {10, 18.5}, {7, 17.5}, {4, 15}, {2, 12}});
                Circle(12, 12, 3); break;
            case Icon::Recenter:
                Path({{8, 3}, {3, 3}, {3, 8}}); Path({{16, 3}, {21, 3}, {21, 8}});
                Path({{3, 16}, {3, 21}, {8, 21}}); Path({{16, 21}, {21, 21}, {21, 16}});
                Circle(12, 12, 3); break;
            case Icon::Plus:
                Path({{5, 12}, {19, 12}}); Path({{12, 5}, {12, 19}}); break;
            case Icon::Minus: Path({{5, 12}, {19, 12}}); break;
            case Icon::Sun:
                Circle(12, 12, 4);
                for (int32 I = 0; I < 8; ++I)
                {
                    const double Angle = double(I) / 8 * 2.0 * PI;
                    const FVector2D Direction(FMath::Cos(Angle), FMath::Sin(Angle));
                    Path({FVector2D(12, 12) + Direction * 7.0, FVector2D(12, 12) + Direction * 10.0});
                }
                break;
            case Icon::Moon:
                Path({{20.5, 14.4}, {19.7, 17.2}, {17.8, 19.4}, {15.2, 20.8}, {12.1, 21.1},
                    {9, 20.3}, {6.4, 18.4}, {4.8, 15.7}, {4.3, 12.6}, {5, 9.5}, {6.8, 6.9},
                    {9.5, 5.2}, {12.4, 4.6}, {11.3, 6.7}, {11, 9}, {11.5, 11.3},
                    {12.8, 13.2}, {14.7, 14.5}, {17, 15}, {19.2, 14.8}, {20.5, 14.4}}); break;
            case Icon::Settings:
            {
                TArray<FVector2D>& Gear = Paths.AddDefaulted_GetRef();
                for (int32 I = 0; I <= 32; ++I)
                {
                    const double Angle = (double(I) / 32 - 0.0625) * 2.0 * PI;
                    const double Radius = I % 4 < 2 ? 9.5 : 7.5;
                    Gear.Emplace(12 + FMath::Cos(Angle) * Radius, 12 + FMath::Sin(Angle) * Radius);
                }
                Circle(12, 12, 3); break;
            }
            case Icon::Cursor:
                Path({{5, 3}, {5, 19}, {9.5, 14.5}, {13, 21}, {16, 19.5}, {12.5, 13}, {19, 13}, {5, 3}}); break;
            case Icon::Mouse:
                Path({{12, 2.5}, {9, 3}, {6.5, 5}, {5.5, 8}, {5.5, 16}, {6.5, 19}, {9, 21},
                    {12, 21.5}, {15, 21}, {17.5, 19}, {18.5, 16}, {18.5, 8}, {17.5, 5}, {15, 3}, {12, 2.5}});
                Path({{12, 3}, {12, 10}}); Path({{5.5, 11}, {18.5, 11}}); break;
            case Icon::Menu:
                Path({{4, 6}, {20, 6}}); Path({{4, 12}, {20, 12}}); Path({{4, 18}, {15, 18}}); break;
            case Icon::ArrowLeft:
                Path({{10, 5}, {3, 12}, {10, 19}}); Path({{3, 12}, {21, 12}}); break;
            case Icon::ArrowRight:
                Path({{14, 5}, {21, 12}, {14, 19}}); Path({{3, 12}, {21, 12}}); break;
            case Icon::ArrowUp:
                Path({{5, 10}, {12, 3}, {19, 10}}); Path({{12, 3}, {12, 21}}); break;
            case Icon::ArrowDown:
                Path({{5, 14}, {12, 21}, {19, 14}}); Path({{12, 3}, {12, 21}}); break;
            case Icon::Stop: Path({{6, 6}, {18, 6}, {18, 18}, {6, 18}, {6, 6}}); break;
            case Icon::Door:
                Path({{4, 21}, {4, 3}, {16, 3}, {16, 21}}); Path({{4, 3}, {12, 6}, {12, 21}, {4, 21}});
                Path({{9, 12}, {9, 13}}); Path({{16, 21}, {20, 21}}); break;
            case Icon::Play: Path({{7, 4}, {20, 12}, {7, 20}, {7, 4}}); break;
            case Icon::Flight:
                Path({{3, 10}, {21, 3}, {14, 21}, {11, 13}, {3, 10}});
                Path({{11, 13}, {21, 3}}); break;
            case Icon::Close: Path({{6, 6}, {18, 18}}); Path({{18, 6}, {6, 18}}); break;
            case Icon::Check: Path({{4, 12}, {9, 17}, {20, 6}}); break;
            }
        }

    protected:
        virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(Size, Size); }

        virtual int32 OnPaint(const FPaintArgs&, const FGeometry& Geometry, const FSlateRect&,
            FSlateWindowElementList& Elements, int32 Layer, const FWidgetStyle& Style, bool bParentEnabled) const override
        {
            const FVector2D Available = Geometry.GetLocalSize();
            const double Side = FMath::Min(double(Size), FMath::Min(Available.X, Available.Y));
            if (Side <= 0.0) return Layer;
            const double Scale = Side / 24.0;
            const FVector2D Offset = (Available - FVector2D(Side, Side)) * 0.5;
            const FLinearColor Color = Tint * Style.GetColorAndOpacityTint();
            const ESlateDrawEffect Effect = ShouldBeEnabled(bParentEnabled) ? ESlateDrawEffect::None : ESlateDrawEffect::DisabledEffect;
            TArray<FVector2D> Points;
            Points.Reserve(33);
            for (const TArray<FVector2D>& Path : Paths)
            {
                Points.Reset();
                for (const FVector2D& Point : Path) Points.Add(Offset + Point * Scale);
                FSlateDrawElement::MakeLines(Elements, Layer, Geometry.ToPaintGeometry(), Points, Effect, Color, true,
                    float(1.8 * Scale));
            }
            return Layer;
        }

    private:
        float Size = 20.0f;
        FLinearColor Tint = Ink;
        TArray<TArray<FVector2D>> Paths;
    };

    inline TSharedRef<SWidget> Glyph(Icon Symbol, float Size = 20.0f, FLinearColor Tint = Ink)
    {
        return SNew(SGameGlyph).Symbol(Symbol).Size(Size).Tint(Tint);
    }
}
