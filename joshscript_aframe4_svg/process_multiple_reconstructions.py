#!/usr/bin/env python3
"""
Process multiple COLMAP sparse reconstructions with gravity correction and generate SVGs.
Based on auto_gravity_align.py but modified to handle multiple folders.
"""

import argparse
import numpy as np
import pycolmap
from pathlib import Path
from datetime import datetime
from sklearn.decomposition import PCA

def export_point_cloud(camera_data, output_file):
    """
    Export camera positions as point cloud in PTS format.
    PTS format: X Y Z R G B Intensity
    """
    with open(output_file, 'w') as f:
        # Write header with point count
        f.write(f"{len(camera_data)}\n")
        
        # Write each camera position as a point
        for cam_data in camera_data:
            # Get oriented 3D position
            pos = cam_data['position_3d_oriented']
            x, y, z = pos[0], pos[1], pos[2]
            
            # Use red color for all camera positions
            r, g, b = 255, 0, 0
            intensity = 255  # Full intensity for camera positions
            
            # PTS format: X Y Z R G B Intensity
            f.write(f"{x:.6f} {y:.6f} {z:.6f} {r} {g} {b} {intensity}\n")
    
    print(f"Exported {len(camera_data)} camera positions to {output_file}")

def estimate_gravity_from_cameras(camera_positions):
    """
    Estimate gravity direction from camera positions using PCA.
    Assumes cameras lie approximately on a plane (constant height).
    
    Args:
        camera_positions: Nx3 array of camera positions
        
    Returns:
        gravity_direction: normalized 3D vector pointing "up"
    """
    print(f"Analyzing {len(camera_positions)} camera positions for gravity detection...")
    
    # Center the camera positions
    mean_pos = np.mean(camera_positions, axis=0)
    centered = camera_positions - mean_pos
    
    print(f"Mean camera position: ({mean_pos[0]:.3f}, {mean_pos[1]:.3f}, {mean_pos[2]:.3f})")
    
    # Apply PCA
    pca = PCA(n_components=3)
    pca.fit(centered)
    
    # Print variance explained by each component
    print(f"PCA variance explained:")
    print(f"  Component 1: {pca.explained_variance_[0]:.6f} (main movement direction)")
    print(f"  Component 2: {pca.explained_variance_[1]:.6f} (secondary movement)")
    print(f"  Component 3: {pca.explained_variance_[2]:.6f} (height variation - should be smallest)")
    
    # The component with smallest variance is perpendicular to the plane
    # This is the gravity direction (up vector)
    gravity_direction = pca.components_[2]  # Last component = smallest variance
    
    print(f"Estimated gravity direction (raw): ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    
    # Make sure it points "up" (positive in the vertical direction)
    # Check if we need to flip it - choose direction with positive Z component
    if gravity_direction[2] < 0:
        gravity_direction = -gravity_direction
        print("Flipped gravity direction to point upward")
    
    print(f"Final gravity direction (up): ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    
    return gravity_direction, mean_pos

def compute_gravity_alignment_rotation(gravity_direction, target_up=np.array([0, 0, 1])):
    """
    Compute rotation matrix to align estimated gravity with target up direction (Z-up).
    Uses Rodrigues' rotation formula.
    
    Args:
        gravity_direction: Current up direction (normalized)
        target_up: Desired up direction (default: [0, 0, 1] for Z-up)
        
    Returns:
        R: 3x3 rotation matrix
    """
    # Normalize both vectors
    gravity_direction = gravity_direction / np.linalg.norm(gravity_direction)
    target_up = target_up / np.linalg.norm(target_up)
    
    print(f"Computing rotation to align:")
    print(f"  From: ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    print(f"  To:   ({target_up[0]:.6f}, {target_up[1]:.6f}, {target_up[2]:.6f})")
    
    # Rotation axis (cross product)
    axis = np.cross(gravity_direction, target_up)
    axis_length = np.linalg.norm(axis)
    
    # Handle special case: vectors already aligned
    if axis_length < 1e-10:
        print("Gravity already aligned with Z-up! Using identity rotation.")
        return np.eye(3)
    
    axis = axis / axis_length
    
    # Rotation angle (dot product)
    dot_product = np.clip(np.dot(gravity_direction, target_up), -1.0, 1.0)
    angle = np.arccos(dot_product)
    angle_degrees = np.degrees(angle)
    
    print(f"  Rotation axis: ({axis[0]:.6f}, {axis[1]:.6f}, {axis[2]:.6f})")
    print(f"  Rotation angle: {angle_degrees:.2f} degrees")
    
    # Rodrigues' rotation formula
    K = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])
    
    R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K
    
    return R

def extract_camera_positions(reconstruction, camera_index=1):
    """
    Extract camera positions and metadata from COLMAP reconstruction.
    
    Args:
        reconstruction: pycolmap.Reconstruction object
        camera_index: Which camera to extract (default: 1)
        
    Returns:
        camera_data: List of camera data dictionaries with positions and metadata
    """
    camera_data = []
    
    # Group images by frame_id
    frame_cameras = {}
    for image_id, image in reconstruction.images.items():
        if hasattr(image, 'frame_id') and image.frame_id is not None:
            if image.frame_id not in frame_cameras:
                frame_cameras[image.frame_id] = []
            frame_cameras[image.frame_id].append(image)
    
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
                
                # Extract additional metadata
                camera_info = {
                    'position_3d': cam_pos,
                    'image_name': image.name,
                    'frame_id': frame_id,
                    'image_id': image_id,
                    'camera_id': image.camera_id,
                    'rotation_matrix': rot_mat,
                    'translation': cam_from_world.translation,
                    'quaternion': cam_from_world.rotation.quat,
                    'height': cam_pos[2]
                }
                
                # Try to extract timestamp from image name
                import re
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', image.name)
                if timestamp_match:
                    camera_info['timestamp'] = timestamp_match.group(1)
                
                camera_data.append(camera_info)
                break
    
    return camera_data

def create_top_down_svg(camera_data, R, origin_m, scale, output_file):
    """
    Create an SVG file showing top-down view of camera positions.
    ViewBox is centered on the median camera position for easy alignment.
    
    Args:
        camera_data: List of camera data dictionaries with positions and metadata
        R: 3x3 rotation matrix
        origin_m: origin in meters (for transformation)
        scale: scale factor
        output_file: path to save SVG file
    """
    print("\nGenerating top-down SVG view of camera positions...")
    
    # Extract positions from camera data
    camera_positions = np.array([cam['position_3d'] for cam in camera_data])
    
    # Transform camera positions same way as DXF export
    transformed_positions = []
    for i, cam_pos in enumerate(camera_positions):
        transformed_pos = origin_m + scale * (R @ cam_pos)
        transformed_positions.append(transformed_pos)
        
        # Update the camera_data with oriented Z-coordinate for height
        camera_data[i]['height'] = transformed_pos[2]
        camera_data[i]['position_3d_oriented'] = transformed_pos
    
    transformed_positions = np.array(transformed_positions)
    
    # Extract X and Y coordinates (top-down view)
    # Flip Y-axis to match SVG coordinate system (Y increases downward in SVG)
    x_coords = transformed_positions[:, 0]
    y_coords = -transformed_positions[:, 1]  # Flip Y to match SVG coordinates
    
    # Calculate average center (mean of all points)
    avg_x = np.mean(x_coords)
    avg_y = np.mean(y_coords)
    
    # Calculate robust bounds (10th to 90th percentile + padding)
    x_sorted = np.sort(x_coords)
    y_sorted = np.sort(y_coords)
    p10_idx = int(len(x_sorted) * 0.1)
    p90_idx = int(len(x_sorted) * 0.9)
    x_p10, x_p90 = x_sorted[p10_idx], x_sorted[p90_idx]
    y_p10, y_p90 = y_sorted[p10_idx], y_sorted[p90_idx]
    
    padding_factor = 1.3  # 30% padding
    width = (x_p90 - x_p10) * padding_factor
    height = (y_p90 - y_p10) * padding_factor
    
    # Shift all coordinates so average becomes origin (0,0)
    x_coords_shifted = x_coords - avg_x
    y_coords_shifted = y_coords - avg_y
    
    # ViewBox with origin at (0,0) and size to contain all shifted points
    viewbox_x = -width / 2
    viewbox_y = -height / 2
    
    print(f"  Average center: X={avg_x:.2f}, Y={avg_y:.2f}")
    print(f"  Robust bounds: {width:.2f} x {height:.2f} meters")
    print(f"  ViewBox: x={viewbox_x:.2f}, y={viewbox_y:.2f}, w={width:.2f}, h={height:.2f}")
    
    # Create SVG content with centered viewBox
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg viewBox="{viewbox_x:.3f} {viewbox_y:.3f} {width:.3f} {height:.3f}" ')
    svg_lines.append(f'     xmlns="http://www.w3.org/2000/svg">')
    svg_lines.append('  <!-- Top-down view of camera positions -->')
    svg_lines.append('  <!-- ViewBox is centered on median camera position -->')
    svg_lines.append(f'  <rect x="{viewbox_x}" y="{viewbox_y}" width="{width}" height="{height}" fill="white" opacity="0"/>')
    
    # Calculate circle radius in world units (scaled appropriately)
    circle_radius = width * 0.008  # ~0.8% of width
    stroke_width = circle_radius * 0.2
    
    # Draw camera positions as circles with enhanced metadata
    for i, (x, y) in enumerate(zip(x_coords_shifted, y_coords_shifted)):
        cam_data = camera_data[i]
        
        # Create rich tooltip with metadata
        tooltip_parts = [
            f"Camera {i+1}",
            f"2D: ({x:.2f}, {y:.2f})",
            f"3D: ({cam_data['position_3d_oriented'][0]:.2f}, {cam_data['position_3d_oriented'][1]:.2f}, {cam_data['position_3d_oriented'][2]:.2f})",
            f"Image: {cam_data['image_name']}",
            f"Frame: {cam_data['frame_id']}",
            f"Height: {cam_data['position_3d_oriented'][2]:.2f}m"
        ]
        
        # Add timestamp if available
        if 'timestamp' in cam_data:
            tooltip_parts.append(f"Time: {cam_data['timestamp']}")
        
        # Add camera ID
        tooltip_parts.append(f"Cam ID: {cam_data['camera_id']}")
        
        tooltip_text = " | ".join(tooltip_parts)
        
        svg_lines.append(f'  <circle cx="{x:.3f}" cy="{y:.3f}" r="{circle_radius:.4f}" ')
        svg_lines.append(f'          fill="red" stroke="darkred" stroke-width="{stroke_width:.4f}" ')
        svg_lines.append(f'          opacity="0.8">')
        svg_lines.append(f'    <title>{tooltip_text}</title>')
        svg_lines.append(f'  </circle>')
    
    # Draw path connecting cameras
    path_points = [f"{x:.3f},{y:.3f}" for x, y in zip(x_coords_shifted, y_coords_shifted)]
    svg_lines.append(f'  <polyline points="{" ".join(path_points)}" ')
    svg_lines.append(f'            fill="none" stroke="red" stroke-width="{stroke_width * 2:.4f}" ')
    svg_lines.append(f'            opacity="0.4" />')
    
    # Add center marker for reference (now at origin 0,0)
    marker_size = circle_radius * 3
    svg_lines.append(f'  <line x1="{-marker_size}" y1="0" ')
    svg_lines.append(f'        x2="{marker_size}" y2="0" ')
    svg_lines.append(f'        stroke="blue" stroke-width="{stroke_width:.4f}" opacity="0.5" />')
    svg_lines.append(f'  <line x1="0" y1="{-marker_size}" ')
    svg_lines.append(f'        x2="0" y2="{marker_size}" ')
    svg_lines.append(f'        stroke="blue" stroke-width="{stroke_width:.4f}" opacity="0.5" />')
    
    svg_lines.append('</svg>')
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))
    
    print(f"  Saved SVG to: {output_file}")
    print(f"  {len(camera_positions)} camera positions rendered")
    print(f"  ViewBox centered on median - no offset calculations needed in HTML!")
    
    # Export point cloud (PTS format)
    pts_output_file = str(output_file).replace('.svg', '.pts')
    export_point_cloud(camera_data, pts_output_file)
    
    print(f"  Saved point cloud to: {pts_output_file}")
    print(f"  {len(camera_data)} points exported")

