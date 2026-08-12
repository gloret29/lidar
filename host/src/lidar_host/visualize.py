"""Visualisation temps réel Open3D."""

from __future__ import annotations

import argparse
import socket
import threading

import numpy as np
import open3d as o3d

from lidar_host.protocol import parse_packet


class PointCloudAccumulator:
    def __init__(self, max_points: int = 500_000) -> None:
        self._lock = threading.Lock()
        self._points: list[tuple[float, float, float]] = []
        self._max_points = max_points

    def add_packet(self, data: bytes) -> int:
        packet = parse_packet(data)
        if packet is None:
            return 0

        with self._lock:
            for p in packet.points:
                self._points.append((p.x, p.y, p.z))
            if len(self._points) > self._max_points:
                self._points = self._points[-self._max_points :]
            return len(packet.points)

    def snapshot(self) -> np.ndarray:
        with self._lock:
            if not self._points:
                return np.empty((0, 3), dtype=np.float64)
            return np.asarray(self._points, dtype=np.float64)


def _udp_thread(port: int, acc: PointCloudAccumulator, stop: threading.Event) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    sock.settimeout(0.5)
    print(f"[visualize] listening on UDP :{port}")

    while not stop.is_set():
        try:
            data, _ = sock.recvfrom(65535)
            n = acc.add_packet(data)
            if n:
                print(f"[visualize] +{n} points (total snapshot pending)")
        except TimeoutError:
            continue

    sock.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualisation temps réel nuage de points")
    parser.add_argument("--port", type=int, default=9000, help="Port UDP")
    args = parser.parse_args()

    acc = PointCloudAccumulator()
    stop = threading.Event()
    thread = threading.Thread(target=_udp_thread, args=(args.port, acc, stop), daemon=True)
    thread.start()

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="LiDAR Scanner 3D", width=1280, height=720)
    cloud = o3d.geometry.PointCloud()
    vis.add_geometry(cloud)

    try:
        while vis.poll_events():
            pts = acc.snapshot()
            if len(pts) > 0:
                cloud.points = o3d.utility.Vector3dVector(pts)
                vis.update_geometry(cloud)
            vis.update_renderer()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        thread.join(timeout=2)
        vis.destroy_window()


if __name__ == "__main__":
    main()
