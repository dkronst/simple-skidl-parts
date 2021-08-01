"""
This module defines power circuits
"""

from re import A
from skidl import *

_R = Part("Device", "R", footprint = 'Resistor_SMD:R_0805_2012Metric', dest=TEMPLATE)

def _get_logic_mosfet(v_signal_min: float, current_max: float) -> Part:
    """
    Chooses the correct logic MOSFET for the application given a minimal signal and maximum
    working current.

    Args:
        v_signal_min (float): Minimum required signal voltage (Vgs(th) might be a good start)
        current_max (float): The maximum current requirement for that part to withstand

    Returns:
        Part: A skidl part with the correct MOSFET
    """
    # For the moment, only two mosfets can be chosen. One for 3.3V and one for 5V.
    assert current_max <= 30
    v33 = Part("Transistor_FET", "IRLIZ44N", footprint="TO-220-3_Vertical")   
    v5 = Part("Transistor_FET", "IRLZ44N", footprint="TO-220-3_Vertical")

    if v_signal_min >= 4.5:
        return v5
    else:
        return v33

@subcircuit
def dc_motor_on_off(gate: Net, vin: Net, gnd: Net, v_signal_min: float = 5, motor_current_max: float = 10) -> None:
    """
    Creates a subcircuit for a simple DC motor on/off mosfet switch (e.g. control a motor with arduino).
    Note: To prevent noise, make sure that the motor's leads have a circ. 100pF capacitor.

    Args:
        gate (Net): The control signal - on is high.
        vin (Net): Connect this pin to the motor's negative side. The other side to the motor's power source.
        gnd (Net): Ground net for both motor and signal
        v_signal_min (float, optional): Defaults to 5 (V).
        motor_current_max (float, optional): Defaults to 10(A).
    """
    mosfet = _get_logic_mosfet(v_signal_min, motor_current_max)
    mosfet[1] += gate
    mosfet[2] += gnd
    mosfet[3] += vin

    # Pull the gate down
    R_pd = _R(value="10K")
    R_pd[1] += gnd
    R_pd[2] += gate

    # protect mosfet
    D = Part("Diode", "1N4001", footprint="D_SOD-123")
    D[1] += vin
    D[2] += gnd


@subcircuit
def low_dropout_power(vin: Net, out: Net, gnd: Net, vin_max: float, vout: float, max_current: float, reverse_polarity_protection: bool) -> Part:
    """
    Creates a Low Dropout power unit for given parameters. The circuit is taken from
    https://www.ti.com/product/UA78?DCM=yes&utm_source=supplyframe&utm_medium=SEP&utm_campaign=not_alldatasheet&dclid=CImvu8_-ivICFQZB9ggdwfQH0w

    Args:
        vin (Net): Power comming in
        out (Net): Connect your device to this net
        gnd (Net): Ground net (common)
        vin_max (float): The maximum voltage allowed as input to this power unit
        vout (float): The requested output voltage
        max_current (float): Maximum allowed current
        reverse_polarity_protection (bool): Add a reverse polarity protection diode

    Returns:
        Part: The subcircuit of this power unit
    """
    
    reg = Part("Regulator_Linear", "LM7805_TO220", footprint="TO-220-3_Vertical")

    C1 = Part("Device", "CP", value = "33uF", footprint="CP_Elec_6.3x5.8")
    C2 = Part("Device", "CP", value = "0.1uF", footprint="CP_Elec_6.3x5.8")

    if reverse_polarity_protection:
        D = Part("Diode", "1N4001", footprint="D_SOD-123")
        n = Net()
        D[1] += vin
        D[2] += n
    else:
        n = vin

    C1[1] += n
    C1[2] += gnd
    C2[1] += out
    C2[2] += gnd

    reg[1] += vin
    reg[2] += gnd
    reg[3] += out
