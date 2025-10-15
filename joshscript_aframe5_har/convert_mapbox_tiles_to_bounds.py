#!/usr/bin/env python3
"""
Convert Mapbox tile coordinates to WGS84 bounds
"""

import json
import math

def tile_to_lng_lat(x, y, z):
    """Convert Mapbox tile coordinates to longitude/latitude"""
    n = 2.0 ** z
    lng = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lng, lat

def get_tile_bounds(x, y, z):
    """Get the bounds of a Mapbox tile in WGS84 coordinates"""
    # Top-left corner
    lng1, lat1 = tile_to_lng_lat(x, y, z)
    # Bottom-right corner  
    lng2, lat2 = tile_to_lng_lat(x + 1, y + 1, z)
    
    return {
        'min_lng': lng1,
        'max_lng': lng2,
        'min_lat': lat2,  # Note: lat2 is smaller (more south)
        'max_lat': lat1   # Note: lat1 is larger (more north)
    }

def main():
    # Load the floor plan data
    with open('floorplan_data/GroundFloor_data.json', 'r') as f:
        data = json.load(f)
    
    print("=== MAPBOX TILE ANALYSIS ===")
    print(f"Floor plan URL: {data['floorplan_url']}")
    print()
    
    # Analyze each zoom level
    zoom_levels = {}
    for tile in data['mapbox_data']:
        z = tile['z']
        x = tile['x']
        y = tile['y']
        
        if z not in zoom_levels:
            zoom_levels[z] = []
        zoom_levels[z].append((x, y))
    
    # Convert tiles to bounds
    all_bounds = []
    for z, tiles in zoom_levels.items():
        print(f"Zoom Level {z}:")
        for x, y in tiles:
            bounds = get_tile_bounds(x, y, z)
            all_bounds.append(bounds)
            print(f"  Tile {x},{y}: {bounds['min_lng']:.6f}, {bounds['min_lat']:.6f} to {bounds['max_lng']:.6f}, {bounds['max_lat']:.6f}")
        print()
    
    # Find the bounds from the highest zoom level (most detailed)
    if all_bounds:
        # Get only zoom level 14 tiles (highest detail)
        zoom_14_tiles = [tile for tile in data['mapbox_data'] if tile['z'] == 14]
        zoom_14_bounds = [get_tile_bounds(tile['x'], tile['y'], tile['z']) for tile in zoom_14_tiles]
        
        if zoom_14_bounds:
            min_lng = min(b['min_lng'] for b in zoom_14_bounds)
            max_lng = max(b['max_lng'] for b in zoom_14_bounds)
            min_lat = min(b['min_lat'] for b in zoom_14_bounds)
            max_lat = max(b['max_lat'] for b in zoom_14_bounds)
            
            print("=== ZOOM 14 BOUNDS (HIGHEST DETAIL) ===")
            print(f"Min Lng: {min_lng:.6f}")
            print(f"Max Lng: {max_lng:.6f}")
            print(f"Min Lat: {min_lat:.6f}")
            print(f"Max Lat: {max_lat:.6f}")
            print()
        else:
            # Fallback to overall bounds
            min_lng = min(b['min_lng'] for b in all_bounds)
            max_lng = max(b['max_lng'] for b in all_bounds)
            min_lat = min(b['min_lat'] for b in all_bounds)
            max_lat = max(b['max_lat'] for b in all_bounds)
            
            print("=== OVERALL BOUNDS (FALLBACK) ===")
            print(f"Min Lng: {min_lng:.6f}")
            print(f"Max Lng: {max_lng:.6f}")
            print(f"Min Lat: {min_lat:.6f}")
            print(f"Max Lat: {max_lat:.6f}")
            print()
        
        # Create 4 corner coordinates
        corners = [
            [min_lng, max_lat],  # Top-Left
            [max_lng, max_lat],  # Top-Right
            [max_lng, min_lat],  # Bottom-Right
            [min_lng, min_lat]   # Bottom-Left
        ]
        
        print("=== FLOOR PLAN CORNERS (WGS84) ===")
        corner_names = ['Top-Left', 'Top-Right', 'Bottom-Right', 'Bottom-Left']
        for i, (lng, lat) in enumerate(corners):
            print(f"{corner_names[i]}: [{lng:.6f}, {lat:.6f}]")
        
        # Save the bounds
        bounds_data = {
            'floorplan_bounds': corners,
            'corners': {
                'topLeft': corners[0],
                'topRight': corners[1],
                'bottomRight': corners[2],
                'bottomLeft': corners[3]
            },
            'bounds': {
                'min_lng': min_lng,
                'max_lng': max_lng,
                'min_lat': min_lat,
                'max_lat': max_lat
            }
        }
        
        with open('mapbox_floorplan_bounds.json', 'w') as f:
            json.dump(bounds_data, f, indent=2)
        
        print(f"\nBounds saved to: mapbox_floorplan_bounds.json")

if __name__ == "__main__":
    main()
