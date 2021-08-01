from skidl import *

from ..units import linear

_R = Part("Device", "R", footprint = 'Resistor_SMD:R_0805_2012Metric', dest=TEMPLATE)

@subcircuit
def vdiv(inp, outp, gnd, resistorBase = _R, ratio=2, rtot=1*linear.M):
    R = resistorBase
    r1 = ratio*rtot/(ratio+1)
    r2 = rtot/(ratio+1)
    inp & R(value = linear.get_value_name(r1)) & outp & \
        R(value = linear.get_value_name(r2)) & gnd