"""
Local proxy to the repository's COLMAP Python reader.

This small shim allows scripts in this folder to `import read_write_model`
and run the official implementation located at
`paul/scripts/python/read_write_model.py` without duplicating code.

It simply executes that file and re-exports its globals.
"""
from __future__ import annotations

import runpy
from pathlib import Path

ORIG = Path(__file__).resolve().parents[1] / 'scripts' / 'python' / 'read_write_model.py'
if not ORIG.exists():
    raise FileNotFoundError(f"Cannot find canonical read_write_model.py at {ORIG}")

# Execute and import everything
_g = runpy.run_path(str(ORIG))
globals().update(_g)
