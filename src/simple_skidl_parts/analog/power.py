"""
This module defines power circuits
"""

import math
from typing import Tuple

from re import A
from skidl import *

from ..units import linear
from .power_data import get_lm2596_inductor_value

__all__ = ["dc_motor_on_off", "low_dropout_power", "buck_step_down", "full_bridge_rectifier"]

_R = Part("Device", "R", footprint='Resistor_SMD:R_0805_2012Metric', dest=TEMPLATE)

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

    if v_signal_min >= 4.5:
        return Part("Transistor_FET", "IRLZ44N", footprint="TO-220-3_Horizontal_TabDown", value="IRLZ44N")
    else:
        return Part("Transistor_FET", "IRLIZ44N", footprint="TO-220-3_Horizontal_TabDown", value="IRLIZ44N")

@subcircuit
def dc_motor_on_off(gate: Net, vin: Net, gnd: Net, v_signal_min: float = 5, motor_current_max: float = 10) -> None:
    """
    Creates a subcircuit for a simple DC motor on/off mosfet switch (e.g. control a motor with arduino).
    Note: To prevent noise, make sure that the motor's leads have a circ. 100pF capacitor.

    Args:
        gate (Net): The control signal - on is high.
        vin (Net): Connect this net to the motor's negative lead. The other side to the motor's power source.
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

    # protect mosfet from back emf
    D = Part("Diode", "1N4004", footprint="D_SOD-123")
    D[1] += vin
    D[2] += gnd


@subcircuit
def full_bridge_rectifier(vac1: Net, vac2: Net, dc_out_p:Net, dc_out_m:Net, max_current: float = 1.0, max_voltage: float = 24):
    """
    Uses a full-bridge rectifier to rectify an input AC voltage source with enough capacitors to get a somewhat
    clean DC output. To actually use it, it must go through another proper regulator (e.g. linear reg, buck)

    NOTE: Since there's no ground in this subcircuit, consider the implications for DC. 

    Args:
        vac1 (Net): Input AC power source
        vac2 (Net): Input AC power source
        dc_out_p (Net): The resulting DC +
        dc_out_m (Net): The resulting DC -
        max_current (float): Maximum expected current to output (A)
        max_voltage (float): Maximum expected voltage in input(V)
    """

    db = Part("Diode_Bridge", "ABS10", footprint="Diode_SMD:Diode_Bridge_Diotec_ABS")
    dcap1 = Part("Device", "CP", value="470uF", footprint="Capacitor_SMD:CP_Elec_16x17.5")  # Requires 50V - JLCPCB  #C178551
    dcap2 = Part("Device", "C", value="1uF", footprint="Capacitor_SMD:C_0805_2012Metric")  # Requires 50V - JLCPCB  #C28323
    
    assert max_voltage*math.sqrt(2) <= 50  # 50 since the caps are rated 50V.
    assert max_current <= 4.0

    vac1 += db[3]
    vac2 += db[4]

    dc_out_p += db["+"]
    dc_out_m += db["-"]

    for d in [dcap1, dcap2]:
        dc_out_p += c[1]
        dc_out_m += c[2]

@subcircuit
def buck_step_down(vin: Net, out: Net, gnd: Net, output_voltage: float, input_voltage:float, max_current: float):
    """
    Creates a regulated buck (step-down) subcircuit with all the required components. Adds a reverse polarity protection.
    
    Args:
        vin (Net): Unregulated input net
        out (Net): Regulated output net
        gnd (Net): Ground net
        output_voltage (float): The required regulated output voltage
        input_voltage (float): The expected (maximum) input voltage (unregulated)
        max_current (float): Maxiumu current rating for the circuit
    """

    def get_inductance(V_D: float) -> str:
        """
        returns the inductance required for the buck converter. The inductor is the most critical external part
        of this circuit and should be chosen according to a specific logic (as described in the datasheet).

        Args:
            V_D (float): The forward voltage of the diode used in the design

        Returns:
            str: The inductance and current specifications of the inductor to be used
        """
        V_SAT = 1.16
        e_t = (1000/150)*(input_voltage-output_voltage-V_SAT)*(output_voltage+V_D)/(input_voltage-V_SAT+V_D)
        return get_lm2596_inductor_value(max_current, e_t)

    def get_ff_out_capacitance() -> Tuple[str, str]:
        CAP_DICT = {
            2:("470uF 4V", "33nF"),
            4:("390uF 6.3V", "10nF"),
            6:("330uF 10V", "3.3nF"),
            9:("180uF 16V", "1.5nF"),
            12:("180uF 16V", "1nF"),
            15:("120uF 16V", "680pF"),
            24:("33uF 25V", "220pF"),
            28:("15uF 50V", "220pF")
        }
        volt = 1
        for k,v in CAP_DICT.items():
            if volt < output_voltage <= k:
                return v
        return v
    
    # The datasheet (TI) https://datasheet.lcsc.com/lcsc/1809192335_Texas-Instruments-LM2596SX-ADJ-NOPB_C29781.pdf
    # Reverse polarity protection should be done with P channel MOSFET. For input voltage above ~12V, use a zenner diode and a large resistor
    # to clamp down the voltage to the gate.
    resistance_r1 = 1000 # Should be between 240Ohm and 1.5K according to datasheet
    regulator = Part("Regulator_Switching", "LM2596T-ADJ", value="LM2596T-ADJ", 
            footprint="Package_TO_SOT_SMD:TO-263-5_TabPin3") # JLCPCB #C29781
    c_in = Part("Device", "CP", value="470uF", footprint="Capacitor_SMD:CP_Elec_16x17.5")  # Requires 50V - JLCPCB  #C178551

    if max_current*1.25 <= 1.0 or input_voltage*1.25 <= 40.0:
        d1 = Part("Device", "D_Schottky", value="B5819W", footprint="Diode_SMD:D_SOD-123")
        v_d1 = 0.6
    else:
        #C35722
        d1 = Part("Device", "D_Schottky", value="SS36-E3/57T", footprint="Diode_SMD:DO-214AB")
        v_d1 = 0.75


    l1 = Part("Device", "L", value=get_inductance(v_d1), footprint="Inductor_SMD:L_0805_2012Metric") 
    r1 = _R(value=linear.get_value_name(resistance_r1))  # Requires 1% accuracy, recommended metal film res. Locate near FB pin
    capacitance_ff, capacitance_out = get_ff_out_capacitance()
    c_ff = Part("Device", "C", value=capacitance_ff, footprint="Capacitor_SMD:C_0805_2012Metric")
    c_out = Part("Device", "CP", value=capacitance_out, footprint="Capacitor_SMD:CP_Elec_16x17.5")  # Requires 35V

    VREF = 1.23   # Volt, see datasheet page 9.
    resistance_r2 = resistance_r1 * (output_voltage/VREF - 1.0)
    r2 = _R(value=linear.get_value_name(resistance_r2))  # Requires at least 1% accuracy TODO: create correct resistor combination
    
    # connect the parts:
    vdiv = Net("FB")

    r1[2] & vdiv & r2[1]
    vdiv += regulator["FB"]
    vdiv += c_ff[1]
    c_ff[2] += r2[2]
    gnd | r1[1] | regulator["GND"] | regulator[5] | d1[1] | c_out[2] | c_in[2]
    l1[2] += c_out[1]
    l1[1] | regulator["OUT"] | d1[2] | out

    if input_voltage >= 4:
        rpp = reverse_polarity_protection(input_voltage=input_voltage)
        rpp.vin += vin
        unreg_inp = rpp.vout
        rpp.gnd += gnd
    else:
        unreg_inp = vin

    unreg_inp.drive = vin.drive
    c_in[1] | unreg_inp | regulator["VIN"]


@package
def reverse_polarity_protection(vin: Net, gnd: Net, vout: Net, input_voltage: float, max_current: float=1.0):
    """
    Creates a package for reverse-polarity protection using a power mosfet and optionally 
    a zener diode. 

    Args:
        vin (Net): The input power net
        gnd (Net): The ground net
        vout (Net): Output net (protected + polarity)
        input_voltage (float): The voltage required for normal operation
    """
    if max_current >= 4.0:
        pfet = Part("Transistor_FET", "IRF9540N", value="IRF9540N", footprint="TO-220-3_Horizontal_TabDown")
    else:
        # JLCPCB part #C15127
        pfet = Part("Transistor_FET", "AO3401A", value="AO3401A", footprint="SOT-23")

    if input_voltage >= 10:  # 10V for the max gate voltage of the mosfet (AO3401A)
        # Add a zenner diode to clamp the voltage to ~ 5.6V.
        d = Part("Diode", "ZMMxx", value="ZMM5V6", footprint="D_MiniMELF")
        r = _R(value="50K")
        r[1] += d[2]
        r[2] += gnd
        d[1] += vout
        gate_in = r[1]
    else:
        gate_in = gnd
    
    assert input_voltage >= 4, "Currently, only 4V and upwards are supported for reverse polarity protection"

    # The power mosfet is IRF9540N(PbF) in a TO-220AB config.
    pfet["G"] += gate_in
    pfet["D"] += vin
    pfet["S"] += vout


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
    
    reg = Part("Regulator_Linear", "LM78M05_TO252", footprint="TO-252-2")  # JLCPCB part #C55509

    C1 = Part("Device", "CP", value = "33uF", footprint="CP_Elec_6.3x5.4")
    C2 = Part("Device", "CP", value = "0.1uF", footprint="C_0805_2012Metric")

    if reverse_polarity_protection:
        rpol = reverse_polarity_protection(input_voltage=vin_max, max_current=max_current)
        n = Net(vin.name, drive=POWER)
        rpol.vin += vin
        rpol.vout += n
        rpol.gnd += gnd
    else:
        n = vin

    C1[1] += n
    C1[2] += gnd
    C2[1] += out
    C2[2] += gnd

    reg[1] += n
    reg[2] += gnd
    reg[3] += out
