#!/usr/bin/env python3
"""
Debug Z-values through the pipeline
Compare Z-values at each stage to find where they get corrupted
"""

import json
from pathlib import Path

def analyze_geojson_z_values(geojson_path):
    """Analyze Z-values in GeoJSON file"""
    print(f"\n=== ANALYZING GEOJSON: {geojson_path.name} ===")
    
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    z_values = []
    for feature in data['features']:
        if 'properties' in feature and 'coords3D' in feature['properties']:
            coords3d_str = feature['properties']['coords3D']
            # Parse "3D: (4.506, 0.036, 2.322)" format
            import re
            match = re.search(r'3D: \(([^,]+), ([^,]+), ([^)]+)\)', coords3d_str)
            if match:
                z_values.append(float(match.group(3)))
    
    if z_values:
        print(f"Z-values range: {min(z_values):.3f} to {max(z_values):.3f}")
        print(f"Z-values count: {len(z_values)}")
        print(f"Sample Z-values: {z_values[:5]}")
    else:
        print("No Z-values found in coords3D")
    
    return z_values

def analyze_cone_data_z_values(cone_data_path):
    """Analyze Z-values in cone_data.json file"""
    print(f"\n=== ANALYZING CONE DATA: {cone_data_path.name} ===")
    
    with open(cone_data_path, 'r') as f:
        data = json.load(f)
    
    z_values = []
    for cone in data['cones']:
        if 'dxf_position' in cone and 'z' in cone['dxf_position']:
            z_values.append(cone['dxf_position']['z'])
    
    if z_values:
        print(f"Z-values range: {min(z_values):.3f} to {max(z_values):.3f}")
        print(f"Z-values count: {len(z_values)}")
        print(f"Sample Z-values: {z_values[:5]}")
    else:
        print("No Z-values found in cone positions")
    
    return z_values

def compare_z_values(geojson_z, cone_z):
    """Compare Z-values between GeoJSON and cone data"""
    print(f"\n=== COMPARING Z-VALUES ===")
    
    if not geojson_z or not cone_z:
        print("Cannot compare - missing Z-values in one or both files")
        return
    
    print(f"GeoJSON Z-range: {min(geojson_z):.3f} to {max(geojson_z):.3f}")
    print(f"Cone Data Z-range: {min(cone_z):.3f} to {max(cone_z):.3f}")
    
    # Check if ranges are similar
    geojson_range = max(geojson_z) - min(geojson_z)
    cone_range = max(cone_z) - min(cone_z)
    
    print(f"GeoJSON Z-range span: {geojson_range:.3f}")
    print(f"Cone Data Z-range span: {cone_range:.3f}")
    
    if abs(geojson_range - cone_range) > 0.1:
        print("⚠️  WARNING: Z-value ranges are significantly different!")
    else:
        print("✅ Z-value ranges are similar")

def main():
    """Main debugging function"""
    script_dir = Path(__file__).parent
    
    # Find the most recent GeoJSON file
    geojson_files = list(script_dir.glob('camera_positions*.geojson'))
    if not geojson_files:
        print("No GeoJSON files found!")
        return
    
    geojson_path = max(geojson_files, key=lambda p: p.stat().st_mtime)
    
    # Find cone data files
    cone_data_files = list(script_dir.glob('cone_data*.json'))
    if not cone_data_files:
        print("No cone data files found!")
        return
    
    # Analyze GeoJSON
    geojson_z = analyze_geojson_z_values(geojson_path)
    
    # Analyze each cone data file
    for cone_path in sorted(cone_data_files):
        cone_z = analyze_cone_data_z_values(cone_path)
        
        # Compare with GeoJSON
        compare_z_values(geojson_z, cone_z)

if __name__ == "__main__":
    main()
