import os
import requests
import json
from typing import Optional
from decouple import config


def send_sms(to_number: str, body: str = "") -> Optional[str]:
    """
    Send an SMS using MSG91 Flow API.
    
    Args:
        to_number: Recipient mobile number (with country code, e.g., 919999999999).
        body: Ignored if using Flow API (template based), but kept for signature compatibility.
              If you use a variable in your MSG91 flow (e.g. ##message##), you can map this body to it.
    
    Returns:
        The request ID/Status on success, or None if failed.
    """
    auth_key = config("MSG91_AUTH_KEY", default=None)
    flow_id = config("MSG91_FLOW_ID", default=None)
    sender_id = config("MSG91_SENDER_ID", default="SCHATT")

    if not (auth_key and flow_id):
        print(f"[SMS MOCK] (MSG91 Config Missing) To: {to_number}")
        return "MOCK_SID"

    # MSG91 Flow API Endpoint
    url = "https://control.msg91.com/api/v5/flow/"

    # Prepare Payload
    # Note: MSG91 expects mobile numbers without leading '+' usually, but country code is required.
    # We strip '+' just in case.
    mobile = to_number.replace("+", "")
    
    # Payload structure for V5 Flow
    payload = {
        "template_id": flow_id,
        "sender": sender_id,
        "short_url": "0",
        "mobiles": mobile,
        # If your template has variables, mapped here:
        # "name": "Student Name",
        # "date": "2023-01-01"
        # For now we assume a static flow or one that doesn't strictly require dynamic body mapping
        # unless configured. To keep it simple, we don't map 'body' unless we know the var name.
    }

    headers = {
        "authkey": auth_key,
        "content-type": "application/json"
    }

    try:
        print(f"[MSG91] Sending Flow {flow_id} to {mobile}")
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            print(f"[MSG91 SUCCESS] Response: {response.text}")
            return response.json().get("message", "Success")
        else:
            print(f"[MSG91 ERROR] Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"[MSG91 EXCEPTION] Failed to send: {str(e)}")
        return None

