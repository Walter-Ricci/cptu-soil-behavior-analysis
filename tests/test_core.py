import numpy as np
import pytest

from cptu_analysis.core import compute_ic, correct_qt, gaussian_smooth, layer_table, soil_class


def test_qt_correction_respects_units():
    np.testing.assert_allclose(correct_qt([10.0], [500.0], 0.8), [10.1])


def test_robertson_components_are_finite_and_consistent():
    result = compute_ic(np.array([5.0]), np.array([50.0]), np.array([100.0]), np.array([60.0]))
    expected_ic = np.sqrt((3.47 - np.log10(result.qtn)) ** 2 + (np.log10(result.fr) + 1.22) ** 2)
    np.testing.assert_allclose(result.ic, expected_ic, rtol=1e-8)
    assert 0 < result.n[0] <= 1


def test_invalid_effective_stress_returns_nan():
    assert np.isnan(compute_ic([5.0], [50.0], [100.0], [0.0]).ic[0])


def test_gaussian_filter_reduces_impulse_without_depth_shift():
    z = np.arange(0, 1.01, .01)
    values = np.zeros_like(z)
    values[50] = 1
    smooth = gaussian_smooth(values, z, .05)
    assert np.argmax(smooth) == 50
    assert smooth[50] < 1
    np.testing.assert_allclose(smooth[49], smooth[51])


@pytest.mark.parametrize("value, expected", [(1.0, 0), (1.31, 0), (1.5, 1), (2.6, 2), (4.0, 5)])
def test_soil_class_boundaries(value, expected):
    assert soil_class([value])[0] == expected


def test_layer_thicknesses_cover_profile_interval():
    layers = layer_table([0, .1, .2, .3], [0, 0, 1, 1])
    assert len(layers) == 2
    assert sum(x["thickness_m"] for x in layers) == pytest.approx(.3)


def test_area_ratio_validation():
    with pytest.raises(ValueError):
        correct_qt([1], [1], 1.2)
