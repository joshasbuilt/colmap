#!/usr/bin/env python3
"""
Get NZTM coordinates from Auckland Council GeoMaps and convert to Mount Eden 2000
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pyproj
import time
import re

def get_building_coordinates():
    """
    Navigate to 69 Customs Street East and get NZTM coordinates, then convert to Mount Eden 2000
    """
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://geomapspublic.aucklandcouncil.govt.nz/viewer/index.html")
        
        wait = WebDriverWait(driver, 30)
        
        # Wait for map to load
        print("Waiting for map to load...")
        time.sleep(10)
        
        # Look for search functionality
        print("Looking for search box...")
        search_selectors = [
            "input[type='search']",
            "input[placeholder*='search']",
            "input[placeholder*='Search']",
            ".search-input",
            "#search",
            "[class*='search']"
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    search_box = elements[0]
                    print(f"Found search box: {selector}")
                    break
            except:
                continue
        
        if search_box:
            # Search for the address
            print("Searching for '69 Customs Street East'...")
            search_box.clear()
            search_box.send_keys("69 Customs Street East")
            search_box.submit()
            time.sleep(5)
        
        # Try to get coordinates by clicking on the map
        print("Getting coordinates from map...")
        
        # Look for map canvas
        map_canvas = None
        canvas_selectors = ["canvas", ".ol-viewport", "[class*='map']"]
        
        for selector in canvas_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    map_canvas = elements[0]
                    print(f"Found map canvas: {selector}")
                    break
            except:
                continue
        
        if map_canvas:
            # Click on the center of the map to get coordinates
            actions = ActionChains(driver)
            actions.move_to_element(map_canvas).click().perform()
            time.sleep(2)
        
        # Get coordinates from the display
        print("Extracting coordinates...")
        
        # Look for coordinate display
        coord_text = None
        coord_selectors = [
            "[class*='coordinate']",
            "[id*='coord']",
            ".coordinate-display",
            ".map-coordinates"
        ]
        
        for selector in coord_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if "NZTM" in text and any(char.isdigit() for char in text):
                        coord_text = text
                        print(f"Found coordinates: {coord_text}")
                        break
                if coord_text:
                    break
            except:
                continue
        
        # Also try JavaScript to get coordinates
        if not coord_text:
            print("Trying JavaScript to get coordinates...")
            js_scripts = [
                "return document.querySelector('[class*=\"coordinate\"]')?.textContent;",
                "return document.querySelector('[id*=\"coord\"]')?.textContent;",
                "return Array.from(document.querySelectorAll('*')).find(el => el.textContent?.includes('NZTM'))?.textContent;"
            ]
            
            for js in js_scripts:
                try:
                    result = driver.execute_script(js)
                    if result and "NZTM" in result:
                        coord_text = result
                        print(f"JavaScript found coordinates: {coord_text}")
                        break
                except:
                    continue
        
        if coord_text:
            # Parse NZTM coordinates
            print(f"Parsing coordinates: {coord_text}")
            
            # Extract numbers from the coordinate text
            numbers = re.findall(r'(\d+\.?\d*)', coord_text)
            if len(numbers) >= 2:
                nztm_easting = float(numbers[0])
                nztm_northing = float(numbers[1])
                
                print(f"NZTM coordinates: E: {nztm_easting}, N: {nztm_northing}")
                
                # Convert NZTM to Mount Eden 2000
                mount_eden_coords = convert_nztm_to_mt_eden(nztm_easting, nztm_northing)
                print(f"Mount Eden 2000 coordinates: E: {mount_eden_coords[0]:.3f}, N: {mount_eden_coords[1]:.3f}")
                
                return mount_eden_coords
            else:
                print("Could not parse coordinates from text")
        else:
            print("No coordinates found")
        
        # Get page source to debug
        print("Getting page source for debugging...")
        page_source = driver.page_source
        
        # Look for coordinate patterns in the source
        coord_patterns = [
            r'NZTM\s*:\s*(\d+\.?\d*),\s*(\d+\.?\d*)',
            r'(\d{6,7}\.?\d*)\s*,\s*(\d{6,7}\.?\d*)',
            r'easting["\']?\s*:\s*(\d+\.?\d*)',
            r'northing["\']?\s*:\s*(\d+\.?\d*)'
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                print(f"Found coordinate pattern: {pattern}")
                for match in matches:
                    if len(match) == 2:
                        try:
                            easting = float(match[0])
                            northing = float(match[1])
                            if 1000000 < easting < 2000000 and 5000000 < northing < 7000000:  # NZTM range
                                print(f"NZTM coordinates from source: E: {easting}, N: {northing}")
                                mount_eden_coords = convert_nztm_to_mt_eden(easting, northing)
                                print(f"Mount Eden 2000 coordinates: E: {mount_eden_coords[0]:.3f}, N: {mount_eden_coords[1]:.3f}")
                                return mount_eden_coords
                        except:
                            continue
        
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
    print("Getting building coordinates from Auckland Council GeoMaps...")
    coords = get_building_coordinates()
    if coords:
        print(f"Final Mount Eden 2000 coordinates: E: {coords[0]:.3f}, N: {coords[1]:.3f}")
    else:
        print("Failed to get coordinates")
