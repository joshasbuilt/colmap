#!/usr/bin/env python3
"""
Bake full 3D rotation (yaw, pitch, roll) into 360° equirectangular panorama images.

This script:
1. Reads cone_data.json with forward/up vectors
2. Converts orientation to Euler angles (matching A-Frame logic)
3. Applies full 3D rotation to equirectangular images via spherical remapping
4. Saves processed images to panoramas/processed/
5. Outputs cone_data_processed.json with identity rotations

For equirectangular images, we handle rotation by:
- Converting each output pixel's lon/lat to a 3D direction vector
- Rotating that vector by the inverse rotation
- Converting back to lon/lat to sample from the source image
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation as R

# Default JPEG quality
JPEG_QUALITY = 85


def load_json(path: Path) -> Dict:
    """Load JSON file."""
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Dict, dry_run: bool = False):
    """Save JSON file with pretty printing."""
    if dry_run:
        print(f"[dry-run] Would write JSON: {path}")
        return
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved JSON: {path}")


def dxf_to_aframe_coords(vec: Dict[str, float]) -> np.ndarray:
    """
    Convert DXF (Z-up) coordinates to A-Frame (Y-up) coordinates.
    DXF(x,y,z) -> A-Frame(x, z, -y)
    """
    return np.array([vec['x'], vec['z'], -vec['y']])


def vectors_to_euler_angles(forward: Dict, up: Dict) -> Tuple[float, float, float]:
    """
    Convert forward/up vectors to Euler angles (yaw, pitch, roll) in degrees.
    
    This matches the A-Frame navigation-system.js logic exactly:
    1. Convert DXF coords to A-Frame coords
    2. Build orthonormal basis (right, correctedUp, -forward)
    3. Construct rotation matrix
    4. Extract Euler angles in YXZ order
    
    Returns:
        (yaw, pitch, roll) in degrees
    """
    # Convert to A-Frame coordinates
    fwd_vec = dxf_to_aframe_coords(forward)
    up_vec = dxf_to_aframe_coords(up)
    
    # Normalize
    fwd_vec = fwd_vec / np.linalg.norm(fwd_vec)
    up_vec = up_vec / np.linalg.norm(up_vec)
    
    # Build orthonormal basis
    # right = up × forward
    right = np.cross(up_vec, fwd_vec)
    right = right / np.linalg.norm(right)
    
    # correctedUp = forward × right
    corrected_up = np.cross(fwd_vec, right)
    corrected_up = corrected_up / np.linalg.norm(corrected_up)
    
    # Build rotation matrix: columns are [right, correctedUp, -forward]
    # (camera looks down -Z in THREE.js/A-Frame)
    rot_matrix = np.column_stack([right, corrected_up, -fwd_vec])
    
    # Convert to scipy Rotation object and extract Euler angles
    # Using 'YXZ' order to match THREE.js
    scipy_rot = R.from_matrix(rot_matrix)
    
    # Extract Euler angles in YXZ order (intrinsic rotations)
    # scipy uses lowercase 'yxz' for intrinsic rotations
    euler_rad = scipy_rot.as_euler('YXZ', degrees=False)
    
    # Convert to degrees
    yaw = np.degrees(euler_rad[0])
    pitch = np.degrees(euler_rad[1])
    roll = -np.degrees(euler_rad[2])  # Negate roll to match A-Frame logic
    
    return yaw, pitch, roll


def lonlat_to_direction(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """
    Convert longitude/latitude to 3D direction vector.
    
    For equirectangular images:
    - longitude (lon) ∈ [-π, π]: horizontal position (0 = forward, π/2 = right)
    - latitude (lat) ∈ [-π/2, π/2]: vertical position (0 = horizon, π/2 = up)
    
    Returns:
        Array of shape (..., 3) with unit direction vectors
    """
    x = np.cos(lat) * np.sin(lon)
    y = np.sin(lat)
    z = np.cos(lat) * np.cos(lon)
    
    return np.stack([x, y, z], axis=-1)


def direction_to_lonlat(directions: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert 3D direction vectors to longitude/latitude.
    
    Args:
        directions: Array of shape (..., 3) with unit direction vectors
        
    Returns:
        (lon, lat) in radians
    """
    x, y, z = directions[..., 0], directions[..., 1], directions[..., 2]
    
    lon = np.arctan2(x, z)
    lat = np.arcsin(np.clip(y, -1, 1))
    
    return lon, lat


