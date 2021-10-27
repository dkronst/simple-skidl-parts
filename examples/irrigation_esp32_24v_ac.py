#!/usr/bin/env python

"""
Create an irrigation computer that can control various solonoid type latching water valves.
"""

import math
from typing import List, Tuple

from simple_skidl_parts.analog.power import *
from simple_skidl_parts.analog.power import optocoupled_triac_switch
from simple_skidl_parts.analog.vdiv import *
from simple_skidl_parts.units.linear import *
from simple_skidl_parts.parts_wrapper import TrackedPart, create_bom
from simple_skidl_parts.digital.esp import esp32_s2_with_serial_usb
import simple_skidl_parts.digital.esp as esp_module
from simple_skidl_parts.analog.led import led_simple, LedSingleColors

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


def connect_single_row(to_connect: List, ref: str):
    # Connect to a single row
    num_terms = len(to_connect)*2
    connect = Part("Connector", f"Screw_Terminal_01x{num_terms:02d}", footprint="PhoenixContact_MSTBVA_2,5_2-G_1x{num_terms:02d}_P5.00mm_Vertical", ref=ref)
    for i, otc in enumerate(to_connect):
        connect[i*2+1] += otc.load1
        connect[i*2+2] += otc.load2

def connect_terminal_pairs(to_connect: List, ref: str):
    for _, otc in enumerate(to_connect):
        connect = Part("Connector", "Screw_Terminal_01x02", footprint="PhoenixContact_MSTBVA_2,5_2-G_1x02_P5.00mm_Vertical", ref=ref)
        otc.load1 += connect[1]
        otc.load2 += connect[2]


def main():
    num_of_24vac_values = 8
    num_of_9vdc_pulse_valves = 6
    single_row = False

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
    jack = Part("Connector", "Barrel_Jack_Switch_Pin3Ring", footprint="BarrelJack_CUI_PJ-102AH_Horizontal")
    jack["1"] += gnd
    jack["2"] += v24ac
    jack["3"] += NC

    # The MCU: ESP32-S2-WROVER-I (no built-in antenna for better range)
    mcu = TrackedPart("RF_Module", "ESP32-S2-WROVER-I")
    esp = esp32_s2_with_serial_usb(mcu)  # Takes care of USB and power from USB and also programming
    rst_button = TrackedPart("Switch", "SW_SPST")
    esp["~RESET"] += rst_button["A"]
    gnd += rst_button["B"]
    prog_conn = Part("Connector", "Conn_01x06_Female", footprint="PinHeader_1x06_P2.54mm_Vertical")

    esp[3:8] += prog_conn

    # get the best pins to use:
    best_pins = esp_module.get_usable_gpios()
    to_connect = []

    # create switches:
    for _ in range(num_of_24vac_values):
        pin_name = best_pins.pop(0)
        print(f"Using {pin_name} for 24VAC valve")
        p = mcu[pin_name]
        otc = optocoupled_triac_switch(ac_voltage_max=24.0)
        otc.ac1 += v24ac
        otc.ac2 += gnd
        # to_connect.append((otc.load1, otc.load2))
        to_connect.append(otc)
        p += otc.signal
        gnd += otc.gnd


    if single_row:
        connect_single_row(to_connect, "24VAC_SOL")
    else:
        connect_terminal_pairs(to_connect, "24VAC_SOL")
    
    Net.get("+3V3").do_erc = False
    ERC()

    generate_netlist(file_=open("/tmp/irrigation_netlist.net", "w"))
    create_bom("JLCPCB", "/tmp/irrigation_bom.csv", default_circuit)
    # generate_svg()

if __name__ == "__main__":
    main()