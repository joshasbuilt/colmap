"""Export camera positions from COLMAP reconstruction to TXT file"""
from pathlib import Path
from datetime import datetime
import pycolmap
from export_pointcloud import export_camera_positions

# Parameters
recon_path = Path('reconstruction_single2/export/0')
output_dir = Path('reconstruction_single2/exports')
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = output_dir / f'camera_positions_{timestamp}.txt'

print('Loading reconstruction...')
recon = pycolmap.Reconstruction(str(recon_path))
print(f'Images found: {recon.num_images()}')

# Export camera positions
export_camera_positions(recon, output_file)
print(f'Camera positions exported to: {output_file}')
