"""
This module contains data and data related methods for power related circuits
"""
from typing import List, Tuple
from pathlib import Path

from PIL import Image

_LM2596_INDUCTOR_VALUE_BY_NAME = {
    15: "22uH 0.99A",
    21: "68uH 0.9A", 
    22: "47uH 1.1A", 
    23: "33uH 1.4A", 
    24: "22uH 1.7A", 
    25: "15uH 2.1A", 
    26: "330uH 0.80A",
    27: "220uH 1.00A",
    28: "150uH 1.20A",
    29: "100uH 1.47A",
    30: "68uH 1.78A",
    31: "47uH 2.20A",
    32: "33uH 2.50A",
    33: "22uH 3.10A",
    34: "15uH 3.40A",
    35: "220uH 1.70A",
    36: "150uH 2.10A",
    37: "100uH 2.50A",
    38: "68uH 3.10A",
    39: "47uH 3.50A",
    40: "33uH 3.50A",
    41: "22uH 3.50A",
    42: "150uH 2.70A",
    43: "100uH 3.40A",
    44: "68uH 3.40A"
}


_LM2596_INDUCTOR_KNOWN_POINTS_LOCATION = {
    # The coordinates are picture coords (arbitrary).
    "X": [(209.4, 0.6), (295.34, 0.8), (362.3, 1.0), (476.6, 1.5), (555.71, 2.0), (623.8, 2.5), (676.0, 3.0)],
    "Y": [(182.1, 4.0), (250.0, 6.0), (274.3, 7.0), (296.2, 8.0), (314.1, 9.0), (335.5, 10.0), (404.0, 15.0), (443.0, 20.0), (488.91, 25.0),
          (504.1, 30.0), (556.0, 40.0), (596.24, 50.0), (627.0, 60.0), (648.0, 70.0)]
}

def _get_linear_coord_appx(y_i: float, known_points:List[Tuple[float, float]]) -> float:
    """
    Returns the corresponding X coordinate to a given Y coordinate given a list of known (x,y). 
    This is used when a graph has non uniform coordinates, as is the case in the LM2596 datasheet
    (inductor selection)

    Args:
        y_i: The requested y coordinate
        known_points: A list of known points in the form of [(x,y), (x2, y2)].

    Returns:
        float: A number between 0 and 1 that is where the expected x coordinate should be
    """
    for j, (_, y_j) in enumerate(known_points[:-1]):
        y_n = known_points[j+1][1]
        if y_j <= y_i < y_n:
            break
    x_j, y_j = known_points[j]
    x_n, y_n = known_points[j+1]
    slope = (y_n-y_j)/(x_n-x_j)
    x_i = (y_i - y_j)/slope + x_j
    print(f"Calculated coords: {x_i} = ({y_i} - {y_j})/{slope} + {x_j}, j = {j}")
    x_0 = known_points[0][0]
    x_max = known_points[-1][0]
    return (x_i-x_0)/(x_max-x_0)
        

def get_lm2596_inductor_value(max_current:float, e_t:float) -> str:
    """
    Returns the correct inductor for the lm2596 buck converter
    NOTE: The choice of the inductor is fairly critial for the
    proper functioning of the step-down converter. 

    Args:
        max_current (float): The maximum current rating for the circuit
        e_t (float): The E*T calculated according to the datasheet.

    Returns:
        str: The value(s) for the inductor required
    """
    def _get_max_current_point(i:float, max_x: int) -> int:
        return int(_get_linear_coord_appx(i, _LM2596_INDUCTOR_KNOWN_POINTS_LOCATION["X"])*max_x)

    def _get_et_point(e_t:float, max_y: int) -> int:
        # The y coordinates are inversed in a PNG
        return max_y - int(_get_linear_coord_appx(e_t, _LM2596_INDUCTOR_KNOWN_POINTS_LOCATION["Y"])*max_y)

    img_file = Path(__file__).parent / "lm2596_inductor.png"
    image = Image.open(img_file)

    # according to the datasheet, the x axis starts from 0.6 up to 3.0A 
    # the y axis is 4 to 70 (V*us), however, those are not linearly scaled.
    # We have to approximate it using some linear approximation
    x = _get_max_current_point(max_current, image.size[0]-1)
    assert x < image.size[0]
    y = _get_et_point(e_t, image.size[1]-1)
    assert y < image.size[1]
    l_idx = -1

    while x >= 0:
        l_idx = image.getpixel((x,y))[-1]
        if l_idx in _LM2596_INDUCTOR_VALUE_BY_NAME:
            return _LM2596_INDUCTOR_VALUE_BY_NAME[l_idx]
        else:
            x-=1

    print(f"L index ({max_current} -> {x}, {e_t} -> {y}): {l_idx}")
    assert False, "Cannot find the correct inductor. This is probably a bug (but a different max current value should work around it)"
