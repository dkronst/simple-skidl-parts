"""
Implement utilities to support various BOM functions, e.g. automatic creation of 
provider specific BOM.
"""

from typing import List, Dict
from pathlib import Path
import json
import csv

from skidl import Part
from skidl.circuit import Circuit

_JLCPCB_PREAMBLE = "JLCPCB:"

def _read_parts_skus() -> Dict:
    d = Path(__file__).parent / "suggested_skus.json"
    return json.load(open(d))
    

class TrackedPart(Part):
    def __init__(self, *args, **kv):
        """
        This class wraps skidl's Part class to add some information that's only related to
        specific providers (e.g. part numbers)
        """

        if "sku" in kv:
            sku = kv.pop("sku")
        else:
            sku = None

        super().__init__(*args, **kv)

        self.sku = sku
        if sku is None:
            key_long = f"{self.name} {self.value}"
            key_short = f"{self.name}"
            
            full = _read_parts_skus()
            if key_long in full:
                all_parts = full[key_long]
            elif key_short in full:
                all_parts = full[key_short]
            else:
                assert False, f"Cannot find tracked part sku/footprint '{key_long}' '{key_short}'"

            if "footprint" not in kv:
                kv["footprint"] = self.footprint = all_parts[0]["footprint"]

            by_footprint = {k["footprint"]:k["sku"] for k in all_parts}
            sku = by_footprint.get(kv["footprint"])


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
