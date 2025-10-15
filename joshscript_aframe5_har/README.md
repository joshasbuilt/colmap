# HAR File Analysis (joshscript_aframe5_har)

## Overview
This directory contains tools for analyzing HAR (HTTP Archive) files from asBuilt Vault projects to extract floor plan data and coordinate information.

## Quick Start
**For coordinate extraction, see `COORDINATE_EXTRACTION_GUIDE.md` - this is the main process!**

## Files
- `COORDINATE_EXTRACTION_GUIDE.md` - **MAIN GUIDE** for extracting coordinates
- `extract_ground_floor_coordinates.py` - Creates extraction scripts from HAR files
- `ground_floor_extraction_helper.html` - Browser helper for coordinate extraction
- `ground_floor_coordinates.json` - Extracted Ground Floor coordinates
- `har_analyzer.py` - Core HAR file analysis class
- `process_har_files.py` - Batch processing script for multiple HAR files
- `extract_floorplan_data.py` - Extract floor plan image URLs and base64 data
- `extract_geolocation_bounds.py` - Extract geolocation bounds from HAR files
- `extract_floorplan_coordinates.py` - Extract coordinate data from HAR files
- `convert_edentm_to_wgs84.py` - Convert EDENTM2000 coordinates to WGS84

## The Key Discovery
**HAR files don't contain the actual floor plan coordinates!** They only contain:
- Project URLs
- Mapbox tile data (coordinate extents, not corners)
- Image data (base64 encoded floor plans)

**Real coordinates must be extracted from the browser using React Fiber.**

## Usage

### Extract Coordinates (Main Process)
1. Capture HAR file from project page
2. Run: `python extract_ground_floor_coordinates.py`
3. Open `ground_floor_extraction_helper.html` in browser
4. Follow the extraction process
5. Update floor plan viewer with coordinates

### Basic Analysis
```bash
python har_analyzer.py har_files/project.har
```

### Batch Processing
```bash
python process_har_files.py
```

## Requirements
- Python 3.7+
- See `requirements.txt` for dependencies

## Output
- `ground_floor_coordinates.json` - Extracted coordinates
- `analysis_output/` - HAR analysis results
- `floorplan_data/` - Extracted floor plan images
- `floorplan_coordinates/` - Coordinate data (extents, not corners)
