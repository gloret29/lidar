#!/usr/bin/env python3
"""Génère un aperçu PNG ombré d'un fichier STL (binaire ou ASCII).

Pur Python, sans dépendance : utile en CI ou sur une machine sans
serveur graphique, là où `openscad -o preview.png` échoue faute de
contexte OpenGL.

    python3 stl_preview.py piece.stl piece.png --azim 35 --elev 25
"""

from __future__ import annotations

import argparse
import math
import struct
import zlib
from pathlib import Path

Vec = tuple[float, float, float]


def read_stl(path: Path) -> list[tuple[Vec, Vec, Vec]]:
    """Lit un STL binaire ou ASCII."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path}: fichier trop court pour un STL")

    (count,) = struct.unpack_from("<I", data, 80)
    if len(data) == 84 + count * 50:
        triangles = []
        offset = 84
        for _ in range(count):
            vals = struct.unpack_from("<12f", data, offset)
            triangles.append((vals[3:6], vals[6:9], vals[9:12]))
            offset += 50
        return triangles

    return _read_ascii_stl(data)


def _read_ascii_stl(data: bytes) -> list[tuple[Vec, Vec, Vec]]:
    triangles = []
    verts: list[Vec] = []
    for line in data.decode("ascii", "replace").splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] == "vertex":
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            if len(verts) == 3:
                triangles.append((verts[0], verts[1], verts[2]))
                verts = []
        elif parts and parts[0] == "facet":
            verts = []
    if not triangles:
        raise ValueError("aucun triangle trouvé (STL ASCII invalide ?)")
    return triangles


def normalize(v: Vec) -> Vec:
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def cross(a: Vec, b: Vec) -> Vec:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def camera_basis(azim_deg: float, elev_deg: float) -> tuple[Vec, Vec, Vec]:
    """Renvoie (droite, haut, vers_camera) orthonormés."""
    a = math.radians(azim_deg)
    e = math.radians(elev_deg)
    view = normalize((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
    world_up = (0.0, 0.0, 1.0)
    right = normalize(cross(world_up, view))
    up = cross(view, right)
    return right, up, view


def render(
    triangles: list[tuple[Vec, Vec, Vec]],
    width: int,
    height: int,
    azim: float,
    elev: float,
    color: tuple[int, int, int],
    background: tuple[int, int, int],
    ss: int,
) -> bytearray:
    rw, rh = width * ss, height * ss
    right, up, view = camera_basis(azim, elev)
    light = normalize((view[0] * 0.6 + 0.45, view[1] * 0.6 - 0.35, view[2] * 0.6 + 0.75))

    projected = []
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for tri in triangles:
        pts = []
        for v in tri:
            sx, sy, sz = dot(v, right), dot(v, up), dot(v, view)
            pts.append((sx, sy, sz))
            min_x, max_x = min(min_x, sx), max(max_x, sx)
            min_y, max_y = min(min_y, sy), max(max_y, sy)
        projected.append(pts)

    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    margin = 0.94
    scale = min(rw * margin / span_x, rh * margin / span_y)
    off_x = (rw - span_x * scale) / 2 - min_x * scale
    off_y = (rh - span_y * scale) / 2 - min_y * scale

    zbuf = [float("-inf")] * (rw * rh)
    pix = bytearray(bytes(background) * (rw * rh))

    for pts in projected:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts
        nx, ny, nz = cross(
            (bx - ax, by - ay, bz - az), (cx - ax, cy - ay, cz - az)
        )
        area2 = nx * 0 + ny * 0 + nz  # composante Z du produit vectoriel écran
        if abs(area2) < 1e-12:
            continue

        # Normale géométrique dans l'espace monde pour l'éclairage
        normal = normalize(
            (
                right[0] * nx + up[0] * ny + view[0] * nz,
                right[1] * nx + up[1] * ny + view[1] * nz,
                right[2] * nx + up[2] * ny + view[2] * nz,
            )
        )
        lam = max(0.0, dot(normal, light))
        shade = 0.26 + 0.74 * lam
        rgb = bytes(min(255, int(c * shade)) for c in color)

        px = [(ax * scale + off_x, ay * scale + off_y, az),
              (bx * scale + off_x, by * scale + off_y, bz),
              (cx * scale + off_x, cy * scale + off_y, cz)]
        (ax2, ay2, az2), (bx2, by2, bz2), (cx2, cy2, cz2) = px

        det = (by2 - cy2) * (ax2 - cx2) + (cx2 - bx2) * (ay2 - cy2)
        if abs(det) < 1e-9:
            continue
        inv_det = 1.0 / det

        x0 = max(0, int(math.floor(min(ax2, bx2, cx2))))
        x1 = min(rw - 1, int(math.ceil(max(ax2, bx2, cx2))))
        y0 = max(0, int(math.floor(min(ay2, by2, cy2))))
        y1 = min(rh - 1, int(math.ceil(max(ay2, by2, cy2))))
        if x1 < x0 or y1 < y0:
            continue

        for y in range(y0, y1 + 1):
            py = y + 0.5
            row = y * rw
            for x in range(x0, x1 + 1):
                pxc = x + 0.5
                w0 = ((by2 - cy2) * (pxc - cx2) + (cx2 - bx2) * (py - cy2)) * inv_det
                if w0 < 0 or w0 > 1:
                    continue
                w1 = ((cy2 - ay2) * (pxc - cx2) + (ax2 - cx2) * (py - cy2)) * inv_det
                if w1 < 0 or w1 > 1:
                    continue
                w2 = 1.0 - w0 - w1
                if w2 < 0:
                    continue
                depth = w0 * az2 + w1 * bz2 + w2 * cz2
                idx = row + x
                if depth > zbuf[idx]:
                    zbuf[idx] = depth
                    pix[idx * 3: idx * 3 + 3] = rgb

    if ss == 1:
        return _flip(pix, rw, rh)

    # Sous-échantillonnage (anti-crénelage)
    out = bytearray(width * height * 3)
    inv = 1.0 / (ss * ss)
    for y in range(height):
        for x in range(width):
            r = g = b = 0
            for dy in range(ss):
                base = ((y * ss + dy) * rw + x * ss) * 3
                for dx in range(ss):
                    o = base + dx * 3
                    r += pix[o]
                    g += pix[o + 1]
                    b += pix[o + 2]
            o = (y * width + x) * 3
            out[o] = int(r * inv)
            out[o + 1] = int(g * inv)
            out[o + 2] = int(b * inv)
    return _flip(out, width, height)


def _flip(pix: bytearray, w: int, h: int) -> bytearray:
    """L'origine écran est en bas à gauche, le PNG attend le haut en premier."""
    out = bytearray(len(pix))
    stride = w * 3
    for y in range(h):
        src = (h - 1 - y) * stride
        out[y * stride: (y + 1) * stride] = pix[src: src + stride]
    return out


