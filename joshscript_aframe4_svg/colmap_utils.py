#!/usr/bin/env python3
"""
Shared utilities for COLMAP reconstruction processing
"""

import pycolmap
import numpy as np
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.linear_model import RANSACRegressor

def export_point_cloud(camera_data, output_file):
    """Export camera positions as point cloud in PTS format."""
    with open(output_file, 'w') as f:
        f.write(f"{len(camera_data)}\n")
        for cam_data in camera_data:
            pos = cam_data['position_3d_oriented']
            x, y, z = pos[0], pos[1], pos[2]
            # Use white color (255, 255, 255) for better visibility in ReCap
            f.write(f"{x:.6f} {y:.6f} {z:.6f} 255 255 255 255\n")
    print(f"Exported {len(camera_data)} camera positions to {output_file}")

def export_full_point_cloud(recon, R, output_file, downsample=10):
    """
    Export the full 3D point cloud with gravity correction applied.
    downsample: Keep 1 in N points (e.g., 10 = keep 10% of points)
    """
    # First pass: count points to export
    point_count = (recon.num_points3D() + downsample - 1) // downsample
    
    with open(output_file, 'w') as f:
        f.write(f"{point_count}\n")
        
        # Export points with gravity correction
        point_idx = 0
        exported = 0
        for point_id, point in recon.points3D.items():
            if point_idx % downsample == 0:
                # Apply gravity correction rotation
                oriented_pos = R @ point.xyz
                x, y, z = oriented_pos[0], oriented_pos[1], oriented_pos[2]
                r, g, b = point.color[0], point.color[1], point.color[2]
                intensity = int((int(r) + int(g) + int(b)) / 3.0)
                f.write(f"{x:.6f} {y:.6f} {z:.6f} {r} {g} {b} {intensity}\n")
                exported += 1
            point_idx += 1
    
    print(f"Exported {exported} 3D points (downsampled from {recon.num_points3D()}) to {output_file}")

def estimate_gravity_from_cameras(camera_positions):
    """
    Find the floor plane by clustering cameras into floors, then using PCA on the largest cluster.
    This handles cases where observer goes upstairs (two separate floor planes).
    """
    positions = np.array(camera_positions)
    
    # Try to separate into 2 clusters (ground floor vs upstairs)
    print(f"  Clustering {len(positions)} cameras into floor groups...")
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = kmeans.fit_predict(positions)
    
    # Find the larger cluster
    cluster_0_size = np.sum(labels == 0)
    cluster_1_size = np.sum(labels == 1)
    
    print(f"  Cluster 0: {cluster_0_size} cameras")
    print(f"  Cluster 1: {cluster_1_size} cameras")
    
    # Use the larger cluster (main floor)
    main_cluster_label = 0 if cluster_0_size > cluster_1_size else 1
    main_cluster_positions = positions[labels == main_cluster_label]
    
    print(f"  Using cluster {main_cluster_label} ({len(main_cluster_positions)} cameras) for gravity estimation")
    
    # Now apply PCA to just the main cluster
    mean_pos = np.mean(main_cluster_positions, axis=0)
    centered = main_cluster_positions - mean_pos
    
    # Compute covariance matrix
    cov_matrix = np.cov(centered.T)
    
    # Get eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    
    # Sort by eigenvalue (smallest to largest)
    idx = eigenvalues.argsort()
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    print(f"  PCA on main cluster - eigenvalues:")
    print(f"    Smallest (up direction): {eigenvalues[0]:.6f}")
    print(f"    Middle: {eigenvalues[1]:.6f}")
    print(f"    Largest (main movement): {eigenvalues[2]:.6f}")
    
    # The eigenvector with smallest eigenvalue is the "up" direction
    gravity_direction = eigenvectors[:, 0]
    
    print(f"  Gravity direction: ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    
    # Ensure it points upward (positive Z component)
    if gravity_direction[2] < 0:
        gravity_direction = -gravity_direction
        print(f"  Flipped to point upward")
    
    # Return mean of ALL positions, not just main cluster
    mean_pos_all = np.mean(positions, axis=0)
    
    return gravity_direction, mean_pos_all, labels

def compute_gravity_alignment_rotation(gravity_direction, target_up=np.array([0, 0, 1])):
    """Compute rotation matrix to align estimated gravity with target up direction."""
    gravity_direction = gravity_direction / np.linalg.norm(gravity_direction)
    target_up = target_up / np.linalg.norm(target_up)
    
    axis = np.cross(gravity_direction, target_up)
    axis_length = np.linalg.norm(axis)
    
    if axis_length < 1e-10:
        return np.eye(3)
    
    axis = axis / axis_length
    dot_product = np.clip(np.dot(gravity_direction, target_up), -1.0, 1.0)
    angle = np.arccos(dot_product)
    
    K = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])
    
    R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * np.dot(K, K)
    return R

