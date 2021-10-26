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
    bus = slow_usb_type_c_with_power(convert_to_voltage=convert_to_voltage)
    v33 = bus[1]
    gnd = bus["GND"]
    v5  = bus["+5V"]

    usb_to_uart_chip = TrackedPart("Interface_USB", "CH340G", footprint="SOIC-16_3.9x9.9_P1.27mm", sku="JLCPCB:C14267")

    t_rts, t_dtr = [TrackedPart("Transistor_BJT", "BC847", value="MMBT5551", footprint="SOT-23", sku="JLCPCB:C2145") for a in [1,2]]
    dtr, rts, rx, tx, en, ch_pd,  = [Net(sig) for sig in ["DTR", "RTS", "RX", "TX"]]

    crystal = TrackedPart("Device", "Crystal_GND24", value="12MHz", footprint="Crystal_SMD_3225-4Pin_3.2x2.5mm", sku="C97242")
    c_crys1, c_crys2 = [TrackedPart("Device", "C", value="22p") for a in (1,2)]

    for yx, color in zip([rx, tx, v33], [LedSingleColors.RED, LedSingleColors.GREEN, LedSingleColors.BLUE]):
        led = led_simple(sig_voltage=3.3, color=color)
        led.signal += yx
        led.gnd += gnd
    
    r_pd, r_en, r_t1, t_t2 = [TrackedPart("Device", "R", value="10K") for _ in range(4)]


@package
def slow_usb_type_c_with_power(v33, gnd, v5, dp, dm, convert_to_voltage: float=3.3, 
        esd_protection: bool=True):
    """
    Creates a subcircuit with a USB recepticle connector to be used as a "fast" (a.k.a. slow) USB - up to 1.2MB/sec and 
    as a power source.
    
    Args:
        convert_to_voltage (float): What voltage to convert the power to
        esd_protection: Add ESD protection circuit to the bus, Defaults to True

    Returns:
        Bus: A bus with the relevant connections
    """
    usb_connector = TrackedPart("Connector", "USB_C_Receptacle", footprint="MOLEX_105450-0101", sku="JLCPCB:C134092")

    v5.drive = POWER
    gnd.drive = POWER
    v33.drive = POWER

    low_dropout_power(v5, v33, gnd, 5.5, convert_to_voltage, 1, False)

    connect = lambda x,y: x | y
    reduce(connect, usb_connector["GND"] + [gnd])
    reduce(connect, usb_connector["VBUS"] + [v5])

    usb_connector["SHIELD"] += NC

    if esd_protection:
        c_dp = Net("DP+")
        c_dm = Net("DP-")
        esdp = TrackedPart("Power_Protection", "USBLC6-2SC6", footprint="SOT-23-6", sku="JLCPCB:C7519")
        esdp["GND"] += usb_connector["GND"]
        esdp["VBUS"] += usb_connector["VBUS"]
        dp += Net("PROT_USB_D+")
        dm += Net("PROT_USB_D-")
        dp += esdp["6"]
        dm += esdp["4"]
        c_dp += esdp["1"]
        c_dm += esdp["3"]
    else:
        c_dp = dp
        c_dm = dm


    reduce(connect, usb_connector["D+"] + [c_dp])
    reduce(connect, usb_connector["D-"] + [c_dm])
