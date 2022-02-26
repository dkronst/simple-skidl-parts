# recreating and refactoring an LCD interface using skidl (See OpenEVSE for the excellent Original)

import math
from re import A
from typing import List, Tuple

from simple_skidl_parts.analog.power import *
from simple_skidl_parts.analog.vdiv import *
from simple_skidl_parts.units.linear import *
from simple_skidl_parts.parts_wrapper import TrackedPart, create_bom
from simple_skidl_parts.analog.led import led_simple, LedSingleColors

from skidl import *

def connect_extender(x: Part, c: Part) -> None:
    # The following is from the datasheet of the LCD
    connects = [
        (2, 14),
        (3, 13),
        (4, 12),
        (5, 11),
        (6, 6),
        (7, 5),
        (8, 4)
    ]
    for xp, cp in connects:
        x[xp] += c[cp]
    

def main() -> None:
    # Several nets are common:
    scl, sda, v5, gnd = [Net(name) for name in ["SCL", "SDA", "V5", "GND"]]

    # Decoupling caps:
    for _ in range(4):
        c = Part("Device", "C", value=".1uF", footprint="C_0805_2012Metric")
        v5 & c & gnd

    # Logic Extender
    x = Part("Interface_Expansion", "MCP23017_SP", footprint="DIP-28_W7.62mm_Socket_LongPads")
    for p in ["A0", "A1", "A2", "VSS"]:
        x[p] += gnd
    for p in ["VDD", "~RESET~"]:
        x[p] += v5
    
    x['SCK'] += scl
    x['SDA'] += sda

    for n in [scl, sda]:
        p = Part("Device", "R", value="4K7", footprint="R_0805_2012Metric")
        n & p & v5

    for _ in range(2):
        jst = Part("Connector", "Conn_01x04_Female", footprint="PinHeader_1x04_P2.00mm_Vertical")
        jst[1] += gnd
        jst[2] += v5
        jst[3] += scl
        jst[4] += sda

    jst = Part("Connector", "Conn_01x03_Female", footprint="PinHeader_1x03_P2.00mm_Vertical")
    jst[1] += gnd
    jst[2] += v5
    jst[3] += x["GPA0"]
    
    # Next, let's connect the RGB for the color LEDs in the RGB screen
    # We will have a solder jumper here to support both anode and cathode configuration for the 
    # LED color pins

    # Start with creating the connector for the LCD:
    lcd_connector = Part("Connector", "Conn_01x18_Male", footprint="PinHeader_1x18_P2.54mm_Vertical")
    lcd_connector[1] += gnd
    lcd_connector[2] += v5
    
    lcd_rgb = Net("LCD_RGB")
    sj = Part("Jumper", "SolderJumper_3_Open", footprint="SolderJumper-3_P1.3mm_Open_Pad1.0x1.5mm")
    sj["C"] += lcd_rgb
    sj["A"] += gnd
    sj["B"] += v5

    lcd_connector[15] += lcd_rgb
    
    connect_extender(x, lcd_connector)
    # Data sheet asks for 0.5V for the contrast pin V0 (led_connector[3])
    vdiv(v5, lcd_connector[3], gnd, ratio=10, rtot=25000)

    # We can use AL5809-15XX to control the current of each backlight channel to exactly 
    # 15mA or AL5890-10XX for 10mA. Depending on the LCD requirement. Those can be
    # switched on and off with 500µs intervals. This translates to 2KHz - which is way
    # more than enough for controlling anything the human eye can distinguish.
    # PowerDI-123
    for color, pin, x_pins in zip(["RED", "GREEN", "BLUE"], [16, 17, 18], ["GPA6", "GPA7", "GPB0"]):
        led_driver = Part("Device", "D", value="AL5809-15XX", footprint="D_PowerDI-123")
        x[x_pins] & led_driver &  lcd_connector[pin] 
    
    # Also add a temperature sensor, just for kicks.
    temp_sensor = Part("Sensor_Temperature", "MCP9808_MSOP", footprint="MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm_ThermalVias")
    for p in ["A0", "A1", "A2", "GND"]:
        temp_sensor[p] += gnd
    temp_sensor["VDD"] += v5
    temp_sensor["SDA"] += sda
    temp_sensor["SCL"] += scl

    # and while we're at it, let's also add a real time clock (with a battery), because we can.
    rtc = Part("Timer_RTC", "DS3231M", footprint="SOIC-16W_7.5x10.3mm_P1.27mm")
    for p in range(6,14):
        rtc[p] += gnd
    rtc["VCC"] += v5
    rtc["SCL"] += scl
    rtc["SDA"] += sda
    bat = Part("Device", "Battery_Cell", footprint="BatteryHolder_Keystone_500")
    bat["+"] += rtc["14"]
    bat["-"] += gnd

    generate_netlist(file_ = open("/tmp/lcd_i2c_netlist.net", "w"))

if __name__ == "__main__":
    main()