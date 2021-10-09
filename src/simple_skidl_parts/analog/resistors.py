"""
This module defines resistors and resistor networks

Since most resistors only come in specific values, we cannot just pick whatever we want. 
Additionally, connecting several resistors with low accuracy in parapllel can increase
the resultant accuracy of the complete network.
This module implements these principles.
"""

import math
from skidl import *

@package
def resistor_pack(pin1: Net, pin2: Net, expected_resistance: float, required_accuracy: float):
    pass
