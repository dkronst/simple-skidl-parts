from itertools import product
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

@pytest.mark.parametrize("v_in,voltage_out,max_current", 
    product([1.6, 3, 5, 6, 9, 12, 15, 19, 24, 28, 32],
    [1.6, 3.3, 5, 12, 24],
    [.25, 0.333, .5, 1.0, 1.5, 2.0, 3.0])
)
def test_buck(v_in, voltage_out, max_current):
    reset()
    if v_in < voltage_out + 0.6:
        print("Voltage difference smaller than 0.6 is not supported")
        return

    gnd, v12, vout = Net("GND"), Net("VIN"), Net("VOUT")
    v12.drive = POWER
    gnd.drive = POWER
    vout.drive = POWER
    pow.buck_step_down(v12, vout, gnd, voltage_out, v_in, max_current)

    ERC()
    
    generate_netlist(file_=open(f"/tmp/buck_test_{v_in}_{voltage_out}_{max_current}.net", "w"))
