"""
Defines packages and circuits for espressif ESP type MCUs
"""

from typing import Tuple

from simple_skidl_parts.parts_wrapper import TrackedPart

from skidl import *
from .usb import slow_usb_type_c_with_power
from ..analog.resistors import small_resistor as _R
from ..analog.led import LedSingleColors, led_with_bjt

def _add_decoupling_caps_esp32(v33: Net, gnd: Net):
    caps = [TrackedPart("Device", "C", value=val) for val in ("100p", "1u", "10u")]
    for c in caps:
        v33 & c[1]
        c[2] & gnd


@package
def _dtr_cts_to_esp(dtr: Net, cts: Net, gnd: Net, flash: Net, rst: Net):
    """
    Create a circuit to support resetting and moving to flash mode using DTR and CTS for FTDI programmers

    Args:
        dtr: Net for DTR's signal from the FTDI
        cts: Net for CTS's signal from the FTDI
        gnd: Net for gnd

    Returns:
        Bus: Bus with 2 pins, CTS for ~FLASH, DTR for ~RESET
    """
    t_cts, t_dtr = [TrackedPart("Transistor_BJT", "BC847", value="MMBT5551") for a in [1,2]]
    dtr & _R(10000) & t_dtr["B"]
    cts & _R(10000) & t_cts["B"]
    gnd | t_cts["E"] | t_dtr["E"]

    flash += t_cts["C"]
    rst += t_dtr["C"]
    

@subcircuit
def esp32_s2_with_serial_usb(mcu: Part) -> Bus:
    """
    Creates a subcircuit that wraps the ESP32-S2 module with the regular stuff and connects it to a type-C USB 
    connector. You have to supply the MCU Part object in the mcu parameter

    Args:
        mcu (Part): ESP32-S2 part

    Returns:
        Bus: A bus with the USB bus (see slow_usb_type_c_with_power), the required communication pins 
        required for FTDI programming, "flash" and "reset" pins that can be directly attached to a switch
        connected to ground.
    """
    usb = slow_usb_type_c_with_power()
    gnd = Net("GND")
    v33 = Net("+3V3")
    v5 = Net("+5V")

    gnd += usb.gnd
    v33 += usb.v33
    v5  += usb.v5
    
    mcu["USB_D+"] += usb.dp
    mcu["USB_D-"] += usb.dm

    v33 += mcu["3V3"]

    _add_decoupling_caps_esp32(v33, gnd)
    for p in mcu["GND"]:
        p += gnd
    
    flash, rst = Net("~FLASH"), Net("~RESET")
    for norm_hi, p in zip([flash, rst], ["IO00", "EN"]):
        norm_hi & _R(10000) & v33
        norm_hi += mcu[p]
    
    dtr, cts = Net("DTR"), Net("CTS")
    auto_flash = _dtr_cts_to_esp(dtr, cts)
    auto_flash.rst += mcu["EN"]
    auto_flash.flash += mcu["IO00"]
    comm = Bus("programming", dtr, mcu["TXD0"], mcu["RXD0"], v33, cts, gnd)

    led_with_bjt(mcu["IO13"], gnd, v33, 3.3, LedSingleColors.GREEN, 1.6)

    return Bus("usb_esp", v33, gnd, v5, comm, flash, rst)
    