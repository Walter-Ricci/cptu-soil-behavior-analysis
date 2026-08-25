"""Numerical methods used by the CPTu workflow.

All stresses and sleeve friction are expressed in kPa; cone resistance is MPa.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter1d

ATMOSPHERIC_PRESSURE_KPA = 100.0
IC_BOUNDS = (1.31, 2.05, 2.60, 2.95, 3.60)
SOIL_CLASS_NAMES = (
    "Dense sand / gravelly sand",
    "Clean sand to silty sand",
    "Silty sand to sandy silt",
    "Clayey silt to silty clay",
    "Clay to silty clay",
    "Organic soil / clay",
)


@dataclass(frozen=True)
class IcComponents:
    ic: np.ndarray
    qtn: np.ndarray
    fr: np.ndarray
    n: np.ndarray


def correct_qt(qc_mpa, u2_kpa, area_ratio: float):
    """Correct cone resistance: qt = qc + (1-a)u2, returned in MPa."""
    if not 0.0 < area_ratio <= 1.0:
        raise ValueError("area_ratio must be in (0, 1].")
    return np.asarray(qc_mpa, float) + (1.0 - area_ratio) * np.asarray(u2_kpa, float) / 1000.0


def compute_ic(qt_mpa, fs_kpa, sigma_v_kpa, sigma_eff_kpa, *, max_iter=50, tol=1e-6):
    """Calculate iterative Robertson (2009) Qtn, Fr and Ic."""
    qt = np.asarray(qt_mpa, float)
    fs = np.asarray(fs_kpa, float)
    sv = np.asarray(sigma_v_kpa, float)
    sve = np.asarray(sigma_eff_kpa, float)
    if not (qt.shape == fs.shape == sv.shape == sve.shape):
        raise ValueError("All arrays must have the same shape.")
    qnet = qt * 1000.0 - sv
    valid = np.isfinite(qnet) & np.isfinite(fs) & np.isfinite(sve) & (qnet > 0) & (fs > 0) & (sve > 0)
    ic = np.full(qnet.shape, np.nan)
    qtn = np.full(qnet.shape, np.nan)
    fr = np.full(qnet.shape, np.nan)
    n = np.full(qnet.shape, np.nan)
    if not valid.any():
        return IcComponents(ic, qtn, fr, n)
    qv, fsv, sev = qnet[valid], fs[valid], sve[valid]
    frv = 100.0 * fsv / qv
    nv = np.ones_like(qv)
    icv = np.full_like(qv, 2.6)
    for _ in range(max_iter):
        qtnv = (qv / ATMOSPHERIC_PRESSURE_KPA) * (ATMOSPHERIC_PRESSURE_KPA / sev) ** nv
        next_ic = np.sqrt((3.47 - np.log10(qtnv)) ** 2 + (np.log10(frv) + 1.22) ** 2)
        next_n = np.minimum(1.0, 0.381 * next_ic + 0.05 * sev / ATMOSPHERIC_PRESSURE_KPA - 0.15)
        if np.max(np.abs(next_ic - icv)) < tol:
            icv, nv = next_ic, next_n
            break
        icv, nv = next_ic, next_n
    qtnv = (qv / ATMOSPHERIC_PRESSURE_KPA) * (ATMOSPHERIC_PRESSURE_KPA / sev) ** nv
    ic[valid], qtn[valid], fr[valid], n[valid] = icv, qtnv, frv, nv
    return IcComponents(ic, qtn, fr, n)


def gaussian_smooth(values, depth_m, sigma_m: float):
    """Centered Gaussian filtering with sigma specified in metres."""
    values, depth = np.asarray(values, float), np.asarray(depth_m, float)
    if values.shape != depth.shape or sigma_m <= 0:
        raise ValueError("Matching arrays and a positive sigma are required.")
    if len(values) < 3:
        return values.copy()
    spacing = float(np.nanmedian(np.diff(depth)))
    if not np.isfinite(spacing) or spacing <= 0:
        raise ValueError("Depth must be strictly increasing.")
    return gaussian_filter1d(values, sigma=sigma_m / spacing, mode="nearest", truncate=3.0)


def soil_class(ic):
    """Return zero-based SBTn classes for Ic values."""
    return np.digitize(np.asarray(ic, float), IC_BOUNDS, right=True)


def transition_count(classes):
    classes = np.asarray(classes)
    return int(np.count_nonzero(classes[1:] != classes[:-1])) if len(classes) > 1 else 0


def layer_table(depth_m, classes):
    """Return contiguous layers as dictionaries with top, base and thickness."""
    z, cls = np.asarray(depth_m, float), np.asarray(classes, int)
    if len(z) == 0:
        return []
    edges = np.r_[z[0], (z[:-1] + z[1:]) / 2, z[-1]]
    starts = np.r_[0, np.flatnonzero(cls[1:] != cls[:-1]) + 1]
    stops = np.r_[starts[1:], len(z)]
    return [
        {"class": int(cls[a]), "top_m": float(edges[a]), "base_m": float(edges[b]),
         "thickness_m": float(edges[b] - edges[a])}
        for a, b in zip(starts, stops)
    ]
