#!/usr/bin/env python3
"""
Convert base64 floor plan images from HAR extraction to actual image files.
"""

import base64
from pathlib import Path
import json

def convert_base64_to_image():
    """Convert base64 image data from HAR extraction to image files."""
    
    # Get script directory and navigate to source
    script_dir = Path(__file__).parent
    source_dir = script_dir.parent / 'joshscript_aframe5_har' / 'floorplan_data'
    
    # Destination directory for images
    dest_dir = script_dir / 'floorplan_images'
    dest_dir.mkdir(exist_ok=True)
    
    # Find all base64 image files
    image_files = list(source_dir.glob('*_image.txt'))
    
    if not image_files:
        print(f"No image files found in {source_dir}")
        return
    
    print(f"Found {len(image_files)} base64 image files")
    
    for image_file in image_files:
        floor_name = image_file.stem.replace('_image', '')
        print(f"\nProcessing: {floor_name}")
        
        # Read base64 data
        with open(image_file, 'r', encoding='utf-8') as f:
            base64_data = f.read().strip()
        
        print(f"  Base64 data length: {len(base64_data)} characters")
        
        # Decode base64
        try:
            image_data = base64.b64decode(base64_data)
            print(f"  Decoded image size: {len(image_data)} bytes ({len(image_data)/1024:.1f} KB)")
            
            # Detect image format from magic bytes
            if image_data.startswith(b'\x89PNG'):
                ext = 'png'
            elif image_data.startswith(b'\xff\xd8\xff'):
                ext = 'jpg'
            elif image_data.startswith(b'GIF'):
                ext = 'gif'
            elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:20]:
                ext = 'webp'
            else:
                ext = 'bin'
                print(f"  Warning: Unknown image format, saving as .bin")
            
            # Save image
            output_file = dest_dir / f'{floor_name}.{ext}'
            with open(output_file, 'wb') as f:
                f.write(image_data)
            
            print(f"  [OK] Saved to: {output_file}")
            print(f"  Format: {ext.upper()}")
            
        except Exception as e:
            print(f"  [ERROR] Error decoding image: {e}")
    
    # Create a JSON file with image metadata
    metadata = {
        'images': []
    }
    
    for image_file in dest_dir.glob('*.*'):
        if image_file.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            size_kb = image_file.stat().st_size / 1024
            metadata['images'].append({
                'filename': image_file.name,
                'floor': image_file.stem,
                'size_kb': round(size_kb, 1),
                'format': image_file.suffix[1:].upper()
            })
    
    metadata_file = dest_dir / 'images_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Conversion complete!")
    print(f"Images saved to: {dest_dir}")
    print(f"Metadata saved to: {metadata_file}")
    print(f"{'='*50}")

if __name__ == '__main__':
    convert_base64_to_image()

