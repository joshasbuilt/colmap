# 360° Cone-Based Navigation System

A sophisticated A-Frame-based navigation system for immersive 360° panorama viewing with metallic UI elements, advanced lighting, and cone-based positioning data.

## Features

### Core Functionality
- **360° Panorama Viewer** - Immersive full-sphere image viewing
- **Cone-Based Navigation** - Navigate through space using 3D cone position data from COLMAP
- **Metallic UI Elements** - Professional metallic spheres and ribbons with realistic materials
- **Advanced Lighting** - 4-light system for optimal visual quality
- **Camera Orientation** - Automatic camera direction based on cone forward vectors
- **Path Visualization** - Metallic ribbons connecting navigation points

### Interactive Elements
- **Navigation Spheres** - Click to jump between panorama positions
- **Size Control** - Adjust sphere size dynamically
- **Elevation Control** - Raise/lower all navigation markers
- **Comment System** - Add annotation markers at specific locations
- **Hover Effects** - Visual feedback on interactive elements

### Professional Materials
- **Metallic Physical Materials** - Using THREE.js advanced material system
  - Metalness: 0.6
  - Roughness: 0.12
  - Clearcoat: 0.2
  - Environment mapping for realistic reflections
- **Shared Materials** - Optimized performance with material reuse
- **Semi-transparent Elements** - Professional opacity for layered visibility

## Project Structure

```
joshscript_aframe/
├── index.html              # Main HTML with A-Frame scene
├── navigation-system.js    # Core navigation logic
├── styles.css              # UI styling
├── cone_data.json          # Example cone position data
├── server.py               # Python development server
├── panoramas/              # 360° panorama images
│   ├── frame_001.jpg
│   ├── frame_002.jpg
│   └── ...
└── README.md               # This file
```

## Installation & Setup

### Prerequisites
- Python 3.x (for local web server)
- Modern web browser (Chrome, Firefox, Edge)
- 360° panorama images

### Quick Start

1. **Navigate to the directory:**
   ```bash
   cd paul/joshscript_aframe
   ```

2. **Place your panorama images:**
   - Create a `panoramas/` folder
   - Add your 360° images (frame_001.jpg, frame_002.jpg, etc.)

3. **Update cone data:**
   - Replace `cone_data.json` with your actual cone data
   - Ensure `image_path` points to correct panorama files

4. **Start the server:**
   ```bash
   python server.py
   ```

5. **Open in browser:**
   - Navigate to `http://localhost:8000`
   - Grant any required permissions for camera/mouse controls

## Cone Data Format

The system expects a JSON file with this structure:

```json
{
  "export_info": {
    "timestamp": "2025-10-08T15:15:27.167623",
    "total_cones": 45,
    "camera_index_used": 1,
    "dxf_file": "pointcloud_affine_manual.dxf"
  },
  "cones": [
    {
      "cone_id": 1,
      "dxf_position": {
        "x": 3.275,
        "y": 0.809,
        "z": 1.901
      },
      "direction": {
        "x": -0.019,
        "y": 0.999,
        "z": -0.049
      },
      "camera_index": 1,
      "frame_number": 1,
      "image_path": "panoramas/frame_001.jpg"
    }
  ]
}
```

### Field Descriptions

- **`cone_id`**: Unique identifier (1-based)
- **`dxf_position`**: 3D coordinates in DXF space (meters)
- **`direction`**: Normalized 3D vector for camera orientation
  - x: Horizontal direction (left/right)
  - y: Vertical direction (up/down)
  - z: Depth direction (forward/back)
- **`image_path`**: Relative path to 360° panorama image

## Usage

### Navigation Controls

- **Mouse**: Look around the 360° environment
- **Click Spheres**: Navigate to different positions
- **UI Panel**: Control sphere visibility, size, and elevation

### UI Controls

#### Sphere Controls
- **Show/Hide Spheres** - Toggle navigation sphere visibility
- **Sphere Size** - Adjust marker size (0.01 - 0.3)
- **Elevation** - Vertical offset for all markers (-2 to +2)

#### Comment System
- **Toggle Comments** - Show/hide annotation markers
- **Add Comment** - Create marker at current position
- Click markers to view metadata

#### Data Management
- **Export Data** - Download current state as JSON
- **Reset View** - Return to first cone position

