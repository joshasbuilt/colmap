#!/usr/bin/env python3
"""
Debug the PROJECT_BASE_POINT transformation
Compare coordinates before and after transformation
"""

import json
import math
from pathlib import Path

# Project Base Point Configuration
PROJECT_BASE_POINT = {
    'northing': 808226.1590,
    'easting': 397922.9125,
    'elevation': 13.0000,
    'angle_to_true_north': 92.04  # degrees
}

def debug_transformation():
    """Debug the transformation with sample points"""
    
    # Load the GeoJSON
    geojson_path = Path('camera_positions_2025-10-19 (12).geojson')
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    # Get first 5 points for debugging
    sample_points = []
    for i, feature in enumerate(data['features'][:5]):
        if feature['geometry']['type'] == 'Point':
            props = feature['properties']
            
            # Parse 3D coordinates
            coords3d_str = props.get('coords3D', '')
            import re
            match = re.search(r'3D: \(([^,]+), ([^,]+), ([^)]+)\)', coords3d_str)
            if match:
                x = float(match.group(1))
                y = float(match.group(2))
                z = float(match.group(3))
                
                sample_points.append({
                    'frame': props.get('frame', 'unknown'),
                    'group': props.get('group', 'unknown'),
                    'x': x,
                    'y': y,
                    'z': z,
                    'easting': props.get('easting', 0),
                    'northing': props.get('northing', 0)
                })
    
    print("=== DEBUGGING TRANSFORMATION ===")
    print(f"Base Point: Easting={PROJECT_BASE_POINT['easting']}, Northing={PROJECT_BASE_POINT['northing']}")
    print(f"Rotation Angle: {PROJECT_BASE_POINT['angle_to_true_north']}°")
    print()
    
    # Convert angle to radians
    rotation_rad = math.radians(PROJECT_BASE_POINT['angle_to_true_north'])
    
    for point in sample_points:
        print(f"Frame {point['frame']} ({point['group']}):")
        print(f"  Original 3D: ({point['x']:.3f}, {point['y']:.3f}, {point['z']:.3f})")
        print(f"  Mt Eden: ({point['easting']:.3f}, {point['northing']:.3f})")
        
        # Apply transformation
        delta_e = point['easting'] - PROJECT_BASE_POINT['easting']
        delta_n = point['northing'] - PROJECT_BASE_POINT['northing']
        delta_z = point['z']  # Keep Z as is
        
        # Rotate by negative angle
        cos_theta = math.cos(-rotation_rad)
        sin_theta = math.sin(-rotation_rad)
        
        x = delta_e * cos_theta - delta_n * sin_theta
        y = delta_e * sin_theta + delta_n * cos_theta
        z = delta_z
        
        print(f"  DXF Result: ({x:.3f}, {y:.3f}, {z:.3f})")
        print(f"  Delta from base: E={delta_e:.3f}, N={delta_n:.3f}")
        print(f"  Rotation: cos={cos_theta:.3f}, sin={sin_theta:.3f}")
        print()

if __name__ == "__main__":
    debug_transformation()

