import pycolmap
import numpy as np
from pathlib import Path

recon_path = Path('reconstruction_single2/export/0')
recon = pycolmap.Reconstruction(str(recon_path))

# Revit transformation parameters
origin_feet = (67.472490761, -23.114793212, 151.586679018)
basis_x = (-0.418467115, 0.908065903, 0.017366330)
basis_y = (0.020676428, 0.028640980, -0.999375895)
basis_z = (-0.907996563, -0.417846874, -0.030760868)
scale = 1.65

# Build rotation matrix
R = np.column_stack([np.array(basis_x), np.array(basis_y), np.array(basis_z)])
origin_m = np.array(origin_feet) * 0.3048

camera_index = 4

# Group images by frame_id
frame_cameras = {}
for image_id, image in recon.images.items():
    if hasattr(image, 'frame_id') and image.frame_id is not None:
        if image.frame_id not in frame_cameras:
            frame_cameras[image.frame_id] = []
        frame_cameras[image.frame_id].append(image)

print(f"Total frames: {len(frame_cameras)}")

# Check first few frames
cameras_found = 0
fallback_used = 0

for frame_id in sorted(list(frame_cameras.keys()))[:5]:
    images_in_frame = frame_cameras[frame_id]
    print(f"\nFrame {frame_id}: {len(images_in_frame)} images")
    
    camera_found = False
    for image in images_in_frame:
        print(f"  - {image.name}, camera_id: {image.camera_id}")
        if f"camera{camera_index}" in image.name.lower():
            print(f"    ✓ MATCH! camera{camera_index} found")
            camera_found = True
            
            # Extract direction
            cam_from_world = image.cam_from_world()
            rot_mat = cam_from_world.rotation.matrix()
            cam_forward = rot_mat.T @ np.array([0.0, 0.0, -1.0])
            print(f"    Forward direction (world): {cam_forward}")
            
            # Transform to Revit coordinates
            transformed_dir = R @ cam_forward
            transformed_dir = transformed_dir / np.linalg.norm(transformed_dir)
            print(f"    Forward direction (Revit): {transformed_dir}")
            break
    
    if camera_found:
        cameras_found += 1
    else:
        fallback_used += 1
        print(f"  ✗ camera{camera_index} NOT FOUND - using fallback")

print(f"\n\nSummary: {cameras_found} cameras found, {fallback_used} fallbacks used")

