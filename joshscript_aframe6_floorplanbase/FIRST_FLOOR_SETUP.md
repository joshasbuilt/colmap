# First Floor Setup Instructions

## Current Status
✅ **Ground Floor**: Loaded with real coordinates  
⏳ **First Floor**: Ready for coordinate extraction  

## Next Steps

### 1. Extract First Floor Coordinates
1. Open: `paul/joshscript_aframe5_har/first_floor_extraction_helper.html`
2. Click the First Floor URL to open the project
3. Wait for floor plan to load completely
4. Open Developer Console (F12)
5. Copy and paste the extraction script
6. Copy the coordinates from the output

### 2. Update Floor Plan Viewer
Once you have the First Floor coordinates, update `floor_plan_viewer.html`:

```javascript
firstFloor: {
    name: "First Floor", 
    image: "floorplan_images/FirstFloor.png",
    bounds: [
        [lng1, lat1],  // Top-Left
        [lng2, lat2],  // Top-Right
        [lng3, lat3],  // Bottom-Right
        [lng4, lat4]   // Bottom-Left
    ]
}
```

### 3. Layer Control
Both floors will be loaded on top of each other. Use the context menu:
- **Right-click** on any object
- **Send to Back** to control which floor is visible
- Both floors have their own bounds polygon and corner labels

## Current Ground Floor Coordinates
```javascript
groundFloor: {
    bounds: [
        [174.74069378281493, -36.80542933064474],   // Top-Left
        [174.7412528239626, -36.805448062383675],   // Top-Right
        [174.74123108024065, -36.80581545281087],   // Bottom-Right
        [174.74067203909297, -36.80579672107194]    // Bottom-Left
    ]
}
```

## Files Ready
- `first_floor_extraction_helper.html` - Browser helper
- `first_floor_extraction_script.js` - Console script
- `floor_plan_viewer.html` - Updated to handle both floors
