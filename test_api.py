import requests
import json

url = "http://127.0.0.1:5000/api/products/694cf45cb85e0363cbbc377a"
response = requests.get(url)
data = response.json()

print("Status Code:", response.status_code)
print("Has reviews:", 'reviews' in data)
print("Keys:", list(data.keys()))
print("\nFull response:")
print(json.dumps(data, indent=2))
