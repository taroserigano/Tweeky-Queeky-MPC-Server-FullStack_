import requests
import json

url = "http://localhost:5000/api/agent/v2/chat"
payload = {"query": "Recommend gaming gear"}

try:
    response = requests.post(url, json=payload, timeout=60)
    data = response.json()
    resp = data.get("response", "")
    
    with open("chatbot_response.txt", "w", encoding="utf-8") as f:
        f.write(resp)
    
    if "Secretlab" in resp or "PlayStation" in resp:
        print("✅ NEW CODE WORKING!")
    elif "trending products" in resp.lower():
        print("❌ OLD CODE STILL RUNNING")
    print("Response saved to chatbot_response.txt")
except Exception as e:
    print(f"Error: {e}")