def apply_equirectangular_rotation(
    img: np.ndarray,
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float
) -> np.ndarray:
    """
    Apply full 3D rotation to an equirectangular panorama image.
    
    Process:
    1. For each output pixel, compute its lon/lat
    2. Convert lon/lat to 3D direction vector
    3. Apply inverse rotation to the direction
    4. Convert back to lon/lat to find source pixel
    5. Sample from source image with bilinear interpolation
    
    Args:
        img: Input image array (H, W, 3)
        yaw_deg: Yaw rotation in degrees (left/right)
        pitch_deg: Pitch rotation in degrees (up/down)
        roll_deg: Roll rotation in degrees (tilt)
        
    Returns:
        Rotated image array (H, W, 3)
    """
    height, width = img.shape[0], img.shape[1]
    
    # Create rotation object
    # We need INVERSE rotation because we're doing inverse mapping
    # (finding where each output pixel should sample from in the input)
    rot = R.from_euler('YXZ', [yaw_deg, pitch_deg, -roll_deg], degrees=True)
    rot_inverse = rot.inv()
    
    # Create output pixel grid
    # lon ∈ [-π, π], lat ∈ [-π/2, π/2]
    i_coords = np.arange(height)
    j_coords = np.arange(width)
    j_grid, i_grid = np.meshgrid(j_coords, i_coords)
    
    # Convert pixel coordinates to lon/lat
    lon_out = (j_grid / width) * 2 * np.pi - np.pi  # [0, width] -> [-π, π]
    lat_out = (0.5 - i_grid / height) * np.pi  # [0, height] -> [π/2, -π/2]
    
    # Convert to 3D direction vectors
    directions_out = lonlat_to_direction(lon_out, lat_out)
    
    # Apply inverse rotation
    directions_rotated = rot_inverse.apply(directions_out.reshape(-1, 3))
    directions_rotated = directions_rotated.reshape(height, width, 3)
    
    # Convert back to lon/lat for source sampling
    lon_src, lat_src = direction_to_lonlat(directions_rotated)
    
    # Convert lon/lat back to pixel coordinates
    j_src = (lon_src + np.pi) / (2 * np.pi) * width  # [-π, π] -> [0, width]
    i_src = (0.5 - lat_src / np.pi) * height  # [π/2, -π/2] -> [0, height]
    
    # Wrap longitude (handles seam properly)
    j_src = j_src % width
    
    # Clip latitude (poles)
    i_src = np.clip(i_src, 0, height - 1)
    
    # Bilinear interpolation
    output = np.zeros_like(img)
    
    # Get integer and fractional parts
    j0 = np.floor(j_src).astype(int) % width
    j1 = (j0 + 1) % width
    i0 = np.floor(i_src).astype(int)
    i1 = np.minimum(i0 + 1, height - 1)
    
    frac_j = j_src - np.floor(j_src)
    frac_i = i_src - np.floor(i_src)
    
    # Perform bilinear interpolation for each channel
    for c in range(3):
        output[:, :, c] = (
            img[i0, j0, c] * (1 - frac_i) * (1 - frac_j) +
            img[i0, j1, c] * (1 - frac_i) * frac_j +
            img[i1, j0, c] * frac_i * (1 - frac_j) +
            img[i1, j1, c] * frac_i * frac_j
        )
    
    return output.astype(np.uint8)