def generate_svg(camera_data, output_file):
    """Generate SVG from camera data."""
    # Sort camera data by image name to ensure chronological order
    camera_data_sorted = sorted(camera_data, key=lambda x: x['image_name'])
    
    # Remove duplicate positions (same X,Y coordinates) to prevent loops
    unique_positions = []
    seen_positions = set()
    
    for cam_data in camera_data_sorted:
        pos = cam_data['position_3d_oriented']
        pos_key = (round(pos[0], 3), round(pos[1], 3))  # Round to avoid floating point precision issues
        
        if pos_key not in seen_positions:
            unique_positions.append(cam_data)
            seen_positions.add(pos_key)
    
    print(f"  Removed {len(camera_data_sorted) - len(unique_positions)} duplicate positions")
    
    # Get 2D coordinates (X, Y from oriented positions) in chronological order
    x_coords = [cam['position_3d_oriented'][0] for cam in unique_positions]
    y_coords = [cam['position_3d_oriented'][1] for cam in unique_positions]
    
    # Calculate bounds
    avg_x = np.mean(x_coords)
    avg_y = np.mean(y_coords)
    
    x_sorted = np.sort(x_coords)
    y_sorted = np.sort(y_coords)
    p10_idx = int(len(x_sorted) * 0.1)
    p90_idx = int(len(x_sorted) * 0.9)
    x_p10, x_p90 = x_sorted[p10_idx], x_sorted[p90_idx]
    y_p10, y_p90 = y_sorted[p10_idx], y_sorted[p90_idx]
    
    padding_factor = 1.3
    width = (x_p90 - x_p10) * padding_factor
    height = (y_p90 - y_p10) * padding_factor
    
    # Shift coordinates so average becomes origin
    x_coords_shifted = np.array(x_coords) - avg_x
    y_coords_shifted = np.array(y_coords) - avg_y
    
    viewbox_x = -width / 2
    viewbox_y = -height / 2
    
    # Create SVG
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg viewBox="{viewbox_x:.3f} {viewbox_y:.3f} {width:.3f} {height:.3f}" ')
    svg_lines.append(f'     xmlns="http://www.w3.org/2000/svg">')
    svg_lines.append('  <!-- Gravity-corrected camera positions -->')
    
    circle_radius = width * 0.008
    stroke_width = circle_radius * 0.2
    
    # Draw camera positions in chronological order
    for i, (x, y) in enumerate(zip(x_coords_shifted, y_coords_shifted)):
        cam_data = unique_positions[i]
        pos = cam_data['position_3d_oriented']
        
        tooltip_parts = [
            f"Camera {i+1}",
            f"2D: ({x:.2f}, {y:.2f})",
            f"3D: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})",
            f"Image: {cam_data['image_name']}",
            f"Frame: {cam_data.get('frame_id', 'unknown')}",
            f"Height: {pos[2]:.2f}m"
        ]
        
        tooltip_text = " | ".join(tooltip_parts)
        
        svg_lines.append(f'  <circle cx="{x:.3f}" cy="{y:.3f}" r="{circle_radius:.4f}" ')
        svg_lines.append(f'          fill="red" stroke="darkred" stroke-width="{stroke_width:.4f}" ')
        svg_lines.append(f'          opacity="0.8">')
        svg_lines.append(f'    <title>{tooltip_text}</title>')
        svg_lines.append(f'  </circle>')
    
    # Draw path connecting consecutive points only (no closed loop)
    print(f"  Drawing {len(x_coords_shifted) - 1} line segments for trajectory")
    for i in range(len(x_coords_shifted) - 1):
        x1, y1 = x_coords_shifted[i], y_coords_shifted[i]
        x2, y2 = x_coords_shifted[i + 1], y_coords_shifted[i + 1]
        svg_lines.append(f'  <line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" ')
        svg_lines.append(f'        stroke="red" stroke-width="{stroke_width * 2:.4f}" ')
        svg_lines.append(f'        opacity="0.4" />')
    
    # Debug: Show first and last few positions
    print(f"  First 3 positions: {[(x_coords_shifted[i], y_coords_shifted[i]) for i in range(min(3, len(x_coords_shifted)))]}")
    print(f"  Last 3 positions: {[(x_coords_shifted[i], y_coords_shifted[i]) for i in range(max(0, len(x_coords_shifted)-3), len(x_coords_shifted))]}")
    
    svg_lines.append('</svg>')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))
    
    print(f"Generated SVG with {len(camera_data)} camera positions")
    print(f"  ViewBox: {viewbox_x:.3f} {viewbox_y:.3f} {width:.3f} {height:.3f}")

