#!/usr/bin/env python3
"""
Calculate exact WGS84 coordinates that match Auckland Council GeoMaps result
"""

import pyproj

def calculate_exact_coordinates():
    """
    Calculate WGS84 coordinates that will give us the exact Auckland Council result
    """
    
    # Auckland Council GeoMaps result
    target_easting = 400411.67
    target_northing = 803804.11
    
    print(f"Target Mount Eden 2000 coordinates: E: {target_easting}, N: {target_northing}")
    print("=" * 60)
    
    # Set up coordinate transformations
    wgs84 = pyproj.Proj(init='epsg:4326')
    mt_eden = pyproj.Proj(init='epsg:2105')
    
    # Convert Mount Eden 2000 back to WGS84
    longitude, latitude = pyproj.transform(mt_eden, wgs84, target_easting, target_northing)
    
    print(f"Calculated WGS84 coordinates: {longitude:.14f}, {latitude:.14f}")
    
    # Verify the conversion
    print("\nVerification:")
    back_easting, back_northing = pyproj.transform(wgs84, mt_eden, longitude, latitude)
    print(f"Converted back to Mount Eden 2000: E: {back_easting:.6f}, N: {back_northing:.6f}")
    print(f"Target:                           E: {target_easting}, N: {target_northing}")
    print(f"Difference:                       E: {back_easting - target_easting:.6f}m, N: {back_northing - target_northing:.6f}m")
    
    # Calculate the 4 corner coordinates based on the building dimensions
    print("\n" + "=" * 60)
    print("Calculating 4 corner coordinates...")
    
    # Building dimensions (approximate from the original coordinates)
    # We'll use the original WGS84 coordinates as a template for the relative positions
    original_corners = [
        [174.76904030579692, -36.845437470625626],  # Top-left
        [174.76953833830476, -36.84556978976499],   # Top-right
        [174.76945222065177, -36.84577937864095],   # Bottom-right
        [174.76895418814394, -36.84564705950159]    # Bottom-left
    ]
    
    # Calculate the center point of the original coordinates
    center_lng = sum(corner[0] for corner in original_corners) / 4
    center_lat = sum(corner[1] for corner in original_corners) / 4
    
    print(f"Original center: {center_lng:.14f}, {center_lat:.14f}")
    print(f"New center:      {longitude:.14f}, {latitude:.14f}")
    
    # Calculate offset from original center to new center
    offset_lng = longitude - center_lng
    offset_lat = latitude - center_lat
    
    print(f"Offset:          {offset_lng:.14f}, {offset_lat:.14f}")
    
    # Apply offset to all corners
    new_corners = []
    corner_names = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]
    
    print("\nNew corner coordinates:")
    for i, (orig_lng, orig_lat) in enumerate(original_corners):
        new_lng = orig_lng + offset_lng
        new_lat = orig_lat + offset_lat
        
        # Convert to Mount Eden 2000 to verify
        corner_easting, corner_northing = pyproj.transform(wgs84, mt_eden, new_lng, new_lat)
        
        new_corners.append([new_lng, new_lat])
        
        print(f"{corner_names[i]}:")
        print(f"  WGS84: {new_lng:.14f}, {new_lat:.14f}")
        print(f"  Mount Eden 2000: E: {corner_easting:.3f}, N: {corner_northing:.3f}")
        print()
    
    # Generate JavaScript code
    print("JavaScript code for pic2.html:")
    print("=" * 60)
    print("floorplanBounds: [")
    for i, (lng, lat) in enumerate(new_corners):
        print(f"    [{lng:.14f}, {lat:.14f}],  // {corner_names[i]}")
    print("],")
    
    return new_corners

if __name__ == "__main__":
    calculate_exact_coordinates()

