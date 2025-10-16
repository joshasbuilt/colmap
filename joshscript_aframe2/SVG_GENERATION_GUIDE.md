# SVG Generation Guide

## Overview

This guide explains how to generate SVG files from COLMAP sparse reconstruction folders. The SVG files visualize camera positions and orientations in a top-down 2D view.

## Generated SVG Files

The following SVG files have been generated from `D:\Camera01\reconstruction_mask3_012_previews_run\sparse`:

| SVG File | Reconstruction Folder | Camera Positions | Description |
|----------|----------------------|------------------|-------------|
| camera_positions_0.svg | 0 | 1,832 | Main reconstruction with most cameras |
| camera_positions_1.svg | 1 | 720 | Large reconstruction subset |
| camera_positions_2.svg | 2 | 88 | Small reconstruction subset |
| camera_positions_3.svg | 3 | 88 | Small reconstruction subset |
| camera_positions_4.svg | 4 | 80 | Small reconstruction subset |
| camera_positions_5.svg | 5 | 112 | Medium reconstruction subset |
| camera_positions_6.svg | 6 | 112 | Medium reconstruction subset |

## How to Use the Script

### Basic Usage

```bash
python generate_svgs_from_sparse.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse" --folders 0 1 2 3 4 5 6
```

### Using the Batch File

Double-click `GENERATE_SVGS.bat` to automatically regenerate all SVG files.

### Command-Line Options

- `--sparse-dir`: Path to the sparse directory containing numbered reconstruction folders
- `--folders`: Specific folder numbers to process (e.g., 0 1 2 3)
- `--output-dir`: Output directory for SVG files (default: current directory)

### Examples

Generate SVG for a single reconstruction:
```bash
python generate_svgs_from_sparse.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse" --folders 0
```

Generate SVGs for all numbered folders (auto-detect):
```bash
python generate_svgs_from_sparse.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse"
```

Output to a different directory:
```bash
python generate_svgs_from_sparse.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse" --folders 0 1 2 --output-dir "output_svgs"
```

## SVG File Structure

Each SVG file contains:

1. **Camera Markers**: Red circles representing camera positions
2. **Camera IDs**: Text labels showing the camera/image ID
3. **Orientation Arrows**: Blue arrows showing camera viewing direction
4. **Interactive Elements**: Hover effects for better visualization

### SVG Features

- **Viewbox**: 1000x1000 with automatic scaling
- **Responsive**: 100% width and height, adapts to container
- **Styled**: CSS classes for easy customization
- **Interactive**: Cursor pointer and hover opacity effects
- **Metadata**: Image names stored in data attributes

## Technical Details

### COLMAP Binary File Format

The script reads the following COLMAP binary files:
- `cameras.bin`: Camera intrinsic parameters
- `images.bin`: Camera poses (position and orientation)

### Supported Camera Models

The script supports all standard COLMAP camera models:
- SIMPLE_PINHOLE (3 params)
- PINHOLE (4 params)
- SIMPLE_RADIAL (4 params)
- RADIAL (5 params)
- OPENCV (8 params)
- OPENCV_FISHEYE (8 params)
- FULL_OPENCV (12 params)
- FOV (5 params)
- SIMPLE_RADIAL_FISHEYE (4 params)
- RADIAL_FISHEYE (5 params)
- THIN_PRISM_FISHEYE (12 params)

### Coordinate Transformation

The script performs the following transformations:
1. Reads quaternion (qw, qx, qy, qz) and translation (tx, ty, tz) from COLMAP
2. Converts to camera center: C = -R^T * t
3. Projects to 2D (X-Y plane) for top-down view
4. Scales and centers within SVG viewbox with margins
5. Calculates orientation arrows from rotation matrix

## Troubleshooting

### Error: "Missing binary files"
- Check that the sparse folder contains `cameras.bin` and `images.bin`
- Verify the path to the sparse directory is correct

### Error: "No images found in reconstruction"
- The reconstruction folder may be empty
- Check that COLMAP reconstruction completed successfully

### SVG appears blank
- Check that camera positions are within reasonable bounds
- The scaling might need adjustment if coordinates are very large/small

### Dependencies

The script requires:
```bash
pip install numpy lxml
```

## Integration with A-Frame Viewer

To use these SVG files in the A-Frame floorplan viewer:

1. Open `floorplan-viewer.html` in your web browser
2. The viewer can load any of the generated SVG files
3. Modify the HTML to point to the desired SVG file
4. The camera positions will overlay on your floorplan

## Next Steps

- Overlay SVG on actual floorplan images
- Add click handlers to navigate between camera positions
- Implement filtering to show/hide camera subsets
- Add color coding for different camera rigs or time periods
- Create merged view showing all reconstructions simultaneously



