"""analyze_transform.py
Compute and print how the current transform (new = 1.5 * R @ orig) moves the COLMAP point cloud.

Outputs:
 - number of points
 - original centroid and bounds
 - transformed centroid and bounds
 - sample point mappings (first 10)
 - centroid displacement vector and magnitude
 - per-point displacement stats (mean, std, min, max)
 - where the origin maps to under the transform

Run:
    python analyze_transform.py
"""
from pathlib import Path
import numpy as np
import pycolmap

# Revit basis vectors (columns of R)
basis_x = np.array([-0.115146894, 0.991024226, -0.067913000])
basis_y = np.array([0.086343771, -0.058123614, -0.994568448])
basis_z = np.array([-0.989588776, -0.120385332, -0.078876015])

# Build rotation matrix R with columns [BasisX, BasisY, BasisZ]
R = np.column_stack([basis_x, basis_y, basis_z])
scale = 1.5
R_scaled = scale * R

# Path to reconstruction
recon_path = Path('reconstruction_single/sparse/0')
print(f"Loading reconstruction from {recon_path}...")
recon = pycolmap.Reconstruction(str(recon_path))

# Collect points
pts = []
for pid, p in recon.points3D.items():
    pts.append(np.array(p.xyz, dtype=float))
pts = np.vstack(pts)
N = pts.shape[0]
print(f"Point count: {N}")

# Original stats
centroid = pts.mean(axis=0)
minpt = pts.min(axis=0)
maxpt = pts.max(axis=0)

# Transform
pts_t = (R_scaled @ pts.T).T  # new = 1.5 * R @ orig
centroid_t = pts_t.mean(axis=0)
minpt_t = pts_t.min(axis=0)
maxpt_t = pts_t.max(axis=0)

# Displacements
disp = pts_t - pts
disp_mag = np.linalg.norm(disp, axis=1)

# Print summary
np.set_printoptions(precision=6, suppress=True)
print('\nOriginal centroid (COLMAP coords):')
print(f"  {centroid[0]:.6f}, {centroid[1]:.6f}, {centroid[2]:.6f}")
print('Original bounds (min -> max):')
print(f"  X: {minpt[0]:.6f} -> {maxpt[0]:.6f}")
print(f"  Y: {minpt[1]:.6f} -> {maxpt[1]:.6f}")
print(f"  Z: {minpt[2]:.6f} -> {maxpt[2]:.6f}")

print('\nTransformed centroid (new = 1.5 * R @ orig):')
print(f"  {centroid_t[0]:.6f}, {centroid_t[1]:.6f}, {centroid_t[2]:.6f}")
print('Transformed bounds (min -> max):')
print(f"  X: {minpt_t[0]:.6f} -> {maxpt_t[0]:.6f}")
print(f"  Y: {minpt_t[1]:.6f} -> {maxpt_t[1]:.6f}")
print(f"  Z: {minpt_t[2]:.6f} -> {maxpt_t[2]:.6f}")

# Centroid displacement
centroid_disp = centroid_t - centroid
centroid_disp_mag = np.linalg.norm(centroid_disp)
print('\nCentroid displacement (transformed - original):')
print(f"  dx = {centroid_disp[0]:.6f}, dy = {centroid_disp[1]:.6f}, dz = {centroid_disp[2]:.6f}")
print(f"  magnitude = {centroid_disp_mag:.6f}")

# Displacement stats
print('\nPer-point displacement magnitude stats (units):')
print(f"  mean = {disp_mag.mean():.6f}, std = {disp_mag.std():.6f}")
print(f"  min = {disp_mag.min():.6f}, max = {disp_mag.max():.6f}")

# Sample points
n_show = min(10, N)
print(f"\nSample first {n_show} points (orig -> transformed):")
for i in range(n_show):
    o = pts[i]
    t = pts_t[i]
    print(f"  {i}: {o[0]:.6f}, {o[1]:.6f}, {o[2]:.6f}  ->  {t[0]:.6f}, {t[1]:.6f}, {t[2]:.6f}")

# Origin mapping
origin = np.array([0.0, 0.0, 0.0])
origin_t = R_scaled @ origin
print('\nWhere the origin (0,0,0) maps to under the transform:')
print(f"  {origin_t[0]:.6f}, {origin_t[1]:.6f}, {origin_t[2]:.6f}")

print('\nNote: No translation was applied. The transform is rotation+scale only; so points move to R*scale @ orig. If you want the Revit origin translation applied too, run the affine export with origin in feet -> meters and I will compute and export that version.')
