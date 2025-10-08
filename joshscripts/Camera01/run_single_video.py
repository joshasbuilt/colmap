#!/usr/bin/env python3
"""
Run reconstruction for a single video with loop detection enabled
"""

import sys
from pathlib import Path

# Add the panorama_sfm examples directory to path
script_dir = Path(__file__).parent
repo_root = script_dir.parent.parent
examples_dir = repo_root / "python" / "examples"
sys.path.insert(0, str(examples_dir))

import panorama_sfm
import argparse

def main():
    # Paths
    base_dir = Path(__file__).parent
    frame_dir = base_dir / "VID_20251007_100811_00_008_frames"
    mask_template = base_dir / "mask_template2.png"
    output_dir = base_dir / "reconstruction_single"
    
    print(f"Frame directory: {frame_dir}")
    print(f"Mask template: {mask_template}")
    print(f"Output directory: {output_dir}")
    
    # Check paths exist
    if not frame_dir.exists():
        raise FileNotFoundError(f"Frame directory not found: {frame_dir}")
    if not mask_template.exists():
        raise FileNotFoundError(f"Mask template not found: {mask_template}")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Create args object to pass to panorama_sfm.run()
    args = argparse.Namespace(
        input_image_path=frame_dir,
        output_path=output_dir,
        matcher="sequential",  # Sequential matching with loop detection enabled
        pano_render_type="overlapping",  # Create 8 virtual cameras per panorama
        camera_mask_path=mask_template,  # Apply mask to all images
    )
    
    # Run reconstruction
    panorama_sfm.run(args)
    
    print("\n" + "="*80)
    print("Reconstruction complete!")
    print(f"Output directory: {output_dir}")
    print("="*80)

if __name__ == "__main__":
    main()
