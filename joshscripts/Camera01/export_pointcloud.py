"""
Export COLMAP sparse reconstruction to point cloud formats for Cyclone
"""
import pycolmap
import numpy as np
from pathlib import Path
from datetime import datetime
import itertools

def export_to_pts(reconstruction, output_file, flip_yz=True):
    """Export to PTS format (X Y Z R G B Intensity) with optional Y and Z flip"""
    with open(output_file, 'w') as f:
        # Write header
        f.write(f"{reconstruction.num_points3D()}\n")
        
        # Write points
        for point_id, point in reconstruction.points3D.items():
            xyz = point.xyz
            rgb = point.color
            # PTS format: X Y Z R G B Intensity
            if flip_yz:
                # Flipping Y and Z: X Z Y becomes X Y Z
                intensity = int((int(rgb[0]) + int(rgb[1]) + int(rgb[2])) / 3.0)
                f.write(f"{xyz[0]:.6f} {xyz[2]:.6f} {xyz[1]:.6f} "
                       f"{rgb[0]} {rgb[1]} {rgb[2]} {intensity}\n")
            else:
                intensity = int((int(rgb[0]) + int(rgb[1]) + int(rgb[2])) / 3.0)
                f.write(f"{xyz[0]:.6f} {xyz[1]:.6f} {xyz[2]:.6f} "
                       f"{rgb[0]} {rgb[1]} {rgb[2]} {intensity}\n")
    
    print(f"Exported {reconstruction.num_points3D()} points to {output_file}")

def export_to_ply(reconstruction, output_file, flip_yz=True):
    """Export to PLY format with optional Y and Z flip"""
    with open(output_file, 'w') as f:
        # Write header
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {reconstruction.num_points3D()}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        
        # Write points
        for point_id, point in reconstruction.points3D.items():
            xyz = point.xyz
            rgb = point.color
            if flip_yz:
                f.write(f"{xyz[0]:.6f} {xyz[2]:.6f} {xyz[1]:.6f} "
                       f"{rgb[0]} {rgb[1]} {rgb[2]}\n")
            else:
                f.write(f"{xyz[0]:.6f} {xyz[1]:.6f} {xyz[2]:.6f} "
                       f"{rgb[0]} {rgb[1]} {rgb[2]}\n")
    
    print(f"Exported {reconstruction.num_points3D()} points to {output_file}")

def export_to_xyz(reconstruction, output_file, flip_yz=True):
    """Export to simple XYZ format (X Y Z R G B) with optional Y and Z flip"""
    with open(output_file, 'w') as f:
        for point_id, point in reconstruction.points3D.items():
            xyz = point.xyz
            rgb = point.color
            if flip_yz:
                f.write(f"{xyz[0]:.6f} {xyz[2]:.6f} {xyz[1]:.6f} "
                       f"{rgb[0]} {rgb[1]} {rgb[2]}\n")
            else:
                f.write(f"{xyz[0]:.6f} {xyz[1]:.6f} {xyz[2]:.6f} "
                       f"{rgb[0]} {rgb[1]} {rgb[2]}\n")
    
    print(f"Exported {reconstruction.num_points3D()} points to {output_file}")

