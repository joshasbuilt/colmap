import json

# Load cone data
with open('cone_data.json', 'r') as f:
    data = json.load(f)

# Check first few cones
print("First 3 cones coordinates:")
for i in range(3):
    cone = data['cones'][i]
    pos = cone['dxf_position']
    print(f"Cone {i+1}: X={pos['x']:.3f}, Y={pos['y']:.3f}, Z={pos['z']:.3f}")

# Check if there's a pattern
print("\nChecking for Z-Y swap pattern...")
x_vals = [cone['dxf_position']['x'] for cone in data['cones'][:10]]
y_vals = [cone['dxf_position']['y'] for cone in data['cones'][:10]]
z_vals = [cone['dxf_position']['z'] for cone in data['cones'][:10]]

print(f"X range: {min(x_vals):.3f} to {max(x_vals):.3f}")
print(f"Y range: {min(y_vals):.3f} to {max(y_vals):.3f}")
print(f"Z range: {min(z_vals):.3f} to {max(z_vals):.3f}")

# Check if Y and Z might be swapped
print(f"\nY values look like heights: {all(abs(y) < 1.0 for y in y_vals)}")
print(f"Z values look like heights: {all(abs(z) < 10.0 and abs(z) > 0.1 for z in z_vals)}")
