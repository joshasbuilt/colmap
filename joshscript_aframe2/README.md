# joshscript_aframe2

A clean, organized A-Frame visualization project for COLMAP camera position visualization.

## Project Structure

```
joshscript_aframe2/
├── floorplan-viewer.html        # Main A-Frame visualization file
├── styles.css                   # Styling for the visualization
├── navigation-system.js         # Navigation functionality
├── server.py                    # Local server for serving files
├── generate_camera_positions_svg.py  # Python script to generate SVG from COLMAP data
├── SVG_CREATION_PROCESS.md     # Detailed documentation for SVG creation
└── README.md                    # This file
```

## Quick Start

1. **Start the local server**:
   ```bash
   python server.py
   ```

2. **Open the visualization**:
   - Navigate to `http://localhost:8000/floorplan-viewer.html`
   - The visualization will load with the floorplan and camera positions

## COLMAP Integration

### Method 1: From COLMAP Database (database.db)

The project is configured to work with the current COLMAP import folder:
```
video1_frames_workspace/
├── database.db
├── database.db-shm
└── database.db-wal
```

To generate a new SVG file with camera positions from your COLMAP database:

```bash
python generate_camera_positions_svg.py --db ../video1_frames_workspace/database.db --output camera_positions.svg
```

Options:
- `--db`: Path to COLMAP database file
- `--output`: Output SVG file path
- `--width`: SVG width (default: 1000)
- `--height`: SVG height (default: 1000)

### Method 2: From Sparse Reconstruction Folders (NEW!)

Generate SVG files directly from COLMAP sparse reconstruction binary files:

```bash
python generate_svgs_from_sparse.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse" --folders 0 1 2 3 4 5 6
```

Or use the batch file:
```bash
GENERATE_SVGS.bat
```

**Current Generated SVGs:**
- `camera_positions_0.svg` - 1,832 camera positions
- `camera_positions_1.svg` - 720 camera positions
- `camera_positions_2.svg` - 88 camera positions
- `camera_positions_3.svg` - 88 camera positions
- `camera_positions_4.svg` - 80 camera positions
- `camera_positions_5.svg` - 112 camera positions
- `camera_positions_6.svg` - 112 camera positions

See `SVG_GENERATION_GUIDE.md` for detailed documentation on generating SVGs from sparse reconstructions.

## Features

- **Interactive Floorplan**: Load and display floorplan images
- **Camera Position Overlay**: SVG overlay showing camera positions
- **Navigation System**: Smooth navigation between camera positions
- **Responsive Design**: Works on different screen sizes
- **Real-time Updates**: Easy to update camera positions

## Dependencies

### Python Scripts
- `sqlite3` (built-in)
- `numpy`
- `pyproj`
- `lxml`

Install with:
```bash
pip install numpy pyproj lxml
```

### Web Dependencies
- A-Frame
- Fabric.js
- Modern web browser

## File Descriptions

### `floorplan-viewer.html`
The main visualization file containing:
- A-Frame scene setup
- Floorplan loading and display
- SVG overlay functionality
- Camera position visualization
- Navigation controls

### `styles.css`
Styling for the visualization including:
- Layout styles
- Camera marker styles
- Navigation controls
- Responsive design

### `navigation-system.js`
Navigation functionality including:
- Camera position switching
- Smooth transitions
- User interface controls

### `server.py`
Simple HTTP server for local development:
- Serves static files
- Handles CORS for local development
- Basic error handling

### `generate_camera_positions_svg.py`
Python script for generating SVG files:
- Extracts camera positions from COLMAP database
- Handles coordinate transformations
- Generates properly formatted SVG files
- Supports customization options

## Development

### Adding New Features
1. Modify the appropriate file (HTML, CSS, or JS)
2. Test with the local server
3. Update documentation as needed

### Customizing Camera Positions
1. Run the SVG generation script with your COLMAP database
2. Adjust coordinate transformations if needed
3. Test the visualization with the new SVG

### Troubleshooting
- Check browser console for errors
- Verify COLMAP database path
- Ensure all dependencies are installed
- Check SVG file format and syntax

## Notes

- This is a clean version of the original joshscript_aframe project
- The COLMAP import folder structure has changed from `project1/` to `video1_frames_workspace/`
- All essential functionality has been preserved
- The project is ready for new development and customization
