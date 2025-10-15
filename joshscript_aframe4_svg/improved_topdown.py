#!/usr/bin/env python3
"""
Improved top-down projection using PCA components and height peak detection.
"""

import argparse
import numpy as np
import pycolmap
from pathlib import Path
from datetime import datetime
from sklearn.decomposition import PCA
from scipy import stats

def find_height_peaks(camera_positions, num_peaks=2):
    """
    Find the most common height levels (peaks) in camera positions.
    
    Args:
        camera_positions: Nx3 array of camera positions
        num_peaks: Number of peaks to find (default: 2 for ground + first floor)
        
    Returns:
        peak_heights: Array of peak heights
        peak_counts: Number of cameras at each peak
    """
    z_coords = camera_positions[:, 2]
    
    # Use kernel density estimation to find peaks
    kde = stats.gaussian_kde(z_coords)
    z_range = np.linspace(z_coords.min(), z_coords.max(), 1000)
    density = kde(z_range)
    
    # Find peaks in the density
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(density, height=0.1, distance=50)
    
    if len(peaks) == 0:
        # Fallback: use simple histogram
        hist, bin_edges = np.histogram(z_coords, bins=20)
        peak_indices = np.argsort(hist)[-num_peaks:]
        peak_heights = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in peak_indices]
        peak_counts = hist[peak_indices]
    else:
        # Sort peaks by height (density)
        peak_densities = density[peaks]
        sorted_indices = np.argsort(peak_densities)[::-1]  # Descending order
        peak_heights = z_range[peaks[sorted_indices[:num_peaks]]]
        
        # Count cameras near each peak
        peak_counts = []
        for peak_height in peak_heights:
            # Find cameras within 0.5m of this peak
            distances = np.abs(z_coords - peak_height)
            count = np.sum(distances < 0.5)
            peak_counts.append(count)
    
    return np.array(peak_heights), np.array(peak_counts)

