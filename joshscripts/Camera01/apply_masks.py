"""
Apply mask template to all extracted frames.
This script copies the mask_template.png to each frame folder with the correct naming.
"""

import shutil
from pathlib import Path

# Configuration
CAMERA_DIR = Path(__file__).parent
MASK_TEMPLATE = CAMERA_DIR / "mask_template3.png"

# Find all frame folders
frame_folders = [
    "VID_20250925_113140_00_051_frames",
    "VID_20250929_133439_00_053_frames", 
    "VID_20250930_131540_00_054_frames",
    "VID_20251007_170505_00_012_frames"
]

def apply_masks():
    """Copy mask template to all frame folders with correct naming."""
    
    # Verify mask template exists
    if not MASK_TEMPLATE.exists():
        print(f"❌ ERROR: Mask template not found at {MASK_TEMPLATE}")
        print("   Please ensure mask_template.png exists in the Camera01 folder.")
        return False
    
    print(f"✓ Found mask template: {MASK_TEMPLATE}")
    print(f"  Size: {MASK_TEMPLATE.stat().st_size / (1024*1024):.2f} MB")
    print()
    
    total_masks = 0
    
    for folder_name in frame_folders:
        folder_path = CAMERA_DIR / folder_name
        
        if not folder_path.exists():
            print(f"⚠ Skipping {folder_name} - folder not found")
            continue
        
        # Find all JPG frames in this folder
        jpg_files = sorted(folder_path.glob("*.jpg"))
        
        if not jpg_files:
            print(f"⚠ No JPG files found in {folder_name}")
            continue
        
        print(f"📁 Processing: {folder_name}")
        print(f"   Found {len(jpg_files)} frames")
        
        # Copy mask for each frame
        for jpg_file in jpg_files:
            # Mask filename must be: frame_name.jpg.png
            mask_file = folder_path / f"{jpg_file.name}.png"
            
            # Copy the template mask
            shutil.copy2(MASK_TEMPLATE, mask_file)
            total_masks += 1
        
        print(f"   ✓ Created {len(jpg_files)} mask files")
        print()
    
    print("=" * 60)
    print(f"✅ SUCCESS! Created {total_masks} mask files")
    print("=" * 60)
    print()
    print("Mask files are ready for COLMAP processing!")
    print("Each frame now has a corresponding .jpg.png mask file.")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("COLMAP Mask Application Script")
    print("=" * 60)
    print()
    
    success = apply_masks()
    
    if success:
        print()
        print("🎯 Next steps:")
        print("1. Verify masks by checking any *_frames folder")
        print("2. You should see .jpg.png files alongside .jpg files")
        print("3. Ready to run panorama_sfm.py with masked frames!")
    else:
        print()
        print("❌ Mask application failed. Please check the errors above.")
