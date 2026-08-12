"""Générateur UDP de paquets v2 — valide la station hôte sans matériel.

Simule un balayage dans une scène 3D (pièce en L + mobilier), encode le
protocole firmware, envoie vers l'hôte et enregistre le nuage en .pcd
(défaut : scans/simulate.pcd).

Terminal A :
    lidar-visualize --port 9000

Terminal B :
    lidar-simulate --host 127.0.0.1 --port 9000 --fast

Sans récepteur (fichier seul) :
    lidar-simulate --fast --no-udp --output scans/sim.pcd
"""

from __future__ import annotations

import argparse
import math
import socket
import struct
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from lidar_host import (
    FLAG_SCAN_END,
    FLAG_SCAN_START,
    HEADER_SIZE,
    PACKET_MAGIC,
    PROTOCOL_VERSION,
)
from lidar_host.protocol import parse_packet
from lidar_host.receiver import save_cloud
from lidar_host.transform import Calibration, polar_to_cartesian, valid_mask

_HEADER = struct.Struct("<IHHIHHQii")
assert _HEADER.size == HEADER_SIZE


@dataclass(frozen=True)
class Solid:
    """Pavé axis-aligned opaque (mur, meuble, sol…)."""

    box_min: tuple[float, float, float]
    box_max: tuple[float, float, float]
    albedo: float = 1.0  # 0..1, module l'intensité renvoyée


def pack_packet(
    points: list[tuple[int, int, int, int]],
    *,
    sequence: int,
    flags: int = 0,
    speed_dhz: int = 50,
    t_start_us: int = 0,
    psi_start_mdeg: int = 0,
    psi_end_mdeg: int = 0,
) -> bytes:
    """points = [(rho_mm, theta_cdeg, intensity, dt_us), ...]"""
    header = _HEADER.pack(
        PACKET_MAGIC,
        PROTOCOL_VERSION,
        flags,
        sequence,
        len(points),
        speed_dhz,
        t_start_us,
        psi_start_mdeg,
        psi_end_mdeg,
    )
    body = b"".join(
        struct.pack("<HHBBH", rho, theta, inten, 0, dt)
        for rho, theta, inten, dt in points
    )
    return header + body


def ray_enter_box(
    origin: np.ndarray,
    direction: np.ndarray,
    box_min: np.ndarray,
    box_max: np.ndarray,
) -> float | None:
    """Distance jusqu'à l'entrée d'un AABB (origine à l'extérieur)."""
    tmin, tmax = -np.inf, np.inf
    for i in range(3):
        d = direction[i]
        if abs(d) < 1e-12:
            if origin[i] < box_min[i] or origin[i] > box_max[i]:
                return None
            continue
        inv = 1.0 / d
        t1 = (box_min[i] - origin[i]) * inv
        t2 = (box_max[i] - origin[i]) * inv
        if t1 > t2:
            t1, t2 = t2, t1
        tmin = max(tmin, t1)
        tmax = min(tmax, t2)
        if tmin > tmax:
            return None
    if tmax < 0 or tmin < 1e-4:
        # Origine à l'intérieur ou derrière : pas d'entrée valide.
        return None
    return float(tmin)


def direction_head_frame(theta_rad: float, psi_rad: float) -> np.ndarray:
    """Direction unitaire cohérente avec transform.polar_to_cartesian."""
    hx, hy, hz = math.cos(theta_rad), 0.0, math.sin(theta_rad)
    c, s = math.cos(psi_rad), math.sin(psi_rad)
    return np.array([c * hx - s * hy, s * hx + c * hy, hz], dtype=np.float64)


def _box(
    x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
    albedo: float = 1.0,
) -> Solid:
    return Solid(
        (min(x0, x1), min(y0, y1), min(z0, z1)),
        (max(x0, x1), max(y0, y1), max(z0, z1)),
        albedo,
    )


def build_scene_box(
    width: float, depth: float, height: float, sensor_z: float, wall: float = 0.12
) -> tuple[np.ndarray, list[Solid]]:
    """Pièce rectangulaire vide (murs / sol / plafond en coque)."""
    origin = np.zeros(3)
    z0, z1 = -sensor_z, height - sensor_z
    x0, x1 = -width / 2, width / 2
    y0, y1 = -depth / 2, depth / 2
    solids = [
        _box(x0, x1, y0, y1, z0, z0 + wall, 0.85),          # sol
        _box(x0, x1, y0, y1, z1 - wall, z1, 0.95),          # plafond
        _box(x0, x0 + wall, y0, y1, z0, z1, 0.9),           # -X
        _box(x1 - wall, x1, y0, y1, z0, z1, 0.9),           # +X
        _box(x0, x1, y0, y0 + wall, z0, z1, 0.9),           # -Y
        _box(x0, x1, y1 - wall, y1, z0, z1, 0.9),           # +Y
    ]
    return origin, solids


