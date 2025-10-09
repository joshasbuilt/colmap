# 3D Rotation Baking for 360° Panoramas

## Overview

This document explains the `bake_full_3d_rotation.py` script that bakes full 3D rotations (yaw, pitch, roll) into 360° equirectangular panorama images.

## What It Does

The script takes panorama images with camera orientation data and "bakes in" the rotation corrections by actually rotating the pixels in the image. This means:

1. **Before processing**: Images need rotation applied in A-Frame viewer using forward/up vectors
2. **After processing**: Images are pre-rotated, so they display correctly with identity rotation

## Test Results (First 5 Images)

Successfully processed 5 panoramas with the following rotations:

| Cone | Image | Yaw | Pitch | Roll |
|------|-------|-----|-------|------|
| 1 | frame_0023.jpg | -177.59° | 0.08° | 179.94° |
| 2 | frame_0024.jpg | 179.76° | 6.44° | 0.26° |
| 3 | frame_0025.jpg | -174.66° | 0.24° | 179.81° |
| 4 | frame_0026.jpg | 177.30° | -0.12° | -179.91° |
| 5 | frame_0027.jpg | 0.14° | -1.66° | -2.91° |

All images processed successfully and saved to `panoramas/processed/`

## How It Works

### 1. Coordinate System Conversion
Converts DXF (Z-up) coordinates to A-Frame (Y-up):
```
DXF(x,y,z) → A-Frame(x, z, -y)
```

### 2. Euler Angle Extraction
Uses the same logic as `navigation-system.js`:
- Builds orthonormal basis from forward/up vectors
- Constructs rotation matrix
- Extracts Euler angles in YXZ order
- Matches A-Frame's THREE.js implementation exactly

### 3. Equirectangular Rotation
For each output pixel:
1. Convert pixel coordinates to longitude/latitude
2. Convert lon/lat to 3D direction vector
3. Apply inverse rotation to the direction
4. Convert back to lon/lat to find source pixel
5. Sample from source with bilinear interpolation

This approach properly handles:
- Wraparound at the seam (longitude ±180°)
- Poles (latitude ±90°)
- Sub-pixel accuracy with interpolation
- Full 3D rotation (not just horizontal shifting)

## Usage

### Basic Usage
```bash
# Process first 5 images (testing)
python bake_full_3d_rotation.py --limit 5

# Process all images
python bake_full_3d_rotation.py

# Dry run (see what would happen)
python bake_full_3d_rotation.py --dry-run
```

### Advanced Options
```bash
# Custom input/output files
python bake_full_3d_rotation.py --input cone_data.json --output cone_data_processed.json

# Adjust JPEG quality
python bake_full_3d_rotation.py --quality 90

# Process specific number of images
python bake_full_3d_rotation.py --limit 10
```

## Output Files

### Processed Images
- **Location**: `panoramas/processed/frame_XXXX.jpg`
- **Format**: JPEG with progressive encoding
- **Quality**: 85 (default, configurable)
- **Optimization**: Enabled for smaller file sizes

### Processed JSON
- **File**: `cone_data_processed.json`
- **Changes**:
  - `image_path` updated to point to processed images
  - `original_image_path` stores original path
  - `direction` vectors set to identity (forward = -Y, up = +Z in DXF)
  - `rotation_baked` flag set to true

### Backup
- **File**: `cone_data.bak.TIMESTAMP.json`
- Automatic backup of original file before processing

## Identity Rotation Format

After processing, all cones have identity rotation in DXF coordinates:

```json
"direction": {
  "forward": {"x": 0.0, "y": -1.0, "z": 0.0},
  "up": {"x": 0.0, "y": 0.0, "z": 1.0}
}
```

This means:
- Forward points in -Y direction (DXF)
- Up points in +Z direction (DXF Z-up)
- When displayed in A-Frame, no rotation is needed

## Performance

- **Image size**: 5760x2880 pixels (typical 360° panorama)
- **Processing time**: ~3-5 seconds per image
- **Memory usage**: Moderate (loads full image into numpy array)

## Technical Details

### Dependencies
- `numpy`: Array operations and interpolation
- `PIL/Pillow`: Image loading and saving
- `scipy`: Rotation matrix and Euler angle conversion

### Coordinate Systems
- **DXF**: Z-up, right-handed (from COLMAP)
- **A-Frame**: Y-up, right-handed (THREE.js standard)
- **Equirectangular**: Longitude [-π, π], Latitude [-π/2, π/2]

### Rotation Convention
- **Euler Order**: YXZ (intrinsic rotations)
- **Axes**: X=pitch (up/down), Y=yaw (left/right), Z=roll (tilt)
- **Inverse Rotation**: Applied during pixel remapping (inverse mapping)

## Comparison with Previous Script

### `bake_rotations_and_compress.py` (Old)
- Only handled yaw (horizontal shifting)
- Simple pixel rolling
- Fast but incomplete

### `bake_full_3d_rotation.py` (New)
- Handles yaw, pitch, and roll
- Full 3D spherical rotation
- Proper equirectangular mapping
- Matches A-Frame rendering exactly

## Verification

To verify the processed images work correctly:

1. Update your A-Frame viewer to use `cone_data_processed.json`
2. The panoramas should display with correct orientation
3. No additional rotation should be needed in the viewer

The `applySkyRotation()` function in `navigation-system.js` will receive identity rotations and apply no transformation.

## Future Improvements

Potential enhancements:
- Parallel processing for faster batch operations
- GPU acceleration using OpenGL/CUDA
- Progressive quality levels for different viewing distances
- Smart caching to avoid reprocessing unchanged images

---

**Created**: October 9, 2025  
**Test Status**: ✅ Passed (5/5 images processed successfully)  
**Script**: `bake_full_3d_rotation.py`