def process_cone_image(
    cone: Dict,
    dry_run: bool = False,
    quality: int = JPEG_QUALITY
) -> Tuple[bool, str]:
    """
    Process a single cone's image: calculate rotation and apply to panorama.
    
    Returns:
        (success, processed_path) tuple
    """
    image_path = Path(cone['image_path'])
    
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return False, ""
    
    # Calculate Euler angles from direction vectors
    direction = cone.get('direction')
    if not direction or not direction.get('forward') or not direction.get('up'):
        print(f"❌ Missing direction data for cone {cone['cone_id']}")
        return False, ""
    
    yaw, pitch, roll = vectors_to_euler_angles(
        direction['forward'],
        direction['up']
    )
    
    print(f"📐 Cone {cone['cone_id']}: yaw={yaw:.2f}°, pitch={pitch:.2f}°, roll={roll:.2f}°")
    
    # Create processed directory
    processed_dir = image_path.parent / 'processed'
    processed_path = processed_dir / image_path.name
    
    if dry_run:
        print(f"[dry-run] Would process: {image_path} -> {processed_path}")
        return True, str(processed_path.relative_to(Path.cwd())).replace('\\', '/')
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and process image
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_array = np.array(img)
            height, width = img_array.shape[0], img_array.shape[1]
            
            print(f"🔄 Processing {width}x{height} panorama...")
            
            # Apply rotation
            rotated_array = apply_equirectangular_rotation(
                img_array, yaw, pitch, roll
            )
            
            # Save processed image
            output_img = Image.fromarray(rotated_array)
            output_img.save(
                processed_path,
                format='JPEG',
                quality=quality,
                optimize=True,
                progressive=True
            )
            
            print(f"✅ Saved: {processed_path}")
            
            # Return relative path (using absolute path resolution)
            try:
                rel_path = processed_path.relative_to(Path.cwd())
            except ValueError:
                # If relative_to fails, use the path relative to the image parent
                rel_path = Path(image_path.parent.name) / 'processed' / image_path.name
            
            rel_path_str = str(rel_path).replace('\\', '/')
            return True, rel_path_str
            
    except Exception as e:
        print(f"❌ Failed to process {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return False, ""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Bake full 3D rotation (yaw, pitch, roll) into 360° panoramas'
    )
    parser.add_argument(
        '--input', '-i',
        default='cone_data.json',
        help='Input JSON file with cone data'
    )
    parser.add_argument(
        '--output', '-o',
        default='cone_data_processed.json',
        help='Output JSON file with processed cone data'
    )
    parser.add_argument(
        '--quality', '-q',
        type=int,
        default=JPEG_QUALITY,
        help='JPEG quality for output images (default: 85)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without processing images'
    )
    parser.add_argument(
        '--limit', '-n',
        type=int,
        default=None,
        help='Only process first N cones (for testing)'
    )
    
    args = parser.parse_args(argv)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return 1
    
    print(f"📂 Loading: {input_path}")
    data = load_json(input_path)
    
    cones = data.get('cones', [])
    if not cones:
        print("❌ No cones found in input data")
        return 1
    
    # Limit for testing
    if args.limit:
        cones = cones[:args.limit]
        print(f"⚠️  Processing only first {args.limit} cones (--limit flag)")
    
    print(f"🎯 Processing {len(cones)} cones...\n")
    
    # Process each cone
    processed_cones = []
    success_count = 0
    fail_count = 0
    
    for cone in cones:
        print(f"\n{'='*60}")
        print(f"Processing Cone {cone['cone_id']} - {cone['image_path']}")
        print('='*60)
        
        success, processed_path = process_cone_image(
            cone, 
            dry_run=args.dry_run,
            quality=args.quality
        )
        
        if success:
            # Create new cone entry with processed path and identity rotation
            new_cone = cone.copy()
            new_cone['image_path'] = processed_path
            new_cone['original_image_path'] = cone['image_path']
            
            # Set direction to identity (forward = +Z, up = +Y in A-Frame coords)
            # Which is (0, 0, 1) for forward and (0, 1, 0) for up in A-Frame
            # Converting back to DXF: A-Frame(x,y,z) -> DXF(x, -z, y)
            new_cone['direction'] = {
                'forward': {'x': 0.0, 'y': -1.0, 'z': 0.0},  # Forward in DXF
                'up': {'x': 0.0, 'y': 0.0, 'z': 1.0}  # Up in DXF (Z-up)
            }
            new_cone['rotation_baked'] = True
            
            processed_cones.append(new_cone)
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Processing Summary")
    print('='*60)
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed:  {fail_count}")
    print('='*60)
    
    if not args.dry_run and processed_cones:
        # Create output data
        output_data = data.copy()
        output_data['cones'] = processed_cones
        output_data['export_info']['processing_timestamp'] = datetime.now().isoformat()
        output_data['export_info']['rotation_baked'] = True
        output_data['export_info']['original_file'] = str(input_path)
        
        # Backup original
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_path = input_path.with_suffix(f'.bak.{timestamp}.json')
        shutil.copy2(input_path, backup_path)
        print(f"\n💾 Backup created: {backup_path}")
        
        # Save processed data
        output_path = Path(args.output)
        save_json(output_path, output_data)
        print(f"\n🎉 All done! Processed data saved to: {output_path}")
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())

