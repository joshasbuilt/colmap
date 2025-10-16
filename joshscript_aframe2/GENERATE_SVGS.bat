@echo off
REM Batch file to generate SVG files from COLMAP sparse reconstruction folders

echo Generating SVG files from COLMAP sparse reconstructions...
echo.

python generate_svgs_from_sparse.py --sparse-dir "D:\Camera01\reconstruction_mask3_012_previews_run\sparse" --folders 0 1 2 3 4 5 6 --output-dir .

echo.
echo Done! SVG files have been generated in the current directory.
pause



