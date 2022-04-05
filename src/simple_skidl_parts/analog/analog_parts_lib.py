

from pathlib import Path
from skidl import *

SSP_LIB_PATH = str((Path(__file__).parent.parent.parent.parent/"skidl_libs"/"External").absolute())

def _create_lib() -> None:
    """
    Create a library with the required parts.
    """
    lib = SchLib(name="External")
    
    tps54331 = Part(name="TPS54331", tool=SKIDL, dest=TEMPLATE)
    tps54331.ref_prefix = "U"
    tps54331.description = "28-V, 3-A non-synchronous buck converter"
    
    pins = [
        Pin(num=1, name="BOOT", func=Pin.types.INPUT),
        Pin(num=2, name="VIN", func=Pin.types.PWRIN),
        Pin(num=3, name="EN", func=Pin.types.INPUT),
        Pin(num=4, name="SS", func=Pin.types.INPUT),
        Pin(num=5, name="VSNS", func=Pin.types.INPUT),
        Pin(num=6, name="COMP", func=Pin.types.INPUT),
        Pin(num=7, name="GND", func=Pin.types.PWRIN),
        Pin(num=8, name="PH", func=Pin.types.PWROUT)
    ]
    for p in pins:
        tps54331 += p
    
    hlk_power = Part(name="HLK_10MXX", tool=SKIDL, dest=TEMPLATE)
    hlk_power.ref_prefix = "U"
    hlk_power.description = "Hilink 10Mxx power supply"
    pins = [
        Pin(num=1, name="ACP", func=Pin.types.PWRIN),
        Pin(num=2, name="ACN", func=Pin.types.PWRIN),
        Pin(num=3, name="VO-", func=Pin.types.PWROUT),
        Pin(num=4, name="VO+", func=Pin.types.PWROUT),
    ]
    lib += tps54331
    lib += hlk_power

    lib.export(SSP_LIB_PATH)

def main() -> None:
    """
    Create a new skidl tool part library to use with this project. Some parts are missing from 
    KiCad and but we still can add them. Only the footprint matters when using skidl
    """
    _create_lib()

if __name__ == "__main__":
    main()
