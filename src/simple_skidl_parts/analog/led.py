"""
Module defines usage of LEDs
"""

from typing import Dict
from enum import Enum

from skidl import *

from ..units import linear
from ..parts_wrapper import TrackedPart
from .resistors import small_resistor as _R

class LedSingleColors(Enum):
    # No RGB LEDs since they have more pins
    RED = 0,
    ORANGE = 1,
    YELLOW = 2,
    GREEN = 3,
    BLUE = 4,
    WHITE = 5

def _get_closest_footprint(size: float) -> str:
    """Returns the closest footprint for the given size in mm. 

    Args:
        size (float): Approximate size in milimeters of the LED needed.
    """
    sizes = {
        1.0: "LED_0402_1005Metric",
        1.6: "LED_0603_1608Metric",
        2.0: "LED_0805_2012Metric",
        3.2: "LED_1206_3216Metric"
    }
    best = 999.0
    best_dist = 1.0
    for k in sizes:
        print(f"{k} {size} {abs(size-k)} {best}")
        if abs(size-k) < best_dist:
            best = k
            best_dist = abs(size-k)


    print(f"{k} {size} {best}")
    return sizes[best]

def _get_led_value(footprint: str, color: LedSingleColors) -> Dict:
    _led_by_footprint = {
        "LED_0603_1608Metric": {
            LedSingleColors.ORANGE: {
                "value": "XL-0603QYC", 
                "i_f": 0.02,
                "v_f": 2.1
            },
            LedSingleColors.YELLOW: {
                "value": "XL-0603QYGC",
                "v_f": 2.1,
                "i_f": 0.02
            },
            LedSingleColors.GREEN: {
                "sku": "JLCPCB:C2288",
                "value": "C2288",     # JLCPCB number only - change for your setup.
                "v_f": 2.9,
                "i_f": 0.02
            },
            LedSingleColors.WHITE: {
                "sku": "JLCPCB:C2286",
                "value": "KT-0603W",  # JLCPCB number is: C2286,
                "v_f": 2.8,
                "i_f": 0.02
            },
            LedSingleColors.BLUE: {
                "value": "BL-HB336G-TRB",
                "v_f": 2.9,
                "i_f": 0.03
            },
            LedSingleColors.RED: {
                "sku": "JLCPCB:C2286",
                "value": "KT-0603R",
                "v_f": 2.1,
                "i_f": 0.02
            }
        },
        "LED_0805_2012Metric": {
            LedSingleColors.YELLOW: {
                "sku": "JLCPCB:C2296",
                "value": "17-21SUYC/TR8",   # JLCPCB: C2296
                "v_f": 2.1,
                "i_f": 0.02
            },
            LedSingleColors.BLUE: {
                "sku": "JLCPCB:C2293",
                "value": "XL-0805QBC",   # JLCPCB: C2293
                "v_f": 2.9,
                "i_f": 0.025
            }
        }
    }
    return _led_by_footprint[footprint][color]


@package
def led_simple(signal: Net, gnd: Net, sig_voltage: float, color: LedSingleColors, size: float):
    fp = _get_closest_footprint(size)
    led_data = _get_led_value(fp, color)
    led = TrackedPart("Device", "LED_Small", value=led_data["value"], footprint=fp, sku=led_data.get("sku"))
    led[1] += signal
    i_led = led_data["i_f"]
    led_f = led_data["v_f"]

    r_value = (sig_voltage - led_f)/i_led
    
    r = _R(r_value)
    r[1] += led[2]
    r[2] += gnd

@subcircuit
def led_with_bjt(signal: Net, gnd: Net, vcc: Net, vcc_voltage: float, color: LedSingleColors, size: float):
    """
    Creates an LED with the given parameters that uses a BJT to amplify the signal given and not rely on
    it to provide the current

    Args:
        signal (Net): [description]
        gnd (Net): [description]
        vcc (Net): [description]
        vcc_voltage (float): [description]
        color (LedSingleColors): [description]
        size (float): [description]
    """
    bjt = TrackedPart("Transistor_BJT", "BC847", value="MMBT5551")
    r = _R(10000)
    signal & r[1]
    r[2] & bjt["B"]

    vcc += bjt["C"]
    led = led_simple(sig_voltage=vcc_voltage, color=color, size=size)
    led.signal += bjt["E"]
    led.gnd += gnd
