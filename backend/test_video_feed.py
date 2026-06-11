"""
Test the video feed endpoint directly to see if it works
"""
import cv2
import time

print("Testing video feed with current configuration...")
print("=" * 60)

# Simulate what the video feed endpoint does
source = "http://10.145.76.160:8080/video"
print(f"Camera source: {source}\n")

# Retry logic (same as in gen_frames)
max_retries = 3
retry_delay = 1

for attempt in range(max_retries):
    try:
        print(f"[VIDEO_FEED] Connection attempt {attempt + 1}/{max_retries}")
        
        if attempt > 0:
            wait_time = retry_delay * (2 ** attempt)
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
        
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        
        if not cap.isOpened():
            print(f"❌ Could not open camera (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                continue
            else:
                print("\n⚠️ Max retries reached. Camera feed would fail.")
                break
        
        print("✅ Camera opened successfully!")
        
        # Try to read a few frames
        for i in range(5):
            success, frame = cap.read()
            if not success:
                print(f"❌ Failed to read frame {i+1}/5")
            else:
                print(f"✅ Frame {i+1}/5 read successfully - Shape: {frame.shape}")
        
        cap.release()
        print("\n✅ Video feed test completed successfully!")
        print("The camera feed should work in the backend.")
        break
        
    except Exception as e:
        print(f"❌ Error on attempt {attempt + 1}: {e}")
        if attempt < max_retries - 1:
            print(f"Retrying...")
        else:
            print("\n⚠️ All attempts failed. Video feed will not work.")

print("=" * 60)
