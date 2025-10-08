import cv2
import os
import numpy as np

def calculate_sharpness(image):
    """Calculate image sharpness using Laplacian variance"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

# Create output directory
os.makedirs('VID_20251007_100811_00_008_frames', exist_ok=True)

# Open video
cap = cv2.VideoCapture('VID_20251007_100811_00_008.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
interval = int(fps * 2)  # Every 2 seconds

count = 0
frame_num = 0
window_frames = []
window_sharpness = []

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Collect frames within the 2-second window
    window_frames.append(frame)
    window_sharpness.append(calculate_sharpness(frame))
    
    # When we reach the end of a 2-second interval, save the sharpest frame
    if (frame_num + 1) % interval == 0 or not ret:
        if window_frames:
            # Find the sharpest frame in the window
            sharpest_idx = np.argmax(window_sharpness)
            sharpest_frame = window_frames[sharpest_idx]
            
            output_path = f'VID_20251007_100811_00_008_frames/frame_{count:04d}.jpg'
            cv2.imwrite(output_path, sharpest_frame)
            print(f'Frame {count}: sharpness = {window_sharpness[sharpest_idx]:.2f}')
            count += 1
            
            # Reset window
            window_frames = []
            window_sharpness = []
    
    frame_num += 1

# Handle any remaining frames in the last window
if window_frames:
    sharpest_idx = np.argmax(window_sharpness)
    sharpest_frame = window_frames[sharpest_idx]
    output_path = f'VID_20251007_100811_00_008_frames/frame_{count:04d}.jpg'
    cv2.imwrite(output_path, sharpest_frame)
    print(f'Frame {count}: sharpness = {window_sharpness[sharpest_idx]:.2f}')
    count += 1

cap.release()
print(f'\nExtracted {count} sharpest frames (every 2 seconds)')
