#!/usr/bin/env python3
"""
Bake rotation corrections into 360 images and compress them.

Behavior:
- Reads a navigation/geojson-style manifest containing image references (default
  `360-navigation-data (19).json`).
- Finds every dict with an `imagePath` property (recursively), reads the
  corresponding JPEG, horizontally shifts pixels according to the entry's
  `rotationCorrection` (degrees), and writes the result to a `processed`
  subdirectory next to the source image (same filename). Existing processed
  files are overwritten.
- Saves JPEG with quality default 80 (re-using project convention).
- Produces a new JSON file with `-processed` appended to the original filename
  (e.g. `360-navigation-data (19)-processed.json`). For each processed
  sphere entry the `imagePath` is updated to point into `.../processed/...`
  and `rotationCorrection` is set to 0. The original JSON is left untouched.

Notes:
- This tool expects only JPG sources. If a source is not a JPEG, the script
  raises an error and stops (per user instruction).
- A `--dry-run` flag prints planned actions without writing files.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List

import numpy as np
from PIL import Image

# Default JPEG quality, match manifest_batch_processor.py
JPEG_QUALITY = 80
# Previously we special-cased `path7/` for testing; per request negate all rotations



def load_json(path: Path) -> Dict:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Dict, dry_run: bool = False):
    if dry_run:
        print(f"[dry-run] Would write JSON: {path}")
        return
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved JSON: {path}")


def find_image_entries(obj: object) -> List[Tuple[Dict, str]]:
    """Recursively find dicts that contain an 'imagePath' key.

    Returns a list of (parent_dict, key_name) where parent_dict[key_name]
    is a dict that contains 'imagePath'. In practice we will inspect the
    dict for `imagePath` and `rotationCorrection` keys.
    """
    found = []

    if isinstance(obj, dict):
        if 'imagePath' in obj:
            found.append((obj, 'imagePath'))
        for v in obj.values():
            found.extend(find_image_entries(v))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_image_entries(item))

    return found


def ensure_processed_path_for(src: Path) -> Path:
    """Return destination path for the processed image and ensure directory exists."""
    parent = src.parent
    processed_dir = parent / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir / src.name


def bake_and_compress_image(src_path: Path, rotation_deg: float, dst_path: Path, dry_run: bool = False) -> bool:
    """Apply horizontal shift and save as JPEG at dst_path.

    Returns True on success, False otherwise.
    """
    if not src_path.exists():
        print(f"❌ Source not found: {src_path}")
        return False

    # Enforce JPEG-only sources as requested
    suffix = src_path.suffix.lower()
    if suffix not in ('.jpg', '.jpeg'):
        raise RuntimeError(f"Non-JPEG source encountered: {src_path} (only JPG/JPEG supported)")

    if dry_run:
        print(f"[dry-run] Would process: {src_path} -> {dst_path} (rotation={rotation_deg}°)")
        return True

    try:
        with Image.open(src_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            arr = np.array(img)
            height, width = arr.shape[0], arr.shape[1]

            # Compute float pixel shift (positive = shift right)
            shift = (rotation_deg / 360.0) * width

            # Normalize shift into [0, width)
            shift = shift % width

            int_shift = int(np.floor(shift))
            frac = shift - np.floor(shift)

            # Integer roll(s)
            rolled1 = np.roll(arr, int_shift, axis=1)
            if frac == 0:
                blended = rolled1
            else:
                rolled2 = np.roll(arr, (int_shift + 1) % width, axis=1)
                blended = np.clip((1.0 - frac) * rolled1 + frac * rolled2, 0, 255).astype(np.uint8)

            out_img = Image.fromarray(blended)

            # Save as JPEG with requested quality and optimization
            dst_path_parent = dst_path.parent
            dst_path_parent.mkdir(parents=True, exist_ok=True)

            save_kwargs = {
                'format': 'JPEG',
                'quality': JPEG_QUALITY,
                'optimize': True,
                'progressive': True,
            }

            out_img.save(dst_path, **save_kwargs)
            print(f"✅ Processed and saved: {dst_path} ({width}x{height}, rotation baked {rotation_deg:.2f}°)")
            return True

    except Exception as e:
        print(f"❌ Failed to process {src_path}: {e}")
        return False


def make_processed_manifest(original_path: Path, data: Dict, mapping: Dict[str, str], suffix: str, dry_run: bool = False) -> Path:
    """Create processed manifest file path and write updated JSON."""
    stem = original_path.stem
    new_name = f"{stem}{suffix}{original_path.suffix}"
    new_path = original_path.with_name(new_name)

    # Create deep copy with updates applied
    new_data = json.loads(json.dumps(data))

    # Update every dict that has an imagePath and exists in mapping
    entries_updated = 0
    for parent_dict, _ in find_image_entries(new_data):
        orig_path = parent_dict.get('imagePath')
        if not orig_path:
            continue
        if orig_path in mapping:
            parent_dict['imagePath'] = mapping[orig_path]
            # Zero out rotationCorrection where present
            if 'rotationCorrection' in parent_dict:
                parent_dict['rotationCorrection'] = 0
            entries_updated += 1

    # Ensure deterministically ordered spheres within each path based on imagePath
    try:
        paths = new_data.get('paths', []) if isinstance(new_data, dict) else []
        for path in paths:
            spheres = path.get('spheres') if isinstance(path, dict) else None
            if isinstance(spheres, list):
                spheres.sort(key=lambda s: (s.get('imagePath') or '').lower())
    except Exception as exc:
        print(f"⚠️ Failed to sort spheres by imagePath: {exc}")

    print(f"📦 Will update {entries_updated} imagePath entries in new manifest")

    if dry_run:
        print(f"[dry-run] Would write processed manifest to: {new_path}")
        return new_path

    # Backup original manifest (timestamped)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = original_path.with_suffix(original_path.suffix + f'.bak.{timestamp}')
    shutil.copy2(original_path, backup_path)
    print(f"💾 Backup of original manifest written to: {backup_path}")

    save_json(new_path, new_data, dry_run=False)
    return new_path


def main(argv=None):
    p = argparse.ArgumentParser(description='Bake rotations into 360 images and compress to JPEG (processed subdir).')
    p.add_argument('--manifest', '-m', default='360-navigation-data (19).json', help='Manifest JSON file to process')
    p.add_argument('--suffix', default='-processed', help='Suffix to append to new JSON filename (before .json)')
    p.add_argument('--dry-run', action='store_true', help='Do not write files; show planned actions')
    p.add_argument('--quality', type=int, default=JPEG_QUALITY, help='JPEG quality for output images')

    args = p.parse_args(argv)

    # Set module-level JPEG_QUALITY without creating a local binding that
    # confuses the interpreter (avoid 'global' after using the name).
    globals()['JPEG_QUALITY'] = int(args.quality)

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return 2

    data = load_json(manifest_path)

    # Find all image entries (unique paths)
    entries = find_image_entries(data)
    image_paths = []
    for parent, _ in entries:
        ip = parent.get('imagePath')
        if ip and ip not in image_paths:
            image_paths.append(ip)

    print(f"🔎 Found {len(image_paths)} unique imagePath entries to process")

    # Map from original imagePath -> processed relative path
    mapping = {}
    processed = 0
    skipped = 0

    for rel_path in image_paths:
        src_path = Path(rel_path)
        dst_path = ensure_processed_path_for(src_path)

        # Gather rotation value from the corresponding entry(s) - use first match
        rotation = 0.0
        for parent, _ in entries:
            if parent.get('imagePath') == rel_path and 'rotationCorrection' in parent:
                try:
                    rotation = float(parent.get('rotationCorrection', 0) or 0)
                except Exception:
                    rotation = 0.0
                break

        # Unconditionally invert the rotation sign for every image (keeps zero as zero)
        rotation = -rotation
        print(f"↩️ Negated rotation for {rel_path} -> {rotation:.2f}°")

        try:
            success = bake_and_compress_image(src_path, rotation, dst_path, dry_run=args.dry_run)
        except RuntimeError as e:
            print(f"❌ Error: {e}")
            return 3

        if success:
            # Build relative processed path string (relative style, no leading slash)
            rel_processed = str(Path(src_path.parent.name) / 'processed' / src_path.name) if src_path.parent.name else str(dst_path.name)
            # But better to preserve the original relative folder structure exactly
            # So compute path relative to current working dir if possible
            # Make processed path relative to cwd and normalize to forward slashes
            try:
                relp = os.path.relpath(dst_path, start=Path.cwd())
            except Exception:
                relp = str(dst_path)
            relp = relp.replace('\\', '/')
            mapping[rel_path] = relp
            processed += 1
        else:
            skipped += 1

    print(f"✅ Processing complete. Processed: {processed}, Skipped: {skipped}")

    # Create processed manifest (new JSON) and write it
    new_manifest = make_processed_manifest(manifest_path, data, mapping, args.suffix, dry_run=args.dry_run)

    print(f"All done. New manifest: {new_manifest}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
