
// FIRST FLOOR COORDINATE EXTRACTION SCRIPT
// Run this in the browser console on: https://projects.asbuiltvault.com/asset/26cea261-340c-440e-ab72-793c42eb6f1f/plan-viewer/3427e14c-ab69-46d2-94bb-115cc3811995/

console.log("=== FIRST FLOOR COORDINATE EXTRACTION ===");

// Step 1: Find the map element
const mapElement = document.querySelector('#map_show, .mapboxgl-map, [class*="mapbox"]');
console.log('Map element found:', mapElement);

if (!mapElement) {
    console.error('❌ Map element not found! Make sure the page is fully loaded.');
    throw new Error('Map element not found');
}

// Step 2: Access React Fiber
const fiberKeys = Object.keys(mapElement).filter(key => key.startsWith('__reactFiber'));
console.log('Available React Fiber keys:', fiberKeys);

const fiber = mapElement[fiberKeys[0]];
console.log('React Fiber found:', fiber);

if (!fiber) {
    console.error('❌ React Fiber not found!');
    throw new Error('React Fiber not found');
}

// Step 3: Search for map instance in the fiber tree
function findMapInFiber(fiber, depth = 0) {
    if (depth > 15) return null; // Prevent infinite recursion
    
    // Check if this fiber has a map instance
    if (fiber && fiber.memoizedProps && fiber.memoizedProps.map) {
        console.log('✅ Found map in fiber at depth', depth, ':', fiber.memoizedProps.map);
        return fiber.memoizedProps.map;
    }
    
    // Check if this fiber has a map instance in state
    if (fiber && fiber.memoizedState && fiber.memoizedState.map) {
        console.log('✅ Found map in state at depth', depth, ':', fiber.memoizedState.map);
        return fiber.memoizedState.map;
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

const mapInstanceWrapper = findMapInFiber(fiber);
console.log('Map instance wrapper found:', mapInstanceWrapper);

if (!mapInstanceWrapper) {
    console.error('❌ Map instance wrapper not found!');
    throw new Error('Map instance wrapper not found');
}

// Step 4: Extract the actual Map instance from the wrapper
const mapInstance = mapInstanceWrapper.current;
console.log('Actual Map instance:', mapInstance);

if (!mapInstance) {
    console.error('❌ Map instance not found in wrapper!');
    throw new Error('Map instance not found in wrapper');
}

// Step 5: Get map style and sources
const style = mapInstance.getStyle();
console.log('Map style sources:', Object.keys(style.sources));

// Step 6: Find the floor plan image source
const imageSources = Object.keys(style.sources).filter(key => key.includes('image-source'));
console.log('Image sources found:', imageSources);

if (imageSources.length === 0) {
    console.error('❌ No image sources found!');
    throw new Error('No image sources found');
}

// Step 7: Extract coordinates from the first image source
const imageSourceKey = imageSources[0];
const imageSource = style.sources[imageSourceKey];
console.log('Image source:', imageSource);

if (!imageSource.coordinates) {
    console.error('❌ No coordinates found in image source!');
    throw new Error('No coordinates found in image source');
}

const coordinates = imageSource.coordinates;
console.log('=== FIRST FLOOR COORDINATES ===');
console.log(JSON.stringify(coordinates, null, 2));

// Step 8: Create the JSON file content
const jsonContent = {
    "project": "First Floor",
    "url": "https://projects.asbuiltvault.com/asset/26cea261-340c-440e-ab72-793c42eb6f1f/plan-viewer/3427e14c-ab69-46d2-94bb-115cc3811995/",
    "floorplan_bounds": coordinates,
    "corners": {
        "topLeft": coordinates[0],
        "topRight": coordinates[1],
        "bottomRight": coordinates[2],
        "bottomLeft": coordinates[3]
    },
    "extraction_date": new Date().toISOString()
};

console.log('=== JSON CONTENT TO SAVE ===');
console.log(JSON.stringify(jsonContent, null, 2));

// Step 9: Copy to clipboard (if available)
if (navigator.clipboard) {
    navigator.clipboard.writeText(JSON.stringify(jsonContent, null, 2)).then(() => {
        console.log('✅ Coordinates copied to clipboard!');
    });
} else {
    console.log('📋 Copy the JSON content above and save it to: first_floor_coordinates.json');
}

console.log('=== EXTRACTION COMPLETE ===');
