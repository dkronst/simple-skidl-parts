"""
Define units in the linear realm of electronics (i.e. Ohm's law, etc.)
"""

from rkm_codes import from_rkm, to_rkm

K = 1000
M = 1000*K
G = 1000*M

m = 1E-3
u = 1E-3*m
n = 1E-3*u

def get_value_name(value):
    return to_rkm(value)


    