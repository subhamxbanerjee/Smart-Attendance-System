import cv2

print("Testing IP Webcam connection...")
print("URL: http://10.145.76.160:8080/video\n")

try:
    cap = cv2.VideoCapture("http://10.145.76.160:8080/video")
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
    
    if cap.isOpened():
        print("✅ SUCCESS: Connected to IP Webcam!")
        ret, frame = cap.read()
        if ret:
            print(f"✅ Frame read successfully!")
            print(f"   Frame shape: {frame.shape}")
            print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
        else:
            print("⚠️ Connected but couldn't read frame")
        cap.release()
    else:
        print("❌ FAILED: Could not connect to IP Webcam")
        print("\nTroubleshooting:")
        print("1. Make sure IP Webcam app is running on your phone")
        print("2. Verify phone and laptop are on the same Wi-Fi network")
        print("3. Try opening http://10.145.76.160:8080 in your browser")
except Exception as e:
    print(f"❌ ERROR: {e}")