def build_scene_apartment(
    width: float, depth: float, height: float, sensor_z: float, wall: float = 0.12
) -> tuple[np.ndarray, list[Solid]]:
    """Appartement en L : salon + couloir, mobilier, ouverture de porte.

    Plan (vue du dessus, Z vers le haut) — le capteur est à l'origine ::

                    +Y
                     │
              ┌──────┴──────┐
              │   salon     │
              │      ●      │──────┐
              │             │ couloir
              └─────────────┘      │
                                   └──
                         +X
    """
    origin = np.zeros(3)
    z0, z1 = -sensor_z, height - sensor_z
    # Salon (rectangle principal).
    sx0, sx1 = -width / 2, width / 2
    sy0, sy1 = -depth / 2, depth / 2
    # Couloir / aile sur +X (profondeur réduite).
    wing_w = max(1.8, width * 0.45)
    wing_d = max(2.2, depth * 0.55)
    wx0, wx1 = sx1 - wall, sx1 + wing_w
    wy0, wy1 = -wing_d / 2, wing_d / 2

    solids: list[Solid] = []

    # --- Sol & plafond (salon + aile) ---
    solids += [
        _box(sx0, sx1, sy0, sy1, z0, z0 + wall, 0.8),
        _box(sx1, wx1, wy0, wy1, z0, z0 + wall, 0.8),
        _box(sx0, sx1, sy0, sy1, z1 - wall, z1, 0.95),
        _box(sx1, wx1, wy0, wy1, z1 - wall, z1, 0.95),
    ]

    # --- Murs du salon ---
    # +X : deux pans de part et d'autre de l'ouverture vers l'aile
    solids += [
        _box(sx0, sx0 + wall, sy0, sy1, z0, z1, 0.92),                 # -X
        _box(sx0, sx1, sy1 - wall, sy1, z0, z1, 0.92),                 # +Y
        _box(sx1 - wall, sx1, sy0, wy0, z0, z1, 0.92),
        _box(sx1 - wall, sx1, wy1, sy1, z0, z1, 0.92),
    ]

    # Mur -Y avec baie de porte (deux jambages + linteau)
    door_w, door_h = 0.9, 2.05
    door_cx = sx0 + width * 0.28
    solids += [
        _box(sx0, door_cx - door_w / 2, sy0, sy0 + wall, z0, z1, 0.92),
        _box(door_cx + door_w / 2, sx1, sy0, sy0 + wall, z0, z1, 0.92),
        _box(
            door_cx - door_w / 2, door_cx + door_w / 2,
            sy0, sy0 + wall,
            z0 + door_h, z1, 0.92,
        ),
    ]

    # --- Murs de l'aile ---
    solids += [
        _box(wx1 - wall, wx1, wy0, wy1, z0, z1, 0.9),
        _box(sx1, wx1, wy0, wy0 + wall, z0, z1, 0.9),
        _box(sx1, wx1, wy1 - wall, wy1, z0, z1, 0.9),
    ]

    # --- Mobilier ---
    # Canapé le long du mur +Y
    solids.append(_box(-1.1, 1.1, sy1 - 0.95, sy1 - 0.25, z0 + wall, z0 + wall + 0.75, 0.55))
    # Table basse devant le canapé
    solids.append(_box(-0.55, 0.55, sy1 - 1.55, sy1 - 1.05, z0 + wall, z0 + wall + 0.40, 0.7))
    # Bibliothèque haute contre -X
    solids.append(_box(sx0 + wall + 0.05, sx0 + wall + 0.40, -0.9, 0.9, z0 + wall, z0 + wall + 2.0, 0.5))
    # Îlot / table cuisine côté aile
    solids.append(_box(sx1 + 0.4, sx1 + 1.4, -0.45, 0.45, z0 + wall, z0 + wall + 0.90, 0.65))
    # Colonne / pilier
    solids.append(_box(0.85, 1.15, -0.15, 0.15, z0 + wall, z1 - wall, 0.75))
    # Meuble bas sous fenêtre (mur +Y aile)
    solids.append(_box(sx1 + 0.3, wx1 - wall - 0.1, wy1 - 0.55, wy1 - wall - 0.05,
                       z0 + wall, z0 + wall + 0.55, 0.6))
    # Carton / obstacle bas près du centre
    solids.append(_box(-0.35, 0.15, -1.4, -1.05, z0 + wall, z0 + wall + 0.55, 0.45))

    return origin, solids


