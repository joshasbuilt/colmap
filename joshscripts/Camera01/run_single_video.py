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
    # Paths (defaults)
    base_dir = Path(__file__).parent
    # Use the requested frames folder and mask_template3 by default
    frame_dir = base_dir / "VID_20251007_170505_00_012_frames"
    mask_template = base_dir / "mask_template3.png"
    output_dir = base_dir / "reconstruction_mask3_012"
    
    print(f"Frame directory: {frame_dir}")
    print(f"Mask template: {mask_template}")
    print(f"Output directory: {output_dir}")
    
    # Check paths exist
    if not frame_dir.exists():
        raise FileNotFoundError(f"Frame directory not found: {frame_dir}")
    if not mask_template.exists():
        raise FileNotFoundError(f"Mask template not found: {mask_template}")
    
    # Allow overrides from the command line for quick testing
    parser = argparse.ArgumentParser(description="Run panorama_sfm on a single video frames folder")
    parser.add_argument("--frames", type=Path, default=frame_dir, help="Path to extracted frame images")
    parser.add_argument("--mask", type=Path, default=mask_template, help="Mask image to apply to all images")
    parser.add_argument("--output", type=Path, default=output_dir, help="Output directory")
    parser.add_argument("--matcher", default="sequential", help="Matcher to use (default: sequential)")
    parser.add_argument("--pano_render_type", default="overlapping", help="Pano render type (default: overlapping)")
    parsed = parser.parse_args()

    # Apply parsed CLI values
    frame_dir = parsed.frames
    mask_template = parsed.mask
    output_dir = parsed.output

    # Create output directory (including parents)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create args object to pass to panorama_sfm.run()
    args = argparse.Namespace(
        input_image_path=frame_dir,
        output_path=output_dir,
        matcher=parsed.matcher,  # Sequential matching with loop detection enabled
        pano_render_type=parsed.pano_render_type,  # Create 8 virtual cameras per panorama
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
