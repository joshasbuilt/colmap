#!/usr/bin/env python3
"""
Convert EDENTM2000 coordinates to WGS84 for floor plan bounds.
"""

import json
from pathlib import Path
import pyproj

def convert_mt_eden_to_wgs84(easting, northing):
    """Convert Mt Eden 2000 (EPSG:2105) to WGS84 (EPSG:4326)."""
    # Define projections
    mt_eden = pyproj.Proj('EPSG:2105')
    wgs84 = pyproj.Proj('EPSG:4326')
    
    # Transform
    transformer = pyproj.Transformer.from_proj(mt_eden, wgs84, always_xy=True)
    lng, lat = transformer.transform(easting, northing)
    
    return [lng, lat]

def create_floor_plan_bounds(points):
    """Create 4-corner bounds from point cloud."""
    if not points:
        return None
    
    xs = [p['x'] for p in points]
    ys = [p['y'] for p in points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    print(f"  Mt Eden 2000 bounds:")
    print(f"    X (Easting): {min_x:.2f} to {max_x:.2f}")
    print(f"    Y (Northing): {min_y:.2f} to {max_y:.2f}")
    
    # Create 4 corners in Mt Eden 2000
    corners_mt_eden = {
        'topLeft': [min_x, max_y],
        'topRight': [max_x, max_y],
        'bottomRight': [max_x, min_y],
        'bottomLeft': [min_x, min_y]
    }
    
    # Convert each corner to WGS84
    corners_wgs84 = {}
    coordinates_wgs84 = []
    
    print(f"\n  WGS84 bounds:")
    for corner_name, (e, n) in corners_mt_eden.items():
        lng, lat = convert_mt_eden_to_wgs84(e, n)
        corners_wgs84[corner_name] = [lng, lat]
        coordinates_wgs84.append([lng, lat])
        print(f"    {corner_name}: [{lng:.14f}, {lat:.14f}]")
    
    return {
        'coordinates': coordinates_wgs84,
        'corners': corners_wgs84,
        'mt_eden_bounds': corners_mt_eden
    }

def main():
    script_dir = Path(__file__).parent
    input_dir = script_dir / 'map_bounds_data'
    output_dir = script_dir / 'wgs84_bounds'
    output_dir.mkdir(exist_ok=True)
    
    # Read the map data
    map_data_file = input_dir / 'all_floors_map_data.json'
    with open(map_data_file, 'r', encoding='utf-8') as f:
        all_map_data = json.load(f)
    
    all_bounds = {}
    
    for floor_name, data in all_map_data.items():
        print(f"\n{'='*60}")
        print(f"Processing: {floor_name}")
        print(f"{'='*60}")
        
        points = data.get('points', [])
        if not points:
            print(f"  No points found for {floor_name}")
            continue
        
        print(f"  Found {len(points)} points")
        
        bounds = create_floor_plan_bounds(points)
        
        if bounds:
            all_bounds[floor_name] = bounds
            
            # Save individual floor bounds
            output_file = output_dir / f'{floor_name}_wgs84_bounds.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(bounds, f, indent=2)
            print(f"\n  Saved to: {output_file}")
    
    # Save combined bounds
    combined_file = output_dir / 'all_floors_wgs84_bounds.json'
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_bounds, f, indent=2)
    print(f"\n{'='*60}")
    print(f"Saved combined bounds to: {combined_file}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

