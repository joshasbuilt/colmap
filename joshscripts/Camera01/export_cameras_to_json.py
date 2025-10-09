"""Export camera positions from COLMAP reconstruction to JSON format for A-Frame navigation"""
from pathlib import Path
from datetime import datetime
import json
import numpy as np
import pycolmap

# Revit transformation parameters
origin_feet = (67.472490761, -23.114793212, 151.586679018)
basis_x = (-0.418467115, 0.908065903, 0.017366330)
basis_y = (0.020676428, 0.028640980, -0.999375895)
basis_z = (-0.907996563, -0.417846874, -0.030760868)
scale = 1.65

# Camera to export
camera_index = 1

# Paths
recon_path = Path('reconstruction_single2/export/0')
output_dir = Path('reconstruction_single2/exports')
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = output_dir / f'cone_data_{timestamp}.json'

# Build transformation
R = np.column_stack([np.array(basis_x), np.array(basis_y), np.array(basis_z)])
origin_m = np.array(origin_feet) * 0.3048

print('Loading reconstruction...')
recon = pycolmap.Reconstruction(str(recon_path))
print(f'Total images: {recon.num_images()}')

# Extract camera positions and directions
cones = []
cone_id = 1

# Group images by frame_id
frame_cameras = {}
for image_id, image in recon.images.items():
    if hasattr(image, 'frame_id') and image.frame_id is not None:
        if image.frame_id not in frame_cameras:
            frame_cameras[image.frame_id] = []
        frame_cameras[image.frame_id].append(image)

print(f'Total frames: {len(frame_cameras)}')
print(f'Extracting camera{camera_index} from each frame...')

# For each frame, find the specific camera
for frame_id in sorted(frame_cameras.keys()):
    images_in_frame = frame_cameras[frame_id]
    
    for image in images_in_frame:
        # Check if this is the camera we want
        if f"camera{camera_index}" in image.name.lower():
            # Get camera position
            cam_from_world = image.cam_from_world()
            rot_mat = cam_from_world.rotation.matrix()
            cam_pos = -rot_mat.T @ cam_from_world.translation
            
            # Get camera viewing direction and up vector
            cam_forward = image.viewing_direction().flatten()
            
            # Calculate up vector (camera's Y-axis pointing up)
            cam_up = rot_mat.T @ np.array([0.0, 1.0, 0.0])
            
            # Apply transformation to position
            transformed_pos = origin_m + scale * (R @ cam_pos)
            
            # Apply transformation to direction vectors (rotation only)
            transformed_forward = R @ cam_forward
            transformed_forward = transformed_forward / np.linalg.norm(transformed_forward)
            
            transformed_up = R @ cam_up
            transformed_up = transformed_up / np.linalg.norm(transformed_up)
            
            # Extract frame number from image name (e.g., "frame_0023.jpg" -> 23)
            frame_num = None
            try:
                parts = image.name.split('/')[-1].split('_')
                for part in parts:
                    if part.startswith('00') or part[0].isdigit():
                        frame_num = int(part.replace('.jpg', '').replace('.png', ''))
                        break
            except:
                frame_num = frame_id
            
            # Create cone entry
            cone_entry = {
                "cone_id": cone_id,
                "dxf_position": {
                    "x": float(transformed_pos[0]),
                    "y": float(transformed_pos[1]),
                    "z": float(transformed_pos[2])
                },
                "direction": {
                    "forward": {
                        "x": float(transformed_forward[0]),
                        "y": float(transformed_forward[1]),
                        "z": float(transformed_forward[2])
                    },
                    "up": {
                        "x": float(transformed_up[0]),
                        "y": float(transformed_up[1]),
                        "z": float(transformed_up[2])
                    }
                },
                "camera_index": camera_index,
                "frame_number": frame_num,
                "image_path": f"panoramas/{image.name.split('/')[-1]}"
            }
            
            cones.append(cone_entry)
            cone_id += 1
            break

print(f'Extracted {len(cones)} camera positions')

# Create export info
export_data = {
    "export_info": {
        "timestamp": datetime.now().isoformat(),
        "total_cones": len(cones),
        "camera_index_used": camera_index,
        "dxf_file": f"pointcloud_affine_manual_{timestamp}.dxf"
    },
    "cones": cones
}

# Write JSON file
with open(output_file, 'w') as f:
    json.dump(export_data, f, indent=2)

print(f'\nWrote {len(cones)} camera positions to: {output_file}')
print(f'Format matches cone_data.json for A-Frame navigation')

