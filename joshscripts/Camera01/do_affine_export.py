from pathlib import Path
from datetime import datetime
import pycolmap
from export_pointcloud import export_to_dxf_transformed

# Revit origin in feet (as provided earlier)
# updated origin from user attachment
origin_feet = (67.472490761, -23.114793212, 151.586679018)
# Revit basis vectors
basis_x = (-0.418467115, 0.908065903, 0.017366330)
basis_y = (0.020676428, 0.028640980, -0.999375895)
basis_z = (-0.907996563, -0.417846874, -0.030760868)

# Parameters
scale = 1.65
marker_size = 0.02
downsample_scale = 0.1  # Keep 1 in 10 points (0.1 = 10% of points)


# 


# Paths
recon_path = Path('reconstruction_single2/export/0')
recon = pycolmap.Reconstruction(str(recon_path))

# Downsample: keep only 1 in 10 points
print(f'Original points: {recon.num_points3D()}')

output_dir = Path('reconstruction_single2/exports')
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
out_dir = output_dir / f'affine_manual_{timestamp}'
out_dir.mkdir(exist_ok=True)
out_file = out_dir / f'pointcloud_affine_manual_{timestamp}.dxf'

# Run affine export: origin_feet will be converted to meters inside the function
export_to_dxf_transformed(
    recon, out_file, marker_size=marker_size, scale=scale,
    origin_feet=origin_feet, basis_x=basis_x, basis_y=basis_y, basis_z=basis_z,
    downsample_factor=int(1/downsample_scale),  # Convert 0.1 to 10
    include_camera_poses=True,  # Include camera positions as directional shapes
    camera_index=1  # Use camera1 instead of camera4
)
print(f'Wrote affine DXF with origin and scale to: {out_file}')
