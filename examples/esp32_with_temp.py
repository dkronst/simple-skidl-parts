from re import A
from simple_skidl_parts.analog.power import *
from simple_skidl_parts.analog.power import buck_step_down_regular
from simple_skidl_parts.analog.vdiv import *
from simple_skidl_parts.units.linear import *
from simple_skidl_parts.parts_wrapper import TrackedPart, create_bom
from simple_skidl_parts.analog.led import led_simple, LedSingleColors
from simple_skidl_parts.digital.esp import esp32_wroom_external_programmer

from skidl import *

def main() -> None:
    v12, scl, sda, v33, gnd, miso, mosi = [Net(name) for name in ["12V", "SCL", "SDA", "3V3", "GND", "MISO", "MOSI"]]
    
    v12.drive = POWER
    gnd.drive = POWER
    v33.drive = POWER

    mcu = TrackedPart("RF_Module", "ESP32-WROOM-32D", footprint="ESP32-WROOM-32", sku="JLCPCB:C701343")
    esp32_wroom_external_programmer(mcu, v33, gnd)

    scl += mcu["IO22"]
    sda += mcu["IO21"]
    miso += mcu["IO19"]
    mosi += mcu["IO18"]
    
    led1, led2 = [Part("LED", "WS2812B", footprint="LED_SMD:LED_SK6812MINI_PLCC4_3.5x3.5mm_P1.75mm") for _ in range(2)]
    led1["VDD"] | led2["VDD"] | v33
    led1["VSS"] | led2["VSS"] | gnd
    led1["DIN"] += mcu["IO17"]
    led2["DIN"] += led1["DOUT"]

    led_jst = Part("Connector", "Conn_01x03_Female", label="LED", footprint="PinHeader_1x03_P2.00mm_Vertical")
    led_jst[2] += gnd
    led_jst[1] += v33
    led_jst[3] += led2["DOUT"]

    rx_5v = Net("RX-5V")
    tx    = Net("TX")
    rx    = Net("RX")

    tx += mcu[".*TXD0.*"]  # TXD0
    rx += mcu[".*RXD0.*"]

    led_comm = Part("Connector", "Conn_01x06_Female", label="OPENEVSE-CTRL", footprint="PinHeader_1x06_P2.00mm_Vertical")
    led_comm[1] += gnd
    led_comm[2] += v12
    led_comm[3] += NC
    led_comm[4] += tx
    led_comm[5] += rx_5v
    led_comm[6] += NC
    
    rx_5v & TrackedPart("Diode", "1N4148W") & rx

    prg = Part("Connector", "Conn_01x04_Female", label="PROGRAM", footprint="PinHeader_1x04_P2.00mm_Vertical")
    prg[1] += gnd
    prg[2] += v33
    prg[3] += rx
    prg[4] += tx

    buck_step_down_regular(v12, v33, gnd, 3.3, 15, 4.5, 1.5)

    # Also add a temperature sensor
    temp_sensor = Part("Sensor_Temperature", "MCP9808_MSOP", footprint="MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm_ThermalVias")
    for p in ["A0", "A1", "A2", "GND"]:
        temp_sensor[p] += gnd
    temp_sensor["VDD"] += v33
    temp_sensor["SDA"] += sda
    temp_sensor["SCL"] += scl

    scl & R(4700) & v33 & R(4700) & sda

    ERC()

    generate_netlist(file_="/tmp/esp32_with_temp.net")
    create_bom("JLCPCB", "/tmp/esp_with_temp_bom.csv", default_circuit)

if __name__ == "__main__":
    main()