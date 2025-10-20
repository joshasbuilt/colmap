#!/usr/bin/env python3
"""
Simple GeoJSON to Cone Data Converter
Converts the already-transformed GeoJSON from floor plan viewer to cone_data.json

The GeoJSON already contains the correct coordinates from our transformation,
so we just need to format it properly for Revit/A-Frame.
"""

import json
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


def load_geojson(filepath: Path) -> Dict:
    """Load GeoJSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def calculate_direction_vectors(positions: List[Tuple[float, float, float]]) -> List[Dict[str, Dict[str, float]]]:
    """
    Calculate forward and up direction vectors for each camera position
    
    Args:
        positions: List of (x, y, z) positions
        
    Returns:
        List of direction dictionaries with 'forward' and 'up' vectors
    """
    directions = []
    
    for i, (x, y, z) in enumerate(positions):
        # Calculate forward vector (direction to next camera)
        if i < len(positions) - 1:
            next_x, next_y, next_z = positions[i + 1]
            forward_x = next_x - x
            forward_y = next_y - y
            forward_z = next_z - z
        else:
            # For last camera, use direction from previous camera
            if i > 0:
                prev_x, prev_y, prev_z = positions[i - 1]
                forward_x = x - prev_x
                forward_y = y - prev_y
                forward_z = z - prev_z
            else:
                # Single camera case
                forward_x, forward_y, forward_z = 1.0, 0.0, 0.0
        
        # Normalize forward vector
        forward_length = math.sqrt(forward_x**2 + forward_y**2 + forward_z**2)
        if forward_length > 0:
            forward_x /= forward_length
            forward_y /= forward_length
            forward_z /= forward_length
        
        # Calculate up vector (perpendicular to forward, mostly vertical)
        # Use cross product of forward with vertical (0,0,1)
        up_x = -forward_y
        up_y = forward_x
        up_z = 0.0
        
        # Normalize up vector
        up_length = math.sqrt(up_x**2 + up_y**2 + up_z**2)
        if up_length > 0:
            up_x /= up_length
            up_y /= up_length
            up_z /= up_length
        
        directions.append({
            'forward': {'x': forward_x, 'y': forward_y, 'z': forward_z},
            'up': {'x': up_x, 'y': up_y, 'z': up_z}
        })
    
    return directions


def convert_geojson_to_cone_data(geojson_path: Path, output_path: Path, 
                                  panorama_dir: str = 'panoramas') -> Dict:
    """
    Convert GeoJSON to cone_data.json format
    
    Args:
        geojson_path: Path to input GeoJSON file
        output_path: Path to output cone_data.json file
        panorama_dir: Directory containing panorama images
        
    Returns:
        Dictionary containing the cone data
    """
    # Load GeoJSON
    geojson_data = load_geojson(geojson_path)
    
    # Apply rotational transform around origin (negative rotation)
    angle_to_true_north = 92.04 + 180  # degrees
    rotation_rad = math.radians(angle_to_true_north)  # Negative rotation
    cos_theta = math.cos(rotation_rad)
    sin_theta = math.sin(rotation_rad)
    
    # Extract camera positions from GeoJSON
    positions = []
    camera_data = []
    
    for i, feature in enumerate(geojson_data['features']):
        if feature['geometry']['type'] == 'Point':
            coords = feature['geometry']['coordinates']
            props = feature.get('properties', {})
            
            # Get the coordinates
            x, y, z = coords[0], coords[1], coords[2]
            
            # Apply rotation around origin
            rotated_x = x * cos_theta - y * sin_theta
            rotated_y = x * sin_theta + y * cos_theta
            # Add 0.5 m (500 mm) to elevation as requested
            rotated_z = z + 0.5
            
            positions.append((rotated_x, rotated_y, rotated_z))
            
            # Extract metadata
            camera_data.append({
                'cone_id': i + 1,
                'dxf_position': {'x': rotated_x, 'y': rotated_y, 'z': rotated_z},
                'camera_index': 1,  # Default camera index
                'frame_number': i,
                'image_path': f"{panorama_dir}/frame_{i:04d}.jpg",
                'metadata': {
                    'mt_eden_coords': {
                        'easting': props.get('easting', 0),
                        'northing': props.get('northing', 0),
                        'height': props.get('height', 0)
                    },
                    'original_image': props.get('frame', f'frame_{i:04d}'),
                    'camera_name': props.get('imageName', f'Camera {i+1}'),
                    'group': props.get('group', 'Unknown')
                }
            })
    
    # Calculate direction vectors
    directions = calculate_direction_vectors(positions)
    
    # Add directions to camera data
    for i, direction in enumerate(directions):
        camera_data[i]['direction'] = direction
    
    # Create cone data structure
    cone_data = {
        'export_info': {
            'timestamp': datetime.now().isoformat(),
            'total_cones': len(camera_data),
            'camera_index_used': 1,
            'source_file': geojson_path.name,
            'base_point': {
                'northing': 808226.159,
                'easting': 397922.9125,
                'elevation': 13.0,
                'angle_to_true_north': 92.04
            }
        },
        'cones': camera_data
    }
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(cone_data, f, indent=2)
    
    print(f"Converted {len(camera_data)} cameras to cone_data.json")
    print(f"Output saved to: {output_path}")
    
    return cone_data


def find_most_recent_geojson(directory: Path = None) -> Path:
    """Find the most recent GeoJSON file in the directory"""
    if directory is None:
        directory = Path.cwd()
    
    geojson_files = list(directory.glob('*.geojson'))
    if not geojson_files:
        return None
    
    # Sort by modification time (most recent first)
    most_recent = max(geojson_files, key=lambda f: f.stat().st_mtime)
    return most_recent


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert GeoJSON to cone_data.json')
    parser.add_argument('geojson_file', nargs='?', help='Input GeoJSON file (optional - will auto-detect if not provided)')
    parser.add_argument('-o', '--output', help='Output file (default: cone_data.json)')
    parser.add_argument('-p', '--panorama-dir', default='panoramas', 
                       help='Panorama directory (default: panoramas)')
    parser.add_argument('--auto', action='store_true', 
                       help='Auto-detect most recent GeoJSON file')
    
    args = parser.parse_args()
    
    # Determine input file
    if args.auto or args.geojson_file is None:
        print("Auto-detecting most recent GeoJSON file...")
        geojson_path = find_most_recent_geojson()
        if geojson_path is None:
            print("Error: No GeoJSON files found in current directory")
            return
        print(f"Found: {geojson_path.name}")
    else:
        geojson_path = Path(args.geojson_file)
        if not geojson_path.exists():
            print(f"Error: GeoJSON file not found: {geojson_path}")
            return
    
    output_path = Path(args.output) if args.output else Path('cone_data.json')
    
    convert_geojson_to_cone_data(geojson_path, output_path, args.panorama_dir)


if __name__ == '__main__':
    main()
