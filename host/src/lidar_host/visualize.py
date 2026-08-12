"""Visualisation temps réel du nuage pendant le balayage."""

from __future__ import annotations

import argparse
import os
import sys
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


def _display_hint() -> str:
    return (
        "Open3D n'a pas pu ouvrir de fenêtre (affichage graphique absent).\n"
        "Sous WSL2, essayez dans l'ordre :\n"
        "  1. export DISPLAY=:0   # WSLg (Windows 11)\n"
        "  2. sinon enregistrer sans fenêtre :\n"
        "       lidar-receive --port 9000 --output scans/test.pcd --auto-stop\n"
        "     puis ouvrir le .pcd sous Windows (CloudCompare, Open3D natif…)\n"
        "  3. ou lancer host/ depuis Python Windows, pas depuis WSL."
    )


def _run_headless(acc: CloudAccumulator, stop: threading.Event, output: Path | None) -> None:
    """Réception seule, avec compteur — même rôle que lidar-receive."""
    print("[visualize] mode sans fenêtre (réception seule)")
    print(_display_hint())
    if output is None:
        output = Path("scans/headless.pcd")
        print(f"[visualize] --output non fourni → {output}")
    try:
        while not stop.is_set():
            time.sleep(0.5)
            print(
                f"\r[visualize] {len(acc):>9,} points  "
                f"{acc.packets:>6} paquets  {acc.dropped} perdus",
                end="",
                flush=True,
            )
            if acc.finished:
                print("\n[visualize] fin de scan signalée")
                break
    except KeyboardInterrupt:
        print()
    finally:
        stop.set()

    points = acc.snapshot()
    print(f"[visualize] {len(points):,} points")
    if len(points):
        save_cloud(points, output)
        print(f"[visualize] enregistré dans {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Visualisation temps réel du scan")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--calibration", type=Path, default=Path("calibration.json"))
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--refresh", type=float, default=0.25, help="période d'affichage (s)")
    ap.add_argument(
        "--headless",
        action="store_true",
        help="ne pas ouvrir de fenêtre (réception + .pcd uniquement)",
    )
    args = ap.parse_args()

    # WSLg : souvent présent mais DISPLAY non exporté dans le shell.
    if not args.headless and not os.environ.get("DISPLAY") and not os.environ.get(
        "WAYLAND_DISPLAY"
    ):
        if Path("/mnt/wslg").exists():
            os.environ.setdefault("DISPLAY", ":0")
            print("[visualize] DISPLAY non défini — essai avec DISPLAY=:0 (WSLg)")

    calib = Calibration.load(args.calibration)
    acc = CloudAccumulator(calib)
    stop = threading.Event()
    thread = threading.Thread(target=listen, args=(acc, args.port, stop), daemon=True)
    thread.start()

    if args.headless:
        try:
            _run_headless(acc, stop, args.output)
        finally:
            thread.join(timeout=2)
        return

    vis = o3d.visualization.Visualizer()
    ok = vis.create_window(window_name="Scanner 3D LiDAR", width=1400, height=900)
    opt = vis.get_render_option() if ok else None
    if not ok or opt is None:
        # create_window peut renvoyer True puis laisser opt à None (GLFW headless).
        try:
            vis.destroy_window()
        except Exception:
            pass
        print(_display_hint(), file=sys.stderr)
        try:
            _run_headless(acc, stop, args.output)
        finally:
            thread.join(timeout=2)
        return

    cloud = o3d.geometry.PointCloud()
    vis.add_geometry(cloud)
    vis.add_geometry(o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5))
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
