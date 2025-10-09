"""Export transformed COLMAP points to XYZ/PTS after applying full affine:
new = origin_m + scale * R @ orig

Writes:
 - ASCII XYZ (X Y Z R G B) to reconstruction_single/exports/transformed_points_<timestamp>.xyz
 - ASCII PTS (N lines) to reconstruction_single/exports/transformed_points_<timestamp>.pts
"""
from pathlib import Path
from datetime import datetime
import numpy as np
import pycolmap

# Parameters (use the same values we tested)
origin_feet = (18.511377949, 28.950097280, 6.108436373)
scale = 1.5
downsample_scale = 0.1  # Keep 1 in 10 points (0.1 = 10% of points)
basis_x = (-0.115146894, 0.991024226, -0.067913000)
basis_y = (0.086343771, -0.058123614, -0.994568448)
basis_z = (-0.989588776, -0.120385332, -0.078876015)

# Output
out_dir = Path('reconstruction_single/exports')
out_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
xyz_file = out_dir / f'transformed_points_{timestamp}.xyz'
pts_file = out_dir / f'transformed_points_{timestamp}.pts'

# Build rotation matrix and origin in meters
R = np.column_stack([np.array(basis_x), np.array(basis_y), np.array(basis_z)])
origin_m = np.array(origin_feet) * 0.3048

print('Loading reconstruction...')
recon = pycolmap.Reconstruction(str(Path('reconstruction_single/sparse/0')))
N = recon.num_points3D()
print(f'Points found: {N}')
print(f'Downsampling scale: {downsample_scale} (keeping 1 in {int(1/downsample_scale)} points)')

# Collect and transform points with downsampling
points = []
point_count = 0
downsample_factor = int(1 / downsample_scale)  # Convert 0.1 to 10
for pid, p in recon.points3D.items():
    # Apply downsampling
    if point_count % downsample_factor != 0:
        point_count += 1
        continue
    point_count += 1
    
    orig = np.array(p.xyz, dtype=float)
    transformed = origin_m + scale * (R @ orig)
    color = [255, 0, 0]  # Force all points to red
    points.append((transformed, color))

print(f'Points after downsampling: {len(points)}')

# Write XYZ (X Y Z R G B)
with open(xyz_file, 'w') as f:
    for t, c in points:
        f.write(f"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f} {int(c[0])} {int(c[1])} {int(c[2])}\n")

# Write simple PTS (first line N, then X Y Z R G B I)
with open(pts_file, 'w') as f:
    f.write(f"{len(points)}\n")
    for t, c in points:
        intensity = int((int(c[0]) + int(c[1]) + int(c[2]))/3)
        f.write(f"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f} {int(c[0])} {int(c[1])} {int(c[2])} {intensity}\n")

print(f'Wrote transformed XYZ to: {xyz_file}')
print(f'Wrote transformed PTS to: {pts_file}')
print('\nSample transformed point (first):')
if points:
    t0, c0 = points[0]
    print(f'  {t0[0]:.6f}, {t0[1]:.6f}, {t0[2]:.6f}  color={c0}')
