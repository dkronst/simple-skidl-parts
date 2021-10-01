#!/usr/bin/env python

"""
Create a thermoelectric fridge controller to control motor and peltier from a 12 folt source.
"""

from simple_skidl_parts.analog.power import *
from simple_skidl_parts.analog.vdiv import *
from simple_skidl_parts.units.linear import *
from simple_skidl_parts.analog.led import led_simple, LedSingleColors
from skidl import *


_R = Part("Device", "R", footprint='Resistor_SMD:R_0805_2012Metric', dest=TEMPLATE)

def main():
    v12 = Net("12V")
    v12.drive = POWER

    gnd = Net("GND")
    gnd.drive = POWER

    v5 =  Net("5V")
    v5.drive = POWER
    
    # Create a 5v net
    low_dropout_power(v12, v5, gnd, 16, 5, 20, False)

    mcu = Part("MCU_Microchip_ATtiny", "ATtiny85-20PU", footprint="DIP-8_W7.62mm_LongPads")
    mcu[4] += gnd
    mcu[8] += v5

    # Reminder: 
    # Analog in: A1[7], A2[2], A3[3]
    # Wire: PB3[2]
    # PWM: [5], [6]

    # We'll use PB3 for the 1-wire communications and the A3 for voltage.
    divided = Net("VDIV")
    vdiv(v12, divided, gnd, ratio=4, rtot=10*K)

    mcu[3] += divided

    to_motor = Net("MOTOR")
    to_tec = Net("THEC")

    wire1 = Net("WIRE")

    dc_motor_on_off(mcu[1], to_motor, gnd)
    dc_motor_on_off(mcu[6], to_tec, gnd)

    wire_resistor = _R(value="4K7")

    mcu[2] | wire_resistor[1]
    wire_resistor[2] | wire1

    connect = Part("Connector", "Screw_Terminal_01x02", footprint="PhoenixContact_MSTBVA_2,5_2-G_1x02_P5.00mm_Vertical", dest=TEMPLATE)

    connect_motor, connect_tec, connect_pow, connect_wire_pow, connect_wire_data = connect(5)

    for c, n in zip([connect_motor, connect_tec, connect_pow, connect_wire_pow, connect_wire_data],
            ["MOTOR", "TEC", "PWR", "5V-PWR", "WIRE"]):
        c.ref = n

    # Add LEDs
    for m in [to_motor, to_tec]:
        led = led_simple(sig_voltage=15.0, color=LedSingleColors.RED, size=1.6)
        led.signal += v12
        led.gnd += m

    led = led_simple(sig_voltage=5.0, color=LedSingleColors.YELLOW, size=2.0)
    led.signal += v5
    led.gnd += gnd

    led = led_simple(sig_voltage=5.0, color=LedSingleColors.BLUE, size=2.0)
    led.signal += mcu[5]
    led.gnd += gnd
    
    connect_motor[1] += to_motor
    connect_motor[2] += v12

    connect_tec[1] += to_tec
    connect_tec[2] += v12

    connect_pow[1] += v12
    connect_pow[2] += gnd

    connect_wire_pow[1] += v5
    connect_wire_pow[2] += gnd


    connect_wire_data[1] += wire1
    connect_wire_data[2] += wire1
    
    ERC()

    generate_netlist(file_=open("/tmp/netlist.net", "w"))

if __name__ == "__main__":
    main()