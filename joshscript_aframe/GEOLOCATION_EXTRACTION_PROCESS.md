# Geolocation Data Extraction Process

## Overview
This document describes the process used to extract geolocation data (WGS84 coordinates) from the asBuilt Vault project page for the floorplan image.

## Target URL
```
https://projects.asbuiltvault.com/asset/80cfe870-052d-4950-acae-686987bbf64c/plan-viewer/0ccb51e7-753c-4dd1-9518-11353c54e0d5/
```

## Process Steps

### 1. Initial Investigation
- Used browser developer tools to inspect the page
- Found Mapbox GL JS implementation with map container `#map_show`
- Identified React-based architecture using React Fiber

### 2. Network Analysis
- Downloaded HAR file from Network tab
- Analyzed API calls but found no explicit coordinate data in network requests
- Found Mapbox access token and default coordinates (not project-specific)

### 3. Browser Console Investigation
- Used multiple console scripts to search for coordinate data
- Searched for global variables containing coordinate information
- Found user location data in sessionStorage but not project coordinates

### 4. React Fiber Analysis
- Accessed React Fiber properties on the map element
- Found map instance in `fiber.return.memoizedProps.map.current`
- Successfully extracted the Mapbox Map object

### 5. Map Instance Data Extraction
- Used `mapInstance.getStyle()` to access map sources
- Found three key sources:
  - `composite`: Mapbox base map data
  - `points`: 610 feature points (markers)
  - `0ccb51e7-753c-4dd1-9518-11353c54e0d5-image-source`: Floorplan image with coordinates

### 6. Coordinate Data Extraction
- Extracted floorplan image bounds from image source coordinates
- Used first 3 points from points source as reference points
- All coordinates are in WGS84 format (longitude, latitude)

## Key Console Scripts Used

### 1. Initial Map Search
```javascript
// Look for Mapbox map instance
const mapSelectors = ['#map_show', '.mapboxgl-map', '[class*="mapbox"]', '#mapDiv'];
mapSelectors.forEach(selector => {
    const element = document.querySelector(selector);
    if (element) {
        console.log(`Found element with selector "${selector}":`, element);
    }
});
```

### 2. React Fiber Analysis
```javascript
// Access React Fiber properties
const mapElement = document.getElementById('map_show');
const fiber = mapElement.__reactFiber$26742qmob3b;
console.log('React Fiber found:', fiber);
```

### 3. Map Instance Extraction
```javascript
// Extract map instance from React Fiber
const mapInstance = fiber.return.memoizedProps.map.current;
console.log('Map instance:', mapInstance);
```

### 4. Coordinate Data Extraction
```javascript
// Get map style and sources
const style = mapInstance.getStyle();
const imageSource = style.sources['0ccb51e7-753c-4dd1-9518-11353c54e0d5-image-source'];
const pointsSource = style.sources['points'];

// Extract coordinates
console.log('Floorplan bounds:', imageSource.coordinates);
console.log('Reference points:', pointsSource.data.features.slice(0, 3));
```

## Extracted Data

### Floorplan Image Bounds (WGS84)
```json
[
  [174.76904030579692, -36.845437470625626],  // Top-left
  [174.76953833830476, -36.84556978976499],   // Top-right
  [174.76945222065177, -36.84577937864095],   // Bottom-right
  [174.76895418814394, -36.84564705950159]    // Bottom-left
]
```

### Reference Points (WGS84)
```json
[
  {
    "coordinates": [174.76925647074228, -36.84554398060178],
    "properties": {
      "id": "a33d49c4-fe00-41ee-a10b-38172ec7b549",
      "name": "L10_3_60",
      "colour": "#009247"
    }
  },
  {
    "coordinates": [174.76921081300972, -36.845569620599406],
    "properties": {
      "id": "17e28b48-9c2d-48fd-9a57-189a5d83f2b0",
      "name": "L10_3_49",
      "colour": "#009247"
    }
  },
  {
    "coordinates": [174.76928719941384, -36.84561806489802],
    "properties": {
      "id": "ef6fe1d1-e283-4b3d-b8db-addcca29167e",
      "name": "L10_3_134",
      "colour": "#009247"
    }
  }
]
```

## Location Information
- **City**: Auckland, New Zealand
- **Coordinates**: ~174.77°E, -36.85°S
- **Coordinate System**: WGS84 (EPSG:4326)

## Technical Notes

### Mapbox GL JS Implementation
- The project uses Mapbox GL JS for interactive mapping
- Map instance is stored in React state via useRef hook
- Image source uses Mapbox's image overlay feature with geographic bounds

### Data Structure
- Floorplan image is overlaid using 4 corner coordinates
- 610 marker points are stored as GeoJSON features
- All coordinates are in [longitude, latitude] format (WGS84)

### Browser Compatibility
- Process requires modern browser with React DevTools
- Console access needed for React Fiber inspection
- Mapbox GL JS must be loaded and initialized

## Files Created
- `paul/joshscript_aframe/reference_materials/projects.asbuiltvault.com.har` - Network traffic capture
- `paul/joshscript_aframe/GEOLOCATION_EXTRACTION_PROCESS.md` - This documentation

## Next Steps
1. Integrate coordinate data into pic2.html floorplan viewer
2. Create coordinate transformation system (pixel ↔ WGS84)
3. Add reference point overlay functionality
4. Implement click-to-get-coordinates feature

## Date
January 8, 2025
