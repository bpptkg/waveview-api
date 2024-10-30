import unittest

import numpy as np

from waveview.contrib.bpptkg.outliers import remove_outliers


class TestBPPTKGAmplitudeCalculator(unittest.TestCase):
    def test_remove_outliers_no_outliers(self) -> None:
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = remove_outliers(data.copy())
        np.testing.assert_array_equal(result, data)

    def test_remove_outliers_with_outliers(self) -> None:
        data = np.array([1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10])
        expected_result = np.array([1, 2, 3, 4, 5, 0, 6, 7, 8, 9, 10])
        result = remove_outliers(data.copy())
        np.testing.assert_array_equal(result, expected_result)

    def test_remove_outliers_all_outliers(self) -> None:
        data = np.array([0, 0, 0, 0, 0])
        expected_result = np.zeros_like(data)
        result = remove_outliers(data.copy())
        np.testing.assert_array_equal(result, expected_result)

    def test_remove_outliers_mixed_data(self) -> None:
        data = np.array([1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10, -100])
        expected_result = np.array([1, 2, 3, 4, 5, 0, 6, 7, 8, 9, 10, 0])
        result = remove_outliers(data.copy())
        np.testing.assert_array_equal(result, expected_result)

    def test_remove_outliers_empty_array(self) -> None:
        data = np.array([])
        expected_result = np.array([])
        result = remove_outliers(data.copy())
        np.testing.assert_array_equal(result, expected_result)

    def test_remove_outliers_single_value(self) -> None:
        data = np.array([100])
        expected_result = np.array([0])
        result = remove_outliers(data.copy())
        np.testing.assert_array_equal(result, expected_result)

    def test_remove_outliers_identical_values(self) -> None:
        data = np.array([5, 5, 5, 5, 5])
        expected_result = np.array([0, 0, 0, 0, 0])
        result = remove_outliers(data.copy())
        np.testing.assert_array_equal(result, expected_result)


if __name__ == "__main__":
    unittest.main()
