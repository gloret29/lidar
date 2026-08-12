"""Vérification de la transformation polaire -> cartésien.

Ces tests encodent la géométrie décrite dans docs/geometry.md. Ils
constituent le garde-fou contre la régression la plus coûteuse du
projet : reprendre la formule sphérique naïve, qui produit un nuage
cohérent mais faux.
"""

import numpy as np
import pytest

from lidar_host.transform import Calibration, polar_to_cartesian


def convert(rho, theta, psi, calib=None):
    calib = calib or Calibration()
    return polar_to_cartesian(
        np.array([rho], dtype=float),
        np.array([theta], dtype=float),
        np.array([psi], dtype=float),
        calib,
    )[0]


class TestDirections:
    """theta est l'ÉLÉVATION, psi l'AZIMUT."""

    def test_origin_points_along_x(self):
        assert convert(1.0, 0.0, 0.0) == pytest.approx([1, 0, 0], abs=1e-9)

    def test_theta_90_points_up(self):
        assert convert(1.0, 90.0, 0.0) == pytest.approx([0, 0, 1], abs=1e-9)

    def test_theta_270_points_down(self):
        assert convert(1.0, 270.0, 0.0) == pytest.approx([0, 0, -1], abs=1e-9)

    def test_theta_180_points_backwards(self):
        assert convert(1.0, 180.0, 0.0) == pytest.approx([-1, 0, 0], abs=1e-9)

    def test_psi_90_rotates_to_y(self):
        assert convert(1.0, 0.0, 90.0) == pytest.approx([0, 1, 0], abs=1e-9)

    def test_zenith_is_invariant_under_psi(self):
        """Le zénith est sur l'axe : il ne doit pas bouger avec psi."""
        for psi in (0.0, 45.0, 90.0, 180.0):
            assert convert(1.0, 90.0, psi) == pytest.approx([0, 0, 1], abs=1e-9)


class TestScanPlaneIsVertical:
    def test_plane_contains_rotation_axis(self):
        """Pour un psi donné, tous les points sont dans un plan vertical."""
        theta = np.linspace(0, 359, 360)
        psi = np.full_like(theta, 37.0)
        pts = polar_to_cartesian(np.ones_like(theta), theta, psi, Calibration())

        # La normale du plan est horizontale et orthogonale à la direction psi.
        normal = np.array([-np.sin(np.radians(37.0)), np.cos(np.radians(37.0)), 0.0])
        assert np.abs(pts @ normal).max() < 1e-9

    def test_180_degrees_cover_the_sphere(self):
        """Un balayage de 180 deg couvre la sphère : aucune direction manquante."""
        theta = np.linspace(0, 359, 180)
        psi = np.linspace(0, 179, 180)
        tt, pp = np.meshgrid(theta, psi)
        pts = polar_to_cartesian(
            np.ones(tt.size), tt.ravel(), pp.ravel(), Calibration()
        )
        # Chacun des huit octants doit être atteint.
        signs = {tuple(np.sign(p).astype(int)) for p in pts if np.all(np.abs(p) > 0.1)}
        octants = {s for s in signs if 0 not in s}
        assert len(octants) == 8

    def test_norm_is_preserved(self):
        theta = np.linspace(0, 359, 720)
        psi = np.linspace(0, 180, 720)
        rho = np.full(720, 3.7)
        pts = polar_to_cartesian(rho, theta, psi, Calibration())
        assert np.linalg.norm(pts, axis=1) == pytest.approx(3.7, abs=1e-9)


class TestNaiveFormulaIsWrong:
    """Garde-fou : la formule sphérique naïve n'est PAS équivalente."""

    @staticmethod
    def naive(rho, theta_deg, phi_deg):
        t, p = np.radians(theta_deg), np.radians(phi_deg)
        return np.array([
            rho * np.cos(p) * np.cos(t),
            rho * np.cos(p) * np.sin(t),
            rho * np.sin(p),
        ])

    def test_naive_collapses_at_90_degrees(self):
        """À phi = 90 deg, la formule naïve écrase tout le scan au zénith."""
        for theta in (0.0, 45.0, 90.0, 180.0):
            assert self.naive(1.0, theta, 90.0) == pytest.approx([0, 0, 1], abs=1e-9)

    def test_correct_formula_does_not_collapse(self):
        """La transformation correcte balaie bien un cercle complet."""
        pts = [convert(1.0, theta, 90.0) for theta in (0.0, 90.0, 180.0, 270.0)]
        assert len({tuple(np.round(p, 6)) for p in pts}) == 4

    def test_formulas_disagree_away_from_origin(self):
        correct = convert(1.0, 45.0, 60.0)
        naive = self.naive(1.0, 45.0, 60.0)
        assert np.linalg.norm(correct - naive) > 0.3