def export_to_dxf_transformed(reconstruction, output_file, marker_size=0.02, scale=1.5,
                               origin_feet=(18.511377949, 28.950097280, 6.108436373),
                               basis_x=(-0.115146894, 0.991024226, -0.067913000),
                               basis_y=(0.086343771, -0.058123614, -0.994568448),
                               basis_z=(-0.989588776, -0.120385332, -0.078876015),
                               downsample_factor=1,
                               include_camera_poses=True,
                               camera_index=4):
    """Export to DXF format applying Revit affine transform:
    new = Origin_m + scale * R * orig
    origin_feet: Origin (X,Y,Z) from Revit in feet
    basis_x/y/z: basis vectors from Revit transform (defaults to identity)
    """
    # Convert origin from feet to meters
    origin_m = np.array(origin_feet) * 0.3048

    # Build rotation matrix R from basis vectors (columns)
    R = np.column_stack([np.array(basis_x), np.array(basis_y), np.array(basis_z)])

    # Extract camera poses if requested
    camera_poses = []
    if include_camera_poses:
        print(f"Extracting camera poses using camera index {camera_index}...")
        # Extract unique frame positions for visualization (45 positions from specified camera)
        camera_positions = []
        camera_directions = []  # Store forward direction vectors
        
        # Group images by frame_id and find the specific camera in each frame
        frame_cameras = {}  # frame_id -> list of images
        for image_id, image in reconstruction.images.items():
            if hasattr(image, 'frame_id') and image.frame_id is not None:
                if image.frame_id not in frame_cameras:
                    frame_cameras[image.frame_id] = []
                frame_cameras[image.frame_id].append(image)
        
        # For each frame, find the camera with matching index
        for frame_id in sorted(frame_cameras.keys()):
            images_in_frame = frame_cameras[frame_id]
            camera_found = False
            
            for image in images_in_frame:
                # Check if this is the camera we want (by checking image name)
                # Assuming image names contain camera index like "pano_camera4"
                if f"camera{camera_index}" in image.name.lower():
                    # Get this camera's position in world coordinates
                    # Camera center = -R^T * t where R and t are from cam_from_world
                    cam_from_world = image.cam_from_world()
                    rot_mat = cam_from_world.rotation.matrix()
                    cam_pos = -rot_mat.T @ cam_from_world.translation
                    
                    # Get camera's viewing direction using COLMAP's built-in method
                    cam_forward = image.viewing_direction().flatten()
                    
                    # Apply the EXACT same transformation as 3D points
                    transformed_pos = origin_m + scale * (R @ cam_pos)
                    transformed_pos = tuple(float(x) for x in transformed_pos)
                    
                    # Transform the direction vector (rotation only, no translation)
                    transformed_dir = R @ cam_forward
                    transformed_dir = transformed_dir / np.linalg.norm(transformed_dir)  # Normalize
                    
                    camera_positions.append(transformed_pos)
                    camera_directions.append(tuple(float(x) for x in transformed_dir))
                    camera_found = True
                    break
            
            if not camera_found and frame_id in reconstruction.frames:
                # Fallback to rig position if specific camera not found
                frame = reconstruction.frames[frame_id]
                if frame.has_pose:
                    frame_pos = frame.rig_from_world.translation
                    transformed_pos = origin_m + scale * (R @ frame_pos)
                    transformed_pos = tuple(float(x) for x in transformed_pos)
                    camera_positions.append(transformed_pos)
                    camera_directions.append((0.0, 0.0, 1.0))  # Default direction

        print(f"Found {len(camera_positions)} camera positions (using camera{camera_index})")
        print(f"Using camera viewing directions from COLMAP")

    with open(output_file, 'w') as f:
        # Write DXF header
        f.write("  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n")
        
        # Write TABLES section
        f.write("  0\nSECTION\n  2\nTABLES\n")
        f.write("  0\nTABLE\n  2\nLAYER\n 70\n     1\n")
        f.write("  0\nLAYER\n  2\n0\n 70\n     0\n 62\n   254\n  6\nCONTINUOUS\n")
        f.write("  0\nENDTAB\n  0\nENDSEC\n")
        
        # Write BLOCKS section
        f.write("  0\nSECTION\n  2\nBLOCKS\n  0\nENDSEC\n")
        
        # Write ENTITIES section
        f.write("  0\nSECTION\n  2\nENTITIES\n")
        
        # Create octahedron at each point with Revit affine applied
        point_count = 0
        for point_id, point in reconstruction.points3D.items():
            # Apply downsampling
            if point_count % downsample_factor != 0:
                point_count += 1
                continue
            point_count += 1
            xyz = np.array(point.xyz)

            # Apply full affine: new = origin_m + scale * R @ xyz
            transformed = origin_m + scale * (R @ xyz)
            x, y, z = float(transformed[0]), float(transformed[1]), float(transformed[2])
            
            # Scale the marker size too
            half = (marker_size * scale) / 2
            
            # Define 6 vertices of octahedron
            vertices = [
                (x + half, y, z),      # +X
                (x - half, y, z),      # -X
                (x, y + half, z),      # +Y
                (x, y - half, z),      # -Y
                (x, y, z + half),      # +Z
                (x, y, z - half),      # -Z
            ]
            
            # Define 8 triangular faces
            faces = [
                (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),  # Top pyramid
                (0, 5, 2), (2, 5, 1), (1, 5, 3), (3, 5, 0),  # Bottom pyramid
            ]
            
            # Write each triangular face as 3DFACE
            for face in faces:
                v1, v2, v3 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
                
                f.write("  0\n3DFACE\n")
                f.write("  8\n0\n")
                f.write(f" 10\n{v1[0]:.6f}\n")
                f.write(f" 20\n{v1[1]:.6f}\n")
                f.write(f" 30\n{v1[2]:.6f}\n")
                f.write(f" 11\n{v2[0]:.6f}\n")
                f.write(f" 21\n{v2[1]:.6f}\n")
                f.write(f" 31\n{v2[2]:.6f}\n")
                f.write(f" 12\n{v3[0]:.6f}\n")
                f.write(f" 22\n{v3[1]:.6f}\n")
                f.write(f" 32\n{v3[2]:.6f}\n")
                f.write(f" 13\n{v3[0]:.6f}\n")
                f.write(f" 23\n{v3[1]:.6f}\n")
                f.write(f" 33\n{v3[2]:.6f}\n")

        # Add camera position cones (big directional markers)
        if include_camera_poses and camera_positions:
            print("Adding camera position directional cones...")
            camera_marker_size = marker_size * scale * 5.0  # 5x larger than point markers

            for i, pos in enumerate(camera_positions):
                x, y, z = pos
                direction = np.array(camera_directions[i])
                
                # Create a cone pointing in the direction of travel/camera forward
                # Cone: tip at camera position, base extending in forward direction (wide end leads)
                cone_length = camera_marker_size * 2.0  # Length of cone
                base_radius = camera_marker_size / 2  # Radius of cone base
                
                # Tip of cone at camera position
                tip = np.array([x, y, z])
                # Base center in direction of travel
                base_center = np.array([x, y, z]) + direction * cone_length
                
                # Create a perpendicular basis for the base circle
                # Find two perpendicular vectors to direction
                if abs(direction[0]) < 0.9:
                    perp1 = np.cross(direction, [1, 0, 0])
                else:
                    perp1 = np.cross(direction, [0, 1, 0])
                perp1 = perp1 / np.linalg.norm(perp1) * base_radius
                perp2 = np.cross(direction, perp1)
                perp2 = perp2 / np.linalg.norm(perp2) * base_radius
                
                # Create 8 points around the base circle (at the wide end, in direction of travel)
                n_sides = 8
                base_vertices = []
                for j in range(n_sides):
                    angle = 2 * np.pi * j / n_sides
                    base_pt = base_center + np.cos(angle) * perp1 + np.sin(angle) * perp2
                    base_vertices.append(tuple(float(c) for c in base_pt))
                
                tip_tuple = tuple(float(c) for c in tip)
                
                # Create triangular faces from base to tip
                for j in range(n_sides):
                    v1 = base_vertices[j]
                    v2 = base_vertices[(j + 1) % n_sides]
                    v3 = tip_tuple
                    
                    f.write("  0\n3DFACE\n")
                    f.write("  8\n1\n")  # Layer 1 for camera positions
                    f.write(f" 10\n{v1[0]:.6f}\n")
                    f.write(f" 20\n{v1[1]:.6f}\n")
                    f.write(f" 30\n{v1[2]:.6f}\n")
                    f.write(f" 11\n{v2[0]:.6f}\n")
                    f.write(f" 21\n{v2[1]:.6f}\n")
                    f.write(f" 31\n{v2[2]:.6f}\n")
                    f.write(f" 12\n{v3[0]:.6f}\n")
                    f.write(f" 22\n{v3[1]:.6f}\n")
                    f.write(f" 32\n{v3[2]:.6f}\n")
                    f.write(f" 13\n{v3[0]:.6f}\n")
                    f.write(f" 23\n{v3[1]:.6f}\n")
                    f.write(f" 33\n{v3[2]:.6f}\n")
                
                # Also create base cap at the wide end (for better visibility)
                center = tuple(float(c) for c in base_center)
                for j in range(n_sides):
                    v1 = center
                    v2 = base_vertices[j]
                    v3 = base_vertices[(j + 1) % n_sides]
                    
                    f.write("  0\n3DFACE\n")
                    f.write("  8\n1\n")
                    f.write(f" 10\n{v1[0]:.6f}\n")
                    f.write(f" 20\n{v1[1]:.6f}\n")
                    f.write(f" 30\n{v1[2]:.6f}\n")
                    f.write(f" 11\n{v2[0]:.6f}\n")
                    f.write(f" 21\n{v2[1]:.6f}\n")
                    f.write(f" 31\n{v2[2]:.6f}\n")
                    f.write(f" 12\n{v3[0]:.6f}\n")
                    f.write(f" 22\n{v3[1]:.6f}\n")
                    f.write(f" 32\n{v3[2]:.6f}\n")
                    f.write(f" 13\n{v3[0]:.6f}\n")
                    f.write(f" 23\n{v3[1]:.6f}\n")
                    f.write(f" 33\n{v3[2]:.6f}\n")

        # End entities section
        f.write("  0\nENDSEC\n")
        f.write("  0\nEOF\n")
    
    point_faces = reconstruction.num_points3D() * 8
    camera_faces = len(camera_positions) * 16 if include_camera_poses and camera_positions else 0  # 16 faces per cone (8 sides + 8 base)

    print(f"Exported {reconstruction.num_points3D()} points as transformed octahedrons to {output_file}")
    print(f"  Scale: {scale}x")
    print(f"  Origin (feet): {origin_feet}")
    print(f"  Origin applied (meters): ({origin_m[0]:.6f}, {origin_m[1]:.6f}, {origin_m[2]:.6f})")
    print(f"  BasisX: {basis_x}")
    print(f"  BasisY: {basis_y}")
    print(f"  BasisZ: {basis_z}")
    print(f"  Marker size: {marker_size * scale:.6f} units")
    print(f"  Point cloud faces: {point_faces}")

    if include_camera_poses and camera_positions:
        camera_marker_size = marker_size * scale * 5.0
        print(f"  Camera positions: {len(camera_positions)} directional cones (using camera{camera_index} from each frame)")
        print(f"  Camera cone size: {camera_marker_size:.3f} units")
        print(f"  Camera cone faces: {camera_faces}")

    print(f"  Total faces: {point_faces + camera_faces}")


