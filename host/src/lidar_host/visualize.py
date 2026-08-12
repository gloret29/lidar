"""Visualisation temps réel du nuage pendant le balayage."""

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path

import numpy as np
import open3d as o3d

from lidar_host.receiver import CloudAccumulator, listen, save_cloud
from lidar_host.transform import Calibration


def colorize_by_height(points: np.ndarray) -> np.ndarray:
    """Dégradé sur Z : rend immédiatement lisibles sol, murs et plafond."""
    if len(points) == 0:
        return np.empty((0, 3))
    z = points[:, 2]
    lo, hi = np.percentile(z, 2), np.percentile(z, 98)
    t = np.clip((z - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    colors = np.empty((len(points), 3))
    colors[:, 0] = t
    colors[:, 1] = 0.35 + 0.4 * np.sin(np.pi * t)
    colors[:, 2] = 1.0 - t
    return colors


def main() -> None:
    ap = argparse.ArgumentParser(description="Visualisation temps réel du scan")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--calibration", type=Path, default=Path("calibration.json"))
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--refresh", type=float, default=0.25, help="période d'affichage (s)")
    args = ap.parse_args()

    calib = Calibration.load(args.calibration)
    acc = CloudAccumulator(calib)
    stop = threading.Event()
    thread = threading.Thread(target=listen, args=(acc, args.port, stop), daemon=True)
    thread.start()

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="Scanner 3D LiDAR", width=1400, height=900)
    cloud = o3d.geometry.PointCloud()
    vis.add_geometry(cloud)
    vis.add_geometry(o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5))

    opt = vis.get_render_option()
    opt.point_size = 1.5
    opt.background_color = np.array([0.08, 0.09, 0.11])

    last_draw = 0.0
    first = True
    try:
        while vis.poll_events():
            now = time.monotonic()
            if now - last_draw >= args.refresh:
                last_draw = now
                pts = acc.snapshot()
                if len(pts):
                    cloud.points = o3d.utility.Vector3dVector(pts)
                    cloud.colors = o3d.utility.Vector3dVector(colorize_by_height(pts))
                    vis.update_geometry(cloud)
                    if first:
                        vis.reset_view_point(True)
                        first = False
            vis.update_renderer()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        thread.join(timeout=2)
        vis.destroy_window()

    points = acc.snapshot()
    print(f"[visualize] {len(points):,} points")
    if args.output is not None and len(points):
        save_cloud(points, args.output)
        print(f"[visualize] enregistré dans {args.output}")


if __name__ == "__main__":
    main()
