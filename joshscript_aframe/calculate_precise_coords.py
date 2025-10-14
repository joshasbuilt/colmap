#!/usr/bin/env python3
"""
Calculate precise Mount Eden 2000 coordinates from known WGS84 coordinates
"""

import pyproj

def calculate_precise_mt_eden_coords():
    """
    Calculate Mount Eden 2000 coordinates for the 4 corners using the known WGS84 coordinates
    """
    
    # Known WGS84 coordinates for the 4 corners
    wgs84_corners = [
        [174.76904030579692, -36.845437470625626],  # Top-left
        [174.76953833830476, -36.84556978976499],   # Top-right
        [174.76945222065177, -36.84577937864095],   # Bottom-right
        [174.76895418814394, -36.84564705950159]    # Bottom-left
    ]
    
    # Expected Mount Eden 2000 coordinates (from your reference)
    expected_corners = [
        [400430.99, 803807.31],  # Top-left expected
        [400475.00, 803792.00],  # Top-right estimated
        [400467.00, 803768.00],  # Bottom-right estimated
        [400422.00, 803783.00]   # Bottom-left estimated
    ]
    
    # Set up coordinate transformations
    wgs84 = pyproj.Proj(init='epsg:4326')
    mt_eden = pyproj.Proj(init='epsg:2105')
    
    print("Calculating Mount Eden 2000 coordinates from WGS84...")
    print("=" * 60)
    
    calculated_coords = []
    
    for i, (lng, lat) in enumerate(wgs84_corners):
        # Convert WGS84 to Mount Eden 2000
        easting, northing = pyproj.transform(wgs84, mt_eden, lng, lat)
        calculated_coords.append((easting, northing))
        
        corner_names = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]
        
        print(f"{corner_names[i]}:")
        print(f"  WGS84: {lng:.8f}, {lat:.8f}")
        print(f"  Mount Eden 2000: E: {easting:.3f}, N: {northing:.3f}")
        
        if i < len(expected_corners):
            exp_e, exp_n = expected_corners[i]
            diff_e = easting - exp_e
            diff_n = northing - exp_n
            print(f"  Expected: E: {exp_e}, N: {exp_n}")
            print(f"  Difference: E: {diff_e:.3f}m, N: {diff_n:.3f}m")
        
        print()
    
    # Calculate the systematic offset
    if len(calculated_coords) > 0:
        # Use the first corner (top-left) to calculate offset
        calc_e, calc_n = calculated_coords[0]
        exp_e, exp_n = expected_corners[0]
        
        offset_e = exp_e - calc_e
        offset_n = exp_n - calc_n
        
        print("Systematic Offset Analysis:")
        print(f"Calculated Top-Left: E: {calc_e:.3f}, N: {calc_n:.3f}")
        print(f"Expected Top-Left:   E: {exp_e}, N: {exp_n}")
        print(f"Required Offset:     E: +{offset_e:.3f}m, N: +{offset_n:.3f}m")
        print()
        
        # Apply offset to all calculated coordinates
        print("Corrected Mount Eden 2000 coordinates (with offset applied):")
        print("=" * 60)
        
        corrected_coords = []
        for i, (calc_e, calc_n) in enumerate(calculated_coords):
            corr_e = calc_e + offset_e
            corr_n = calc_n + offset_n
            corrected_coords.append((corr_e, corr_n))
            
            corner_names = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]
            print(f"{corner_names[i]}: E: {corr_e:.3f}, N: {corr_n:.3f}")
        
        return corrected_coords
    
    return calculated_coords

def generate_javascript_coords(corrected_coords):
    """
    Generate JavaScript code to update the floorplanBounds array
    """
    print("\nJavaScript code to update floorplanBounds:")
    print("=" * 60)
    
    js_code = "floorplanBounds: [\n"
    corner_names = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]
    
    for i, (easting, northing) in enumerate(corrected_coords):
        # Convert back to WGS84 for the JavaScript array
        wgs84 = pyproj.Proj(init='epsg:4326')
        mt_eden = pyproj.Proj(init='epsg:2105')
        
        lng, lat = pyproj.transform(mt_eden, wgs84, easting, northing)
        
        js_code += f"    [{lng:.14f}, {lat:.14f}],  // {corner_names[i]} (E: {easting:.3f}, N: {northing:.3f})\n"
    
    js_code += "],"
    
    print(js_code)
    return js_code

if __name__ == "__main__":
    corrected_coords = calculate_precise_mt_eden_coords()
    
    if corrected_coords:
        generate_javascript_coords(corrected_coords)

