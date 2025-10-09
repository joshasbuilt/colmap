@echo off
cd /d "C:\Users\JoshuaLumley\Dropbox\0000 Github Repos\asBuilt_DataColmap\paul\joshscripts\Camera01"
echo Starting COLMAP reconstruction...
echo Frame directory: VID_20251007_170505_00_012_frames
echo Mask template: mask_template3.png
echo Output directory: reconstruction_VID_20251007_170505_00_012
echo.
python run_single_video.py
echo.
echo Reconstruction complete! Press any key to close...
pause






