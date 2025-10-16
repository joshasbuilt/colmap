#!/usr/bin/env python3
"""
Test script to generate SVG and point cloud from COLMAP database
"""

import pycolmap
import numpy as np
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
    """
    # Convert to numpy array
    positions = np.array(camera_positions)
    
    # Center the data
    mean_pos = np.mean(positions, axis=0)
    centered = positions - mean_pos
    
    # Apply PCA
    pca = PCA(n_components=3)
    pca.fit(centered)
    
    # The normal to the plane is the last principal component (smallest variance)
    gravity_direction = pca.components_[2]
    
    # Ensure it points upward (positive Z)
    if gravity_direction[2] < 0:
        gravity_direction = -gravity_direction
    
    return gravity_direction, mean_pos

def compute_gravity_alignment_rotation(gravity_direction, target_up=np.array([0, 0, 1])):
    """
    Compute rotation matrix to align estimated gravity with target up direction (Z-up).
    """
    # Normalize both vectors
    gravity_direction = gravity_direction / np.linalg.norm(gravity_direction)
    target_up = target_up / np.linalg.norm(target_up)
    
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
    
    R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * np.dot(K, K)
    
    return R

def main():
    # Load COLMAP reconstruction from existing sparse reconstruction
    sparse_path = "../joshscripts/Camera01/reconstruction_single/sparse/0"
    print(f"Loading COLMAP reconstruction from: {sparse_path}")
    
    # Load reconstruction
    recon = pycolmap.Reconstruction(sparse_path)
    print(f"  Total images: {recon.num_images()}")
    print(f"  Total cameras: {recon.num_cameras()}")
    print(f"  Total 3D points: {recon.num_points3D()}")
    
    # Extract camera positions
    camera_data = []
    for image_id, image in recon.images.items():
        # Get camera position
        cam_from_world = image.cam_from_world()
        rot_mat = cam_from_world.rotation.matrix()
        cam_pos = -rot_mat.T @ cam_from_world.translation
        
        camera_info = {
            'position_3d': cam_pos,
            'image_name': image.name,
            'image_id': image_id,
            'camera_id': image.camera_id,
            'rotation_matrix': rot_mat,
            'translation': cam_from_world.translation,
            'quaternion': cam_from_world.rotation.quat,
            'height': cam_pos[2]
        }
        camera_data.append(camera_info)
    
    print(f"  Extracted {len(camera_data)} camera positions")
    
    # Get camera positions for gravity estimation
    camera_positions = [cam['position_3d'] for cam in camera_data]
    
    # Estimate gravity direction
    print("\nEstimating gravity direction...")
    gravity_direction, mean_pos = estimate_gravity_from_cameras(camera_positions)
    print(f"Estimated gravity direction: ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    print(f"Mean position: ({mean_pos[0]:.6f}, {mean_pos[1]:.6f}, {mean_pos[2]:.6f})")
    
    # Compute rotation matrix
    print("\nComputing gravity alignment rotation...")
    R = compute_gravity_alignment_rotation(gravity_direction)
    
    # Apply gravity correction to all camera positions
    print("\nApplying gravity correction...")
    for i, cam_data in enumerate(camera_data):
        # Apply rotation to get oriented position
        oriented_pos = R @ cam_data['position_3d']
        camera_data[i]['position_3d_oriented'] = oriented_pos
        
        if i < 5:  # Show first 5 for debugging
            print(f"  Camera {i+1}: {cam_data['position_3d']} -> {oriented_pos}")
    
    # Export point cloud
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pts_file = f"camera_positions_{timestamp}.pts"
    
    print(f"\nExporting point cloud...")
    export_point_cloud(camera_data, pts_file)
    
    # Show height analysis
    heights = [cam['position_3d_oriented'][2] for cam in camera_data]
    print(f"\nHeight analysis:")
    print(f"  Min Z: {min(heights):.3f}m")
    print(f"  Max Z: {max(heights):.3f}m")
    print(f"  Range: {max(heights) - min(heights):.3f}m")
    print(f"  Average: {sum(heights)/len(heights):.3f}m")
    
    print(f"\n✅ Point cloud exported to: {pts_file}")

if __name__ == "__main__":
    main()
