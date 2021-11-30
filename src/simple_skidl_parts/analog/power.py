"""
This module defines power circuits
"""

import math
from typing import Tuple
from functools import reduce

from re import A
from skidl import *

from ..units import linear
from ..parts_wrapper import TrackedPart
from .power_data import get_lm2596_inductor_value
from .resistors import small_resistor as R

__all__ = ["dc_motor_on_off", "low_dropout_power", "buck_step_down", "full_bridge_rectifier"]

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

    if v_signal_min >= 4.5 and current_max >= 4:
        return Part("Transistor_FET", "IRLZ44N", footprint="TO-220-3_Horizontal_TabDown", value="IRLZ44N")
    elif current_max >= 4:
        return Part("Transistor_FET", "IRLIZ44N", footprint="TO-220-3_Horizontal_TabDown", value="IRLIZ44N")
    
    if v_signal_min >= 2.5:
        return TrackedPart("Transistor_FET", "AO3400A", sku="JLCPCB:C20917", footprint="SOT-23")
    else:
        raise NotImplementedError("Please add a proper MOSFET")

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
    R_pd = R(10000)
    R_pd[1] += gnd
    R_pd[2] += gate

    # protect mosfet from back emf
    D = TrackedPart("Diode", "SM4007", sku="JLCPCB:C64898", footprint="D_SOD-123")
    D["K"] += vin
    D["A"] += gnd


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

    db = TrackedPart("Diode_Bridge", "ABS10", footprint="Diode_SMD:Diode_Bridge_Diotec_ABS")
    dcap1 = TrackedPart("Device", "CP", value="470uF", footprint="Capacitor_SMD:CP_Elec_16x17.5", sku="JLCPCB:C178551")  # Requires 50V - JLCPCB  #C178551
    dcap2 = TrackedPart("Device", "C", value="1uF", footprint="Capacitor_SMD:C_0805_2012Metric", sku="JLCPCB:C28323")  # Requires 50V - JLCPCB  #C28323
    
    assert max_voltage*math.sqrt(2) <= 50  # 50 since the caps are rated 50V.
    assert max_current <= 4.0

    vac1 += db[3]
    vac2 += db[4]

    dc_out_p += db["+"]
    dc_out_m += db["-"]

    for d in [dcap1, dcap2]:
        dc_out_p += d[1]
        dc_out_m += d[2]

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
            2:("470u 4V", "33n"),
            4:("390u 6.3V", "10n"),
            6:("330u 10V", "3n3"),
            9:("180u 16V", "1n5"),
            12:("180u 16V", "1n"),
            15:("120u 16V", "680p"),
            24:("33u 25V", "220p"),
            28:("15u 50V", "220p")
        }
        volt = 1
        for k,v in CAP_DICT.items():
            if volt < output_voltage <= k:
                return v
        # Out is the large one and the FF is the small one
        return v
    
    # The datasheet (TI) https://datasheet.lcsc.com/lcsc/1809192335_Texas-Instruments-LM2596SX-ADJ-NOPB_C29781.pdf
    # Reverse polarity protection should be done with P channel MOSFET. For input voltage above ~12V, use a zenner diode and a large resistor
    # to clamp down the voltage to the gate.
    resistance_r1 = 1000 # Should be between 240Ohm and 1.5K according to datasheet
    regulator = TrackedPart("Regulator_Switching", "LM2596T-ADJ", value="LM2596T-ADJ", sku="JLCPCB:C29781",
            footprint="Package_TO_SOT_SMD:TO-263-5_TabPin3") # JLCPCB #C29781
    c_in = TrackedPart("Device", "CP", value="470uF", footprint="Capacitor_SMD:CP_Elec_16x17.5", sku="JLCPCB:C178551")  # Requires 50V - JLCPCB  #C178551

    if max_current*1.25 <= 1.0 or input_voltage*1.25 <= 40.0:
        d1 = TrackedPart("Device", "D_Schottky", value="B5819W", footprint="Diode_SMD:D_SOD-123", sku="JLCPCB:C8598")
        v_d1 = 0.6
    else:
        #C35722
        d1 = TrackedPart("Device", "D_Schottky", value="SS36-E3/57T", footprint="Diode_SMD:D_SMA", sku="JLCPCB:C35722")
        v_d1 = 0.75


    # Some values:
    # for 100uH 1.5A -> C167258 @ L_12x12mm_H6mm
    l1 = Part("Device", "L", value=get_inductance(v_d1), footprint="Inductor_SMD:L_0805_2012Metric") 
    r1 = R(resistance_r1, 48)  # Requires 1% accuracy or better, recommended metal film res. Locate near FB pin
    capacitance_out, capacitance_ff = get_ff_out_capacitance()
    c_ff = TrackedPart("Device", "C", value=capacitance_ff)
    c_out = TrackedPart("Device", "CP", value=capacitance_out)

    VREF = 1.23   # Volt, see datasheet page 9.
    resistance_r2 = resistance_r1 * (output_voltage/VREF - 1.0)
    r2 = R(resistance_r2, 48)  # Requires at least 1% accuracy
    
    # connect the parts:
    vdiv = Net("FB")

    r1[2] & vdiv 
    vdiv | r2[1]
    vdiv += regulator["FB"]
    vdiv += c_ff[1]
    c_ff[2] | out | r2[2] 
    gnd | r1[1] | regulator["GND"] | regulator[5] | d1[1] 
    gnd | c_out[2] 
    gnd | c_in[2]
    l1[2] += out
    c_out[1] | out
    l1[1] | regulator["OUT"] | d1[2] 

    if input_voltage >= 4:
        rpp = reverse_polarity_protection(input_voltage=input_voltage)
        rpp.vin += vin
        unreg_inp = rpp.vout
        rpp.gnd += gnd
    else:
        unreg_inp = vin

    unreg_inp.drive = vin.drive
    to_vin = Net()
    to_vin.drive = POWER
    c_in[1] | unreg_inp | to_vin
    to_vin & regulator["VIN"]



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
        pfet = TrackedPart("Transistor_FET", "AO3401A", value="AO3401A", footprint="SOT-23", sku="JLCPCB:C15127")

    if input_voltage >= 10:  # 10V for the max gate voltage of the mosfet (AO3401A)
        # Add a zenner diode to clamp the voltage to ~ 5.6V.
        d = TrackedPart("Diode", "ZMMxx", value="ZMM5V6", footprint="D_MiniMELF", sku="JLCPCB:C8062")
        r = R(50E+3)
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
def low_dropout_power(vin: Net, out: Net, gnd: Net, vin_max: float, vout: float, max_current: float, add_reverse_polarity_protection: bool) -> Part:
    """
    Creates a Low Dropout power unit for given parameters. The circuit is taken from
    https://www.ti.com/product/UA78?DCM=yes&utm_source=supplyframe&utm_medium=SEP&utm_campaign=not_alldatasheet&dclid=CImvu8_-ivICFQZB9ggdwfQH0w

    Args:
        vin (Net): Power comming in
        out (Net): Connect your device to this net
        gnd (Net): Ground net (common)/D
        vin_max (float): The maximum voltage allowed as input to this power unit
        vout (float): The requested output voltage
        max_current (float): Maximum allowed current
        add_reverse_polarity_protection (bool): Add a reverse polarity protection diode

    Returns:
        Part: The subcircuit of this power unit
    """
    assert max_current <= 1, "atm not implemented"
    
    if vout == 5.0:
        reg = TrackedPart("Regulator_Linear", "LM78M05_TO252", footprint="TO-252-2", sku="JLCPCB:C55509")  # JLCPCB part #C55509
        C1 = TrackedPart("Device", "C", value = "330p")
        C2 = TrackedPart("Device", "C", value = "100p")
    elif vout == 3.3:
        reg = TrackedPart("Regulator_Linear", "AMS1117-3.3", footprint="SOT-223", sku="JLCPCB:C6186")  # JLCPCB part #C55509
        C1 = TrackedPart("Device", "C", value = "22u")
        C2 = TrackedPart("Device", "C", value = "10u")
    else:
        raise NotImplementedError("only 5V and 3V3 are implemented right now")


    if add_reverse_polarity_protection:
        rpol = reverse_polarity_protection(input_voltage=vin_max, max_current=max_current)
        n = Net.get(vin.name)
        n.drive=POWER
        rpol.vin += vin
        rpol.vout += n
        rpol.gnd += gnd
    else:
        n = vin

    C1[1] += n
    C1[2] += gnd
    C2[1] += out
    C2[2] += gnd

    reg["VI"] += n
    reg["GND"] += gnd
    reg["VO"] += out

