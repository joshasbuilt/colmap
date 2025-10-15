#!/usr/bin/env python3
"""
Extract the actual WGS84 map bounds from HAR files.
Looking for the map_url data in the application API response.
"""

import json
from pathlib import Path

def extract_map_bounds(har_path):
    """Extract map bounds from HAR file."""
    print(f"\nProcessing: {har_path.name}")
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    map_data = {
        'application': None,
        'points': [],
        'map_url': None,
        'coordinate_system': None
    }
    
    # Look for the application API response
    for entry in entries:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        # Check if this contains the map data
        if 'map_url' in text and 'f9dba6e1-98a8-458e-b9dc-5f67913f2872' in text:
            try:
                api_response = json.loads(text)
                application = api_response.get('data', {}).get('application', {})
                
                map_data['application'] = application
                map_data['map_url'] = application.get('map_url')
                map_data['coordinate_system'] = application.get('coordinate_system')
                
                # Extract points with coordinates
                points = application.get('points', [])
                for point in points:
                    if 'x' in point and 'y' in point:
                        map_data['points'].append({
                            'id': point.get('id'),
                            'x': point.get('x'),
                            'y': point.get('y'),
                            'z': point.get('z'),
                            'coordinate_system': point.get('coordinate_system', map_data['coordinate_system'])
                        })
                
                print(f"  Found application data:")
                print(f"    Map URL: {map_data['map_url']}")
                print(f"    Coordinate System: {map_data['coordinate_system']}")
                print(f"    Points: {len(map_data['points'])}")
                
                # Show first few points
                for i, pt in enumerate(map_data['points'][:3]):
                    print(f"    Point {i+1}: X={pt['x']}, Y={pt['y']}, Z={pt['z']}")
                
                break
                
            except Exception as e:
                print(f"  Error parsing application data: {e}")
    
    return map_data

def main():
    script_dir = Path(__file__).parent
    har_files_dir = script_dir / 'har_files'
    output_dir = script_dir / 'map_bounds_data'
    output_dir.mkdir(exist_ok=True)
    
    har_files = list(har_files_dir.glob('*.har'))
    
    print(f"Found {len(har_files)} HAR files")
    
    all_map_data = {}
    
    for har_file in har_files:
        floor_name = har_file.stem.replace('projects.asbuiltvault.com_', '')
        data = extract_map_bounds(har_file)
        all_map_data[floor_name] = data
        
        # Save individual floor data
        output_file = output_dir / f'{floor_name}_map_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved to: {output_file}")
    
    # Save combined data
    combined_file = output_dir / 'all_floors_map_data.json'
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_map_data, f, indent=2)
    print(f"\nSaved combined data to: {combined_file}")
    
    # Print summary
    print("\n=== MAP DATA SUMMARY ===")
    for floor_name, data in all_map_data.items():
        print(f"\n{floor_name}:")
        print(f"  Coordinate System: {data['coordinate_system']}")
        print(f"  Points: {len(data['points'])}")
        if data['points']:
            xs = [p['x'] for p in data['points']]
            ys = [p['y'] for p in data['points']]
            print(f"  X range: {min(xs):.2f} to {max(xs):.2f}")
            print(f"  Y range: {min(ys):.2f} to {max(ys):.2f}")

if __name__ == '__main__':
    main()

