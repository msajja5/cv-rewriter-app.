import requests
import json

data = {
    "transcript": "Can you tell me about yourself?",
    "cv": "I am a Data Analyst.",
    "job_role": "Looking for a Data Analyst.",
    "context": []
}

try:
    response = requests.post("http://127.0.0.1:8000/chat", json=data, stream=True)
    print(f"Status Code: {response.status_code}")
    print("Response Content:")
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
