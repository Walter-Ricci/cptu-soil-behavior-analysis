"""Profile-level sensitivity analysis and engineering diagnostics."""
from __future__ import annotations

import numpy as np

from .core import compute_ic, correct_qt, gaussian_smooth, layer_table, soil_class, transition_count


def estimate_area_ratio(qc, u2, qt, fallback=0.80):
    qc, u2, qt = map(lambda x: np.asarray(x, float), (qc, u2, qt))
    mask = np.isfinite(qc + u2 + qt) & (np.abs(u2) >= 20)
    estimates = 1.0 - (qt[mask] - qc[mask]) * 1000.0 / u2[mask]
    estimates = estimates[(estimates >= 0.60) & (estimates <= 0.95)]
    return (float(np.median(estimates)), "inferred") if len(estimates) >= 10 else (fallback, "assumed")


def analyze_profile(frame, sigmas=(0.05, 0.12, 0.25), thin_layer_m=0.10):
    z = frame.depth.to_numpy(float)
    qc, fs, u2, qt = (frame[c].to_numpy(float) for c in ("qc", "fs", "u2", "qt"))
    sv, sve = frame.sigma_v.to_numpy(float), frame.sigma_eff.to_numpy(float)
    raw = compute_ic(qt, fs, sv, sve).ic
    area_ratio, area_source = estimate_area_ratio(qc, u2, qt)
    valid_pub = np.isfinite(raw) & np.isfinite(frame.ic_published.to_numpy(float))
    pub_error = raw[valid_pub] - frame.ic_published.to_numpy(float)[valid_pub]
    raw_cls, raw_layers = soil_class(raw), layer_table(z, soil_class(raw))
    rough_raw = np.nanstd(np.diff(raw))
    rows, curves = [], {}
    for sigma in sigmas:
        qc_s = gaussian_smooth(qc, z, sigma)
        fs_s = np.maximum(gaussian_smooth(fs, z, sigma), 1e-6)
        u2_s = gaussian_smooth(u2, z, sigma)
        smooth = compute_ic(correct_qt(qc_s, u2_s, area_ratio), fs_s, sv, sve).ic
        smooth_cls, layers = soil_class(smooth), layer_table(z, soil_class(smooth))
        delta = smooth - raw
        rows.append({"sigma_m": sigma, "mae_raw_smooth": float(np.nanmean(abs(delta))),
                     "rmse_raw_smooth": float(np.sqrt(np.nanmean(delta ** 2))),
                     "variability_reduction_pct": float(100 * (1 - np.nanstd(np.diff(smooth)) / rough_raw)),
                     "class_changes_pct": float(100 * np.mean(smooth_cls != raw_cls)),
                     "transitions_before": transition_count(raw_cls),
                     "transitions_after": transition_count(smooth_cls),
                     "layers_before": len(raw_layers), "layers_after": len(layers),
                     "thin_layers_before": sum(x["thickness_m"] < thin_layer_m for x in raw_layers),
                     "thin_layers_after": sum(x["thickness_m"] < thin_layer_m for x in layers)})
        curves[sigma] = smooth
    return {"depth": z, "ic_raw": raw, "ic_smooth": curves[sigmas[0]], "area_ratio": area_ratio,
            "area_ratio_source": area_source, "validation_mae": float(np.nanmean(abs(pub_error))),
            "validation_rmse": float(np.sqrt(np.nanmean(pub_error ** 2))), "sigma_metrics": rows}
