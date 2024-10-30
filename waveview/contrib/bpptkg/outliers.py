import numpy as np


def remove_outliers(data: np.ndarray) -> np.ndarray:
    if len(data) == 0:
        return data
    q1 = np.quantile(data, 0.1)
    q3 = np.quantile(data, 0.9)
    iqr = q3 - q1
    threshold = 1.5 * iqr

    lower_bound = q1 - threshold
    upper_bound = q3 + threshold
    data[(data <= lower_bound) | (data >= upper_bound)] = 0
    return data
