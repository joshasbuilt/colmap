#!/usr/bin/env python3
"""Transform cone_data.json positions into an observer-local frame.

Reads `cone_data.json` in the same folder, applies an axis mapping (swap/negate Y/Z),
then computes positions relative to the first cone (treated as observer origin).
Writes `cone_data_transformed_frame.json` next to the input file.

Usage: python transform_cone_data_to_frame.py [--swap] [--negate_y] [--negate_z]
Default behavior: --swap (swap Y and Z), no negation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List


def load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]):
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def map_axes(x: float, y: float, z: float, swap: bool, negate_y: bool, negate_z: bool):
    # Start with (x, y, z)
    if swap:
        y, z = z, y
    if negate_y:
        y = -y
    if negate_z:
        z = -z
    return x, y, z


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', default='cone_data.json', help='Input cone_data.json path')
    parser.add_argument('--output', '-o', default='cone_data_transformed_frame.json', help='Output JSON path')
    parser.add_argument('--swap', action='store_true', default=True, help='Swap Y and Z axes')
    parser.add_argument('--no-swap', dest='swap', action='store_false', help='Do not swap Y and Z')
    parser.add_argument('--negate-y', action='store_true', help='Negate Y after swap')
    parser.add_argument('--negate-z', action='store_true', help='Negate Z after swap')
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return 1

    data = load_json(input_path)
    cones = data.get('cones', [])
    if not cones:
        print('No cones in input')
        return 1

    # Use first cone as observer origin
    first = cones[0]
    fp = first.get('dxf_position')
    if fp is None:
        print('First cone has no dxf_position')
        return 1
    fx, fy, fz = fp.get('x', 0.0), fp.get('y', 0.0), fp.get('z', 0.0)

    transformed: List[Dict[str, Any]] = []
    for cone in cones:
        d = cone.get('dxf_position', {})
        x, y, z = d.get('x', 0.0), d.get('y', 0.0), d.get('z', 0.0)
        x_m, y_m, z_m = map_axes(x, y, z, swap=args.swap, negate_y=args.negate_y, negate_z=args.negate_z)
        # Compute relative to observer
        rx = x_m - fx
        ry = y_m - fy
        rz = z_m - fz
        transformed.append({
            'cone_id': cone.get('cone_id'),
            'original_position': {'x': x, 'y': y, 'z': z},
            'mapped_position': {'x': x_m, 'y': y_m, 'z': z_m},
            'relative_position': {'x': rx, 'y': ry, 'z': rz}
        })

    out = {
        'source': str(input_path),
        'mapping': {
            'swap_yz': args.swap,
            'negate_y': args.negate_y,
            'negate_z': args.negate_z
        },
        'observer_cone_id': first.get('cone_id'),
        'transformed_cones': transformed
    }

    save_json(Path(args.output), out)
    print(f"Wrote: {args.output}")

    # Print first 5 relative positions
    print('\nFirst 5 relative positions (x,y,z):')
    for t in transformed[:5]:
        rp = t['relative_position']
        print(f"  cone {t['cone_id']}: ({rp['x']:.6f}, {rp['y']:.6f}, {rp['z']:.6f})")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
