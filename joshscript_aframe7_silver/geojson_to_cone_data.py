#!/usr/bin/env python3
"""
GeoJSON to Cone Data Converter
Converts floor plan viewer GeoJSON export to A-Frame cone_data.json

This script inverts the Project Base Point transformation to convert
real-world Mt Eden 2000 coordinates back to local model space coordinates.

Project Base Point (from survey data):
- Northing: 808226.1590
- Easting: 397922.9125
- Elevation: 13.0000
- Angle to True North: 92.04°

Coordinate System Flow:
1. GeoJSON Input: Real-world Mt Eden 2000 (Northing, Easting, Height)
2. Transform: Invert base point transformation
3. Output: Local DXF coordinates (X, Y, Z) for A-Frame
"""

import json
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


# Project Base Point Configuration
PROJECT_BASE_POINT = {
    'northing': 808226.1590,
    'easting': 397922.9125,
    'elevation': 13.0000,
    'angle_to_true_north': 92.04  # degrees
}


class CoordinateTransformer:
    """Handles coordinate transformation from Mt Eden to DXF local space"""
    
    def __init__(self, base_point: Dict[str, float]):
        self.base_n = base_point['northing']
        self.base_e = base_point['easting']
        self.base_z = base_point['elevation']
        self.rotation_angle = base_point['angle_to_true_north']
        
        # Convert rotation angle to radians
        self.rotation_rad = math.radians(self.rotation_angle)
        
    def mt_eden_to_dxf(self, easting: float, northing: float, height: float = 0.0) -> Tuple[float, float, float]:
        """
        Convert Mt Eden 2000 coordinates to local DXF coordinates
        
        Steps:
        1. Translate to origin (subtract base point)
        2. Rotate by negative of base angle (to align with model axes)
        3. Return DXF coordinates (X, Y, Z)
        
        Args:
            easting: Mt Eden Easting coordinate (meters)
            northing: Mt Eden Northing coordinate (meters)
            height: Elevation above base (meters) - defaults to 0 for 2D data
            
        Returns:
            Tuple of (x, y, z) in DXF local space
        """
        # Step 1: Translate to origin (2D only - ignore elevation)
        delta_e = easting - self.base_e
        delta_n = northing - self.base_n
        # Use height directly (already oriented from COLMAP)
        delta_z = height
        
        # Step 2: Rotate by negative angle (inverse rotation)
        # Standard rotation matrix for counterclockwise rotation
        cos_theta = math.cos(-self.rotation_rad)
        sin_theta = math.sin(-self.rotation_rad)
        
        x = delta_e * cos_theta - delta_n * sin_theta
        y = delta_e * sin_theta + delta_n * cos_theta
        z = delta_z  # Keep Z as relative to base elevation
        
        return (x, y, z)
    
    def calculate_direction_vectors(self, positions: List[Tuple[float, float, float]]) -> List[Dict[str, Dict[str, float]]]:
        """
        Calculate forward and up direction vectors for each camera position
        
        For now, we'll use a simple approach:
        - Forward: direction along the path (to next camera)
        - Up: vertical (0, 0, 1) adjusted for terrain
        
        Args:
            positions: List of (x, y, z) positions in DXF space
            
        Returns:
            List of direction dictionaries with 'forward' and 'up' vectors
        """
        directions = []
        
        for i, (x, y, z) in enumerate(positions):
            # Calculate forward vector (direction to next camera)
            if i < len(positions) - 1:
                next_x, next_y, next_z = positions[i + 1]
                dx = next_x - x
                dy = next_y - y
                dz = next_z - z
            elif i > 0:
                # For last camera, use direction from previous
                prev_x, prev_y, prev_z = positions[i - 1]
                dx = x - prev_x
                dy = y - prev_y
                dz = z - prev_z
            else:
                # Single camera, use default forward direction
                dx, dy, dz = 1.0, 0.0, 0.0
            
            # Normalize forward vector
            forward_length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if forward_length > 0:
                forward_x = dx / forward_length
                forward_y = dy / forward_length
                forward_z = dz / forward_length
            else:
                forward_x, forward_y, forward_z = 1.0, 0.0, 0.0
            
            # Calculate up vector (perpendicular to forward, roughly vertical)
            # Simple approach: use world up (0, 0, 1) and adjust
            up_x = 0.0
            up_y = 0.0
            up_z = 1.0
            
            # Make up vector orthogonal to forward (Gram-Schmidt)
            dot = forward_x * up_x + forward_y * up_y + forward_z * up_z
            up_x = up_x - dot * forward_x
            up_y = up_y - dot * forward_y
            up_z = up_z - dot * forward_z
            
            # Normalize up vector
            up_length = math.sqrt(up_x*up_x + up_y*up_y + up_z*up_z)
            if up_length > 0:
                up_x = up_x / up_length
                up_y = up_y / up_length
                up_z = up_z / up_length
            else:
                up_x, up_y, up_z = 0.0, 0.0, 1.0
            
            directions.append({
                'forward': {'x': forward_x, 'y': forward_y, 'z': forward_z},
                'up': {'x': up_x, 'y': up_y, 'z': up_z}
            })
        
        return directions


