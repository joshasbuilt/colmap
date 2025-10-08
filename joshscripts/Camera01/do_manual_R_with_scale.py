from pathlib import Path
from datetime import datetime
import numpy as np
import pycolmap
from export_pointcloud import export_to_dxf_rotation

# Revit basis vectors (columns of R)
basis_x = np.array([-0.115146894, 0.991024226, -0.067913000])
basis_y = np.array([0.086343771, -0.058123614, -0.994568448])
basis_z = np.array([-0.989588776, -0.120385332, -0.078876015])

# Build rotation matrix R with columns [BasisX, BasisY, BasisZ]
R = np.column_stack([basis_x, basis_y, basis_z])

scale = 1.5

# To apply uniform scale with existing export_to_dxf_rotation (which applies R @ xyz),
# we can pre-multiply R by scale so transformed = (scale*R) @ xyz == scale*(R @ xyz)
R_scaled = scale * R

# Load reconstruction
recon_path = Path("reconstruction_single/sparse/0")
reconstruction = pycolmap.Reconstruction(str(recon_path))

# Export: scale marker size by same factor so markers stay proportional
marker_size = 0.02 * scale

output_dir = Path("reconstruction_single/exports")
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_dir = output_dir / f"manual_R_scaled_{timestamp}"
out_dir.mkdir(exist_ok=True)
out_file = out_dir / f"pointcloud_manual_R_scaled_{timestamp}.dxf"

export_to_dxf_rotation(reconstruction, out_file, R_scaled, marker_size=marker_size)
print(f"Wrote scaled manual-R DXF to: {out_file}")
print(f"Scale applied: {scale}x; marker_size used: {marker_size}")
