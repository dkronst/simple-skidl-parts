import pytest

import simple_skidl_parts.analog.power as pow
from skidl import *

def test_motor_on_off():
    gnd, gate, to_motor = Net("GND"), Net("GATE"), Net("MOTOR")
    pow.dc_motor_on_off(gate, to_motor, gnd, 5, 10)

    generate_netlist(file_=open("/tmp/lala.net", "w"))

@pytest.mark.parametrize("reverse_pol", [True, False])
def test_regulated_power(reverse_pol):
    gnd, v12, vout = Net("GND"), Net("V12"), Net("V5")
    pow.low_dropout_power(v12, gnd, vout, 12, 5, 0.4, reverse_pol)

    generate_netlist(file_=open("/tmp/lala.net", "w"))
