#!/usr/bin/env python3
"""Génère le projet KiCad du scanner LiDAR (schéma de câblage modules)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = "lidar"


def uid() -> str:
    return str(uuid.uuid4())


def fmt_effects(justify: str = "left", hide: bool = False) -> str:
    hide_s = " hide" if hide else ""
    return f"(effects (font (size 1.27 1.27)) (justify {justify}){hide_s})"


def sym_prop(name: str, value: str, x: float, y: float, hide: bool = False) -> str:
    return (
        f'    (property "{name}" "{value}" (at {x} {y} 0)\n'
        f"      {fmt_effects(hide=hide)})\n"
    )


def sym_pin(number: str, name: str, x: float, y: float, angle: int,
            ptype: str = "passive", shape: str = "line") -> str:
    return f"""    (pin {ptype} {shape} (at {x} {y} {angle})
      (length 2.54)
      (name "{name}" (effects (font (size 1.27 1.27))))
      (number "{number}" (effects (font (size 1.27 1.27))))
    )"""


def module_symbol(lib_name: str, ref_prefix: str, description: str,
                  left_pins: list[tuple[str, str]], right_pins: list[tuple[str, str]]) -> str:
    """Rectangle module with pins on left (even y) and right sides."""
    n = max(len(left_pins), len(right_pins), 1)
    h = n * 5.08
    y0 = -h / 2 + 2.54
    body = f"""  (symbol "{lib_name}"
    (pin_names (offset 1.016) (hide yes))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
{sym_prop("Reference", ref_prefix, 0, h / 2 + 2.54, hide=True)}
{sym_prop("Value", lib_name.split(":")[1], 0, -h / 2 - 2.54, hide=True)}
{sym_prop("Footprint", "", 0, 0, hide=True)}
{sym_prop("Datasheet", "~", 0, 0, hide=True)}
{sym_prop("Description", description, 0, 0, hide=True)}
    (symbol "{lib_name.split(':')[1]}_0_1"
      (rectangle (start -5.08 {-h / 2:.3f}) (end 5.08 {h / 2:.3f})
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
    )
    (symbol "{lib_name.split(':')[1]}_1_1"
"""
    for i, (num, name) in enumerate(left_pins):
        y = y0 + i * 5.08
        body += sym_pin(num, name, -5.08, y, 180) + "\n"
    for i, (num, name) in enumerate(right_pins):
        y = y0 + i * 5.08
        body += sym_pin(num, name, 5.08, y, 0) + "\n"
    body += """    )
    (embedded_fonts no)
  )
"""
    return body


def std_resistor() -> str:
    return """  (symbol "Device:R"
    (pin_numbers hide)
    (pin_names (offset 0))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "R" (at 2.032 0 90)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "R" (at 0 0 90)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "" (at -1.778 0 90)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (property "Datasheet" "~" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (property "Description" "Resistor" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (symbol "R_0_1"
      (rectangle (start -1.016 -2.54) (end 1.016 2.54)
        (stroke (width 0.254) (type default))
        (fill (type none))
      )
    )
    (symbol "R_1_1"
      (pin passive line (at 0 3.81 270)
        (length 1.27)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 0 -3.81 90)
        (length 1.27)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
    (embedded_fonts no)
  )
"""


def std_cap() -> str:
    return """  (symbol "Device:C"
    (pin_numbers hide)
    (pin_names (offset 0.254))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "C" (at 0.635 2.54 0)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "C" (at 0.635 -2.54 0)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "" (at 0.9652 -3.81 0)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (property "Datasheet" "~" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (property "Description" "Unpolarized capacitor" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (symbol "C_0_1"
      (polyline
        (pts (xy -2.032 -0.762) (xy 2.032 -0.762))
        (stroke (width 0.508) (type default))
        (fill (type none))
      )
      (polyline
        (pts (xy -2.032 0.762) (xy 2.032 0.762))
        (stroke (width 0.508) (type default))
        (fill (type none))
      )
    )
    (symbol "C_1_1"
      (pin passive line (at 0 3.81 270)
        (length 2.794)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 0 -3.81 90)
        (length 2.794)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
    (embedded_fonts no)
  )
"""


def std_power(name: str, value: str) -> str:
    return f"""  (symbol "power:{name}"
    (power)
    (pin_numbers hide)
    (pin_names (offset 0) hide)
    (exclude_from_sim yes)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "#PWR" (at 0 -3.81 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{value}" (at 0 3.556 0)
      (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Description" "Power symbol creates a global label with name \\"{value}\\"" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (symbol "{name}_0_1"
      (polyline
        (pts (xy 0 0) (xy 0 2.54))
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (polyline
        (pts (xy 0 2.54) (xy -0.762 1.778) (xy 0.762 1.778) (xy 0 2.54))
        (stroke (width 0) (type default))
        (fill (type none))
      )
    )
    (symbol "{name}_1_1"
      (pin power_in line (at 0 0 90)
        (length 0)
        (name "{value}" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
    )
    (embedded_fonts no)
  )
"""


def std_motor() -> str:
    return """  (symbol "Device:Motor_DC"
    (pin_numbers hide)
    (pin_names (offset 0.254) (hide yes))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "M" (at 2.032 0 90)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "Motor_DC" (at 2.032 0 90)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "" (at 1.524 0 90)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (property "Datasheet" "~" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (property "Description" "Motor" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (justify left) hide))
    (symbol "Motor_DC_0_1"
      (circle (center 0 0) (radius 2.54)
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
      (polyline
        (pts (xy -1.651 1.905) (xy -0.762 1.905) (xy -0.762 2.794) (xy 0.762 0.508) (xy 0.762 -0.381) (xy -0.762 -2.794) (xy -0.762 -1.905) (xy -1.651 -1.905))
        (stroke (width 0.254) (type default))
        (fill (type none))
      )
    )
    (symbol "Motor_DC_1_1"
      (pin passive line (at 0 5.08 270)
        (length 2.54)
        (name "+" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 0 -5.08 90)
        (length 2.54)
        (name "-" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
    (embedded_fonts no)
  )
"""


def lib_symbols() -> str:
    parts = [
        module_symbol("lidar:PowerBank", "BAT", "Power bank USB-C PD 100 W",
                      [("1", "USB-C+")], [("2", "USB-C-")]),
        module_symbol("lidar:TriggerPD", "U", "Module trigger USB-C PD → 12 V",
                      [("1", "USB-C"), ("2", "GND")], [("3", "+12V")]),
        module_symbol("lidar:Buck12-5", "U", "Convertisseur buck 12 V → 5 V 3 A",
                      [("1", "+12V"), ("2", "GND")], [("3", "+5V"), ("4", "GND")]),
        module_symbol("lidar:ESP32-S3", "U", "ESP32-S3 DevKitC-1 N16R8",
                      [("1", "3V3"), ("2", "GND"), ("3", "5V/VIN"), ("4", "GPIO0"),
                       ("5", "GPIO4"), ("6", "GPIO5"), ("7", "GPIO6"), ("8", "GPIO7"),
                       ("9", "GPIO8"), ("10", "GPIO9")],
                      [("11", "GPIO15"), ("12", "GPIO16"), ("13", "GPIO17"),
                       ("14", "GPIO18"), ("15", "GND"), ("16", "3V3")]),
        module_symbol("lidar:LD19", "LD", "LiDAR LD19 (JST 4p, tête tournante)",
                      [("1", "VCC"), ("2", "GND")], [("3", "TX"), ("4", "PWM")]),
        module_symbol("lidar:MPU6050", "U", "MPU6050 GY-521 (base fixe)",
                      [("1", "VCC"), ("2", "GND"), ("3", "SDA"), ("4", "SCL")],
                      [("5", "AD0")]),
        module_symbol("lidar:TMC2209", "U", "Driver TMC2209 v2.0",
                      [("1", "VM"), ("2", "GND"), ("3", "VIO"), ("4", "MS1"), ("5", "MS2")],
                      [("6", "STEP"), ("7", "DIR"), ("8", "EN"), ("9", "PDN_UART"),
                       ("10", "DIAG"), ("11", "A+"), ("12", "A-"), ("13", "B+"), ("14", "B-")]),
        std_resistor(),
        std_cap(),
        std_power("GND", "GND"),
        std_power("+12V", "+12V"),
        std_power("+5V", "+5V"),
        std_power("+3V3", "+3V3"),
        std_motor(),
    ]
    return "(lib_symbols\n" + "".join(parts) + ")\n"


def placed_symbol(lib_id: str, ref: str, value: str, x: float, y: float, rot: int,
                  pin_count: int, root_uuid: str, desc: str = "") -> str:
    su = uid()
    pins = ""
    for i in range(1, pin_count + 1):
        pins += f'    (pin "{i}" (uuid "{uid()}"))\n'
    return f"""(symbol
  (lib_id "{lib_id}")
  (at {x} {y} {rot})
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board no)
  (dnp no)
  (uuid "{su}")
  (property "Reference" "{ref}" (at {x + 5} {y - 5} 0)
    {fmt_effects()})
  (property "Value" "{value}" (at {x + 5} {y + 5} 0)
    {fmt_effects()})
  (property "Footprint" "" (at {x} {y} 0)
    {fmt_effects(hide=True)})
  (property "Datasheet" "~" (at {x} {y} 0)
    {fmt_effects(hide=True)})
  (property "Description" "{desc}" (at {x} {y} 0)
    {fmt_effects(hide=True)})
{pins}  (instances
    (project "{PROJECT}"
      (path "/{root_uuid}" (reference "{ref}") (unit 1))
    )
  )
)
"""


def power_flag(value: str, x: float, y: float, root_uuid: str, ref_num: int) -> str:
    lib = f"power:{value}" if value != "GND" else "power:GND"
    su = uid()
    return f"""(symbol
  (lib_id "{lib}")
  (at {x} {y} 0)
  (unit 1)
  (exclude_from_sim yes)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (uuid "{su}")
  (property "Reference" "#PWR{ref_num:02d}" (at {x} {y - 3} 0)
    {fmt_effects(hide=True)})
  (property "Value" "{value}" (at {x} {y + 3} 0)
    {fmt_effects()})
  (property "Footprint" "" (at {x} {y} 0)
    {fmt_effects(hide=True)})
  (property "Datasheet" "" (at {x} {y} 0)
    {fmt_effects(hide=True)})
  (pin "1" (uuid "{uid()}"))
  (instances
    (project "{PROJECT}"
      (path "/{root_uuid}" (reference "#PWR{ref_num:02d}") (unit 1))
    )
  )
)
"""


def wire(x1, y1, x2, y2) -> str:
    return f"""(wire
  (pts (xy {x1} {y1}) (xy {x2} {y2}))
  (stroke (width 0) (type default))
  (uuid "{uid()}")
)
"""


def label(name: str, x: float, y: float, rot: int = 0) -> str:
    return f"""(label "{name}"
  (at {x} {y} {rot})
  (fields_autoplaced)
  {fmt_effects()}
  (uuid "{uid()}")
)
"""


def global_label(name: str, x: float, y: float, rot: int = 0, shape: str = "input") -> str:
    return f"""(global_label "{name}"
  (shape {shape})
  (at {x} {y} {rot})
  (fields_autoplaced)
  {fmt_effects()}
  (uuid "{uid()}")
  (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0)
    {fmt_effects(hide=True)})
)
"""


def text_note(x: float, y: float, content: str, size: float = 1.27) -> str:
    return f"""(text "{content}"
  (exclude_from_sim yes)
  (at {x} {y} 0)
  (effects (font (size {size} {size})) (justify left bottom))
  (uuid "{uid()}")
)
"""


def no_connect(x: float, y: float) -> str:
    return f"""(no_connect (at {x} {y}) (uuid "{uid()}"))
"""


def schematic(root_uuid: str) -> str:
    body = []
    pwr = 1

    def pwr_sym(val: str, x: float, y: float) -> None:
        nonlocal pwr
        body.append(power_flag(val, x, y, root_uuid, pwr))
        pwr += 1

    # --- Alimentation (haut) ---
    body.append(placed_symbol("lidar:PowerBank", "BAT1", "USB-C PD 100W",
                              30, 35, 0, 2, root_uuid, "Power bank"))
    body.append(placed_symbol("lidar:TriggerPD", "U2", "Trigger PD 12V",
                              90, 35, 0, 3, root_uuid))
    body.append(placed_symbol("lidar:Buck12-5", "U4", "Buck 12→5V 3A",
                              160, 35, 0, 4, root_uuid))
    body.append(wire(55, 35, 65, 35))
    body.append(wire(115, 35, 135, 35))
    body.append(global_label("+12V", 125, 35, 0, "output"))
    body.append(wire(125, 35, 135, 35))
    body.append(global_label("+5V", 195, 35, 0, "output"))

    # --- ESP32 centre ---
    body.append(placed_symbol("lidar:ESP32-S3", "U1", "ESP32-S3 DevKitC-1",
                              120, 110, 0, 16, root_uuid))
    pwr_sym("+5V", 95, 97.46)
    body.append(wire(95, 97.46, 114.92, 97.46))
    pwr_sym("GND", 95, 102.54)
    body.append(wire(95, 102.54, 114.92, 102.54))
    pwr_sym("+3V3", 95, 107.62)
    body.append(wire(95, 107.62, 114.92, 107.62))

    # --- LD19 (gauche) ---
    body.append(placed_symbol("lidar:LD19", "LD1", "LD19",
                              30, 95, 0, 4, root_uuid))
    pwr_sym("+5V", 55, 87.62)
    body.append(wire(55, 87.62, 60, 87.62))
    body.append(wire(60, 87.62, 60, 92.54))
    body.append(wire(60, 92.54, 65, 92.54))
    pwr_sym("GND", 55, 97.54)
    body.append(wire(55, 97.54, 65, 97.54))
    body.append(label("LD19_TX", 70, 100.08, 0))
    body.append(wire(65, 100.08, 70, 100.08))
    body.append(label("LD19_PWM", 70, 105.16, 0))
    body.append(wire(65, 105.16, 70, 105.16))
    body.append(label("LD19_TX", 114.92, 145.16, 180))
    body.append(wire(70, 100.08, 114.92, 145.16))
    body.append(label("LD19_PWM", 114.92, 140.08, 180))
    body.append(wire(70, 105.16, 114.92, 140.08))

    # --- MPU6050 (gauche bas) ---
    body.append(placed_symbol("lidar:MPU6050", "U5", "MPU6050 GY-521",
                              30, 145, 0, 5, root_uuid))
    pwr_sym("+3V3", 55, 137.62)
    body.append(wire(55, 137.62, 65, 137.62))
    pwr_sym("GND", 55, 147.54)
    body.append(wire(55, 147.54, 65, 147.54))
    body.append(no_connect(60, 157.54))
    body.append(wire(65, 157.54, 60, 157.54))
    body.append(text_note(62, 160, "AD0→GND (0x68)", 1.0))
    body.append(label("I2C_SDA", 70, 147.62, 0))
    body.append(wire(65, 147.62, 70, 147.62))
    body.append(label("I2C_SCL", 70, 152.7, 0))
    body.append(wire(65, 152.7, 70, 152.7))
    body.append(label("I2C_SDA", 114.92, 132.54, 180))
    body.append(wire(70, 147.62, 114.92, 132.54))
    body.append(label("I2C_SCL", 114.92, 127.46, 180))
    body.append(wire(70, 152.7, 114.92, 127.46))

    # --- TMC2209 (droite) ---
    body.append(placed_symbol("lidar:TMC2209", "U3", "TMC2209",
                              210, 95, 0, 14, root_uuid))
    pwr_sym("+12V", 200, 87.62)
    body.append(wire(200, 87.62, 204.92, 87.62))
    pwr_sym("GND", 200, 97.54)
    body.append(wire(200, 97.54, 204.92, 97.54))
    pwr_sym("+3V3", 200, 102.62)
    body.append(wire(200, 102.62, 204.92, 102.62))
    pwr_sym("GND", 200, 107.7)
    body.append(wire(200, 107.7, 204.92, 107.7))
    pwr_sym("GND", 200, 112.78)
    body.append(wire(200, 112.78, 204.92, 112.78))

    # STEP DIR EN
    for net, pin_y, gpio in [("TMC_STEP", 120.08, "GPIO4"),
                              ("TMC_DIR", 125.16, "GPIO5"),
                              ("TMC_EN", 130.24, "GPIO6")]:
        body.append(label(net, 125.08, pin_y, 0))
        body.append(wire(125.08, pin_y, 204.92, pin_y))
        body.append(label(net, 204.92, pin_y, 0))

    # UART 1-wire + R1
    body.append(label("TMC_UART", 125.08, 135.32, 0))
    body.append(wire(125.08, 135.32, 145, 135.32))
    su = uid()
    body.append(f"""(symbol
  (lib_id "Device:R")
  (at 155 135.32 0)
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (uuid "{su}")
  (property "Reference" "R1" (at 158 133 0) {fmt_effects()})
  (property "Value" "1k" (at 158 137 0) {fmt_effects()})
  (property "Footprint" "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal" (at 155 135.32 0)
    {fmt_effects(hide=True)})
  (property "Datasheet" "~" (at 155 135.32 0) {fmt_effects(hide=True)})
  (pin "1" (uuid "{uid()}"))
  (pin "2" (uuid "{uid()}"))
  (instances
    (project "{PROJECT}"
      (path "/{root_uuid}" (reference "R1") (unit 1))
    )
  )
)
""")
    body.append(wire(145, 135.32, 151.46, 135.32))
    body.append(wire(158.54, 135.32, 165, 135.32))
    body.append(label("TMC_UART", 165, 135.32, 0))
    body.append(wire(165, 135.32, 204.92, 135.32))
    body.append(label("TMC_UART", 125.08, 145.16, 0))
    body.append(wire(125.08, 145.16, 165, 145.16))
    body.append(wire(165, 145.16, 165, 135.32))
    body.append(label("TMC_DIAG", 125.08, 150.24, 0))
    body.append(wire(125.08, 150.24, 204.92, 150.24))
    body.append(label("TMC_DIAG", 204.92, 150.24, 0))

    # Moteur
    body.append(placed_symbol("Device:Motor_DC", "M1", "NEMA 17",
                              280, 120, 0, 2, root_uuid))
    body.append(label("MOT_A", 235, 120.08, 0))
    body.append(wire(235, 120.08, 275, 115))
    body.append(label("MOT_B", 235, 130.24, 0))
    body.append(wire(235, 130.24, 275, 125))

    # Condensateurs de découplage
    for ref, val, x, y in [("C1", "100nF", 175, 55), ("C2", "100nF", 185, 55)]:
        su = uid()
        body.append(f"""(symbol
  (lib_id "Device:C")
  (at {x} {y} 0)
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (uuid "{su}")
  (property "Reference" "{ref}" (at {x + 3} {y - 2} 0) {fmt_effects()})
  (property "Value" "{val}" (at {x + 3} {y + 2} 0) {fmt_effects()})
  (property "Footprint" "" (at {x} {y} 0) {fmt_effects(hide=True)})
  (property "Datasheet" "~" (at {x} {y} 0) {fmt_effects(hide=True)})
  (pin "1" (uuid "{uid()}"))
  (pin "2" (uuid "{uid()}"))
  (instances
    (project "{PROJECT}"
      (path "/{root_uuid}" (reference "{ref}") (unit 1))
    )
  )
)
""")
        pwr_sym("+12V" if ref == "C1" else "+5V", x, y - 3.81)
        body.append(wire(x, y - 3.81, x, y - 1.016))
        pwr_sym("GND", x, y + 3.81)
        body.append(wire(x, y + 1.016, x, y + 3.81))

    # Notes
    body.append(text_note(30, 185,
                          "Schéma de câblage modules — pas de PCB. Voir docs/wiring.md", 1.4))
    body.append(text_note(30, 190,
                          "GPIO33-37 interdits (PSRAM). LD19 TX → ESP32 GPIO18 (RX).", 1.2))
    body.append(text_note(30, 195,
                          "MS1=MS2=GND sur TMC2209. Masse commune obligatoire.", 1.2))

    sch_uuid = uid()
    return f"""(kicad_sch
  (version 20231120)
  (generator "lidar-generate_kicad")
  (generator_version "1.0")
  (uuid "{sch_uuid}")
  (paper "A3")
{lib_symbols()}
{"".join(body)}
  (sheet_instances
    (path "/{root_uuid}" (page "1"))
  )
  (embedded_fonts no)
)
"""


def kicad_sym_file() -> str:
    """Bibliothèque externe (symboles modules uniquement)."""
    mods = [
        module_symbol("lidar:PowerBank", "BAT", "Power bank USB-C PD 100 W",
                      [("1", "USB-C+")], [("2", "USB-C-")]),
        module_symbol("lidar:TriggerPD", "U", "Module trigger USB-C PD → 12 V",
                      [("1", "USB-C"), ("2", "GND")], [("3", "+12V")]),
        module_symbol("lidar:Buck12-5", "U", "Convertisseur buck 12 V → 5 V 3 A",
                      [("1", "+12V"), ("2", "GND")], [("3", "+5V"), ("4", "GND")]),
        module_symbol("lidar:ESP32-S3", "U", "ESP32-S3 DevKitC-1 N16R8",
                      [("1", "3V3"), ("2", "GND"), ("3", "5V/VIN"), ("4", "GPIO0"),
                       ("5", "GPIO4"), ("6", "GPIO5"), ("7", "GPIO6"), ("8", "GPIO7"),
                       ("9", "GPIO8"), ("10", "GPIO9")],
                      [("11", "GPIO15"), ("12", "GPIO16"), ("13", "GPIO17"),
                       ("14", "GPIO18"), ("15", "GND"), ("16", "3V3")]),
        module_symbol("lidar:LD19", "LD", "LiDAR LD19 (JST 4p, tête tournante)",
                      [("1", "VCC"), ("2", "GND")], [("3", "TX"), ("4", "PWM")]),
        module_symbol("lidar:MPU6050", "U", "MPU6050 GY-521 (base fixe)",
                      [("1", "VCC"), ("2", "GND"), ("3", "SDA"), ("4", "SCL")],
                      [("5", "AD0")]),
        module_symbol("lidar:TMC2209", "U", "Driver TMC2209 v2.0",
                      [("1", "VM"), ("2", "GND"), ("3", "VIO"), ("4", "MS1"), ("5", "MS2")],
                      [("6", "STEP"), ("7", "DIR"), ("8", "EN"), ("9", "PDN_UART"),
                       ("10", "DIAG"), ("11", "A+"), ("12", "A-"), ("13", "B+"), ("14", "B-")]),
    ]
    return f"""(kicad_symbol_lib
  (version 20231120)
  (generator "lidar-generate_kicad")
  (generator_version "1.0")
{"".join(mods)}
)
"""


def sym_lib_table() -> str:
    return f"""(sym_lib_table
  (version 7)
  (lib (name "lidar")(type "KiCad")(uri "${{KIPRJMOD}}/symbols/lidar.kicad_sym")(options "")(descr "Modules scanner LiDAR"))
)
"""


def fp_lib_table() -> str:
    return """(fp_lib_table
  (version 7)
)
"""


def kicad_pro(root_uuid: str) -> str:
    data = {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {},
                "diff_pair_dimensions": [],
                "drc_exclusions": [],
                "rules": {},
                "track_widths": [],
                "via_dimensions": [],
            },
            "layer_presets": [],
            "viewports": [],
        },
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "libraries": {
            "pinned_footprint_libs": [],
            "pinned_symbol_libs": [],
        },
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
        "net_settings": {"classes": [], "meta": {"version": 0}, "netclass_assignments": []},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "specctra_dsn": "",
                                  "step": "", "vrml": ""},
                   "page_layout_descr_file": ""},
        "schematic": {
            "legacy_lib_dir": "",
            "legacy_lib_list": [],
            "meta": {"version": 1},
            "net_format_name": "",
            "page_layout_descr_file": "",
            "plot_directory": "",
            "spice_current_sheet_as_root": False,
            "spice_external_command": "",
            "spice_model_current_sheet_as_root": True,
            "spice_save_all_currents": False,
            "spice_save_all_dissipations": False,
            "spice_save_all_voltages": False,
            "subpart_first_id": 0,
            "subpart_id_separator": 0,
        },
        "sheets": [[root_uuid, "Root", f"{PROJECT}.kicad_sch"]],
        "text_variables": {},
    }
    return json.dumps(data, indent=2) + "\n"


def readme() -> str:
    return """# Projet KiCad — Scanner 3D LiDAR

Schéma de **câblage entre modules** (pas de PCB — montage sur breadboard /
borniers dans le boîtier `electronics_box`).

## Ouvrir

1. Installer [KiCad](https://www.kicad.org/) 8 ou 9.
2. Ouvrir `lidar.kicad_pro` dans ce dossier.

## Regénérer

```bash
python3 hardware/generate_kicad.py
```

## Contenu du schéma

| Réf | Module |
|---|---|
| BAT1 | Power bank USB-C PD |
| U2 | Trigger PD → 12 V |
| U4 | Buck 12 V → 5 V |
| U1 | ESP32-S3 DevKitC-1 N16R8 |
| LD1 | LiDAR LD19 (tête tournante) |
| U5 | MPU6050 (base fixe) |
| U3 | TMC2209 |
| M1 | NEMA 17 |
| R1 | 1 kΩ (UART TMC, liaison un fil) |
| C1, C2 | 100 nF (découplage, optionnel sur breadboard) |

Brochage GPIO : voir [`docs/wiring.md`](../docs/wiring.md) et
[`firmware/include/config.h`](../firmware/include/config.h).

## Notes

- Les symboles `lidar:*` représentent des **modules breakout**, pas des composants
  à souder.
- Aucune PCB n'est incluse : `on_board` est à `no` pour les modules.
- Les symboles `Device:R`, `Device:C`, `power:*` viennent des bibliothèques
  KiCad standard (embarquées dans le schéma).
"""


def main() -> None:
    root_uuid = uid()
    sym_dir = ROOT / "symbols"
    sym_dir.mkdir(parents=True, exist_ok=True)

    (sym_dir / "lidar.kicad_sym").write_text(kicad_sym_file(), encoding="utf-8")
    (ROOT / "sym-lib-table").write_text(sym_lib_table(), encoding="utf-8")
    (ROOT / "fp-lib-table").write_text(fp_lib_table(), encoding="utf-8")
    (ROOT / f"{PROJECT}.kicad_pro").write_text(kicad_pro(root_uuid), encoding="utf-8")
    (ROOT / f"{PROJECT}.kicad_sch").write_text(schematic(root_uuid), encoding="utf-8")
    (ROOT / "README.md").write_text(readme(), encoding="utf-8")

    print(f"wrote {ROOT / PROJECT}.kicad_pro")
    print(f"wrote {ROOT / PROJECT}.kicad_sch")
    print(f"wrote {sym_dir / 'lidar.kicad_sym'}")


if __name__ == "__main__":
    main()
