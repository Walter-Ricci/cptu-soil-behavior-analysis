import pandas as pd
import pytest

from cptu_analysis.io import prepare_profile


def test_prepare_profile_sorts_and_deduplicates():
    frame = pd.DataFrame({
        "depth": list(range(11, 0, -1)) + [1], "qc": [1] * 12, "fs": [1] * 12,
        "u2": [1] * 12, "qt": [1] * 12, "sigma_v": [1] * 12, "sigma_eff": [1] * 12,
    })
    result = prepare_profile(frame)
    assert result.depth.is_monotonic_increasing
    assert result.depth.is_unique


def test_prepare_profile_rejects_too_few_records():
    frame = pd.DataFrame({c: [1] * 5 for c in ["depth", "qc", "fs", "u2", "qt", "sigma_v", "sigma_eff"]})
    with pytest.raises(ValueError):
        prepare_profile(frame)