def find_optimal_x_rotation(temp_positions, labels):
    """
    Find the optimal X-axis rotation to align building floors horizontally.
    Returns the best rotation angle in degrees.
    """
    best_angle_x = 0
    best_variance = float('inf')
    
    # Test X-axis rotation angles (every 0.5 degrees, full range)
    for angle_x_deg in np.arange(-90, 91, 0.5):
        angle_x_rad = np.radians(angle_x_deg)
        
        # X-axis rotation matrix (rotation around X-axis)
        R_x_test = np.array([
            [1, 0, 0],
            [0, np.cos(angle_x_rad), -np.sin(angle_x_rad)],
            [0, np.sin(angle_x_rad), np.cos(angle_x_rad)]
        ])
        
        # Apply test rotation to full 3D points
        rotated = temp_positions @ R_x_test.T
        
        # CORRECT METHOD: Find parallel lines in Y-Z plane
        # Disregard X, treat Y as X and Z as Y for 2D analysis
        yz_points = rotated[:, [1, 2]]  # Only Y and Z coordinates
        
        # Use the SAME clustering as first pass (don't re-cluster)
        # Just analyze the Y-Z coordinates of the existing clusters
        cluster_0_yz = yz_points[labels == 0]  # Ground floor Y-Z points
        cluster_1_yz = yz_points[labels == 1]  # Upstairs Y-Z points
        
        # Check if both clusters have enough points
        if len(cluster_0_yz) < 50 or len(cluster_1_yz) < 50:
            continue
            
        # Use RANSAC to find the best horizontal lines
        if len(cluster_0_yz) > 50 and len(cluster_1_yz) > 50:
            # Fit horizontal lines using RANSAC
            ransac_0 = RANSACRegressor(random_state=42)
            ransac_0.fit(cluster_0_yz[:, 0:1], cluster_0_yz[:, 1])
            slope_0 = ransac_0.estimator_.coef_[0]
            
            ransac_1 = RANSACRegressor(random_state=42)
            ransac_1.fit(cluster_1_yz[:, 0:1], cluster_1_yz[:, 1])
            slope_1 = ransac_1.estimator_.coef_[0]
            
            # Both lines should be horizontal (slope ≈ 0)
            horizontal_penalty = abs(slope_0) + abs(slope_1)
            
            # Lines should be parallel (similar slopes)
            parallel_penalty = abs(slope_0 - slope_1)
            
            total_z_variance = horizontal_penalty + parallel_penalty
        else:
            total_z_variance = float('inf')
        
        if total_z_variance < best_variance:
            best_variance = total_z_variance
            best_angle_x = angle_x_deg
    
    return best_angle_x, best_variance

def process_camera_data(camera_data, debug_output=True):
    """
    Process camera data with gravity correction and optimal X-axis rotation.
    Returns the combined rotation matrix and updated camera data.
    """
    if len(camera_data) < 3:
        print(f"  WARNING: Not enough camera positions ({len(camera_data)}) for gravity estimation")
        return None, camera_data
    
    # Apply gravity correction using camera positions
    print("  Estimating gravity from camera positions...")
    camera_positions = [cam['position_3d'] for cam in camera_data]
    gravity_direction, mean_pos, labels = estimate_gravity_from_cameras(camera_positions)
    R = compute_gravity_alignment_rotation(gravity_direction)
    
    print(f"  Gravity direction: ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    print(f"  Rotation angle: {np.degrees(np.arccos(np.clip(np.dot(gravity_direction, [0,0,1]), -1, 1))):.2f}°")
    
    # Apply rotation to get oriented positions
    print(f"  Applying rotation to {len(camera_data)} camera positions...")
    
    # Find optimal X-axis rotation to align building floors horizontally
    print(f"  Finding optimal X-axis rotation to align building floors horizontally...")
    
    # First apply gravity alignment
    temp_positions = []
    for cam_data in camera_data:
        temp_pos = R @ cam_data['position_3d']
        temp_positions.append(temp_pos)
    temp_positions = np.array(temp_positions)
    
    # Find optimal X-axis rotation
    best_angle_x, best_variance = find_optimal_x_rotation(temp_positions, labels)
    
    print(f"  Best X-axis rotation: {best_angle_x}° (Z-variance: {best_variance:.6f})")
    
    # Apply the optimal X-axis rotation
    angle_x = np.radians(best_angle_x)
    R_x_optimal = np.array([
        [1, 0, 0],
        [0, np.cos(angle_x), -np.sin(angle_x)],
        [0, np.sin(angle_x), np.cos(angle_x)]
    ])
    
    # Combined rotation: gravity alignment + optimal X-axis rotation
    R_combined = R_x_optimal @ R
    
    if debug_output:
        print(f"  DEBUG: Second pass rotation matrix:")
        print(f"    R_x_optimal = {R_x_optimal}")
        print(f"    Angle applied: {best_angle_x}°")
        print(f"  DEBUG: Testing if second pass is working...")
        
        # Test a few points to see the difference
        test_cam = camera_data[0]
        before_second = R @ test_cam['position_3d']
        after_second = R_combined @ test_cam['position_3d']
        print(f"    Test camera before second pass: ({before_second[0]:.3f}, {before_second[1]:.3f}, {before_second[2]:.3f})")
        print(f"    Test camera after second pass:  ({after_second[0]:.3f}, {after_second[1]:.3f}, {after_second[2]:.3f})")
        print(f"    Z difference: {after_second[2] - before_second[2]:.6f}")
    
    # Apply combined rotation to all camera positions
    for i, cam_data in enumerate(camera_data):
        oriented_pos = R_combined @ cam_data['position_3d']
        camera_data[i]['position_3d_oriented'] = oriented_pos
    
    return R_combined, camera_data
