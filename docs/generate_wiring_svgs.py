#!/usr/bin/env python3
"""Génère les plans de câblage SVG dans docs/wiring/."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "wiring"


def svg(w: int, h: int, body: str, title: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <title>{title}</title>
  <rect width="{w}" height="{h}" fill="#f7f7f5"/>
  <style>
    .box {{ fill:#fff; stroke:#222; stroke-width:1.5; }}
    .box-pwr {{ fill:#fff8f0; stroke:#8b4513; stroke-width:1.5; }}
    .box-mcu {{ fill:#eef4ff; stroke:#1a3a6b; stroke-width:1.5; }}
    .box-sen {{ fill:#eefaf0; stroke:#1b5e20; stroke-width:1.5; }}
    .box-mot {{ fill:#faf0ff; stroke:#4a148c; stroke-width:1.5; }}
    .title {{ font:700 16px "Segoe UI",system-ui,sans-serif; fill:#111; }}
    .label {{ font:600 12px "Segoe UI",system-ui,sans-serif; fill:#111; }}
    .small {{ font:11px "Segoe UI",system-ui,sans-serif; fill:#333; }}
    .note {{ font:11px "Segoe UI",system-ui,sans-serif; fill:#555; }}
    .v12 {{ stroke:#c62828; stroke-width:2.5; fill:none; }}
    .v5 {{ stroke:#ef6c00; stroke-width:2.2; fill:none; }}
    .v33 {{ stroke:#1565c0; stroke-width:2; fill:none; }}
    .gnd {{ stroke:#212121; stroke-width:2.5; fill:none; }}
    .sig {{ stroke:#2e7d32; stroke-width:1.8; fill:none; }}
    .sig2 {{ stroke:#6a1b9a; stroke-width:1.8; fill:none; }}
    .leg {{ font:11px "Segoe UI",system-ui,sans-serif; fill:#222; }}
  </style>
  {body}
</svg>
"""


def rect(x, y, w, h, cls, lines):
    t = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="{cls}"/>\n'
    for i, line in enumerate(lines):
        weight = "label" if i == 0 else "small"
        t += f'<text x="{x + w/2}" y="{y + 18 + i*15}" text-anchor="middle" class="{weight}">{line}</text>\n'
    return t


def wire(x1, y1, x2, y2, cls, label="", lx=None, ly=None):
    t = f'<path d="M{x1},{y1} L{x2},{y2}" class="{cls}"/>\n'
    if label:
        lx = x1 + (x2 - x1) * 0.5 if lx is None else lx
        ly = y1 + (y2 - y1) * 0.5 - 6 if ly is None else ly
        t += f'<text x="{lx}" y="{ly}" text-anchor="middle" class="note">{label}</text>\n'
    return t


def polyline(pts, cls, label="", lx=None, ly=None):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    t = f'<path d="{d}" class="{cls}"/>\n'
    if label and lx is not None:
        t += f'<text x="{lx}" y="{ly}" text-anchor="middle" class="note">{label}</text>\n'
    return t


