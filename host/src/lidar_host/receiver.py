"""Réception UDP et accumulation de points."""

from __future__ import annotations

import argparse
import socket
from pathlib import Path

import numpy as np

from lidar_host.protocol import parse_packet


def receive_loop(port: int, output: Path | None = None) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    sock.settimeout(1.0)
    print(f"[receiver] listening on UDP :{port}")

    all_points: list[tuple[float, float, float]] = []
    packet_count = 0

    try:
        while True:
            try:
                data, addr = sock.recvfrom(65535)
            except TimeoutError:
                continue

            packet = parse_packet(data)
            if packet is None:
                continue

            packet_count += 1
            for p in packet.points:
                all_points.append((p.x, p.y, p.z))

            if packet_count % 50 == 0:
                print(f"[receiver] {packet_count} packets, {len(all_points)} points")

    except KeyboardInterrupt:
        print(f"\n[receiver] stopped — {len(all_points)} points total")

    sock.close()

    if output and all_points:
        _save_pcd(all_points, output)
        print(f"[receiver] saved {output}")


def _save_pcd(points: list[tuple[float, float, float]], path: Path) -> None:
    import open3d as o3d

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    o3d.io.write_point_cloud(str(path), cloud)


def main() -> None:
    parser = argparse.ArgumentParser(description="Réception UDP nuage de points LiDAR")
    parser.add_argument("--port", type=int, default=9000, help="Port UDP")
    parser.add_argument("--output", type=Path, default=None, help="Fichier .pcd à la fin (Ctrl+C)")
    args = parser.parse_args()
    receive_loop(args.port, args.output)


if __name__ == "__main__":
    main()
