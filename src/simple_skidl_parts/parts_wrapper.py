"""
Implement utilities to support various BOM functions, e.g. automatic creation of 
provider specific BOM.
"""

from typing import List
import csv

from skidl import Part, Circuit
from skidl.circuit import Circuit

_JLCPCB_PREAMBLE = "JLCPCB:"

class TrackedPart(Part):
    def __init___(self, *args, **kv):
        """
        This class wraps skidl's Part class to add some information that's only related to
        specific providers (e.g. part numbers)
        """

        if "sku" in kv:
            self.sku = kv.pop("sku")
        else:
            self.sku = None

        super().__init__(*args, **kv)


def _jlcpcb_line_gen(part:Part) -> List[str]:
    sku = part.sku[len(_JLCPCB_PREAMBLE):] if hasattr(part, "sku") \
        and part.sku is not None\
            and part.sku.startswith(_JLCPCB_PREAMBLE) else None

    return [f"{part.name} {part.value}", part.ref, part.footprint, sku]


def create_bom(provider: str, filename: str, circ: Circuit):
    line_gen = _LINE_GENERATORS[provider]
    with open(filename, "w", newline="") as w:
        writer = csv.writer(w)
        writer.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part # (optional)"])
        for part in circ.parts:
            writer.writerow(line_gen(part))

_LINE_GENERATORS = {
    "JLCPCB": _jlcpcb_line_gen,
}
