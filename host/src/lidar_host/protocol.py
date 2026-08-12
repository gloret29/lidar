"""Décodage du protocole UDP v2 (points en polaire brut)."""

from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np

from lidar_host import HEADER_SIZE, PACKET_MAGIC, POINT_SIZE, PROTOCOL_VERSION

_HEADER = struct.Struct("<IHHIHHQii")
assert _HEADER.size == HEADER_SIZE


@dataclass
class Packet:
    """Un datagramme décodé, en représentation vectorisée."""

    sequence: int
    flags: int
    lidar_speed_hz: float
    t_start_us: int
    psi_start_deg: float
    psi_end_deg: float
    rho_m: np.ndarray       # (N,) mètres
    theta_deg: np.ndarray   # (N,) élévation
    intensity: np.ndarray   # (N,) uint8
    dt_us: np.ndarray       # (N,) décalage depuis t_start

    def __len__(self) -> int:
        return int(self.rho_m.shape[0])

    @property
    def psi_deg(self) -> np.ndarray:
        """Azimut interpolé à l'horodatage de chaque point.

        À 2 deg/s, psi ne varie que de 0,005 deg sur un paquet : cette
        interpolation est presque toujours négligeable, mais elle reste
        correcte si l'on accélère le balayage.
        """
        span = self.psi_end_deg - self.psi_start_deg
        total = float(self.dt_us[-1]) if len(self) > 1 and self.dt_us[-1] else 0.0
        if total <= 0.0:
            return np.full(len(self), self.psi_start_deg)
        return self.psi_start_deg + span * (self.dt_us / total)


def parse_packet(data: bytes) -> Packet | None:
    """Décode un datagramme. Renvoie None si la trame est invalide."""
    if len(data) < HEADER_SIZE:
        return None

    (magic, version, flags, sequence, count, speed_dhz, t_start,
     psi_start, psi_end) = _HEADER.unpack_from(data, 0)

    if magic != PACKET_MAGIC or version != PROTOCOL_VERSION:
        return None
    if len(data) < HEADER_SIZE + count * POINT_SIZE:
        return None

    raw = np.frombuffer(
        data, dtype=np.dtype([
            ("rho_mm", "<u2"),
            ("theta_cdeg", "<u2"),
            ("intensity", "u1"),
            ("reserved", "u1"),
            ("dt_us", "<u2"),
        ]),
        count=count,
        offset=HEADER_SIZE,
    )

    return Packet(
        sequence=sequence,
        flags=flags,
        lidar_speed_hz=speed_dhz / 10.0,
        t_start_us=t_start,
        psi_start_deg=psi_start / 1000.0,
        psi_end_deg=psi_end / 1000.0,
        rho_m=raw["rho_mm"].astype(np.float64) / 1000.0,
        theta_deg=raw["theta_cdeg"].astype(np.float64) / 100.0,
        intensity=raw["intensity"].copy(),
        dt_us=raw["dt_us"].astype(np.float64),
    )
