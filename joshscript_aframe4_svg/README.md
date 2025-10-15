# joshscript_aframe4

A streamlined workflow for processing multiple COLMAP sparse reconstructions with automatic gravity correction and SVG generation.

## Overview

This project is based on the proven `auto_gravity_align.py` script from `paul/joshscripts/Camera01/` but modified to handle multiple reconstruction folders and generate SVGs in the correct format.

## Key Features

- **🎯 Automatic Gravity Correction** - Uses PCA to detect gravity direction from camera positions
- **📁 Multiple Folder Processing** - Process multiple sparse reconstruction folders at once
- **🎨 Correct SVG Format** - Generates SVGs matching the reference format exactly
- **⚙️ Proven Algorithm** - Based on the working `auto_gravity_align.py` script
- **🔧 Proper Transformations** - Uses origin, scale, and robust bounds calculation

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Process all reconstruction folders in a sparse directory:

```bash
python process_multiple_reconstructions.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse"
```

### Specific Folders

Process only specific folders:

```bash
python process_multiple_reconstructions.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse" --folders 0 1 2 3 4 5 6
```

### Custom Parameters

```bash
python process_multiple_reconstructions.py \
  --sparse-dir "path/to/sparse" \
  --folders 0 1 2 3 \
  --camera-index 1 \
  --output-dir "my_svgs" \
  --origin-feet 67.472490761 -23.114793212 151.586679018 \
  --scale 1.65
```

## Output

- **SVG Files**: `camera_positions_0.svg`, `camera_positions_1.svg`, etc.
- **Format**: Matches the reference format from `paul/joshscript_aframe/camera_positions.svg`
- **Features**: 
  - Red circles for camera positions
  - Red trajectory lines
  - Proper scaling and viewBox
  - Gravity-corrected coordinates

## How It Works

1. **Load Reconstruction** - Loads COLMAP sparse reconstruction
2. **Extract Camera Positions** - Gets camera1 positions from each frame
3. **Gravity Detection** - Uses PCA to find ground plane normal
4. **Rotation Calculation** - Computes rotation to align with Z-up
5. **Coordinate Transformation** - Applies origin, scale, and rotation
6. **Robust Bounds** - Calculates 10th-90th percentile bounds with padding
7. **Centered ViewBox** - Shifts coordinates so median is at origin
8. **SVG Generation** - Creates SVG with correct format and scaling

## Parameters

- `--sparse-dir`: Path to sparse directory containing numbered folders
- `--folders`: Specific folder numbers to process (optional)
- `--output-dir`: Output directory for SVG files (default: svg_output)
- `--camera-index`: Camera index to extract (default: 1)
- `--origin-feet`: Origin in feet (x y z) (default: Revit origin)
- `--scale`: Scale factor (default: 1.65)

## Requirements

- Python 3.7+
- pycolmap
- numpy
- scikit-learn

## Based On

This project is based on the proven scripts from `paul/joshscripts/Camera01/`:
- `auto_gravity_align.py` - Gravity correction algorithm
- `do_affine_export_gravity.py` - Transformation parameters
- `export_cameras_to_json.py` - Camera extraction logic
