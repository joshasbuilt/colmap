#!/usr/bin/env python3
"""
Export camera data to JSON format with image names for JavaScript consumption
"""

import pycolmap
import json
from pathlib import Path
from colmap_utils import process_camera_data

def export_reconstruction_to_json(folder_path, folder_num, output_dir):
    """Export a single reconstruction to JSON format"""
    print(f"Processing folder {folder_num}: {folder_path}")
    
    # Load reconstruction
    recon = pycolmap.Reconstruction(str(folder_path))
    print(f"  Loaded reconstruction with {recon.num_images()} images")
    
    # Extract camera data
    camera_data = []
    for image_id, image in recon.images.items():
        cam_from_world = image.cam_from_world()
        rot_mat = cam_from_world.rotation.matrix()
        cam_pos = -rot_mat.T @ cam_from_world.translation
        
        cam_data = {
            'image_id': image_id,
            'image_name': image.name,
            'position_3d': cam_pos.tolist(),
            'position_3d_oriented': None,
            'height': float(cam_pos[2]),
            'camera_id': image.camera_id
        }
        camera_data.append(cam_data)
    
    print(f"  Found {len(camera_data)} registered camera positions")
    
    # Process camera data with gravity correction
    R_combined, camera_data = process_camera_data(camera_data, debug_output=False)
    
    if R_combined is None:
        print(f"  WARNING: Not enough camera positions for gravity estimation")
        return
    
    # Convert to JSON-friendly format
    json_data = {
        'reconstruction_id': folder_num,
        'num_cameras': len(camera_data),
        'cameras': []
    }
    
    for cam_data in camera_data:
        json_data['cameras'].append({
            'image_id': int(cam_data['image_id']),
            'image_name': cam_data['image_name'],
            'x': float(cam_data['position_3d_oriented'][0]),
            'y': float(cam_data['position_3d_oriented'][1]),
            'z': float(cam_data['position_3d_oriented'][2]),
            'height': float(cam_data['height'])
        })
    
    # Save to JSON file
    output_file = output_dir / f"camera_data_{folder_num}.json"
    with open(output_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"  Exported {len(json_data['cameras'])} cameras to {output_file}")

def main():
    # Process all reconstruction folders
    sparse_path = Path("D:/Camera01/reconstruction_mask3_012_previews_run/sparse")
    
    if not sparse_path.exists():
        print(f"ERROR: Sparse directory not found: {sparse_path}")
        return
    
    # Create output directory
    output_dir = Path("svg_output")
    output_dir.mkdir(exist_ok=True)
    
    # Find all numbered subdirectories
    reconstruction_folders = []
    for item in sparse_path.iterdir():
        if item.is_dir() and item.name.isdigit():
            reconstruction_folders.append(int(item.name))
    
    reconstruction_folders.sort()
    
    if not reconstruction_folders:
        print("ERROR: No reconstruction folders found")
        return
    
    print(f"Found reconstruction folders: {reconstruction_folders}")
    
    # Process each reconstruction folder
    for folder_num in reconstruction_folders:
        print(f"\n{'='*60}")
        print(f"PROCESSING RECONSTRUCTION FOLDER: {folder_num}")
        print(f"{'='*60}")
        
        folder_path = sparse_path / str(folder_num)
        if not folder_path.exists():
            print(f"ERROR: Folder {folder_num} not found: {folder_path}")
            continue
        
        try:
            export_reconstruction_to_json(folder_path, folder_num, output_dir)
        except Exception as e:
            print(f"ERROR processing folder {folder_num}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*60}")
    print("ALL RECONSTRUCTIONS EXPORTED TO JSON")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

