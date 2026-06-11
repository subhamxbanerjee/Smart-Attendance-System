
import requests
import json

try:
    print("Triggering debug build...")
    resp = requests.get("http://127.0.0.1:8000/api/face/debug/build-encodings/")
    print(f"Status Code: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2))
    except:
        print(resp.text)
except Exception as e:
    print(f"Error: {e}")