### Camera Controls

- **Mouse Movement** - Look around (reverse mouse drag enabled)
- **WASD Disabled** - Fixed camera position for stability
- **Auto-Orientation** - Camera automatically faces cone direction

## Advanced Features

### Material System

The system uses THREE.js PBR (Physically Based Rendering) materials:

```javascript
{
  color: 0xeeeeee,          // Base color (white/silver)
  metalness: 0.6,           // Metallic appearance
  roughness: 0.12,          // Surface smoothness
  clearcoat: 0.2,           // Additional coat layer
  clearcoatRoughness: 0.08, // Coat surface quality
  envMapIntensity: 0.9,     // Environment reflection strength
  reflectivity: 0.85,       // Mirror-like properties
  transparent: true,        // Allow opacity control
  opacity: 0.9              // 90% opaque
}
```

### Lighting System

Four-light setup for professional illumination:

1. **Ambient Light** - Base illumination (20%)
2. **Primary Directional** - Main light source (80%)
3. **Secondary Directional** - Fill light (40%)
4. **Tertiary Directional** - Accent light (30%)
5. **Point Light** - Local highlight (50%)

### Environment Mapping

- Automatic PMREM generation from sky texture
- Real-time environment map updates
- Metallic reflections based on current panorama

## Customization

### Configuration Options

Edit `navigation-system.js`:

```javascript
const CONFIG = {
    DATA_FILE: 'cone_data.json',        // Cone data source
    PANORAMA_BASE_PATH: '',             // Base path for images
    SPHERE_SEGMENTS: 32,                // Sphere detail level
    RIBBON_WIDTH: 0.03,                 // Path ribbon width
    COMMENT_SIZE: 0.15,                 // Comment marker size
    MOUSE_SENSITIVITY: 1.0              // Look sensitivity
};
```

### Styling

Edit `styles.css` to customize:
- UI panel colors and transparency
- Button styles and gradients
- Loading indicator appearance
- Tooltip styling

## Performance Optimization

### Best Practices

1. **Image Optimization**
   - Use JPG format for panoramas
   - Recommended resolution: 4096x2048 or 8192x4096
   - Compress images to balance quality/size

2. **Material Sharing**
   - Shared materials across similar objects
   - Deferred environment map generation
   - Efficient THREE.js resource management

3. **Sphere Count**
   - System handles 45+ spheres efficiently
   - Consider LOD (Level of Detail) for 100+ cones

4. **Browser Performance**
   - Chrome/Edge recommended for best performance
   - Hardware acceleration should be enabled
   - Minimum 4GB RAM recommended

## Troubleshooting

### Common Issues

**Panoramas not loading:**
- Check `cone_data.json` image paths
- Ensure panoramas folder exists
- Verify image files are accessible
- Check browser console for errors

**Spheres not visible:**
- Toggle sphere visibility in UI
- Adjust sphere size slider
- Check if position coordinates are reasonable
- Verify cone data loaded successfully

**Navigation not working:**
- Click directly on spheres
- Ensure raycaster is working (check cursor)
- Verify click events in browser console

**Materials appear flat:**
- Wait for environment map to generate
- Check lighting system is active
- Verify THREE.js is loaded properly

### Debug Mode

Open browser console (F12) to see:
- Cone loading status
- Navigation events
- Material updates
- Error messages

## Integration with COLMAP

This system is designed to work with COLMAP reconstruction data:

1. **Export from COLMAP**
   - Use the `export_pointcloud.py` script
   - Generate cone metadata JSON
   - Extract 360° panoramas from reconstruction

2. **Data Mapping**
   - DXF positions → A-Frame world coordinates
   - Camera directions → Euler angles
   - Frame numbers → Image paths

3. **Coordinate Systems**
   - Right-handed coordinate system
   - Y-up orientation
   - Meters as base unit

## License

This project is part of the asBuilt COLMAP reconstruction system.

## Credits

- **A-Frame** - WebVR framework
- **THREE.js** - 3D graphics library
- **COLMAP** - Structure from Motion reconstruction

## Support

For issues or questions:
1. Check browser console for errors
2. Verify all files are present
3. Test with example cone_data.json
4. Ensure panorama images are valid

---

**Version**: 1.0.0  
**Last Updated**: October 2025







