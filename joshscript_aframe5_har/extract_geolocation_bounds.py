#!/usr/bin/env python3
"""
Extract geolocation bounds from HAR files for floor plans.
"""

import json
import re
from pathlib import Path

def extract_geolocation_from_har(har_path):
    """Extract geolocation bounds from a HAR file."""
    print(f"\nProcessing: {har_path.name}")
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    geolocation_data = {
        'floorplan_bounds': None,
        'mapbox_bounds': None,
        'api_responses': [],
        'coordinate_data': []
    }
    
    # Look for API responses that might contain coordinate data
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        
        # Check for AsBuiltVault API responses
        if 'projects.asbuiltvault.com/api' in url:
            content = response.get('content', {})
            text = content.get('text', '')
            
            if text:
                try:
                    api_data = json.loads(text)
                    geolocation_data['api_responses'].append({
                        'url': url,
                        'data': api_data
                    })
                    print(f"  Found API response: {url}")
                except:
                    pass
        
        # Look for Mapbox tile requests to infer bounds
        if 'api.mapbox.com' in url and '.vector.pbf' in url:
            match = re.search(r'/(\d+)/(\d+)/(\d+)\.vector\.pbf', url)
            if match:
                z, x, y = match.groups()
                geolocation_data['coordinate_data'].append({
                    'z': int(z),
                    'x': int(x),
                    'y': int(y),
                    'url': url
                })
    
    # Try to extract bounds from Mapbox tiles
    if geolocation_data['coordinate_data']:
        tiles = geolocation_data['coordinate_data']
        z_values = [t['z'] for t in tiles]
        x_values = [t['x'] for t in tiles]
        y_values = [t['y'] for t in tiles]
        
        if z_values:
            max_z = max(z_values)
            # Filter tiles at the highest zoom level
            high_zoom_tiles = [t for t in tiles if t['z'] == max_z]
            
            if high_zoom_tiles:
                min_x = min(t['x'] for t in high_zoom_tiles)
                max_x = max(t['x'] for t in high_zoom_tiles)
                min_y = min(t['y'] for t in high_zoom_tiles)
                max_y = max(t['y'] for t in high_zoom_tiles)
                
                # Convert tile coordinates to lat/lng bounds
                # This is a rough approximation
                n = 2 ** max_z
                lng_min = (min_x / n) * 360.0 - 180.0
                lng_max = ((max_x + 1) / n) * 360.0 - 180.0
                lat_max = 180.0 / 3.14159 * (2 * 3.14159 * (1 - min_y / n) - 3.14159)
                lat_min = 180.0 / 3.14159 * (2 * 3.14159 * (1 - (max_y + 1) / n) - 3.14159)
                
                geolocation_data['mapbox_bounds'] = {
                    'zoom': max_z,
                    'tile_bounds': {
                        'min_x': min_x, 'max_x': max_x,
                        'min_y': min_y, 'max_y': max_y
                    },
                    'geo_bounds': {
                        'lng_min': lng_min, 'lng_max': lng_max,
                        'lat_min': lat_min, 'lat_max': lat_max
                    }
                }
                
                print(f"  Mapbox bounds (zoom {max_z}):")
                print(f"    Lng: {lng_min:.6f} to {lng_max:.6f}")
                print(f"    Lat: {lat_min:.6f} to {lat_max:.6f}")
    
    return geolocation_data

def main():
    script_dir = Path(__file__).parent
    har_files_dir = script_dir / 'har_files'
    output_dir = script_dir / 'geolocation_data'
    output_dir.mkdir(exist_ok=True)
    
    har_files = list(har_files_dir.glob('*.har'))
    
    print(f"Found {len(har_files)} HAR files")
    
    all_geolocation = {}
    
    for har_file in har_files:
        floor_name = har_file.stem.replace('projects.asbuiltvault.com_', '')
        data = extract_geolocation_from_har(har_file)
        all_geolocation[floor_name] = data
        
        # Save individual floor data
        output_file = output_dir / f'{floor_name}_geolocation.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved to: {output_file}")
    
    # Save combined data
    combined_file = output_dir / 'all_floors_geolocation.json'
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_geolocation, f, indent=2)
    print(f"\nSaved combined data to: {combined_file}")
    
    # Print summary
    print("\n=== GEOLOCATION EXTRACTION SUMMARY ===")
    for floor_name, data in all_geolocation.items():
        print(f"\n{floor_name}:")
        print(f"  API responses: {len(data['api_responses'])}")
        print(f"  Mapbox tiles: {len(data['coordinate_data'])}")
        if data['mapbox_bounds']:
            bounds = data['mapbox_bounds']['geo_bounds']
            print(f"  Estimated bounds:")
            print(f"    Lng: {bounds['lng_min']:.6f} to {bounds['lng_max']:.6f}")
            print(f"    Lat: {bounds['lat_min']:.6f} to {bounds['lat_max']:.6f}")

if __name__ == '__main__':
    main()


