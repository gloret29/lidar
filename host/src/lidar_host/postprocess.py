"""Post-traitement : filtrage, recalage multi-positions, maillage."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import open3d as o3d


def clean(
    cloud: o3d.geometry.PointCloud,
    voxel: float = 0.0,
    nb_neighbors: int = 20,
    std_ratio: float = 2.0,
) -> o3d.geometry.PointCloud:
    if voxel > 0:
        cloud = cloud.voxel_down_sample(voxel)
    cloud, _ = cloud.remove_statistical_outlier(nb_neighbors, std_ratio)
    return cloud


def register(clouds: list[o3d.geometry.PointCloud], voxel: float = 0.05):
    """Recalage grossier par FPFH puis affinage ICP, deux à deux."""
    merged = clouds[0]
    for i, src in enumerate(clouds[1:], start=1):
        src_d = src.voxel_down_sample(voxel)
        tgt_d = merged.voxel_down_sample(voxel)
        for c in (src_d, tgt_d):
            c.estimate_normals(
                o3d.geometry.KDTreeSearchParamHybrid(radius=voxel * 2, max_nn=30)
            )

        result = o3d.pipelines.registration.registration_icp(
            src_d, tgt_d, voxel * 3, np.eye(4),
            o3d.pipelines.registration.TransformationEstimationPointToPlane(),
        )
        print(f"  position {i}: fitness={result.fitness:.3f} "
              f"rmse={result.inlier_rmse:.4f}")
        if result.fitness < 0.3:
            print(f"  ATTENTION : recalage douteux pour la position {i}. "
                  f"Recouvrement probablement insuffisant.")
        merged = merged + src.transform(result.transformation)
    return merged


def poisson_mesh(cloud: o3d.geometry.PointCloud, depth: int = 8):
    cloud.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
    )
    cloud.orient_normals_consistent_tangent_plane(30)
    mesh, densities = o3d.pipelines.surface_reconstruction_poisson(cloud, depth=depth) \
        if hasattr(o3d.pipelines, "surface_reconstruction_poisson") else \
        o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(cloud, depth=depth)
    # Élague les zones reconstruites à partir de trop peu de points.
    keep = np.asarray(densities) > np.quantile(np.asarray(densities), 0.02)
    mesh.remove_vertices_by_mask(~keep)
    return mesh


def smooth_mesh(
    mesh: o3d.geometry.TriangleMesh,
    method: str = "taubin",
    iterations: int = 10,
) -> o3d.geometry.TriangleMesh:
    """Lisse la surface. Taubin préserve mieux le volume que Laplacian."""
    method = method.lower()
    if method in ("none", "off", ""):
        return mesh
    if method == "taubin":
        return mesh.filter_smooth_taubin(number_of_iterations=iterations)
    if method == "laplacian":
        return mesh.filter_smooth_laplacian(number_of_iterations=iterations)
    if method == "simple":
        return mesh.filter_smooth_simple(number_of_iterations=iterations)
    raise ValueError(f"méthode de lissage inconnue : {method}")


def main_register() -> None:
    ap = argparse.ArgumentParser(description="Recalage de plusieurs scans")
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--voxel", type=float, default=0.05)
    args = ap.parse_args()

    clouds = [o3d.io.read_point_cloud(str(p)) for p in args.inputs]
    print(f"[register] {len(clouds)} positions")
    merged = register(clouds, args.voxel)
    o3d.io.write_point_cloud(str(args.output), merged)
    print(f"[register] {len(merged.points):,} points -> {args.output}")


def main_mesh() -> None:
    ap = argparse.ArgumentParser(description="Reconstruction de surface")
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--voxel", type=float, default=0.01)
    ap.add_argument(
        "--smooth",
        choices=("none", "taubin", "laplacian", "simple"),
        default="taubin",
        help="lissage post-Poisson (taubin recommandé)",
    )
    ap.add_argument(
        "--smooth-iter",
        type=int,
        default=10,
        help="nombre d'itérations de lissage",
    )
    args = ap.parse_args()

    path = Path(args.input)
    if path.suffix.lower() == ".ply":
        # Relisser un maillage déjà produit.
        mesh = o3d.io.read_triangle_mesh(str(path))
        if len(mesh.triangles) == 0:
            raise SystemExit(f"[mesh] aucun triangle dans {path}")
    else:
        cloud = clean(o3d.io.read_point_cloud(str(path)), voxel=args.voxel)
        mesh = poisson_mesh(cloud, args.depth)

    if args.smooth != "none":
        print(f"[mesh] lissage {args.smooth} × {args.smooth_iter}")
        mesh = smooth_mesh(mesh, args.smooth, args.smooth_iter)
        mesh.compute_vertex_normals()

    o3d.io.write_triangle_mesh(str(args.output), mesh)
    print(f"[mesh] {len(mesh.triangles):,} triangles -> {args.output}")


if __name__ == "__main__":
    main_mesh()
