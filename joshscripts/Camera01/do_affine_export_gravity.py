from pathlib import Path
from datetime import datetime
import pycolmap
from export_pointcloud import export_cameras_only_to_dxf_transformed

# Revit origin in feet (as provided earlier)
# updated origin from user attachment
origin_feet = (67.472490761, -23.114793212, 151.586679018)
# Revit basis vectors
# basis_x = (-0.418467115, 0.908065903, 0.017366330)
# basis_y = (0.020676428, 0.028640980, -0.999375895)
# basis_z = (-0.907996563, -0.417846874, -0.030760868)

basis_x = (1,0,0)
basis_y = (0,1,0)
basis_z = (0,0,1)

# Parameters
scale = 1.65
marker_size = 0.02
downsample_scale = 0.1  # Keep 1 in 10 points (0.1 = 10% of points)



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
# Only include camera poses, no 3D points
export_cameras_only_to_dxf_transformed(
    recon, out_file, marker_size=marker_size, scale=scale,
    origin_feet=origin_feet, basis_x=basis_x, basis_y=basis_y, basis_z=basis_z,
    camera_index=1  # Use camera1 instead of camera4
)
print(f'Wrote camera poses DXF with origin and scale to: {out_file}')

print('\n' + '='*70)
print('NEXT STEPS:')
print('='*70)
print('1. Check the generated DXF file in your CAD software (AutoCAD, etc.)')
print('2. Verify the point cloud and camera positions are correctly aligned')
print('3. If the DXF looks good, proceed to generate JSON data for A-Frame:')
print('')
print('   python export_cameras_to_json.py')
print('')
print('4. This will create cone_data_YYYYMMDD_HHMMSS.json in reconstruction_single2/exports/')
print('5. Copy that file to paul/joshscript_aframe/cone_data.json for the web viewer')
print('='*70)