# Floor Plan Viewer (joshscript_aframe6_floorplanbase)

## Overview
Interactive floor plan viewer using pic3 technology with Mt Eden coordinates. Displays floor plan images with proper geolocation and coordinate transformations.

## Technology Stack
- **Fabric.js**: Canvas manipulation and interactive graphics
- **Proj4js**: Coordinate transformations between WGS84 and Mt Eden 2000
- **HTML5 Canvas**: Drawing and rendering
- **Python HTTP Server**: Local development server

## Key Features
- **Pan and Zoom**: Middle-click drag to pan, scroll wheel to zoom
- **Coordinate Display**: Real-time cursor coordinates in both WGS84 and Mt Eden 2000
- **Rotated Floor Plans**: Supports non-orthogonal floor plans with proper angle display
- **Multi-Floor Support**: Display multiple floor plans with layer management
- **Layer Control**: Right-click to send floors to back/forward
- **SVG Overlay**: Load and display camera position SVGs from COLMAP reconstructions

## Coordinate Systems
- **WGS84 (EPSG:4326)**: Standard global coordinates (longitude, latitude)
- **Mt Eden 2000 (EPSG:2105)**: Local New Zealand projection (Easting, Northing in meters)

## Usage

### Launch the Viewer
```bash
cd paul/joshscript_aframe6_floorplanbase
python server.py
```
Then open http://localhost:8000 in your browser.

## Adding New Floors

### Step 1: Extract Coordinates
Use the coordinate extraction process from `paul/joshscript_aframe5_har/`:
1. Load the project page in your browser
2. Open Developer Console (F12)
3. Run the extraction script to get WGS84 coordinates
4. Save coordinates as JSON file (e.g., `basement_coordinates.json`)

### Step 2: Add Floor Data
Edit the `geolocationData` object in `floor_plan_viewer.html`:

```javascript
const geolocationData = {
    groundFloor: {
        name: 'Ground Floor',
        image: 'floorplan_images/GroundFloor.png',
        bounds: [
            [174.74069378281493, -36.80542933064474],   // Top-Left
            [174.7412528239626, -36.805448062383675],   // Top-Right
            [174.74123108024065, -36.80581545281087],   // Bottom-Right
            [174.74067203909297, -36.80579672107194]    // Bottom-Left
        ]
    },
    firstFloor: {
        name: 'First Floor',
        image: 'floorplan_images/FirstFloor.png',
        bounds: [
            [174.74067575711504, -36.805431462369086],
            [174.74123484878098, -36.805451153593665],
            [174.74121799992923, -36.80582960011253],
            [174.7406589082633, -36.80580990888795]
        ]
    },
    // Add new floor here:
    basement: {
        name: 'Basement',
        image: 'floorplan_images/Basement.png',
        bounds: [
            [longitude1, latitude1],   // Top-Left
            [longitude2, latitude2],   // Top-Right
            [longitude3, latitude3],   // Bottom-Right
            [longitude4, latitude4]    // Bottom-Left
        ]
    }
};
```

### Step 3: Add Floor Image
1. Place the floor plan image in `floorplan_images/` directory
2. Name it according to the `image` property in the floor data

### Step 4: Update Initialization
Add the new floor to the initialization section:

```javascript
// Load all floors
Object.values(geolocationData).forEach(floorData => {
    loadFloorplanImage(floorData.image, floorData.bounds, floorData.name);
});
```

### Step 5: Test Layer Management
- Right-click on any floor to send it to back/forward
- Each floor is a single object for easy layer management
- Use the coordinate display to verify alignment

## File Structure
```
paul/joshscript_aframe6_floorplanbase/
├── floor_plan_viewer.html    # Main viewer application
├── server.py                 # Python HTTP server
├── README.md                 # This documentation
├── floorplan_images/         # Floor plan image files
│   ├── GroundFloor.png
│   ├── FirstFloor.png
│   └── [Additional floors...]
└── svg_files/                # SVG overlay files
    ├── camera_positions_0.svg
    ├── camera_positions_1.svg
    ├── camera_positions_2.svg
    ├── camera_positions_3.svg
    ├── camera_positions_4.svg
    ├── camera_positions_5.svg
    └── camera_positions_6.svg
```

## Current Floors
- **Ground Floor**: Main level with proper geolocation
- **First Floor**: Upper level with proper geolocation
- **Layer Management**: Right-click to send floors to back/forward

## SVG Overlays
- **Camera Positions**: 7 SVG files showing camera trajectories from COLMAP reconstructions
- **Enhanced Metadata**: Rich tooltips with detailed camera information
- **Interactive**: Each SVG can be selected, moved, scaled, and rotated
- **Layer Control**: Right-click to send SVGs to back/forward
- **Auto-loading**: All SVGs load automatically after floor plans

### Enhanced Metadata Includes:
- **2D Coordinates**: Projected position in the SVG view
- **3D Coordinates**: Original COLMAP world coordinates
- **Image Filename**: Source image from the reconstruction
- **Frame ID**: Sequential frame identifier
- **Height**: Z-coordinate (elevation) in meters
- **Camera ID**: COLMAP camera identifier
- **Timestamp**: Extracted from image filename (when available)

## Coordinate Extraction Process
The coordinates used in this viewer were extracted using the process documented in `paul/joshscript_aframe5_har/COORDINATE_EXTRACTION_GUIDE.md`.

## Troubleshooting

### Floor Plan Appears Orthogonal
- **Cause**: Using coordinate extents instead of actual floor plan corners
- **Solution**: Extract coordinates using React Fiber from the actual project page

### Floor Plan Appears Upside Down
- **Cause**: Incorrect coordinate order or Y-axis orientation
- **Solution**: Verify coordinate order matches: Top-Left, Top-Right, Bottom-Right, Bottom-Left

### Coordinates Don't Match Expected Location
- **Cause**: Wrong project coordinates or coordinate system
- **Solution**: Verify you're using the correct project URL and coordinate system

## Development Notes
- Based on `paul/joshscript_aframe/pic3.html` structure
- Maintains same rotation and positioning logic
- Uses real-world coordinates for accurate geolocation
- Supports both WGS84 and Mt Eden 2000 coordinate systems