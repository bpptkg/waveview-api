import numpy as np


def clean_outliers(data: np.ndarray) -> np.ndarray:
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


def remove_outliers(data: np.ndarray, window_size: int = 500) -> np.ndarray:
    result = np.zeros_like(data)
    for i in range(len(data) - window_size + 1):
        window = data[i : i + window_size]
        cleaned_window = clean_outliers(window)
        result[i + window_size // 2] = cleaned_window[
            window_size // 2
        ]  # Assign the middle value.
    return result
