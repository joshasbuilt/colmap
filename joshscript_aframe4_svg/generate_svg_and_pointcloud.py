#!/usr/bin/env python3
"""
Generate SVG and point cloud from COLMAP reconstruction with gravity correction
"""

import pycolmap
import numpy as np
from pathlib import Path
from datetime import datetime
from colmap_utils import (
    export_point_cloud, 
    export_full_point_cloud, 
    process_camera_data, 
    generate_svg
)


def main():
    # Load COLMAP reconstruction from the correct D: drive location
    sparse_path = "D:/Camera01/reconstruction_mask3_012_previews_run/sparse/0"
    print(f"Loading COLMAP reconstruction from: {sparse_path}")
    
    recon = pycolmap.Reconstruction(sparse_path)
    print(f"  Total images: {recon.num_images()}")
    print(f"  Total 3D points: {recon.num_points3D()}")
    
    # Extract camera positions
    camera_data = []
    for image_id, image in recon.images.items():
        cam_from_world = image.cam_from_world()
        rot_mat = cam_from_world.rotation.matrix()
        cam_pos = -rot_mat.T @ cam_from_world.translation
        
        camera_info = {
            'position_3d': cam_pos,
            'image_name': image.name,
            'image_id': image_id,
            'camera_id': image.camera_id,
            'height': cam_pos[2]
        }
        camera_data.append(camera_info)
    
    print(f"  Extracted {len(camera_data)} camera positions")
    
    # Process camera data with gravity correction
    R_combined, camera_data = process_camera_data(camera_data, debug_output=True)
    
    if R_combined is None:
        print("ERROR: Failed to process camera data")
        return
    
    # Show sample transformations (first 5 cameras)
    print(f"Sample transformations (first 5 cameras):")
    for i, cam_data in enumerate(camera_data):
        if i < 5:
            orig = cam_data['position_3d']
            oriented_pos = cam_data['position_3d_oriented']
            print(f"  Camera {i+1}:")
            print(f"    Before: ({orig[0]:7.3f}, {orig[1]:7.3f}, {orig[2]:7.3f})")
            print(f"    After:  ({oriented_pos[0]:7.3f}, {oriented_pos[1]:7.3f}, {oriented_pos[2]:7.3f})")
    
    # Create output directory
    output_dir = Path("svg_output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate output files with correct naming
    svg_file = output_dir / "camera_positions_0.svg"
    pts_file = output_dir / "camera_positions_0.pts"
    full_pts_file = output_dir / "full_pointcloud_0.pts"
    
    print(f"\nGenerating SVG...")
    generate_svg(camera_data, str(svg_file))
    
    print(f"Generating camera position point cloud...")
    export_point_cloud(camera_data, str(pts_file))
    
    # Export full 3D point cloud
    print(f"Generating full 3D point cloud (downsampled to 10%)...")
    export_full_point_cloud(recon, R_combined, str(full_pts_file), downsample=10)
    
    # Show height analysis
    heights = [cam['position_3d_oriented'][2] for cam in camera_data]
    print(f"\nCamera height analysis:")
    print(f"  Min Z: {min(heights):.6f}m")
    print(f"  Max Z: {max(heights):.6f}m")
    print(f"  Range: {max(heights) - min(heights):.6f}m")
    print(f"  Average: {sum(heights)/len(heights):.6f}m")
    
    print(f"\n✅ Files generated in svg_output/:")
    print(f"  SVG: {svg_file.name}")
    print(f"  Camera positions: {pts_file.name}")
    print(f"  Full point cloud: {full_pts_file.name} (10% sample)")

if __name__ == "__main__":
    main()