def process_single_reconstruction(sparse_folder, output_dir, camera_index=1, 
                                origin_feet=(67.472490761, -23.114793212, 151.586679018),
                                scale=1.65):
    """
    Process a single reconstruction folder with gravity correction.
    """
    folder_name = sparse_folder.name
    print(f"\n{'='*70}")
    print(f"PROCESSING FOLDER: {folder_name}")
    print(f"{'='*70}")
    
    # Load reconstruction
    print("Loading COLMAP reconstruction...")
    recon = pycolmap.Reconstruction(str(sparse_folder))
    print(f"  Total images: {recon.num_images()}")
    print(f"  Total 3D points: {recon.num_points3D()}")
    
    # Extract camera positions and metadata
    print(f"Extracting camera{camera_index} positions from each frame...")
    camera_data = extract_camera_positions(recon, camera_index=camera_index)
    print(f"  Extracted {len(camera_data)} camera positions with metadata")
    
    if len(camera_data) < 3:
        print("  Warning: Not enough camera positions for gravity estimation. Skipping...")
        return False
    
    # Extract positions for gravity estimation
    camera_positions = np.array([cam['position_3d'] for cam in camera_data])
    
    # Estimate gravity direction using PCA
    print("\nEstimating gravity direction from camera plane...")
    gravity_direction, mean_camera_pos = estimate_gravity_from_cameras(camera_positions)
    
    # Compute rotation to align with Z-up
    print("\nComputing rotation to align with Z-up...")
    R = compute_gravity_alignment_rotation(gravity_direction)
    
    # Convert origin to meters for transformations
    origin_m = np.array(origin_feet) * 0.3048
    
    # Generate SVG with enhanced metadata
    svg_file = output_dir / f'camera_positions_{folder_name}.svg'
    create_top_down_svg(camera_data, R, origin_m, scale, svg_file)
    
    print(f"\nSuccessfully processed folder {folder_name}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Process multiple COLMAP reconstructions with gravity correction')
    parser.add_argument('--sparse-dir', default='D:/Camera01/reconstruction_mask3_012_previews_run/sparse', help='Path to sparse directory containing numbered folders')
    parser.add_argument('--folders', nargs='+', type=int, default=None, help='Specific folder numbers to process (e.g., 0 1 2 3)')
    parser.add_argument('--output-dir', default='svg_output', help='Output directory for SVG files')
    parser.add_argument('--camera-index', type=int, default=1, help='Camera index to extract (e.g., 1 for camera1)')
    parser.add_argument('--origin-feet', nargs=3, type=float, default=[67.472490761, -23.114793212, 151.586679018], 
                       help='Origin in feet (x y z)')
    parser.add_argument('--scale', type=float, default=1.65, help='Scale factor')
    
    args = parser.parse_args()
    
    sparse_dir = Path(args.sparse_dir)
    output_dir = Path(args.output_dir)
    
    if not sparse_dir.exists():
        print(f"Error: Sparse directory not found: {sparse_dir}")
        return 1
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine which folders to process
    if args.folders:
        folder_numbers = args.folders
    else:
        # Find all numbered folders
        folder_numbers = []
        for item in sparse_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                folder_numbers.append(int(item.name))
        folder_numbers.sort()
    
    if not folder_numbers:
        print("No reconstruction folders found")
        return 1
    
    print(f"Processing {len(folder_numbers)} reconstruction folders: {folder_numbers}")
    print(f"Output directory: {output_dir}")
    print(f"Camera index: {args.camera_index}")
    print(f"Origin: {args.origin_feet}")
    print(f"Scale: {args.scale}")
    
    # Process each folder
    success_count = 0
    for folder_num in folder_numbers:
        sparse_folder = sparse_dir / str(folder_num)
        
        try:
            success = process_single_reconstruction(
                sparse_folder, output_dir, 
                camera_index=args.camera_index,
                origin_feet=tuple(args.origin_feet),
                scale=args.scale
            )
            if success:
                success_count += 1
        except Exception as e:
            print(f"Error processing folder {folder_num}: {e}")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Completed: {success_count}/{len(folder_numbers)} folders processed successfully")
    print(f"SVG files saved to: {output_dir}")
    
    return 0 if success_count > 0 else 1

if __name__ == '__main__':
    exit(main())
