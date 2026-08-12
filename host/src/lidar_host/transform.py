"""Conversion polaire -> cartésien, avec calibration.

La transformation appliquée est :

    p = R_level . R_z(psi) . ( rho * u(theta) + t )

avec u(theta) = (cos theta, 0, sin theta), le plan de balayage du LiDAR
étant vertical et contenant l'axe de rotation.

theta (angle interne du LiDAR) est l'ÉLÉVATION.
psi   (angle moteur) est l'AZIMUT.

Voir docs/geometry.md pour la démonstration et le contre-exemple qui
disqualifie la formule sphérique naïve.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Calibration:
    lever_arm_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    psi_offset_deg: float = 0.0
    theta_offset_deg: float = 0.0
    steps_per_degree: float = 8.889
    timestamp_offset_us: int = 0
    g_zero: tuple[float, float, float] = (0.0, 0.0, -1.0)
    rho_min_m: float = 0.05
    rho_max_m: float = 12.0
    intensity_min: int = 0
    _level: np.ndarray = field(default=None, repr=False)

    @classmethod
    def load(cls, path: Path | str | None) -> "Calibration":
        if path is None:
            return cls()
        p = Path(path)
        if not p.exists():
            return cls()
        raw = json.loads(p.read_text())
        lever = raw.get("lever_arm_mm", {})
        return cls(
            lever_arm_mm=(
                float(lever.get("tx", 0.0)),
                float(lever.get("ty", 0.0)),
                float(lever.get("tz", 0.0)),
            ),
            psi_offset_deg=float(raw.get("psi_offset_deg", 0.0)),
            theta_offset_deg=float(raw.get("theta_offset_deg", 0.0)),
            steps_per_degree=float(raw.get("steps_per_degree", 8.889)),
            timestamp_offset_us=int(raw.get("timestamp_offset_us", 0)),
            g_zero=tuple(raw.get("g_zero", [0.0, 0.0, -1.0])),
            rho_min_m=float(raw.get("rho_min_m", 0.05)),
            rho_max_m=float(raw.get("rho_max_m", 12.0)),
            intensity_min=int(raw.get("intensity_min", 0)),
        )

    @property
    def level_matrix(self) -> np.ndarray:
        """Rotation amenant g_zero sur (0, 0, -1)."""
        if self._level is None:
            self._level = _rotation_between(
                np.asarray(self.g_zero, dtype=np.float64),
                np.array([0.0, 0.0, -1.0]),
            )
        return self._level


def _rotation_between(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Plus petite rotation amenant le vecteur a sur le vecteur b."""
    na = a / (np.linalg.norm(a) or 1.0)
    nb = b / (np.linalg.norm(b) or 1.0)
    v = np.cross(na, nb)
    c = float(np.dot(na, nb))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else -np.eye(3)
    vx = np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0],
    ])
    return np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))


def polar_to_cartesian(
    rho_m: np.ndarray,
    theta_deg: np.ndarray,
    psi_deg: np.ndarray,
    calib: Calibration,
) -> np.ndarray:
    """Convertit des mesures polaires en points (N, 3), en mètres."""
    theta = np.radians(theta_deg + calib.theta_offset_deg)
    psi = np.radians(psi_deg + calib.psi_offset_deg)

    tx, ty, tz = (v / 1000.0 for v in calib.lever_arm_mm)

    # Repère de la tête : le plan de balayage est le plan XZ.
    hx = rho_m * np.cos(theta) + tx
    hy = np.full_like(rho_m, ty)
    hz = rho_m * np.sin(theta) + tz

    cos_psi, sin_psi = np.cos(psi), np.sin(psi)
    pts = np.empty((rho_m.shape[0], 3), dtype=np.float64)
    pts[:, 0] = cos_psi * hx - sin_psi * hy
    pts[:, 1] = sin_psi * hx + cos_psi * hy
    pts[:, 2] = hz

    level = calib.level_matrix
    if not np.allclose(level, np.eye(3)):
        pts = pts @ level.T
    return pts


def valid_mask(
    rho_m: np.ndarray, intensity: np.ndarray, calib: Calibration
) -> np.ndarray:
    """Écarte les non-retours et les mesures hors plage."""
    return (
        (rho_m >= calib.rho_min_m)
        & (rho_m <= calib.rho_max_m)
        & (intensity >= calib.intensity_min)
    )
