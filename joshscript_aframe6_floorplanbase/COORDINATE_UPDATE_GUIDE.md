# Coordinate Update Guide

## Quick Reference
To update the floor plan viewer with new coordinates:

### 1. Extract Coordinates
Follow the process in `paul/joshscript_aframe5_har/COORDINATE_EXTRACTION_GUIDE.md`

### 2. Update Viewer
Edit `floor_plan_viewer.html` and update the `geolocationData.floorplanBounds` array:

```javascript
const geolocationData = {
    floorplanBounds: [
        [lng1, lat1],  // Top-Left
        [lng2, lat2],  // Top-Right  
        [lng3, lat3],  // Bottom-Right
        [lng4, lat4]   // Bottom-Left
    ]
};
```

### 3. Test
Refresh the browser to see the updated floor plan with new coordinates.

## Current Coordinates (Ground Floor)
```javascript
floorplanBounds: [
    [174.74069378281493, -36.80542933064474],   // Top-Left
    [174.7412528239626, -36.805448062383675],   // Top-Right
    [174.74123108024065, -36.80581545281087],   // Bottom-Right
    [174.74067203909297, -36.80579672107194]    // Bottom-Left
]
```

## Troubleshooting
- **Orthogonal display**: Wrong coordinates (using extents instead of corners)
- **Upside down**: Incorrect coordinate order
- **Wrong location**: Wrong project coordinates
