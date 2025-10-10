"""
Automatically detect gravity direction from camera positions and align reconstruction.

This script:
1. Loads COLMAP reconstruction
2. Extracts camera positions (assumes they lie on approximate plane)
3. Uses PCA to find the ground plane normal (gravity direction)
4. Computes rotation to align gravity with Z-up
5. Exports aligned DXF with camera poses only

No manual basis vectors needed - fully automatic!
"""

from pathlib import Path
from datetime import datetime
import numpy as np
import pycolmap
from sklearn.decomposition import PCA
from export_pointcloud import export_to_dxf_transformed


def estimate_gravity_from_cameras(camera_positions):
    """
    Estimate gravity direction from camera positions using PCA.
    Assumes cameras lie approximately on a plane (constant height).
    
    Args:
        camera_positions: Nx3 array of camera positions
        
    Returns:
        gravity_direction: normalized 3D vector pointing "up"
    """
    print(f"Analyzing {len(camera_positions)} camera positions...")
    
    # Center the camera positions
    mean_pos = np.mean(camera_positions, axis=0)
    centered = camera_positions - mean_pos
    
    print(f"Mean camera position: ({mean_pos[0]:.3f}, {mean_pos[1]:.3f}, {mean_pos[2]:.3f})")
    
    # Apply PCA
    pca = PCA(n_components=3)
    pca.fit(centered)
    
    # Print variance explained by each component
    print(f"\nPCA variance explained:")
    print(f"  Component 1: {pca.explained_variance_[0]:.6f} (main movement direction)")
    print(f"  Component 2: {pca.explained_variance_[1]:.6f} (secondary movement)")
    print(f"  Component 3: {pca.explained_variance_[2]:.6f} (height variation - should be smallest)")
    
    # The component with smallest variance is perpendicular to the plane
    # This is the gravity direction (up vector)
    gravity_direction = pca.components_[2]  # Last component = smallest variance
    
    print(f"\nEstimated gravity direction (raw): ({gravity_direction[0]:.6f}, {gravity_direction[1]:.6f}, {gravity_direction[2]:.6f})")
    
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
    
    print(f"\nComputing rotation to align:")
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
    Extract camera positions from COLMAP reconstruction.
    
    Args:
        reconstruction: pycolmap.Reconstruction object
        camera_index: Which camera to extract (default: 1)
        
    Returns:
        camera_positions: Nx3 array of camera positions
    """
    camera_positions = []
    
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
                
                camera_positions.append(cam_pos)
                break
    
    return np.array(camera_positions)


def rotation_matrix_to_basis_vectors(R):
    """
    Convert rotation matrix to basis vectors for compatibility with existing export functions.
    
    Args:
        R: 3x3 rotation matrix
        
    Returns:
        basis_x, basis_y, basis_z: tuple of basis vectors
    """
    basis_x = tuple(R[:, 0])
    basis_y = tuple(R[:, 1])
    basis_z = tuple(R[:, 2])
    
    return basis_x, basis_y, basis_z


def create_top_down_svg(camera_positions, R, origin_m, scale, output_file):
    """
    Create an SVG file showing top-down view of camera positions.
    ViewBox is centered on the median camera position for easy alignment.
    
    Args:
        camera_positions: Nx3 array of camera positions (original COLMAP coords)
        R: 3x3 rotation matrix
        origin_m: origin in meters (for transformation)
        scale: scale factor
        output_file: path to save SVG file
    """
    print("\nGenerating top-down SVG view of camera positions...")
    
    # Transform camera positions same way as DXF export
    transformed_positions = []
    for cam_pos in camera_positions:
        transformed_pos = origin_m + scale * (R @ cam_pos)
        transformed_positions.append(transformed_pos)
    
    transformed_positions = np.array(transformed_positions)
    
    # Extract X and Y coordinates (top-down view)
    x_coords = transformed_positions[:, 0]
    y_coords = transformed_positions[:, 1]
    
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
    
    # Draw camera positions as circles (shifted so median is at origin)
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


def main():
    print("="*70)
    print("AUTOMATIC GRAVITY ALIGNMENT FOR COLMAP RECONSTRUCTION")
    print("="*70)
    print()
    
    # Parameters
    origin_feet = (67.472490761, -23.114793212, 151.586679018)
    scale = 1.65
    marker_size = 0.02
    downsample_scale = 0.1  # Keep 1 in 10 points (0.1 = 10% of points)
    camera_index = 1
    
    # Paths
    recon_path = Path('reconstruction_single2/export/0')
    output_dir = Path('reconstruction_single2/exports')
    output_dir.mkdir(exist_ok=True)
    
    # Load reconstruction
    print("Loading COLMAP reconstruction...")
    recon = pycolmap.Reconstruction(str(recon_path))
    print(f"  Total images: {recon.num_images()}")
    print(f"  Total 3D points: {recon.num_points3D()}")
    print()
    
    # Extract camera positions
    print(f"Extracting camera{camera_index} positions from each frame...")
    camera_positions = extract_camera_positions(recon, camera_index=camera_index)
    print(f"  Extracted {len(camera_positions)} camera positions")
    print()
    
    # Estimate gravity direction using PCA
    print("="*70)
    print("STEP 1: ESTIMATE GRAVITY DIRECTION FROM CAMERA PLANE")
    print("="*70)
    gravity_direction, mean_camera_pos = estimate_gravity_from_cameras(camera_positions)
    print()
    
    # Compute rotation to align with Z-up
    print("="*70)
    print("STEP 2: COMPUTE ROTATION TO ALIGN WITH Z-UP")
    print("="*70)
    R = compute_gravity_alignment_rotation(gravity_direction)
    print()
    
    # Convert rotation matrix to basis vectors
    basis_x, basis_y, basis_z = rotation_matrix_to_basis_vectors(R)
    
    # Convert origin to meters for transformations
    origin_m = np.array(origin_feet) * 0.3048
    
    print("="*70)
    print("STEP 3: EXPORT ALIGNED DXF (3D POINTS + CAMERA POSES)")
    print("="*70)
    print(f"Basis vectors derived from automatic gravity detection:")
    print(f"  basis_x = ({basis_x[0]:.9f}, {basis_x[1]:.9f}, {basis_x[2]:.9f})")
    print(f"  basis_y = ({basis_y[0]:.9f}, {basis_y[1]:.9f}, {basis_y[2]:.9f})")
    print(f"  basis_z = ({basis_z[0]:.9f}, {basis_z[1]:.9f}, {basis_z[2]:.9f})")
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = output_dir / f'auto_gravity_{timestamp}'
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f'pointcloud_gravity_aligned_{timestamp}.dxf'
    
    # Export 3D points + cameras
    export_to_dxf_transformed(
        recon, out_file, marker_size=marker_size, scale=scale,
        origin_feet=origin_feet, basis_x=basis_x, basis_y=basis_y, basis_z=basis_z,
        downsample_factor=int(1/downsample_scale),  # Convert 0.1 to 10
        include_camera_poses=True,  # Include camera positions as directional shapes
        camera_index=camera_index
    )
    
    # Generate top-down SVG view
    svg_file = out_dir / f'camera_positions_topdown_{timestamp}.svg'
    create_top_down_svg(camera_positions, R, origin_m, scale, svg_file)
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"[OK] Automatically detected gravity from {len(camera_positions)} camera positions")
    print(f"[OK] Aligned coordinate system to Z-up")
    print(f"[OK] Exported 3D points + cameras DXF to: {out_file}")
    print(f"[OK] Exported top-down SVG view to: {svg_file}")
    print()
    print("="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Open the DXF in your CAD software (AutoCAD, etc.)")
    print("2. Verify cameras are now gravity-aligned (Z points up)")
    print("3. If alignment looks good, proceed to generate JSON for A-Frame:")
    print()
    print("   python export_cameras_to_json.py")
    print()
    print("   (Note: You'll need to update export_cameras_to_json.py with the")
    print("    auto-detected basis vectors if you want matching alignment)")
    print("="*70)


if __name__ == '__main__':
    main()

