import math
from restaurant_finder.utils import calculate_distance


def test_calculate_distance_zero():
    assert calculate_distance(0, 0, 0, 0) == 0


def test_calculate_distance_known():
    dist = calculate_distance(35.607, 140.106, 35.608, 140.107)
    assert math.isclose(dist, 143.308, rel_tol=1e-3)
