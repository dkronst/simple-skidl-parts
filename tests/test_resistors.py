from itertools import product
import pytest

import simple_skidl_parts.analog.power as pow
from simple_skidl_parts.units.linear import e_series_number
from skidl import *

@pytest.mark.parametrize("res,expected", [(10.1, 10), (10, 10), (11, 11), (430.1, 430), (423, 430), (1.01, 1.0)])
def test_closest_preferred_number_e24(res, expected):
    assert e_series_number(res, 24) == expected

@pytest.mark.parametrize("res,expected", [(4.593, 4.59), (2.369, 2.37), (3.10, 3.09)])
def test_closest_preferred_number_e192(res, expected):
    assert e_series_number(res, 192) == expected