def power_svg() -> str:
    body = '<text x="24" y="28" class="title">Plan d’alimentation — Scanner 3D LiDAR</text>\n'
    body += rect(40, 50, 160, 56, "box-pwr", ["Power bank", "USB-C PD 100 W"])
    body += rect(260, 50, 160, 56, "box-pwr", ["Trigger PD", "→ 12 V DC"])
    body += rect(480, 50, 150, 56, "box-mot", ["TMC2209", "VM = 12 V"])
    body += rect(260, 160, 160, 56, "box-pwr", ["Buck", "12 V → 5 V / 3 A"])
    body += rect(480, 140, 150, 50, "box-sen", ["LD19", "P5V vert"])
    body += rect(480, 210, 150, 50, "box-mcu", ["ESP32-S3", "5V / VIN"])
    body += rect(700, 210, 140, 50, "box-sen", ["MPU6050", "3,3 V"])
    body += rect(700, 140, 140, 50, "box-mot", ["TMC2209", "VIO 3,3 V"])

    # 12V path
    body += polyline([(200, 78), (260, 78)], "v12", "USB-C", 230, 70)
    body += polyline([(420, 78), (480, 78)], "v12", "12 V", 450, 70)
    body += polyline([(340, 106), (340, 160)], "v12")
    # 5V
    body += polyline([(420, 188), (480, 165)], "v5", "5 V", 445, 168)
    body += polyline([(420, 188), (480, 235)], "v5")
    # 3.3V from ESP
    body += polyline([(630, 235), (700, 235)], "v33", "3,3 V", 665, 228)
    body += polyline([(555, 210), (555, 120), (700, 120), (700, 165)], "v33", "3,3 V", 640, 112)

    # GND rail
    body += f'<path d="M40,300 L840,300" class="gnd"/>\n'
    body += '<text x="40" y="318" class="label">Masse commune (GND) — obligatoire entre tous les modules</text>\n'
    for x in (120, 340, 555, 555, 770, 770):
        body += f'<path d="M{x},300 L{x},280" class="gnd"/>\n'
    # drops from boxes
    body += polyline([(120, 106), (120, 300)], "gnd")
    body += polyline([(340, 216), (340, 300)], "gnd")
    body += polyline([(555, 260), (555, 300)], "gnd")
    body += polyline([(555, 190), (620, 190), (620, 300)], "gnd")
    body += polyline([(770, 190), (770, 300)], "gnd")
    body += polyline([(770, 260), (770, 300)], "gnd")

    # legend
    y = 350
    body += f'<path d="M40,{y} L80,{y}" class="v12"/><text x="90" y="{y+4}" class="leg">12 V (trigger PD → TMC VM + buck)</text>\n'
    body += f'<path d="M360,{y} L400,{y}" class="v5"/><text x="410" y="{y+4}" class="leg">5 V (buck → LD19 + ESP32)</text>\n'
    body += f'<path d="M40,{y+28} L80,{y+28}" class="v33"/><text x="90" y="{y+32}" class="leg">3,3 V (ESP32 → MPU6050 + TMC VIO)</text>\n'
    body += f'<path d="M360,{y+28} L400,{y+28}" class="gnd"/><text x="410" y="{y+32}" class="leg">GND commun</text>\n'
    body += '<text x="40" y="410" class="note">Mesurer 12 V et 5 V à vide avant de connecter les charges. Consommation typique : 8–12 W en balayage.</text>\n'
    return svg(880, 430, body, "Alimentation scanner LiDAR")


def signals_svg() -> str:
    body = '<text x="24" y="28" class="title">Plan des signaux — ESP32-S3 ↔ périphériques</text>\n'
    body += rect(340, 160, 180, 90, "box-mcu", ["ESP32-S3", "DevKitC-1 N16R8", "cœur du câblage"])

    body += rect(40, 60, 160, 70, "box-sen", ["LD19 (tête)", "UART 230400", "PWM 30 kHz"])
    body += rect(40, 200, 160, 70, "box-sen", ["MPU6050", "I2C 0x68", "base fixe"])
    body += rect(640, 80, 180, 90, "box-mot", ["TMC2209", "STEP/DIR/EN", "UART + DIAG"])
    body += rect(640, 230, 180, 60, "box-mot", ["NEMA 17", "N/B = A  V/R = B"])

    # LD19
    body += polyline([(200, 80), (340, 180)], "sig", "TX → GPIO18", 250, 110)
    body += polyline([(200, 100), (340, 195)], "sig2", "PWM ← GPIO17", 255, 135)
    # MPU
    body += polyline([(200, 225), (340, 210)], "sig", "SDA GPIO8", 260, 208)
    body += polyline([(200, 245), (340, 225)], "sig2", "SCL GPIO9", 260, 248)
    # TMC control
    body += polyline([(520, 185), (640, 110)], "sig", "STEP 4", 575, 130)
    body += polyline([(520, 195), (640, 125)], "sig2", "DIR 5", 580, 155)
    body += polyline([(520, 205), (640, 140)], "sig", "EN 6", 585, 175)
    body += polyline([(520, 215), (640, 155)], "sig2", "UART 7/15", 560, 200)
    body += polyline([(520, 225), (640, 170)], "sig", "DIAG 16", 575, 220)
    # Motor
    body += polyline([(730, 170), (730, 230)], "v12", "phases", 750, 200)

    body += '<text x="40" y="320" class="label">Résistance UART TMC</text>\n'
    body += """
    <rect x="40" y="330" width="420" height="70" rx="6" class="box"/>
    <text x="50" y="352" class="small">GPIO7 (TX) ──[ 1 kΩ ]──┬── PDN (TWOTREES, pas USART)</text>
    <text x="50" y="372" class="small">GPIO15 (RX) ────────────┘</text>
    <text x="50" y="390" class="note">MS1 = MS2 = GND → adresse UART 0. EN actif à l’état bas.</text>
    """
    body += '<text x="500" y="350" class="label">Interdits N16R8</text>\n'
    body += '<text x="500" y="370" class="note">GPIO 33–37 = PSRAM (ne pas utiliser)</text>\n'
    body += '<text x="500" y="388" class="note">Éviter aussi 19/20 (USB) et 26–32 (flash)</text>\n'
    return svg(860, 430, body, "Signaux scanner LiDAR")


