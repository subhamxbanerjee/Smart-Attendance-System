import cv2
import sys

# Test different IP Webcam URLs
test_urls = [
    "http://10.139.13.8:8080/video",
    "http://10.48.101.18:8080/video",
]

print("Testing camera connections...\n")

for url in test_urls:
    print(f"Trying: {url}")
    try:
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        
        if cap.isOpened():
            print(f"✅ SUCCESS: Connected to {url}")
            ret, frame = cap.read()
            if ret:
                print(f"✅ Frame read successfully! Shape: {frame.shape}")
            else:
                print(f"⚠️ Connected but couldn't read frame")
            cap.release()
            print(f"\n👉 Use this URL in your .env file: CAMERA_SOURCE={url}\n")
            sys.exit(0)
        else:
            print(f"❌ FAILED: Could not connect to {url}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()

print("\n⚠️ None of the URLs worked. Please:")
print("1. Make sure IP Webcam app is running on your phone")
print("2. Check that your phone and laptop are on the SAME Wi-Fi network")
print("3. Note the IP address shown in the IP Webcam app")
print("4. Try that IP address with this pattern: http://YOUR_IP:8080/video")