SCENES = {
    "box": build_scene_box,
    "apartment": build_scene_apartment,
}


def sample_scene(
    psi_deg: float,
    theta_deg: np.ndarray,
    *,
    origin: np.ndarray,
    solids: list[Solid],
    rho_max_m: float = 12.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Renvoie (rho_m, intensity) pour une colonne d'élévations à ψ fixé."""
    psi = math.radians(psi_deg)
    rho = np.zeros(len(theta_deg), dtype=np.float64)
    inten = np.zeros(len(theta_deg), dtype=np.uint8)

    for i, th_deg in enumerate(theta_deg):
        direction = direction_head_frame(math.radians(float(th_deg)), psi)
        best_t: float | None = None
        best_albedo = 1.0
        for solid in solids:
            t = ray_enter_box(
                origin, direction,
                np.asarray(solid.box_min), np.asarray(solid.box_max),
            )
            if t is None or t > rho_max_m:
                continue
            if best_t is None or t < best_t:
                best_t = t
                best_albedo = solid.albedo

        if best_t is None:
            rho[i] = 0.0
            inten[i] = 0
        else:
            rho[i] = best_t
            facing = abs(direction[np.argmax(np.abs(direction))])
            inten[i] = int(np.clip((60 + 160 * facing) * best_albedo, 1, 255))
    return rho, inten


def iter_scan_packets(
    *,
    psi_end_deg: float,
    psi_speed_deg_s: float,
    points_per_packet: int,
    theta_step_deg: float,
    width: float,
    depth: float,
    height: float,
    sensor_z: float,
    realtime: bool,
    scene: str = "apartment",
):
    """Générateur de datagrammes pour un balayage 0 → psi_end."""
    builder = SCENES.get(scene, build_scene_apartment)
    origin, solids = builder(width, depth, height, sensor_z)

    thetas = np.arange(0.0, 360.0, theta_step_deg)
    n_theta = len(thetas)

    dt_packet_s = points_per_packet / 4500.0
    d_psi = psi_speed_deg_s * dt_packet_s

    sequence = 0
    t0 = time.monotonic()
    psi = 0.0
    theta_idx = 0
    first = True
    t_us = 0

    while psi <= psi_end_deg + 1e-9:
        idx = (theta_idx + np.arange(points_per_packet)) % n_theta
        batch_theta = thetas[idx]
        theta_idx += points_per_packet

        rho, inten = sample_scene(psi, batch_theta, origin=origin, solids=solids)
        psi_end = min(psi + d_psi, psi_end_deg)
        flags = FLAG_SCAN_START if first else 0
        first = False

        points = []
        for k in range(points_per_packet):
            rho_mm = int(np.clip(round(rho[k] * 1000), 0, 65535))
            theta_cdeg = int(round(batch_theta[k] * 100)) % 36000
            dt = int(k * (dt_packet_s * 1e6) / max(points_per_packet - 1, 1))
            points.append((rho_mm, theta_cdeg, int(inten[k]), min(dt, 65535)))

        yield pack_packet(
            points,
            sequence=sequence,
            flags=flags,
            speed_dhz=50,
            t_start_us=t_us,
            psi_start_mdeg=int(round(psi * 1000)),
            psi_end_mdeg=int(round(psi_end * 1000)),
        )
        sequence += 1
        t_us += int(dt_packet_s * 1e6)
        psi = psi_end

        if realtime:
            target = t0 + sequence * dt_packet_s
            delay = target - time.monotonic()
            if delay > 0:
                time.sleep(delay)
        else:
            time.sleep(0.001)

        if psi >= psi_end_deg - 1e-9:
            break

    yield pack_packet(
        [(0, 0, 0, 0)],
        sequence=sequence,
        flags=FLAG_SCAN_END,
        speed_dhz=50,
        t_start_us=t_us,
        psi_start_mdeg=int(round(psi_end_deg * 1000)),
        psi_end_mdeg=int(round(psi_end_deg * 1000)),
    )


def accumulate_points(datagrams: list[bytes], calib: Calibration) -> np.ndarray:
    """Décode les datagrammes et renvoie le nuage XYZ (même chaîne que l'hôte)."""
    chunks: list[np.ndarray] = []
    for raw in datagrams:
        packet = parse_packet(raw)
        if packet is None or len(packet) == 0:
            continue
        mask = valid_mask(packet.rho_m, packet.intensity, calib)
        if not mask.any():
            continue
        chunks.append(
            polar_to_cartesian(
                packet.rho_m[mask],
                packet.theta_deg[mask],
                packet.psi_deg[mask],
                calib,
            )
        )
    if not chunks:
        return np.empty((0, 3))
    return np.concatenate(chunks, axis=0)


def output_path_for_loop(base: Path, loop: int, loops: int) -> Path:
    if loops == 1:
        return base
    stem, suffix = base.stem, base.suffix or ".pcd"
    return base.with_name(f"{stem}_{loop:02d}{suffix}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Flux UDP de test (scène synthétique) pour la station hôte"
    )
    ap.add_argument("--host", default="127.0.0.1", help="IP de la station hôte")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--psi-end", type=float, default=180.0, help="amplitude azimut (°)")
    ap.add_argument("--speed", type=float, default=2.0, help="vitesse azimut (°/s)")
    ap.add_argument("--theta-step", type=float, default=1.0, help="pas d'élévation (°)")
    ap.add_argument("--points", type=int, default=120, help="points par datagramme")
    ap.add_argument("--width", type=float, default=5.0, help="largeur salon X (m)")
    ap.add_argument("--depth", type=float, default=4.5, help="profondeur salon Y (m)")
    ap.add_argument("--height", type=float, default=2.6, help="hauteur sous plafond (m)")
    ap.add_argument("--sensor-z", type=float, default=1.5, help="hauteur capteur (m)")
    ap.add_argument(
        "--scene",
        choices=sorted(SCENES),
        default="apartment",
        help="box = pavé vide ; apartment = L + mobilier (défaut)",
    )
    ap.add_argument(
        "--fast",
        action="store_true",
        help="envoyer au plus vite (ignorer le temps réel LD19)",
    )
    ap.add_argument("--loops", type=int, default=1, help="nombre de balayages (0 = infini)")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("scans/simulate.pcd"),
        help="fichier .pcd du nuage simulé",
    )
    ap.add_argument("--no-save", action="store_true", help="UDP uniquement")
    ap.add_argument("--no-udp", action="store_true", help="fichier uniquement")
    ap.add_argument(
        "--calibration",
        type=Path,
        default=Path("calibration.json"),
        help="calibration appliquée au .pcd enregistré",
    )
    args = ap.parse_args()

    save = not args.no_save and args.output is not None and str(args.output) != ""
    send_udp = not args.no_udp
    if not save and not send_udp:
        ap.error("rien à faire : retirez --no-save ou --no-udp")

    calib = Calibration.load(args.calibration) if save else None
    sock = None
    dest = (args.host, args.port)
    if send_udp:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(
        f"[simulate] scène « {args.scene} »  "
        f"{args.width}×{args.depth}×{args.height} m  "
        f"ψ 0…{args.psi_end}° @ {args.speed}°/s"
    )
    if send_udp:
        print(f"[simulate] UDP → {args.host}:{args.port}")
        print("[simulate] lancer lidar-visualize ou lidar-receive dans un autre terminal")
    if save:
        print(f"[simulate] enregistrement → {args.output}")

    loop = 0
    try:
        while args.loops == 0 or loop < args.loops:
            loop += 1
            datagrams: list[bytes] = []
            for datagram in iter_scan_packets(
                psi_end_deg=args.psi_end,
                psi_speed_deg_s=args.speed,
                points_per_packet=args.points,
                theta_step_deg=args.theta_step,
                width=args.width,
                depth=args.depth,
                height=args.height,
                sensor_z=args.sensor_z,
                realtime=not args.fast,
                scene=args.scene,
            ):
                datagrams.append(datagram)
                if sock is not None:
                    sock.sendto(datagram, dest)

            print(f"[simulate] balayage {loop} terminé ({len(datagrams)} datagrammes)")

            if save and calib is not None:
                points = accumulate_points(datagrams, calib)
                out = output_path_for_loop(args.output, loop, args.loops or loop)
                if len(points):
                    save_cloud(points, out)
                    print(f"[simulate] {len(points):,} points → {out}")
                else:
                    print(f"[simulate] aucun point valide, {out} non écrit")
    except KeyboardInterrupt:
        print("\n[simulate] interrompu")
    finally:
        if sock is not None:
            sock.close()


if __name__ == "__main__":
    main()