class TestLeverArm:
    def test_offset_along_scan_axis(self):
        calib = Calibration(lever_arm_mm=(100.0, 0.0, 0.0))
        assert convert(1.0, 0.0, 0.0, calib) == pytest.approx([1.1, 0, 0], abs=1e-9)

    def test_offset_rotates_with_head(self):
        calib = Calibration(lever_arm_mm=(100.0, 0.0, 0.0))
        assert convert(1.0, 0.0, 90.0, calib) == pytest.approx([0, 1.1, 0], abs=1e-9)

    def test_vertical_offset_is_not_rotated(self):
        calib = Calibration(lever_arm_mm=(0.0, 0.0, 50.0))
        assert convert(1.0, 0.0, 90.0, calib) == pytest.approx([0, 1, 0.05], abs=1e-9)

    def test_pure_translation_when_head_does_not_rotate(self):
        """À psi constant, un décalage n'est qu'une translation : pas de courbure."""
        theta = np.linspace(-30, 30, 200)
        rho = 3.0 / np.cos(np.radians(theta))
        psi = np.zeros_like(theta)

        biased = polar_to_cartesian(
            rho, theta, psi, Calibration(lever_arm_mm=(30.0, 0.0, 0.0))
        )
        assert biased[:, 0] == pytest.approx(3.03, abs=1e-9)

    def test_uncompensated_offset_curves_a_flat_wall(self):
        """Justifie la calibration : c'est la ROTATION qui révèle le défaut.

        Le centre optique décalé décrit un cercle quand la tête tourne.
        Reconstruire en supposant l'origine sur l'axe déforme donc un plan
        en surface courbe — erreur systématique, que le filtrage
        d'aberrants ne corrigera jamais.
        """
        tx_mm, wall = 30.0, 3.0
        tx = tx_mm / 1000.0

        # Mesures simulées d'un mur plan à x = wall, tête décalée de tx.
        psi = np.linspace(-70, 70, 300)
        rho = wall / np.cos(np.radians(psi)) - tx
        theta = np.zeros_like(psi)

        exact = polar_to_cartesian(
            rho, theta, psi, Calibration(lever_arm_mm=(tx_mm, 0.0, 0.0))
        )
        assert exact[:, 0] == pytest.approx(wall, abs=1e-9)

        biased = polar_to_cartesian(rho, theta, psi, Calibration())
        assert biased[:, 0].std() > 0.004
        assert np.ptp(biased[:, 0]) > 0.015  # ~20 mm de flèche sur 140 deg


class TestLevelling:
    def test_identity_when_already_level(self):
        calib = Calibration(g_zero=(0.0, 0.0, -1.0))
        assert np.allclose(calib.level_matrix, np.eye(3))

    def test_tilt_is_corrected(self):
        """Une base penchée de 5 deg est redressée."""
        tilt = np.radians(5.0)
        g = (np.sin(tilt), 0.0, -np.cos(tilt))
        calib = Calibration(g_zero=g)
        corrected = calib.level_matrix @ np.array(g)
        assert corrected == pytest.approx([0, 0, -1], abs=1e-9)

    def test_levelling_preserves_distances(self):
        calib = Calibration(g_zero=(0.1, 0.05, -0.99))
        pts = polar_to_cartesian(
            np.full(50, 2.0), np.linspace(0, 359, 50),
            np.linspace(0, 180, 50), calib,
        )
        assert np.linalg.norm(pts, axis=1) == pytest.approx(2.0, abs=1e-9)


class TestOffsets:
    def test_psi_offset_shifts_azimuth(self):
        calib = Calibration(psi_offset_deg=90.0)
        assert convert(1.0, 0.0, 0.0, calib) == pytest.approx([0, 1, 0], abs=1e-9)

    def test_theta_offset_shifts_elevation(self):
        calib = Calibration(theta_offset_deg=90.0)
        assert convert(1.0, 0.0, 0.0, calib) == pytest.approx([0, 0, 1], abs=1e-9)
