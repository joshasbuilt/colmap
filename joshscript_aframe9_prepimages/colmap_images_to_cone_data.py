#!/usr/bin/env python3
"""
Create cone_data.json from a COLMAP sparse model (images.txt/images.bin).

Outputs DXF-style `dxf_position` and `direction` entries suitable for
`bake_full_3d_rotation.py` and the viewer.

Usage example:
  python colmap_images_to_cone_data.py --model-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse" \
    --images-dir "." --output cone_data_from_colmap.json --dry-run --limit 5

The script expects the model directory to contain cameras.(bin|txt), images.(bin|txt), points3D.(bin|txt)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import numpy as np

from read_write_model import read_model, qvec2rotmat
import re
from glob import glob


def camera_center_from_qt(qvec: np.ndarray, tvec: np.ndarray) -> np.ndarray:
    """Compute camera center (world coordinates) from qvec,tvec using COLMAP convention.

    COLMAP stores images with qvec,tvec such that a point X_world is projected as:
      x_cam = R * X_world + t
    To get camera center C (world coords):
      C = -R^T * t
    where R = qvec2rotmat(qvec)
    """
    Rm = qvec2rotmat(qvec)
    # invert
    R_world_cam = Rm.T
    C = -R_world_cam @ tvec
    return C


def forward_up_from_qvec(qvec: np.ndarray) -> Dict[str, Dict[str, float]]:
    """Derive forward and up vectors in DXF convention from qvec.

    We'll compute the camera-to-world rotation (R_world_cam) and extract
    the forward vector as -Z axis of camera (camera looks along -Z in THREE.js),
    but in COLMAP convention the camera axes follow the rotation matrix.
    We'll return vectors as DXF (x,y,z) without flipping — bake_full_3d_rotation
    expects DXF coordinates where later it converts to A-Frame.
    """
    Rm = qvec2rotmat(qvec)
    R_world_cam = Rm.T
    # Camera axes in world coordinates: columns of R_world_cam are camera X,Y,Z
    cam_x = R_world_cam[:, 0]
    cam_y = R_world_cam[:, 1]
    cam_z = R_world_cam[:, 2]

    # forward is -Z in camera coordinates so world forward = -cam_z
    forward = -cam_z
    up = cam_y

    return {
        'forward': {'x': float(forward[0]), 'y': float(forward[1]), 'z': float(forward[2])},
        'up': {'x': float(up[0]), 'y': float(up[1]), 'z': float(up[2])}
    }


def build_cone_entries(cameras, images, images_dir: Path, limit: int | None = None):
    cones = []
    # Sort images by numeric frame index extracted from the filename where possible
    def extract_frame_num(name: str):
        m = re.search(r"(\d{3,})", Path(name).stem)
        return int(m.group(1)) if m else 10**9

    items = list(images.items())
    items.sort(key=lambda kv: extract_frame_num(kv[1].name))
    if limit:
        items = items[:limit]

    for idx, (img_id, img) in enumerate(items, start=1):
        qvec = img.qvec
        tvec = img.tvec
        name = img.name

        C = camera_center_from_qt(qvec, tvec)

        direction = forward_up_from_qvec(qvec)

        # image path resolution
        # First try the exact path (images_dir/name). If that doesn't exist,
        # attempt to map to a flat images_dir where files are named like
        # 'frame_0176.jpg' instead of 'pano_camera0/frame_0176_hp_preview.jpg'.
        candidate = images_dir / name
        mapped_reason = None
        if not candidate.exists():
            # Try basename directly (strip any directory)
            base = Path(name).name
            candidate = images_dir / base
            if candidate.exists():
                mapped_reason = 'basename'
            else:
                # Strip common suffixes like '_hp_preview' or '_preview'
                stripped = re.sub(r'(_hp_preview|_preview|_preview.jpg|_hp_preview.jpg)$', '', base)
                # Ensure file extension
                if not stripped.lower().endswith('.jpg') and not stripped.lower().endswith('.jpeg'):
                    stripped_name = stripped + '.jpg'
                else:
                    stripped_name = stripped
                candidate = images_dir / stripped_name
                if candidate.exists():
                    mapped_reason = 'stripped_suffix'
                else:
                    # As a last resort, search for the numeric id within filenames
                    m = re.search(r'(\d{3,})', base)
                    found = None
                    if m:
                        digits = m.group(1)
                        # search images_dir for files containing these digits
                        for p in images_dir.iterdir():
                            if p.is_file() and digits in p.name:
                                found = p
                                break
                    if found:
                        candidate = found
                        mapped_reason = 'digit_search'
                    else:
                        # keep the original candidate (which will be missing)
                        candidate = images_dir / base
        img_path = candidate

        cone = {
            'cone_id': idx,
            'image_id': int(img_id),
            'image_path': str(img_path).replace('\\', '/'),
            'colmap_name': name,
            'dxf_position': {'x': float(C[0]), 'y': float(C[1]), 'z': float(C[2])},
            'direction': direction,
        }
        if mapped_reason:
            cone['image_path_mapping'] = mapped_reason
        cones.append(cone)

    return cones


def main(argv=None):
    p = argparse.ArgumentParser(description='COLMAP images -> cone_data.json')
    p.add_argument('--model-dir', required=True, help='Path to COLMAP model folder (contains images.txt or images.bin)')
    p.add_argument('--images-dir', default='.', help='Directory prefix for image files (default: current dir)')
    p.add_argument('--output', default='cone_data_from_colmap.json', help='Output JSON file path (relative paths resolved relative to script directory)')
    p.add_argument('--limit', type=int, default=None, help='Limit number of images (for testing)')
    p.add_argument('--camera', type=int, default=None, help='1-based camera index to filter (e.g. 2 -> matches "pano_camera1")')
    p.add_argument('--dry-run', action='store_true', help='Do not write file; print sample')
    args = p.parse_args(argv)

    model_dir = Path(args.model_dir)
    images_dir = Path(args.images_dir)

    # Resolve output path so that relative paths (including the default) are placed
    # in the same directory as this script file. This matches the expectation that
    # running the script will create the JSON next to the script itself.
    script_dir = Path(__file__).resolve().parent
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = script_dir / out_path

    print(f"📂 Reading COLMAP model from: {model_dir}")
    cameras, images, points3D = read_model(str(model_dir))

    print(f"Found {len(cameras)} cameras, {len(images)} images, {len(points3D)} points3D")

    # Optionally filter images by camera index (COLMAP image names contain a folder
    # like 'pano_camera0/frame_0176_hp_preview.jpg'). The --camera argument is
    # 1-based (so --camera 2 matches 'pano_camera1').
    if args.camera is not None:
        cam_idx = int(args.camera) - 1
        key = f'pano_camera{cam_idx}/'
        filtered = {k: v for k, v in images.items() if key in v.name}
        print(f"🔎 Filtering images by camera folder: '{key}' -> {len(filtered)} matches")
        cones = build_cone_entries(cameras, filtered, images_dir, limit=args.limit)
    else:
        cones = build_cone_entries(cameras, images, images_dir, limit=args.limit)

    export = {
        'export_info': {
            'source': 'colmap',
            'model_dir': str(model_dir),
            'timestamp': datetime.now().isoformat(),
        },
        'cones': cones
    }

    if args.dry_run:
        print('\n--- DRY RUN: first 5 cones ---')
        for c in cones[:5]:
            print(json.dumps(c, indent=2))
        return 0

    with out_path.open('w', encoding='utf-8') as f:
        json.dump(export, f, indent=2)
    print(f"✅ Wrote: {out_path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
