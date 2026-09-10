#pragma once

// Selection and readiness only. Slate owns adaptive sizing, including DPI and
// rounding absolute geometry endpoints; no second pixel-scale conversion here.
namespace BreziOutput
{
enum class Mode { Invalid, Retina, FourK };
enum class Error { None, InvalidArgument, ConflictingCapture, ConflictingOutput };
struct Decision { Mode Output; Error Problem; };
constexpr Decision Select(bool Named, Mode Requested, bool Capture4K, bool CaptureUI, bool CaptureScene)
{
    if (Named && Requested == Mode::Invalid) return {Mode::Invalid, Error::InvalidArgument};
    const bool Legacy4K = Capture4K || CaptureUI;
    if (CaptureScene && Legacy4K) return {Mode::Invalid, Error::ConflictingCapture};
    if (Named && Requested == Mode::Retina && Legacy4K) return {Mode::Invalid, Error::ConflictingOutput};
    return {Legacy4K ? Mode::FourK : Named ? Requested : Mode::Retina, Error::None};
}
struct Pixels { int X; int Y; };
constexpr bool Positive(Pixels P) { return P.X > 0 && P.Y > 0; }
constexpr bool Equal(Pixels A, Pixels B) { return A.X == B.X && A.Y == B.Y; }
constexpr bool Matches(Mode Output, bool Fixed, bool GeometryValid, Pixels Drawable, Pixels Viewport, Pixels Target, Pixels Rhi)
{
    if (Output == Mode::Invalid || !GeometryValid || !Positive(Drawable)) return false;
    const Pixels Expected = Output == Mode::FourK ? Pixels{3840, 2160} : Drawable;
    return Fixed == (Output == Mode::FourK) && Equal(Viewport, Expected)
        && Equal(Target, Expected) && Equal(Rhi, Expected);
}
}
