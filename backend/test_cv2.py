try:
    import cv2
    print("cv2 imported successfully")
    print(cv2.__version__)
except ImportError as e:
    print(f"Error importing cv2: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
