# GeoJSON to A-Frame Converter (Silver)

This directory contains tools to convert floor plan viewer data to A-Frame cone_data.json format.

## Workflow

```
Floor Plan Viewer → GeoJSON Export → Coordinate Transform → cone_data.json → A-Frame
```

## Project Base Point

The coordinate transformation uses the following project base point:

- **Northing**: 808226.1590
- **Easting**: 397922.9125
- **Elevation**: 13.0000
- **Angle to True North**: 92.04°

## Usage

### Step 1: Export GeoJSON from Floor Plan Viewer

In the floor plan viewer browser console, run:

```javascript
exportCameraPositionsAsGeoJSON()
```

This will download a file like `camera_positions_2025-10-16.geojson`

### Step 2: Convert to cone_data.json

```bash
cd paul/joshscript_aframe7_silver
python geojson_to_cone_data.py
```

The script will:
1. Load the GeoJSON file
2. Transform Mt Eden 2000 coordinates to DXF local space
3. Calculate camera direction vectors
4. Generate cone_data.json

### Step 3: Use in A-Frame

Copy the generated `cone_data.json` to your A-Frame project directory.

## Coordinate Transformation

### Forward Transform (Survey → Model)
1. **Translate**: Subtract base point (origin to base point)
2. **Rotate**: Rotate by angle to true north (92.04°)
3. **Result**: Local DXF coordinates

### Inverse Transform (Model → Survey) - This Script
1. **Translate**: Subtract base point from Mt Eden coordinates
2. **Rotate**: Rotate by negative angle (-92.04°)
3. **Result**: Local DXF coordinates

## File Structure

- `geojson_to_cone_data.py` - Main converter script
- `camera_positions.geojson` - Input GeoJSON (from floor plan viewer)
- `cone_data.json` - Output A-Frame data
- `README.md` - This file

## Next Steps

After generating cone_data.json, you'll need:
1. Copy cone_data.json to your A-Frame project
2. Copy panorama images to the panoramas/ directory
3. Adjust image paths if needed
4. Test in A-Frame navigation system


