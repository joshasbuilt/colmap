#!/usr/bin/env python3
"""
Extract precise coordinates from Auckland Council GeoMaps
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def extract_coordinates_from_auckland_maps():
    """
    Extract coordinates from Auckland Council GeoMaps using Selenium
    """
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Auckland Council GeoMaps
        print("Loading Auckland Council GeoMaps...")
        driver.get("https://geomapspublic.aucklandcouncil.govt.nz/viewer/index.html")
        
        # Wait for the map to load
        wait = WebDriverWait(driver, 30)
        
        # Look for coordinate display elements
        print("Looking for coordinate display...")
        
        # Common selectors for coordinate displays in mapping applications
        coord_selectors = [
            "[class*='coordinate']",
            "[class*='easting']",
            "[class*='northing']",
            "[id*='coord']",
            "[id*='easting']",
            "[id*='northing']",
            ".coordinate-display",
            ".map-coordinates",
            ".position-info"
        ]
        
        coordinates_found = False
        for selector in coord_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found coordinate elements with selector: {selector}")
                    for element in elements:
                        text = element.text.strip()
                        if text and any(char.isdigit() for char in text):
                            print(f"Coordinate text: {text}")
                    coordinates_found = True
            except Exception as e:
                continue
        
        if not coordinates_found:
            print("No coordinate display found. Checking page source...")
            
            # Get page source and look for coordinate patterns
            page_source = driver.page_source
            
            # Look for coordinate patterns in the HTML
            import re
            
            # Pattern for Easting/Northing coordinates (6-digit numbers)
            coord_pattern = r'(\d{6,7}\.?\d*)\s*,\s*(\d{6,7}\.?\d*)'
            matches = re.findall(coord_pattern, page_source)
            
            if matches:
                print("Found coordinate patterns in page source:")
                for match in matches:
                    print(f"  {match[0]}, {match[1]}")
            else:
                print("No coordinate patterns found in page source")
        
        # Try to interact with the map to get coordinates
        print("Attempting to get coordinates by clicking on map...")
        
        # Look for map canvas or clickable area
        map_selectors = [
            "canvas",
            "[class*='map']",
            "[class*='viewer']",
            "[id*='map']",
            ".ol-viewport"
        ]
        
        map_element = None
        for selector in map_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    map_element = elements[0]
                    print(f"Found map element: {selector}")
                    break
            except:
                continue
        
        if map_element:
            # Try to get coordinates by clicking on the map
            print("Clicking on map to get coordinates...")
            map_element.click()
            time.sleep(2)
            
            # Check if coordinates appeared after clicking
            for selector in coord_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for element in elements:
                            text = element.text.strip()
                            if text and any(char.isdigit() for char in text):
                                print(f"Coordinates after click: {text}")
                except:
                    continue
        
        # Get the current URL to see if it contains coordinate info
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        # Look for coordinate parameters in URL
        coord_url_pattern = r'[?&](?:x|easting|e)=([\d.]+)[&,]?(?:y|northing|n)=([\d.]+)'
        url_matches = re.findall(coord_url_pattern, current_url)
        if url_matches:
            print("Found coordinates in URL:")
            for match in url_matches:
                print(f"  Easting: {match[0]}, Northing: {match[1]}")
        
        # Try to execute JavaScript to get map coordinates
        print("Executing JavaScript to get map coordinates...")
        try:
            # Common JavaScript patterns for getting map coordinates
            js_scripts = [
                "return window.map && window.map.getCenter && window.map.getCenter();",
                "return window.viewer && window.viewer.getCenter && window.viewer.getCenter();",
                "return window.ol && window.ol.getCenter && window.ol.getCenter();",
                "return document.querySelector('[class*=\"coordinate\"]') && document.querySelector('[class*=\"coordinate\"]').textContent;",
                "return document.querySelector('[id*=\"coord\"]') && document.querySelector('[id*=\"coord\"]').textContent;"
            ]
            
            for js in js_scripts:
                try:
                    result = driver.execute_script(js)
                    if result:
                        print(f"JavaScript result: {result}")
                except:
                    continue
        except Exception as e:
            print(f"JavaScript execution failed: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if 'driver' in locals():
            driver.quit()

def alternative_api_approach():
    """
    Try to find API endpoints for Auckland Council GeoMaps
    """
    print("\nTrying alternative API approach...")
    
    # Common API endpoints for mapping services
    api_endpoints = [
        "https://geomapspublic.aucklandcouncil.govt.nz/api/",
        "https://geomapspublic.aucklandcouncil.govt.nz/rest/",
        "https://geomapspublic.aucklandcouncil.govt.nz/geoserver/",
        "https://geomapspublic.aucklandcouncil.govt.nz/arcgis/",
        "https://geomapspublic.aucklandcouncil.govt.nz/services/"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                print(f"Found accessible endpoint: {endpoint}")
                print(f"Response: {response.text[:200]}...")
        except:
            continue

if __name__ == "__main__":
    print("Extracting coordinates from Auckland Council GeoMaps...")
    extract_coordinates_from_auckland_maps()
    alternative_api_approach()