def pinout_svg() -> str:
    """Tableau visuel broche par broche."""
    rows = [
        ("GPIO", "Fonction", "Vers", "Fil conseillé"),
        ("18", "LD19 RX", "TX STL-19P (blanc)", "Blanc"),
        ("17", "LD19 PWM", "PWM STL-19P (noir)", "Noir"),
        ("8", "I2C SDA", "MPU6050 SDA", "Bleu"),
        ("9", "I2C SCL", "MPU6050 SCL", "Vert"),
        ("4", "STEP", "TMC2209 STEP", "Orange"),
        ("5", "DIR", "TMC2209 DIR", "Violet"),
        ("6", "EN", "TMC2209 EN", "Gris"),
        ("7", "TMC TX", "PDN via 1 kΩ (pas USART)", "Brun"),
        ("15", "TMC RX", "PDN direct", "Brun"),
        ("16", "DIAG", "Pastille DIAG (triangle)", "Rose"),
        ("0", "BOOT", "Reset Wi‑Fi (maintenu)", "—"),
        ("GND", "Masse", "Tous les GND", "Noir"),
        ("3V3", "3,3 V", "MPU + TMC VIO", "Rouge clair"),
        ("5V", "5 V VIN", "Depuis buck", "Rouge"),
    ]
    h = 56 + len(rows) * 28 + 40
    body = '<text x="24" y="28" class="title">Brochage ESP32-S3 — table de câblage</text>\n'
    cols = [40, 120, 280, 480]
    widths = [70, 150, 180, 160]
    y0 = 50
    for i, row in enumerate(rows):
        y = y0 + i * 28
        bg = "#e8e8e4" if i == 0 else ("#fff" if i % 2 else "#f3f3ef")
        body += f'<rect x="40" y="{y}" width="600" height="28" fill="{bg}" stroke="#ccc"/>\n'
        for j, cell in enumerate(row):
            weight = "label" if i == 0 else "small"
            body += f'<text x="{cols[j] + 8}" y="{y + 18}" class="{weight}">{cell}</text>\n'
    body += f'<text x="40" y="{h - 16}" class="note">Alimentations LD19 5 V et TMC VM 12 V viennent du buck / trigger, pas des pins ESP32.</text>\n'
    return svg(680, h, body, "Brochage ESP32-S3")


def overview_svg() -> str:
    body = '<text x="24" y="28" class="title">Schéma d’ensemble — Scanner 3D LiDAR DIY</text>\n'
    # Tripod / mech note
    body += rect(40, 50, 200, 80, "box", ["Tête tournante", "LD19 + berceau", "câble en hélice ±90°"])
    body += rect(300, 50, 220, 80, "box-mcu", ["Boîtier (trépied)", "ESP32-S3 + TMC2209", "buck + trigger + MPU"])
    body += rect(580, 50, 200, 80, "box-pwr", ["Énergie", "Power bank PD", "12 V + 5 V"])
    body += rect(300, 180, 220, 70, "box-mot", ["Moteur fixe", "NEMA 17 sous plateau", "axe vertical"])
    body += rect(40, 180, 200, 70, "box-sen", ["Station hôte", "Wi‑Fi UDP :9000", "Open3D / receive"])

    body += polyline([(240, 90), (300, 90)], "sig", "UART+PWM", 270, 80)
    body += polyline([(520, 90), (580, 90)], "v12", "12/5 V", 550, 80)
    body += polyline([(410, 130), (410, 180)], "sig2", "STEP…", 430, 155)
    body += polyline([(140, 130), (140, 180)], "sig", "Wi‑Fi", 160, 155)

    body += '<text x="40" y="290" class="label">Règles d’or</text>\n'
    body += '<text x="40" y="312" class="small">1. Une seule masse commune (trigger, buck, ESP, TMC, LD19, moteur).</text>\n'
    body += '<text x="40" y="332" class="small">2. MPU6050 en 3,3 V uniquement — jamais en 5 V.</text>\n'
    body += '<text x="40" y="352" class="small">3. LD19 TX → ESP32 RX (GPIO18). Inverser = silence total.</text>\n'
    body += '<text x="40" y="372" class="small">4. 1 kΩ sur TX UART du TMC. Mesurer 12 V et 5 V avant branchement charges.</text>\n'
    body += '<text x="40" y="392" class="small">5. Premier essai sans moteur ; mou du câble LiDAR ~120 mm en hélice.</text>\n'
    return svg(820, 420, body, "Ensemble scanner LiDAR")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "01_ensemble.svg": overview_svg(),
        "02_alimentation.svg": power_svg(),
        "03_signaux.svg": signals_svg(),
        "04_brochage.svg": pinout_svg(),
    }
    for name, content in files.items():
        path = OUT / name
        path.write_text(content, encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