def load_geojson(filepath: Path) -> Dict:
    """Load GeoJSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_camera_data(geojson: Dict) -> List[Dict]:
    """
    Extract camera positions and metadata from GeoJSON
    
    Returns list of camera dictionaries with:
    - easting, northing, height
    - frame number
    - image path
    - other metadata
    """
    cameras = []
    
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [])
        
        if len(coords) >= 2:  # Only need 2D coordinates
            # Use Mt Eden coordinates from properties (not WGS84 from geometry)
            easting = props.get('easting')
            northing = props.get('northing')
            
            if easting is not None and northing is not None:
                # Extract oriented height from coords3D string
                coords3d_str = props.get('coords3D', '')
                oriented_height = 0.0
                if coords3d_str and '3D:' in coords3d_str:
                    try:
                        # Extract coordinates from "3D: (-4.99, 1.69, 1.46)" format
                        coords_part = coords3d_str.split('3D:')[1].strip()
                        coords_part = coords_part.strip('()')
                        coords_list = [float(x.strip()) for x in coords_part.split(',')]
                        if len(coords_list) >= 3:
                            oriented_height = coords_list[2]  # Z coordinate
                    except:
                        oriented_height = props.get('height', 0.0)  # Fallback to height property
                else:
                    oriented_height = props.get('height', 0.0)  # Fallback to height property
                
                camera = {
                    'easting': easting,
                    'northing': northing,
                    'height': oriented_height,  # Use oriented height from coords3D
                    'longitude': coords[0],
                    'latitude': coords[1],
                    'frame': props.get('frame', '0000'),
                    'frame_id': props.get('frameId', '0'),
                    'image': props.get('image', ''),
                    'camera': props.get('camera', ''),
                'coords_3d': props.get('coords3D', ''),
                'group': props.get('group', '')
            }
            cameras.append(camera)
    
    return cameras


def convert_geojson_to_cone_data(geojson_path: Path, output_path: Path, 
                                  panorama_dir: str = 'panoramas') -> Dict:
    """
    Main conversion function
    
    Args:
        geojson_path: Path to input GeoJSON file
        output_path: Path to output cone_data.json file
        panorama_dir: Directory name for panorama images
        
    Returns:
        The generated cone_data dictionary
    """
    print(f"Loading GeoJSON from: {geojson_path}")
    geojson = load_geojson(geojson_path)
    
    print(f"Extracting camera data...")
    cameras = extract_camera_data(geojson)
    print(f"Found {len(cameras)} camera positions")
    
    # Calculate dynamic base elevation from camera heights
    heights = [cam['height'] for cam in cameras if 'height' in cam]
    if heights:
        min_height = min(heights)
        max_height = max(heights)
        print(f"Camera height range: {min_height:.2f}m to {max_height:.2f}m")
        print(f"Using minimum height as base elevation: {min_height:.2f}m")
        
        # Update base point with dynamic elevation
        dynamic_base_point = PROJECT_BASE_POINT.copy()
        dynamic_base_point['elevation'] = min_height
    else:
        dynamic_base_point = PROJECT_BASE_POINT
    
    # Initialize transformer
    transformer = CoordinateTransformer(dynamic_base_point)
    
    # Transform coordinates
    print("Transforming coordinates from Mt Eden to DXF space...")
    dxf_positions = []
    for cam in cameras:
        x, y, z = transformer.mt_eden_to_dxf(
            cam['easting'], 
            cam['northing'], 
            cam['height']
        )
        dxf_positions.append((x, y, z))
        print(f"  Frame {cam['frame']}: Mt Eden ({cam['easting']:.2f}, {cam['northing']:.2f}, {cam['height']:.2f}) "
              f"→ DXF ({x:.2f}, {y:.2f}, {z:.2f})")
    
    # Calculate direction vectors
    print("Calculating camera direction vectors...")
    directions = transformer.calculate_direction_vectors(dxf_positions)
    
    # Build cone data structure
    cones = []
    for i, (cam, pos, direction) in enumerate(zip(cameras, dxf_positions, directions)):
        # Extract frame number for image path
        frame_num = cam['frame']
        if isinstance(frame_num, str):
            frame_num = frame_num.lstrip('0') or '0'
        
        cone = {
            'cone_id': i + 1,
            'dxf_position': {
                'x': pos[0],
                'y': pos[1],
                'z': pos[2]
            },
            'direction': direction,
            'camera_index': 1,  # Default camera index
            'frame_number': int(frame_num),
            'image_path': f"{panorama_dir}/frame_{cam['frame']}.jpg",
            'metadata': {
                'mt_eden_coords': {
                    'easting': cam['easting'],
                    'northing': cam['northing'],
                    'height': cam['height']
                },
                'wgs84_coords': {
                    'longitude': cam['longitude'],
                    'latitude': cam['latitude']
                },
                'original_image': cam['image'],
                'camera_name': cam['camera'],
                'group': cam['group']
            }
        }
        cones.append(cone)
    
    # Create final cone_data structure
    cone_data = {
        'export_info': {
            'timestamp': datetime.now().isoformat(),
            'total_cones': len(cones),
            'camera_index_used': 1,
            'source_file': str(geojson_path.name),
            'base_point': PROJECT_BASE_POINT
        },
        'cones': cones
    }
    
    # Write output
    print(f"\nWriting cone_data.json to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(cone_data, f, indent=2)
    
    print(f"\n✓ Conversion complete!")
    print(f"  Generated {len(cones)} cone entries")
    print(f"  Output: {output_path}")
    
    return cone_data


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent
    
    # Look for any GeoJSON file in the directory
    geojson_files = list(script_dir.glob('camera_positions*.geojson'))
    
    if not geojson_files:
        print(f"ERROR: No GeoJSON files found in: {script_dir}")
        print(f"\nPlease:")
        print(f"1. Export GeoJSON from floor plan viewer using: exportCameraPositionsAsGeoJSON()")
        print(f"2. Place the exported file in: {script_dir}")
        return
    
    # Use the first (or most recent) GeoJSON file
    geojson_path = geojson_files[0]
    if len(geojson_files) > 1:
        # Use the most recent file
        geojson_path = max(geojson_files, key=lambda p: p.stat().st_mtime)
        print(f"Found multiple GeoJSON files, using most recent: {geojson_path.name}")
    
    output_path = script_dir / 'cone_data.json'
    
    print(f"Using GeoJSON file: {geojson_path.name}")
    convert_geojson_to_cone_data(geojson_path, output_path)


if __name__ == '__main__':
    main()

