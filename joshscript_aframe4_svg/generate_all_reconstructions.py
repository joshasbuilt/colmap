#!/usr/bin/env python3
"""
Generate SVG and point cloud from ALL COLMAP reconstructions with gravity correction
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

# Configuration flag - easily switch between XY and YZ views
# ================================================================
# USE_YZ_VIEW = False  # XY view (top-down, red dots) - DEFAULT
# USE_YZ_VIEW = True   # YZ view (side view, blue dots)
# ================================================================
USE_YZ_VIEW = True  # Set to True for YZ side view, False for XY top view

def generate_svg_yz(camera_data, output_file):
    """Generate SVG from camera data using YZ coordinates (side view)."""
    # Sort camera data by image name to ensure chronological order
    camera_data_sorted = sorted(camera_data, key=lambda x: x['image_name'])
    
    # Remove duplicate positions (same Y,Z coordinates) to prevent loops
    unique_positions = []
    seen_positions = set()
    
    for cam_data in camera_data_sorted:
        pos = cam_data['position_3d_oriented']
        pos_key = (round(pos[1], 3), round(pos[2], 3))  # Y,Z coordinates
        
        if pos_key not in seen_positions:
            unique_positions.append(cam_data)
            seen_positions.add(pos_key)
    
    print(f"  Removed {len(camera_data_sorted) - len(unique_positions)} duplicate positions")
    
    # Get 2D coordinates (Y, Z from oriented positions) in chronological order
    y_coords = [cam['position_3d_oriented'][1] for cam in unique_positions]
    z_coords = [cam['position_3d_oriented'][2] for cam in unique_positions]
    
    # Calculate bounds
    avg_y = np.mean(y_coords)
    avg_z = np.mean(z_coords)
    
    y_sorted = np.sort(y_coords)
    z_sorted = np.sort(z_coords)
    p10_idx = int(len(y_sorted) * 0.1)
    p90_idx = int(len(y_sorted) * 0.9)
    y_p10, y_p90 = y_sorted[p10_idx], y_sorted[p90_idx]
    z_p10, z_p90 = z_sorted[p10_idx], z_sorted[p90_idx]
    
    padding_factor = 1.3
    width = (y_p90 - y_p10) * padding_factor
    height = (z_p90 - z_p10) * padding_factor
    
    # Shift coordinates so average becomes origin
    y_coords_shifted = np.array(y_coords) - avg_y
    z_coords_shifted = np.array(z_coords) - avg_z
    
    viewbox_y = -width / 2
    viewbox_z = -height / 2
    
    # Create SVG
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg viewBox="{viewbox_y:.3f} {viewbox_z:.3f} {width:.3f} {height:.3f}" ')
    svg_lines.append(f'     xmlns="http://www.w3.org/2000/svg">')
    svg_lines.append('  <!-- Gravity-corrected camera positions (YZ side view) -->')
    
    circle_radius = width * 0.008
    stroke_width = circle_radius * 0.2
    
    # Draw camera positions in chronological order
    for i, (y, z) in enumerate(zip(y_coords_shifted, z_coords_shifted)):
        cam_data = unique_positions[i]
        pos = cam_data['position_3d_oriented']
        
        tooltip_parts = [
            f"Camera {i+1}",
            f"YZ: ({y:.2f}, {z:.2f})",
            f"3D: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})",
            f"Image: {cam_data['image_name']}",
            f"Frame: {cam_data.get('frame_id', 'unknown')}",
            f"Height: {pos[2]:.2f}m"
        ]
        
        tooltip_text = " | ".join(tooltip_parts)
        
        svg_lines.append(f'  <circle cx="{y:.3f}" cy="{z:.3f}" r="{circle_radius:.4f}" ')
        svg_lines.append(f'          fill="blue" stroke="darkblue" stroke-width="{stroke_width:.4f}" ')
        svg_lines.append(f'          opacity="0.8">')
        svg_lines.append(f'    <title>{tooltip_text}</title>')
        svg_lines.append(f'  </circle>')
    
    # Draw path connecting consecutive points only (no closed loop)
    print(f"  Drawing {len(y_coords_shifted) - 1} line segments for trajectory")
    for i in range(len(y_coords_shifted) - 1):
        y1, z1 = y_coords_shifted[i], z_coords_shifted[i]
        y2, z2 = y_coords_shifted[i + 1], z_coords_shifted[i + 1]
        svg_lines.append(f'  <line x1="{y1:.3f}" y1="{z1:.3f}" x2="{y2:.3f}" y2="{z2:.3f}" ')
        svg_lines.append(f'        stroke="blue" stroke-width="{stroke_width * 2:.4f}" ')
        svg_lines.append(f'        opacity="0.4" />')
    
    # Debug: Show first and last few positions
    print(f"  First 3 positions: {[(y_coords_shifted[i], z_coords_shifted[i]) for i in range(min(3, len(y_coords_shifted)))]}")
    print(f"  Last 3 positions: {[(y_coords_shifted[i], z_coords_shifted[i]) for i in range(max(0, len(y_coords_shifted)-3), len(y_coords_shifted))]}")
    
    svg_lines.append('</svg>')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))
    
    print(f"Generated YZ SVG with {len(unique_positions)} camera positions")
    print(f"  ViewBox: {viewbox_y:.3f} {viewbox_z:.3f} {width:.3f} {height:.3f}")


def process_single_reconstruction(folder_path, folder_num):
    """Process a single reconstruction folder"""
    print(f"Processing folder {folder_num}: {folder_path}")
    
    # Load reconstruction
    recon = pycolmap.Reconstruction(str(folder_path))
    print(f"  Loaded reconstruction with {recon.num_cameras()} cameras, {recon.num_images()} images, {recon.num_points3D()} 3D points")
    
    # Extract camera data
    camera_data = []
    for image_id, image in recon.images.items():
        # All images in a reconstruction are already registered
        cam_from_world = image.cam_from_world()
        rot_mat = cam_from_world.rotation.matrix()
        cam_pos = -rot_mat.T @ cam_from_world.translation
        
        cam_data = {
            'image_id': image_id,
            'image_name': image.name,
            'position_3d': cam_pos,
            'position_3d_oriented': None,  # Will be filled after gravity correction
            'height': cam_pos[2],
            'camera_id': image.camera_id
        }
        camera_data.append(cam_data)
    
    print(f"  Found {len(camera_data)} registered camera positions")
    
    # Process camera data with gravity correction
    R_combined, camera_data = process_camera_data(camera_data, debug_output=False)
    
    if R_combined is None:
        print(f"  WARNING: Not enough camera positions for gravity estimation")
        return
    
    # Generate output files
    output_dir = Path("svg_output")
    output_dir.mkdir(exist_ok=True)
    
    svg_file = output_dir / f"camera_positions_{folder_num}.svg"
    pts_file = output_dir / f"camera_positions_{folder_num}.pts"
    full_pts_file = output_dir / f"full_pointcloud_{folder_num}.pts"
    
    # Generate SVG based on configuration flag
    if USE_YZ_VIEW:
        generate_svg_yz(camera_data, svg_file)
        print(f"  Generated YZ SVG: {svg_file}")
    else:
        generate_svg(camera_data, svg_file)
        print(f"  Generated XY SVG: {svg_file}")
    
    # Export camera positions as point cloud
    export_point_cloud(camera_data, pts_file)
    print(f"  Generated camera PTS: {pts_file}")
    
    # Export full 3D point cloud with gravity correction
    export_full_point_cloud(recon, R_combined, full_pts_file, downsample=10)
    print(f"  Generated full PTS: {full_pts_file}")
    
    # Show height analysis
    heights = [cam['position_3d_oriented'][2] for cam in camera_data]
    print(f"  Camera height analysis:")
    print(f"    Min Z: {min(heights):.6f}m")
    print(f"    Max Z: {max(heights):.6f}m")
    print(f"    Range: {max(heights) - min(heights):.6f}m")
    print(f"    Average: {sum(heights)/len(heights):.6f}m")
    
    print(f"  Folder {folder_num} processing complete!")

def main():
    # Process all reconstruction folders
    sparse_path = Path("D:/Camera01/reconstruction_mask3_012_previews_run/sparse")
    
    if not sparse_path.exists():
        print(f"ERROR: Sparse directory not found: {sparse_path}")
        return
    
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
    
    # Show current configuration
    view_type = "YZ (side view, blue)" if USE_YZ_VIEW else "XY (top-down, red)"
    print(f"Using {view_type} view for SVG generation")
    
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
            # Process this reconstruction
            process_single_reconstruction(folder_path, folder_num)
        except Exception as e:
            print(f"ERROR processing folder {folder_num}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*60}")
    print("ALL RECONSTRUCTIONS PROCESSED")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
