import numpy as np

DIRECTIONS = {
    'North': np.array([-1, 0]),
    'West': np.array([0, -1]),
    'East': np.array([0, 1]),
    'South': np.array([1, 0])
}

INVERTED_DIRECTIONS = {
    (-1, 0): 'North',
    (0, -1): 'West',
    (0, 1): 'East',
    (1, 0): 'South'
}

SLEEP_TIME = 0.2
RESEND_TIMEOUT = 15