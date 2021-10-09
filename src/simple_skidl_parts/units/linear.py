"""
Define units in the linear realm of electronics (i.e. Ohm's law, etc.)
"""

import math
import bisect
from rkm_codes import from_rkm, to_rkm

K = 1000
M = 1000*K
G = 1000*M

m = 1E-3
u = 1E-3*m
n = 1E-3*u

def get_value_name(value):
    return to_rkm(value)

def e_series_number(res: float, series: int) -> float:
    """
    returns the closest E Series number from the preferred list

    Args:
        res (float): [description]
        series (int): Preferred value series to use (e.g. E12 will have an input of 12, E24, 24 and so on.)
        
    Returns:
        float: The resistance of the resistor, in Ohm
    """
    def _calculate_for_e24():
        # some special cases (unknown why it's like that, but that's the way it is)
        # for E24, the values are not as calculated.
        digits = int(math.log10(res))
        E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

        i = bisect.bisect_left(E24, res/math.pow(10, digits))
        j = bisect.bisect_right(E24, res/math.pow(10, digits))
        
        decade = math.pow(10, digits)
        return [decade*E24[i], decade*E24[j-1]]


    e_value = series*math.log10(res)

    if series == 24:
        possible = _calculate_for_e24()
    else:
        possible = [math.pow(10, x/series) for x in (int(e_value), int(e_value+0.5))]

    # choose the best one:
    result = possible[0] if abs(possible[0]-res) < abs(possible[1]-res) else possible[1]
    round_to = int(math.log10(res))
    num_of_sig_digits = 1 if series < 48 else 2
    return round(result, -round_to + num_of_sig_digits)
