"""Independent Fourier benchmark and uniform-floor identities; no site approval.

Units: kN, m. A periodic 40 m cell approximates an infinite beam for a
centered finite-width wall. Harmonic load coefficients are integrated exactly.
No imported solver from either of the two main ground-support calculations.
"""
import json, math
from pathlib import Path
import numpy as np

B = Path(__file__).resolve().parents[1]
E = 28.6e6
EI = E / 12000  # b=1 m, h=0.1 m: I=b h^3/12
G, Q, GAMMAG, GAMMAQ = 4.5, 2.0, 1.35, 1.5
WALLS = [("H200", 5.2115625, .2), ("partition", 6.9375, .14),
         ("garage", 12.975, .301)]

def direct(P, a, ks, factor=1):
    rigidity = EI * factor
    beta = (ks / (4 * rigidity)) ** .25
    t = beta * a / 2
    return {"M_center_kNm_m": P / (4 * beta) * math.exp(-t) * math.sin(t) / t,
            "wall_w_center_m": P / (a * ks) * (1 - math.exp(-t) * math.cos(t))}

def fourier(P, a, ks, harmonics, factor=1, cell=40):
    n = np.arange(1, harmonics + 1, dtype=float)
    omega = 2 * math.pi * n / cell
    qn = 2 * P / cell * np.sinc(n * a / cell)
    wn = qn / (EI * factor * omega ** 4 + ks)
    return {"M_center_kNm_m": float(np.sum(EI * factor * omega**2 * wn)),
            "wall_w_center_m": float(P / cell / ks + np.sum(wn))}

def main():
    uniform = [{"ks_MN_m3": k, "characteristic_pressure_kPa": G + Q,
                "ULS_pressure_kPa": GAMMAG * G + GAMMAQ * Q,
                "QP_pressure_kPa": G + .3 * Q,
                "characteristic_spring_compression_mm": (G + Q) / k,
                "QP_spring_compression_mm": (G + .3 * Q) / k,
                "ideal_uniform_internal_bending_kNm_m": 0.0}
               for k in [5, 10, 20, 50]]
    benchmarks = []
    for k in [5, 10, 20, 50]:
        for name, P, a in WALLS:
            for factor in [1, .25]:
                exact = direct(P, a, k * 1000, factor)
                coarse = fourier(P, a, k * 1000, 4096, factor)
                fine = fourier(P, a, k * 1000, 16384, factor)
                errors = {key: abs(fine[key] / value - 1) for key, value in exact.items()}
                assert max(errors.values()) < 1e-6, (k, name, factor, errors)
                benchmarks.append({"wall": name, "wall_gk_kN_m": P,
                                   "wall_width_m": a, "ks_MN_m3": k,
                                   "EI_factor": factor, "closed_form": exact,
                                   "fourier_4096": coarse, "fourier_16384": fine,
                                   "relative_errors": errors})
    result = {"status": "CONDITIONAL_MODEL_NOT_SITE_APPROVAL", "EI_kNm2": EI,
              "main_support": "continuous homogeneous elastic foundation",
              "uniform_floor": uniform, "benchmarks": benchmarks,
              "maximum_relative_error": max(max(v['relative_errors'].values()) for v in benchmarks),
              "limitations": ["The ks grid is a parameter sensitivity, not measured fill properties.",
                              "p/ks describes spring compression only; not final total consolidation settlement.",
                              "Zero bending holds only for an ideal infinite uniform floor, uniform load and uniform support.",
                              "No whole-building geotechnical or structural approval is made."]}
    (B / 'results/ground-support-independent.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({"uniform_floor": uniform, "maximum_relative_error": result['maximum_relative_error']}))

if __name__ == '__main__':
    main()
