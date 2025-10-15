#!/usr/bin/env python3
"""
Generate SVG files from COLMAP sparse reconstruction folders
Reads binary format (cameras.bin, images.bin) from multiple sparse folders
"""

import struct
import numpy as np
from lxml import etree
import argparse
import os
from pathlib import Path

def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character="<"):
    """Read and unpack the next bytes from a binary file."""
    data = fid.read(num_bytes)
    return struct.unpack(endian_character + format_char_sequence, data)

def read_cameras_binary(path_to_model_file):
    """
    Read cameras.bin file
    Camera model IDs and their parameter counts:
    0: SIMPLE_PINHOLE (3 params: f, cx, cy)
    1: PINHOLE (4 params: fx, fy, cx, cy)
    2: SIMPLE_RADIAL (4 params: f, cx, cy, k)
    3: RADIAL (5 params: f, cx, cy, k1, k2)
    4: OPENCV (8 params: fx, fy, cx, cy, k1, k2, p1, p2)
    5: OPENCV_FISHEYE (8 params: fx, fy, cx, cy, k1, k2, k3, k4)
    6: FULL_OPENCV (12 params: fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6)
    7: FOV (5 params: fx, fy, cx, cy, omega)
    8: SIMPLE_RADIAL_FISHEYE (4 params: f, cx, cy, k)
    9: RADIAL_FISHEYE (5 params: f, cx, cy, k1, k2)
    10: THIN_PRISM_FISHEYE (12 params)
    """
    CAMERA_MODEL_NUM_PARAMS = {
        0: 3,  # SIMPLE_PINHOLE
        1: 4,  # PINHOLE
        2: 4,  # SIMPLE_RADIAL
        3: 5,  # RADIAL
        4: 8,  # OPENCV
        5: 8,  # OPENCV_FISHEYE
        6: 12, # FULL_OPENCV
        7: 5,  # FOV
        8: 4,  # SIMPLE_RADIAL_FISHEYE
        9: 5,  # RADIAL_FISHEYE
        10: 12 # THIN_PRISM_FISHEYE
    }
    
    cameras = {}
    with open(path_to_model_file, "rb") as fid:
        num_cameras = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_cameras):
            camera_properties = read_next_bytes(
                fid, num_bytes=24, format_char_sequence="iiQQ")
            camera_id = camera_properties[0]
            model_id = camera_properties[1]
            width = camera_properties[2]
            height = camera_properties[3]
            num_params = CAMERA_MODEL_NUM_PARAMS.get(model_id, 4)
            params = read_next_bytes(
                fid, num_bytes=8*num_params,
                format_char_sequence="d"*num_params)
            cameras[camera_id] = {
                'id': camera_id,
                'model': model_id,
                'width': width,
                'height': height,
                'params': params
            }
    return cameras

def read_images_binary(path_to_model_file):
    """
    Read images.bin file
    Returns: dictionary of images with their camera poses
    """
    images = {}
    with open(path_to_model_file, "rb") as fid:
        num_reg_images = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_reg_images):
            binary_image_properties = read_next_bytes(
                fid, num_bytes=64, format_char_sequence="idddddddi")
            image_id = binary_image_properties[0]
            qw = binary_image_properties[1]
            qx = binary_image_properties[2]
            qy = binary_image_properties[3]
            qz = binary_image_properties[4]
            tx = binary_image_properties[5]
            ty = binary_image_properties[6]
            tz = binary_image_properties[7]
            camera_id = binary_image_properties[8]
            
            # Read image name
            image_name = ""
            current_char = read_next_bytes(fid, 1, "c")[0]
            while current_char != b"\x00":
                image_name += current_char.decode("utf-8")
                current_char = read_next_bytes(fid, 1, "c")[0]
            
            # Read points2D
            num_points2D = read_next_bytes(fid, num_bytes=8, format_char_sequence="Q")[0]
            x_y_id_s = read_next_bytes(
                fid, num_bytes=24*num_points2D,
                format_char_sequence="ddq"*num_points2D)
            
            images[image_id] = {
                'id': image_id,
                'qw': qw, 'qx': qx, 'qy': qy, 'qz': qz,
                'tx': tx, 'ty': ty, 'tz': tz,
                'camera_id': camera_id,
                'name': image_name
            }
    return images

def quaternion_to_rotation_matrix(qw, qx, qy, qz):
    """Convert quaternion to rotation matrix"""
    # Normalize quaternion
    norm = np.sqrt(qw*qw + qx*qx + qy*qy + qz*qz)
    if norm == 0:
        return np.eye(3)
    qw, qx, qy, qz = qw/norm, qx/norm, qy/norm, qz/norm
    
    # Convert to rotation matrix
    R = np.array([
        [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx*qx + qy*qy)]
    ])
    
    return R

def camera_center_from_pose(qw, qx, qy, qz, tx, ty, tz):
    """
    Calculate camera center from quaternion and translation
    COLMAP uses: X_world = R * X_camera + t
    Camera center: C = -R^T * t
    """
    R = quaternion_to_rotation_matrix(qw, qx, qy, qz)
    t = np.array([tx, ty, tz])
    C = -R.T @ t
    return C

