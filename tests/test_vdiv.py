import pytest

import simple_skidl_parts.analog.vdiv as vdiv
from skidl import *

def test_vdiv1():
    gnd, vin, vout = Net("GND"), Net("Vin"), Net("OUT")
    v = vdiv.vdiv(vin, vout, gnd, ratio=3.0)

    generate_netlist(file_=open("/tmp/lala.net", "w"))


