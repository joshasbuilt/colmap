#!/usr/bin/env python3
"""
Bake full 3D rotation (yaw, pitch, roll) into 360° equirectangular panorama images.

This is a copy of the canonical baker but changed so that processed images
are always written under the script directory's `processed/` folder. That
matches the workflow where you keep originals in `paul/joshscript_aframe9_prepimages/original`
and want outputs next to the script.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation as R

# Default JPEG quality
JPEG_QUALITY = 85


def load_json(path: Path) -> Dict:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Dict, dry_run: bool = False):
    if dry_run:
        print(f"[dry-run] Would write JSON: {path}")
        return
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved JSON: {path}")


def dxf_to_aframe_coords(vec: Dict[str, float]) -> np.ndarray:
    return np.array([vec['x'], vec['z'], -vec['y']])


def vectors_to_euler_angles(forward: Dict, up: Dict) -> Tuple[float, float, float]:
    fwd_vec = dxf_to_aframe_coords(forward)
    up_vec = dxf_to_aframe_coords(up)
    fwd_vec = fwd_vec / np.linalg.norm(fwd_vec)
    up_vec = up_vec / np.linalg.norm(up_vec)
    right = np.cross(up_vec, fwd_vec)
    right = right / np.linalg.norm(right)
    corrected_up = np.cross(fwd_vec, right)
    corrected_up = corrected_up / np.linalg.norm(corrected_up)
    rot_matrix = np.column_stack([right, corrected_up, -fwd_vec])
    scipy_rot = R.from_matrix(rot_matrix)
    euler_rad = scipy_rot.as_euler('YXZ', degrees=False)
    yaw = np.degrees(euler_rad[0])
    pitch = np.degrees(euler_rad[1])
    roll = -np.degrees(euler_rad[2])
    return yaw, pitch, roll


def lonlat_to_direction(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    x = np.cos(lat) * np.sin(lon)
    y = np.sin(lat)
    z = np.cos(lat) * np.cos(lon)
    return np.stack([x, y, z], axis=-1)


def direction_to_lonlat(directions: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    x, y, z = directions[..., 0], directions[..., 1], directions[..., 2]
    lon = np.arctan2(x, z)
    lat = np.arcsin(np.clip(y, -1, 1))
    return lon, lat


def apply_equirectangular_rotation(img: np.ndarray, yaw_deg: float, pitch_deg: float, roll_deg: float) -> np.ndarray:
    height, width = img.shape[0], img.shape[1]
    rot = R.from_euler('YXZ', [yaw_deg, pitch_deg, -roll_deg], degrees=True)
    rot_inverse = rot.inv()
    i_coords = np.arange(height)
    j_coords = np.arange(width)
    j_grid, i_grid = np.meshgrid(j_coords, i_coords)
    lon_out = (j_grid / width) * 2 * np.pi - np.pi
    lat_out = (0.5 - i_grid / height) * np.pi
    directions_out = lonlat_to_direction(lon_out, lat_out)
    directions_rotated = rot_inverse.apply(directions_out.reshape(-1, 3))
    directions_rotated = directions_rotated.reshape(height, width, 3)
    lon_src, lat_src = direction_to_lonlat(directions_rotated)
    j_src = (lon_src + np.pi) / (2 * np.pi) * width
    i_src = (0.5 - lat_src / np.pi) * height
    j_src = j_src % width
    i_src = np.clip(i_src, 0, height - 1)
    output = np.zeros_like(img)
    j0 = np.floor(j_src).astype(int) % width
    j1 = (j0 + 1) % width
    i0 = np.floor(i_src).astype(int)
    i1 = np.minimum(i0 + 1, height - 1)
    frac_j = j_src - np.floor(j_src)
    frac_i = i_src - np.floor(i_src)
    for c in range(3):
        output[:, :, c] = (
            img[i0, j0, c] * (1 - frac_i) * (1 - frac_j) +
            img[i0, j1, c] * (1 - frac_i) * frac_j +
            img[i1, j0, c] * frac_i * (1 - frac_j) +
            img[i1, j1, c] * frac_i * frac_j
        )
    return output.astype(np.uint8)


def process_cone_image(cone: Dict, dry_run: bool = False, quality: int = JPEG_QUALITY) -> Tuple[bool, str]:
    image_path = Path(cone['image_path'])
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return False, ""
    direction = cone.get('direction')
    if not direction or not direction.get('forward') or not direction.get('up'):
        print(f"❌ Missing direction data for cone {cone['cone_id']}")
        return False, ""
    yaw, pitch, roll = vectors_to_euler_angles(direction['forward'], direction['up'])
    print(f"📐 Cone {cone['cone_id']}: yaw={yaw:.2f}°, pitch={pitch:.2f}°, roll={roll:.2f}°")

    # Ensure processed images are written under this script's directory
    script_dir = Path(__file__).resolve().parent
    processed_dir = script_dir / 'processed'
    processed_path = processed_dir / image_path.name

    if dry_run:
        print(f"[dry-run] Would process: {image_path} -> {processed_path}")
        # Return path relative to script_dir so downstream JSON points under the prepimages folder
        try:
            rel = processed_path.relative_to(script_dir)
            return True, str(rel).replace('\\', '/')
        except Exception:
            return True, str(processed_path).replace('\\', '/')

    processed_dir.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_array = np.array(img)
            height, width = img_array.shape[0], img_array.shape[1]
            print(f"🔄 Processing {width}x{height} panorama...")
            rotated_array = apply_equirectangular_rotation(img_array, yaw, pitch, roll)
            output_img = Image.fromarray(rotated_array)
            output_img.save(processed_path, format='JPEG', quality=quality, optimize=True, progressive=True)
            print(f"✅ Saved: {processed_path}")
            try:
                rel_path = processed_path.relative_to(script_dir)
            except ValueError:
                rel_path = processed_path
            rel_path_str = str(rel_path).replace('\\', '/')
            return True, rel_path_str

    except Exception as e:
        print(f"❌ Failed to process {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return False, ""


def main(argv=None):
    parser = argparse.ArgumentParser(description='Bake full 3D rotation (yaw, pitch, roll) into 360° panoramas')
    parser.add_argument('--input', '-i', default='cone_data.json', help='Input JSON file with cone data')
    parser.add_argument('--output', '-o', default='cone_data_processed.json', help='Output JSON file with processed cone data')
    parser.add_argument('--quality', '-q', type=int, default=JPEG_QUALITY, help='JPEG quality for output images (default: 85)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without processing images')
    parser.add_argument('--limit', '-n', type=int, default=None, help='Only process first N cones (for testing)')
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
    if args.limit:
        cones = cones[:args.limit]
        print(f"⚠️  Processing only first {args.limit} cones (--limit flag)")
    print(f"🎯 Processing {len(cones)} cones...\n")
    processed_cones = []
    success_count = 0
    fail_count = 0
    for cone in cones:
        print(f"\n{'='*60}")
        print(f"Processing Cone {cone['cone_id']} - {cone['image_path']}")
        print('='*60)
        success, processed_path = process_cone_image(cone, dry_run=args.dry_run, quality=args.quality)
        if success:
            success_count += 1
            new_cone = cone.copy()
            new_cone['image_path'] = processed_path
            new_cone['original_image_path'] = cone['image_path']
            new_cone['direction'] = {
                'forward': {'x': 0.0, 'y': -1.0, 'z': 0.0},
                'up': {'x': 0.0, 'y': 0.0, 'z': 1.0}
            }
            new_cone['rotation_baked'] = True
            processed_cones.append(new_cone)
        else:
            fail_count += 1
    print('\n📊 Processing Summary')
    print('============================================================')
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed:  {fail_count}")
    print('============================================================')
    export = {
        'export_info': {
            'source': 'bake_full_3d_rotation (prepimages copy)',
            'timestamp': datetime.now().isoformat()
        },
        'cones': processed_cones
    }
    out_path = Path(args.output)
    save_json(out_path, export, dry_run=args.dry_run)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
