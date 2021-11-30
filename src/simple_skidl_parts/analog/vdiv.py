from skidl import *

from ..units import linear
from .resistors import small_resistor as R

@subcircuit
def vdiv(inp, outp, gnd, ratio=2, rtot=1*linear.M):
    r1 = ratio*rtot/(ratio+1)
    r2 = rtot/(ratio+1)
    inp & R(r1) & outp & \
        R(r2) & gnd