def create_camera_positions_svg(camera_data, output_path, svg_width=1000, svg_height=1000):
    """Create SVG file with camera positions in the same format as reference files"""
    
    if not camera_data:
        print("Warning: No camera data to create SVG")
        return
    
    # Calculate bounds for proper viewBox
    x_coords = [camera['x'] for camera in camera_data]
    y_coords = [camera['y'] for camera in camera_data]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    # Add margins (10% of range)
    range_x = max_x - min_x if max_x != min_x else 1
    range_y = max_y - min_y if max_y != min_y else 1
    margin_x = range_x * 0.1
    margin_y = range_y * 0.1
    
    view_x = min_x - margin_x
    view_y = min_y - margin_y
    view_width = range_x + 2 * margin_x
    view_height = range_y + 2 * margin_y
    
    # Create SVG root element with proper viewBox
    svg = etree.Element("svg", 
                       xmlns="http://www.w3.org/2000/svg",
                       viewBox=f"{view_x:.3f} {view_y:.3f} {view_width:.3f} {view_height:.3f}")
    
    # Add comment
    comment = etree.Comment("Top-down view of camera positions")
    svg.insert(0, comment)
    
    # Add background rect (invisible but defines bounds)
    bg_rect = etree.SubElement(svg, "rect",
                              x=f"{view_x:.3f}",
                              y=f"{view_y:.3f}",
                              width=f"{view_width:.3f}",
                              height=f"{view_height:.3f}",
                              fill="white",
                              opacity="0")
    
    # Create camera trajectory polyline
    if len(camera_data) > 1:
        # Sort by camera_id to ensure proper order
        sorted_cameras = sorted(camera_data, key=lambda x: x.get('camera_id', 0))
        
        # Create polyline points string
        points = []
        for camera in sorted_cameras:
            x, y = camera['x'], camera['y']
            points.append(f"{x:.3f},{y:.3f}")
        
        polyline_points = " ".join(points)
        
        # Add trajectory polyline
        polyline = etree.SubElement(svg, "polyline",
                                   points=polyline_points,
                                   fill="none",
                                   stroke="blue",
                                   stroke_width="0.1",
                                   opacity="0.6")
    
    # Add individual camera markers
    for i, camera in enumerate(camera_data):
        x, y = camera['x'], camera['y']
        camera_id = camera.get('camera_id', i)
        image_name = camera.get('name', f'cam_{i}')
        
        # Create camera circle (small red circles like reference)
        circle = etree.SubElement(svg, "circle",
                                cx=f"{x:.3f}",
                                cy=f"{y:.3f}",
                                r="0.0985",  # Same size as reference
                                fill="red",
                                stroke="darkred",
                                stroke_width="0.0197",
                                opacity="0.8")
        
        # Add title with coordinates for tooltip
        title = etree.SubElement(circle, "title")
        title.text = f"Camera {camera_id}: ({x:.2f}, {y:.2f})"
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(etree.tostring(svg, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

def process_sparse_reconstruction(sparse_folder, output_path):
    """Process a single sparse reconstruction folder and create SVG"""
    
    cameras_bin = os.path.join(sparse_folder, 'cameras.bin')
    images_bin = os.path.join(sparse_folder, 'images.bin')
    
    if not os.path.exists(cameras_bin) or not os.path.exists(images_bin):
        print(f"Error: Missing binary files in {sparse_folder}")
        return False
    
    print(f"Processing: {sparse_folder}")
    
    # Read camera and image data
    cameras = read_cameras_binary(cameras_bin)
    images = read_images_binary(images_bin)
    
    print(f"  Found {len(cameras)} cameras and {len(images)} images")
    
    if len(images) == 0:
        print(f"  Warning: No images found in reconstruction")
        return False
    
    # Extract camera positions
    positions = []
    for img_id, img in images.items():
        # Get camera center in world coordinates
        center = camera_center_from_pose(
            img['qw'], img['qx'], img['qy'], img['qz'],
            img['tx'], img['ty'], img['tz']
        )
        
        # Get camera orientation (viewing direction)
        R = quaternion_to_rotation_matrix(
            img['qw'], img['qx'], img['qy'], img['qz']
        )
        # Camera looks along negative Z in camera coordinates
        forward = R @ np.array([0, 0, -1])
        
        positions.append({
            'camera_id': img_id,
            'name': img['name'],
            'position': center,
            'forward': forward
        })
    
    # Use real-world coordinates directly (like reference files)
    camera_data = []
    for pos in positions:
        # Use actual world coordinates (X-Y plane)
        x = pos['position'][0]
        y = pos['position'][1]
        
        camera_data.append({
            'camera_id': pos['camera_id'],
            'name': pos['name'],
            'x': x,
            'y': y
        })
    
    # Create SVG
    create_camera_positions_svg(camera_data, output_path)
    
    print(f"  Created: {output_path} ({len(camera_data)} cameras)")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Generate SVG files from COLMAP sparse reconstruction folders'
    )
    parser.add_argument(
        '--sparse-dir', 
        required=True, 
        help='Path to sparse directory containing numbered folders (0, 1, 2, etc.)'
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Output directory for SVG files (default: current directory)'
    )
    parser.add_argument(
        '--folders',
        nargs='+',
        type=int,
        default=None,
        help='Specific folder numbers to process (e.g., 0 1 2 3). If not specified, processes all folders.'
    )
    
    args = parser.parse_args()
    
    sparse_dir = Path(args.sparse_dir)
    output_dir = Path(args.output_dir)
    
    if not sparse_dir.exists():
        print(f"Error: Sparse directory not found: {sparse_dir}")
        return 1
    
    # Create output directory if it doesn't exist
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
    print("-" * 60)
    
    # Process each folder
    success_count = 0
    for folder_num in folder_numbers:
        sparse_folder = sparse_dir / str(folder_num)
        output_file = output_dir / f"camera_positions_{folder_num}.svg"
        
        if process_sparse_reconstruction(str(sparse_folder), str(output_file)):
            success_count += 1
        print()
    
    print("-" * 60)
    print(f"Completed: {success_count}/{len(folder_numbers)} SVG files generated")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    exit(main())

