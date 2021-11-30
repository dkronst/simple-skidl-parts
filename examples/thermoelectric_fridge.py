#!/usr/bin/env python

"""
Create a thermoelectric fridge controller to control motor and peltier from a 12 folt source.
"""

from simple_skidl_parts.analog.power import *
from simple_skidl_parts.analog.vdiv import *
from simple_skidl_parts.units.linear import *
from simple_skidl_parts.analog.led import led_simple, LedSingleColors
from simple_skidl_parts.parts_wrapper import create_bom
from simple_skidl_parts.analog.resistors import small_resistor as R

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
    low_dropout_power(v12, v5, gnd, 16, 5, 0.5, True)

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
    to_bldc_motor = Net("MOTOR-5V")

    wire1 = Net("WIRE")

    dc_motor_on_off(mcu[1], to_motor, gnd)
    dc_motor_on_off(mcu[6], to_tec, gnd)

    wire_resistor = R(4700)

    mcu[2] | wire_resistor[1]
    wire_resistor[2] | wire1

    connect = Part("Connector", "Screw_Terminal_01x02", footprint="TerminalBlock_MetzConnect_Type055_RT01502HDWU_1x02_P5.00mm_Horizontal", dest=TEMPLATE)

    connect_motor, connect_tec, connect_pow, connect_wire_pow, connect_wire_data = connect(5)

    for c, n in zip([connect_motor, connect_tec, connect_pow, connect_wire_pow, connect_wire_data],
            ["MOTOR", "TEC", "PWR", "5V-PWR", "WIRE"]):
        c.ref = n
    
    connect_fan_1, connect_fan_2 = [Part("Connector", "Conn_01x02_Male", footprint="PinHeader_1x02_P2.54mm_Vertical") for _ in range(2)]
    dc_motor_on_off(mcu[5], to_bldc_motor, gnd, v_signal_min=5, motor_current_max=3)

    for c in [connect_fan_1, connect_fan_2]:
        c.ref = to_bldc_motor.name
        c[1] += v5
        c[2] += to_bldc_motor

    led = led_simple(sig_voltage=5.0, color=LedSingleColors.RED, size=1.6)
    led.signal += v5
    led.gnd += to_bldc_motor
    

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

    tvs = Part("Device", "D_TVS_ALT", value="17V", footprint="D_DO-15_P3.81mm_Vertical_KathodeUp")
    for p in range(2):
        tvs[p+1] += connect_motor[p+1]

    connect_tec[1] += to_tec
    connect_tec[2] += v12

    connect_pow[1] += v12
    connect_pow[2] += gnd

    connect_wire_pow[1] += v5
    connect_wire_pow[2] += gnd

    connect_wire_data[1] += wire1
    connect_wire_data[2] += wire1
    
    ERC()

    create_bom("JLCPCB", "/tmp/bom.csv", default_circuit)
    generate_netlist(file_=open("/tmp/netlist.net", "w"))

if __name__ == "__main__":
    main()