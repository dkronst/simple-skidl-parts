#import pytest
from skidl import *
from skidl.pyspice import V, R, gnd, u_V, u_kOhm

from simple_skidl_parts.analog.power import reverse_polarity_protection
import simple_skidl_parts.parts_wrapper


def test_spice():
    reset()
    from skidl.pyspice import gnd

    vs = V(ref="VS", dc_value=1 @ u_V)
    r1 = R(value = 1.3 @ u_kOhm)            # Create a 1.3 Kohm resistor.
    vs['p'] += r1[1]       # Connect one end of the resistor to the positive terminal of the voltage source.
    gnd += vs['n'], r1[2]  # Connect the other end of the resistor and the negative terminal of the source to ground.

    # Simulate the circuit.
    circ = generate_netlist()              # Translate the SKiDL code into a PyCircuit Circuit object.
    sim = circ.simulator()                 # Create a simulator for the Circuit object.
    dc_vals = sim.dc(VS=slice(0, 1, 0.1))  # Run a DC simulation where the voltage ramps from 0 to 1V by 0.1V increments.
    # Get the voltage applied to the resistor and the current coming out of the voltage source.
    voltage = dc_vals.nodes["v-sweep"]
    current = -dc_vals['VS']               # Get the current coming out of the positive terminal of the voltage source.

    # Print a table showing the current through the resistor for the various applied voltages.
    print('{:^7s}{:^7s}'.format('V', ' I (mA)'))
    print('='*15)
    for v, i in zip(voltage.as_ndarray(), current.as_ndarray()*1000):
        print('{:6.2f} {:6.2f}'.format(v, i))
        assert(abs(v - i*1.3) < 0.01)

def mock_part(*args, **kwargs):
    """
    A method that replaces the TrackedPart and Part classes with the
    relevant Spice equivalents.
    """

    from skidl.pyspice import M, R, V, D, gnd, lib_search_paths
    if "SpiceLib" not in lib_search_paths["spice"]:
        lib_search_paths["spice"].append('SpiceLib')
    
    # Search for the spice libraries in the lib_search_paths

    import skidl.pyspice as p
 
    match args:
        case ["Transistor_FET", _]:
            splib = SchLib("ph_fet.lib")
            the_part = Part(splib, "BS250_PH")
            for i, p in zip((1,2,3), "DGS"):
                the_part[i].aliases += [p]
            assert("value" in kwargs)
        case ["Diode", _]:
            splib = SchLib("m_zener.lib")
            if "5v6" in kwargs["value"].lower():
                the_part = Part(splib, "mmqa5v6t1")
            else:
                assert False, f"not implemented {kwargs}"
        case ["Device", "D"]:
            splib = SchLib("on_rect.lib")
            the_part = Part(splib, "1n4001rl")
        case ["Device", "R"]:
            the_part = R()
        case _:
            assert False
    
    return the_part

def test_reverse_pol_protection(monkeypatch):
    """
    Test the reverse polarity protection circuitry in the power module. 
    Use a monkeypatch to override the TrackedPart and Part classes and use
    the Spiced versions instead.
    """
    monkeypatch.setattr(simple_skidl_parts.analog.power, "Part", mock_part)
    monkeypatch.setattr(simple_skidl_parts.analog.power, "TrackedPart", mock_part)
    monkeypatch.setattr(simple_skidl_parts.analog.resistors, "TrackedPart", mock_part)
    reset()
    from skidl.pyspice import gnd

    rpol = reverse_polarity_protection(max_current=2, input_voltage=25)
    vs = V(ref="VS", dc_value=24 @ u_V)
    r1 = R(value = 1 @ u_kOhm)            # Create a 1 Kohm resistor.
    rpol.vin += vs['p']
    rpol.gnd += gnd
    rpol.vout += r1[1]
    r1[2] += gnd
    vs['n'] += r1[2]
    
    circ = generate_netlist()
    sim = circ.simulator()
    dc_vals = sim.dc(VS=slice(-24, 24, 0.1))
    
    voltage = dc_vals.nodes["v-sweep"]
    current = -dc_vals['VS']               # Get the current coming out of the positive terminal of the voltage source.

    # Print a table showing the current through the resistor for the various applied voltages.
    print('{:^7s}{:^7s}'.format('V', ' I (mA)'))
    print('='*15)
    for v, i in zip(voltage.as_ndarray(), current.as_ndarray()*1000):
        print('{:6.2f} {:6.2f}'.format(v, i))
        assert v > 0 or abs(i) < 0.01