import cv2
import os
import time
from decouple import config

# Manually load .env if needed, or rely on decouple if it finds it
# Assuming run from backend directory

print("--- Camera Debug Script ---")

try:
    camera_source = config('CAMERA_SOURCE', default='')
except Exception as e:
    print(f"Error reading .env: {e}")
    camera_source = ''

print(f"CAMERA_SOURCE from env: '{camera_source}'")

if not camera_source:
    print("ERROR: CAMERA_SOURCE is empty.")
    exit(1)

print(f"Attempting to connect to: {camera_source}")
print("Please wait...")

start_time = time.time()
cap = cv2.VideoCapture(camera_source)
end_time = time.time()

print(f"cv2.VideoCapture call took {end_time - start_time:.2f} seconds")

if cap.isOpened():
    print("SUCCESS: Camera opened successfully!")
    ret, frame = cap.read()
    if ret:
        print(f"SUCCESS: Read a frame of shape {frame.shape}")
        # Optional: save it
        cv2.imwrite("debug_frame.jpg", frame)
        print("Saved debug_frame.jpg")
    else:
        print("WARNING: Camera opened but failed to read frame.")
else:
    print("FAILURE: Could not open camera.")
    print("Suggestions:")
    print("1. Check if the URL is correct.")
    print("2. Check if the device is reachable (ping the IP).")
    print("3. Try opening the URL in VLC Player.")
    print("4. If using an IP Webcam app, make sure it's running.")

cap.release()
print("--- End Debug ---")
