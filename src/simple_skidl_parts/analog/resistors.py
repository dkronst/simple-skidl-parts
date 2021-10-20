"""
This module defines resistors and resistor networks
"""

from skidl import *
from simple_skidl_parts.parts_wrapper import TrackedPart
from ..units.linear import get_value_name

def small_resistor(value: float) -> TrackedPart:
    """
    Creates a tracked part with the closest value (in Ohms)

    Args:
        value: The number of ohms for the given resistor

    Returns:
        TrackedPart: A tracked part with footprint and (hopefully) an SKU.
    """

    val = get_value_name(value, 24)
    return TrackedPart("Device", "R", value=val)