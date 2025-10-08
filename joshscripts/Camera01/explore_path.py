#!/usr/bin/env python3
"""
Explore the panorama_sfm path to debug import issues
"""

import sys
from pathlib import Path

def explore_path():
    print("=" * 60)
    print("PATH EXPLORATION SCRIPT")
    print("=" * 60)
    
    # Current script location
    script_dir = Path(__file__).parent
    print(f"Script directory: {script_dir}")
    print(f"Script directory (resolved): {script_dir.resolve()}")
    print()
    
    # Try different path combinations
    paths_to_try = [
        script_dir / ".." / ".." / ".." / ".." / "paul" / "python" / "examples",
        script_dir / ".." / ".." / ".." / "paul" / "python" / "examples", 
        script_dir / ".." / ".." / "paul" / "python" / "examples",
        Path("C:/Users/JoshuaLumley/Dropbox/0000 Github Repos/asBuilt_DataColmap/paul/python/examples"),
    ]
    
    for i, path in enumerate(paths_to_try):
        resolved_path = path.resolve()
        exists = resolved_path.exists()
        print(f"Path {i+1}: {path}")
        print(f"  Resolved: {resolved_path}")
        print(f"  Exists: {exists}")
        
        if exists:
            print(f"  Contents:")
            try:
                contents = list(resolved_path.iterdir())
                for item in contents:
                    print(f"    - {item.name}")
            except Exception as e:
                print(f"    Error reading directory: {e}")
        print()
    
    # Try to find panorama_sfm.py
    print("Searching for panorama_sfm.py...")
    search_paths = [
        Path("C:/Users/JoshuaLumley/Dropbox/0000 Github Repos/asBuilt_DataColmap"),
        Path("C:/Users/JoshuaLumley/Dropbox/0000 Github Repos"),
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            print(f"Searching in: {search_path}")
            try:
                for py_file in search_path.rglob("panorama_sfm.py"):
                    print(f"  Found: {py_file}")
                    print(f"  Parent: {py_file.parent}")
            except Exception as e:
                print(f"  Error searching: {e}")
        print()

if __name__ == "__main__":
    explore_path()


