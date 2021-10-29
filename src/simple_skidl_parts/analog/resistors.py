"""
This module defines resistors and resistor networks
"""

from skidl import *
from simple_skidl_parts.parts_wrapper import TrackedPart
from ..units.linear import get_value_name

def small_resistor(value: float, e_series: int=24) -> TrackedPart:
    """
    Creates a tracked part with the closest value (in Ohms)

    Args:
        value: The number of ohms for the given resistor
        e_series: The preferred number series to be used (24 for 5%, 48 for 1% and so on)

    Returns:
        TrackedPart: A tracked part with footprint and (hopefully) an SKU.
    """

    val = get_value_name(value, e_series)
    return TrackedPart("Device", "R", value=val)