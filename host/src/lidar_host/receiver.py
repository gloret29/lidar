"""Réception UDP, conversion cartésienne et accumulation du nuage."""

from __future__ import annotations

import argparse
import socket
import threading
from pathlib import Path

import numpy as np

from lidar_host import FLAG_SCAN_END, FLAG_SHOCK_DETECTED
from lidar_host.protocol import parse_packet
from lidar_host.transform import Calibration, polar_to_cartesian, valid_mask


class CloudAccumulator:
    """Accumule les points reçus, protégé par verrou."""

    def __init__(self, calib: Calibration, max_points: int = 4_000_000) -> None:
        self._lock = threading.Lock()
        self._chunks: list[np.ndarray] = []
        self._count = 0
        self._max = max_points
        self.calib = calib
        self.packets = 0
        self.dropped = 0
        self.shock = False
        self.finished = False
        self._next_seq: int | None = None

    def add_datagram(self, data: bytes) -> int:
        packet = parse_packet(data)
        if packet is None:
            return 0

        if self._next_seq is not None and packet.sequence != self._next_seq:
            self.dropped += max(0, packet.sequence - self._next_seq)
        self._next_seq = packet.sequence + 1

        if packet.flags & FLAG_SHOCK_DETECTED:
            self.shock = True
        if packet.flags & FLAG_SCAN_END:
            self.finished = True

        mask = valid_mask(packet.rho_m, packet.intensity, self.calib)
        if not mask.any():
            return 0

        pts = polar_to_cartesian(
            packet.rho_m[mask], packet.theta_deg[mask],
            packet.psi_deg[mask], self.calib,
        )

        with self._lock:
            if self._count + pts.shape[0] <= self._max:
                self._chunks.append(pts)
                self._count += pts.shape[0]
            self.packets += 1
        return int(pts.shape[0])

    def snapshot(self) -> np.ndarray:
        with self._lock:
            if not self._chunks:
                return np.empty((0, 3))
            if len(self._chunks) > 1:
                self._chunks = [np.concatenate(self._chunks, axis=0)]
            return self._chunks[0]

    def __len__(self) -> int:
        return self._count


def listen(
    accumulator: CloudAccumulator, port: int, stop: threading.Event
) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
    sock.bind(("", port))
    sock.settimeout(0.5)
    print(f"[receiver] écoute UDP sur le port {port}")

    try:
        while not stop.is_set():
            try:
                data, _ = sock.recvfrom(65535)
            except (TimeoutError, socket.timeout):
                continue
            accumulator.add_datagram(data)
    finally:
        sock.close()


def save_cloud(points: np.ndarray, path: Path) -> None:
    import open3d as o3d

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    path.parent.mkdir(parents=True, exist_ok=True)
    o3d.io.write_point_cloud(str(path), cloud)


def main() -> None:
    ap = argparse.ArgumentParser(description="Réception d'un scan LiDAR")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--output", type=Path, default=None, help="fichier .pcd/.ply")
    ap.add_argument("--calibration", type=Path, default=Path("calibration.json"))
    ap.add_argument("--auto-stop", action="store_true",
                    help="s'arrêter à la réception du drapeau de fin de scan")
    args = ap.parse_args()

    calib = Calibration.load(args.calibration)
    acc = CloudAccumulator(calib)
    stop = threading.Event()
    thread = threading.Thread(target=listen, args=(acc, args.port, stop), daemon=True)
    thread.start()

    try:
        while not stop.is_set():
            thread.join(timeout=1.0)
            print(f"\r[receiver] {len(acc):>9,} points  "
                  f"{acc.packets:>6} paquets  {acc.dropped} perdus", end="")
            if args.auto_stop and acc.finished:
                print("\n[receiver] fin de scan signalée")
                break
    except KeyboardInterrupt:
        print()
    finally:
        stop.set()
        thread.join(timeout=2)

    if acc.shock:
        print("[receiver] ATTENTION : choc détecté, le scan est suspect")

    points = acc.snapshot()
    print(f"[receiver] {len(points):,} points au total")
    if args.output is not None and len(points):
        save_cloud(points, args.output)
        print(f"[receiver] enregistré dans {args.output}")


if __name__ == "__main__":
    main()
