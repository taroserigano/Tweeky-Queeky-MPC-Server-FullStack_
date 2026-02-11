"""Final chatbot test - runs in background and saves result to file."""
import requests
import json
import time
import sys

def test_chatbot():
    url = "http://localhost:5000/api/agent/v2/chat"
    payload = {"query": "Recommend gaming gear"}
    
    # Wait for backend to be ready
    for i in range(30):
        try:
            # Quick health check
            r = requests.get("http://localhost:5000/api/products", timeout=2)
            if r.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
    else:
        return "ERROR: Backend not responding after 30 seconds"
    
    # Test chatbot
    try:
        response = requests.post(url, json=payload, timeout=90)
        data = response.json()
        resp_text = data.get("response", "")
        
        # Check which code version
        if "Secretlab" in resp_text or "PlayStation" in resp_text or "Xbox" in resp_text:
            result = "✅ ✅ ✅ NEW CODE WORKING! ✅ ✅ ✅\n\n" + resp_text[:600]
        elif "trending products" in resp_text.lower() or "best deals" in resp_text.lower():
            result = "❌ ❌ ❌ OLD CODE STILL RUNNING ❌ ❌ ❌\n\n" + resp_text[:600]
        else:
            result = "⚠️ UNCLEAR - CHECK MANUALLY\n\n" + resp_text[:600]
        
        return result
        
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    result = test_chatbot()
    
    # Save to file
    with open("CHATBOT_TEST_RESULT.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CHATBOT FIX TEST RESULT\n")
        f.write("=" * 70 + "\n\n")
        f.write(result)
        f.write("\n\n" + "=" * 70)
    
    # Also print
    print(result)
