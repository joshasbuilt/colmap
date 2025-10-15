#!/usr/bin/env python3
"""
Extract floor plan images and coordinate data from HAR files.
"""

import json
import base64
from pathlib import Path
import re

def extract_floorplan_from_har(har_path):
    """Extract floor plan data from a HAR file."""
    print(f"\nProcessing: {har_path.name}")
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    floorplan_data = {
        'floorplan_url': None,
        'floorplan_image_base64': None,
        'geolocation_bounds': None,
        'mapbox_data': [],
        'image_sources': []
    }
    
    # Look for floor plan images
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        
        # Check if this is a floor plan image (from blob storage)
        if 'vaultprojectswebprod.blob.core.windows.net' in url or 'f9dba6e1-98a8-458e-b9dc-5f67913f2872' in url:
            print(f"  Found floor plan URL: {url}")
            floorplan_data['floorplan_url'] = url
            floorplan_data['image_sources'].append(url)
            
            # Try to extract image data
            content = response.get('content', {})
            encoding = content.get('encoding', '')
            text = content.get('text', '')
            
            if encoding == 'base64' and text:
                print(f"  Extracted base64 image data ({len(text)} bytes)")
                floorplan_data['floorplan_image_base64'] = text
        
        # Look for Mapbox tile requests with coordinates
        if 'api.mapbox.com' in url and '.vector.pbf' in url:
            # Extract tile coordinates from URL
            match = re.search(r'/(\d+)/(\d+)/(\d+)\.vector\.pbf', url)
            if match:
                z, x, y = match.groups()
                floorplan_data['mapbox_data'].append({
                    'z': int(z),
                    'x': int(x),
                    'y': int(y),
                    'url': url
                })
    
    return floorplan_data

def main():
    # Get the script directory
    script_dir = Path(__file__).parent
    har_files_dir = script_dir / 'har_files'
    output_dir = script_dir / 'floorplan_data'
    output_dir.mkdir(exist_ok=True)
    
    har_files = list(har_files_dir.glob('*.har'))
    
    print(f"Found {len(har_files)} HAR files")
    
    all_data = {}
    
    for har_file in har_files:
        floor_name = har_file.stem.replace('projects.asbuiltvault.com_', '')
        data = extract_floorplan_from_har(har_file)
        all_data[floor_name] = data
        
        # Save individual floor data
        output_file = output_dir / f'{floor_name}_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            # Don't include base64 data in JSON (too large)
            json_data = {k: v for k, v in data.items() if k != 'floorplan_image_base64'}
            json.dump(json_data, f, indent=2)
        print(f"  Saved to: {output_file}")
        
        # Save base64 image if found
        if data['floorplan_image_base64']:
            image_file = output_dir / f'{floor_name}_image.txt'
            with open(image_file, 'w', encoding='utf-8') as f:
                f.write(data['floorplan_image_base64'])
            print(f"  Saved base64 image to: {image_file}")
    
    # Save combined data
    combined_file = output_dir / 'all_floors_data.json'
    with open(combined_file, 'w', encoding='utf-8') as f:
        # Don't include base64 data
        combined_data = {k: {kk: vv for kk, vv in v.items() if kk != 'floorplan_image_base64'} 
                        for k, v in all_data.items()}
        json.dump(combined_data, f, indent=2)
    print(f"\nSaved combined data to: {combined_file}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    for floor_name, data in all_data.items():
        print(f"\n{floor_name}:")
        print(f"  Floor plan URL found: {'Yes' if data['floorplan_url'] else 'No'}")
        print(f"  Image data extracted: {'Yes' if data['floorplan_image_base64'] else 'No'}")
        print(f"  Mapbox tiles: {len(data['mapbox_data'])}")
        print(f"  Image sources: {len(data['image_sources'])}")

if __name__ == '__main__':
    main()