def export_to_dxf_rotation(reconstruction, output_file, R, marker_size=0.02):
    """Export to DXF with only rotation applied (no translation, no scale).
    R: 3x3 numpy array rotation matrix applied as new = R @ orig
    """
    with open(output_file, 'w') as f:
        f.write("  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nTABLES\n")
        f.write("  0\nTABLE\n  2\nLAYER\n 70\n     1\n")
        f.write("  0\nLAYER\n  2\n0\n 70\n     0\n 62\n   254\n  6\nCONTINUOUS\n")
        f.write("  0\nENDTAB\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nBLOCKS\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nENTITIES\n")

        for point_id, point in reconstruction.points3D.items():
            xyz = np.array(point.xyz)
            rotated = R @ xyz
            x, y, z = float(rotated[0]), float(rotated[1]), float(rotated[2])

            half = marker_size / 2
            vertices = [
                (x + half, y, z),
                (x - half, y, z),
                (x, y + half, z),
                (x, y - half, z),
                (x, y, z + half),
                (x, y, z - half),
            ]
            faces = [
                (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                (0, 5, 2), (2, 5, 1), (1, 5, 3), (3, 5, 0),
            ]

            for face in faces:
                v1, v2, v3 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
                f.write("  0\n3DFACE\n")
                f.write("  8\n0\n")
                f.write(f" 10\n{v1[0]:.6f}\n")
                f.write(f" 20\n{v1[1]:.6f}\n")
                f.write(f" 30\n{v1[2]:.6f}\n")
                f.write(f" 11\n{v2[0]:.6f}\n")
                f.write(f" 21\n{v2[1]:.6f}\n")
                f.write(f" 31\n{v2[2]:.6f}\n")
                f.write(f" 12\n{v3[0]:.6f}\n")
                f.write(f" 22\n{v3[1]:.6f}\n")
                f.write(f" 32\n{v3[2]:.6f}\n")
                f.write(f" 13\n{v3[0]:.6f}\n")
                f.write(f" 23\n{v3[1]:.6f}\n")
                f.write(f" 33\n{v3[2]:.6f}\n")

        f.write("  0\nENDSEC\n")
        f.write("  0\nEOF\n")

    print(f"Exported {reconstruction.num_points3D()} points as rotated octahedrons to {output_file}")


def export_rotation_variants(reconstruction, outdir, timestamp):
    """Generate DXF files for unique rotation matrices built from 90-degree Euler steps.
    Produces unique matrices (deduplicated) for rx,ry,rz in {0,90,180,270} degrees.
    """
    def Rx(deg):
        r = np.deg2rad(deg)
        c, s = np.cos(r), np.sin(r)
        return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    def Ry(deg):
        r = np.deg2rad(deg)
        c, s = np.cos(r), np.sin(r)
        return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    def Rz(deg):
        r = np.deg2rad(deg)
        c, s = np.cos(r), np.sin(r)
        return np.array([[c,-s,0],[s,c,0],[0,0,1]])

    angles = [0,90,180,270]
    mats = {}
    for rx in angles:
        for ry in angles:
            for rz in angles:
                # Apply rotations in X, then Y, then Z order
                R = Rz(rz) @ Ry(ry) @ Rx(rx)
                key = np.array2string(R, precision=6)
                if key not in mats:
                    mats[key] = (R, (rx,ry,rz))

    print(f"Preparing to export {len(mats)} rotation-only DXF variants into {outdir}")
    rdir = outdir / f"rotations_{timestamp}"
    rdir.mkdir(exist_ok=True)

    for key, (R, angles) in mats.items():
        rx, ry, rz = angles
        name = f"rot_rx{rx}_ry{ry}_rz{rz}"
        out_file = rdir / f"pointcloud_{name}_{timestamp}.dxf"
        export_to_dxf_rotation(reconstruction, out_file, R, marker_size=0.02)

    print(f"Wrote {len(mats)} rotation DXF files to {rdir}")


def export_axis_rotations(reconstruction, outdir, timestamp, angles=None, marker_size=0.02):
    """Export DXFs rotating around a single axis at the provided angles (degrees).
    Creates subfolders X/, Y/, Z/ under outdir/axis_rotations_{timestamp}.
    """
    if angles is None:
        angles = [-180, -135, -90, -45, 0, 45, 90, 135, 180]

    def Rx(deg):
        r = np.deg2rad(deg); c,s = np.cos(r), np.sin(r)
        return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    def Ry(deg):
        r = np.deg2rad(deg); c,s = np.cos(r), np.sin(r)
        return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    def Rz(deg):
        r = np.deg2rad(deg); c,s = np.cos(r), np.sin(r)
        return np.array([[c,-s,0],[s,c,0],[0,0,1]])

    base_dir = outdir / f"axis_rotations_{timestamp}"
    base_dir.mkdir(exist_ok=True)

    axes = {'X': Rx, 'Y': Ry, 'Z': Rz}
    total = 0
    for ax_name, ax_fn in axes.items():
        sdir = base_dir / ax_name
        sdir.mkdir(exist_ok=True)
        for ang in angles:
            R = ax_fn(ang)
            safe = f"rot_{ax_name}{ang:+03d}"
            out_file = sdir / f"pointcloud_{safe}_{timestamp}.dxf"
            export_to_dxf_rotation(reconstruction, out_file, R, marker_size=marker_size)
            total += 1

    print(f"Wrote {total} axis-rotation DXF files to {base_dir} (subfolders X,Y,Z)")


def export_single_axis_rotations(reconstruction, outdir, timestamp, axis='Z', angles=None, marker_size=0.02):
    """Export a small, focused set of rotations about a single axis.
    axis: 'X','Y' or 'Z'. Default 'Z'.
    angles: list of degrees; default logical order: [0,90,-90,180,45,-45]
    Writes to outdir/axis_rot_<axis>_<timestamp>/
    """
    if angles is None:
        angles = [0, 90, -90, 180, 45, -45]

    def Rx(deg):
        r = np.deg2rad(deg); c,s = np.cos(r), np.sin(r)
        return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    def Ry(deg):
        r = np.deg2rad(deg); c,s = np.cos(r), np.sin(r)
        return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    def Rz(deg):
        r = np.deg2rad(deg); c,s = np.cos(r), np.sin(r)
        return np.array([[c,-s,0],[s,c,0],[0,0,1]])

    funcs = {'X': Rx, 'Y': Ry, 'Z': Rz}
    if axis not in funcs:
        raise ValueError("axis must be 'X','Y' or 'Z'")

    adir = outdir / f"axis_rot_{axis}_{timestamp}"
    adir.mkdir(exist_ok=True)

    fn = funcs[axis]
    for ang in angles:
        R = fn(ang)
        sign = f"{ang:+03d}".replace('+', '+')
        out_file = adir / f"pointcloud_rot_{axis}{sign}_{timestamp}.dxf"
        export_to_dxf_rotation(reconstruction, out_file, R, marker_size=marker_size)

    print(f"Wrote {len(angles)} rotation DXFs for axis {axis} to {adir}")


def export_to_dxf_inverse_rotation(reconstruction, output_file, R_inv, marker_size=0.02):
    """Export to DXF applying inverse rotation R_inv (R_inv @ orig)."""
    with open(output_file, 'w') as f:
        f.write("  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nTABLES\n")
        f.write("  0\nTABLE\n  2\nLAYER\n 70\n     1\n")
        f.write("  0\nLAYER\n  2\n0\n 70\n     0\n 62\n   254\n  6\nCONTINUOUS\n")
        f.write("  0\nENDTAB\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nBLOCKS\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nENTITIES\n")

        for point_id, point in reconstruction.points3D.items():
            xyz = np.array(point.xyz)
            transformed = R_inv @ xyz
            x, y, z = float(transformed[0]), float(transformed[1]), float(transformed[2])

            half = marker_size / 2
            vertices = [
                (x + half, y, z),
                (x - half, y, z),
                (x, y + half, z),
                (x, y - half, z),
                (x, y, z + half),
                (x, y, z - half),
            ]
            faces = [
                (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                (0, 5, 2), (2, 5, 1), (1, 5, 3), (3, 5, 0),
            ]

            for face in faces:
                v1, v2, v3 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
                f.write("  0\n3DFACE\n")
                f.write("  8\n0\n")
                f.write(f" 10\n{v1[0]:.6f}\n")
                f.write(f" 20\n{v1[1]:.6f}\n")
                f.write(f" 30\n{v1[2]:.6f}\n")
                f.write(f" 11\n{v2[0]:.6f}\n")
                f.write(f" 21\n{v2[1]:.6f}\n")
                f.write(f" 31\n{v2[2]:.6f}\n")
                f.write(f" 12\n{v3[0]:.6f}\n")
                f.write(f" 22\n{v3[1]:.6f}\n")
                f.write(f" 32\n{v3[2]:.6f}\n")
                f.write(f" 13\n{v3[0]:.6f}\n")
                f.write(f" 23\n{v3[1]:.6f}\n")
                f.write(f" 33\n{v3[2]:.6f}\n")

        f.write("  0\nENDSEC\n")
        f.write("  0\nEOF\n")

    print(f"Exported {reconstruction.num_points3D()} points with inverse rotation to {output_file}")


def export_to_dxf_inverse_rotation_after_translation(reconstruction, output_file, R_inv, origin_feet, marker_size=0.02):
    """Export to DXF applying inverse rotation to the inverse-translated cloud: R_inv @ (orig - origin_m)."""
    origin_m = np.array(origin_feet) * 0.3048
    with open(output_file, 'w') as f:
        f.write("  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nTABLES\n")
        f.write("  0\nTABLE\n  2\nLAYER\n 70\n     1\n")
        f.write("  0\nLAYER\n  2\n0\n 70\n     0\n 62\n   254\n  6\nCONTINUOUS\n")
        f.write("  0\nENDTAB\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nBLOCKS\n  0\nENDSEC\n")
        f.write("  0\nSECTION\n  2\nENTITIES\n")

        for point_id, point in reconstruction.points3D.items():
            xyz = np.array(point.xyz)
            transformed = R_inv @ (xyz - origin_m)
            x, y, z = float(transformed[0]), float(transformed[1]), float(transformed[2])

            half = marker_size / 2
            vertices = [
                (x + half, y, z),
                (x - half, y, z),
                (x, y + half, z),
                (x, y - half, z),
                (x, y, z + half),
                (x, y, z - half),
            ]
            faces = [
                (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                (0, 5, 2), (2, 5, 1), (1, 5, 3), (3, 5, 0),
            ]

            for face in faces:
                v1, v2, v3 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
                f.write("  0\n3DFACE\n")
                f.write("  8\n0\n")
                f.write(f" 10\n{v1[0]:.6f}\n")
                f.write(f" 20\n{v1[1]:.6f}\n")
                f.write(f" 30\n{v1[2]:.6f}\n")
                f.write(f" 11\n{v2[0]:.6f}\n")
                f.write(f" 21\n{v2[1]:.6f}\n")
                f.write(f" 31\n{v2[2]:.6f}\n")
                f.write(f" 12\n{v3[0]:.6f}\n")
                f.write(f" 22\n{v3[1]:.6f}\n")
                f.write(f" 32\n{v3[2]:.6f}\n")
                f.write(f" 13\n{v3[0]:.6f}\n")
                f.write(f" 23\n{v3[1]:.6f}\n")
                f.write(f" 33\n{v3[2]:.6f}\n")

        f.write("  0\nENDSEC\n")
        f.write("  0\nEOF\n")

    print(f"Exported {reconstruction.num_points3D()} points with inverse rotation after translation to {output_file}")


def build_R_from_basisX(bx, by_hint=(0.0, 1.0, 0.0)):
    """Build an orthonormal rotation matrix where the X column is aligned to bx.
    by_hint is used to seed Gram-Schmidt for the remaining axes.
    Returns R (3x3) with columns [u1, u2, u3].
    """
    bx = np.array(bx, dtype=float)
    if np.linalg.norm(bx) == 0:
        raise ValueError('basis_x must be non-zero')
    u1 = bx / np.linalg.norm(bx)

    by = np.array(by_hint, dtype=float)
    # Make by orthogonal to u1
    proj = np.dot(u1, by) * u1
    v2 = by - proj
    if np.linalg.norm(v2) < 1e-8:
        # fallback pick a perpendicular vector
        if abs(u1[0]) < 0.9:
            v2 = np.array([1.0, 0.0, 0.0]) - np.dot(u1, [1.0,0.0,0.0]) * u1
        else:
            v2 = np.array([0.0, 1.0, 0.0]) - np.dot(u1, [0.0,1.0,0.0]) * u1

    u2 = v2 / np.linalg.norm(v2)
    u3 = np.cross(u1, u2)
    u3 = u3 / np.linalg.norm(u3)

    R = np.column_stack([u1, u2, u3])
    return R


def export_basisX_only(reconstruction, outdir, timestamp,
                       basis_x=(-0.128616418, 0.988815520, -0.075509499),
                       basis_y_hint=(0.078486847, -0.065753367, -0.994744344),
                       marker_size=0.02):
    """Export a single DXF applying rotation R built from BasisX only (no translation/scale)."""
    R = build_R_from_basisX(basis_x, basis_y_hint)
    bdir = outdir / f"basisX_only_{timestamp}"
    bdir.mkdir(exist_ok=True)
    out_file = bdir / f"pointcloud_basisX_only_{timestamp}.dxf"
    export_to_dxf_rotation(reconstruction, out_file, R, marker_size=marker_size)
    print(f"Wrote basisX-only DXF to {out_file}")


def build_R_from_basisY(by, bx_hint=(1.0, 0.0, 0.0)):
    """Build an orthonormal rotation matrix where the Y column is aligned to by.
    bx_hint seeds Gram-Schmidt for the remaining axes. Returns R with columns [u1,u2,u3].
    """
    by = np.array(by, dtype=float)
    if np.linalg.norm(by) == 0:
        raise ValueError('basis_y must be non-zero')
    u2 = by / np.linalg.norm(by)

    # Choose a stable global reference (prefer Z) that's not parallel to u2
    ref = np.array([0.0, 0.0, 1.0], dtype=float)
    if abs(np.dot(u2, ref)) > 0.95:
        # too parallel, use X as fallback
        ref = np.array([1.0, 0.0, 0.0], dtype=float)

    # Build u3 as cross(u2, ref) then u1 = cross(u2, u3)
    u3 = np.cross(u2, ref)
    u3 = u3 / np.linalg.norm(u3)
    u1 = np.cross(u2, u3)
    u1 = u1 / np.linalg.norm(u1)

    R = np.column_stack([u1, u2, u3])
    return R


def export_basisY_only(reconstruction, outdir, timestamp,
                       basis_y=(0.078486847, -0.065753367, -0.994744344),
                       basis_x_hint=(-0.128616418, 0.988815520, -0.075509499),
                       marker_size=0.02):
    """Export a single DXF applying rotation R built from BasisY only (no translation/scale)."""
    R = build_R_from_basisY(basis_y, basis_x_hint)
    bdir = outdir / f"basisY_only_{timestamp}"
    bdir.mkdir(exist_ok=True)
    out_file = bdir / f"pointcloud_basisY_only_{timestamp}.dxf"
    export_to_dxf_rotation(reconstruction, out_file, R, marker_size=marker_size)
    print(f"Wrote basisY-only DXF to {out_file}")


def build_R_from_basisZ(bz, bx_hint=(1.0, 0.0, 0.0)):
    """Build an orthonormal rotation matrix where the Z column is aligned to bz.
    bx_hint seeds a stable reference if bz is nearly parallel to the preferred reference.
    Returns R with columns [u1,u2,u3].
    """
    bz = np.array(bz, dtype=float)
    if np.linalg.norm(bz) == 0:
        raise ValueError('basis_z must be non-zero')
    u3 = bz / np.linalg.norm(bz)

    # Prefer a global reference X; if parallel to u3, fallback to Y
    ref = np.array([1.0, 0.0, 0.0], dtype=float)
    if abs(np.dot(u3, ref)) > 0.95:
        ref = np.array([0.0, 1.0, 0.0], dtype=float)

    # Build u1 as cross(ref, u3) then u2 = cross(u3, u1)
    u1 = np.cross(ref, u3)
    u1 = u1 / np.linalg.norm(u1)
    u2 = np.cross(u3, u1)
    u2 = u2 / np.linalg.norm(u2)

    R = np.column_stack([u1, u2, u3])
    return R


def export_basisZ_only(reconstruction, outdir, timestamp,
                       basis_z=(-0.988583649, -0.133866957, -0.069152050),
                       basis_x_hint=(1.0, 0.0, 0.0),
                       marker_size=0.02):
    """Export a single DXF applying rotation R built from BasisZ only (no translation/scale)."""
    R = build_R_from_basisZ(basis_z, basis_x_hint)
    bdir = outdir / f"basisZ_only_{timestamp}"
    bdir.mkdir(exist_ok=True)
    out_file = bdir / f"pointcloud_basisZ_only_{timestamp}.dxf"
    export_to_dxf_rotation(reconstruction, out_file, R, marker_size=marker_size)
    print(f"Wrote basisZ-only DXF to {out_file}")

def export_to_dxf(reconstruction, output_file, marker_size=0.2, flip_yz=True):
    """Export to DXF format with small octahedron markers at each point
    Octahedrons are simple 8-faced shapes that are visible from all angles
    Optional Y and Z flip for coordinate system adjustment"""
    
    with open(output_file, 'w') as f:
        # Write DXF header
        f.write("  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n")
        
        # Write TABLES section
        f.write("  0\nSECTION\n  2\nTABLES\n")
        f.write("  0\nTABLE\n  2\nLAYER\n 70\n     1\n")
        f.write("  0\nLAYER\n  2\n0\n 70\n     0\n 62\n   254\n  6\nCONTINUOUS\n")
        f.write("  0\nENDTAB\n  0\nENDSEC\n")
        
        # Write BLOCKS section
        f.write("  0\nSECTION\n  2\nBLOCKS\n  0\nENDSEC\n")
        
        # Write ENTITIES section
        f.write("  0\nSECTION\n  2\nENTITIES\n")
        
        # Create octahedron at each point (6 vertices, 8 triangular faces)
        for point_id, point in reconstruction.points3D.items():
            xyz = point.xyz
            # Apply flip if requested
            if flip_yz:
                x, y, z = xyz[0], xyz[2], xyz[1]
            else:
                x, y, z = xyz[0], xyz[1], xyz[2]
            
            # Define 6 vertices of octahedron (axis-aligned diamond shape)
            half = marker_size / 2
            vertices = [
                (x + half, y, z),      # +X
                (x - half, y, z),      # -X
                (x, y + half, z),      # +Y
                (x, y - half, z),      # -Y
                (x, y, z + half),      # +Z
                (x, y, z - half),      # -Z
            ]
            
            # Define 8 triangular faces (indices into vertices)
            faces = [
                (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),  # Top pyramid
                (0, 5, 2), (2, 5, 1), (1, 5, 3), (3, 5, 0),  # Bottom pyramid
            ]
            
            # Write each triangular face as 3DFACE
            for face in faces:
                v1, v2, v3 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
                
                f.write("  0\n3DFACE\n")
                f.write("  8\n0\n")
                f.write(f" 10\n{v1[0]:.6f}\n")
                f.write(f" 20\n{v1[1]:.6f}\n")
                f.write(f" 30\n{v1[2]:.6f}\n")
                f.write(f" 11\n{v2[0]:.6f}\n")
                f.write(f" 21\n{v2[1]:.6f}\n")
                f.write(f" 31\n{v2[2]:.6f}\n")
                f.write(f" 12\n{v3[0]:.6f}\n")
                f.write(f" 22\n{v3[1]:.6f}\n")
                f.write(f" 32\n{v3[2]:.6f}\n")
                f.write(f" 13\n{v3[0]:.6f}\n")  # Repeat last vertex for triangle
                f.write(f" 23\n{v3[1]:.6f}\n")
                f.write(f" 33\n{v3[2]:.6f}\n")
        
        # End entities section
        f.write("  0\nENDSEC\n")
        f.write("  0\nEOF\n")
    
    print(f"Exported {reconstruction.num_points3D()} points as octahedron markers to {output_file}")
    print(f"  Each octahedron is {marker_size} units across (8 triangular faces)")
    print(f"  Total faces: {reconstruction.num_points3D() * 8}")

def export_camera_positions(reconstruction, output_file):
    """Export camera positions as TXT file"""
    with open(output_file, 'w') as f:
        f.write("# Image_ID Camera_ID Image_Name X Y Z QW QX QY QZ\n")
        for image_id, image in reconstruction.images.items():
            # Get camera center (inverse transform)
            rot_mat = image.cam_from_world().rotation().matrix().T
            cam_center = -rot_mat @ image.cam_from_world().translation()
            quat = image.cam_from_world().rotation().quat()  # [w, x, y, z]
            f.write(f"{image_id} {image.camera_id} {image.name} "
                   f"{cam_center[0]:.6f} {cam_center[1]:.6f} {cam_center[2]:.6f} "
                   f"{quat[0]:.6f} {quat[1]:.6f} {quat[2]:.6f} {quat[3]:.6f}\n")
    
    print(f"Exported {reconstruction.num_images()} camera positions to {output_file}")

def main():
    # Load reconstruction
    recon_path = Path("reconstruction_single/sparse/0")
    output_dir = Path("reconstruction_single/exports")
    output_dir.mkdir(exist_ok=True)
    
    # Create datetime suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Loading reconstruction from {recon_path}...")
    reconstruction = pycolmap.Reconstruction(str(recon_path))
    
    print(f"\nReconstruction summary:")
    print(f"  Cameras: {reconstruction.num_cameras()}")
    print(f"  Registered images: {reconstruction.num_images()}")
    print(f"  3D points: {reconstruction.num_points3D()}")
    print(f"\nExporting a single, focused DXF using BasisZ only (no mass variants)...\n")
    export_basisZ_only(
        reconstruction, output_dir, timestamp,
        basis_z=(-0.988583649, -0.133866957, -0.069152050),
        basis_x_hint=(1.0, 0.0, 0.0),
        marker_size=0.02,
    )
    
    print("\n" + "="*70)
    print("Export complete!")
    print("="*70)
    print(f"\nOutput files in: {output_dir}")
    print(f"  - basisX-only folder: basisX_only_{timestamp} (single DXF)")

if __name__ == "__main__":
    main()