def estimate_gravity_from_cameras_improved(camera_positions):
    """
    Estimate gravity direction using the most populated height level.
    """
    print(f"Analyzing {len(camera_positions)} camera positions...")
    
    # Find height peaks
    peak_heights, peak_counts = find_height_peaks(camera_positions)
    
    print(f"Height peaks found:")
    for i, (height, count) in enumerate(zip(peak_heights, peak_counts)):
        print(f"  Peak {i+1}: Z={height:.3f}m, {count} cameras")
    
    # Use the peak with most cameras
    main_peak_idx = np.argmax(peak_counts)
    main_peak_height = peak_heights[main_peak_idx]
    main_peak_count = peak_counts[main_peak_idx]
    
    print(f"Using peak {main_peak_idx+1} (Z={main_peak_height:.3f}m) with {main_peak_count} cameras")
    
    # Filter cameras near the main peak
    z_coords = camera_positions[:, 2]
    peak_tolerance = 0.5  # 0.5m tolerance
    near_peak_mask = np.abs(z_coords - main_peak_height) < peak_tolerance
    peak_cameras = camera_positions[near_peak_mask]
    
    print(f"Using {len(peak_cameras)} cameras within {peak_tolerance}m of peak")
    
    if len(peak_cameras) < 3:
        print("Warning: Not enough cameras near peak, using all cameras")
        peak_cameras = camera_positions
    
    # Center the camera positions
    mean_pos = np.mean(peak_cameras, axis=0)
    centered = peak_cameras - mean_pos
    
    print(f"Mean position: ({mean_pos[0]:.3f}, {mean_pos[1]:.3f}, {mean_pos[2]:.3f})")
    
    # Apply PCA
    pca = PCA(n_components=3)
    pca.fit(centered)
    
    # Print variance explained by each component
    print(f"PCA variance explained:")
    print(f"  Component 1: {pca.explained_variance_[0]:.6f} (main movement direction)")
    print(f"  Component 2: {pca.explained_variance_[1]:.6f} (secondary movement)")
    print(f"  Component 3: {pca.explained_variance_[2]:.6f} (height variation - should be smallest)")
    
    # The component with smallest variance is perpendicular to the plane
    gravity_direction = pca.components_[2]
    
    print(f"Estimated gravity direction (raw): ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    
    # Make sure it points "up"
    if gravity_direction[2] < 0:
        gravity_direction = -gravity_direction
        print("Flipped gravity direction to point upward")
    
    print(f"Final gravity direction (up): ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    
    return gravity_direction, mean_pos, peak_cameras

def compute_gravity_alignment_rotation(gravity_direction, target_up=np.array([0, 0, 1])):
    """Compute rotation matrix to align estimated gravity with target up direction."""
    gravity_direction = gravity_direction / np.linalg.norm(gravity_direction)
    target_up = target_up / np.linalg.norm(target_up)
    
    print(f"Computing rotation to align:")
    print(f"  From: ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    print(f"  To:   ({target_up[0]:.6f}, {target_up[1]:.6f}, {target_up[2]:.6f})")
    
    axis = np.cross(gravity_direction, target_up)
    axis_length = np.linalg.norm(axis)
    
    if axis_length < 1e-10:
        print("Gravity already aligned with Z-up! Using identity rotation.")
        return np.eye(3)
    
    axis = axis / axis_length
    
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
    """Extract camera positions from COLMAP reconstruction."""
    camera_positions = []
    
    frame_cameras = {}
    for image_id, image in reconstruction.images.items():
        if hasattr(image, 'frame_id') and image.frame_id is not None:
            if image.frame_id not in frame_cameras:
                frame_cameras[image.frame_id] = []
            frame_cameras[image.frame_id].append(image)
    
    for frame_id in sorted(frame_cameras.keys()):
        images_in_frame = frame_cameras[frame_id]
        for image in images_in_frame:
            if f"camera{camera_index}" in image.name.lower():
                cam_from_world = image.cam_from_world()
                rot_mat = cam_from_world.rotation.matrix()
                cam_pos = -rot_mat.T @ cam_from_world.translation
                camera_positions.append(cam_pos)
                break
    
    return np.array(camera_positions)

def create_improved_top_down_svg(camera_positions, R, origin_m, scale, output_file):
    """
    Create an SVG using PCA components as 2D coordinates for better top-down view.
    """
    print("\nGenerating improved top-down SVG view...")
    
    # Transform camera positions
    transformed_positions = []
    for cam_pos in camera_positions:
        transformed_pos = origin_m + scale * (R @ cam_pos)
        transformed_positions.append(transformed_pos)
    
    transformed_positions = np.array(transformed_positions)
    
    # Use PCA components as 2D coordinates instead of X,Y projection
    mean_pos = np.mean(transformed_positions, axis=0)
    centered = transformed_positions - mean_pos
    
    # Apply PCA to get the actual movement plane
    pca = PCA(n_components=3)
    pca.fit(centered)
    
    # Use the first two PCA components as our 2D coordinates
    pca_coords = centered @ pca.components_[:2].T
    x_coords = pca_coords[:, 0]
    y_coords = -pca_coords[:, 1]  # Flip Y-axis to fix upside-down issue
    
    print(f"Using PCA components as 2D coordinates:")
    print(f"  Component 1 variance: {pca.explained_variance_[0]:.6f}")
    print(f"  Component 2 variance: {pca.explained_variance_[1]:.6f}")
    
    # Calculate bounds
    avg_x = np.mean(x_coords)
    avg_y = np.mean(y_coords)
    
    # Robust bounds calculation
    x_sorted = np.sort(x_coords)
    y_sorted = np.sort(y_coords)
    p10_idx = int(len(x_sorted) * 0.1)
    p90_idx = int(len(x_sorted) * 0.9)
    x_p10, x_p90 = x_sorted[p10_idx], x_sorted[p90_idx]
    y_p10, y_p90 = y_sorted[p10_idx], y_sorted[p90_idx]
    
    padding_factor = 1.3
    width = (x_p90 - x_p10) * padding_factor
    height = (y_p90 - y_p10) * padding_factor
    
    # Center coordinates
    x_coords_shifted = x_coords - avg_x
    y_coords_shifted = y_coords - avg_y
    
    viewbox_x = -width / 2
    viewbox_y = -height / 2
    
    print(f"  Average center: X={avg_x:.2f}, Y={avg_y:.2f}")
    print(f"  Robust bounds: {width:.2f} x {height:.2f}")
    print(f"  ViewBox: x={viewbox_x:.2f}, y={viewbox_y:.2f}, w={width:.2f}, h={height:.2f}")
    
    # Create SVG
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg viewBox="{viewbox_x:.3f} {viewbox_y:.3f} {width:.3f} {height:.3f}" ')
    svg_lines.append(f'     xmlns="http://www.w3.org/2000/svg">')
    svg_lines.append('  <!-- Improved top-down view using PCA components -->')
    svg_lines.append('  <!-- ViewBox is centered on median camera position -->')
    svg_lines.append(f'  <rect x="{viewbox_x}" y="{viewbox_y}" width="{width}" height="{height}" fill="white" opacity="0"/>')
    
    # Calculate circle radius
    circle_radius = width * 0.008
    stroke_width = circle_radius * 0.2
    
    # Draw camera positions
    for i, (x, y) in enumerate(zip(x_coords_shifted, y_coords_shifted)):
        svg_lines.append(f'  <circle cx="{x:.3f}" cy="{y:.3f}" r="{circle_radius:.4f}" ')
        svg_lines.append(f'          fill="red" stroke="darkred" stroke-width="{stroke_width:.4f}" ')
        svg_lines.append(f'          opacity="0.8">')
        svg_lines.append(f'    <title>Camera {i+1}: ({x:.2f}, {y:.2f})</title>')
        svg_lines.append(f'  </circle>')
    
    # Draw path connecting cameras
    path_points = [f"{x:.3f},{y:.3f}" for x, y in zip(x_coords_shifted, y_coords_shifted)]
    svg_lines.append(f'  <polyline points="{" ".join(path_points)}" ')
    svg_lines.append(f'            fill="none" stroke="red" stroke-width="{stroke_width * 2:.4f}" ')
    svg_lines.append(f'            opacity="0.4" />')
    
    # Add center marker
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

def process_single_reconstruction_improved(sparse_folder, output_dir, camera_index=1, 
                                         origin_feet=(67.472490761, -23.114793212, 151.586679018),
                                         scale=1.65):
    """Process a single reconstruction with improved top-down projection."""
    folder_name = sparse_folder.name
    print(f"\n{'='*70}")
    print(f"PROCESSING FOLDER: {folder_name} (IMPROVED)")
    print(f"{'='*70}")
    
    # Load reconstruction
    recon = pycolmap.Reconstruction(str(sparse_folder))
    print(f"Total images: {recon.num_images()}")
    
    # Extract camera positions
    camera_positions = extract_camera_positions(recon, camera_index=camera_index)
    print(f"Extracted {len(camera_positions)} camera positions")
    
    if len(camera_positions) < 3:
        print("Not enough camera positions. Skipping...")
        return False
    
    # Improved gravity estimation with height peaks
    gravity_direction, mean_pos, peak_cameras = estimate_gravity_from_cameras_improved(camera_positions)
    
    # Compute rotation
    R = compute_gravity_alignment_rotation(gravity_direction)
    
    # Convert origin to meters
    origin_m = np.array(origin_feet) * 0.3048
    
    # Generate SVG
    svg_file = output_dir / f'camera_positions_{folder_name}.svg'
    create_improved_top_down_svg(camera_positions, R, origin_m, scale, svg_file)
    
    print(f"Successfully processed folder {folder_name}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Process reconstructions with improved top-down projection')
    parser.add_argument('--sparse-dir', required=True, help='Path to sparse directory')
    parser.add_argument('--folders', nargs='+', type=int, default=None, help='Specific folder numbers')
    parser.add_argument('--output-dir', default='svg_output', help='Output directory')
    parser.add_argument('--camera-index', type=int, default=1, help='Camera index to extract')
    parser.add_argument('--origin-feet', nargs=3, type=float, default=[67.472490761, -23.114793212, 151.586679018], 
                       help='Origin in feet')
    parser.add_argument('--scale', type=float, default=1.65, help='Scale factor')
    
    args = parser.parse_args()
    
    sparse_dir = Path(args.sparse_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine folders to process
    if args.folders:
        folder_numbers = args.folders
    else:
        folder_numbers = []
        for item in sparse_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                folder_numbers.append(int(item.name))
        folder_numbers.sort()
    
    print(f"Processing {len(folder_numbers)} reconstruction folders: {folder_numbers}")
    print(f"Output directory: {output_dir}")
    
    # Process each folder
    success_count = 0
    for folder_num in folder_numbers:
        sparse_folder = sparse_dir / str(folder_num)
        try:
            success = process_single_reconstruction_improved(
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

if __name__ == '__main__':
    main()
