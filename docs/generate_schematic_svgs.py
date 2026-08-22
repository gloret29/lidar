#!/usr/bin/env python3
"""Génère des schémas électriques classiques (style Arduino) dans docs/wiring/."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "wiring"

STYLE = """
  .wire { fill:none; stroke:#111; stroke-width:1.6; }
  .wire-thin { fill:none; stroke:#111; stroke-width:1.2; }
  .sym { fill:none; stroke:#111; stroke-width:1.6; }
  .sym-fill { fill:#fff; stroke:#111; stroke-width:1.6; }
  .title { font:700 18px "Segoe UI",system-ui,sans-serif; fill:#111; }
  .label { font:600 12px "Segoe UI",system-ui,sans-serif; fill:#111; }
  .small { font:11px "Segoe UI",system-ui,sans-serif; fill:#111; }
  .pin { font:10px "Consolas","Courier New",monospace; fill:#111; }
  .note { font:10px "Segoe UI",system-ui,sans-serif; fill:#444; }
  .ref { font:700 11px "Segoe UI",system-ui,sans-serif; fill:#111; }
"""


def svg(w: int, h: int, body: str, title: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <title>{title}</title>
  <rect width="{w}" height="{h}" fill="#fff"/>
  <style>{STYLE}</style>
  {body}
</svg>
"""


def line(x1, y1, x2, y2, cls="wire") -> str:
    return f'<path d="M{x1},{y1} L{x2},{y2}" class="{cls}"/>\n'


def poly(pts, cls="wire") -> str:
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    return f'<path d="{d}" class="{cls}"/>\n'


def dot(x, y) -> str:
    return f'<circle cx="{x}" cy="{y}" r="2.8" fill="#111"/>\n'


def text(x, y, s, cls="small", anchor="start") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{s}</text>\n'


def ground(x, y) -> str:
    return (
        line(x, y, x, y + 10)
        + line(x - 10, y + 10, x + 10, y + 10)
        + line(x - 6, y + 14, x + 6, y + 14)
        + line(x - 3, y + 18, x + 3, y + 18)
    )


def battery(x, y, ref: str, label: str) -> str:
    t = (
        line(x, y, x, y + 18)
        + line(x - 8, y + 18, x - 8, y + 34, "sym")
        + line(x + 8, y + 22, x + 8, y + 30, "sym")
        + line(x - 8, y + 26, x + 8, y + 26, "sym")
        + text(x - 22, y + 12, ref, "ref")
        + text(x - 34, y + 48, label, "small", "middle")
    )
    return t


def resistor_h(x, y, ref: str, value: str) -> str:
    w = 46
    t = poly([(x, y), (x + 8, y), (x + 14, y - 5), (x + 22, y + 5),
              (x + 30, y - 5), (x + 38, y + 5), (x + 46, y), (x + w, y)])
    t += text(x + 8, y - 10, ref, "ref")
    t += text(x + 8, y + 18, value, "small")
    return t


def capacitor_v(x, y, ref: str, value: str) -> str:
    t = line(x, y, x, y + 10)
    t += line(x - 8, y + 10, x + 8, y + 10, "sym")
    t += line(x - 8, y + 16, x + 8, y + 16, "sym")
    t += line(x, y + 16, x, y + 26)
    t += text(x + 12, y + 8, ref, "ref")
    t += text(x + 12, y + 22, value, "small")
    return t


def motor(x, y, ref: str, label: str) -> str:
    t = f'<circle cx="{x}" cy="{y}" r="22" class="sym-fill"/>\n'
    t += text(x, y + 5, "M", "label", "middle")
    t += text(x - 28, y - 28, ref, "ref")
    t += text(x, y + 38, label, "small", "middle")
    return t


def ic_block(x, y, w, h, ref: str, name: str, pins_left: list[str], pins_right: list[str]) -> str:
    t = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="sym-fill"/>\n'
    t += text(x + w / 2, y + 16, ref, "ref", "middle")
    t += text(x + w / 2, y + 32, name, "label", "middle")
    step_l = (h - 50) / max(len(pins_left), 1)
    for i, pin in enumerate(pins_left):
        py = y + 48 + i * step_l
        t += line(x - 24, py, x, py)
        t += text(x - 28, py + 4, pin, "pin", "end")
    step_r = (h - 50) / max(len(pins_right), 1)
    for i, pin in enumerate(pins_right):
        py = y + 48 + i * step_r
        t += line(x + w, py, x + w + 24, py)
        t += text(x + w + 28, py + 4, pin, "pin")
    return t


def mcu_esp32(x, y) -> str:
    w, h = 120, 420
    left = ["3V3", "GND", "5V/VIN", "GPIO0 BOOT", "GPIO4 STEP", "GPIO5 DIR",
            "GPIO6 EN", "GPIO7 TMC TX", "GPIO8 SDA", "GPIO9 SCL"]
    right = ["GPIO15 TMC RX", "GPIO16 DIAG", "GPIO17 PWM", "GPIO18 RX",
             "GND", "3V3", "5V/VIN", "NC", "NC", "NC"]
    t = ic_block(x, y, w, h, "U1", "ESP32-S3 DevKitC-1", left, right)
    t += text(x + w / 2, y + h - 18, "N16R8", "note", "middle")
    return t


def power_schematic() -> str:
    body = text(24, 28, "Schéma d’alimentation — Scanner 3D LiDAR", "title")
    rail_12, rail_5, gnd_y = 96, 220, 420

    body += battery(80, 70, "BAT1", "Power bank")
    body += text(80, 130, "USB-C PD 100 W", "small", "middle")
    body += ic_block(180, 60, 110, 70, "U2", "Trigger PD", ["USB-C in"], ["+12 V", "GND"])
    body += line(80, rail_12, 156, rail_12)
    body += dot(80, rail_12)
    body += line(314, rail_12, 720, rail_12)
    body += text(520, rail_12 - 8, "+12 V", "label", "middle")

    body += ic_block(620, 40, 100, 50, "U3", "TMC2209", ["VM"], ["GND"])
    body += line(670, 90, 670, rail_12)
    body += dot(670, rail_12)

    body += ic_block(180, 190, 110, 70, "U4", "Buck 12→5 V", ["+12 V in", "GND"], ["+5 V", "GND"])
    body += line(235, rail_12, 235, 238)
    body += dot(235, rail_12)
    body += line(314, rail_5, 720, rail_5)
    body += text(520, rail_5 - 8, "+5 V / 3 A", "label", "middle")
    body += line(235, 238, 235, rail_5)
    body += dot(235, rail_5)

    body += ic_block(560, 170, 90, 50, "LD1", "LD19", ["VCC 5 V"], ["GND"])
    body += line(536, 218, 560, 218)
    body += line(536, 218, 536, rail_5)
    body += dot(536, rail_5)

    body += ic_block(700, 170, 90, 50, "U1", "ESP32-S3", ["5V/VIN"], ["GND"])
    body += line(676, 218, 676, rail_5)
    body += dot(676, rail_5)

    body += line(745, 260, 745, 300)
    body += text(760, 292, "+3,3 V", "label")
    body += ic_block(700, 300, 90, 50, "U5", "MPU6050", ["VCC 3,3 V"], ["GND"])
    body += ic_block(560, 300, 90, 50, "U3b", "TMC2209", ["VIO 3,3 V"], ["GND"])

    body += capacitor_v(420, 170, "C1", "100 nF")
    body += line(420, rail_12, 420, 170)
    body += dot(420, rail_12)
    body += ground(420, 196)
    body += capacitor_v(480, 190, "C2", "100 nF")
    body += line(480, rail_5, 480, 190)
    body += dot(480, rail_5)
    body += ground(480, 216)

    body += line(60, gnd_y, 780, gnd_y)
    body += text(40, gnd_y + 4, "GND", "label")
    body += line(235, 248, 235, gnd_y)
    body += line(314, 118, 314, gnd_y)
    body += line(605, 218, 605, gnd_y)
    body += line(676, 218, 676, gnd_y)
    body += line(745, 218, 745, gnd_y)
    body += line(605, 348, 605, gnd_y)
    body += line(745, 348, 745, gnd_y)
    body += line(670, 90, 670, gnd_y)
    for gx in (80, 235, 314, 536, 605, 670, 676, 745):
        body += ground(gx, gnd_y)

    body += text(40, 460, "Masse commune obligatoire entre trigger, buck, ESP32, TMC2209, LD19 et moteur.", "note")
    body += text(40, 478, "Mesurer +12 V et +5 V à vide avant de connecter les charges. Consommation typique : 8–12 W.", "note")
    return svg(820, 500, body, "Alimentation — schéma classique")


def signals_schematic() -> str:
    body = text(24, 28, "Schéma des signaux — ESP32-S3 ↔ périphériques", "title")

    mcu_x, mcu_y = 300, 50
    body += mcu_esp32(mcu_x, mcu_y)

    # Pin Y positions on MCU (left side used pins)
    def pin_y_left(idx: int) -> float:
        return mcu_y + 48 + idx * (370 / 9)

    def pin_y_right(idx: int) -> float:
        return mcu_y + 48 + idx * (370 / 9)

    # LD19 (top left)
    body += ic_block(40, 40, 90, 90, "LD1", "LD19 LiDAR", ["TX", "PWM in", "VCC", "GND"], [])
    body += text(85, 150, "tête tournante", "note", "middle")
    tx_y = pin_y_right(3)  # GPIO18 RX
    pwm_y = pin_y_right(2)  # GPIO17 PWM
    body += line(130, 62, 220, 62)
    body += line(220, 62, 220, tx_y)
    body += line(220, tx_y, mcu_x + 120 + 24, tx_y)
    body += text(170, 54, "TX → RX", "small", "middle")
    body += line(130, 82, 210, 82)
    body += line(210, 82, 210, pwm_y)
    body += line(210, pwm_y, mcu_x + 120 + 24, pwm_y)
    body += text(165, 74, "PWM ←", "small", "middle")

    # MPU6050 (bottom left)
    body += ic_block(40, 260, 90, 80, "U5", "MPU6050", ["SDA", "SCL", "AD0", "VCC", "GND"], [])
    sda_y = pin_y_left(8)
    scl_y = pin_y_left(9) if pin_y_left(9) else pin_y_left(8) + 37
    scl_y = pin_y_left(8) + 37
    body += line(130, 286, 250, 286)
    body += line(250, 286, 250, sda_y)
    body += line(250, sda_y, mcu_x - 24, sda_y)
    body += text(185, 278, "SDA GPIO8", "small", "middle")
    body += line(130, 306, 240, 306)
    body += line(240, 306, 240, scl_y)
    body += line(240, scl_y, mcu_x - 24, scl_y)
    body += text(175, 298, "SCL GPIO9", "small", "middle")
    body += line(130, 326, 230, 326)
    body += ground(230, 326)
    body += text(150, 318, "AD0→GND (0x68)", "note")

    # TMC2209 (right)
    body += ic_block(620, 80, 120, 200, "U3", "TMC2209", [],
                     ["STEP", "DIR", "EN", "PDN", "DIAG", "MS1", "MS2", "VM", "VIO", "GND"])
    step_y = pin_y_left(4)
    dir_y = pin_y_left(5)
    en_y = pin_y_left(6)
    tx_y_mcu = pin_y_left(7)
    rx_y = pin_y_right(0)
    diag_y = pin_y_right(1)
    body += line(mcu_x + 120 + 24, step_y, 620, 108)
    body += text(520, step_y - 6, "GPIO4", "small", "middle")
    body += line(mcu_x + 120 + 24, dir_y, 620, 128)
    body += text(520, dir_y - 6, "GPIO5", "small", "middle")
    body += line(mcu_x + 120 + 24, en_y, 620, 148)
    body += text(520, en_y - 6, "GPIO6", "small", "middle")

    # UART with 1k resistor
    uart_x = 560
    body += line(mcu_x + 120 + 24, tx_y_mcu, uart_x, tx_y_mcu)
    body += line(mcu_x + 120 + 24, rx_y, uart_x + 60, rx_y)
    body += line(uart_x + 60, rx_y, uart_x + 60, tx_y_mcu)
    body += dot(uart_x + 60, tx_y_mcu)
    body += line(uart_x + 60, tx_y_mcu, 620, 168)
    body += resistor_h(uart_x, tx_y_mcu - 1, "R1", "1 kΩ")
    body += text(545, tx_y_mcu + 22, "GPIO7 TX", "small", "middle")
    body += text(545, rx_y - 8, "GPIO15 RX", "small", "middle")

    body += line(mcu_x + 120 + 24, diag_y, 620, 188)
    body += text(520, diag_y - 6, "GPIO16", "small", "middle")

    # MS1 MS2 to GND
    body += line(620, 208, 590, 208)
    body += line(590, 208, 590, 240)
    body += ground(590, 240)
    body += line(620, 228, 575, 228)
    body += line(575, 228, 575, 240)
    body += text(555, 252, "MS1=MS2=GND", "note", "middle")

    # Motor
    body += motor(760, 360, "M1", "NEMA 17")
    body += line(740, 168, 760, 338)
    body += line(740, 188, 748, 338)
    body += text(700, 250, "M1A/M1B", "small", "middle")
    body += text(700, 270, "M2A/M2B", "small", "middle")

    # GND common note
    body += line(620, 260, 620, 400)
    body += line(620, 400, 80, 400)
    body += ground(80, 400)
    body += text(350, 392, "Masse commune (GND)", "label", "middle")

    body += text(40, 470, "LD19 : UART 230 400 bauds 8N1, 3,3 V compatibles. PWM 30 kHz → 5 Hz (firmware).", "note")
    body += text(40, 488, "GPIO 33–37 interdits (PSRAM N16R8). EN TMC actif à l’état bas.", "note")
    return svg(860, 510, body, "Signaux — schéma classique")


def full_schematic() -> str:
    """Schéma d’ensemble compact, style didactique."""
    body = text(24, 28, "Schéma électrique — Scanner 3D LiDAR DIY", "title")

    body += mcu_esp32(320, 60)

    # Left column: sensors
    body += ic_block(40, 80, 100, 70, "LD1", "LD19", ["TX", "PWM", "5V", "GND"], [])
    body += ic_block(40, 200, 100, 70, "U5", "MPU6050", ["SDA", "SCL", "3V3", "GND"], [])

    # Right column: driver + motor
    body += ic_block(620, 100, 110, 130, "U3", "TMC2209", ["VM 12V", "VIO 3V3", "GND"], ["STEP", "DIR", "EN", "UART", "DIAG"])
    body += motor(760, 300, "M1", "NEMA 17")

    # Power (top)
    body += battery(40, 320, "BAT1", "PD 100W")
    body += ic_block(130, 310, 90, 55, "U2", "Trigger", ["in"], ["12V"])
    body += ic_block(240, 310, 90, 55, "U4", "Buck", ["12V"], ["5V"])

    body += line(230, 337, 320, 337)
    body += line(330, 337, 320, 120)
    body += text(275, 328, "5V", "small", "middle")
    body += line(220, 337, 220, 280)
    body += line(220, 280, 620, 280)
    body += line(620, 280, 620, 230)
    body += text(420, 272, "12V → VM", "small", "middle")

    # UART resistor detail box
    body += f'<rect x="500" y="380" width="300" height="72" class="sym-fill"/>\n'
    body += text(510, 400, "Liaison UART TMC2209 (un fil)", "label")
    body += text(510, 420, "GPIO7 ──[ R1 1 kΩ ]──┬── PDN_UART", "pin")
    body += text(510, 438, "GPIO15 ──────────────┘", "pin")

    body += text(40, 470, "Voir 05_alimentation.svg et 06_signaux.svg pour le détail fil par fil.", "note")
    return svg(860, 490, body, "Schéma électrique ensemble")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "05_schematic_alimentation.svg": power_schematic(),
        "06_schematic_signaux.svg": signals_schematic(),
        "07_schematic_ensemble.svg": full_schematic(),
    }
    for name, content in files.items():
        path = OUT / name
        path.write_text(content, encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
