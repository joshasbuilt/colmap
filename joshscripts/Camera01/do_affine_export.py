from pathlib import Path
from datetime import datetime
import pycolmap
from export_pointcloud import export_to_dxf_transformed

# Revit origin in feet (as provided earlier)
# updated origin from user attachment
origin_feet = (18.511377949, 28.950097280, 6.108436373)
# Revit basis vectors
basis_x = (-0.115146894, 0.991024226, -0.067913000)
basis_y = (0.086343771, -0.058123614, -0.994568448)
basis_z = (-0.989588776, -0.120385332, -0.078876015)

# Parameters
scale = 1.5
marker_size = 0.02

# Paths
recon_path = Path('reconstruction_single/sparse/0')
recon = pycolmap.Reconstruction(str(recon_path))
output_dir = Path('reconstruction_single/exports')
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
out_dir = output_dir / f'affine_manual_{timestamp}'
out_dir.mkdir(exist_ok=True)
out_file = out_dir / f'pointcloud_affine_manual_{timestamp}.dxf'

# Run affine export: origin_feet will be converted to meters inside the function
export_to_dxf_transformed(
    recon, out_file, marker_size=marker_size, scale=scale,
    origin_feet=origin_feet, basis_x=basis_x, basis_y=basis_y, basis_z=basis_z
)
print(f'Wrote affine DXF with origin and scale to: {out_file}')
