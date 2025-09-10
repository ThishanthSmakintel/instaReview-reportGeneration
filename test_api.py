import requests
import json

url = "http://127.0.0.1:5000/reports/generate"
data = {
    "companyId": "123456789A_123456_01-01_FNB",
    "from": "2024-01-01T00:00:00Z",
    "to": "2024-01-31T23:59:59Z"
}

response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")