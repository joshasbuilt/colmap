# Extract Floor Plan Coordinates from Browser Console

## Overview
The HAR files don't contain the floor plan coordinate bounds directly. We need to extract them from the live website using browser console, just like we did for the L10 project.

## Steps to Extract Coordinates

### 1. Open the Floor Plan Page
Navigate to one of these URLs in your browser:
- **First Floor**: `https://projects.asbuiltvault.com/asset/26cea261-340c-440e-ab72-793c42eb6f1f/plan-viewer/3427e14c-ab69-46d2-94bb-115cc3811995/`
- **Ground Floor**: `https://projects.asbuiltvault.com/asset/26cea261-340c-440e-ab72-793c42eb6f1f/plan-viewer/2773c270-1382-4c53-8aa1-8dd25b15a460/`

### 2. Open Developer Tools
- Press `F12` or right-click → "Inspect"
- Go to the **Console** tab

### 3. Find the Map Element
Run this command to find the Mapbox map:
```javascript
const mapElement = document.getElementById('map_show');
console.log('Map element found:', mapElement);
```

### 4. Access React Fiber
```javascript
// Find the React Fiber property (the key will be different)
const fiberKey = Object.keys(mapElement).find(key => key.startsWith('__reactFiber$'));
const fiber = mapElement[fiberKey];
console.log('React Fiber found:', fiber);
```

### 5. Extract Map Instance
```javascript
const mapInstance = fiber.return.memoizedProps.map.current;
console.log('Map instance:', mapInstance);
```

### 6. Get Map Style and Sources
```javascript
const style = mapInstance.getStyle();
console.log('Map style:', style);
console.log('Available sources:', Object.keys(style.sources));
```

### 7. Extract Floor Plan Coordinates
```javascript
// Find the image source (it will have a UUID in the name)
const imageSourceKey = Object.keys(style.sources).find(key => key.includes('-image-source'));
console.log('Image source key:', imageSourceKey);

const imageSource = style.sources[imageSourceKey];
console.log('Floor plan coordinates:', imageSource.coordinates);

// Format as JSON for easy copying
console.log(JSON.stringify(imageSource.coordinates, null, 2));
```

### 8. Alternative: All-in-One Script
Run this single command to extract everything:
```javascript
(function() {
    try {
        const mapElement = document.getElementById('map_show');
        const fiberKey = Object.keys(mapElement).find(key => key.startsWith('__reactFiber$'));
        const fiber = mapElement[fiberKey];
        const mapInstance = fiber.return.memoizedProps.map.current;
        const style = mapInstance.getStyle();
        const imageSourceKey = Object.keys(style.sources).find(key => key.includes('-image-source'));
        const imageSource = style.sources[imageSourceKey];
        
        console.log('=== FLOOR PLAN COORDINATES ===');
        console.log('Source ID:', imageSourceKey);
        console.log('Coordinates (WGS84):');
        console.log(JSON.stringify(imageSource.coordinates, null, 2));
        
        // Also save to clipboard if possible
        const coordsText = JSON.stringify(imageSource.coordinates, null, 2);
        navigator.clipboard.writeText(coordsText).then(() => {
            console.log('✓ Coordinates copied to clipboard!');
        }).catch(err => {
            console.log('Could not copy to clipboard:', err);
        });
        
        return imageSource.coordinates;
    } catch (error) {
        console.error('Error extracting coordinates:', error);
        console.log('Try running the steps individually');
    }
})();
```

## Expected Output Format

The coordinates should be in this format (4 corners):
```json
[
  [longitude, latitude],  // Top-left
  [longitude, latitude],  // Top-right
  [longitude, latitude],  // Bottom-right
  [longitude, latitude]   // Bottom-left
]
```

Example (from L10 project):
```json
[
  [174.76904030579692, -36.845437470625626],
  [174.76953833830476, -36.84556978976499],
  [174.76945222065177, -36.84577937864095],
  [174.76895418814394, -36.84564705950159]
]
```

## Troubleshooting

### If React Fiber key is different:
```javascript
// List all keys on the map element
Object.keys(document.getElementById('map_show')).forEach(key => console.log(key));
```

### If map instance is in a different location:
```javascript
// Try alternative paths
const fiber = mapElement[fiberKey];
console.log('Fiber return:', fiber.return);
console.log('Memoized props:', fiber.return.memoizedProps);
```

### If you can't find the image source:
```javascript
// List all sources
const style = mapInstance.getStyle();
Object.keys(style.sources).forEach(key => {
    console.log(key, style.sources[key].type);
});
```

## After Extraction

Once you have the coordinates:

1. Save them to a file: `FirstFloor_coordinates.json` or `GroundFloor_coordinates.json`

2. Update the floor plan viewer HTML:
   - Replace the `geolocationData.floorplanBounds` array with your extracted coordinates

3. The coordinates should be in Auckland area (~174.7°E, -36.8°S)

## Date
October 15, 2025



