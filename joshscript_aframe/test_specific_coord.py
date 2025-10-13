#!/usr/bin/env python3
"""
Test specific coordinate: 174.768784, -36.84544
"""

import pyproj

def test_specific_coordinate():
    # Test coordinate
    longitude = 174.768784
    latitude = -36.84544
    
    print(f"Testing coordinate: {longitude}, {latitude}")
    print("=" * 50)
    
    # Set up coordinate transformations
    wgs84 = pyproj.Proj(init='epsg:4326')
    mt_eden = pyproj.Proj(init='epsg:2105')
    
    # Convert WGS84 to Mount Eden 2000
    easting, northing = pyproj.transform(wgs84, mt_eden, longitude, latitude)
    
    print(f"WGS84 input: {longitude}, {latitude}")
    print(f"Mount Eden 2000: E: {easting:.6f}, N: {northing:.6f}")
    
    # Compare with expected
    expected_easting = 400430.99
    expected_northing = 803807.31
    
    print(f"Expected: E: {expected_easting}, N: {expected_northing}")
    print(f"Difference: E: {easting - expected_easting:.6f}m, N: {northing - expected_northing:.6f}m")
    
    # Calculate distance error
    import math
    distance_error = math.sqrt((easting - expected_easting)**2 + (northing - expected_northing)**2)
    print(f"Distance error: {distance_error:.6f}m")
    
    # Convert back to verify
    back_lng, back_lat = pyproj.transform(mt_eden, wgs84, easting, northing)
    print(f"Round-trip: {back_lng:.10f}, {back_lat:.10f}")
    print(f"Round-trip error: {abs(longitude - back_lng):.10f}, {abs(latitude - back_lat):.10f}")

if __name__ == "__main__":
    test_specific_coordinate()
