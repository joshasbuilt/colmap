#!/usr/bin/env python3
"""
Generate SVG and point cloud from COLMAP reconstruction with gravity correction
"""

import pycolmap
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.decomposition import PCA

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
    from sklearn.cluster import KMeans
    
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
    
    return gravity_direction, mean_pos_all

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
    # Get 2D coordinates (X, Y from oriented positions)
    x_coords = [cam['position_3d_oriented'][0] for cam in camera_data]
    y_coords = [cam['position_3d_oriented'][1] for cam in camera_data]
    
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
    
    # Draw camera positions
    for i, (x, y) in enumerate(zip(x_coords_shifted, y_coords_shifted)):
        cam_data = camera_data[i]
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
    
    # Draw path
    path_points = [f"{x:.3f},{y:.3f}" for x, y in zip(x_coords_shifted, y_coords_shifted)]
    svg_lines.append(f'  <polyline points="{" ".join(path_points)}" ')
    svg_lines.append(f'            fill="none" stroke="red" stroke-width="{stroke_width * 2:.4f}" ')
    svg_lines.append(f'            opacity="0.4" />')
    
    svg_lines.append('</svg>')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))
    
    print(f"Generated SVG with {len(camera_data)} camera positions")
    print(f"  ViewBox: {viewbox_x:.3f} {viewbox_y:.3f} {width:.3f} {height:.3f}")

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
    
    # Apply gravity correction using camera positions
    print("\nEstimating gravity from camera positions...")
    camera_positions = [cam['position_3d'] for cam in camera_data]
    gravity_direction, mean_pos = estimate_gravity_from_cameras(camera_positions)
    R = compute_gravity_alignment_rotation(gravity_direction)
    
    print(f"  Gravity direction: ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    print(f"  Rotation angle: {np.degrees(np.arccos(np.clip(np.dot(gravity_direction, [0,0,1]), -1, 1))):.2f}°")
    
    # Apply rotation to get oriented positions
    print(f"\nApplying rotation to {len(camera_data)} camera positions...")
    
    # Find optimal X-axis rotation to align building floors horizontally
    print(f"Finding optimal X-axis rotation to align building floors horizontally...")
    
    # First apply gravity alignment
    temp_positions = []
    for cam_data in camera_data:
        temp_pos = R @ cam_data['position_3d']
        temp_positions.append(temp_pos)
    temp_positions = np.array(temp_positions)
    
    # Now find the best X-axis rotation to align building floors horizontally
    # Simple X-axis rotation (around X-axis) - no flattening, just find the angle
    best_angle_x = 0
    best_variance = float('inf')
    
    # Test X-axis rotation angles (every 0.5 degrees for higher precision)
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
        
        # Calculate Z-variance (minimize to make floors horizontal)
        z_variance = np.var(rotated[:, 2])
        
        if z_variance < best_variance:
            best_variance = z_variance
            best_angle_x = angle_x_deg
    
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
    
    print(f"Sample transformations (first 5 cameras):")
    for i, cam_data in enumerate(camera_data):
        oriented_pos = R_combined @ cam_data['position_3d']
        camera_data[i]['position_3d_oriented'] = oriented_pos
        
        # Show first 5 transformations
        if i < 5:
            orig = cam_data['position_3d']
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
