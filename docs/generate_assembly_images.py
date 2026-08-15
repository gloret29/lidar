#!/usr/bin/env python3
"""Génère les illustrations du guide de montage (docs/assembly/)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAD = ROOT / "mechanical" / "openscad" / "assembly_steps.scad"
PREVIEW = ROOT / "mechanical" / "tools" / "stl_preview.py"
OUT = Path(__file__).resolve().parent / "assembly"
OPENSCAD = "openscad"

# step_id, fichier, azimut, élévation, largeur, hauteur, couleur dominante
MECH_STEPS = [
    ("01", "Préparation tige Ø8 × 115 mm", 0, 12, 820, 280, "d8dce0"),
    ("02", "Insert trépied 1/4\"-20", 35, 28, 760, 620, "4a90d9"),
    ("03", "NEMA 17 sous le plateau", 35, 22, 760, 620, "4a90d9"),
    ("04", "Deux roulements 608ZZ", 35, 18, 760, 700, "5aa469"),
    ("05", "Accouplement 5→8 mm", 35, 20, 760, 680, "5aa469"),
    ("06", "Colonne sur le plateau", 38, 16, 760, 780, "5aa469"),
    ("07", "Tige + accouplement serré", 38, 14, 760, 820, "5aa469"),
    ("08", "LD19 sur le berceau", 40, 18, 760, 620, "e8a33d"),
    ("09", "Berceau sur la tige", 38, 12, 700, 900, "6f7c8a"),
    ("10", "Boîtier électronique", 35, 28, 760, 560, "9b6bc4"),
    ("11", "Câble LiDAR en hélice", 38, 12, 700, 900, "6f7c8a"),
]


def svg_header(w: int, h: int, title: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <title>{title}</title>
  <rect width="{w}" height="{h}" fill="#f7f8fa"/>
  <style>
    .title {{ font:700 15px "Segoe UI",system-ui,sans-serif; fill:#111; }}
    .box {{ fill:#fff; stroke:#333; stroke-width:1.4; }}
    .label {{ font:600 12px "Segoe UI",system-ui,sans-serif; fill:#111; }}
    .small {{ font:11px "Segoe UI",system-ui,sans-serif; fill:#333; }}
    .arrow {{ fill:none; stroke:#1565c0; stroke-width:1.6; marker-end:url(#arr); }}
  </style>
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#1565c0"/>
    </marker>
  </defs>
"""


def step12_svg() -> str:
    """Étape 12 — séquence de mise sous tension (schéma)."""
    w, h = 820, 420
    body = svg_header(w, h, "Étape 12 — premières mises sous tension")
    body += f'<text x="24" y="28" class="title">Étape 12 — premières mises sous tension</text>\n'

    cards = [
        ("12a", "Sans moteur", "LD19 + Wi-Fi", "Moniteur série : trames LD19\nPortail LiDAR-Scanner-Setup"),
        ("12b", "300 mA", "Rotation ±10°", "StealthChop quasi silencieux\nPas de vibration"),
        ("12c", "Homing", "StallGuard", "Ajuster SGTHRS (~80)\n10 essais répétables"),
        ("12d", "700 mA", "Scan 180°", "Balayage complet\nVérifier nuage UDP"),
    ]
    x0 = 30
    for i, (ref, title, sub, detail) in enumerate(cards):
        x = x0 + i * 195
        body += f'<rect x="{x}" y="50" width="175" height="320" rx="8" class="box"/>\n'
        body += f'<text x="{x + 12}" y="78" class="label">{ref} — {title}</text>\n'
        body += f'<text x="{x + 12}" y="98" class="small">{sub}</text>\n'
        for j, line in enumerate(detail.split("\n")):
            body += f'<text x="{x + 12}" y="{130 + j * 18}" class="small">{line}</text>\n'
        if i < 3:
            body += (
                f'<path d="M{x + 175},{190} L{x + 195},{190}" class="arrow"/>\n'
            )

    body += "</svg>\n"
    return body


def render_mech_step(step_num: int, out_png: Path, azim: float, elev: float,
                     width: int, height: int, color: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        stl = Path(tmp.name)
    try:
        subprocess.run(
            [
                OPENSCAD,
                "-D", f"step={step_num}",
                "--export-format=binstl",
                "-o", str(stl),
                str(SCAD),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "python3", str(PREVIEW), str(stl), str(out_png),
                "--width", str(width),
                "--height", str(height),
                "--azim", str(azim),
                "--elev", str(elev),
                "--color", color,
                "--background", "f4f6f8",
                "--ss", "2",
            ],
            check=True,
        )
    finally:
        stl.unlink(missing_ok=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    for sid, _title, azim, elev, w, h, color in MECH_STEPS:
        num = int(sid)
        png = OUT / f"step-{sid}.png"
        print(f"step {sid} …", end=" ", flush=True)
        render_mech_step(num, png, azim, elev, w, h, color)
        print(png.name)

    svg_path = OUT / "step-12.svg"
    svg_path.write_text(step12_svg(), encoding="utf-8")
    print("wrote", svg_path)


if __name__ == "__main__":
    main()
