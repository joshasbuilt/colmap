from export_pointcloud import build_R_from_basisX, build_R_from_basisY, build_R_from_basisZ
import numpy as np

def rot_to_euler_zyx(R):
    # Returns [yaw(Z), pitch(Y), roll(X)] in degrees for R = Rz(yaw) @ Ry(pitch) @ Rx(roll)
    r20 = R[2,0]
    if abs(r20) < 0.999999:
        pitch = -np.arcsin(r20)
        cp = np.cos(pitch)
        roll = np.arctan2(R[2,1]/cp, R[2,2]/cp)
        yaw = np.arctan2(R[1,0]/cp, R[0,0]/cp)
    else:
        # Gimbal lock case
        yaw = 0.0
        if r20 <= -0.999999:
            pitch = np.pi/2
            roll = np.arctan2(R[0,1], R[0,2])
        else:
            pitch = -np.pi/2
            roll = np.arctan2(-R[0,1], -R[0,2])
    return np.degrees(np.array([yaw, pitch, roll]))

bx = (-0.128616418, 0.988815520, -0.075509499)
by = (0.078486847, -0.065753367, -0.994744344)
bz = (-0.988583649, -0.133866957, -0.069152050)

R_x = build_R_from_basisX(bx, by_hint=by)
R_y = build_R_from_basisY(by, bx_hint=bx)
R_z = build_R_from_basisZ(bz, bx_hint=bx)

angles_x = rot_to_euler_zyx(R_x)
angles_y = rot_to_euler_zyx(R_y)
angles_z = rot_to_euler_zyx(R_z)

np.set_printoptions(precision=6, suppress=True)
print('BasisX rotation matrix (R_x):')
print(R_x)
print('ZYX Euler [yaw(Z), pitch(Y), roll(X)] (deg):', angles_x)
print('\nBasisY rotation matrix (R_y):')
print(R_y)
print('ZYX Euler [yaw(Z), pitch(Y), roll(X)] (deg):', angles_y)
print('\nBasisZ rotation matrix (R_z):')
print(R_z)
print('ZYX Euler [yaw(Z), pitch(Y), roll(X)] (deg):', angles_z)
