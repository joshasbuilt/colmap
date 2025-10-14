#!/usr/bin/env python3
"""
Test coordinate conversion using official EPSG:2105 directly
"""

from pyproj import CRS, Transformer

def test_epsg2105_direct():
    # Use official EPSG:2105 directly
    crs_wgs84 = CRS.from_epsg(4326)  # WGS84
    crs_mount_eden = CRS.from_epsg(2105)  # NZGD2000 / Mount Eden 2000
    
    # Create transformer
    transformer = Transformer.from_crs(crs_wgs84, crs_mount_eden, always_xy=True)
    
    # Test coordinates
    longitude = 174.768783
    latitude = -36.84544
    
    print(f"Input WGS84 coordinates:")
    print(f"  Longitude: {longitude}")
    print(f"  Latitude: {latitude}")
    print()
    
    # Convert
    easting, northing = transformer.transform(longitude, latitude)
    
    print(f"Converted using official EPSG:2105:")
    print(f"  Easting: {easting:.6f}")
    print(f"  Northing: {northing:.6f}")
    print()
    
    # Compare with expected
    expected_easting = 400430.99
    expected_northing = 803807.31
    
    print(f"Expected coordinates:")
    print(f"  Easting: {expected_easting}")
    print(f"  Northing: {expected_northing}")
    print()
    
    print(f"Difference:")
    print(f"  Easting: {easting - expected_easting:.6f} meters")
    print(f"  Northing: {northing - expected_northing:.6f} meters")
    print()
    
    # Test the reverse transformation
    transformer_reverse = Transformer.from_crs(crs_mount_eden, crs_wgs84, always_xy=True)
    back_lng, back_lat = transformer_reverse.transform(easting, northing)
    
    print(f"Reverse transformation (verification):")
    print(f"  Longitude: {back_lng:.10f}")
    print(f"  Latitude: {back_lat:.10f}")
    print()
    
    print(f"Round-trip accuracy:")
    print(f"  Longitude difference: {abs(longitude - back_lng):.10f}")
    print(f"  Latitude difference: {abs(latitude - back_lat):.10f}")

if __name__ == "__main__":
    test_epsg2105_direct()