def _rc_snub_values(ac_voltage_max: float, ac_freq: float=50.0, max_current_ac: float = 1.5) -> Tuple[float, float]:
    # This uses the same as the calculator for the RC snubber circuit, from: 
    # https://learnabout-electronics.org/Downloads/HIQUEL_SnubberCalculator_AppNote_EN_0100.xls

    # We'll choose some "reasonable" numbers for the snubber. These numbers may be wrong for some
    # applications, but they might be ok for you.
    DV_DT = 5E+6 #sec
    DAMPING_FACTOR = 0.8

    v_p2p = math.sqrt(2)*ac_voltage_max
    l     = ac_voltage_max/(math.pi*2*ac_freq*max_current_ac)
    ω_0   = 0.75*DV_DT/(DAMPING_FACTOR*v_p2p)

    snub_cap = 1/(ω_0*ω_0*l)  # F
    snub_res = 2*DAMPING_FACTOR*math.sqrt(l/snub_cap)

    return snub_res, snub_cap

@package
def optocoupled_triac_switch(ac1: Net, ac2: Net, signal: Net, gnd: Net, load1: Net, load2: Net,
            ac_voltage_max: float, sig_voltage: float=2.7, ac_freq: float=50.0, 
            max_current_ac: float = 1.5):

    # Some more info here:
    # https://slideplayer.com/slide/17171190/
    # https://electronics.stackexchange.com/questions/387080/driving-a-24vac-solenoid-with-arduino-using-a-octocopuler-and-a-triaca
    # https://learnabout-electronics.org/Semiconductors/thyristors_66.php

    snub_res, snub_cap = _rc_snub_values(ac_voltage_max, ac_freq, max_current_ac)
    r_snub = R(snub_res)
    c_snub = TrackedPart("Device", "C", value=linear.get_value_name(snub_cap))

    triac = Part("Triac_Thyristor", "BT138-600", footprint="TO-220-3_Vertical")
    assert max_current_ac <= 12.0, "Current above 12A is not supported currently for this type of switching"

    load2.drive = POWER
    load2 += ac2

    opto = Part("Relay_SolidState", "MOC3020M", footprint="DIP-6_W7.62mm_LongPads")
    v_f_opto = 1.4     # Given in datasheet of VO3020 by Vishay (which I use) - 1.5 max. 
    i_f_opto = 0.02    # Although it can be reduced, this is fine.

    r_val = (sig_voltage - v_f_opto)/i_f_opto

    cur_lim_r = R(r_val)
    opto["1"] += cur_lim_r[1]
    cur_lim_r[2] += signal
    opto["2"] += gnd

    # Holding current on output is around 100μA and the maximum current for the opto-triac
    # is 100mA, so we need a resistor to prevent maximum current and allow minimal holding current
    # The surge that r_surge2 is protecting against is the one from the snubber cap. 
    
    r_surge1 = R((ac_voltage_max*2)/0.9)
    r_surge2 = R(ac_voltage_max/0.1)

    triac["G"] += opto["4"]
    opto["4"] += r_surge2[1]

    out1 = Net("AC-OUT")
    out1.drive = POWER
    ac1.drive = POWER

    triac["A1"] += out1
    r_surge2[2] += out1

    triac["A2"] += ac1
    r_surge1[1] += ac1
    r_surge1[2] += opto["6"]
    
    ac1 & r_snub[1]
    r_snub[2] & c_snub[1]
    c_snub[2] & out1

    # Using a through hole for this part for now
    fuse = Part("Device", "Polyfuse", value=max_current_ac, footprint="Fuse_Bourns_MF-RG300")
    out1 += fuse[1]
    load1 += fuse[2]
    load1.drive = POWER

    # Lastly, protect the opto-triac from surges. The much larger triac should be fine with these.
    tvs = Part("Device", "D_TVS_ALT", value=f"{int(ac_voltage_max*2)}", footprint="Diode_THT:D_DO-15_P3.81mm_Vertical_KathodeUp")
    tvs[1] += opto[4]
    tvs[2] += opto[6]

