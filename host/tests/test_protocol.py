"""Décodage du protocole UDP v2."""

import struct

import numpy as np
import pytest

from lidar_host import HEADER_SIZE, PACKET_MAGIC, PROTOCOL_VERSION
from lidar_host.protocol import parse_packet

HEADER = struct.Struct("<IHHIHHQii")


def build_packet(points, *, sequence=0, flags=0, speed_dhz=50,
                 t_start=1234567, psi_start_mdeg=0, psi_end_mdeg=0,
                 magic=PACKET_MAGIC, version=PROTOCOL_VERSION):
    header = HEADER.pack(magic, version, flags, sequence, len(points),
                         speed_dhz, t_start, psi_start_mdeg, psi_end_mdeg)
    body = b"".join(
        struct.pack("<HHBBH", rho, theta, inten, 0, dt)
        for rho, theta, inten, dt in points
    )
    return header + body


def test_header_size_matches_firmware():
    assert HEADER.size == HEADER_SIZE == 32


def test_roundtrip_single_point():
    pkt = parse_packet(build_packet([(1500, 4500, 200, 0)]))
    assert pkt is not None
    assert len(pkt) == 1
    assert pkt.rho_m[0] == pytest.approx(1.5)
    assert pkt.theta_deg[0] == pytest.approx(45.0)
    assert pkt.intensity[0] == 200


def test_metadata_is_decoded():
    pkt = parse_packet(build_packet(
        [(1000, 0, 10, 0)], sequence=42, flags=0x0003,
        speed_dhz=50, psi_start_mdeg=12000, psi_end_mdeg=12500,
    ))
    assert pkt.sequence == 42
    assert pkt.flags == 0x0003
    assert pkt.lidar_speed_hz == pytest.approx(5.0)
    assert pkt.psi_start_deg == pytest.approx(12.0)
    assert pkt.psi_end_deg == pytest.approx(12.5)


def test_psi_is_interpolated_across_the_packet():
    points = [(1000, 0, 10, 0), (1000, 0, 10, 500), (1000, 0, 10, 1000)]
    pkt = parse_packet(build_packet(
        points, psi_start_mdeg=10000, psi_end_mdeg=11000
    ))
    assert pkt.psi_deg == pytest.approx([10.0, 10.5, 11.0])


def test_constant_psi_when_no_time_span():
    pkt = parse_packet(build_packet(
        [(1000, 0, 10, 0), (1000, 0, 10, 0)],
        psi_start_mdeg=7000, psi_end_mdeg=7000,
    ))
    assert pkt.psi_deg == pytest.approx([7.0, 7.0])


def test_negative_psi_survives_the_encoding():
    pkt = parse_packet(build_packet([(1000, 0, 10, 0)], psi_start_mdeg=-4500,
                                    psi_end_mdeg=-4500))
    assert pkt.psi_start_deg == pytest.approx(-4.5)


@pytest.mark.parametrize("bad", [
    b"",
    b"\x00" * 10,
    b"\x00" * 40,
])
def test_garbage_is_rejected(bad):
    assert parse_packet(bad) is None


def test_wrong_magic_is_rejected():
    assert parse_packet(build_packet([(1, 2, 3, 4)], magic=0xDEADBEEF)) is None


def test_wrong_version_is_rejected():
    assert parse_packet(build_packet([(1, 2, 3, 4)], version=99)) is None


def test_truncated_body_is_rejected():
    data = build_packet([(1000, 0, 10, 0)] * 5)
    assert parse_packet(data[:-9]) is None


def test_full_packet():
    points = [(1000 + i, (i * 80) % 36000, i % 256, i * 20) for i in range(120)]
    pkt = parse_packet(build_packet(points))
    assert len(pkt) == 120
    assert pkt.rho_m[-1] == pytest.approx(1.119)
    assert np.all(pkt.theta_deg < 360.0)
