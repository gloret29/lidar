"""Le simulateur produit des paquets que parse_packet accepte."""

from pathlib import Path

import numpy as np

from lidar_host import FLAG_SCAN_END, FLAG_SCAN_START
from lidar_host.protocol import parse_packet
from lidar_host.simulate import (
    accumulate_points,
    iter_scan_packets,
    output_path_for_loop,
    pack_packet,
)
from lidar_host.transform import Calibration


def test_pack_roundtrip():
    raw = pack_packet(
        [(1500, 4500, 200, 10)],
        sequence=7,
        flags=FLAG_SCAN_START,
        psi_start_mdeg=1000,
        psi_end_mdeg=1100,
    )
    pkt = parse_packet(raw)
    assert pkt is not None
    assert pkt.sequence == 7
    assert pkt.flags & FLAG_SCAN_START
    assert pkt.rho_m[0] == 1.5
    assert pkt.theta_deg[0] == 45.0


def test_scan_emits_start_and_end():
    packets = list(
        iter_scan_packets(
            psi_end_deg=2.0,
            psi_speed_deg_s=10.0,
            points_per_packet=12,
            theta_step_deg=30.0,
            width=5.0,
            depth=4.5,
            height=2.6,
            sensor_z=1.5,
            realtime=False,
            scene="apartment",
        )
    )
    assert len(packets) >= 2
    first = parse_packet(packets[0])
    last = parse_packet(packets[-1])
    assert first is not None and last is not None
    assert first.flags & FLAG_SCAN_START
    assert last.flags & FLAG_SCAN_END
    assert any(parse_packet(p).rho_m.max() > 0.5 for p in packets[:-1])


def test_accumulate_builds_cloud():
    packets = list(
        iter_scan_packets(
            psi_end_deg=5.0,
            psi_speed_deg_s=20.0,
            points_per_packet=12,
            theta_step_deg=15.0,
            width=5.0,
            depth=4.5,
            height=2.6,
            sensor_z=1.5,
            realtime=False,
            scene="apartment",
        )
    )
    pts = accumulate_points(packets, Calibration())
    assert pts.ndim == 2 and pts.shape[1] == 3
    assert len(pts) > 100
    assert np.abs(pts).max() < 12.0


def test_apartment_has_more_solids_than_box():
    from lidar_host.simulate import build_scene_apartment, build_scene_box

    _, apt = build_scene_apartment(5.0, 4.5, 2.6, 1.5)
    _, box = build_scene_box(5.0, 4.5, 2.6, 1.5)
    assert len(apt) > len(box) + 5


def test_output_path_for_loop():
    assert output_path_for_loop(Path("scans/sim.pcd"), 1, 1) == Path("scans/sim.pcd")
    assert output_path_for_loop(Path("scans/sim.pcd"), 2, 3) == Path("scans/sim_02.pcd")
