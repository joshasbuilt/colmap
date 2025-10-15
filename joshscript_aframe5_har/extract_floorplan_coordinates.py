#!/usr/bin/env python3
"""
Extract precise floor plan coordinates from HAR files.
"""

import json
import re
from pathlib import Path

def extract_floorplan_coordinates(har_path):
    """Extract floor plan coordinates from a HAR file."""
    print(f"\nProcessing: {har_path.name}")
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    floorplan_data = {
        'application_data': None,
        'coordinates': {},
        'map_data': {},
        'raw_responses': []
    }
    
    # Look for the specific application API response
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        
        # Look for the application-specific API call
        if 'api/vault/asset' in url and 'application' in url:
            content = response.get('content', {})
            text = content.get('text', '')
            
            if text:
                try:
                    api_data = json.loads(text)
                    floorplan_data['raw_responses'].append({
                        'url': url,
                        'data': api_data
                    })
                    
                    # Extract application data
                    if 'data' in api_data and 'data' in api_data['data']:
                        app_data = api_data['data']['data']
                        
                        floorplan_data['application_data'] = {
                            'id': app_data.get('id'),
                            'name': app_data.get('name'),
                            'type': app_data.get('type'),
                            'map_file_name': app_data.get('map_file_name'),
                            'latitude': app_data.get('latitude'),
                            'longitude': app_data.get('longitude'),
                            'map_location': app_data.get('map_location')
                        }
                        
                        print(f"  Found application data:")
                        print(f"    Name: {app_data.get('name')}")
                        print(f"    File: {app_data.get('map_file_name')}")
                        print(f"    Lat: {app_data.get('latitude')}")
                        print(f"    Lng: {app_data.get('longitude')}")
                        print(f"    Location: {app_data.get('map_location')}")
                        
                        # Store coordinates
                        floorplan_data['coordinates'] = {
                            'latitude': app_data.get('latitude'),
                            'longitude': app_data.get('longitude')
                        }
                        
                except Exception as e:
                    print(f"  Error parsing API response: {e}")
    
    # Look for any other coordinate-related data
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        
        if 'projects.asbuiltvault.com' in url:
            content = response.get('content', {})
            text = content.get('text', '')
            
            if text and ('lat' in text.lower() or 'lng' in text.lower() or 'coordinate' in text.lower()):
                try:
                    data = json.loads(text)
                    # Search for coordinate patterns
                    coord_patterns = find_coordinate_patterns(data)
                    if coord_patterns:
                        floorplan_data['map_data'][url] = coord_patterns
                except:
                    pass
    
    return floorplan_data

def find_coordinate_patterns(data, path=""):
    """Recursively find coordinate patterns in JSON data."""
    patterns = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Look for coordinate-like values
            if key.lower() in ['lat', 'latitude', 'lng', 'longitude', 'x', 'y', 'easting', 'northing']:
                if isinstance(value, (int, float)) and abs(value) > 0:
                    patterns.append({
                        'path': current_path,
                        'key': key,
                        'value': value
                    })
            
            # Recursively search nested objects
            if isinstance(value, (dict, list)):
                patterns.extend(find_coordinate_patterns(value, current_path))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            if isinstance(item, (dict, list)):
                patterns.extend(find_coordinate_patterns(item, current_path))
    
    return patterns

def main():
    script_dir = Path(__file__).parent
    har_files_dir = script_dir / 'har_files'
    output_dir = script_dir / 'floorplan_coordinates'
    output_dir.mkdir(exist_ok=True)
    
    har_files = list(har_files_dir.glob('*.har'))
    
    print(f"Found {len(har_files)} HAR files")
    
    all_coordinates = {}
    
    for har_file in har_files:
        floor_name = har_file.stem.replace('projects.asbuiltvault.com_', '')
        data = extract_floorplan_coordinates(har_file)
        all_coordinates[floor_name] = data
        
        # Save individual floor data
        output_file = output_dir / f'{floor_name}_coordinates.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved to: {output_file}")
    
    # Save combined data
    combined_file = output_dir / 'all_floors_coordinates.json'
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_coordinates, f, indent=2)
    print(f"\nSaved combined data to: {combined_file}")
    
    # Print summary
    print("\n=== FLOOR PLAN COORDINATES SUMMARY ===")
    for floor_name, data in all_coordinates.items():
        print(f"\n{floor_name}:")
        if data['application_data']:
            app = data['application_data']
            print(f"  Application: {app['name']}")
            print(f"  File: {app['map_file_name']}")
            print(f"  Coordinates: Lat={app['latitude']}, Lng={app['longitude']}")
            print(f"  Location: {app['map_location']}")
        else:
            print(f"  No application data found")
        
        if data['coordinates']:
            coords = data['coordinates']
            print(f"  Raw coordinates: Lat={coords['latitude']}, Lng={coords['longitude']}")
        
        if data['map_data']:
            print(f"  Additional coordinate data: {len(data['map_data'])} sources")

if __name__ == '__main__':
    main()
