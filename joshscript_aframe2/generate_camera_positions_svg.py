#!/usr/bin/env python3
"""
Generate SVG file with camera positions from COLMAP database
"""

import sqlite3
import numpy as np
import pyproj
from lxml import etree
import argparse
import os

def get_camera_positions(db_path):
    """Extract camera positions from COLMAP database"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query camera information
    camera_query = """
    SELECT camera_id, prior_focal_length, prior_principal_point_x, prior_principal_point_y
    FROM cameras
    ORDER BY camera_id
    """
    
    cursor.execute(camera_query)
    cameras = cursor.fetchall()
    
    # Query image positions (camera poses)
    image_query = """
    SELECT image_id, camera_id, name, prior_qw, prior_qx, prior_qy, prior_qz, 
           prior_tx, prior_ty, prior_tz
    FROM images
    ORDER BY image_id
    """
    
    cursor.execute(image_query)
    images = cursor.fetchall()
    
    conn.close()
    return cameras, images

def quaternion_to_rotation_matrix(qw, qx, qy, qz):
    """Convert quaternion to rotation matrix"""
    # Normalize quaternion
    norm = np.sqrt(qw*qw + qx*qx + qy*qy + qz*qz)
    qw, qx, qy, qz = qw/norm, qx/norm, qy/norm, qz/norm
    
    # Convert to rotation matrix
    R = np.array([
        [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx*qx + qy*qy)]
    ])
    
    return R

def transform_coordinates(coords, source_crs, target_crs):
    """Transform coordinates between different coordinate systems"""
    transformer = pyproj.Transformer.from_crs(source_crs, target_crs)
    return transformer.transform(coords[0], coords[1])

def create_camera_positions_svg(camera_data, output_path, svg_width=1000, svg_height=1000):
    """Create SVG file with camera positions"""
    
    # Create SVG root element
    svg = etree.Element("svg", 
                       xmlns="http://www.w3.org/2000/svg",
                       width="100%",
                       height="100%",
                       viewBox=f"0 0 {svg_width} {svg_height}",
                       overflow="visible")
    
    # Add style definitions
    style = etree.SubElement(svg, "style")
    style.text = """
    .camera-marker { cursor: pointer; }
    .camera-marker:hover { opacity: 0.7; }
    .camera-circle { fill: #ff4444; stroke: #000000; stroke-width: 2; }
    .camera-text { font-family: Arial, sans-serif; font-size: 12px; fill: #000000; text-anchor: middle; }
    .orientation-arrow { stroke: #0066cc; stroke-width: 2; fill: none; }
    """
    
    # Add camera positions group
    camera_group = etree.SubElement(svg, "g", id="camera-positions")
    
    # Add orientation arrows group
    orientation_group = etree.SubElement(svg, "g", id="camera-orientations")
    
    # Add camera markers
    for i, camera in enumerate(camera_data):
        x, y = camera['x'], camera['y']
        camera_id = camera.get('camera_id', i)
        
        # Create camera marker group
        marker_group = etree.SubElement(camera_group, "g", 
                                      id=f"camera-{camera_id}",
                                      class_="camera-marker")
        
        # Add circle for camera position
        circle = etree.SubElement(marker_group, "circle",
                                cx=str(x),
                                cy=str(y),
                                r="8",
                                class_="camera-circle")
        
        # Add camera ID text
        text = etree.SubElement(marker_group, "text",
                              x=str(x),
                              y=str(y - 15),
                              class_="camera-text")
        text.text = str(camera_id)
        
        # Add orientation arrow if available
        if 'orientation' in camera:
            ox, oy = camera['orientation']
            arrow_length = 20
            
            # Calculate arrow end point
            end_x = x + ox * arrow_length
            end_y = y + oy * arrow_length
            
            # Draw orientation arrow
            arrow = etree.SubElement(orientation_group, "line",
                                   x1=str(x),
                                   y1=str(y),
                                   x2=str(end_x),
                                   y2=str(end_y),
                                   class_="orientation-arrow")
            
            # Add arrowhead
            arrowhead = etree.SubElement(orientation_group, "polygon",
                                       points=f"{end_x},{end_y} {end_x-5},{end_y-3} {end_x-5},{end_y+3}",
                                       fill="#0066cc")
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(etree.tostring(svg, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

def process_colmap_data(db_path, output_path, coordinate_system='floorplan'):
    """Process COLMAP data and create SVG"""
    
    print(f"Processing COLMAP database: {db_path}")
    
    # Get camera data from database
    cameras, images = get_camera_positions(db_path)
    
    print(f"Found {len(cameras)} cameras and {len(images)} images")
    
    # Process camera positions
    camera_data = []
    
    for image in images:
        image_id, camera_id, name, qw, qx, qy, qz, tx, ty, tz = image
        
        # Convert quaternion to rotation matrix
        R = quaternion_to_rotation_matrix(qw, qx, qy, qz)
        
        # Camera position in world coordinates
        position = np.array([tx, ty, tz])
        
        # Camera orientation (forward direction)
        forward = R @ np.array([0, 0, 1])  # Z-axis is forward in COLMAP
        
        # For now, use simple 2D projection (top-down view)
        # In a real implementation, you'd need proper coordinate transformation
        x = position[0] * 100 + 500  # Scale and offset for SVG
        y = position[1] * 100 + 500
        
        camera_data.append({
            'camera_id': camera_id,
            'x': x,
            'y': y,
            'orientation': (forward[0], forward[1])
        })
    
    # Create SVG
    create_camera_positions_svg(camera_data, output_path)
    
    print(f"SVG created: {output_path}")
    print(f"Generated {len(camera_data)} camera markers")

def main():
    parser = argparse.ArgumentParser(description='Generate SVG from COLMAP database')
    parser.add_argument('--db', required=True, help='Path to COLMAP database file')
    parser.add_argument('--output', default='camera_positions.svg', help='Output SVG file path')
    parser.add_argument('--width', type=int, default=1000, help='SVG width')
    parser.add_argument('--height', type=int, default=1000, help='SVG height')
    
    args = parser.parse_args()
    
    try:
        process_colmap_data(args.db, args.output)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
