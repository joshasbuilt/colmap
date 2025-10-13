#!/usr/bin/env python3
"""
Test coordinate conversion from WGS84 to Mount Eden 2000 (EPSG:2105)
Using the same parameters as the JavaScript code
"""

import pyproj

def test_coordinate_conversion():
    # Define the Mount Eden 2000 projection (EPSG:2105) using OFFICIAL parameters
    mount_eden_2000 = pyproj.Proj(
        proj='tmerc',
        lat_0=-36.8797222222222,  # Official latitude of origin
        lon_0=174.764166666667,   # Official central meridian
        k=0.9999,
        x_0=400000,
        y_0=800000,
        ellps='GRS80',
        towgs84='0,0,0,0,0,0,0',
        units='m',
        no_defs=True
    )
    
    # Also test using the official EPSG:2105 directly
    mount_eden_official = pyproj.Proj(init='epsg:2105')
    
    # WGS84 projection
    wgs84 = pyproj.Proj(proj='longlat', datum='WGS84', no_defs=True)
    
    # Test coordinates
    longitude = 174.768783
    latitude = -36.84544
    
    print(f"Input WGS84 coordinates:")
    print(f"  Longitude: {longitude}")
    print(f"  Latitude: {latitude}")
    print()
    
    # Convert WGS84 to Mount Eden 2000 using manual parameters
    easting1, northing1 = pyproj.transform(wgs84, mount_eden_2000, longitude, latitude)
    
    print(f"Converted to Mount Eden 2000 (manual parameters):")
    print(f"  Easting: {easting1:.3f}")
    print(f"  Northing: {northing1:.3f}")
    print()
    
    # Convert WGS84 to Mount Eden 2000 using official EPSG:2105
    easting2, northing2 = pyproj.transform(wgs84, mount_eden_official, longitude, latitude)
    
    print(f"Converted to Mount Eden 2000 (official EPSG:2105):")
    print(f"  Easting: {easting2:.3f}")
    print(f"  Northing: {northing2:.3f}")
    print()
    
    print(f"Difference between methods:")
    print(f"  Easting difference: {abs(easting1 - easting2):.6f} meters")
    print(f"  Northing difference: {abs(northing1 - northing2):.6f} meters")
    print()
    
    # Compare with expected coordinates
    expected_easting = 400430.99
    expected_northing = 803807.31
    
    print(f"Comparison with expected coordinates:")
    print(f"  Expected: E: {expected_easting}, N: {expected_northing}")
    print(f"  Manual:   E: {easting1:.3f}, N: {northing1:.3f}")
    print(f"  Official: E: {easting2:.3f}, N: {northing2:.3f}")
    print()
    print(f"Difference from expected (manual):")
    print(f"  Easting: {easting1 - expected_easting:.3f} meters")
    print(f"  Northing: {northing1 - expected_northing:.3f} meters")
    print()
    print(f"Difference from expected (official):")
    print(f"  Easting: {easting2 - expected_easting:.3f} meters")
    print(f"  Northing: {northing2 - expected_northing:.3f} meters")

if __name__ == "__main__":
    test_coordinate_conversion()
