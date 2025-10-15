#!/usr/bin/env python3
"""
Extract floor plan coordinates from browser using the process from GEOLOCATION_EXTRACTION_PROCESS.md
"""

import json
import webbrowser
import time
import os

def main():
    # Load the Ground Floor HAR data to get the floor plan URL
    with open('har_files/projects.asbuiltvault.com_GroundFloor.har', 'r') as f:
        har_data = json.load(f)
    
    # Find the floor plan URL from the HAR data
    floorplan_url = None
    for entry in har_data['log']['entries']:
        if 'response' in entry and 'content' in entry['response']:
            content = entry['response']['content']
            if 'mimeType' in content and 'image' in content['mimeType']:
                if 'text' in content and 'vaultprojectswebprod.blob.core.windows.net' in content['text']:
                    floorplan_url = entry['request']['url']
                    break
    
    if not floorplan_url:
        print("❌ Could not find floor plan URL in HAR file")
        return
    
    print("=== FLOOR PLAN COORDINATE EXTRACTION ===")
    print(f"Floor plan URL: {floorplan_url}")
    print()
    
    # Create the browser extraction instructions
    instructions = f"""
=== BROWSER COORDINATE EXTRACTION INSTRUCTIONS ===

1. Open this URL in your browser:
   {floorplan_url}

2. Wait for the floor plan to load completely

3. Open Developer Console (F12)

4. Run these console commands (one by one):

   // Step 1: Find the map element
   const mapElement = document.querySelector('#map_show, .mapboxgl-map, [class*="mapbox"]');
   console.log('Map element found:', mapElement);

   // Step 2: Access React Fiber
   const fiber = mapElement.__reactFiber$26742qmob3b || 
                 mapElement._reactInternalFiber ||
                 Object.keys(mapElement).find(key => key.startsWith('__reactFiber'));
   console.log('React Fiber found:', fiber);

   // Step 3: Extract map instance
   const mapInstance = fiber.return.memoizedProps.map.current;
   console.log('Map instance:', mapInstance);

   // Step 4: Get map style and sources
   const style = mapInstance.getStyle();
   console.log('Map style sources:', Object.keys(style.sources));

   // Step 5: Find the floor plan image source
   const imageSources = Object.keys(style.sources).filter(key => key.includes('image-source'));
   console.log('Image sources found:', imageSources);

   // Step 6: Extract coordinates from the first image source
   const imageSourceKey = imageSources[0];
   const imageSource = style.sources[imageSourceKey];
   console.log('Floor plan bounds:', imageSource.coordinates);

   // Step 7: Copy the coordinates
   const coordinates = imageSource.coordinates;
   console.log('=== COORDINATES TO COPY ===');
   console.log(JSON.stringify(coordinates, null, 2));

5. Copy the coordinates from the console output

6. Save them to: extracted_coordinates.json
"""

    print(instructions)
    
    # Create a simple HTML file to help with the extraction
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Coordinate Extraction Helper</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .instructions {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .code {{ background: #000; color: #0f0; padding: 10px; border-radius: 3px; font-family: monospace; }}
        .url {{ background: #e6f3ff; padding: 10px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>Floor Plan Coordinate Extraction</h1>
    
    <div class="url">
        <strong>Floor Plan URL:</strong><br>
        <a href="{floorplan_url}" target="_blank">{floorplan_url}</a>
    </div>
    
    <div class="instructions">
        <h2>Steps:</h2>
        <ol>
            <li>Click the URL above to open the floor plan</li>
            <li>Wait for it to load completely</li>
            <li>Open Developer Console (F12)</li>
            <li>Run the console commands below</li>
            <li>Copy the coordinates from the output</li>
        </ol>
    </div>
    
    <h2>Console Commands:</h2>
    <div class="code">
// Step 1: Find the map element
const mapElement = document.querySelector('#map_show, .mapboxgl-map, [class*="mapbox"]');
console.log('Map element found:', mapElement);

// Step 2: Access React Fiber
const fiber = mapElement.__reactFiber$26742qmob3b || 
              mapElement._reactInternalFiber ||
              Object.keys(mapElement).find(key => key.startsWith('__reactFiber'));
console.log('React Fiber found:', fiber);

// Step 3: Extract map instance
const mapInstance = fiber.return.memoizedProps.map.current;
console.log('Map instance:', mapInstance);

// Step 4: Get map style and sources
const style = mapInstance.getStyle();
console.log('Map style sources:', Object.keys(style.sources));

// Step 5: Find the floor plan image source
const imageSources = Object.keys(style.sources).filter(key => key.includes('image-source'));
console.log('Image sources found:', imageSources);

// Step 6: Extract coordinates from the first image source
const imageSourceKey = imageSources[0];
const imageSource = style.sources[imageSourceKey];
console.log('Floor plan bounds:', imageSource.coordinates);

// Step 7: Copy the coordinates
const coordinates = imageSource.coordinates;
console.log('=== COORDINATES TO COPY ===');
console.log(JSON.stringify(coordinates, null, 2));
    </div>
</body>
</html>
"""
    
    with open('coordinate_extraction_helper.html', 'w') as f:
        f.write(html_content)
    
    print(f"📄 Helper HTML file created: coordinate_extraction_helper.html")
    print("🌐 Open this file in your browser to follow the extraction process")

if __name__ == "__main__":
    main()

