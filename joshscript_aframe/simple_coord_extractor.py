#!/usr/bin/env python3
"""
Simple coordinate extractor - just click on map and get coordinates
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pyproj
import time
import re

def get_coordinates():
    """
    Get coordinates by clicking on the Auckland Council map
    """
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://geomapspublic.aucklandcouncil.govt.nz/viewer/index.html")
        
        print("Waiting for map to load...")
        time.sleep(15)  # Give it more time to load
        
        # Find and click on the map
        print("Looking for map canvas...")
        canvas = driver.find_element(By.TAG_NAME, "canvas")
        
        # Click on the center of the map
        print("Clicking on map...")
        actions = ActionChains(driver)
        actions.move_to_element(canvas).click().perform()
        time.sleep(3)
        
        # Get all text content that might contain coordinates
        print("Extracting coordinate information...")
        
        # Get page source and look for coordinate patterns
        page_source = driver.page_source
        
        # Look for NZTM coordinate patterns
        patterns = [
            r'NZTM\s*:\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)',
            r'(\d{6,7}\.?\d*)\s*,\s*(\d{6,7}\.?\d*)',
            r'"easting":\s*(\d+\.?\d*)',
            r'"northing":\s*(\d+\.?\d*)',
            r'x["\']?\s*:\s*(\d+\.?\d*)',
            r'y["\']?\s*:\s*(\d+\.?\d*)'
        ]
        
        coordinates_found = []
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    try:
                        easting = float(match[0])
                        northing = float(match[1])
                        
                        # Check if it looks like NZTM coordinates
                        if 1000000 < easting < 2000000 and 5000000 < northing < 7000000:
                            coordinates_found.append((easting, northing))
                            print(f"Found NZTM coordinates: E: {easting}, N: {northing}")
                    except:
                        continue
        
        # Also try to get coordinates from visible text elements
        print("Checking visible text elements...")
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'NZTM') or contains(text(), ',')]")
        
        for element in all_elements:
            text = element.text.strip()
            if "NZTM" in text and any(char.isdigit() for char in text):
                print(f"Found coordinate text: {text}")
                
                # Extract numbers
                numbers = re.findall(r'(\d+\.?\d*)', text)
                if len(numbers) >= 2:
                    try:
                        easting = float(numbers[0])
                        northing = float(numbers[1])
                        if 1000000 < easting < 2000000 and 5000000 < northing < 7000000:
                            coordinates_found.append((easting, northing))
                            print(f"Parsed NZTM coordinates: E: {easting}, N: {northing}")
                    except:
                        continue
        
        # Convert NZTM to Mount Eden 2000
        if coordinates_found:
            print(f"\nFound {len(coordinates_found)} coordinate sets:")
            
            for i, (nztm_e, nztm_n) in enumerate(coordinates_found):
                print(f"Set {i+1}: NZTM E: {nztm_e}, N: {nztm_n}")
                
                # Convert to Mount Eden 2000
                mt_eden_coords = convert_nztm_to_mt_eden(nztm_e, nztm_n)
                print(f"         Mount Eden 2000 E: {mt_eden_coords[0]:.3f}, N: {mt_eden_coords[1]:.3f}")
                
                # Compare with expected
                expected_e = 400430.99
                expected_n = 803807.31
                diff_e = mt_eden_coords[0] - expected_e
                diff_n = mt_eden_coords[1] - expected_n
                print(f"         Difference from expected: E: {diff_e:.3f}m, N: {diff_n:.3f}m")
                print()
            
            return coordinates_found[0]  # Return first set
        else:
            print("No NZTM coordinates found")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    finally:
        if 'driver' in locals():
            driver.quit()

def convert_nztm_to_mt_eden(nztm_easting, nztm_northing):
    """
    Convert NZTM coordinates to Mount Eden 2000
    """
    # NZTM (EPSG:2193)
    nztm = pyproj.Proj(init='epsg:2193')
    
    # Mount Eden 2000 (EPSG:2105)
    mt_eden = pyproj.Proj(init='epsg:2105')
    
    # Convert
    mt_eden_easting, mt_eden_northing = pyproj.transform(nztm, mt_eden, nztm_easting, nztm_northing)
    
    return (mt_eden_easting, mt_eden_northing)

if __name__ == "__main__":
    print("Extracting coordinates from Auckland Council GeoMaps...")
    coords = get_coordinates()
    if coords:
        print(f"Final NZTM coordinates: E: {coords[0]}, N: {coords[1]}")
        mt_eden = convert_nztm_to_mt_eden(coords[0], coords[1])
        print(f"Mount Eden 2000 coordinates: E: {mt_eden[0]:.3f}, N: {mt_eden[1]:.3f}")
    else:
        print("Failed to get coordinates")

