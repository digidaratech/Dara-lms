import requests
import json

# Test the save_partial endpoint
url = "http://localhost:5000/exam/save_partial"

# Sample data to send
data = {
    "course_id": 1,
    "answers": {
        "1": "B",
        "2": "C"
    },
    "status": "failed_due_to_tab_switch",
    "timestamp": "2023-01-01T00:00:00Z"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error making request: {e}")