# Coordinate Extraction Guide (joshscript_aframe5_har)

## Overview
This guide documents the process for extracting floor plan coordinates from asBuilt Vault projects using HAR files and browser console techniques.

## The Problem We Solved
- **Initial Issue**: Floor plan appeared orthogonal (rectangular) instead of rotated
- **Root Cause**: Using coordinate extents from HAR files instead of actual floor plan corners
- **Solution**: Extract coordinates directly from the Mapbox map instance using React Fiber

## Quick Start for Next Project

### 1. Capture HAR File
1. Open the floor plan project in browser
2. Open Developer Tools (F12) → Network tab
3. Refresh the page to capture all requests
4. Right-click → "Save all as HAR with content"
5. Save as `projects.asbuiltvault.com_[ProjectName].har`

### 2. Extract Project URL from HAR
```bash
cd paul/joshscript_aframe5_har
python extract_ground_floor_coordinates.py
```
This creates extraction scripts for the project found in the HAR file.

### 3. Extract Coordinates from Browser
1. Open `ground_floor_extraction_helper.html` in browser
2. Click the project URL to open the floor plan
3. Wait for floor plan to load completely
4. Open Developer Console (F12)
5. Copy and paste the extraction script
6. Copy the coordinates from the output

### 4. Update Floor Plan Viewer
Update `paul/joshscript_aframe6_floorplanbase/floor_plan_viewer.html` with the extracted coordinates.

## Detailed Process

### Step 1: HAR File Analysis
The HAR file contains the actual project URL, not the coordinate data:
```json
{
  "request": {
    "url": "https://projects.asbuiltvault.com/asset/[ASSET_ID]/plan-viewer/[PLAN_ID]/"
  }
}
```

### Step 2: Browser Console Extraction
Use React Fiber to access the Mapbox map instance:

```javascript
// Find map element
const mapElement = document.querySelector('#map_show, .mapboxgl-map, [class*="mapbox"]');

// Access React Fiber
const fiberKeys = Object.keys(mapElement).filter(key => key.startsWith('__reactFiber'));
const fiber = mapElement[fiberKeys[0]];

// Find map instance in fiber tree
function findMapInFiber(fiber, depth = 0) {
    if (depth > 15) return null;
    
    if (fiber && fiber.memoizedProps && fiber.memoizedProps.map) {
        return fiber.memoizedProps.map;
    }
    
    // Search in return, child, and sibling
    const searchPaths = [fiber.return, fiber.child, fiber.sibling];
    for (const path of searchPaths) {
        if (path) {
            const result = findMapInFiber(path, depth + 1);
            if (result) return result;
        }
    }
    return null;
}

// Extract coordinates
const mapInstanceWrapper = findMapInFiber(fiber);
const mapInstance = mapInstanceWrapper.current; // Key: access .current property
const style = mapInstance.getStyle();
const imageSources = Object.keys(style.sources).filter(key => key.includes('image-source'));
const coordinates = style.sources[imageSources[0]].coordinates;
```

### Step 3: Coordinate Format
The extracted coordinates are in WGS84 format (longitude, latitude):
```json
[
  [174.74069378281493, -36.80542933064474],   // Top-Left
  [174.7412528239626, -36.805448062383675],   // Top-Right
  [174.74123108024065, -36.80581545281087],   // Bottom-Right
  [174.74067203909297, -36.80579672107194]    // Bottom-Left
]
```

## Common Issues and Solutions

### Issue: "Cannot read properties of undefined (reading 'memoizedProps')"
**Cause**: React Fiber structure is different than expected
**Solution**: Use the search function to find the map instance in the fiber tree

### Issue: "mapInstance.getStyle is not a function"
**Cause**: Map instance is wrapped in a React ref object
**Solution**: Access `mapInstance.current` instead of `mapInstance` directly

### Issue: "No image sources found"
**Cause**: Floor plan hasn't loaded completely
**Solution**: Wait for the floor plan to fully load before running the script

### Issue: Floor plan appears orthogonal
**Cause**: Using coordinate extents instead of actual floor plan corners
**Solution**: Extract coordinates from the Mapbox map instance, not from HAR file data

## Files Created
- `extract_ground_floor_coordinates.py`: Creates extraction scripts from HAR file
- `ground_floor_extraction_helper.html`: Browser helper for coordinate extraction
- `ground_floor_extraction_script.js`: Console script for coordinate extraction
- `ground_floor_coordinates.json`: Extracted coordinates in JSON format

## Why This Process Works
1. **HAR files don't contain coordinate data** - they only have the project URL
2. **Mapbox stores coordinates in the map instance** - accessible via React Fiber
3. **React Fiber provides access to component state** - including the map instance
4. **Map instance contains the actual floor plan bounds** - not just coordinate extents

## Next Project Checklist
- [ ] Capture HAR file from project page
- [ ] Extract project URL from HAR file
- [ ] Create extraction scripts using `extract_ground_floor_coordinates.py`
- [ ] Run extraction in browser console
- [ ] Save coordinates to JSON file
- [ ] Update floor plan viewer with new coordinates
- [ ] Test floor plan display (should be rotated, not orthogonal)

## Time Saved
This process reduces coordinate extraction from **hours of trial and error** to **5-10 minutes** for future projects.

