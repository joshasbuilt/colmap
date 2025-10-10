"""Quick script to check what colors are in the COLMAP reconstruction"""
from pathlib import Path
import pycolmap
import numpy as np

recon_path = Path('reconstruction_single2/export/0')
recon = pycolmap.Reconstruction(str(recon_path))

print(f"Total 3D points: {recon.num_points3D()}")
print("\nSampling first 10 point colors:")

for i, (point_id, point) in enumerate(recon.points3D.items()):
    if i >= 10:
        break
    rgb = point.color
    print(f"Point {point_id}: RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")

# Get color statistics
all_colors = []
for point_id, point in recon.points3D.items():
    all_colors.append(point.color)

all_colors = np.array(all_colors)
print(f"\nColor statistics:")
print(f"  Mean RGB: ({all_colors[:, 0].mean():.1f}, {all_colors[:, 1].mean():.1f}, {all_colors[:, 2].mean():.1f})")
print(f"  Min RGB: ({all_colors[:, 0].min()}, {all_colors[:, 1].min()}, {all_colors[:, 2].min()})")
print(f"  Max RGB: ({all_colors[:, 0].max()}, {all_colors[:, 1].max()}, {all_colors[:, 2].max()})")


