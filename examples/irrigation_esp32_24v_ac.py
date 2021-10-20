#!/usr/bin/env python

"""
Create an irrigation computer that can control various solonoid type latching water valves.
"""

import math

from simple_skidl_parts.analog.power import *
from simple_skidl_parts.analog.vdiv import *
from simple_skidl_parts.units.linear import *
from simple_skidl_parts.parts_wrapper import TrackedPart, create_bom
from simple_skidl_parts.digital.esp import esp32_s2_with_serial_usb

from skidl import *

_R = Part("Device", "R", footprint='Resistor_SMD:R_0805_2012Metric', dest=TEMPLATE)

def connect_power(vout: Net, vin: Net, gnd: Net) -> None:
    """
    Create a stabilized output voltage of 3v3 for the MCU

    Args:
        vout (Net): output voltage (3v3 DC)
        vin (Net): input (24AC)
        gnd (Net): just the ground
    """
    vdc = Net("35VDC")
    vdc.drive = POWER
    full_bridge_rectifier(vin, gnd, vdc, gnd, 0.5, 24*math.sqrt(2))
    buck_step_down(vdc, vout, gnd, 3.1, 24*math.sqrt(2), .75)

def main():
    num_of_24vac_values = 6
    num_of_9vdc_pulse_valves = 6

    v24ac = Net("24VAC")
    v24ac.drive = POWER

    gnd = Net("GND")
    gnd.drive = POWER

    # modules for the irrigation controller
    # power - 24VAC
    # mcu - ESP32 - SMD with USB for programming and debugging
    # wire bus for sensors - for sensors such as light sensor, humidity, temperature, soil, ph etc.
    # valve output - two possible outputs here: 1. 24VAC or 2. pulsed 9-12V DC but you can add more if you wish.
    # Connectors for: 24VAC, programming, valves, sensors

    # power for the MCU:
    v33 = Net("+3V3")
    connect_power(v33, v24ac, gnd)

    # The MCU: ESP32-S2-WROVER-I (no built-in antenna for better range)
    mcu = TrackedPart("RF_Module", "ESP32-S2-WROVER-I")
    esp = esp32_s2_with_serial_usb(mcu)  # Takes care of USB and power from USB and also programming
    rst_button = TrackedPart("Switch", "SW_SPST")
    esp["~RESET"] += rst_button["A"]
    gnd += rst_button["B"]
            
    # connect = Part("Connector", "Screw_Terminal_01x02", footprint="PhoenixContact_MSTBVA_2,5_2-G_1x02_P5.00mm_Vertical", dest=TEMPLATE)

    # for c, n in zip([connect_motor, connect_tec, connect_pow, connect_wire_pow, connect_wire_data],
    #         ["MOTOR", "TEC", "PWR", "5V-PWR", "WIRE"]):
    #     c.ref = n
    
    ERC()

    generate_netlist(file_=open("/tmp/irrigation_netlist.net", "w"))
    create_bom("JLCPCB", "/tmp/irrigation_bom.csv", default_circuit)
    generate_svg()

if __name__ == "__main__":
    main()