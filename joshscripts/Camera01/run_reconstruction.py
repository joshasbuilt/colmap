"""
Run COLMAP panorama SfM reconstruction on Camera01 combined frames.
This script processes all 3 videos together with masking applied.
"""

import sys
from pathlib import Path

# Add the python examples directory to path so we can import panorama_sfm
paul_dir = Path(__file__).parent.parent.parent
examples_dir = paul_dir / "python" / "examples"
sys.path.insert(0, str(examples_dir))

import argparse

# Import the panorama_sfm module
import panorama_sfm

def main():
    """Run the panorama SfM reconstruction."""
    
    # Configuration
    camera_dir = Path(__file__).parent
    input_frames = camera_dir / "combined_frames_clean"  # Single video frames
    output_path = camera_dir / "reconstruction_single"
    mask_path = camera_dir / "mask_template2.png"  # New mask template
    
    print("=" * 70)
    print("COLMAP Panorama SfM Reconstruction - Camera01")
    print("=" * 70)
    print()
    print(f"Input frames: {input_frames}")
    print(f"Output path: {output_path}")
    print()
    print("Configuration:")
    print("  - Render mode: overlapping (8 virtual cameras per panorama)")
    print("  - Matcher: sequential with LOOP DETECTION enabled")
    print("  - Masking: Enabled (using mask_template2.png)")
    print("  - Total panoramas: ~78 frames (single video)")
    print("  - Expected virtual images: ~624 images (78 × 8)")
    print()
    print("=" * 70)
    print()
    
    # Create argument parser matching panorama_sfm.py requirements
    args = argparse.Namespace(
        input_image_path=input_frames,
        output_path=output_path,
        matcher="sequential",
        pano_render_type="overlapping",
        camera_mask_path=mask_path,  # Apply the new mask template to all images
        test_mode=False  # Full reconstruction with all frames
    )
    
    # Run the panorama SfM pipeline
    print("Starting panorama SfM reconstruction...")
    print("This may take 30-60 minutes depending on your hardware.")
    print()
    
    try:
        panorama_sfm.run(args)
        print()
        print("=" * 70)
        print("✅ RECONSTRUCTION COMPLETE!")
        print("=" * 70)
        print()
        print(f"Results saved to: {output_path}")
        print()
        print("Output contains:")
        print(f"  - images/          : Virtual perspective images")
        print(f"  - masks/           : Feature extraction masks")
        print(f"  - database.db      : Feature database")
        print(f"  - sparse/          : Sparse 3D reconstruction")
        print()
        print("Next steps:")
        print("  1. View the reconstruction in COLMAP GUI")
        print("  2. Export camera poses and 3D points")
        print("  3. Optionally run dense reconstruction")
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR during reconstruction:")
        print("=" * 70)
        print(f"{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
