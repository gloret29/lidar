"""Parsing du protocole UDP binaire firmware ↔ hôte."""

from __future__ import annotations

import struct
from dataclasses import dataclass

from lidar_host import HEADER_SIZE, PACKET_MAGIC, POINT_SIZE


@dataclass
class Point:
    x: float
    y: float
    z: float
    quality: int


@dataclass
class Packet:
    version: int
    timestamp_us: int
    points: list[Point]


def parse_packet(data: bytes) -> Packet | None:
    """Parse un datagramme UDP complet."""
    if len(data) < HEADER_SIZE:
        return None

    magic, version, count, timestamp_us = struct.unpack_from("<IHHQ", data, 0)
    if magic != PACKET_MAGIC:
        return None

    expected = HEADER_SIZE + count * POINT_SIZE
    if len(data) < expected:
        return None

    points: list[Point] = []
    offset = HEADER_SIZE
    for _ in range(count):
        x, y, z, quality = struct.unpack_from("<fffI", data, offset)
        points.append(Point(x=x, y=y, z=z, quality=quality))
        offset += POINT_SIZE

    return Packet(version=version, timestamp_us=timestamp_us, points=points)
