"""
Defines things USB
"""

from simple_skidl_parts.parts_wrapper import TrackedPart
from simple_skidl_parts.analog.power import low_dropout_power
from simple_skidl_parts.analog.led import led_simple, LedSingleColors
from skidl import *

@subcircuit
def usb_to_serial(convert_to_voltage: float = 3.3) -> Bus:
    """
    Converts the signal given in USB to UART using a CH340G chip

    Args:
        convert_to_voltage (float, optional): Convert the signal to this voltage. Defaults to 3.3.

    Returns:
        Bus: A set of pins to be used as the UART output and
    """

    usb_connector = TrackedPart("Connector", "USB_C_Receptacle", footprint="MOLEX_105450-0101", sku="JLCPCB:C134092")
    usb_to_uart_chip = TrackedPart("Interface_USB", "CH340G", footprint="SOIC-16_3.9x9.9_P1.27mm", sku="JLCPCB:C14267")

    t_rts, t_dtr = [TrackedPart("Transistor_BJT", "BC847", value="MMBT5551", footprint="SOT-23", sku="JLCPCB:C2145") for a in [1,2]]
    v33 = Net("+3V3")
    gnd = Net("GND")
    v5  = Net("+5V")

    low_dropout_power(v5, v33, gnd, 5.5, 3.3, 1, False)   # No need for reverse polarity protection for USB.

    # For USB we want to have D+ and D- nets so we get a differential trace
    dp, dm = Net("D+"), Net("D-")

    dtr, rts, rx, tx = [Net(sig) for sig in ["DTR", "RTS", "RX", "TX"]]

    crystal = TrackedPart("Device", "Crystal_GND24", value="12MHz", footprint="Crystal_SMD_3225-4Pin_3.2x2.5mm", sku="C97242")
    c_crys1, c_crys2 = [TrackedPart("Device", "C", value="22p") for a in (1,2)]

    for yx, color in zip([rx, tx, v33], [LedSingleColors.RED, LedSingleColors.GREEN, LedSingleColors.BLUE]):
        led = led_simple(sig_voltage=3.3, color=color)
        led.signal += yx
        led.gnd += gnd


    

    
       

    