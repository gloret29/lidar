"""Générateur UDP de paquets v2 — valide la station hôte sans matériel.

Simule un balayage dans une pièce rectangulaire (rayons contre un pavé
axis-aligned), encode le protocole firmware et envoie vers l'hôte.

Terminal A :
    lidar-visualize --port 9000

Terminal B :
    lidar-simulate --host 127.0.0.1 --port 9000
"""

from __future__ import annotations

import argparse
import math
import socket
import struct
import time

import numpy as np

from lidar_host import (
    FLAG_SCAN_END,
    FLAG_SCAN_START,
    HEADER_SIZE,
    PACKET_MAGIC,
    PROTOCOL_VERSION,
)

_HEADER = struct.Struct("<IHHIHHQii")
assert _HEADER.size == HEADER_SIZE


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


def ray_hit_box(
    origin: np.ndarray,
    direction: np.ndarray,
    box_min: np.ndarray,
    box_max: np.ndarray,
) -> float | None:
    """Intersection rayon / AABB. Renvoie la distance > 0 ou None."""
    # Méthode des slabs (Kay–Kajiya).
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
    if tmax < 0:
        return None
    hit = tmin if tmin > 1e-4 else tmax
    return float(hit) if hit > 1e-4 else None


def direction_head_frame(theta_rad: float, psi_rad: float) -> np.ndarray:
    """Direction unitaire cohérente avec transform.polar_to_cartesian."""
    # Dans la tête : u = (cos θ, 0, sin θ), puis R_z(ψ).
    hx, hy, hz = math.cos(theta_rad), 0.0, math.sin(theta_rad)
    c, s = math.cos(psi_rad), math.sin(psi_rad)
    return np.array([c * hx - s * hy, s * hx + c * hy, hz], dtype=np.float64)


def sample_room(
    psi_deg: float,
    theta_deg: np.ndarray,
    *,
    origin: np.ndarray,
    box_min: np.ndarray,
    box_max: np.ndarray,
    rho_max_m: float = 12.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Renvoie (rho_m, intensity) pour une colonne d'élévations à ψ fixé."""
    psi = math.radians(psi_deg)
    rho = np.zeros(len(theta_deg), dtype=np.float64)
    inten = np.zeros(len(theta_deg), dtype=np.uint8)

    for i, th_deg in enumerate(theta_deg):
        direction = direction_head_frame(math.radians(float(th_deg)), psi)
        hit = ray_hit_box(origin, direction, box_min, box_max)
        if hit is None or hit > rho_max_m:
            rho[i] = 0.0
            inten[i] = 0
        else:
            rho[i] = hit
            # Intensité grossière : murs plus brillants de face.
            facing = abs(direction[np.argmax(np.abs(direction))])
            inten[i] = int(np.clip(80 + 140 * facing, 1, 255))
    return rho, inten


def room_bounds(width: float, depth: float, height: float, sensor_z: float):
    """Pièce centrée en XY, sol à z=-sensor_z, plafond à height-sensor_z."""
    origin = np.array([0.0, 0.0, 0.0])
    box_min = np.array([-width / 2, -depth / 2, -sensor_z])
    box_max = np.array([width / 2, depth / 2, height - sensor_z])
    return origin, box_min, box_max


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
):
    """Générateur de datagrammes pour un balayage 0 → psi_end."""
    origin, box_min, box_max = room_bounds(width, depth, height, sensor_z)

    # Élévations : un tour LiDAR complet, comme le LD19 (0…360).
    thetas = np.arange(0.0, 360.0, theta_step_deg)
    n_theta = len(thetas)

    # Avance en ψ entre deux paquets (ψ quasi constant dans un datagramme,
    # comme côté firmware à 2 °/s).
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

        rho, inten = sample_room(
            psi, batch_theta,
            origin=origin, box_min=box_min, box_max=box_max,
        )
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


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Flux UDP de test (pièce synthétique) pour la station hôte"
    )
    ap.add_argument("--host", default="127.0.0.1", help="IP de la station hôte")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--psi-end", type=float, default=180.0, help="amplitude azimut (°)")
    ap.add_argument("--speed", type=float, default=2.0, help="vitesse azimut (°/s)")
    ap.add_argument("--theta-step", type=float, default=1.0, help="pas d'élévation (°)")
    ap.add_argument("--points", type=int, default=120, help="points par datagramme")
    ap.add_argument("--width", type=float, default=4.0, help="largeur pièce X (m)")
    ap.add_argument("--depth", type=float, default=5.0, help="profondeur pièce Y (m)")
    ap.add_argument("--height", type=float, default=2.5, help="hauteur pièce (m)")
    ap.add_argument("--sensor-z", type=float, default=1.5, help="hauteur capteur (m)")
    ap.add_argument(
        "--fast",
        action="store_true",
        help="envoyer au plus vite (ignorer le temps réel LD19)",
    )
    ap.add_argument("--loops", type=int, default=1, help="nombre de balayages (0 = infini)")
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = (args.host, args.port)

    print(
        f"[simulate] → {args.host}:{args.port}  "
        f"pièce {args.width}×{args.depth}×{args.height} m  "
        f"ψ 0…{args.psi_end}° @ {args.speed}°/s"
    )
    print("[simulate] lancer lidar-visualize ou lidar-receive dans un autre terminal")

    loop = 0
    try:
        while args.loops == 0 or loop < args.loops:
            loop += 1
            n = 0
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
            ):
                sock.sendto(datagram, dest)
                n += 1
            print(f"[simulate] balayage {loop} terminé ({n} datagrammes)")
    except KeyboardInterrupt:
        print("\n[simulate] interrompu")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