def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += pixels[y * stride: (y + 1) * stride]

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + chunk(b"IEND", b"")
    )


def parse_color(text: str) -> tuple[int, int, int]:
    text = text.lstrip("#")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def main() -> None:
    ap = argparse.ArgumentParser(description="Aperçu PNG ombré d'un STL (binaire ou ASCII)")
    ap.add_argument("stl", type=Path)
    ap.add_argument("png", type=Path)
    ap.add_argument("--width", type=int, default=760)
    ap.add_argument("--height", type=int, default=620)
    ap.add_argument("--azim", type=float, default=35.0)
    ap.add_argument("--elev", type=float, default=22.0)
    ap.add_argument("--color", default="4a90d9")
    ap.add_argument("--background", default="f4f6f8")
    ap.add_argument("--ss", type=int, default=2, help="facteur de suréchantillonnage")
    args = ap.parse_args()

    triangles = read_stl(args.stl)
    pixels = render(
        triangles,
        args.width,
        args.height,
        args.azim,
        args.elev,
        parse_color(args.color),
        parse_color(args.background),
        max(1, args.ss),
    )
    args.png.parent.mkdir(parents=True, exist_ok=True)
    write_png(args.png, args.width, args.height, pixels)
    print(f"{args.png}  ({len(triangles)} triangles)")


if __name__ == "__main__":
    main()
