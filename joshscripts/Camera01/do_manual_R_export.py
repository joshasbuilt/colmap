from pathlib import Path
from datetime import datetime
import numpy as np
import pycolmap
from export_pointcloud import export_to_dxf_rotation

# Revit basis vectors (columns of R) provided by you
basis_x = np.array([-0.115146894, 0.991024226, -0.067913000])
basis_y = np.array([0.086343771, -0.058123614, -0.994568448])
basis_z = np.array([-0.989588776, -0.120385332, -0.078876015])

# Build rotation matrix R with columns [BasisX, BasisY, BasisZ]
R = np.column_stack([basis_x, basis_y, basis_z])

# Z-Y-X (yaw, pitch, roll) decomposition
def rot_to_euler_zyx(R):
    # yaw (Z), pitch (Y), roll (X)
    r11, r21, r31 = R[0,0], R[1,0], R[2,0]
    r32, r33 = R[2,1], R[2,2]
    yaw = np.arctan2(r21, r11)
    pitch = np.arcsin(-R[2,0])
    roll = np.arctan2(r32, r33)
    return np.degrees(np.array([yaw, pitch, roll]))

angles = rot_to_euler_zyx(R)

# Axis-angle from rotation matrix
def rotation_matrix_to_axis_angle(R):
    # Using Rodrigues' formula inverse
    angle = np.arccos(max(min((np.trace(R) - 1) / 2, 1.0), -1.0))
    if abs(angle) < 1e-8:
        return np.array([1.0,0.0,0.0]), 0.0
    rx = (R[2,1] - R[1,2]) / (2*np.sin(angle))
    ry = (R[0,2] - R[2,0]) / (2*np.sin(angle))
    rz = (R[1,0] - R[0,1]) / (2*np.sin(angle))
    axis = np.array([rx, ry, rz])
    axis = axis / np.linalg.norm(axis)
    return axis, np.degrees(angle)

axis, angle_deg = rotation_matrix_to_axis_angle(R)

# Print results
print('\nManual Revit rotation matrix R (columns are BasisX, BasisY, BasisZ):')
np.set_printoptions(precision=9, suppress=True)
print(R)
print('\nZYX Euler angles [yaw(Z), pitch(Y), roll(X)] in degrees:')
print(f"yaw={angles[0]:.6f}°, pitch={angles[1]:.6f}°, roll={angles[2]:.6f}°")
print('\nAxis-angle representation:')
print(f"axis=[{axis[0]:.6f}, {axis[1]:.6f}, {axis[2]:.6f}], angle={angle_deg:.6f}°")

# Load reconstruction and export DXF applying R (rotation-only)
recon_path = Path("reconstruction_single/sparse/0")
reconstruction = pycolmap.Reconstruction(str(recon_path))

output_dir = Path("reconstruction_single/exports")
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_dir = output_dir / f"manual_R_{timestamp}"
out_dir.mkdir(exist_ok=True)
out_file = out_dir / f"pointcloud_manual_R_{timestamp}.dxf"

export_to_dxf_rotation(reconstruction, out_file, R, marker_size=0.02)
print(f"\nWrote DXF with manual R to: {out_file}\n")
