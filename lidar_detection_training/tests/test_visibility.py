import numpy as np

from lidar_training.visibility import FloorFitConfig, count_target_returns, fit_floor_plane, summarize_counts


def test_floor_fit_and_target_count() -> None:
    x, y = np.meshgrid(np.linspace(0.5, 3.0, 20), np.linspace(-0.5, 0.5, 10))
    z = 0.02 * x + 0.01 * y - 1.2
    floor = np.column_stack((x.ravel(), y.ravel(), z.ravel(), np.zeros(x.size)))
    target = np.array([[1.5, 0.1, -1.02, 50.0], [1.55, 0.12, -1.08, 40.0]])
    points = np.vstack((floor, target)).astype(np.float32)
    coefficients = fit_floor_plane(points, FloorFitConfig(z_range_m=(-1.3, -1.1)))
    np.testing.assert_allclose(coefficients, [0.02, 0.01, -1.2], atol=1e-6)
    count, selected = count_target_returns(points, coefficients, (1.5, 0.1))
    assert count == 2
    assert selected[:, 3].tolist() == [50.0, 40.0]


def test_count_summary() -> None:
    summary = summarize_counts(np.array([0, 2, 4, 10]))
    assert summary["mean"] == 4.0
    assert summary["zero_fraction"] == 0.25
    assert summary["under_3_fraction"] == 0.5
    assert summary["under_10_fraction"] == 0.75
